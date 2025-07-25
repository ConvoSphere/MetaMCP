"""
Workflow persistence layer for MetaMCP.
"""

import json
import logging
from datetime import datetime
from typing import Any

from metamcp.composition.models import (
    WorkflowDefinition,
    WorkflowExecutionResult,
)
from metamcp.exceptions import WorkflowPersistenceError
from metamcp.utils.database import get_database_manager

logger = logging.getLogger(__name__)


class WorkflowPersistence:
    """Workflow persistence manager."""

    def __init__(self):
        self.db = get_database_manager()

    async def initialize(self) -> None:
        """Initialize the persistence layer."""
        await self._create_tables()
        logger.info("Workflow persistence layer initialized")

    async def _create_tables(self) -> None:
        """Create necessary database tables for workflow persistence."""
        try:
            # Create workflows table
            await self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT NOT NULL,
                    definition JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """
            )

            # Create workflow executions table
            await self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_data JSONB,
                    output_data JSONB,
                    error_data JSONB,
                    execution_time FLOAT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
            """
            )

            # Create workflow steps executions table
            await self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_step_executions (
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_data JSONB,
                    output_data JSONB,
                    error_data JSONB,
                    execution_time FLOAT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
                )
            """
            )

            # Create indexes for better performance
            await self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name)
            """
            )
            await self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflows_active ON workflows(is_active)
            """
            )
            await self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON workflow_executions(workflow_id)
            """
            )
            await self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_executions_status ON workflow_executions(status)
            """
            )
            await self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_step_executions_execution_id ON workflow_step_executions(execution_id)
            """
            )

            logger.info("Workflow persistence tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create workflow tables: {e}")
            raise WorkflowPersistenceError(
                f"Failed to initialize persistence layer: {e}"
            )

    async def save_workflow(self, workflow: WorkflowDefinition) -> None:
        """Save or update a workflow definition."""
        try:
            workflow_data = {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "definition": json.dumps(workflow.model_dump(mode="json")),
                "updated_at": datetime.utcnow(),
            }

            # Check if workflow exists
            existing = await self.db.fetchrow(
                "SELECT id FROM workflows WHERE id = $1", workflow.id
            )

            if existing:
                # Update existing workflow
                await self.db.execute(
                    """
                    UPDATE workflows
                    SET name = $2, description = $3, version = $4,
                        definition = $5, updated_at = $6
                    WHERE id = $1
                """,
                    workflow.id,
                    workflow.name,
                    workflow.description,
                    workflow.version,
                    workflow_data["definition"],
                    workflow_data["updated_at"],
                )
                logger.debug(f"Updated workflow: {workflow.id}")
            else:
                # Insert new workflow
                await self.db.execute(
                    """
                    INSERT INTO workflows (id, name, description, version, definition, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    workflow.id,
                    workflow.name,
                    workflow.description,
                    workflow.version,
                    workflow_data["definition"],
                    datetime.utcnow(),
                    workflow_data["updated_at"],
                )
                logger.debug(f"Saved new workflow: {workflow.id}")

        except Exception as e:
            logger.error(f"Failed to save workflow {workflow.id}: {e}")
            raise WorkflowPersistenceError(f"Failed to save workflow: {e}")

    async def load_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Load a workflow definition by ID."""
        try:
            row = await self.db.fetchrow(
                """
                SELECT definition FROM workflows
                WHERE id = $1 AND is_active = TRUE
            """,
                workflow_id,
            )

            if row:
                definition_data = json.loads(row["definition"])
                return WorkflowDefinition(**definition_data)

            return None

        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_id}: {e}")
            raise WorkflowPersistenceError(f"Failed to load workflow: {e}")

    async def load_all_workflows(self) -> list[WorkflowDefinition]:
        """Load all active workflow definitions."""
        try:
            rows = await self.db.fetch(
                """
                SELECT definition FROM workflows
                WHERE is_active = TRUE
                ORDER BY name
            """
            )

            workflows = []
            for row in rows:
                try:
                    definition_data = json.loads(row["definition"])
                    workflow = WorkflowDefinition(**definition_data)
                    workflows.append(workflow)
                except Exception as e:
                    logger.warning(f"Failed to parse workflow definition: {e}")
                    continue

            logger.info(f"Loaded {len(workflows)} workflows")
            return workflows

        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")
            raise WorkflowPersistenceError(f"Failed to load workflows: {e}")

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Soft delete a workflow (mark as inactive)."""
        try:
            result = await self.db.execute(
                """
                UPDATE workflows
                SET is_active = FALSE, updated_at = $2
                WHERE id = $1 AND is_active = TRUE
            """,
                workflow_id,
                datetime.utcnow(),
            )

            # Check if any rows were affected
            success = result and "UPDATE 1" in result
            if success:
                logger.info(f"Deleted workflow: {workflow_id}")
            else:
                logger.warning(f"Workflow not found or already deleted: {workflow_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            raise WorkflowPersistenceError(f"Failed to delete workflow: {e}")

    async def save_execution(self, execution: WorkflowExecutionResult) -> None:
        """Save a workflow execution record."""
        try:
            execution_data = {
                "id": execution.id,
                "workflow_id": execution.workflow_id,
                "status": (
                    execution.status.value
                    if hasattr(execution.status, "value")
                    else str(execution.status)
                ),
                "input_data": (
                    json.dumps(execution.input_data) if execution.input_data else None
                ),
                "output_data": (
                    json.dumps(execution.output_data) if execution.output_data else None
                ),
                "error_data": (
                    json.dumps(execution.error_data) if execution.error_data else None
                ),
                "execution_time": execution.execution_time,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
            }

            # Check if execution exists
            existing = await self.db.fetchrow(
                "SELECT id FROM workflow_executions WHERE id = $1", execution.id
            )

            if existing:
                # Update existing execution
                await self.db.execute(
                    """
                    UPDATE workflow_executions
                    SET status = $2, output_data = $3, error_data = $4,
                        execution_time = $5, completed_at = $6
                    WHERE id = $1
                """,
                    execution.id,
                    execution_data["status"],
                    execution_data["output_data"],
                    execution_data["error_data"],
                    execution_data["execution_time"],
                    execution_data["completed_at"],
                )
                logger.debug(f"Updated execution: {execution.id}")
            else:
                # Insert new execution
                await self.db.execute(
                    """
                    INSERT INTO workflow_executions
                    (id, workflow_id, status, input_data, output_data, error_data,
                     execution_time, started_at, completed_at, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    execution.id,
                    execution.workflow_id,
                    execution_data["status"],
                    execution_data["input_data"],
                    execution_data["output_data"],
                    execution_data["error_data"],
                    execution_data["execution_time"],
                    execution_data["started_at"],
                    execution_data["completed_at"],
                    datetime.utcnow(),
                )
                logger.debug(f"Saved new execution: {execution.id}")

        except Exception as e:
            logger.error(f"Failed to save execution {execution.id}: {e}")
            raise WorkflowPersistenceError(f"Failed to save execution: {e}")

    async def load_execution(self, execution_id: str) -> dict[str, Any] | None:
        """Load a workflow execution record."""
        try:
            row = await self.db.fetchrow(
                """
                SELECT * FROM workflow_executions WHERE id = $1
            """,
                execution_id,
            )

            if row:
                return dict(row)

            return None

        except Exception as e:
            logger.error(f"Failed to load execution {execution_id}: {e}")
            raise WorkflowPersistenceError(f"Failed to load execution: {e}")

    async def get_workflow_executions(
        self, workflow_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get execution history for a workflow."""
        try:
            rows = await self.db.fetch(
                """
                SELECT * FROM workflow_executions
                WHERE workflow_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """,
                workflow_id,
                limit,
            )

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get executions for workflow {workflow_id}: {e}")
            raise WorkflowPersistenceError(f"Failed to get workflow executions: {e}")

    async def cleanup_old_executions(self, days: int = 30) -> int:
        """Clean up old execution records."""
        try:
            result = await self.db.execute(
                """
                DELETE FROM workflow_step_executions
                WHERE execution_id IN (
                    SELECT id FROM workflow_executions
                    WHERE created_at < NOW() - INTERVAL '%s days'
                )
            """,
                days,
            )

            result = await self.db.execute(
                """
                DELETE FROM workflow_executions
                WHERE created_at < NOW() - INTERVAL '%s days'
            """,
                days,
            )

            # Extract number of deleted rows
            deleted_count = 0
            if result and "DELETE" in result:
                deleted_count = int(result.split()[-1])

            logger.info(f"Cleaned up {deleted_count} old execution records")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {e}")
            raise WorkflowPersistenceError(f"Failed to cleanup executions: {e}")


# Global persistence manager instance
_persistence_manager: WorkflowPersistence | None = None


def get_persistence_manager() -> WorkflowPersistence:
    """Get the global workflow persistence manager."""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = WorkflowPersistence()
    return _persistence_manager

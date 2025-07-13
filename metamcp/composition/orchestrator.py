"""
Workflow Orchestrator

This module provides high-level workflow orchestration capabilities,
including workflow management, execution coordination, and state persistence.
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from ..exceptions import WorkflowExecutionError, WorkflowValidationError
from ..utils.logging import get_logger
from .engine import WorkflowEngine
from .models import (
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    WorkflowState,
    WorkflowStatus,
)

logger = get_logger(__name__)


class WorkflowOrchestrator:
    """
    High-level workflow orchestrator.
    
    This class provides workflow management, execution coordination,
    and state persistence capabilities.
    """

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.engine = WorkflowEngine()
        self.execution_history: Dict[str, WorkflowExecutionResult] = {}
        self.active_executions: Dict[str, WorkflowState] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow orchestrator."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Workflow Orchestrator...")

            # Initialize workflow engine
            await self.engine.initialize()

            # Load persisted workflows
            await self._load_persisted_workflows()

            self._initialized = True
            logger.info("Workflow Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Workflow Orchestrator: {e}")
            raise WorkflowExecutionError(f"Initialization failed: {str(e)}")

    async def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """
        Register a workflow definition.
        
        Args:
            workflow: Workflow definition to register
        """
        try:
            await self.engine.register_workflow(workflow)
            logger.info(f"Registered workflow: {workflow.id}")

        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.id}: {e}")
            raise WorkflowValidationError(f"Workflow registration failed: {str(e)}")

    async def execute_workflow(
        self,
        request: WorkflowExecutionRequest,
        tool_executor: callable
    ) -> WorkflowExecutionResult:
        """
        Execute a workflow.
        
        Args:
            request: Workflow execution request
            tool_executor: Function to execute tools
            
        Returns:
            Workflow execution result
        """
        try:
            # Validate request
            self._validate_execution_request(request)

            # Execute workflow
            result = await self.engine.execute_workflow(request, tool_executor)

            # Store execution history
            self.execution_history[result.execution_id] = result

            # Clean up active execution
            if result.execution_id in self.active_executions:
                del self.active_executions[result.execution_id]

            logger.info(f"Workflow execution completed: {result.execution_id}")

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise WorkflowExecutionError(f"Workflow execution failed: {str(e)}")

    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecutionResult]:
        """
        Get the status of a workflow execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Workflow execution result or None if not found
        """
        # Check active executions
        if execution_id in self.active_executions:
            state = self.active_executions[execution_id]
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=state.workflow_id,
                status=state.status,
                error=state.error,
                step_results=state.step_results,
                started_at=state.started_at,
                completed_at=state.completed_at,
                metadata=state.metadata
            )

        # Check execution history
        return self.execution_history.get(execution_id)

    async def cancel_workflow(self, execution_id: str) -> bool:
        """
        Cancel a running workflow execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            if execution_id in self.active_executions:
                state = self.active_executions[execution_id]
                state.status = WorkflowStatus.CANCELLED
                state.completed_at = datetime.now(UTC)
                
                # Move to history
                result = WorkflowExecutionResult(
                    execution_id=execution_id,
                    workflow_id=state.workflow_id,
                    status=state.status,
                    error="Cancelled by user",
                    step_results=state.step_results,
                    started_at=state.started_at,
                    completed_at=state.completed_at,
                    metadata=state.metadata
                )
                
                self.execution_history[execution_id] = result
                del self.active_executions[execution_id]
                
                logger.info(f"Cancelled workflow execution: {execution_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to cancel workflow {execution_id}: {e}")
            return False

    async def list_workflows(self) -> List[WorkflowDefinition]:
        """
        List all registered workflows.
        
        Returns:
            List of workflow definitions
        """
        return list(self.engine.workflows.values())

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get a specific workflow definition.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow definition or None if not found
        """
        return self.engine.workflows.get(workflow_id)

    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow definition.
        
        Args:
            workflow_id: Workflow ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if workflow_id in self.engine.workflows:
                del self.engine.workflows[workflow_id]
                logger.info(f"Deleted workflow: {workflow_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False

    async def get_execution_history(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowExecutionResult]:
        """
        Get execution history.
        
        Args:
            workflow_id: Filter by workflow ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of execution results
        """
        results = []
        
        for execution in self.execution_history.values():
            if workflow_id is None or execution.workflow_id == workflow_id:
                results.append(execution)

        # Sort by start time (newest first)
        results.sort(key=lambda x: x.started_at, reverse=True)
        
        return results[:limit]

    async def get_active_executions(self) -> List[WorkflowExecutionResult]:
        """
        Get currently active workflow executions.
        
        Returns:
            List of active execution results
        """
        results = []
        
        for execution_id, state in self.active_executions.items():
            result = WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=state.workflow_id,
                status=state.status,
                error=state.error,
                step_results=state.step_results,
                started_at=state.started_at,
                completed_at=state.completed_at,
                metadata=state.metadata
            )
            results.append(result)

        return results

    async def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old execution history.
        
        Args:
            max_age_hours: Maximum age in hours to keep
            
        Returns:
            Number of executions cleaned up
        """
        cutoff_time = datetime.now(UTC).timestamp() - (max_age_hours * 3600)
        cleaned_count = 0

        execution_ids_to_remove = []
        
        for execution_id, result in self.execution_history.items():
            if result.started_at.timestamp() < cutoff_time:
                execution_ids_to_remove.append(execution_id)

        for execution_id in execution_ids_to_remove:
            del self.execution_history[execution_id]
            cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old executions")

        return cleaned_count

    def _validate_execution_request(self, request: WorkflowExecutionRequest) -> None:
        """Validate workflow execution request."""
        if not request.workflow_id:
            raise WorkflowValidationError("Workflow ID is required")

        if request.workflow_id not in self.engine.workflows:
            raise WorkflowValidationError(f"Workflow not found: {request.workflow_id}")

        if request.timeout and request.timeout <= 0:
            raise WorkflowValidationError("Timeout must be positive")

    async def _load_persisted_workflows(self) -> None:
        """Load persisted workflows from storage."""
        # TODO: Implement persistence layer
        # For now, this is a placeholder
        logger.info("Loading persisted workflows...")

    async def _persist_workflow(self, workflow: WorkflowDefinition) -> None:
        """Persist workflow to storage."""
        # TODO: Implement persistence layer
        # For now, this is a placeholder
        logger.debug(f"Persisting workflow: {workflow.id}")

    async def shutdown(self) -> None:
        """Shutdown the workflow orchestrator."""
        logger.info("Shutting down Workflow Orchestrator...")
        
        # Cancel active executions
        for execution_id in list(self.active_executions.keys()):
            await self.cancel_workflow(execution_id)
        
        self._initialized = False
        logger.info("Workflow Orchestrator shutdown complete") 
"""
Unit tests for workflow persistence.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from metamcp.composition.models import WorkflowDefinition, WorkflowStep
from metamcp.composition.persistence import WorkflowPersistence, get_persistence_manager
from metamcp.exceptions import WorkflowPersistenceError


class TestWorkflowPersistence:
    """Test workflow persistence functionality."""

    @pytest.fixture
    def persistence(self):
        """Create a persistence manager instance."""
        return WorkflowPersistence()

    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow definition."""
        steps = [
            WorkflowStep(
                id="step1",
                name="Test Step",
                step_type="tool_call",
                config={"tool_name": "test_tool"},
            )
        ]

        return WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            description="A test workflow",
            version="1.0.0",
            steps=steps,
            entry_point="step1",
        )

    @pytest.mark.asyncio
    async def test_initialize(self, persistence):
        """Test persistence initialization."""
        mock_db = AsyncMock()
        persistence.db = mock_db

        await persistence.initialize()

        # Check that tables are created
        assert (
            mock_db.execute.call_count >= 3
        )  # workflows, executions, step_executions tables

    @pytest.mark.asyncio
    async def test_save_new_workflow(self, persistence, sample_workflow):
        """Test saving a new workflow."""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = None  # No existing workflow
        persistence.db = mock_db

        await persistence.save_workflow(sample_workflow)

        # Verify INSERT was called
        mock_db.execute.assert_called()
        args = mock_db.execute.call_args[0]
        assert "INSERT INTO workflows" in args[0]

    @pytest.mark.asyncio
    async def test_save_existing_workflow(self, persistence, sample_workflow):
        """Test updating an existing workflow."""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {"id": sample_workflow.id}  # Existing workflow
        persistence.db = mock_db

        await persistence.save_workflow(sample_workflow)

        # Verify UPDATE was called
        mock_db.execute.assert_called()
        args = mock_db.execute.call_args[0]
        assert "UPDATE workflows" in args[0]

    @pytest.mark.asyncio
    async def test_load_workflow_found(self, persistence, sample_workflow):
        """Test loading an existing workflow."""
        mock_db = AsyncMock()
        workflow_data = json.dumps(sample_workflow.model_dump(mode="json"))
        mock_db.fetchrow.return_value = {"definition": workflow_data}
        persistence.db = mock_db

        result = await persistence.load_workflow(sample_workflow.id)

        assert result is not None
        assert result.id == sample_workflow.id
        assert result.name == sample_workflow.name

    @pytest.mark.asyncio
    async def test_load_workflow_not_found(self, persistence):
        """Test loading a non-existent workflow."""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = None
        persistence.db = mock_db

        result = await persistence.load_workflow("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_all_workflows(self, persistence, sample_workflow):
        """Test loading all workflows."""
        mock_db = AsyncMock()
        workflow_data = json.dumps(sample_workflow.model_dump(mode="json"))
        mock_db.fetch.return_value = [{"definition": workflow_data}]
        persistence.db = mock_db

        result = await persistence.load_all_workflows()

        assert len(result) == 1
        assert result[0].id == sample_workflow.id

    @pytest.mark.asyncio
    async def test_delete_workflow_success(self, persistence):
        """Test successful workflow deletion."""
        mock_db = AsyncMock()
        mock_db.execute.return_value = "UPDATE 1"  # Successful update
        persistence.db = mock_db

        result = await persistence.delete_workflow("test-workflow")

        assert result is True
        mock_db.execute.assert_called()
        args = mock_db.execute.call_args[0]
        assert "UPDATE workflows" in args[0]
        assert "is_active = FALSE" in args[0]

    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self, persistence):
        """Test deleting a non-existent workflow."""
        mock_db = AsyncMock()
        mock_db.execute.return_value = "UPDATE 0"  # No rows affected
        persistence.db = mock_db

        result = await persistence.delete_workflow("non-existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_workflow_executions(self, persistence):
        """Test getting workflow execution history."""
        mock_db = AsyncMock()
        execution_data = [
            {"id": "exec1", "status": "completed", "created_at": datetime.utcnow()},
            {"id": "exec2", "status": "running", "created_at": datetime.utcnow()},
        ]
        mock_db.fetch.return_value = execution_data
        persistence.db = mock_db

        result = await persistence.get_workflow_executions("test-workflow")

        assert len(result) == 2
        assert result[0]["id"] == "exec1"

    @pytest.mark.asyncio
    async def test_cleanup_old_executions(self, persistence):
        """Test cleaning up old execution records."""
        mock_db = AsyncMock()
        mock_db.execute.return_value = "DELETE 5"  # 5 rows deleted
        persistence.db = mock_db

        result = await persistence.cleanup_old_executions(30)

        assert result == 5
        # Should call execute twice (step executions, then main executions)
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_save_workflow_error(self, persistence, sample_workflow):
        """Test error handling in save_workflow."""
        mock_db = AsyncMock()
        mock_db.fetchrow.side_effect = Exception("Database error")
        persistence.db = mock_db

        with pytest.raises(WorkflowPersistenceError):
            await persistence.save_workflow(sample_workflow)

    @pytest.mark.asyncio
    async def test_load_workflow_error(self, persistence):
        """Test error handling in load_workflow."""
        mock_db = AsyncMock()
        mock_db.fetchrow.side_effect = Exception("Database error")
        persistence.db = mock_db

        with pytest.raises(WorkflowPersistenceError):
            await persistence.load_workflow("test-workflow")


def test_get_persistence_manager_singleton():
    """Test that get_persistence_manager returns singleton."""
    manager1 = get_persistence_manager()
    manager2 = get_persistence_manager()
    assert manager1 is manager2

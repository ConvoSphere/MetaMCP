"""
Composition API

This module provides REST API endpoints for workflow composition
and orchestration functionality.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..composition.models import (
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    WorkflowStatus,
)
from ..composition.orchestrator import WorkflowOrchestrator
from ..exceptions import WorkflowExecutionError, WorkflowValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create router
composition_router = APIRouter(prefix="/composition", tags=["composition"])


# Dependency injection
def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get workflow orchestrator instance."""
    # Note: In a production environment, this would use a proper DI container
    # like FastAPI's dependency injection system with scoped instances
    return WorkflowOrchestrator()


# Request/Response models
class WorkflowRegistrationRequest(BaseModel):
    """Request to register a workflow."""

    workflow: WorkflowDefinition = Field(..., description="Workflow definition")


class WorkflowRegistrationResponse(BaseModel):
    """Response for workflow registration."""

    workflow_id: str = Field(..., description="Registered workflow ID")
    message: str = Field(..., description="Registration message")


class WorkflowExecutionResponse(BaseModel):
    """Response for workflow execution."""

    execution_id: str = Field(..., description="Execution ID")
    workflow_id: str = Field(..., description="Workflow ID")
    status: WorkflowStatus = Field(..., description="Execution status")
    result: dict[str, Any] | None = Field(None, description="Execution result")
    error: str | None = Field(None, description="Error message if failed")
    execution_time: float | None = Field(None, description="Execution time in seconds")
    started_at: datetime = Field(..., description="Start time")
    completed_at: datetime | None = Field(None, description="Completion time")


class WorkflowListResponse(BaseModel):
    """Response for workflow listing."""

    workflows: list[WorkflowDefinition] = Field(..., description="List of workflows")
    total_count: int = Field(..., description="Total number of workflows")


class ExecutionHistoryResponse(BaseModel):
    """Response for execution history."""

    executions: list[WorkflowExecutionResult] = Field(
        ..., description="Execution history"
    )
    total_count: int = Field(..., description="Total number of executions")


# API Endpoints
@composition_router.post(
    "/workflows",
    response_model=WorkflowRegistrationResponse,
    summary="Register workflow",
)
async def register_workflow(
    request: WorkflowRegistrationRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> WorkflowRegistrationResponse:
    """
    Register a new workflow definition.

    Args:
        request: Workflow registration request
        orchestrator: Workflow orchestrator

    Returns:
        Registration response
    """
    try:
        await orchestrator.register_workflow(request.workflow)

        return WorkflowRegistrationResponse(
            workflow_id=request.workflow.id,
            message=f"Workflow '{request.workflow.name}' registered successfully",
        )

    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        )
    except Exception as e:
        logger.error(f"Workflow registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.get(
    "/workflows", response_model=WorkflowListResponse, summary="List workflows"
)
async def list_workflows(
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> WorkflowListResponse:
    """
    List all registered workflows.

    Args:
        orchestrator: Workflow orchestrator

    Returns:
        List of workflows
    """
    try:
        workflows = await orchestrator.list_workflows()

        return WorkflowListResponse(workflows=workflows, total_count=len(workflows))

    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowDefinition,
    summary="Get workflow",
)
async def get_workflow(
    workflow_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> WorkflowDefinition:
    """
    Get a specific workflow definition.

    Args:
        workflow_id: Workflow ID
        orchestrator: Workflow orchestrator

    Returns:
        Workflow definition
    """
    try:
        workflow = await orchestrator.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found",
            )

        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.delete("/workflows/{workflow_id}", summary="Delete workflow")
async def delete_workflow(
    workflow_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> dict[str, str]:
    """
    Delete a workflow definition.

    Args:
        workflow_id: Workflow ID to delete
        orchestrator: Workflow orchestrator

    Returns:
        Deletion response
    """
    try:
        success = await orchestrator.delete_workflow(workflow_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found",
            )

        return {"message": f"Workflow '{workflow_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.post(
    "/workflows/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    summary="Execute workflow",
)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> WorkflowExecutionResponse:
    """
    Execute a workflow.

    Args:
        workflow_id: Workflow ID to execute
        request: Execution request
        background_tasks: FastAPI background tasks
        orchestrator: Workflow orchestrator

    Returns:
        Execution response
    """
    try:
        # Set workflow ID from path
        request.workflow_id = workflow_id

        # Mock tool executor for now
        async def mock_tool_executor(tool_name: str, arguments: dict[str, Any]) -> Any:
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": f"Mock execution of {tool_name}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Execute workflow
        result = await orchestrator.execute_workflow(request, mock_tool_executor)

        return WorkflowExecutionResponse(
            execution_id=result.execution_id,
            workflow_id=result.workflow_id,
            status=result.status,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time,
            started_at=result.started_at,
            completed_at=result.completed_at,
        )

    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        )
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get execution status",
)
async def get_execution_status(
    execution_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> WorkflowExecutionResponse:
    """
    Get the status of a workflow execution.

    Args:
        execution_id: Execution ID
        orchestrator: Workflow orchestrator

    Returns:
        Execution status
    """
    try:
        result = await orchestrator.get_workflow_status(execution_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution '{execution_id}' not found",
            )

        return WorkflowExecutionResponse(
            execution_id=result.execution_id,
            workflow_id=result.workflow_id,
            status=result.status,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time,
            started_at=result.started_at,
            completed_at=result.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status {execution_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.post(
    "/executions/{execution_id}/cancel", summary="Cancel execution"
)
async def cancel_execution(
    execution_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> dict[str, str]:
    """
    Cancel a running workflow execution.

    Args:
        execution_id: Execution ID to cancel
        orchestrator: Workflow orchestrator

    Returns:
        Cancellation response
    """
    try:
        success = await orchestrator.cancel_workflow(execution_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution '{execution_id}' not found or not running",
            )

        return {"message": f"Execution '{execution_id}' cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.get(
    "/executions",
    response_model=ExecutionHistoryResponse,
    summary="Get execution history",
)
async def get_execution_history(
    workflow_id: str | None = None,
    limit: int = 100,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> ExecutionHistoryResponse:
    """
    Get workflow execution history.

    Args:
        workflow_id: Filter by workflow ID (optional)
        limit: Maximum number of results
        orchestrator: Workflow orchestrator

    Returns:
        Execution history
    """
    try:
        executions = await orchestrator.get_execution_history(workflow_id, limit)

        return ExecutionHistoryResponse(
            executions=executions, total_count=len(executions)
        )

    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@composition_router.get(
    "/executions/active",
    response_model=ExecutionHistoryResponse,
    summary="Get active executions",
)
async def get_active_executions(
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> ExecutionHistoryResponse:
    """
    Get currently active workflow executions.

    Args:
        orchestrator: Workflow orchestrator

    Returns:
        Active executions
    """
    try:
        executions = await orchestrator.get_active_executions()

        return ExecutionHistoryResponse(
            executions=executions, total_count=len(executions)
        )

    except Exception as e:
        logger.error(f"Failed to get active executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

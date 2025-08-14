"""
Resource Management API

This module provides API endpoints for monitoring and controlling
tool executions with resource limits.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..security.api_keys import APIKeyManager, get_api_key_manager
from ..security.resource_limits import (
    ExecutionStatus,
    ResourceLimitManager,
    ResourceLimits,
    get_resource_limit_manager,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/resources", tags=["Resource Management"])


class ResourceLimitsRequest(BaseModel):
    """Resource limits request model."""

    cpu_time_soft: int | None = Field(30, description="CPU time soft limit in seconds")
    cpu_time_hard: int | None = Field(60, description="CPU time hard limit in seconds")
    memory_usage_soft: int | None = Field(
        512, description="Memory usage soft limit in MB"
    )
    memory_usage_hard: int | None = Field(
        1024, description="Memory usage hard limit in MB"
    )
    execution_time_soft: int | None = Field(
        300, description="Execution time soft limit in seconds"
    )
    execution_time_hard: int | None = Field(
        600, description="Execution time hard limit in seconds"
    )
    api_calls_soft: int | None = Field(100, description="API calls soft limit")
    api_calls_hard: int | None = Field(200, description="API calls hard limit")
    concurrent_executions_soft: int | None = Field(
        5, description="Concurrent executions soft limit"
    )
    concurrent_executions_hard: int | None = Field(
        10, description="Concurrent executions hard limit"
    )


class ExecutionMetricsRequest(BaseModel):
    """Execution metrics update request model."""

    cpu_time: float | None = Field(None, description="CPU time in seconds")
    memory_usage: float | None = Field(None, description="Memory usage in MB")
    api_calls: int | None = Field(None, description="Number of API calls")


class InterruptExecutionRequest(BaseModel):
    """Interrupt execution request model."""

    reason: str | None = Field(
        "Manual interruption", description="Reason for interruption"
    )


def get_resource_manager() -> ResourceLimitManager:
    """Get resource limit manager instance."""
    return get_resource_limit_manager()


def get_api_manager() -> APIKeyManager:
    """Get API key manager instance."""
    return get_api_key_manager()


@router.post("/executions/start")
async def start_execution(
    tool_id: str,
    user_id: str,
    limits: ResourceLimitsRequest | None = None,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Start a new tool execution with resource monitoring.

    Args:
        tool_id: Tool ID to execute
        user_id: User ID executing the tool
        limits: Custom resource limits (optional)
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Execution information with execution ID
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Convert limits to ResourceLimits object
        custom_limits = None
        if limits:
            custom_limits = ResourceLimits(
                cpu_time_soft=limits.cpu_time_soft,
                cpu_time_hard=limits.cpu_time_hard,
                memory_usage_soft=limits.memory_usage_soft,
                memory_usage_hard=limits.memory_usage_hard,
                execution_time_soft=limits.execution_time_soft,
                execution_time_hard=limits.execution_time_hard,
                api_calls_soft=limits.api_calls_soft,
                api_calls_hard=limits.api_calls_hard,
                concurrent_executions_soft=limits.concurrent_executions_soft,
                concurrent_executions_hard=limits.concurrent_executions_hard,
            )

        # Start execution
        execution_id = resource_manager.start_execution(tool_id, user_id, custom_limits)

        # Get execution info
        execution_info = resource_manager.get_execution_info(execution_id)

        logger.info(f"Started execution {execution_id} for tool {tool_id}")

        return {
            "execution_id": execution_id,
            "status": "started",
            "execution_info": execution_info,
        }

    except Exception as e:
        logger.error(f"Error starting execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/end")
async def end_execution(
    execution_id: str,
    status: ExecutionStatus = ExecutionStatus.COMPLETED,
    error_message: str | None = None,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    End a tool execution.

    Args:
        execution_id: Execution ID to end
        status: Final execution status
        error_message: Error message if failed
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Execution end confirmation
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # End execution
        success = resource_manager.end_execution(execution_id, status, error_message)

        if not success:
            raise HTTPException(status_code=404, detail="Execution not found")

        logger.info(f"Ended execution {execution_id} with status {status.value}")

        return {
            "execution_id": execution_id,
            "status": "ended",
            "final_status": status.value,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/executions/{execution_id}/metrics")
async def update_execution_metrics(
    execution_id: str,
    metrics: ExecutionMetricsRequest,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Update execution metrics.

    Args:
        execution_id: Execution ID to update
        metrics: Metrics to update
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Metrics update confirmation
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Update metrics
        success = resource_manager.update_execution_metrics(
            execution_id,
            cpu_time=metrics.cpu_time,
            memory_usage=metrics.memory_usage,
            api_calls=metrics.api_calls,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Execution not found")

        return {"execution_id": execution_id, "status": "metrics_updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}")
async def get_execution_info(
    execution_id: str,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Get execution information.

    Args:
        execution_id: Execution ID to get info for
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Execution information
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Get execution info
        execution_info = resource_manager.get_execution_info(execution_id)

        if not execution_info:
            raise HTTPException(status_code=404, detail="Execution not found")

        return execution_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_executions(
    user_id: str | None = Query(None, description="Filter by user ID"),
    active_only: bool = Query(True, description="Only return active executions"),
    limit: int = Query(100, description="Maximum number of records to return"),
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    List executions.

    Args:
        user_id: Filter by user ID (optional)
        active_only: Only return active executions
        limit: Maximum number of records to return
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        List of executions
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Get executions
        if active_only:
            executions = resource_manager.list_active_executions(user_id)
        else:
            executions = resource_manager.list_execution_history(user_id, limit)

        return {
            "executions": executions,
            "count": len(executions),
            "active_only": active_only,
        }

    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/interrupt")
async def interrupt_execution(
    execution_id: str,
    request: InterruptExecutionRequest,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Interrupt a running execution.

    Args:
        execution_id: Execution ID to interrupt
        request: Interrupt request with reason
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Interrupt confirmation
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Interrupt execution
        success = resource_manager.interrupt_execution(execution_id, request.reason)

        if not success:
            raise HTTPException(status_code=404, detail="Execution not found")

        logger.info(f"Interrupted execution {execution_id}: {request.reason}")

        return {
            "execution_id": execution_id,
            "status": "interrupted",
            "reason": request.reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interrupting execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}/limits/soft")
async def check_soft_limits(
    execution_id: str,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Check soft limits for an execution.

    Args:
        execution_id: Execution ID to check
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Soft limit violations
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Check soft limits
        violations = resource_manager.check_soft_limits(execution_id)

        if not violations:
            raise HTTPException(status_code=404, detail="Execution not found")

        return {
            "execution_id": execution_id,
            "soft_limit_violations": {
                limit.value: exceeded for limit, exceeded in violations.items()
            },
            "has_violations": any(violations.values()),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking soft limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}/limits/hard")
async def check_hard_limits(
    execution_id: str,
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Check hard limits for an execution.

    Args:
        execution_id: Execution ID to check
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Hard limit violations
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Check hard limits
        violations = resource_manager.check_hard_limits(execution_id)

        if not violations:
            raise HTTPException(status_code=404, detail="Execution not found")

        return {
            "execution_id": execution_id,
            "hard_limit_violations": {
                limit.value: exceeded for limit, exceeded in violations.items()
            },
            "has_violations": any(violations.values()),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking hard limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_resource_status(
    resource_manager: ResourceLimitManager = Depends(get_resource_manager),
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Get overall resource management status.

    Args:
        resource_manager: Resource limit manager
        api_key: API key for authentication

    Returns:
        Resource management status
    """
    try:
        # Validate API key
        api_manager = get_api_manager()
        if not api_manager.check_permission(api_key, "resource_management"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Get status information
        active_executions = resource_manager.list_active_executions()
        recent_history = resource_manager.list_execution_history(limit=10)

        return {
            "active_executions_count": len(active_executions),
            "recent_executions_count": len(recent_history),
            "manager_initialized": resource_manager.is_initialized,
            "active_executions": active_executions,
            "recent_executions": recent_history,
        }

    except Exception as e:
        logger.error(f"Error getting resource status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

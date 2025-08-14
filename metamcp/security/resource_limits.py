"""
Resource Limits Management

This module provides resource limits for tool execution with soft and hard limits,
plus API endpoints to monitor and control execution.
"""

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..config import get_settings
from ..exceptions import ResourceLimitError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LimitType(Enum):
    """Resource limit types."""

    CPU_TIME = "cpu_time"
    MEMORY_USAGE = "memory_usage"
    EXECUTION_TIME = "execution_time"
    API_CALLS = "api_calls"
    CONCURRENT_EXECUTIONS = "concurrent_executions"


class ExecutionStatus(Enum):
    """Tool execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"


@dataclass
class ResourceLimits:
    """Resource limits configuration."""

    cpu_time_soft: int = 30  # seconds
    cpu_time_hard: int = 60  # seconds
    memory_usage_soft: int = 512  # MB
    memory_usage_hard: int = 1024  # MB
    execution_time_soft: int = 300  # seconds
    execution_time_hard: int = 600  # seconds
    api_calls_soft: int = 100
    api_calls_hard: int = 200
    concurrent_executions_soft: int = 5
    concurrent_executions_hard: int = 10


@dataclass
class ExecutionContext:
    """Tool execution context."""

    execution_id: str
    tool_id: str
    user_id: str
    start_time: datetime
    status: ExecutionStatus = ExecutionStatus.RUNNING
    end_time: datetime | None = None
    cpu_time: float = 0.0
    memory_usage: float = 0.0
    api_calls: int = 0
    error_message: str | None = None
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    interrupt_callback: Callable | None = None


class ResourceLimitManager:
    """
    Resource Limit Manager for tool execution.

    Manages soft and hard limits for tool execution with monitoring
    and control capabilities.
    """

    def __init__(self):
        """Initialize Resource Limit Manager."""
        self.active_executions: dict[str, ExecutionContext] = {}
        self.execution_history: list[ExecutionContext] = []
        self.limit_checkers: dict[LimitType, Callable] = {}
        self._monitoring_task: asyncio.Task | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the resource limit manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Resource Limit Manager...")

            # Initialize limit checkers
            self._setup_limit_checkers()

            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._monitor_executions())

            self._initialized = True
            logger.info("Resource Limit Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Resource Limit Manager: {e}")
            raise ResourceLimitError(
                message=f"Failed to initialize resource limit manager: {str(e)}"
            )

    def start_execution(
        self, tool_id: str, user_id: str, custom_limits: ResourceLimits | None = None
    ) -> str:
        """
        Start a new tool execution with resource monitoring.

        Args:
            tool_id: Tool ID being executed
            user_id: User ID executing the tool
            custom_limits: Custom resource limits (optional)

        Returns:
            Execution ID
        """
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"

        # Use custom limits or defaults
        limits = custom_limits or ResourceLimits()

        # Create execution context
        context = ExecutionContext(
            execution_id=execution_id,
            tool_id=tool_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            resource_limits=limits,
        )

        # Store active execution
        self.active_executions[execution_id] = context

        logger.info(f"Started execution {execution_id} for tool {tool_id}")

        return execution_id

    def end_execution(
        self,
        execution_id: str,
        status: ExecutionStatus = ExecutionStatus.COMPLETED,
        error_message: str | None = None,
    ) -> bool:
        """
        End a tool execution.

        Args:
            execution_id: Execution ID to end
            status: Final execution status
            error_message: Error message if failed

        Returns:
            True if execution was ended, False if not found
        """
        if execution_id not in self.active_executions:
            return False

        context = self.active_executions[execution_id]
        context.status = status
        context.end_time = datetime.utcnow()
        context.error_message = error_message

        # Move to history
        self.execution_history.append(context)
        del self.active_executions[execution_id]

        logger.info(f"Ended execution {execution_id} with status {status.value}")

        return True

    def update_execution_metrics(
        self,
        execution_id: str,
        cpu_time: float | None = None,
        memory_usage: float | None = None,
        api_calls: int | None = None,
    ) -> bool:
        """
        Update execution metrics.

        Args:
            execution_id: Execution ID to update
            cpu_time: CPU time in seconds
            memory_usage: Memory usage in MB
            api_calls: Number of API calls

        Returns:
            True if metrics were updated, False if execution not found
        """
        if execution_id not in self.active_executions:
            return False

        context = self.active_executions[execution_id]

        if cpu_time is not None:
            context.cpu_time = cpu_time
        if memory_usage is not None:
            context.memory_usage = memory_usage
        if api_calls is not None:
            context.api_calls = api_calls

        return True

    def check_soft_limits(self, execution_id: str) -> dict[LimitType, bool]:
        """
        Check if execution has exceeded soft limits.

        Args:
            execution_id: Execution ID to check

        Returns:
            Dictionary of limit types and whether they're exceeded
        """
        if execution_id not in self.active_executions:
            return {}

        context = self.active_executions[execution_id]
        results = {}

        for limit_type, checker in self.limit_checkers.items():
            results[limit_type] = checker(context, soft=True)

        return results

    def check_hard_limits(self, execution_id: str) -> dict[LimitType, bool]:
        """
        Check if execution has exceeded hard limits.

        Args:
            execution_id: Execution ID to check

        Returns:
            Dictionary of limit types and whether they're exceeded
        """
        if execution_id not in self.active_executions:
            return {}

        context = self.active_executions[execution_id]
        results = {}

        for limit_type, checker in self.limit_checkers.items():
            results[limit_type] = checker(context, soft=False)

        return results

    def interrupt_execution(
        self, execution_id: str, reason: str = "Manual interruption"
    ) -> bool:
        """
        Interrupt a running execution.

        Args:
            execution_id: Execution ID to interrupt
            reason: Reason for interruption

        Returns:
            True if execution was interrupted, False if not found
        """
        if execution_id not in self.active_executions:
            return False

        context = self.active_executions[execution_id]

        # Call interrupt callback if available
        if context.interrupt_callback:
            try:
                context.interrupt_callback()
            except Exception as e:
                logger.error(f"Error calling interrupt callback: {e}")

        # End execution
        self.end_execution(execution_id, ExecutionStatus.INTERRUPTED, reason)

        logger.info(f"Interrupted execution {execution_id}: {reason}")

        return True

    def get_execution_info(self, execution_id: str) -> dict[str, Any] | None:
        """
        Get execution information.

        Args:
            execution_id: Execution ID

        Returns:
            Execution information or None if not found
        """
        # Check active executions
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
        else:
            # Check history
            context = next(
                (
                    ctx
                    for ctx in self.execution_history
                    if ctx.execution_id == execution_id
                ),
                None,
            )

        if not context:
            return None

        return {
            "execution_id": context.execution_id,
            "tool_id": context.tool_id,
            "user_id": context.user_id,
            "start_time": context.start_time.isoformat(),
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "status": context.status.value,
            "cpu_time": context.cpu_time,
            "memory_usage": context.memory_usage,
            "api_calls": context.api_calls,
            "error_message": context.error_message,
            "resource_limits": {
                "cpu_time_soft": context.resource_limits.cpu_time_soft,
                "cpu_time_hard": context.resource_limits.cpu_time_hard,
                "memory_usage_soft": context.resource_limits.memory_usage_soft,
                "memory_usage_hard": context.resource_limits.memory_usage_hard,
                "execution_time_soft": context.resource_limits.execution_time_soft,
                "execution_time_hard": context.resource_limits.execution_time_hard,
                "api_calls_soft": context.resource_limits.api_calls_soft,
                "api_calls_hard": context.resource_limits.api_calls_hard,
                "concurrent_executions_soft": context.resource_limits.concurrent_executions_soft,
                "concurrent_executions_hard": context.resource_limits.concurrent_executions_hard,
            },
        }

    def list_active_executions(
        self, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List active executions.

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List of active execution information
        """
        executions = []
        for context in self.active_executions.values():
            if user_id and context.user_id != user_id:
                continue

            executions.append(self.get_execution_info(context.execution_id))

        return executions

    def list_execution_history(
        self, user_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List execution history.

        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of records to return

        Returns:
            List of execution history information
        """
        executions = []
        for context in reversed(self.execution_history[-limit:]):
            if user_id and context.user_id != user_id:
                continue

            executions.append(self.get_execution_info(context.execution_id))

        return executions

    def _setup_limit_checkers(self) -> None:
        """Setup limit checker functions."""
        self.limit_checkers = {
            LimitType.CPU_TIME: self._check_cpu_time_limit,
            LimitType.MEMORY_USAGE: self._check_memory_usage_limit,
            LimitType.EXECUTION_TIME: self._check_execution_time_limit,
            LimitType.API_CALLS: self._check_api_calls_limit,
            LimitType.CONCURRENT_EXECUTIONS: self._check_concurrent_executions_limit,
        }

    def _check_cpu_time_limit(
        self, context: ExecutionContext, soft: bool = True
    ) -> bool:
        """Check CPU time limit."""
        limit = (
            context.resource_limits.cpu_time_soft
            if soft
            else context.resource_limits.cpu_time_hard
        )
        return context.cpu_time > limit

    def _check_memory_usage_limit(
        self, context: ExecutionContext, soft: bool = True
    ) -> bool:
        """Check memory usage limit."""
        limit = (
            context.resource_limits.memory_usage_soft
            if soft
            else context.resource_limits.memory_usage_hard
        )
        return context.memory_usage > limit

    def _check_execution_time_limit(
        self, context: ExecutionContext, soft: bool = True
    ) -> bool:
        """Check execution time limit."""
        limit = (
            context.resource_limits.execution_time_soft
            if soft
            else context.resource_limits.execution_time_hard
        )
        execution_time = (datetime.utcnow() - context.start_time).total_seconds()
        return execution_time > limit

    def _check_api_calls_limit(
        self, context: ExecutionContext, soft: bool = True
    ) -> bool:
        """Check API calls limit."""
        limit = (
            context.resource_limits.api_calls_soft
            if soft
            else context.resource_limits.api_calls_hard
        )
        return context.api_calls > limit

    def _check_concurrent_executions_limit(
        self, context: ExecutionContext, soft: bool = True
    ) -> bool:
        """Check concurrent executions limit."""
        limit = (
            context.resource_limits.concurrent_executions_soft
            if soft
            else context.resource_limits.concurrent_executions_hard
        )
        user_executions = sum(
            1
            for ctx in self.active_executions.values()
            if ctx.user_id == context.user_id
        )
        return user_executions > limit

    async def _monitor_executions(self) -> None:
        """Monitor active executions for limit violations."""
        while self._initialized:
            try:
                for execution_id, context in list(self.active_executions.items()):
                    # Check hard limits
                    hard_limit_violations = self.check_hard_limits(execution_id)

                    if any(hard_limit_violations.values()):
                        # Hard limit exceeded - interrupt execution
                        violated_limits = [
                            limit.value
                            for limit, exceeded in hard_limit_violations.items()
                            if exceeded
                        ]
                        reason = f"Hard limit exceeded: {', '.join(violated_limits)}"
                        self.interrupt_execution(execution_id, reason)

                    # Check soft limits
                    soft_limit_violations = self.check_soft_limits(execution_id)

                    if any(soft_limit_violations.values()):
                        # Soft limit exceeded - log warning
                        violated_limits = [
                            limit.value
                            for limit, exceeded in soft_limit_violations.items()
                            if exceeded
                        ]
                        logger.warning(
                            f"Soft limit exceeded for execution {execution_id}: {', '.join(violated_limits)}"
                        )

                # Sleep before next check
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in execution monitoring: {e}")
                await asyncio.sleep(5)

    async def shutdown(self) -> None:
        """Shutdown the resource limit manager."""
        logger.info("Shutting down Resource Limit Manager")

        # Stop monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the resource limit manager is initialized."""
        return self._initialized


# Global instance
_resource_limit_manager: ResourceLimitManager | None = None


def get_resource_limit_manager() -> ResourceLimitManager:
    """Get the global resource limit manager instance."""
    global _resource_limit_manager
    if _resource_limit_manager is None:
        _resource_limit_manager = ResourceLimitManager()
    return _resource_limit_manager

"""
Tests for Resource Limits System
"""

from datetime import datetime

import pytest

from metamcp.security.resource_limits import (
    ExecutionContext,
    ExecutionStatus,
    LimitType,
    ResourceLimitManager,
    ResourceLimits,
    get_resource_limit_manager,
)


class TestResourceLimitManager:
    """Test Resource Limit Manager functionality."""

    @pytest.fixture
    async def resource_manager(self):
        """Create resource limit manager instance."""
        manager = ResourceLimitManager()
        await manager.initialize()
        yield manager
        await manager.shutdown()

    def test_start_execution(self, resource_manager):
        """Test starting an execution."""
        # Start execution
        execution_id = resource_manager.start_execution(
            tool_id="test_tool", user_id="user_123"
        )

        # Check execution was created
        assert execution_id is not None
        assert execution_id.startswith("exec_")

        # Check execution context
        context = resource_manager.active_executions[execution_id]
        assert context.tool_id == "test_tool"
        assert context.user_id == "user_123"
        assert context.status == ExecutionStatus.RUNNING
        assert context.start_time is not None

    def test_start_execution_with_custom_limits(self, resource_manager):
        """Test starting execution with custom limits."""
        custom_limits = ResourceLimits(
            cpu_time_soft=10,
            cpu_time_hard=20,
            memory_usage_soft=256,
            memory_usage_hard=512,
        )

        execution_id = resource_manager.start_execution(
            tool_id="test_tool", user_id="user_123", custom_limits=custom_limits
        )

        context = resource_manager.active_executions[execution_id]
        assert context.resource_limits.cpu_time_soft == 10
        assert context.resource_limits.cpu_time_hard == 20
        assert context.resource_limits.memory_usage_soft == 256
        assert context.resource_limits.memory_usage_hard == 512

    def test_end_execution(self, resource_manager):
        """Test ending an execution."""
        # Start execution
        execution_id = resource_manager.start_execution("test_tool", "user_123")

        # End execution
        success = resource_manager.end_execution(
            execution_id, ExecutionStatus.COMPLETED, "Success"
        )

        assert success is True

        # Check execution is no longer active
        assert execution_id not in resource_manager.active_executions

        # Check execution is in history
        assert len(resource_manager.execution_history) == 1
        history_item = resource_manager.execution_history[0]
        assert history_item.execution_id == execution_id
        assert history_item.status == ExecutionStatus.COMPLETED
        assert history_item.error_message == "Success"

    def test_update_execution_metrics(self, resource_manager):
        """Test updating execution metrics."""
        # Start execution
        execution_id = resource_manager.start_execution("test_tool", "user_123")

        # Update metrics
        success = resource_manager.update_execution_metrics(
            execution_id, cpu_time=15.5, memory_usage=256.0, api_calls=25
        )

        assert success is True

        # Check metrics were updated
        context = resource_manager.active_executions[execution_id]
        assert context.cpu_time == 15.5
        assert context.memory_usage == 256.0
        assert context.api_calls == 25

    def test_check_soft_limits(self, resource_manager):
        """Test soft limit checking."""
        # Start execution with low limits
        custom_limits = ResourceLimits(
            cpu_time_soft=10,
            cpu_time_hard=20,
            memory_usage_soft=100,
            memory_usage_hard=200,
        )

        execution_id = resource_manager.start_execution(
            "test_tool", "user_123", custom_limits
        )

        # Update metrics to exceed soft limits
        resource_manager.update_execution_metrics(
            execution_id,
            cpu_time=15.0,  # Exceeds soft limit of 10
            memory_usage=150.0,  # Exceeds soft limit of 100
        )

        # Check soft limits
        violations = resource_manager.check_soft_limits(execution_id)

        assert violations[LimitType.CPU_TIME] is True
        assert violations[LimitType.MEMORY_USAGE] is True
        assert violations[LimitType.EXECUTION_TIME] is False  # Not exceeded yet

    def test_check_hard_limits(self, resource_manager):
        """Test hard limit checking."""
        # Start execution with low limits
        custom_limits = ResourceLimits(
            cpu_time_soft=10,
            cpu_time_hard=20,
            memory_usage_soft=100,
            memory_usage_hard=200,
        )

        execution_id = resource_manager.start_execution(
            "test_tool", "user_123", custom_limits
        )

        # Update metrics to exceed hard limits
        resource_manager.update_execution_metrics(
            execution_id,
            cpu_time=25.0,  # Exceeds hard limit of 20
            memory_usage=250.0,  # Exceeds hard limit of 200
        )

        # Check hard limits
        violations = resource_manager.check_hard_limits(execution_id)

        assert violations[LimitType.CPU_TIME] is True
        assert violations[LimitType.MEMORY_USAGE] is True

    def test_interrupt_execution(self, resource_manager):
        """Test interrupting an execution."""
        # Start execution
        execution_id = resource_manager.start_execution("test_tool", "user_123")

        # Set up interrupt callback
        callback_called = False

        def interrupt_callback():
            nonlocal callback_called
            callback_called = True

        context = resource_manager.active_executions[execution_id]
        context.interrupt_callback = interrupt_callback

        # Interrupt execution
        success = resource_manager.interrupt_execution(
            execution_id, "Manual interruption"
        )

        assert success is True
        assert callback_called is True

        # Check execution was ended
        assert execution_id not in resource_manager.active_executions

        # Check execution is in history with interrupted status
        history_item = resource_manager.execution_history[0]
        assert history_item.status == ExecutionStatus.INTERRUPTED
        assert history_item.error_message == "Manual interruption"

    def test_get_execution_info(self, resource_manager):
        """Test getting execution information."""
        # Start execution
        execution_id = resource_manager.start_execution("test_tool", "user_123")

        # Update metrics
        resource_manager.update_execution_metrics(
            execution_id, cpu_time=15.0, memory_usage=256.0, api_calls=25
        )

        # Get execution info
        info = resource_manager.get_execution_info(execution_id)

        assert info is not None
        assert info["execution_id"] == execution_id
        assert info["tool_id"] == "test_tool"
        assert info["user_id"] == "user_123"
        assert info["status"] == ExecutionStatus.RUNNING.value
        assert info["cpu_time"] == 15.0
        assert info["memory_usage"] == 256.0
        assert info["api_calls"] == 25

    def test_list_active_executions(self, resource_manager):
        """Test listing active executions."""
        # Start multiple executions
        exec1 = resource_manager.start_execution("tool1", "user1")
        exec2 = resource_manager.start_execution("tool2", "user1")
        exec3 = resource_manager.start_execution("tool3", "user2")

        # List all active executions
        executions = resource_manager.list_active_executions()
        assert len(executions) == 3

        # List executions for specific user
        user1_executions = resource_manager.list_active_executions(user_id="user1")
        assert len(user1_executions) == 2
        assert all(exec_info["user_id"] == "user1" for exec_info in user1_executions)

    def test_list_execution_history(self, resource_manager):
        """Test listing execution history."""
        # Start and end multiple executions
        exec1 = resource_manager.start_execution("tool1", "user1")
        exec2 = resource_manager.start_execution("tool2", "user1")

        resource_manager.end_execution(exec1, ExecutionStatus.COMPLETED)
        resource_manager.end_execution(exec2, ExecutionStatus.FAILED, "Error")

        # List history
        history = resource_manager.list_execution_history()
        assert len(history) == 2

        # List history for specific user
        user1_history = resource_manager.list_execution_history(user_id="user1")
        assert len(user1_history) == 2
        assert all(exec_info["user_id"] == "user1" for exec_info in user1_history)

    def test_concurrent_executions_limit(self, resource_manager):
        """Test concurrent executions limit."""
        # Start multiple executions for same user
        for i in range(5):
            resource_manager.start_execution(f"tool{i}", "user1")

        # Check concurrent executions limit
        # Default soft limit is 5, hard limit is 10
        for execution_id in resource_manager.active_executions:
            violations = resource_manager.check_soft_limits(execution_id)
            # Should not exceed soft limit yet
            assert violations[LimitType.CONCURRENT_EXECUTIONS] is False

        # Start more executions to exceed soft limit
        for i in range(5, 8):
            resource_manager.start_execution(f"tool{i}", "user1")

        # Now should exceed soft limit
        for execution_id in resource_manager.active_executions:
            violations = resource_manager.check_soft_limits(execution_id)
            assert violations[LimitType.CONCURRENT_EXECUTIONS] is True

    def test_global_instance(self):
        """Test global resource limit manager instance."""
        # Get global instance
        manager1 = get_resource_limit_manager()
        manager2 = get_resource_limit_manager()

        # Should be the same instance
        assert manager1 is manager2


class TestResourceLimits:
    """Test ResourceLimits model."""

    def test_default_limits(self):
        """Test default resource limits."""
        limits = ResourceLimits()

        assert limits.cpu_time_soft == 30
        assert limits.cpu_time_hard == 60
        assert limits.memory_usage_soft == 512
        assert limits.memory_usage_hard == 1024
        assert limits.execution_time_soft == 300
        assert limits.execution_time_hard == 600
        assert limits.api_calls_soft == 100
        assert limits.api_calls_hard == 200
        assert limits.concurrent_executions_soft == 5
        assert limits.concurrent_executions_hard == 10

    def test_custom_limits(self):
        """Test custom resource limits."""
        limits = ResourceLimits(
            cpu_time_soft=10,
            cpu_time_hard=20,
            memory_usage_soft=100,
            memory_usage_hard=200,
            execution_time_soft=60,
            execution_time_hard=120,
            api_calls_soft=50,
            api_calls_hard=100,
            concurrent_executions_soft=2,
            concurrent_executions_hard=5,
        )

        assert limits.cpu_time_soft == 10
        assert limits.cpu_time_hard == 20
        assert limits.memory_usage_soft == 100
        assert limits.memory_usage_hard == 200
        assert limits.execution_time_soft == 60
        assert limits.execution_time_hard == 120
        assert limits.api_calls_soft == 50
        assert limits.api_calls_hard == 100
        assert limits.concurrent_executions_soft == 2
        assert limits.concurrent_executions_hard == 5


class TestExecutionContext:
    """Test ExecutionContext model."""

    def test_execution_context_creation(self):
        """Test ExecutionContext object creation."""
        context = ExecutionContext(
            execution_id="exec_123",
            tool_id="test_tool",
            user_id="user_123",
            start_time=datetime.utcnow(),
            status=ExecutionStatus.RUNNING,
            cpu_time=15.0,
            memory_usage=256.0,
            api_calls=25,
        )

        assert context.execution_id == "exec_123"
        assert context.tool_id == "test_tool"
        assert context.user_id == "user_123"
        assert context.status == ExecutionStatus.RUNNING
        assert context.cpu_time == 15.0
        assert context.memory_usage == 256.0
        assert context.api_calls == 25

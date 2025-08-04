"""
Circuit Breaker Tests

Tests for circuit breaker pattern implementation.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

from metamcp.performance.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerManager,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_initial_state(self):
        """Test circuit breaker initial state."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
    
    def test_successful_call(self):
        """Test successful function call."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.successful_requests == 1
    
    def test_failed_call(self):
        """Test failed function call."""
        config = CircuitBreakerConfig(name="test", failure_threshold=2)
        cb = CircuitBreaker(config)
        
        def fail_func():
            raise ValueError("test error")
        
        # First failure
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2
    
    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(name="test", failure_threshold=3)
        cb = CircuitBreaker(config)
        
        def fail_func():
            raise RuntimeError("test error")
        
        # Fail 3 times
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Next call should be rejected immediately
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "should not be called")
    
    def test_circuit_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        config = CircuitBreakerConfig(
            name="test",
            failure_threshold=1,
            recovery_timeout=1  # 1 second timeout
        )
        cb = CircuitBreaker(config)
        
        # Fail once to open circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Next call should transition to half-open
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_circuit_closes_after_success_threshold(self):
        """Test circuit closes after success threshold in half-open state."""
        config = CircuitBreakerConfig(
            name="test",
            failure_threshold=1,
            recovery_timeout=1,
            success_threshold=2
        )
        cb = CircuitBreaker(config)
        
        # Open circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Two successful calls should close circuit
        for _ in range(2):
            cb.call(lambda: "success")
        
        assert cb.state == CircuitState.CLOSED
        assert cb.success_count == 0  # Reset after closing
    
    def test_circuit_reopens_on_failure_in_half_open(self):
        """Test circuit reopens on failure in half-open state."""
        config = CircuitBreakerConfig(
            name="test",
            failure_threshold=1,
            recovery_timeout=1
        )
        cb = CircuitBreaker(config)
        
        # Open circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Failure in half-open should reopen circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        assert cb.state == CircuitState.OPEN
    
    def test_async_function_support(self):
        """Test async function support."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        async def async_success_func():
            await asyncio.sleep(0.01)
            return "async success"
        
        async def async_fail_func():
            await asyncio.sleep(0.01)
            raise ValueError("async error")
        
        # Test successful async call
        result = asyncio.run(cb.call_async(async_success_func))
        assert result == "async success"
        assert cb.state == CircuitState.CLOSED
        
        # Test failed async call
        with pytest.raises(ValueError):
            asyncio.run(cb.call_async(async_fail_func))
    
    def test_context_manager(self):
        """Test context manager usage."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        async def test_context():
            async with cb.context():
                return "context success"
        
        result = asyncio.run(test_context())
        assert result == "context success"
        assert cb.successful_requests == 1
    
    def test_metrics(self):
        """Test metrics collection."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        # Successful calls
        for _ in range(5):
            cb.call(lambda: "success")
        
        # Failed calls
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        metrics = cb.get_metrics()
        
        assert metrics["name"] == "test"
        assert metrics["total_requests"] == 7
        assert metrics["successful_requests"] == 5
        assert metrics["failed_requests"] == 2
        assert metrics["failure_rate"] == 2 / 7
    
    def test_manual_reset(self):
        """Test manual circuit breaker reset."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        # Open circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        assert cb.state == CircuitState.OPEN
        
        # Manual reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_force_open(self):
        """Test forcing circuit breaker to open state."""
        config = CircuitBreakerConfig(name="test")
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitState.CLOSED
        
        cb.force_open()
        assert cb.state == CircuitState.OPEN
        
        # Should reject calls
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "should not be called")


class TestCircuitBreakerManager:
    """Test circuit breaker manager."""
    
    def test_get_circuit_breaker(self):
        """Test getting circuit breaker from manager."""
        manager = CircuitBreakerManager()
        
        cb1 = manager.get_circuit_breaker("test1")
        cb2 = manager.get_circuit_breaker("test2")
        cb3 = manager.get_circuit_breaker("test1")  # Should return same instance
        
        assert cb1 is not cb2
        assert cb1 is cb3
        assert cb1.config.name == "test1"
        assert cb2.config.name == "test2"
    
    def test_get_circuit_breaker_with_config(self):
        """Test getting circuit breaker with custom config."""
        manager = CircuitBreakerManager()
        
        config = CircuitBreakerConfig(
            name="custom",
            failure_threshold=5,
            recovery_timeout=30
        )
        
        cb = manager.get_circuit_breaker("custom", config)
        assert cb.config.failure_threshold == 5
        assert cb.config.recovery_timeout == 30
    
    async def test_get_circuit_breaker_async(self):
        """Test async circuit breaker retrieval."""
        manager = CircuitBreakerManager()
        
        cb1 = await manager.get_circuit_breaker_async("async_test")
        cb2 = await manager.get_circuit_breaker_async("async_test")
        
        assert cb1 is cb2
    
    def test_get_all_metrics(self):
        """Test getting metrics from all circuit breakers."""
        manager = CircuitBreakerManager()
        
        # Create some circuit breakers
        cb1 = manager.get_circuit_breaker("test1")
        cb2 = manager.get_circuit_breaker("test2")
        
        # Make some calls
        cb1.call(lambda: "success")
        cb2.call(lambda: "success")
        
        metrics = manager.get_all_metrics()
        
        assert "test1" in metrics
        assert "test2" in metrics
        assert metrics["test1"]["total_requests"] == 1
        assert metrics["test2"]["total_requests"] == 1
    
    def test_reset_all(self):
        """Test resetting all circuit breakers."""
        manager = CircuitBreakerManager()
        
        # Create and open some circuit breakers
        cb1 = manager.get_circuit_breaker("test1")
        cb2 = manager.get_circuit_breaker("test2")
        
        # Open circuits
        with pytest.raises(ValueError):
            cb1.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        with pytest.raises(ValueError):
            cb2.call(lambda: (_ for _ in ()).throw(ValueError("test")))
        
        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.OPEN
        
        # Reset all
        manager.reset_all()
        
        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED
    
    def test_force_open_all(self):
        """Test forcing all circuit breakers to open."""
        manager = CircuitBreakerManager()
        
        # Create circuit breakers
        cb1 = manager.get_circuit_breaker("test1")
        cb2 = manager.get_circuit_breaker("test2")
        
        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED
        
        # Force open all
        manager.force_open_all()
        
        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.OPEN


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator."""
    
    def test_sync_decorator(self):
        """Test circuit breaker decorator with sync function."""
        from metamcp.performance.circuit_breaker import circuit_breaker
        
        @circuit_breaker("test_decorator")
        def test_func():
            return "decorated success"
        
        result = test_func()
        assert result == "decorated success"
    
    def test_async_decorator(self):
        """Test circuit breaker decorator with async function."""
        from metamcp.performance.circuit_breaker import circuit_breaker
        
        @circuit_breaker("test_async_decorator")
        async def async_test_func():
            await asyncio.sleep(0.01)
            return "async decorated success"
        
        result = asyncio.run(async_test_func())
        assert result == "async decorated success"
    
    def test_decorator_with_failures(self):
        """Test circuit breaker decorator with failures."""
        from metamcp.performance.circuit_breaker import circuit_breaker
        
        @circuit_breaker("test_failure_decorator", failure_threshold=2)
        def failing_func():
            raise RuntimeError("decorated failure")
        
        # First failure
        with pytest.raises(RuntimeError):
            failing_func()
        
        # Second failure should open circuit
        with pytest.raises(RuntimeError):
            failing_func()
        
        # Third call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            failing_func()


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker."""
    
    def test_real_world_scenario(self):
        """Test realistic circuit breaker scenario."""
        config = CircuitBreakerConfig(
            name="integration_test",
            failure_threshold=3,
            recovery_timeout=2,
            success_threshold=2
        )
        cb = CircuitBreaker(config)
        
        # Simulate service that fails intermittently
        call_count = 0
        
        def unreliable_service():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise ConnectionError("Service unavailable")
            return "Service working"
        
        # First 3 calls should fail and open circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                cb.call(unreliable_service)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(2.1)
        
        # Next call should be in half-open state and succeed
        result = cb.call(unreliable_service)
        assert result == "Service working"
        assert cb.state == CircuitState.HALF_OPEN
        
        # Another successful call should close circuit
        result = cb.call(unreliable_service)
        assert result == "Service working"
        assert cb.state == CircuitState.CLOSED
    
    def test_concurrent_access(self):
        """Test circuit breaker with concurrent access."""
        config = CircuitBreakerConfig(name="concurrent_test")
        cb = CircuitBreaker(config)
        
        def slow_function():
            time.sleep(0.1)
            return "slow success"
        
        # Run multiple concurrent calls
        import threading
        
        results = []
        threads = []
        
        def worker():
            try:
                result = cb.call(slow_function)
                results.append(result)
            except Exception as e:
                results.append(e)
        
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All calls should succeed
        assert len(results) == 5
        assert all(r == "slow success" for r in results)
        assert cb.total_requests == 5
"""
Circuit Breaker Implementation

This module provides a circuit breaker pattern implementation for external service calls,
with configurable failure thresholds, recovery strategies, and monitoring capabilities.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening circuit
    recovery_timeout: int = 60  # Seconds to wait before trying half-open
    expected_exception: type = Exception  # Exception type to count as failure
    success_threshold: int = 2  # Number of successes to close circuit again
    monitor_interval: float = 5.0  # Monitoring interval (ignored in utils impl)


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    current_state: CircuitState = CircuitState.CLOSED
    # Added rejected requests to align with tests expecting this metric
    rejected_requests: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.

    Provides fault tolerance by monitoring failures and temporarily
    stopping calls to failing services.
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
        on_state_change: Callable[[str, CircuitState], None] | None = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name for identification
            config: Configuration parameters
            on_state_change: Callback for state changes
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change

        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_success_time = None
        self._lock = asyncio.Lock()

        # Statistics
        self.stats = CircuitBreakerStats()

        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    # Expose test-friendly metrics similar to performance variant
    @property
    def total_requests(self) -> int:
        return self.stats.total_calls

    @property
    def successful_requests(self) -> int:
        return self.stats.successful_calls

    @property
    def failed_requests(self) -> int:
        return self.stats.failed_calls

    @property
    def rejected_requests(self) -> int:
        return self.stats.rejected_requests

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def last_failure_time(self) -> float | None:
        return self._last_failure_time

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self._state == CircuitState.HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original function exception
        """
        async with self._lock:
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    await self._set_state(CircuitState.HALF_OPEN)
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
                else:
                    # Track rejected
                    self.stats.total_calls += 1
                    self.stats.rejected_requests += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Last failure: {self._last_failure_time}"
                    )

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - update state
            await self._on_success()
            return result

        except self.config.expected_exception:
            # Failure - update state
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self._failure_count = 0
            self._success_count += 1
            self._last_success_time = time.time()

            # Update statistics
            self.stats.total_calls += 1
            self.stats.successful_calls += 1
            self.stats.last_success_time = self._last_success_time

            # Close circuit if in half-open state
            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self.config.success_threshold:
                    await self._set_state(CircuitState.CLOSED)
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED")

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            # Update statistics
            self.stats.total_calls += 1
            self.stats.failed_calls += 1
            self.stats.last_failure_time = self._last_failure_time

            # Open circuit if threshold reached
            if self._failure_count >= self.config.failure_threshold:
                if self._state != CircuitState.OPEN:
                    await self._set_state(CircuitState.OPEN)
                    logger.warning(
                        f"Circuit breaker '{self.name}' opened after "
                        f"{self._failure_count} failures"
                    )

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if not self._last_failure_time:
            return False

        return (time.time() - self._last_failure_time) >= self.config.recovery_timeout

    async def _set_state(self, new_state: CircuitState) -> None:
        """Set circuit state and trigger callback."""
        if self._state != new_state:
            self._state = new_state
            self.stats.current_state = new_state

            # Trigger callback if provided
            if self.on_state_change:
                try:
                    self.on_state_change(self.name, new_state)
                except Exception as e:
                    logger.error(f"Error in circuit breaker state change callback: {e}")

    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self.stats

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self.stats.current_state = CircuitState.CLOSED
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.

    Provides centralized management and monitoring of circuit breakers.
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    # Synchronous API expected by tests
    def get_circuit_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(
                name=name,
                config=config,
                on_state_change=self._on_state_change,
            )
        return self._circuit_breakers[name]

    async def get_circuit_breaker_async(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """Async variant for compatibility."""
        async with self._lock:
            return self.get_circuit_breaker(name, config)

    def _on_state_change(self, name: str, state: CircuitState) -> None:
        """Handle circuit breaker state changes."""
        logger.info(f"Circuit breaker '{name}' state changed to {state.value}")

    # Additional APIs expected by tests
    @property
    def circuit_breakers(self) -> dict[str, CircuitBreaker]:
        return self._circuit_breakers

    def remove_circuit_breaker(self, name: str) -> bool:
        if name in self._circuit_breakers:
            del self._circuit_breakers[name]
            return True
        return False

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        states: dict[str, dict[str, Any]] = {}
        for name, cb in self._circuit_breakers.items():
            states[name] = {
                "name": name,
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "success_count": cb.success_count,
                "last_failure_time": cb.last_failure_time,
            }
        return states

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._circuit_breakers)
        open_circuits = sum(1 for cb in self._circuit_breakers.values() if cb.state == CircuitState.OPEN)
        half_open_circuits = sum(1 for cb in self._circuit_breakers.values() if cb.state == CircuitState.HALF_OPEN)
        closed_circuits = total - open_circuits - half_open_circuits
        agg = {
            "total_circuit_breakers": total,
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "closed_circuits": closed_circuits,
            "total_requests": sum(cb.total_requests for cb in self._circuit_breakers.values()),
            "total_successful": sum(cb.successful_requests for cb in self._circuit_breakers.values()),
            "total_failed": sum(cb.failed_requests for cb in self._circuit_breakers.values()),
            "total_rejected": sum(cb.rejected_requests for cb in self._circuit_breakers.values()),
            "monitoring_active": True,
        }
        # Compute success rate
        total_req = agg["total_requests"]
        agg["overall_success_rate"] = (
            agg["total_successful"] / total_req if total_req > 0 else 0.0
        )
        return agg

    async def get_all_stats(self) -> dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        return {name: cb.get_stats() for name, cb in self._circuit_breakers.items()}

    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self._circuit_breakers.values():
            cb.reset()

    async def close(self) -> None:
        """Close circuit breaker manager."""
        await self.reset_all()
        self._circuit_breakers.clear()


# Global circuit breaker manager instance
_circuit_breaker_manager: CircuitBreakerManager | None = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager instance."""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager


async def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig | None = None,
) -> CircuitBreaker:
    """
    Get circuit breaker by name.

    Args:
        name: Circuit breaker name
        config: Configuration (only used for new instances)

    Returns:
        Circuit breaker instance
    """
    manager = get_circuit_breaker_manager()
    return await manager.get_circuit_breaker_async(name, config)

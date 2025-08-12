"""
Circuit Breaker Pattern Implementation

This module provides a circuit breaker pattern implementation for handling
failures gracefully and preventing cascading failures in distributed systems.
"""

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

from ..config import get_settings
from ..utils.logging import get_logger
from ..utils.constants import (
    DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    DEFAULT_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    DEFAULT_CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
)

logger = get_logger(__name__)
settings = get_settings()


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD
    recovery_timeout: int = DEFAULT_CIRCUIT_BREAKER_RECOVERY_TIMEOUT
    success_threshold: int = DEFAULT_CIRCUIT_BREAKER_SUCCESS_THRESHOLD
    expected_exception: type = Exception
    name: str = "default"


class CircuitBreaker:
    """
    Circuit Breaker implementation for handling failures gracefully.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, all requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()

        # Metrics
        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0
        self.rejected_requests = 0

        logger.info(f"Circuit breaker '{config.name}' initialized")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.state != CircuitState.OPEN:
            return False

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful request."""
        self.success_count += 1
        self.successful_requests += 1

        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed request."""
        self.failure_count += 1
        self.failed_requests += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition circuit breaker to OPEN state."""
        if self.state != CircuitState.OPEN:
            logger.warning(
                f"Circuit breaker '{self.config.name}' transitioning to OPEN state "
                f"(failures: {self.failure_count})"
            )
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.success_count = 0

    def _transition_to_half_open(self) -> None:
        """Transition circuit breaker to HALF_OPEN state."""
        if self.state != CircuitState.HALF_OPEN:
            logger.info(
                f"Circuit breaker '{self.config.name}' transitioning to HALF_OPEN state"
            )
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0

    def _transition_to_closed(self) -> None:
        """Transition circuit breaker to CLOSED state."""
        if self.state != CircuitState.CLOSED:
            logger.info(
                f"Circuit breaker '{self.config.name}' transitioning to CLOSED state"
            )
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
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
            Exception: Original exception from function
        """
        self.total_requests += 1

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.config.name}' is OPEN"
                )

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        self.total_requests += 1

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.config.name}' is OPEN"
                )

        # Execute function
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    @asynccontextmanager
    async def context(self):
        """
        Context manager for circuit breaker.

        Usage:
            async with circuit_breaker.context():
                # Your code here
                result = await some_operation()
        """
        self.total_requests += 1

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.config.name}' is OPEN"
                )

        try:
            yield
            self._on_success()
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "successful_requests": self.successful_requests,
            "rejected_requests": self.rejected_requests,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "failure_rate": (
                self.failed_requests / self.total_requests
                if self.total_requests > 0
                else 0
            ),
        }

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(f"Circuit breaker '{self.config.name}' manually reset")
        self._transition_to_closed()

    def force_open(self) -> None:
        """Force circuit breaker to OPEN state."""
        logger.warning(f"Circuit breaker '{self.config.name}' forced to OPEN state")
        self._transition_to_open()


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_circuit_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker.

        Args:
            name: Circuit breaker name
            config: Circuit breaker configuration

        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig(name=name)
            self.circuit_breakers[name] = CircuitBreaker(config)

        return self.circuit_breakers[name]

    async def get_circuit_breaker_async(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker (async version).

        Args:
            name: Circuit breaker name
            config: Circuit breaker configuration

        Returns:
            Circuit breaker instance
        """
        async with self._lock:
            return self.get_circuit_breaker(name, config)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        return {name: cb.get_metrics() for name, cb in self.circuit_breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()

    def force_open_all(self) -> None:
        """Force all circuit breakers to OPEN state."""
        for cb in self.circuit_breakers.values():
            cb.force_open()


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    failure_threshold: int = DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    recovery_timeout: int = DEFAULT_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    success_threshold: int = DEFAULT_CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
    expected_exception: type = Exception,
):
    """
    Decorator for circuit breaker pattern.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting half-open
        success_threshold: Number of successes to close circuit
        expected_exception: Exception type to consider as failure

    Returns:
        Decorated function
    """

    def decorator(func):
        config = CircuitBreakerConfig(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            expected_exception=expected_exception,
        )

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                cb = circuit_breaker_manager.get_circuit_breaker(name, config)
                return await cb.call_async(func, *args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                cb = circuit_breaker_manager.get_circuit_breaker(name, config)
                return cb.call(func, *args, **kwargs)

            return sync_wrapper

    return decorator

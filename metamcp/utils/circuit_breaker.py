"""
Circuit Breaker Pattern

Implementation of the circuit breaker pattern for handling failures
gracefully and preventing cascading failures.
"""

import asyncio
import time
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar
from dataclasses import dataclass

from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    expected_exception: type = Exception
    monitor_interval: float = 10.0  # seconds


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    The circuit breaker pattern helps prevent cascading failures by
    monitoring for failures and temporarily stopping execution when
    a threshold is reached.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            config: Configuration options
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rejected_requests = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
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
        self.total_requests += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open"
                )
        
        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            # Failure - increment failure count
            self._on_failure()
            raise e
        except Exception as e:
            # Unexpected exception - still count as failure
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful execution."""
        self.successful_requests += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_closed()
        
        logger.debug(f"Circuit breaker '{self.name}' success")

    def _on_failure(self):
        """Handle failed execution."""
        self.failed_requests += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self._transition_to_open()
        
        logger.warning(f"Circuit breaker '{self.name}' failure: {self.failure_count}/{self.config.failure_threshold}")

    def _transition_to_open(self):
        """Transition to open state."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            logger.warning(f"Circuit breaker '{self.name}' opened")

    def _transition_to_closed(self):
        """Transition to closed state."""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            logger.info(f"Circuit breaker '{self.name}' closed")

    def _transition_to_half_open(self):
        """Transition to half-open state."""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            logger.info(f"Circuit breaker '{self.name}' half-open")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self.last_failure_time is None:
            return False
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout

    def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state.
        
        Returns:
            Dictionary with state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.config.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rejected_requests": self.rejected_requests,
            "success_rate": self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
        }

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
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
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self._stop_monitoring = False

    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Configuration options
            
        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        
        return self.circuit_breakers[name]

    def remove_circuit_breaker(self, name: str) -> bool:
        """
        Remove a circuit breaker.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            True if removed, False if not found
        """
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            logger.info(f"Circuit breaker '{name}' removed")
            return True
        return False

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get states of all circuit breakers.
        
        Returns:
            Dictionary mapping circuit breaker names to their states
        """
        return {
            name: cb.get_state()
            for name, cb in self.circuit_breakers.items()
        }

    def start_monitoring(self):
        """Start monitoring circuit breakers."""
        if self.monitoring_task is None or self.monitoring_task.done():
            self._stop_monitoring = False
            self.monitoring_task = asyncio.create_task(self._monitor_loop())
            logger.info("Circuit breaker monitoring started")

    def stop_monitoring(self):
        """Stop monitoring circuit breakers."""
        self._stop_monitoring = True
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
        logger.info("Circuit breaker monitoring stopped")

    async def _monitor_loop(self):
        """Monitoring loop for circuit breakers."""
        while not self._stop_monitoring:
            try:
                # Check all circuit breakers
                for name, cb in self.circuit_breakers.items():
                    state = cb.get_state()
                    
                    # Log state changes
                    if state["state"] == "open":
                        logger.warning(f"Circuit breaker '{name}' is open")
                    elif state["state"] == "half_open":
                        logger.info(f"Circuit breaker '{name}' is half-open")
                    
                    # Check for stuck half-open state
                    if (state["state"] == "half_open" and 
                        (time.time() - state["last_state_change"]) > cb.config.monitor_interval):
                        logger.warning(f"Circuit breaker '{name}' stuck in half-open state")
                
                # Wait before next check
                await asyncio.sleep(self.config.monitor_interval if hasattr(self, 'config') else 10.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Circuit breaker monitoring error: {e}")
                await asyncio.sleep(1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics.
        
        Returns:
            Dictionary with overall statistics
        """
        total_requests = sum(cb.total_requests for cb in self.circuit_breakers.values())
        total_successful = sum(cb.successful_requests for cb in self.circuit_breakers.values())
        total_failed = sum(cb.failed_requests for cb in self.circuit_breakers.values())
        total_rejected = sum(cb.rejected_requests for cb in self.circuit_breakers.values())
        
        open_circuits = sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN)
        half_open_circuits = sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.HALF_OPEN)
        
        return {
            "total_circuit_breakers": len(self.circuit_breakers),
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "closed_circuits": len(self.circuit_breakers) - open_circuits - half_open_circuits,
            "total_requests": total_requests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "total_rejected": total_rejected,
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0.0,
            "monitoring_active": self.monitoring_task is not None and not self.monitoring_task.done()
        }


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator for circuit breaker protection.
    
    Args:
        name: Circuit breaker name
        config: Configuration options
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cb = circuit_breaker_manager.get_circuit_breaker(name, config)
        
        async def async_wrapper(*args, **kwargs) -> T:
            return await cb.call(func, *args, **kwargs)
        
        def sync_wrapper(*args, **kwargs) -> T:
            return cb.call(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 
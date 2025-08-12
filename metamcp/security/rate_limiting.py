"""
Advanced Rate Limiting

This module provides advanced rate limiting capabilities with multiple strategies,
configurable limits, and detailed monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..exceptions import RateLimitExceededError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    key: str
    limit: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    burst_limit: Optional[int] = None
    cost_per_request: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Rate limit state for tracking."""

    key: str
    current_count: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)
    last_request: datetime = field(default_factory=datetime.utcnow)
    tokens: float = 0.0
    burst_tokens: float = 0.0


@dataclass
class RateLimitResult:
    """Rate limit check result."""

    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    limit: int
    window_seconds: int
    cost_used: int = 1


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies.

    This class provides comprehensive rate limiting capabilities with
    support for different algorithms and detailed monitoring.
    """

    def __init__(self):
        """Initialize the rate limiter."""
        self.limiters: Dict[str, RateLimitConfig] = {}
        self.states: Dict[str, RateLimitState] = {}
        self.global_config: Dict[str, Any] = {
            "default_limit": 100,
            "default_window": 60,
            "default_strategy": RateLimitStrategy.FIXED_WINDOW,
            "enable_monitoring": True,
            "cleanup_interval": 3600,  # 1 hour
        }

        # Statistics
        self.stats: Dict[str, Dict[str, Any]] = {}

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> None:
        """Initialize the rate limiter."""
        try:
            logger.info("Initializing Rate Limiter")

            # Start cleanup task
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("Rate Limiter initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Rate Limiter: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the rate limiter."""
        try:
            logger.info("Shutting down Rate Limiter")

            self._running = False
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            logger.info("Rate Limiter shutdown complete")

        except Exception as e:
            logger.error(f"Error during rate limiter shutdown: {e}")

    async def add_rate_limit(self, config: RateLimitConfig) -> None:
        """
        Add a rate limit configuration.

        Args:
            config: Rate limit configuration
        """
        try:
            self.limiters[config.key] = config

            # Initialize state if not exists
            if config.key not in self.states:
                self.states[config.key] = RateLimitState(
                    key=config.key,
                    tokens=(
                        config.limit
                        if config.strategy == RateLimitStrategy.TOKEN_BUCKET
                        else 0
                    ),
                    burst_tokens=config.burst_limit or config.limit,
                )

            # Initialize statistics
            if config.key not in self.stats:
                self.stats[config.key] = {
                    "total_requests": 0,
                    "allowed_requests": 0,
                    "blocked_requests": 0,
                    "total_cost": 0,
                    "last_reset": datetime.utcnow(),
                }

            logger.info(
                f"Added rate limit: {config.key} ({config.limit}/{config.window_seconds}s)"
            )

        except Exception as e:
            logger.error(f"Failed to add rate limit: {e}")
            raise

    async def check_rate_limit(
        self, key: str, cost: int = 1, context: Optional[Dict[str, Any]] = None
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Rate limit key
            cost: Cost of the request
            context: Additional context

        Returns:
            Rate limit result
        """
        try:
            if key not in self.limiters:
                # Use default configuration
                config = RateLimitConfig(
                    key=key,
                    limit=self.global_config["default_limit"],
                    window_seconds=self.global_config["default_window"],
                    strategy=self.global_config["default_strategy"],
                )
                await self.add_rate_limit(config)

            config = self.limiters[key]
            state = self.states[key]

            # Update statistics
            self.stats[key]["total_requests"] += 1
            self.stats[key]["total_cost"] += cost

            # Check rate limit based on strategy
            if config.strategy == RateLimitStrategy.FIXED_WINDOW:
                result = await self._check_fixed_window(config, state, cost)
            elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                result = await self._check_sliding_window(config, state, cost)
            elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                result = await self._check_token_bucket(config, state, cost)
            elif config.strategy == RateLimitStrategy.LEAKY_BUCKET:
                result = await self._check_leaky_bucket(config, state, cost)
            else:
                raise ValueError(f"Unsupported rate limit strategy: {config.strategy}")

            # Update statistics
            if result.allowed:
                self.stats[key]["allowed_requests"] += 1
            else:
                self.stats[key]["blocked_requests"] += 1

            # Update last request time
            state.last_request = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Default to allowing the request if there's an error
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_time=datetime.utcnow() + timedelta(seconds=60),
                limit=0,
                window_seconds=60,
            )

    async def _check_fixed_window(
        self, config: RateLimitConfig, state: RateLimitState, cost: int
    ) -> RateLimitResult:
        """Check rate limit using fixed window strategy."""
        now = datetime.utcnow()
        window_start = now.replace(second=0, microsecond=0)

        # Reset window if needed
        if state.window_start < window_start:
            state.current_count = 0
            state.window_start = window_start

        # Check if request is allowed
        if state.current_count + cost <= config.limit:
            state.current_count += cost
            remaining = config.limit - state.current_count
            reset_time = state.window_start + timedelta(seconds=config.window_seconds)

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=reset_time,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )
        else:
            remaining = max(0, config.limit - state.current_count)
            reset_time = state.window_start + timedelta(seconds=config.window_seconds)
            retry_after = int((reset_time - now).total_seconds())

            return RateLimitResult(
                allowed=False,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )

    async def _check_sliding_window(
        self, config: RateLimitConfig, state: RateLimitState, cost: int
    ) -> RateLimitResult:
        """Check rate limit using sliding window strategy."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=config.window_seconds)

        # Remove expired requests (simplified implementation)
        # In a real implementation, you'd use a more sophisticated data structure
        if state.last_request < window_start:
            state.current_count = 0

        # Check if request is allowed
        if state.current_count + cost <= config.limit:
            state.current_count += cost
            remaining = config.limit - state.current_count
            reset_time = now + timedelta(seconds=config.window_seconds)

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=reset_time,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )
        else:
            remaining = max(0, config.limit - state.current_count)
            reset_time = now + timedelta(seconds=config.window_seconds)
            retry_after = config.window_seconds

            return RateLimitResult(
                allowed=False,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )

    async def _check_token_bucket(
        self, config: RateLimitConfig, state: RateLimitState, cost: int
    ) -> RateLimitResult:
        """Check rate limit using token bucket strategy."""
        now = datetime.utcnow()

        # Refill tokens
        time_passed = (now - state.last_request).total_seconds()
        tokens_to_add = time_passed * (config.limit / config.window_seconds)
        state.tokens = min(config.limit, state.tokens + tokens_to_add)

        # Check if request is allowed
        if state.tokens >= cost:
            state.tokens -= cost
            remaining = int(state.tokens)
            reset_time = now + timedelta(seconds=config.window_seconds)

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=reset_time,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )
        else:
            remaining = int(state.tokens)
            reset_time = now + timedelta(seconds=config.window_seconds)
            retry_after = int(
                (cost - state.tokens) / (config.limit / config.window_seconds)
            )

            return RateLimitResult(
                allowed=False,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )

    async def _check_leaky_bucket(
        self, config: RateLimitConfig, state: RateLimitState, cost: int
    ) -> RateLimitResult:
        """Check rate limit using leaky bucket strategy."""
        now = datetime.utcnow()

        # Leak tokens (simulate processing)
        time_passed = (now - state.last_request).total_seconds()
        tokens_leaked = time_passed * (config.limit / config.window_seconds)
        state.tokens = max(0, state.tokens - tokens_leaked)

        # Check if request is allowed
        if state.tokens + cost <= config.limit:
            state.tokens += cost
            remaining = config.limit - state.tokens
            reset_time = now + timedelta(seconds=config.window_seconds)

            return RateLimitResult(
                allowed=True,
                remaining=int(remaining),
                reset_time=reset_time,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )
        else:
            remaining = config.limit - state.tokens
            reset_time = now + timedelta(seconds=config.window_seconds)
            retry_after = int(
                (cost - remaining) / (config.limit / config.window_seconds)
            )

            return RateLimitResult(
                allowed=False,
                remaining=int(remaining),
                reset_time=reset_time,
                retry_after=retry_after,
                limit=config.limit,
                window_seconds=config.window_seconds,
                cost_used=cost,
            )

    async def reset_rate_limit(self, key: str) -> bool:
        """
        Reset rate limit for a key.

        Args:
            key: Rate limit key

        Returns:
            True if reset successfully
        """
        try:
            if key in self.states:
                state = self.states[key]
                state.current_count = 0
                state.tokens = 0
                state.window_start = datetime.utcnow()
                state.last_request = datetime.utcnow()

                # Reset statistics
                if key in self.stats:
                    self.stats[key]["last_reset"] = datetime.utcnow()

                logger.info(f"Reset rate limit for key: {key}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    async def get_rate_limit_status(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get rate limit status for a key.

        Args:
            key: Rate limit key

        Returns:
            Rate limit status or None if not found
        """
        try:
            if key not in self.limiters or key not in self.states:
                return None

            config = self.limiters[key]
            state = self.states[key]
            stats = self.stats.get(key, {})

            return {
                "key": key,
                "limit": config.limit,
                "window_seconds": config.window_seconds,
                "strategy": config.strategy.value,
                "current_count": state.current_count,
                "tokens": state.tokens,
                "window_start": state.window_start.isoformat(),
                "last_request": state.last_request.isoformat(),
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return None

    async def get_all_rate_limits(self) -> List[Dict[str, Any]]:
        """
        Get status of all rate limits.

        Returns:
            List of rate limit statuses
        """
        try:
            statuses = []
            for key in self.limiters.keys():
                status = await self.get_rate_limit_status(key)
                if status:
                    statuses.append(status)
            return statuses

        except Exception as e:
            logger.error(f"Failed to get all rate limits: {e}")
            return []

    async def remove_rate_limit(self, key: str) -> bool:
        """
        Remove a rate limit configuration.

        Args:
            key: Rate limit key

        Returns:
            True if removed successfully
        """
        try:
            if key in self.limiters:
                del self.limiters[key]

            if key in self.states:
                del self.states[key]

            if key in self.stats:
                del self.stats[key]

            logger.info(f"Removed rate limit: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove rate limit: {e}")
            return False

    async def _cleanup_loop(self) -> None:
        """Cleanup loop for expired rate limit states."""
        while self._running:
            try:
                await asyncio.sleep(self.global_config["cleanup_interval"])
                await self._cleanup_expired_states()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_expired_states(self) -> None:
        """Clean up expired rate limit states."""
        try:
            now = datetime.utcnow()
            expired_keys = []

            for key, state in self.states.items():
                # Remove states that haven't been used for a long time
                if (now - state.last_request).total_seconds() > 86400:  # 24 hours
                    expired_keys.append(key)

            for key in expired_keys:
                await self.remove_rate_limit(key)

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired rate limit states")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.

        Returns:
            Statistics dictionary
        """
        try:
            total_requests = sum(
                stats.get("total_requests", 0) for stats in self.stats.values()
            )
            allowed_requests = sum(
                stats.get("allowed_requests", 0) for stats in self.stats.values()
            )
            blocked_requests = sum(
                stats.get("blocked_requests", 0) for stats in self.stats.values()
            )

            return {
                "total_rate_limits": len(self.limiters),
                "total_requests": total_requests,
                "allowed_requests": allowed_requests,
                "blocked_requests": blocked_requests,
                "success_rate": (
                    (allowed_requests / total_requests * 100)
                    if total_requests > 0
                    else 0
                ),
                "rate_limits": await self.get_all_rate_limits(),
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


class RateLimitMiddleware:
    """
    Middleware for applying rate limiting to requests.
    """

    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize rate limit middleware.

        Args:
            rate_limiter: Rate limiter instance
        """
        self.rate_limiter = rate_limiter

    async def __call__(self, request, call_next):
        """
        Apply rate limiting to the request.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response
        """
        try:
            # Extract rate limit key from request
            rate_limit_key = self._extract_rate_limit_key(request)

            if rate_limit_key:
                # Check rate limit
                result = await self.rate_limiter.check_rate_limit(rate_limit_key)

                if not result.allowed:
                    # Return rate limit exceeded response
                    from fastapi import HTTPException
                    from fastapi.responses import JSONResponse

                    headers = {
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "X-RateLimit-Reset": result.reset_time.isoformat(),
                    }

                    if result.retry_after:
                        headers["Retry-After"] = str(result.retry_after)

                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "retry_after": result.retry_after,
                            "limit": result.limit,
                            "remaining": result.remaining,
                            "reset_time": result.reset_time.isoformat(),
                        },
                        headers=headers,
                    )

            # Continue with request
            response = await call_next(request)

            # Add rate limit headers to response
            if rate_limit_key:
                status = await self.rate_limiter.get_rate_limit_status(rate_limit_key)
                if status:
                    response.headers["X-RateLimit-Limit"] = str(status["limit"])
                    response.headers["X-RateLimit-Remaining"] = str(status["remaining"])
                    response.headers["X-RateLimit-Reset"] = status["window_start"]

            return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # Continue with request if rate limiting fails
            return await call_next(request)

    def _extract_rate_limit_key(self, request) -> Optional[str]:
        """
        Extract rate limit key from request.

        Args:
            request: FastAPI request

        Returns:
            Rate limit key or None
        """
        try:
            # Extract from API key
            api_key = request.headers.get("X-API-Key")
            if api_key:
                return f"api_key:{api_key}"

            # Extract from user ID
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                return f"user:{user_id}"

            # Extract from IP address
            client_ip = request.client.host if request.client else "unknown"
            return f"ip:{client_ip}"

        except Exception as e:
            logger.error(f"Failed to extract rate limit key: {e}")
            return None

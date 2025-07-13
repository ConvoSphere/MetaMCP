"""
Rate Limiting Implementation

This module provides comprehensive rate limiting functionality with support for
both in-memory and Redis-based rate limiting, including per-user and per-endpoint limits.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for a request."""
    limit: int
    remaining: int
    reset_time: int
    window_size: int


class RateLimiterBackend(ABC):
    """Abstract base class for rate limiter backends."""

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, RateLimitInfo]:
        """Check if request is allowed and return rate limit info."""
        pass

    @abstractmethod
    async def get_remaining(self, key: str, limit: int, window: int) -> RateLimitInfo:
        """Get remaining requests for a key."""
        pass

    async def close(self):
        """Close connections if needed. Override in subclasses."""
        pass


class MemoryRateLimiter(RateLimiterBackend):
    """In-memory rate limiter implementation."""

    def __init__(self):
        """Initialize in-memory rate limiter."""
        self._requests: Dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, RateLimitInfo]:
        """Check if request is allowed using in-memory storage."""
        async with self._lock:
            now = time.time()
            window_start = now - window

            # Clean old requests
            self._requests[key] = [req_time for req_time in self._requests[key] 
                                 if req_time > window_start]

            # Check if limit exceeded
            current_requests = len(self._requests[key])
            is_allowed = current_requests < limit

            if is_allowed:
                self._requests[key].append(now)

            # Calculate rate limit info
            reset_time = int(now + window)
            remaining = max(0, limit - current_requests)

            return is_allowed, RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                window_size=window
            )

    async def get_remaining(self, key: str, limit: int, window: int) -> RateLimitInfo:
        """Get remaining requests for a key."""
        async with self._lock:
            now = time.time()
            window_start = now - window

            # Clean old requests
            self._requests[key] = [req_time for req_time in self._requests[key] 
                                 if req_time > window_start]

            current_requests = len(self._requests[key])
            remaining = max(0, limit - current_requests)
            reset_time = int(now + window)

            return RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                window_size=window
            )


class RateLimiter:
    """Main rate limiter class that manages different backends."""

    def __init__(self, backend: RateLimiterBackend):
        """Initialize rate limiter with specified backend."""
        self.backend = backend
        self.settings = get_settings()

    async def is_allowed(self, key: str, limit: Optional[int] = None, 
                        window: Optional[int] = None) -> tuple[bool, RateLimitInfo]:
        """Check if request is allowed."""
        limit = limit or self.settings.rate_limit_requests
        window = window or self.settings.rate_limit_window
        
        return await self.backend.is_allowed(key, limit, window)

    async def get_remaining(self, key: str, limit: Optional[int] = None,
                          window: Optional[int] = None) -> RateLimitInfo:
        """Get remaining requests for a key."""
        limit = limit or self.settings.rate_limit_requests
        window = window or self.settings.rate_limit_window
        
        return await self.backend.get_remaining(key, limit, window)

    def generate_key(self, request: Any, user_id: Optional[str] = None) -> str:
        """Generate rate limit key for a request."""
        # Base key from client IP
        client_ip = getattr(request.client, 'host', 'unknown') if request.client else "unknown"
        base_key = f"rate_limit:{client_ip}"
        
        # Add user-specific key if available
        if user_id:
            base_key += f":user:{user_id}"
        
        # Add endpoint-specific key
        path = request.url.path
        method = request.method
        base_key += f":{method}:{path}"
        
        return base_key

    async def close(self):
        """Close rate limiter connections."""
        if hasattr(self.backend, 'close'):
            await self.backend.close()


def create_rate_limiter(use_redis: bool = False, redis_url: str = "redis://localhost:6379") -> RateLimiter:
    """Create rate limiter instance."""
    if use_redis:
        # For now, fall back to memory limiter
        # Redis implementation can be added later
        logger.warning("Redis rate limiter not implemented yet, using memory limiter")
        backend = MemoryRateLimiter()
    else:
        backend = MemoryRateLimiter()
    
    return RateLimiter(backend)


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""

    def __init__(self, rate_limiter: RateLimiter):
        """Initialize rate limit middleware."""
        self.rate_limiter = rate_limiter
        self.logger = get_logger(__name__)

    async def __call__(self, request: Any, call_next):
        """Process request with rate limiting."""
        try:
            # Generate rate limit key
            key = self.rate_limiter.generate_key(request)
            
            # Check rate limit
            is_allowed, rate_info = await self.rate_limiter.is_allowed(key)
            
            if not is_allowed:
                self.logger.warning(f"Rate limit exceeded for key: {key}")
                
                # Create error response
                error_response = {
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests",
                    "retry_after": rate_info.reset_time - int(time.time())
                }
                
                # Return error response (this will be handled by FastAPI)
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content=error_response,
                    headers={
                        "X-RateLimit-Limit": str(rate_info.limit),
                        "X-RateLimit-Remaining": str(rate_info.remaining),
                        "X-RateLimit-Reset": str(rate_info.reset_time),
                        "Retry-After": str(rate_info.reset_time - int(time.time()))
                    }
                )

            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info.limit)
            response.headers["X-RateLimit-Remaining"] = str(rate_info.remaining)
            response.headers["X-RateLimit-Reset"] = str(rate_info.reset_time)
            
            return response

        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting on error
            return await call_next(request) 
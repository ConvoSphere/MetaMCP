"""
Security Middleware

This module provides security middleware for input validation,
request sanitization, and security headers.
"""

from __future__ import annotations

import re
import json
from typing import Any, Dict, List
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings
from ..utils.logging import get_logger

try:
    # Prefer redis.asyncio (available in redis>=4.2)
    from redis.asyncio import Redis as AsyncRedis  # type: ignore
except Exception:  # pragma: no cover
    AsyncRedis = None  # type: ignore

logger = get_logger(__name__)
settings = get_settings()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for input validation and request sanitization.
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

        # Compile regex patterns for efficiency
        self.sql_injection_pattern = re.compile(
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b)",
            re.IGNORECASE,
        )
        self.xss_pattern = re.compile(
            r"(<script|javascript:|<iframe|<object|<embed|<form|on\w+\s*=)",
            re.IGNORECASE,
        )
        self.path_traversal_pattern = re.compile(
            r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)", re.IGNORECASE
        )
        self.command_injection_pattern = re.compile(
            r"(\b(cat|rm|del|wget|curl|nc|netcat|bash|sh|cmd|powershell)\b)",
            re.IGNORECASE,
        )

    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware."""
        try:
            # Validate request path
            if not self._validate_path(request.url.path):
                return JSONResponse(
                    status_code=400, content={"error": "Invalid request path"}
                )

            # Validate request headers
            if not self._validate_headers(request.headers):
                return JSONResponse(
                    status_code=400, content={"error": "Invalid request headers"}
                )

            # Validate request body for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                body_validation = await self._validate_request_body(request)
                if not body_validation["valid"]:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": f"Invalid request body: {body_validation['reason']}"
                        },
                    )

            # Validate query parameters
            if not self._validate_query_params(request.query_params):
                return JSONResponse(
                    status_code=400, content={"error": "Invalid query parameters"}
                )

            # Process request
            response = await call_next(request)

            # Add security headers (stricter in production)
            response = self._add_security_headers(response)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )

    def _validate_path(self, path: str) -> bool:
        """Validate request path for path traversal attempts."""
        if not path:
            return False

        # Check for path traversal attempts
        if self.path_traversal_pattern.search(path):
            logger.warning(f"Path traversal attempt detected: {path}")
            return False

        # Check for null bytes
        if "\x00" in path:
            logger.warning(f"Null byte detected in path: {path}")
            return False

        return True

    def _validate_headers(self, headers) -> bool:
        """Validate request headers."""
        # Check for suspicious headers
        suspicious_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-forwarded-host",
            "x-forwarded-proto",
        ]

        for header_name in suspicious_headers:
            if header_name in headers:
                header_value = headers[header_name]
                if self._contains_malicious_content(header_value):
                    logger.warning(
                        f"Malicious content in header {header_name}: {header_value}"
                    )
                    return False

        return True

    async def _validate_request_body(self, request: Request) -> Dict[str, Any]:
        """Validate request body for malicious content."""
        try:
            # Get content type
            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                # Validate JSON body
                body = await request.json()
                return self._validate_json_body(body)
            elif "application/x-www-form-urlencoded" in content_type:
                # Validate form data
                form_data = await request.form()
                return self._validate_form_data(form_data)
            elif "multipart/form-data" in content_type:
                # Validate multipart form data
                form_data = await request.form()
                return self._validate_form_data(form_data)
            else:
                # For other content types, read as text and validate
                body = await request.body()
                body_text = body.decode("utf-8", errors="ignore")
                return self._validate_text_body(body_text)

        except Exception as e:
            logger.error(f"Error validating request body: {e}")
            return {"valid": False, "reason": "Invalid request body format"}

    def _validate_json_body(self, body: Any) -> Dict[str, Any]:
        """Validate JSON request body."""
        if isinstance(body, dict):
            return self._validate_dict(body)
        elif isinstance(body, list):
            return self._validate_list(body)
        elif isinstance(body, (str, int, float, bool)):
            return self._validate_primitive(body)
        else:
            return {"valid": False, "reason": "Unsupported JSON type"}

    def _validate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate dictionary data."""
        for key, value in data.items():
            # Validate key
            if not self._validate_string(key):
                return {"valid": False, "reason": f"Invalid key: {key}"}

            # Validate value
            if isinstance(value, dict):
                result = self._validate_dict(value)
                if not result["valid"]:
                    return result
            elif isinstance(value, list):
                result = self._validate_list(value)
                if not result["valid"]:
                    return result
            else:
                result = self._validate_primitive(value)
                if not result["valid"]:
                    return result

        return {"valid": True}

    def _validate_list(self, data: List[Any]) -> Dict[str, Any]:
        """Validate list data."""
        for item in data:
            if isinstance(item, dict):
                result = self._validate_dict(item)
            elif isinstance(item, list):
                result = self._validate_list(item)
            else:
                result = self._validate_primitive(item)

            if not result["valid"]:
                return result

        return {"valid": True}

    def _validate_primitive(self, value: Any) -> Dict[str, Any]:
        """Validate primitive values."""
        if isinstance(value, str):
            if not self._validate_string(value):
                return {"valid": False, "reason": f"Invalid string value: {value}"}
        elif isinstance(value, (int, float)):
            # Validate numeric values
            if not self._validate_number(value):
                return {"valid": False, "reason": f"Invalid numeric value: {value}"}
        elif isinstance(value, bool):
            # Boolean values are always valid
            pass
        else:
            return {"valid": False, "reason": f"Unsupported value type: {type(value)}"}

        return {"valid": True}

    def _validate_string(self, value: str) -> bool:
        """Validate string for malicious content."""
        if not isinstance(value, str):
            return False

        # Check for SQL injection
        if self.sql_injection_pattern.search(value):
            logger.warning(f"SQL injection attempt detected: {value}")
            return False

        # Check for XSS
        if self.xss_pattern.search(value):
            logger.warning(f"XSS attempt detected: {value}")
            return False

        # Check for command injection
        if self.command_injection_pattern.search(value):
            logger.warning(f"Command injection attempt detected: {value}")
            return False

        # Check for null bytes
        if "\x00" in value:
            logger.warning(f"Null byte detected in string: {value}")
            return False

        return True

    def _validate_number(self, value: float) -> bool:
        """Validate numeric values."""
        # Check for NaN or infinity
        if not (float("-inf") < value < float("inf")):
            return False

        return True

    def _validate_form_data(self, form_data) -> Dict[str, Any]:
        """Validate form data."""
        for key, value in form_data.items():
            if not self._validate_string(str(key)):
                return {"valid": False, "reason": f"Invalid form key: {key}"}

            if not self._validate_string(str(value)):
                return {"valid": False, "reason": f"Invalid form value: {value}"}

        return {"valid": True}

    def _validate_text_body(self, text: str) -> Dict[str, Any]:
        """Validate text body."""
        if not self._validate_string(text):
            return {"valid": False, "reason": "Invalid text content"}

        return {"valid": True}

    def _validate_query_params(self, query_params) -> bool:
        """Validate query parameters."""
        for key, value in query_params.items():
            # Validate key
            if not self._validate_string(key):
                logger.warning(f"Invalid query parameter key: {key}")
                return False

            # Validate value
            if not self._validate_string(value):
                logger.warning(f"Invalid query parameter value: {value}")
                return False

        return True

    def _contains_malicious_content(self, value: str) -> bool:
        """Check if value contains malicious content."""
        if not isinstance(value, str):
            return False

        return (
            self.sql_injection_pattern.search(value)
            or self.xss_pattern.search(value)
            or self.path_traversal_pattern.search(value)
            or self.command_injection_pattern.search(value)
            or "\x00" in value
        )

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Only set HSTS if not in debug (assumes HTTPS in prod behind LB)
        if not self.settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Harden CSP in production; allow unsafe-inline/eval only in debug
        if self.settings.debug:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline';"
            )
        else:
            csp = "default-src 'self'; " "script-src 'self'; " "style-src 'self'; "
        response.headers["Content-Security-Policy"] = csp

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.request_counts: dict[str, list[int]] = {}

        # Lazy Redis client for distributed rate limiting
        self._redis: AsyncRedis | None = None
        if self.settings.rate_limit_use_redis and AsyncRedis is not None:
            try:
                self._redis = AsyncRedis.from_url(
                    self.settings.rate_limit_redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    health_check_interval=30,
                )
            except Exception as e:  # pragma: no cover
                logger.error(f"Failed to initialize Redis for rate limiting: {e}")
                self._redis = None

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting middleware."""
        client_ip = self._get_client_ip(request)

        # Check rate limit (Redis preferred)
        allowed, limit, remaining, reset = await self._check_rate_limit(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers=self._rate_limit_headers(limit, remaining, reset),
                content={"error": "Rate limit exceeded"},
            )

        response = await call_next(request)
        # Attach rate limit headers on successful responses too
        for k, v in self._rate_limit_headers(limit, remaining, reset).items():
            response.headers[k] = v
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(self, client_ip: str) -> tuple[bool, int, int, int]:
        """Check if client has exceeded rate limit.
        Returns (allowed, limit, remaining, reset_epoch_seconds).
        """
        limit = self.settings.rate_limit_requests
        window = self.settings.rate_limit_window
        current_time = int(time.time())
        window_start = current_time - (current_time % window)
        reset = window_start + window

        # Distributed rate limiting using Redis if available
        if self._redis is not None:
            key = f"rl:{client_ip}:{window_start}:{window}"
            try:
                # Use INCR with expiry for atomic counter per window
                count = await self._redis.incr(key)
                if count == 1:
                    await self._redis.expire(key, window)
                remaining = max(0, limit - count)
                return (count <= limit, limit, remaining, reset)
            except Exception as e:  # pragma: no cover
                logger.error(f"Redis rate limiting failed, falling back to memory: {e}")
                # fall back to memory

        # Fallback: in-memory per-process
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        # Remove old requests outside the window
        self.request_counts[client_ip] = [
            ts for ts in self.request_counts[client_ip] if ts > current_time - window
        ]
        if len(self.request_counts[client_ip]) >= limit:
            remaining = 0
            return (False, limit, remaining, reset)
        self.request_counts[client_ip].append(current_time)
        remaining = max(0, limit - len(self.request_counts[client_ip]))
        return (True, limit, remaining, reset)

    def _rate_limit_headers(
        self, limit: int, remaining: int, reset: int
    ) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
        }


# Import time module for rate limiting
import time

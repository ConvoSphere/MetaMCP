"""
Security Middleware

This module provides security middleware for input validation,
request sanitization, and security headers.
"""

import re
import json
from typing import Any, Dict, List
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings
from ..utils.logging import get_logger

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
            re.IGNORECASE
        )
        self.xss_pattern = re.compile(
            r"(<script|javascript:|<iframe|<object|<embed|<form|on\w+\s*=)",
            re.IGNORECASE
        )
        self.path_traversal_pattern = re.compile(
            r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
            re.IGNORECASE
        )
        self.command_injection_pattern = re.compile(
            r"(\b(cat|rm|del|wget|curl|nc|netcat|bash|sh|cmd|powershell)\b)",
            re.IGNORECASE
        )

    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware."""
        try:
            # Validate request path
            if not self._validate_path(request.url.path):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request path"}
                )

            # Validate request headers
            if not self._validate_headers(request.headers):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request headers"}
                )

            # Validate request body for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                body_validation = await self._validate_request_body(request)
                if not body_validation["valid"]:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Invalid request body: {body_validation['reason']}"}
                    )

            # Validate query parameters
            if not self._validate_query_params(request.query_params):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid query parameters"}
                )

            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
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
            "x-forwarded-proto"
        ]
        
        for header_name in suspicious_headers:
            if header_name in headers:
                header_value = headers[header_name]
                if self._contains_malicious_content(header_value):
                    logger.warning(f"Malicious content in header {header_name}: {header_value}")
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
        if not (float('-inf') < value < float('inf')):
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
            self.sql_injection_pattern.search(value) or
            self.xss_pattern.search(value) or
            self.path_traversal_pattern.search(value) or
            self.command_injection_pattern.search(value) or
            "\x00" in value
        )

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.request_counts = {}

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting middleware."""
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
            
        response = await call_next(request)
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

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        # Simple in-memory rate limiting (use Redis in production)
        current_time = int(time.time())
        window_start = current_time - self.settings.rate_limit_window
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
            
        # Remove old requests outside the window
        self.request_counts[client_ip] = [
            timestamp for timestamp in self.request_counts[client_ip]
            if timestamp > window_start
        ]
        
        # Check if limit exceeded
        if len(self.request_counts[client_ip]) >= self.settings.rate_limit_requests:
            return False
            
        # Add current request
        self.request_counts[client_ip].append(current_time)
        return True


# Import time module for rate limiting
import time

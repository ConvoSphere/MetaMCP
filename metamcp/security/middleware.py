"""
Enhanced Security Features

This module provides comprehensive security middleware including request signing,
API key management, IP whitelisting, and security headers.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any

from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration."""

    enable_request_signing: bool = True
    enable_api_keys: bool = True
    enable_ip_whitelist: bool = False
    enable_security_headers: bool = True
    allowed_ips: set[str] | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.allowed_ips is None:
            self.allowed_ips = set()

    api_key_header: str = "X-API-Key"
    signature_header: str = "X-Signature"
    timestamp_header: str = "X-Timestamp"
    max_timestamp_drift: int = 300  # 5 minutes


class RequestSigner:
    """Handles request signing and verification."""

    def __init__(self, secret_key: str):
        """Initialize request signer."""
        self.secret_key = secret_key.encode("utf-8")
        self.logger = get_logger(__name__)

    def sign_request(
        self, method: str, path: str, body: str = "", timestamp: int | None = None
    ) -> str:
        """Sign a request."""
        if timestamp is None:
            timestamp = int(time.time())

        # Create signature string
        signature_string = f"{method.upper()}{path}{body}{timestamp}"

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key, signature_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(
        self, method: str, path: str, body: str, signature: str, timestamp: int
    ) -> bool:
        """Verify request signature."""
        expected_signature = self.sign_request(method, path, body, timestamp)
        return hmac.compare_digest(signature, expected_signature)

    def verify_timestamp(self, timestamp: int, max_drift: int = 300) -> bool:
        """Verify request timestamp."""
        current_time = int(time.time())
        return abs(current_time - timestamp) <= max_drift


class APIKeyManager:
    """Manages API keys and permissions."""

    def __init__(self):
        """Initialize API key manager."""
        self.logger = get_logger(__name__)
        self.api_keys: dict[str, dict[str, Any]] = {}
        self._initialize_default_keys()

    def _initialize_default_keys(self):
        """Initialize with default API keys."""
        # Add some default API keys for testing
        self.add_api_key(
            key="test-key-1",
            name="Test API Key 1",
            permissions=["read", "write"],
            rate_limit=1000,
            expires_at=None,
        )

        self.add_api_key(
            key="admin-key-1",
            name="Admin API Key 1",
            permissions=["read", "write", "admin"],
            rate_limit=10000,
            expires_at=None,
        )

    def add_api_key(
        self,
        key: str,
        name: str,
        permissions: list[str],
        rate_limit: int = 1000,
        expires_at: int | None = None,
    ):
        """Add a new API key."""
        self.api_keys[key] = {
            "name": name,
            "permissions": permissions,
            "rate_limit": rate_limit,
            "expires_at": expires_at,
            "created_at": int(time.time()),
        }
        self.logger.info(f"Added API key: {name}")

    def validate_api_key(self, key: str) -> tuple[bool, dict[str, Any] | None]:
        """Validate API key and return key info."""
        if key not in self.api_keys:
            return False, None

        key_info = self.api_keys[key]

        # Check if key is expired
        if key_info and key_info["expires_at"] and time.time() > key_info["expires_at"]:
            return False, None

        return True, key_info

    def has_permission(self, key: str, permission: str) -> bool:
        """Check if API key has specific permission."""
        is_valid, key_info = self.validate_api_key(key)
        if not is_valid:
            return False

        return permission in key_info["permissions"]

    def get_key_rate_limit(self, key: str) -> int | None:
        """Get rate limit for API key."""
        is_valid, key_info = self.validate_api_key(key)
        if not is_valid:
            return None

        return key_info["rate_limit"]


class IPWhitelistManager:
    """Manages IP whitelisting."""

    def __init__(self, allowed_ips: set[str] = None):
        """Initialize IP whitelist manager."""
        self.logger = get_logger(__name__)
        self.allowed_ips = allowed_ips or set()
        self.enabled = len(self.allowed_ips) > 0

    def add_ip(self, ip: str):
        """Add IP to whitelist."""
        self.allowed_ips.add(ip)
        self.enabled = True
        self.logger.info(f"Added IP to whitelist: {ip}")

    def remove_ip(self, ip: str):
        """Remove IP from whitelist."""
        self.allowed_ips.discard(ip)
        self.enabled = len(self.allowed_ips) > 0
        self.logger.info(f"Removed IP from whitelist: {ip}")

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed."""
        if not self.enabled:
            return True

        return ip in self.allowed_ips

    def get_allowed_ips(self) -> set[str]:
        """Get all allowed IPs."""
        return self.allowed_ips.copy()


class SecurityHeadersMiddleware:
    """Adds security headers to responses."""

    def __init__(self):
        """Initialize security headers middleware."""
        self.logger = get_logger(__name__)
        self.settings = get_settings()

    def add_security_headers(self, response: Any):
        """Add security headers to response."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        for header, value in headers.items():
            response.headers[header] = value


class SecurityMiddleware:
    """Comprehensive security middleware."""

    def __init__(self, config: SecurityConfig):
        """Initialize security middleware."""
        self.config = config
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # Initialize security components
        self.request_signer = RequestSigner(self.settings.secret_key)
        self.api_key_manager = APIKeyManager()
        self.ip_whitelist_manager = IPWhitelistManager(config.allowed_ips)
        self.security_headers = SecurityHeadersMiddleware()

    async def __call__(self, request: Any, call_next):
        """Process request with security checks."""
        try:
            # Get client IP
            client_ip = (
                getattr(request.client, "host", "unknown")
                if request.client
                else "unknown"
            )

            # Check IP whitelist
            if not self.ip_whitelist_manager.is_ip_allowed(client_ip):
                self.logger.warning(
                    f"Blocked request from unauthorized IP: {client_ip}"
                )
                return self._create_security_error_response(
                    "IP not whitelisted", 403, {"ip": client_ip}
                )

            # Verify API key if enabled
            if self.config.enable_api_keys:
                api_key = request.headers.get(self.config.api_key_header)
                if not api_key:
                    return self._create_security_error_response(
                        "API key required",
                        401,
                        {"missing_header": self.config.api_key_header},
                    )

                is_valid, key_info = self.api_key_manager.validate_api_key(api_key)
                if not is_valid:
                    return self._create_security_error_response(
                        "Invalid API key", 401, {"invalid_key": True}
                    )

                # Store key info in request state for later use
                request.state.api_key_info = key_info

            # Verify request signature if enabled
            if self.config.enable_request_signing:
                signature = request.headers.get(self.config.signature_header)
                timestamp = request.headers.get(self.config.timestamp_header)

                if not signature or not timestamp:
                    return self._create_security_error_response(
                        "Request signature required", 401, {"missing_signature": True}
                    )

                try:
                    timestamp_int = int(timestamp)
                except ValueError:
                    return self._create_security_error_response(
                        "Invalid timestamp", 400, {"invalid_timestamp": True}
                    )

                # Verify timestamp
                if not self.request_signer.verify_timestamp(
                    timestamp_int, self.config.max_timestamp_drift
                ):
                    return self._create_security_error_response(
                        "Request timestamp expired", 401, {"timestamp_expired": True}
                    )

                # Verify signature
                body = await self._get_request_body(request)
                if not self.request_signer.verify_signature(
                    request.method,
                    str(request.url.path),
                    body,
                    signature,
                    timestamp_int,
                ):
                    return self._create_security_error_response(
                        "Invalid request signature", 401, {"invalid_signature": True}
                    )

            # Process request
            response = await call_next(request)

            # Add security headers
            if self.config.enable_security_headers:
                self.security_headers.add_security_headers(response)

            return response

        except Exception as e:
            self.logger.error(f"Security middleware error: {e}")
            return self._create_security_error_response(
                "Security check failed", 500, {"error": str(e)}
            )

    async def _get_request_body(self, request: Any) -> str:
        """Get request body as string."""
        try:
            body = await request.body()
            return body.decode("utf-8")
        except Exception:
            return ""

    def _create_security_error_response(
        self, message: str, status_code: int, details: dict[str, Any] = None
    ) -> Any:
        """Create security error response."""
        from fastapi.responses import JSONResponse

        error_response = {
            "error": "security_error",
            "message": message,
            "timestamp": int(time.time()),
        }

        if details:
            error_response["details"] = details

        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={"X-Security-Error": "true", "X-Security-Message": message},
        )


def create_security_middleware(config: SecurityConfig) -> SecurityMiddleware:
    """Create security middleware instance."""
    return SecurityMiddleware(config)


def create_default_security_config() -> SecurityConfig:
    """Create default security configuration."""
    settings = get_settings()

    return SecurityConfig(
        enable_request_signing=settings.environment == "production",
        enable_api_keys=True,
        enable_ip_whitelist=False,
        enable_security_headers=True,
        allowed_ips=set(),
    )

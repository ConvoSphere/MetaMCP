"""
MetaMCP Exceptions

This module defines all custom exceptions used throughout the MetaMCP system.
"""

from typing import Any, Dict, Optional


class MetaMCPError(Exception):
    """Base exception for all MetaMCP errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(MetaMCPError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="configuration_error",
            status_code=500,
            details=details
        )


class AuthenticationError(MetaMCPError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="authentication_error",
            status_code=401,
            details=details
        )


class AuthorizationError(MetaMCPError):
    """Authorization-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="authorization_error",
            status_code=403,
            details=details
        )


class ToolRegistrationError(MetaMCPError):
    """Tool registration errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="tool_registration_error",
            status_code=400,
            details=details
        )


class ToolNotFoundError(MetaMCPError):
    """Tool not found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="tool_not_found",
            status_code=404,
            details=details
        )


class ToolExecutionError(MetaMCPError):
    """Tool execution errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="tool_execution_error",
            status_code=500,
            details=details
        )


class VectorSearchError(MetaMCPError):
    """Vector search errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="vector_search_error",
            status_code=500,
            details=details
        )


class LLMServiceError(MetaMCPError):
    """LLM service errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="llm_service_error",
            status_code=500,
            details=details
        )


class PolicyError(MetaMCPError):
    """Policy evaluation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="policy_error",
            status_code=403,
            details=details
        )


class TelemetryError(MetaMCPError):
    """Telemetry errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="telemetry_error",
            status_code=500,
            details=details
        )


class ProxyError(MetaMCPError):
    """Proxy-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="proxy_error",
            status_code=500,
            details=details
        )


class ServerDiscoveryError(MetaMCPError):
    """Server discovery errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="server_discovery_error",
            status_code=500,
            details=details
        )


class ConnectionError(MetaMCPError):
    """Connection-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="connection_error",
            status_code=503,
            details=details
        )


class ValidationError(MetaMCPError):
    """Validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=400,
            details=details
        )


class RateLimitError(MetaMCPError):
    """Rate limiting errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="rate_limit_error",
            status_code=429,
            details=details
        )


class TimeoutError(MetaMCPError):
    """Timeout errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="timeout_error",
            status_code=408,
            details=details
        )


class ResourceNotFoundError(MetaMCPError):
    """Resource not found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="resource_not_found",
            status_code=404,
            details=details
        )


class DatabaseError(MetaMCPError):
    """Database-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="database_error",
            status_code=500,
            details=details
        )


class ExternalServiceError(MetaMCPError):
    """External service errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="external_service_error",
            status_code=502,
            details=details
        )

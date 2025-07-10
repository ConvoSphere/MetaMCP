"""
Custom Exception Classes for MCP Meta-Server

This module defines all custom exceptions used throughout the MCP Meta-Server.
Each exception includes appropriate error codes, status codes, and detailed messages.
"""

from typing import Any


class MetaMCPError(Exception):
    """
    Base exception class for all MCP Meta-Server errors.
    
    This is the parent class for all custom exceptions in the system.
    It provides a consistent interface for error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "unknown_error",
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ):
        """
        Initialize MetaMCP error.
        
        Args:
            message: Human-readable error message
            error_code: Unique error code for programmatic handling
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ToolNotFoundError(MetaMCPError):
    """Raised when a requested tool is not found."""

    def __init__(self, message: str, error_code: str = "tool_not_found"):
        super().__init__(message, error_code, 404)


class ToolRegistrationError(MetaMCPError):
    """Raised when tool registration fails."""

    def __init__(self, message: str, error_code: str = "tool_registration_failed"):
        super().__init__(message, error_code, 400)


class ToolExecutionError(MetaMCPError):
    """Raised when tool execution fails."""

    def __init__(self, message: str, error_code: str = "tool_execution_failed"):
        super().__init__(message, error_code, 500)


class PolicyViolationError(MetaMCPError):
    """Raised when a policy violation occurs."""

    def __init__(self, message: str, error_code: str = "policy_violation"):
        super().__init__(message, error_code, 403)


class AuthenticationError(MetaMCPError):
    """Raised when authentication fails."""

    def __init__(self, message: str, error_code: str = "authentication_failed"):
        super().__init__(message, error_code, 401)


class AuthorizationError(MetaMCPError):
    """Raised when authorization fails."""

    def __init__(self, message: str, error_code: str = "authorization_failed"):
        super().__init__(message, error_code, 403)


class VectorSearchError(MetaMCPError):
    """Raised when vector search operations fail."""

    def __init__(self, message: str, error_code: str = "vector_search_failed"):
        super().__init__(message, error_code, 500)


class EmbeddingError(MetaMCPError):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, error_code: str = "embedding_failed"):
        super().__init__(message, error_code, 500)


class MCPProtocolError(MetaMCPError):
    """Raised when MCP protocol errors occur."""

    def __init__(self, message: str, error_code: str = "mcp_protocol_error"):
        super().__init__(message, error_code, 400)


class DatabaseError(MetaMCPError):
    """Raised when database operations fail."""

    def __init__(self, message: str, error_code: str = "database_error"):
        super().__init__(message, error_code, 500)


class ConfigurationError(MetaMCPError):
    """Raised when configuration errors occur."""

    def __init__(self, message: str, error_code: str = "configuration_error"):
        super().__init__(message, error_code, 500)


class RateLimitError(MetaMCPError):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, error_code: str = "rate_limit_exceeded"):
        super().__init__(message, error_code, 429)


class ValidationError(MetaMCPError):
    """Raised when validation fails."""

    def __init__(self, message: str, error_code: str = "validation_error"):
        super().__init__(message, error_code, 400)


class ServiceUnavailableError(MetaMCPError):
    """Raised when a required service is unavailable."""

    def __init__(self, service: str, reason: str, error_code: str = "service_unavailable"):
        message = f"Service '{service}' is unavailable: {reason}"
        super().__init__(message, error_code, 503)


class HealthCheckError(MetaMCPError):
    """Raised when health checks fail."""

    def __init__(self, component: str, reason: str, error_code: str = "health_check_failed"):
        message = f"Health check failed for '{component}': {reason}"
        super().__init__(message, error_code, 503)


# Error code mapping for quick lookup
ERROR_CODE_MAPPING = {
    "tool_not_found": ToolNotFoundError,
    "tool_registration_failed": ToolRegistrationError,
    "tool_execution_failed": ToolExecutionError,
    "policy_violation": PolicyViolationError,
    "authentication_failed": AuthenticationError,
    "authorization_failed": AuthorizationError,
    "vector_search_failed": VectorSearchError,
    "embedding_failed": EmbeddingError,
    "mcp_protocol_error": MCPProtocolError,
    "database_error": DatabaseError,
    "configuration_error": ConfigurationError,
    "rate_limit_exceeded": RateLimitError,
    "validation_error": ValidationError,
    "service_unavailable": ServiceUnavailableError,
    "health_check_failed": HealthCheckError,
}


def get_exception_class(error_code: str) -> type:
    """
    Get exception class by error code.
    
    Args:
        error_code: Error code string
        
    Returns:
        Exception class or MetaMCPError if not found
    """
    return ERROR_CODE_MAPPING.get(error_code, MetaMCPError)

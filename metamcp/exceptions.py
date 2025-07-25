"""
Custom exceptions for MetaMCP.

This module defines all custom exceptions used throughout the MetaMCP system.
"""

from typing import Any


class MetaMCPException(Exception):
    """Base exception for MetaMCP."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class MetaMCPError(MetaMCPException):
    """General MetaMCP error."""

    pass


# Tool-related exceptions
class ToolNotFoundError(MetaMCPException):
    """Raised when a tool is not found."""

    def __init__(self, tool_name: str, error_code: str = "tool_not_found"):
        super().__init__(
            message=f"Tool '{tool_name}' not found",
            error_code=error_code,
            status_code=404,
        )


class ToolExecutionError(MetaMCPException):
    """Raised when tool execution fails."""

    def __init__(
        self,
        message: str,
        error_code: str = "tool_execution_error",
        tool_name: str | None = None,
    ):
        details = {"tool_name": tool_name} if tool_name else {}
        super().__init__(
            message=message, error_code=error_code, details=details, status_code=500
        )


class ToolRegistrationError(MetaMCPException):
    """Raised when tool registration fails."""

    def __init__(self, message: str, error_code: str = "tool_registration_error"):
        super().__init__(message=message, error_code=error_code, status_code=400)


# Authentication and authorization exceptions
class AuthenticationError(MetaMCPException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message, error_code="authentication_error", status_code=401
        )


class AuthorizationError(MetaMCPException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Authorization failed"):
        super().__init__(
            message=message, error_code="authorization_error", status_code=403
        )


class PolicyViolationError(MetaMCPException):
    """Raised when a policy violation occurs."""

    def __init__(self, message: str, policy_name: str | None = None):
        details = {"policy_name": policy_name} if policy_name else {}
        super().__init__(
            message=message,
            error_code="policy_violation",
            details=details,
            status_code=403,
        )


# MCP protocol exceptions
class MCPProtocolError(MetaMCPException):
    """Raised when MCP protocol errors occur."""

    def __init__(self, message: str, error_code: str = "mcp_protocol_error"):
        super().__init__(message=message, error_code=error_code, status_code=400)


# Vector search exceptions
class VectorSearchError(MetaMCPException):
    """Raised when vector search operations fail."""

    def __init__(self, message: str, error_code: str = "vector_search_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


class EmbeddingError(MetaMCPException):
    """Raised when embedding operations fail."""

    def __init__(self, message: str, error_code: str = "embedding_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Proxy-related exceptions
class ProxyError(MetaMCPException):
    """Raised when proxy operations fail."""

    def __init__(self, message: str, error_code: str = "proxy_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


class ServerDiscoveryError(MetaMCPException):
    """Raised when server discovery fails."""

    def __init__(self, message: str, error_code: str = "server_discovery_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Workflow-related exceptions
class WorkflowExecutionError(MetaMCPException):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, error_code: str = "workflow_execution_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


class WorkflowValidationError(MetaMCPException):
    """Raised when workflow validation fails."""

    def __init__(self, message: str, error_code: str = "workflow_validation_error"):
        super().__init__(message=message, error_code=error_code, status_code=400)


class WorkflowPersistenceError(MetaMCPException):
    """Raised when workflow persistence operations fail."""

    def __init__(self, message: str, error_code: str = "workflow_persistence_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Search-related exceptions
class SearchError(MetaMCPException):
    """Raised when search operations fail."""

    def __init__(self, message: str, error_code: str = "search_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Validation exceptions
class ValidationError(MetaMCPException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            error_code="validation_error",
            details=details,
            status_code=400,
        )


# Circuit breaker exceptions
class CircuitBreakerOpenError(MetaMCPException):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str | None = None):
        details = {"circuit_name": circuit_name} if circuit_name else {}
        super().__init__(
            message=message,
            error_code="circuit_breaker_open",
            details=details,
            status_code=503,
        )


# Configuration exceptions
class ConfigurationError(MetaMCPException):
    """Raised when configuration errors occur."""

    def __init__(self, message: str, config_key: str | None = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message=message,
            error_code="configuration_error",
            details=details,
            status_code=500,
        )


# Database exceptions
class DatabaseError(MetaMCPException):
    """Raised when database operations fail."""

    def __init__(self, message: str, error_code: str = "database_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Monitoring exceptions
class MonitoringError(MetaMCPException):
    """Raised when monitoring operations fail."""

    def __init__(self, message: str, error_code: str = "monitoring_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Rate limiting exceptions
class RateLimitError(MetaMCPException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message, error_code="rate_limit_exceeded", status_code=429
        )


# Timeout exceptions
class TimeoutError(MetaMCPException):
    """Raised when operations timeout."""

    def __init__(self, message: str, operation: str | None = None):
        details = {"operation": operation} if operation else {}
        super().__init__(
            message=message,
            error_code="timeout_error",
            details=details,
            status_code=408,
        )


# Connection exceptions
class ConnectionError(MetaMCPException):
    """Raised when connection errors occur."""

    def __init__(self, message: str, endpoint: str | None = None):
        details = {"endpoint": endpoint} if endpoint else {}
        super().__init__(
            message=message,
            error_code="connection_error",
            details=details,
            status_code=503,
        )


# Resource exceptions
class ResourceNotFoundError(MetaMCPException):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            error_code="resource_not_found",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=404,
        )


class ResourceConflictError(MetaMCPException):
    """Raised when there's a conflict with a resource."""

    def __init__(self, message: str, resource_type: str | None = None):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(
            message=message,
            error_code="resource_conflict",
            details=details,
            status_code=409,
        )


# Service exceptions
class ServiceUnavailableError(MetaMCPException):
    """Raised when a service is unavailable."""

    def __init__(self, service_name: str, message: str | None = None):
        if not message:
            message = f"Service '{service_name}' is unavailable"
        super().__init__(
            message=message,
            error_code="service_unavailable",
            details={"service_name": service_name},
            status_code=503,
        )


# Security exceptions
class SecurityError(MetaMCPException):
    """Raised when security-related errors occur."""

    def __init__(self, message: str, error_code: str = "security_error"):
        super().__init__(message=message, error_code=error_code, status_code=403)


# Telemetry exceptions
class TelemetryError(MetaMCPException):
    """Raised when telemetry operations fail."""

    def __init__(self, message: str, error_code: str = "telemetry_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# LLM service exceptions
class LLMServiceError(MetaMCPException):
    """Raised when LLM service operations fail."""

    def __init__(self, message: str, provider: str | None = None):
        details = {"provider": provider} if provider else {}
        super().__init__(
            message=message,
            error_code="llm_service_error",
            details=details,
            status_code=500,
        )


# Cache exceptions
class CacheError(MetaMCPException):
    """Raised when cache operations fail."""

    def __init__(self, message: str, error_code: str = "cache_error"):
        super().__init__(message=message, error_code=error_code, status_code=500)


# Export all exceptions
__all__ = [
    "MetaMCPException",
    "MetaMCPError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolRegistrationError",
    "AuthenticationError",
    "AuthorizationError",
    "PolicyViolationError",
    "MCPProtocolError",
    "VectorSearchError",
    "EmbeddingError",
    "ProxyError",
    "ServerDiscoveryError",
    "WorkflowExecutionError",
    "WorkflowValidationError",
    "WorkflowPersistenceError",
    "SearchError",
    "ValidationError",
    "CircuitBreakerOpenError",
    "ConfigurationError",
    "DatabaseError",
    "MonitoringError",
    "RateLimitError",
    "TimeoutError",
    "ConnectionError",
    "ResourceNotFoundError",
    "ResourceConflictError",
    "ServiceUnavailableError",
    "SecurityError",
    "TelemetryError",
    "LLMServiceError",
    "CacheError",
]

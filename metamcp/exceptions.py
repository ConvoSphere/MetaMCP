"""
Custom Exception Classes for MCP Meta-Server

This module defines all custom exceptions used throughout the MCP Meta-Server.
Each exception includes appropriate error codes, status codes, and detailed messages.
"""

from typing import Optional, Dict, Any


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
        details: Optional[Dict[str, Any]] = None
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
    """Raised when a requested tool is not found in the registry."""
    
    def __init__(self, tool_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Tool '{tool_name}' not found in registry",
            error_code="tool_not_found",
            status_code=404,
            details=details or {"tool_name": tool_name}
        )


class ToolRegistrationError(MetaMCPError):
    """Raised when tool registration fails."""
    
    def __init__(self, tool_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Failed to register tool '{tool_name}': {reason}",
            error_code="tool_registration_failed",
            status_code=400,
            details=details or {"tool_name": tool_name, "reason": reason}
        )


class ToolExecutionError(MetaMCPError):
    """Raised when tool execution fails."""
    
    def __init__(self, tool_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {reason}",
            error_code="tool_execution_failed",
            status_code=500,
            details=details or {"tool_name": tool_name, "reason": reason}
        )


class PolicyViolationError(MetaMCPError):
    """Raised when a policy rule is violated."""
    
    def __init__(self, policy_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Policy violation in '{policy_name}': {reason}",
            error_code="policy_violation",
            status_code=403,
            details=details or {"policy_name": policy_name, "reason": reason}
        )


class AuthenticationError(MetaMCPError):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str = "Invalid credentials", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Authentication failed: {reason}",
            error_code="authentication_failed",
            status_code=401,
            details=details
        )


class AuthorizationError(MetaMCPError):
    """Raised when authorization fails."""
    
    def __init__(self, resource: str, action: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Access denied for action '{action}' on resource '{resource}'",
            error_code="authorization_failed",
            status_code=403,
            details=details or {"resource": resource, "action": action}
        )


class VectorSearchError(MetaMCPError):
    """Raised when vector search operations fail."""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Vector search failed: {reason}",
            error_code="vector_search_failed",
            status_code=500,
            details=details
        )


class EmbeddingError(MetaMCPError):
    """Raised when embedding generation fails."""
    
    def __init__(self, text: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Failed to generate embedding for text: {reason}",
            error_code="embedding_failed",
            status_code=500,
            details=details or {"text_preview": text[:100] + "..." if len(text) > 100 else text}
        )


class MCPProtocolError(MetaMCPError):
    """Raised when MCP protocol errors occur."""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"MCP protocol error in '{operation}': {reason}",
            error_code="mcp_protocol_error",
            status_code=400,
            details=details or {"operation": operation, "reason": reason}
        )


class DatabaseError(MetaMCPError):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            error_code="database_error",
            status_code=500,
            details=details or {"operation": operation, "reason": reason}
        )


class ConfigurationError(MetaMCPError):
    """Raised when configuration is invalid."""
    
    def __init__(self, setting: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Configuration error for '{setting}': {reason}",
            error_code="configuration_error",
            status_code=500,
            details=details or {"setting": setting, "reason": reason}
        )


class RateLimitError(MetaMCPError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, limit: int, window: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            error_code="rate_limit_exceeded",
            status_code=429,
            details=details or {"limit": limit, "window": window}
        )


class ValidationError(MetaMCPError):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Validation error for field '{field}': {reason}",
            error_code="validation_error",
            status_code=400,
            details=details or {"field": field, "reason": reason}
        )


class ServiceUnavailableError(MetaMCPError):
    """Raised when a required service is unavailable."""
    
    def __init__(self, service: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Service '{service}' is unavailable: {reason}",
            error_code="service_unavailable",
            status_code=503,
            details=details or {"service": service, "reason": reason}
        )


class HealthCheckError(MetaMCPError):
    """Raised when health checks fail."""
    
    def __init__(self, component: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Health check failed for '{component}': {reason}",
            error_code="health_check_failed",
            status_code=500,
            details=details or {"component": component, "reason": reason}
        )


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
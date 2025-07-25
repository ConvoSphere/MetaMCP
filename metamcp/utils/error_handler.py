"""
Enhanced Error Handling

This module provides comprehensive error handling with structured error responses,
correlation IDs, error reporting, and recovery mechanisms.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ErrorContext:
    """Context information for error handling."""

    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    method: str | None = None


@dataclass
class ErrorDetails:
    """Detailed error information."""

    error_code: str
    message: str
    details: dict[str, Any] | None = None
    stack_trace: str | None = None
    context: ErrorContext | None = None
    severity: str = "error"
    category: str = "general"
    recoverable: bool = True
    retry_after: int | None = None


class ErrorHandler:
    """Main error handler class."""

    def __init__(self):
        """Initialize error handler."""
        self.logger = get_logger(__name__)
        self.error_reports: list[ErrorDetails] = []

    def create_error_context(
        self, request: Any = None, user_id: str | None = None
    ) -> ErrorContext:
        """Create error context from request."""
        context = ErrorContext()

        if request:
            context.client_ip = (
                getattr(request.client, "host", None) if request.client else None
            )
            context.user_agent = request.headers.get("user-agent")
            context.endpoint = str(request.url.path)
            context.method = request.method

        if user_id:
            context.user_id = user_id

        return context

    def create_error_response(self, error_details: ErrorDetails) -> dict[str, Any]:
        """Create structured error response."""
        response = {
            "error": {
                "code": error_details.error_code,
                "message": error_details.message,
                "timestamp": (
                    error_details.context.timestamp.isoformat()
                    if error_details.context
                    else None
                ),
                "correlation_id": (
                    error_details.context.correlation_id
                    if error_details.context
                    else None
                ),
                "severity": error_details.severity,
                "category": error_details.category,
                "recoverable": error_details.recoverable,
            }
        }

        if error_details.details:
            response["error"]["details"] = error_details.details

        if error_details.retry_after:
            response["error"]["retry_after"] = error_details.retry_after

        return response

    def handle_exception(
        self, exc: Exception, context: ErrorContext | None = None
    ) -> ErrorDetails:
        """Handle an exception and create error details."""
        if context is None:
            context = ErrorContext()

        # Determine error category and severity
        error_code, severity, category, recoverable = self._classify_exception(exc)

        error_details = ErrorDetails(
            error_code=error_code,
            message=str(exc),
            context=context,
            severity=severity,
            category=category,
            recoverable=recoverable,
        )

        # Log the error
        self.logger.error(
            f"Error occurred: {error_code} - {str(exc)}",
            extra={
                "correlation_id": context.correlation_id,
                "error_code": error_code,
                "severity": severity,
                "category": category,
                "recoverable": recoverable,
            },
        )

        # Store error report
        self.error_reports.append(error_details)

        return error_details

    def _classify_exception(self, exc: Exception) -> tuple[str, str, str, bool]:
        """Classify exception and determine appropriate response."""
        exc_type = type(exc).__name__

        # Authentication errors
        if "auth" in exc_type.lower() or "unauthorized" in str(exc).lower():
            return "AUTH_ERROR", "error", "authentication", False

        # Authorization errors
        if "permission" in exc_type.lower() or "forbidden" in str(exc).lower():
            return "PERMISSION_DENIED", "error", "authorization", False

        # Validation errors
        if "validation" in exc_type.lower() or "invalid" in str(exc).lower():
            return "VALIDATION_ERROR", "warning", "validation", True

        # Rate limiting errors
        if "rate" in exc_type.lower() or "limit" in str(exc).lower():
            return "RATE_LIMIT_EXCEEDED", "warning", "rate_limiting", True

        # Network/connection errors
        if "connection" in exc_type.lower() or "timeout" in str(exc).lower():
            return "NETWORK_ERROR", "error", "network", True

        # Resource errors
        if "resource" in exc_type.lower() or "not found" in str(exc).lower():
            return "RESOURCE_NOT_FOUND", "error", "resource", False

        # Server errors
        if "server" in exc_type.lower() or "internal" in str(exc).lower():
            return "INTERNAL_SERVER_ERROR", "critical", "server", True

        # Default classification
        return "GENERAL_ERROR", "error", "general", True

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_reports:
            return {}

        stats = {
            "total_errors": len(self.error_reports),
            "by_severity": {},
            "by_category": {},
            "by_code": {},
            "recent_errors": [],
        }

        # Count by severity
        for error in self.error_reports:
            stats["by_severity"][error.severity] = (
                stats["by_severity"].get(error.severity, 0) + 1
            )
            stats["by_category"][error.category] = (
                stats["by_category"].get(error.category, 0) + 1
            )
            stats["by_code"][error.error_code] = (
                stats["by_code"].get(error.error_code, 0) + 1
            )

        # Get recent errors (last 10)
        recent_errors = sorted(
            [e for e in self.error_reports if e.context],
            key=lambda x: x.context.timestamp,
            reverse=True,
        )[:10]
        stats["recent_errors"] = [
            {
                "code": error.error_code,
                "message": error.message,
                "timestamp": error.context.timestamp.isoformat(),
                "correlation_id": error.context.correlation_id,
            }
            for error in recent_errors
        ]

        return stats

    def clear_error_reports(self):
        """Clear stored error reports."""
        self.error_reports.clear()


class ErrorRecoveryHandler:
    """Handles error recovery strategies."""

    def __init__(self):
        """Initialize error recovery handler."""
        self.logger = get_logger(__name__)

    def should_retry(self, error_details: ErrorDetails, attempt_count: int) -> bool:
        """Determine if operation should be retried."""
        if not error_details.recoverable:
            return False

        # Don't retry too many times
        if attempt_count >= 3:
            return False

        # Don't retry authentication/authorization errors
        if error_details.category in ["authentication", "authorization"]:
            return False

        return True

    def get_retry_delay(self, attempt_count: int, base_delay: float = 1.0) -> float:
        """Calculate retry delay with exponential backoff."""
        return base_delay * (2 ** (attempt_count - 1))

    def create_retry_response(
        self, error_details: ErrorDetails, attempt_count: int
    ) -> dict[str, Any]:
        """Create response for retry scenario."""
        retry_delay = self.get_retry_delay(attempt_count)

        return {
            "error": {
                "code": error_details.error_code,
                "message": error_details.message,
                "retry_after": retry_delay,
                "attempt_count": attempt_count,
                "max_attempts": 3,
            }
        }


# Global error handler instance
error_handler = ErrorHandler()
recovery_handler = ErrorRecoveryHandler()


def handle_request_error(
    exc: Exception, request: Any = None, user_id: str | None = None
) -> dict[str, Any]:
    """Handle request error and return structured response."""
    context = error_handler.create_error_context(request, user_id)
    error_details = error_handler.handle_exception(exc, context)
    return error_handler.create_error_response(error_details)


def get_error_stats() -> dict[str, Any]:
    """Get error statistics."""
    return error_handler.get_error_statistics()

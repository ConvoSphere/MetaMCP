"""
Logging utilities for MCP Meta-Server

This module provides structured logging functionality using structlog,
with support for JSON formatting, log rotation, and various output formats.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    structured: bool = True,
    json_format: bool = True
) -> None:
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        structured: Enable structured logging with structlog
        json_format: Use JSON format for logs
    """
    # Configure standard library logging first
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        stream=sys.stdout,
    )

    # Create processors chain
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup file logging if specified
    if log_file:
        setup_file_logging(log_file, log_level)


def setup_file_logging(log_file: str, log_level: str = "INFO") -> None:
    """
    Setup file-based logging with rotation.
    
    Args:
        log_file: Path to log file
        log_level: Logging level
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=5,
        encoding="utf-8"
    )

    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger for the given name.
    
    Args:
        name: Logger name, typically __name__
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class AuditLogger:
    """
    Specialized logger for audit events.
    
    Provides structured logging for security and compliance auditing.
    """

    def __init__(self, name: str = "audit"):
        """
        Initialize audit logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)

    def log_authentication(
        self,
        user_id: str,
        success: bool,
        method: str,
        ip_address: str,
        user_agent: str | None = None,
        **kwargs
    ) -> None:
        """
        Log authentication events.
        
        Args:
            user_id: User identifier
            success: Whether authentication succeeded
            method: Authentication method
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional context
        """
        self.logger.info(
            "authentication_event",
            user_id=user_id,
            success=success,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )

    def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        policy: str | None = None,
        **kwargs
    ) -> None:
        """
        Log authorization events.
        
        Args:
            user_id: User identifier
            resource: Resource being accessed
            action: Action being performed
            success: Whether authorization succeeded
            policy: Policy that was evaluated
            **kwargs: Additional context
        """
        self.logger.info(
            "authorization_event",
            user_id=user_id,
            resource=resource,
            action=action,
            success=success,
            policy=policy,
            **kwargs
        )

    def log_tool_execution(
        self,
        user_id: str,
        tool_name: str,
        success: bool,
        execution_time: float,
        input_data: dict[str, Any] | None = None,
        error: str | None = None,
        **kwargs
    ) -> None:
        """
        Log tool execution events.
        
        Args:
            user_id: User identifier
            tool_name: Name of executed tool
            success: Whether execution succeeded
            execution_time: Execution time in seconds
            input_data: Tool input data (sanitized)
            error: Error message if failed
            **kwargs: Additional context
        """
        self.logger.info(
            "tool_execution_event",
            user_id=user_id,
            tool_name=tool_name,
            success=success,
            execution_time=execution_time,
            input_data=input_data,
            error=error,
            **kwargs
        )

    def log_policy_evaluation(
        self,
        user_id: str,
        policy_name: str,
        resource: str,
        action: str,
        result: str,
        evaluation_time: float,
        **kwargs
    ) -> None:
        """
        Log policy evaluation events.
        
        Args:
            user_id: User identifier
            policy_name: Name of evaluated policy
            resource: Resource being accessed
            action: Action being performed
            result: Policy evaluation result
            evaluation_time: Evaluation time in seconds
            **kwargs: Additional context
        """
        self.logger.info(
            "policy_evaluation_event",
            user_id=user_id,
            policy_name=policy_name,
            resource=resource,
            action=action,
            result=result,
            evaluation_time=evaluation_time,
            **kwargs
        )


class PerformanceLogger:
    """
    Logger for performance metrics and timing information.
    """

    def __init__(self, name: str = "performance"):
        """
        Initialize performance logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)

    def log_request_timing(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        **kwargs
    ) -> None:
        """
        Log HTTP request timing.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time: Response time in seconds
            **kwargs: Additional context
        """
        self.logger.info(
            "request_timing",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            **kwargs
        )

    def log_database_timing(
        self,
        operation: str,
        table: str,
        query_time: float,
        rows_affected: int | None = None,
        **kwargs
    ) -> None:
        """
        Log database operation timing.
        
        Args:
            operation: Database operation type
            table: Database table
            query_time: Query execution time in seconds
            rows_affected: Number of rows affected
            **kwargs: Additional context
        """
        self.logger.info(
            "database_timing",
            operation=operation,
            table=table,
            query_time=query_time,
            rows_affected=rows_affected,
            **kwargs
        )

    def log_vector_search_timing(
        self,
        query: str,
        results_count: int,
        search_time: float,
        similarity_threshold: float,
        **kwargs
    ) -> None:
        """
        Log vector search timing.
        
        Args:
            query: Search query
            results_count: Number of results returned
            search_time: Search time in seconds
            similarity_threshold: Similarity threshold used
            **kwargs: Additional context
        """
        self.logger.info(
            "vector_search_timing",
            query_preview=query[:100] + "..." if len(query) > 100 else query,
            results_count=results_count,
            search_time=search_time,
            similarity_threshold=similarity_threshold,
            **kwargs
        )

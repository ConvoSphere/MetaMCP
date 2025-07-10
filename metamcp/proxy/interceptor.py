"""
Tool Call Interceptor

This module provides interception functionality for tool calls,
allowing for pre/post processing, validation, and transformation.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, UTC
import asyncio

from ..exceptions import ProxyError, ToolExecutionError
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InterceptorContext:
    """Context for tool call interception."""
    tool_name: str
    server_id: str
    arguments: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.metadata is None:
            self.metadata = {}


@dataclass
class InterceptorResult:
    """Result from tool call interception."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    modified_arguments: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolCallInterceptor:
    """
    Interceptor for tool calls with pre/post processing hooks.
    
    This class provides a framework for intercepting tool calls
    and adding middleware functionality like validation, transformation,
    logging, and security checks.
    """

    def __init__(self):
        """Initialize the tool call interceptor."""
        self.pre_hooks: List[Callable] = []
        self.post_hooks: List[Callable] = []
        self.error_hooks: List[Callable] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the interceptor."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Tool Call Interceptor...")
            
            # Register default hooks
            self._register_default_hooks()
            
            self._initialized = True
            logger.info("Tool Call Interceptor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Tool Call Interceptor: {e}")
            raise ProxyError(f"Initialization failed: {str(e)}")

    def _register_default_hooks(self) -> None:
        """Register default interception hooks."""
        # Pre-execution hooks
        self.add_pre_hook(self._log_tool_call)
        self.add_pre_hook(self._validate_arguments)
        self.add_pre_hook(self._rate_limit_check)
        
        # Post-execution hooks
        self.add_post_hook(self._log_tool_result)
        self.add_post_hook(self._transform_result)
        
        # Error hooks
        self.add_error_hook(self._log_tool_error)
        self.add_error_hook(self._handle_error)

    def add_pre_hook(self, hook: Callable) -> None:
        """
        Add a pre-execution hook.
        
        Args:
            hook: Hook function to call before tool execution
        """
        self.pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable) -> None:
        """
        Add a post-execution hook.
        
        Args:
            hook: Hook function to call after tool execution
        """
        self.post_hooks.append(hook)

    def add_error_hook(self, hook: Callable) -> None:
        """
        Add an error handling hook.
        
        Args:
            hook: Hook function to call on error
        """
        self.error_hooks.append(hook)

    async def intercept_tool_call(
        self,
        context: InterceptorContext,
        tool_executor: Callable
    ) -> InterceptorResult:
        """
        Intercept a tool call with pre/post processing.
        
        Args:
            context: Interception context
            tool_executor: Function to execute the tool
            
        Returns:
            Interception result
        """
        try:
            # Pre-execution hooks
            modified_context = await self._run_pre_hooks(context)
            
            # Execute tool
            result = await tool_executor(modified_context.arguments)
            
            # Post-execution hooks
            final_result = await self._run_post_hooks(modified_context, result)
            
            return InterceptorResult(
                success=True,
                result=final_result,
                metadata={"intercepted": True}
            )
            
        except Exception as e:
            # Error hooks
            await self._run_error_hooks(context, e)
            
            return InterceptorResult(
                success=False,
                error=str(e),
                metadata={"intercepted": True, "error": True}
            )

    async def _run_pre_hooks(self, context: InterceptorContext) -> InterceptorContext:
        """Run pre-execution hooks."""
        modified_context = context
        
        for hook in self.pre_hooks:
            try:
                result = await hook(modified_context)
                if result is not None:
                    modified_context = result
            except Exception as e:
                logger.warning(f"Pre-hook failed: {e}")
                
        return modified_context

    async def _run_post_hooks(
        self,
        context: InterceptorContext,
        result: Any
    ) -> Any:
        """Run post-execution hooks."""
        modified_result = result
        
        for hook in self.post_hooks:
            try:
                hook_result = await hook(context, modified_result)
                if hook_result is not None:
                    modified_result = hook_result
            except Exception as e:
                logger.warning(f"Post-hook failed: {e}")
                
        return modified_result

    async def _run_error_hooks(
        self,
        context: InterceptorContext,
        error: Exception
    ) -> None:
        """Run error handling hooks."""
        for hook in self.error_hooks:
            try:
                await hook(context, error)
            except Exception as e:
                logger.warning(f"Error hook failed: {e}")

    async def _log_tool_call(self, context: InterceptorContext) -> None:
        """Log tool call for monitoring."""
        logger.info(
            f"Tool call: {context.tool_name} on server {context.server_id} "
            f"by user {context.user_id} at {context.timestamp}"
        )

    async def _validate_arguments(self, context: InterceptorContext) -> InterceptorContext:
        """Validate tool arguments."""
        # Basic validation - can be extended with schema validation
        if not isinstance(context.arguments, dict):
            raise ToolExecutionError("Arguments must be a dictionary")
            
        # Check for required arguments (tool-specific)
        required_args = self._get_required_arguments(context.tool_name)
        for arg in required_args:
            if arg not in context.arguments:
                raise ToolExecutionError(f"Missing required argument: {arg}")
                
        return context

    def _get_required_arguments(self, tool_name: str) -> List[str]:
        """Get required arguments for a tool."""
        # This would be tool-specific - for now return empty list
        return []

    async def _rate_limit_check(self, context: InterceptorContext) -> InterceptorContext:
        """Check rate limits for tool calls."""
        # This would integrate with a rate limiting system
        # For now, just log the check
        logger.debug(f"Rate limit check for {context.tool_name}")
        return context

    async def _log_tool_result(
        self,
        context: InterceptorContext,
        result: Any
    ) -> None:
        """Log tool execution result."""
        logger.info(
            f"Tool completed: {context.tool_name} on server {context.server_id} "
            f"with result type: {type(result).__name__}"
        )

    async def _transform_result(
        self,
        context: InterceptorContext,
        result: Any
    ) -> Any:
        """Transform tool result if needed."""
        # This could format results, add metadata, etc.
        return result

    async def _log_tool_error(
        self,
        context: InterceptorContext,
        error: Exception
    ) -> None:
        """Log tool execution error."""
        logger.error(
            f"Tool error: {context.tool_name} on server {context.server_id} "
            f"failed with: {str(error)}"
        )

    async def _handle_error(
        self,
        context: InterceptorContext,
        error: Exception
    ) -> None:
        """Handle tool execution errors."""
        # This could trigger alerts, retry logic, etc.
        logger.error(f"Error handling for {context.tool_name}: {str(error)}")

    async def create_context(
        self,
        tool_name: str,
        server_id: str,
        arguments: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InterceptorContext:
        """
        Create an interception context.
        
        Args:
            tool_name: Name of the tool being called
            server_id: ID of the server hosting the tool
            arguments: Tool arguments
            user_id: User ID making the call
            session_id: Session ID
            request_id: Request ID for tracing
            metadata: Additional metadata
            
        Returns:
            Interception context
        """
        return InterceptorContext(
            tool_name=tool_name,
            server_id=server_id,
            arguments=arguments,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            metadata=metadata or {}
        )

    async def shutdown(self) -> None:
        """Shutdown the interceptor."""
        logger.info("Shutting down Tool Call Interceptor...")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the interceptor is initialized."""
        return self._initialized 
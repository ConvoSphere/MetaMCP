"""
MCP Meta-Server Core Implementation

This module contains the main MetaMCPServer class that orchestrates all
components of the MCP Meta-Server including tool registry, vector search,
policy engine, and MCP protocol handling.
"""

import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from .config import get_settings
from .exceptions import MetaMCPError, ServiceUnavailableError
from .utils.logging import get_logger, AuditLogger, PerformanceLogger
from .tools.registry import ToolRegistry
from .vector.client import VectorSearchClient
from .security.auth import AuthManager
from .security.policies import PolicyEngine
from .mcp.server import MCPServerHandler
from .llm.service import LLMService


logger = get_logger(__name__)
settings = get_settings()


class MetaMCPServer:
    """
    Main MCP Meta-Server class.
    
    This class orchestrates all components of the MCP Meta-Server:
    - Tool Registry and Management
    - Vector Search for semantic tool discovery
    - Security and Policy Engine
    - MCP Protocol Server
    - LLM Integration for tool descriptions
    """
    
    def __init__(self):
        """Initialize the MCP Meta-Server."""
        self.settings = settings
        self.logger = logger
        self.audit_logger = AuditLogger()
        self.performance_logger = PerformanceLogger()
        
        # Component instances
        self.tool_registry: Optional[ToolRegistry] = None
        self.vector_client: Optional[VectorSearchClient] = None
        self.auth_manager: Optional[AuthManager] = None
        self.policy_engine: Optional[PolicyEngine] = None
        self.mcp_handler: Optional[MCPServerHandler] = None
        self.llm_service: Optional[LLMService] = None
        
        # State management
        self._initialized = False
        self._shutting_down = False
        
    async def initialize(self) -> None:
        """
        Initialize all server components.
        
        Raises:
            ServiceUnavailableError: If initialization fails
        """
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing MCP Meta-Server components...")
            
            # Initialize core services in dependency order
            await self._initialize_llm_service()
            await self._initialize_vector_client()
            await self._initialize_auth_manager()
            await self._initialize_policy_engine()
            await self._initialize_tool_registry()
            await self._initialize_mcp_handler()
            
            # Perform health checks
            await self._perform_initial_health_checks()
            
            self._initialized = True
            self.logger.info("MCP Meta-Server initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP Meta-Server: {e}")
            await self.shutdown()
            raise ServiceUnavailableError(
                service="MCP Meta-Server",
                reason=f"Initialization failed: {str(e)}"
            )
    
    async def _initialize_llm_service(self) -> None:
        """Initialize LLM service for embeddings and descriptions."""
        self.logger.info("Initializing LLM service...")
        self.llm_service = LLMService(self.settings)
        await self.llm_service.initialize()
        
    async def _initialize_vector_client(self) -> None:
        """Initialize vector search client."""
        self.logger.info("Initializing vector search client...")
        self.vector_client = VectorSearchClient(
            url=self.settings.weaviate_url,
            api_key=self.settings.weaviate_api_key,
            timeout=self.settings.weaviate_timeout
        )
        await self.vector_client.initialize()
        
    async def _initialize_auth_manager(self) -> None:
        """Initialize authentication manager."""
        self.logger.info("Initializing authentication manager...")
        self.auth_manager = AuthManager(self.settings)
        await self.auth_manager.initialize()
        
    async def _initialize_policy_engine(self) -> None:
        """Initialize policy engine."""
        self.logger.info("Initializing policy engine...")
        self.policy_engine = PolicyEngine(
            engine_type=self.settings.policy_engine,
            opa_url=self.settings.opa_url if self.settings.policy_engine.value == "opa" else None
        )
        await self.policy_engine.initialize()
        
    async def _initialize_tool_registry(self) -> None:
        """Initialize tool registry."""
        self.logger.info("Initializing tool registry...")
        self.tool_registry = ToolRegistry(
            vector_client=self.vector_client,
            llm_service=self.llm_service,
            policy_engine=self.policy_engine
        )
        await self.tool_registry.initialize()
        
    async def _initialize_mcp_handler(self) -> None:
        """Initialize MCP protocol handler."""
        self.logger.info("Initializing MCP protocol handler...")
        self.mcp_handler = MCPServerHandler(
            tool_registry=self.tool_registry,
            auth_manager=self.auth_manager,
            policy_engine=self.policy_engine,
            audit_logger=self.audit_logger
        )
        await self.mcp_handler.initialize()
        
    async def _perform_initial_health_checks(self) -> None:
        """Perform health checks on all components."""
        self.logger.info("Performing initial health checks...")
        
        health_results = await self.get_health_status()
        
        failed_components = [
            component for component, status in health_results.items()
            if not status.get("healthy", False)
        ]
        
        if failed_components:
            raise ServiceUnavailableError(
                service="Health Check",
                reason=f"Failed components: {', '.join(failed_components)}"
            )
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown all server components.
        """
        if self._shutting_down:
            return
        
        self._shutting_down = True
        self.logger.info("Shutting down MCP Meta-Server...")
        
        # Shutdown components in reverse order
        components = [
            ("MCP Handler", self.mcp_handler),
            ("Tool Registry", self.tool_registry),
            ("Policy Engine", self.policy_engine),
            ("Auth Manager", self.auth_manager),
            ("Vector Client", self.vector_client),
            ("LLM Service", self.llm_service),
        ]
        
        for name, component in components:
            if component:
                try:
                    self.logger.info(f"Shutting down {name}...")
                    await component.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down {name}: {e}")
        
        self._initialized = False
        self.logger.info("MCP Meta-Server shutdown completed")
    
    async def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all components.
        
        Returns:
            Dictionary with component health status
        """
        health_status = {}
        
        components = [
            ("llm_service", self.llm_service),
            ("vector_client", self.vector_client),
            ("auth_manager", self.auth_manager),
            ("policy_engine", self.policy_engine),
            ("tool_registry", self.tool_registry),
            ("mcp_handler", self.mcp_handler),
        ]
        
        for name, component in components:
            if component:
                try:
                    status = await component.health_check()
                    health_status[name] = status
                except Exception as e:
                    health_status[name] = {
                        "healthy": False,
                        "error": str(e),
                        "timestamp": self._get_timestamp()
                    }
            else:
                health_status[name] = {
                    "healthy": False,
                    "error": "Component not initialized",
                    "timestamp": self._get_timestamp()
                }
        
        return health_status
    
    async def search_tools(
        self,
        query: str,
        user_id: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for tools using semantic search.
        
        Args:
            query: Search query describing the desired functionality
            user_id: User ID for authorization
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of matching tools with metadata
            
        Raises:
            MetaMCPError: If search fails
        """
        if not self._initialized:
            raise ServiceUnavailableError(
                service="Tool Search",
                reason="Server not initialized"
            )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Perform semantic search
            results = await self.tool_registry.search_tools(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Filter by user permissions
            authorized_results = []
            for tool in results:
                if await self._check_tool_access(user_id, tool["name"], "read"):
                    authorized_results.append(tool)
            
            # Log performance metrics
            search_time = asyncio.get_event_loop().time() - start_time
            self.performance_logger.log_vector_search_timing(
                query=query,
                results_count=len(authorized_results),
                search_time=search_time,
                similarity_threshold=similarity_threshold,
                user_id=user_id
            )
            
            return authorized_results
            
        except Exception as e:
            self.logger.error(f"Tool search failed: {e}")
            raise
    
    async def execute_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute a tool with the given input data.
        
        Args:
            tool_name: Name of the tool to execute
            input_data: Input data for the tool
            user_id: User ID for authorization
            
        Returns:
            Tool execution result
            
        Raises:
            MetaMCPError: If execution fails
        """
        if not self._initialized:
            raise ServiceUnavailableError(
                service="Tool Execution",
                reason="Server not initialized"
            )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check authorization
            if not await self._check_tool_access(user_id, tool_name, "execute"):
                raise AuthorizationError(
                    resource=tool_name,
                    action="execute"
                )
            
            # Execute tool
            result = await self.tool_registry.execute_tool(
                tool_name=tool_name,
                input_data=input_data
            )
            
            # Log audit event
            execution_time = asyncio.get_event_loop().time() - start_time
            self.audit_logger.log_tool_execution(
                user_id=user_id,
                tool_name=tool_name,
                success=True,
                execution_time=execution_time,
                input_data=self._sanitize_sensitive_data(input_data)
            )
            
            return result
            
        except Exception as e:
            # Log failed execution
            execution_time = asyncio.get_event_loop().time() - start_time
            self.audit_logger.log_tool_execution(
                user_id=user_id,
                tool_name=tool_name,
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
            raise
    
    async def register_tool(
        self,
        tool_data: Dict[str, Any],
        user_id: str
    ) -> str:
        """
        Register a new tool in the registry.
        
        Args:
            tool_data: Tool registration data
            user_id: User ID for authorization
            
        Returns:
            Tool ID
            
        Raises:
            MetaMCPError: If registration fails
        """
        if not self._initialized:
            raise ServiceUnavailableError(
                service="Tool Registration",
                reason="Server not initialized"
            )
        
        try:
            # Check authorization
            if not await self._check_tool_access(user_id, "registry", "create"):
                raise AuthorizationError(
                    resource="registry",
                    action="create"
                )
            
            # Register tool
            tool_id = await self.tool_registry.register_tool(tool_data)
            
            # Log audit event
            self.audit_logger.log_authorization(
                user_id=user_id,
                resource="tool_registry",
                action="create",
                success=True,
                tool_name=tool_data.get("name")
            )
            
            return tool_id
            
        except Exception as e:
            self.logger.error(f"Tool registration failed: {e}")
            raise
    
    async def _check_tool_access(
        self,
        user_id: str,
        tool_name: str,
        action: str
    ) -> bool:
        """
        Check if user has access to perform action on tool.
        
        Args:
            user_id: User ID
            tool_name: Tool name
            action: Action to perform
            
        Returns:
            True if access is allowed
        """
        try:
            policy_input = {
                "user_id": user_id,
                "resource": tool_name,
                "action": action
            }
            
            result = await self.policy_engine.evaluate(
                policy="tool_access",
                input_data=policy_input
            )
            
            return result.get("allowed", False)
            
        except Exception as e:
            self.logger.error(f"Policy evaluation failed: {e}")
            return False
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data for logging."""
        sensitive_keys = ["password", "secret", "token", "key", "credential"]
        sanitized = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    @property
    def is_initialized(self) -> bool:
        """Check if server is initialized."""
        return self._initialized
    
    @property
    def is_shutting_down(self) -> bool:
        """Check if server is shutting down."""
        return self._shutting_down
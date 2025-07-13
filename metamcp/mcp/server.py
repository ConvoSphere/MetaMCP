"""
MCP Server Module

This module provides the MCP (Model Context Protocol) server implementation
using FastMCP for handling MCP protocol communication.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastmcp import FastMCP
from fastmcp.models import (
    Resource,
    TextContent,
    Tool,
)

from ..config import get_settings
from ..exceptions import MetaMCPException
from ..monitoring.telemetry import TelemetryManager
from ..security.auth import AuthManager
from ..security.policies import PolicyEngine
from ..tools.registry import ToolRegistry
from ..utils.logging import get_logger
from ..vector.client import VectorSearchClient

logger = get_logger(__name__)
settings = get_settings()


class MCPServer:
    """
    MCP Server implementation using FastMCP.
    
    This class handles MCP protocol communication, tool discovery,
    and execution with integrated security and monitoring.
    """

    def __init__(self):
        """Initialize the MCP server."""
        self.settings = settings
        self.fastmcp: FastMCP | None = None
        self.telemetry_manager: TelemetryManager | None = None
        self.tool_registry: ToolRegistry | None = None
        self.vector_client: VectorSearchClient | None = None
        self.auth_manager: AuthManager | None = None
        self.policy_engine: PolicyEngine | None = None
        self.router = APIRouter()

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the MCP server components."""
        try:
            logger.info("Initializing MCP Server...")

            # Initialize components
            await self._initialize_components()

            # Initialize FastMCP
            await self._initialize_fastmcp()

            # Setup routes
            self._setup_routes()

            self._initialized = True
            logger.info("MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP Server: {e}")
            raise

    async def _initialize_components(self) -> None:
        """Initialize server components."""
        try:
            # Initialize telemetry
            if self.settings.telemetry_enabled:
                self.telemetry_manager = TelemetryManager()
                await self.telemetry_manager.initialize()

            # Initialize vector client
            if self.settings.vector_search_enabled:
                self.vector_client = VectorSearchClient()
                await self.vector_client.initialize()

            # Initialize auth manager
            self.auth_manager = AuthManager()
            await self.auth_manager.initialize()

            # Initialize policy engine
            if self.settings.policy_enforcement_enabled:
                self.policy_engine = PolicyEngine()
                await self.policy_engine.initialize()

            # Initialize tool registry
            self.tool_registry = ToolRegistry(
                vector_client=self.vector_client,
                policy_engine=self.policy_engine
            )
            await self.tool_registry.initialize()

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def _initialize_fastmcp(self) -> None:
        """Initialize FastMCP server."""
        try:
            self.fastmcp = FastMCP(
                name="metamcp",
                version="1.0.0"
            )

            # Register handlers
            self.fastmcp.list_tools = self._handle_list_tools
            self.fastmcp.call_tool = self._handle_call_tool
            self.fastmcp.list_resources = self._handle_list_resources
            self.fastmcp.read_resource = self._handle_read_resource
            self.fastmcp.list_prompts = self._handle_list_prompts
            self.fastmcp.show_prompt = self._handle_show_prompt

            logger.info("FastMCP initialized")

        except Exception as e:
            logger.error(f"Failed to initialize FastMCP: {e}")
            raise

    def _setup_routes(self) -> None:
        """Setup API routes."""

        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for MCP communication."""
            await websocket.accept()

            try:
                # Handle WebSocket communication directly
                await self.fastmcp.handle_websocket(websocket)

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close()

        @self.router.get("/tools")
        async def list_tools():
            """List available tools."""
            try:
                tools = await self._handle_list_tools()
                return {"tools": tools}
            except Exception as e:
                logger.error(f"Failed to list tools: {e}")
                raise MetaMCPException(
                    error_code="tool_list_error",
                    message="Failed to list tools",
                    details=str(e)
                )

        @self.router.post("/tools/{tool_name}/execute")
        async def execute_tool(tool_name: str, input_data: dict[str, Any]):
            """Execute a tool."""
            try:
                result = await self._handle_call_tool(tool_name, input_data)
                return {"result": result}
            except Exception as e:
                logger.error(f"Failed to execute tool {tool_name}: {e}")
                raise MetaMCPException(
                    error_code="tool_execution_error",
                    message=f"Failed to execute tool {tool_name}",
                    details=str(e)
                )

    async def _handle_list_tools(self) -> list[Tool]:
        """Handle list tools request."""
        if not self.tool_registry:
            return []

        try:
            tools = await self.tool_registry.list_tools()
            return tools

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def _handle_call_tool(
        self,
        name: str,
        arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle tool execution request."""
        if not self.tool_registry:
            raise MetaMCPException(
                error_code="tool_registry_unavailable",
                message="Tool registry not available"
            )

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute tool
            result = await self.tool_registry.execute_tool(
                tool_name=name,
                input_data=arguments
            )

            # Record metrics
            if self.telemetry_manager:
                duration = asyncio.get_event_loop().time() - start_time
                self.telemetry_manager.record_tool_execution(
                    tool_name=name,
                    success=True,
                    duration=duration
                )

            # Convert result to MCP format
            content = TextContent(
                type="text",
                text=str(result)
            )

            return [content]

        except Exception as e:
            # Record error metrics
            if self.telemetry_manager:
                duration = asyncio.get_event_loop().time() - start_time
                self.telemetry_manager.record_tool_execution(
                    tool_name=name,
                    success=False,
                    duration=duration
                )

            logger.error(f"Tool execution failed: {e}")
            raise MetaMCPException(
                error_code="tool_execution_error",
                message=f"Tool execution failed: {str(e)}"
            )

    async def _handle_list_resources(self) -> list[Resource]:
        """Handle list resources request."""
        # For now, return empty list
        # This can be extended to list available resources
        return []

    async def _handle_read_resource(self, uri: str) -> list[TextContent]:
        """Handle read resource request."""
        # For now, return empty list
        # This can be extended to read resources
        return []

    async def _handle_list_prompts(self) -> list[str]:
        """Handle list prompts request."""
        # For now, return empty list
        # This can be extended to list available prompts
        return []

    async def _handle_show_prompt(self, name: str) -> list[TextContent]:
        """Handle show prompt request."""
        # For now, return empty list
        # This can be extended to show prompts
        return []

    async def search_tools(
        self,
        query: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """Search for tools using semantic search."""
        if not self.tool_registry:
            return []

        try:
            import time
            start_time = time.time()
            
            results = await self.tool_registry.search_tools(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )

            # Calculate actual duration
            duration = time.time() - start_time

            # Record vector search metrics
            if self.telemetry_manager:
                self.telemetry_manager.record_vector_search(
                    query_length=len(query),
                    result_count=len(results),
                    duration=duration
                )

            logger.info(f"Vector search completed in {duration:.3f}s, found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Tool search failed: {e}")
            return []

    async def shutdown(self) -> None:
        """Shutdown the MCP server."""
        if not self._initialized:
            return

        logger.info("Shutting down MCP Server...")

        try:
            # Shutdown components
            if self.tool_registry:
                await self.tool_registry.shutdown()

            if self.vector_client:
                await self.vector_client.shutdown()

            if self.auth_manager:
                await self.auth_manager.shutdown()

            if self.policy_engine:
                await self.policy_engine.shutdown()

            if self.telemetry_manager:
                await self.telemetry_manager.shutdown()

            self._initialized = False
            logger.info("MCP Server shutdown complete")

        except Exception as e:
            logger.error(f"Error during MCP Server shutdown: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if MCP server is initialized."""
        return self._initialized

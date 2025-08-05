"""
MCP Server Module

This module provides the MCP (Model Context Protocol) server implementation
using FastMCP for handling MCP protocol communication with support for
WebSocket, HTTP, and stdio transports.
"""

import asyncio
import json
import sys
from typing import Any, AsyncGenerator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastmcp import FastMCP
from mcp.types import Resource, TextContent, Tool

from ..config import get_settings
from ..exceptions import MetaMCPException
from ..monitoring.telemetry import TelemetryManager
from ..security.auth import AuthManager
from ..security.policies import PolicyEngine, PolicyEngineType
from ..tools.registry import ToolRegistry
from ..utils.logging import get_logger
from ..vector.client import VectorSearchClient

logger = get_logger(__name__)
settings = get_settings()


class StdioMCPServer:
    """MCP Server implementation for stdio transport."""
    
    def __init__(self, mcp_server: 'MCPServer'):
        """Initialize stdio server."""
        self.mcp_server = mcp_server
        self.running = False
    
    async def start(self) -> None:
        """Start the stdio MCP server."""
        self.running = True
        logger.info("Starting stdio MCP server...")
        
        try:
            while self.running:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    # Parse JSON-RPC message
                    message = json.loads(line.strip())
                    
                    # Process message
                    response = await self._process_message(message)
                    
                    # Send response to stdout
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": str(e)
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                    
        except KeyboardInterrupt:
            logger.info("Stdio server interrupted")
        except Exception as e:
            logger.error(f"Stdio server error: {e}")
        finally:
            self.running = False
            logger.info("Stdio server stopped")
    
    async def _process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Process MCP message and return response."""
        try:
            method = message.get("method")
            message_id = message.get("id")
            params = message.get("params", {})
            
            if method == "initialize":
                return await self._handle_initialize(message_id, params)
            elif method == "tools/list":
                return await self._handle_list_tools(message_id)
            elif method == "tools/call":
                return await self._handle_call_tool(message_id, params)
            elif method == "resources/list":
                return await self._handle_list_resources(message_id)
            elif method == "resources/read":
                return await self._handle_read_resource(message_id, params)
            elif method == "prompts/list":
                return await self._handle_list_prompts(message_id)
            elif method == "prompts/show":
                return await self._handle_show_prompt(message_id, params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def _handle_initialize(self, message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize message."""
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "protocolVersion": "1.0.0",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "MetaMCP",
                    "version": "1.0.0"
                }
            }
        }
    
    async def _handle_list_tools(self, message_id: Any) -> dict[str, Any]:
        """Handle tools/list message."""
        try:
            tools = await self.mcp_server._handle_list_tools()
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"tools": tools}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to list tools: {str(e)}"
                }
            }
    
    async def _handle_call_tool(self, message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call message."""
        try:
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not name:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing tool name"
                    }
                }
            
            result = await self.mcp_server._handle_call_tool(name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"content": result}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }
    
    async def _handle_list_resources(self, message_id: Any) -> dict[str, Any]:
        """Handle resources/list message."""
        try:
            resources = await self.mcp_server._handle_list_resources()
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"resources": resources}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to list resources: {str(e)}"
                }
            }
    
    async def _handle_read_resource(self, message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/read message."""
        try:
            uri = params.get("uri")
            if not uri:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing resource URI"
                    }
                }
            
            content = await self.mcp_server._handle_read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"contents": content}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to read resource: {str(e)}"
                }
            }
    
    async def _handle_list_prompts(self, message_id: Any) -> dict[str, Any]:
        """Handle prompts/list message."""
        try:
            prompts = await self.mcp_server._handle_list_prompts()
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"prompts": prompts}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to list prompts: {str(e)}"
                }
            }
    
    async def _handle_show_prompt(self, message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/show message."""
        try:
            name = params.get("name")
            if not name:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing prompt name"
                    }
                }
            
            content = await self.mcp_server._handle_show_prompt(name)
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"contents": content}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to show prompt: {str(e)}"
                }
            }
    
    def stop(self) -> None:
        """Stop the stdio server."""
        self.running = False


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
        self.stdio_server: StdioMCPServer | None = None
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

            # Initialize stdio server
            await self._initialize_stdio_server()

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
                self.vector_client = VectorSearchClient(
                    url=self.settings.weaviate_url,
                    api_key=self.settings.weaviate_api_key,
                )
                await self.vector_client.initialize()

            # Initialize auth manager
            self.auth_manager = AuthManager(self.settings)
            await self.auth_manager.initialize()

            # Initialize policy engine
            if self.settings.policy_enforcement_enabled:
                self.policy_engine = PolicyEngine(PolicyEngineType.INTERNAL)
                await self.policy_engine.initialize()

            # Initialize LLM service
            from ..llm.service import LLMService

            self.llm_service = LLMService(self.settings)
            await self.llm_service.initialize()

            # Initialize tool registry
            if self.vector_client and self.llm_service and self.policy_engine:
                self.tool_registry = ToolRegistry(
                    vector_client=self.vector_client,
                    llm_service=self.llm_service,
                    policy_engine=self.policy_engine,
                )
                await self.tool_registry.initialize()
            else:
                logger.warning(
                    "Tool registry not initialized due to missing dependencies"
                )

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def _initialize_fastmcp(self) -> None:
        """Initialize FastMCP server."""
        try:
            self.fastmcp = FastMCP(name="metamcp", version="1.0.0")

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

    async def _initialize_stdio_server(self) -> None:
        """Initialize the stdio MCP server."""
        self.stdio_server = StdioMCPServer(self)
        logger.info("Stdio MCP server initialized")

    def _setup_routes(self) -> None:
        """Setup API routes."""
        logger.info("Setting up MCP routes...")

        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for MCP communication."""
            logger.info("WebSocket connection attempt")
            await websocket.accept()
            logger.info("WebSocket connection accepted")

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
            logger.info("MCP tools endpoint called")
            try:
                tools = await self._handle_list_tools()
                return {"tools": tools}
            except Exception as e:
                logger.error(f"Failed to list tools: {e}")
                raise MetaMCPException(
                    error_code="tool_list_error",
                    message="Failed to list tools",
                    details=str(e),
                )

        @self.router.post("/tools/{tool_name}/execute")
        async def execute_tool(tool_name: str, input_data: dict[str, Any]):
            """Execute a tool."""
            logger.info(f"MCP tool execution endpoint called for {tool_name}")
            try:
                result = await self._handle_call_tool(tool_name, input_data)
                return {"result": result}
            except Exception as e:
                logger.error(f"Failed to execute tool {tool_name}: {e}")
                raise MetaMCPException(
                    error_code="tool_execution_error",
                    message=f"Failed to execute tool {tool_name}",
                    details=str(e),
                )

        logger.info(f"MCP routes setup complete. Router: {self.router}")
        logger.info(
            f"MCP router routes: {[route.path for route in self.router.routes]}"
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
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle tool execution request."""
        if not self.tool_registry:
            raise MetaMCPException(
                error_code="tool_registry_unavailable",
                message="Tool registry not available",
            )

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute tool
            result = await self.tool_registry.execute_tool(
                tool_name=name, input_data=arguments
            )

            # Record metrics
            if self.telemetry_manager:
                duration = asyncio.get_event_loop().time() - start_time
                self.telemetry_manager.record_tool_execution(
                    tool_name=name, success=True, duration=duration
                )

            # Convert result to MCP format
            content = TextContent(type="text", text=str(result))

            return [content]

        except Exception as e:
            # Record error metrics
            if self.telemetry_manager:
                duration = asyncio.get_event_loop().time() - start_time
                self.telemetry_manager.record_tool_execution(
                    tool_name=name, success=False, duration=duration
                )

            logger.error(f"Tool execution failed: {e}")
            raise MetaMCPException(
                error_code="tool_execution_error",
                message=f"Tool execution failed: {str(e)}",
            )

    async def _handle_call_tool_streaming(
        self, name: str, arguments: dict[str, Any]
    ) -> AsyncGenerator[TextContent, None]:
        """Handle tool execution request with streaming response."""
        if not self.tool_registry:
            raise MetaMCPException(
                error_code="tool_registry_unavailable",
                message="Tool registry not available",
            )

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute tool with streaming
            async for chunk in self.tool_registry.execute_tool_streaming(
                tool_name=name, input_data=arguments
            ):
                # Convert chunk to MCP format
                content = TextContent(type="text", text=str(chunk))
                yield content

            # Record metrics
            if self.telemetry_manager:
                duration = asyncio.get_event_loop().time() - start_time
                self.telemetry_manager.record_tool_execution(
                    tool_name=name, success=True, duration=duration
                )

        except Exception as e:
            # Record error metrics
            if self.telemetry_manager:
                duration = asyncio.get_event_loop().time() - start_time
                self.telemetry_manager.record_tool_execution(
                    tool_name=name, success=False, duration=duration
                )

            logger.error(f"Streaming tool execution failed: {e}")
            raise MetaMCPException(
                error_code="tool_execution_error",
                message=f"Streaming tool execution failed: {str(e)}",
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

    async def _handle_read_resource_streaming(
        self, uri: str
    ) -> AsyncGenerator[TextContent, None]:
        """Handle read resource request with streaming response."""
        # For now, return empty generator
        # This can be extended to read resources with streaming
        return
        yield

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

    async def _handle_show_prompt_streaming(
        self, name: str
    ) -> AsyncGenerator[TextContent, None]:
        """Handle show prompt request with streaming response."""
        # For now, return empty generator
        # This can be extended to show prompts with streaming
        return
        yield

    async def send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send notification to connected clients."""
        if self.fastmcp:
            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params
            }
            # Send to WebSocket clients
            await self.fastmcp.send_notification(notification)

    async def broadcast_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast event to all connected clients."""
        await self.send_notification("events/broadcast", {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def send_progress_update(
        self, 
        operation_id: str, 
        progress: float, 
        message: str = ""
    ) -> None:
        """Send progress update to clients."""
        await self.send_notification("progress/update", {
            "operationId": operation_id,
            "progress": progress,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def send_log_message(
        self, 
        level: str, 
        message: str, 
        context: dict[str, Any] = None
    ) -> None:
        """Send log message to clients."""
        await self.send_notification("log/message", {
            "level": level,
            "message": message,
            "context": context or {},
            "timestamp": asyncio.get_event_loop().time()
        })

    async def search_tools(
        self, query: str, max_results: int = 10, similarity_threshold: float = 0.7
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
                similarity_threshold=similarity_threshold,
            )

            # Calculate actual duration
            duration = time.time() - start_time

            # Record vector search metrics
            if self.telemetry_manager:
                self.telemetry_manager.record_vector_search(
                    query_length=len(query),
                    result_count=len(results),
                    duration=duration,
                )

            logger.info(
                f"Vector search completed in {duration:.3f}s, found {len(results)} results"
            )
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

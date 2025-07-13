"""
MCP Proxy Wrapper

This module provides the main wrapper functionality for arbitrary MCP servers,
adding MetaMCP's enhanced features like semantic search, security, and monitoring.
"""

from dataclasses import dataclass
from typing import Any

from fastmcp import FastMCP
from mcp.types import Resource, TextContent, Tool

from ..config import get_settings
from ..exceptions import ProxyError, ToolExecutionError
from ..monitoring.telemetry import TelemetryManager
from ..security.auth import AuthManager
from ..security.policies import PolicyEngine, PolicyEngineType
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class WrappedServerConfig:
    """Configuration for a wrapped MCP server."""
    name: str
    endpoint: str
    transport: str = "http"  # http, websocket, stdio
    auth_required: bool = False
    auth_token: str | None = None
    timeout: int = 30
    retry_attempts: int = 3
    security_level: str = "medium"
    categories: list[str] = None
    description: str = ""
    metadata: dict[str, Any] = None


class MCPProxyWrapper:
    """
    Proxy wrapper for arbitrary MCP servers.
    
    This class wraps existing MCP servers and adds MetaMCP's enhanced
    features like semantic search, security, and monitoring.
    """

    def __init__(self):
        """Initialize the MCP proxy wrapper."""
        self.wrapped_servers: dict[str, WrappedServerConfig] = {}
        self.fastmcp: FastMCP | None = None
        self.auth_manager: AuthManager | None = None
        self.policy_engine: PolicyEngine | None = None
        self.telemetry_manager: TelemetryManager | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the proxy wrapper."""
        if self._initialized:
            return

        try:
            logger.info("Initializing MCP Proxy Wrapper...")

            # Initialize components
            self.auth_manager = AuthManager(settings)
            await self.auth_manager.initialize()

            if settings.policy_enforcement_enabled:
                self.policy_engine = PolicyEngine(PolicyEngineType.INTERNAL)
                await self.policy_engine.initialize()

            if settings.telemetry_enabled:
                self.telemetry_manager = TelemetryManager()
                await self.telemetry_manager.initialize()

            # Initialize FastMCP
            self.fastmcp = FastMCP(
                name="metamcp-proxy",
                version="1.0.0"
            )

            # Register handlers
            self.fastmcp.list_tools = self._handle_list_tools
            self.fastmcp.call_tool = self._handle_call_tool
            self.fastmcp.list_resources = self._handle_list_resources
            self.fastmcp.read_resource = self._handle_read_resource

            self._initialized = True
            logger.info("MCP Proxy Wrapper initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP Proxy Wrapper: {e}")
            raise ProxyError(f"Initialization failed: {str(e)}")

    async def register_server(self, config: WrappedServerConfig) -> str:
        """
        Register a new MCP server to be wrapped.
        
        Args:
            config: Server configuration
            
        Returns:
            Server ID
        """
        try:
            server_id = f"{config.name}_{len(self.wrapped_servers)}"

            # Validate server connectivity
            await self._validate_server_connectivity(config)

            # Store server configuration
            self.wrapped_servers[server_id] = config

            # Register tools from the server
            await self._register_server_tools(server_id, config)

            logger.info(f"Registered MCP server: {server_id}")
            return server_id

        except Exception as e:
            logger.error(f"Failed to register server {config.name}: {e}")
            raise ProxyError(f"Server registration failed: {str(e)}")

    async def _validate_server_connectivity(self, config: WrappedServerConfig) -> None:
        """Validate that the server is reachable and responsive."""
        try:
            # Test connection based on transport type
            if config.transport == "http":
                await self._test_http_connection(config)
            elif config.transport == "websocket":
                await self._test_websocket_connection(config)
            else:
                raise ProxyError(f"Unsupported transport: {config.transport}")

        except Exception as e:
            raise ProxyError(f"Server connectivity test failed: {str(e)}")

    async def _test_http_connection(self, config: WrappedServerConfig) -> None:
        """Test HTTP connection to MCP server."""
        import httpx

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            try:
                response = await client.get(f"{config.endpoint}/health")
                if response.status_code != 200:
                    raise ProxyError(f"Server health check failed: {response.status_code}")
            except Exception as e:
                raise ProxyError(f"HTTP connection failed: {str(e)}")

    async def _test_websocket_connection(self, config: WrappedServerConfig) -> None:
        """Test WebSocket connection to MCP server."""
        import websockets

        try:
            async with websockets.connect(config.endpoint, timeout=config.timeout):
                pass
        except Exception as e:
            raise ProxyError(f"WebSocket connection failed: {str(e)}")

    async def _register_server_tools(self, server_id: str, config: WrappedServerConfig) -> None:
        """Register tools from the wrapped server."""
        try:
            # Get tools from the wrapped server
            tools = await self._get_server_tools(config)

            # Register each tool with metadata
            for tool in tools:
                wrapped_tool = self._wrap_tool(tool, server_id, config)
                # Register with FastMCP
                self.fastmcp.tool(
                    wrapped_tool["name"],
                    wrapped_tool["input_schema"],
                    wrapped_tool["handler"]
                )

        except Exception as e:
            logger.error(f"Failed to register tools from server {server_id}: {e}")
            raise ProxyError(f"Tool registration failed: {str(e)}")

    async def _get_server_tools(self, config: WrappedServerConfig) -> list[dict[str, Any]]:
        """Get tools from the wrapped server."""
        try:
            if config.transport == "http":
                return await self._get_http_server_tools(config)
            elif config.transport == "websocket":
                return await self._get_websocket_server_tools(config)
            else:
                raise ProxyError(f"Unsupported transport for tool discovery: {config.transport}")

        except Exception as e:
            logger.error(f"Failed to get tools from server {config.name}: {e}")
            raise ProxyError(f"Tool discovery failed: {str(e)}")

    async def _get_http_server_tools(self, config: WrappedServerConfig) -> list[dict[str, Any]]:
        """Get tools from HTTP MCP server."""
        import httpx

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {}
            if config.auth_required and config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"

            response = await client.post(
                f"{config.endpoint}/tools/list",
                headers=headers
            )

            if response.status_code != 200:
                raise ProxyError(f"Failed to get tools: {response.status_code}")

            return response.json().get("tools", [])

    async def _get_websocket_server_tools(self, config: WrappedServerConfig) -> list[dict[str, Any]]:
        """Get tools from WebSocket MCP server."""
        import json

        import websockets

        async with websockets.connect(config.endpoint, timeout=config.timeout) as websocket:
            # Send tools/list request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            result = json.loads(response)

            if "error" in result:
                raise ProxyError(f"WebSocket tools/list failed: {result['error']}")

            return result.get("result", {}).get("tools", [])

    def _wrap_tool(self, tool: dict[str, Any], server_id: str, config: WrappedServerConfig) -> dict[str, Any]:
        """Wrap a tool with proxy functionality."""
        original_name = tool.get("name", "unknown")
        wrapped_name = f"{server_id}.{original_name}"

        return {
            "name": wrapped_name,
            "input_schema": tool.get("inputSchema", {}),
            "handler": self._create_wrapped_handler(original_name, server_id, config),
            "description": tool.get("description", config.description),
            "categories": config.categories or [],
            "security_level": config.security_level,
            "server_id": server_id,
            "original_tool": tool
        }

    def _create_wrapped_handler(self, tool_name: str, server_id: str, config: WrappedServerConfig):
        """Create a wrapped handler for tool execution."""
        async def wrapped_handler(args: dict[str, Any]) -> list[TextContent]:
            try:
                # Pre-execution hooks
                await self._before_tool_call(tool_name, server_id, args)

                # Execute tool on wrapped server
                result = await self._execute_wrapped_tool(tool_name, server_id, config, args)

                # Post-execution hooks
                result = await self._after_tool_call(tool_name, server_id, result)

                return [TextContent(type="text", text=str(result))]

            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                raise ToolExecutionError(f"Tool execution failed: {str(e)}")

        return wrapped_handler

    async def _before_tool_call(self, tool_name: str, server_id: str, args: dict[str, Any]) -> None:
        """Pre-execution hooks."""
        # Security validation
        if self.policy_engine:
            await self.policy_engine.validate_tool_access(tool_name, server_id, args)

        # Telemetry
        if self.telemetry_manager:
            self.telemetry_manager.record_tool_call_start(tool_name, server_id)

    async def _after_tool_call(self, tool_name: str, server_id: str, result: Any) -> Any:
        """Post-execution hooks."""
        # Telemetry
        if self.telemetry_manager:
            self.telemetry_manager.record_tool_call_end(tool_name, server_id)

        return result

    async def _execute_wrapped_tool(self, tool_name: str, server_id: str, config: WrappedServerConfig, args: dict[str, Any]) -> Any:
        """Execute tool on the wrapped server."""
        try:
            if config.transport == "http":
                return await self._execute_http_tool(tool_name, config, args)
            elif config.transport == "websocket":
                return await self._execute_websocket_tool(tool_name, config, args)
            else:
                raise ProxyError(f"Unsupported transport for tool execution: {config.transport}")

        except Exception as e:
            logger.error(f"Wrapped tool execution failed: {e}")
            raise ToolExecutionError(f"Wrapped tool execution failed: {str(e)}")

    async def _execute_http_tool(self, tool_name: str, config: WrappedServerConfig, args: dict[str, Any]) -> Any:
        """Execute tool via HTTP."""
        import httpx

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            headers = {"Content-Type": "application/json"}
            if config.auth_required and config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"

            response = await client.post(
                f"{config.endpoint}/tools/call",
                headers=headers,
                json={
                    "name": tool_name,
                    "arguments": args
                }
            )

            if response.status_code != 200:
                raise ToolExecutionError(f"HTTP tool execution failed: {response.status_code}")

            return response.json().get("result")

    async def _execute_websocket_tool(self, tool_name: str, config: WrappedServerConfig, args: dict[str, Any]) -> Any:
        """Execute tool via WebSocket."""
        import json

        import websockets

        async with websockets.connect(config.endpoint, timeout=config.timeout) as websocket:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }

            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            result = json.loads(response)

            if "error" in result:
                raise ToolExecutionError(f"WebSocket tool execution failed: {result['error']}")

            return result.get("result")

    async def _handle_list_tools(self) -> list[Tool]:
        """Handle list tools request."""
        tools = []
        for server_id, config in self.wrapped_servers.items():
            try:
                server_tools = await self._get_server_tools(config)
                for tool in server_tools:
                    wrapped_tool = self._wrap_tool(tool, server_id, config)
                    tools.append(Tool(
                        name=wrapped_tool["name"],
                        description=wrapped_tool["description"],
                        inputSchema=wrapped_tool["input_schema"]
                    ))
            except Exception as e:
                logger.error(f"Failed to get tools from server {server_id}: {e}")

        return tools

    async def _handle_call_tool(self, name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool call request."""
        try:
            # Parse server_id and tool_name from wrapped name
            if "." in name:
                server_id, tool_name = name.split(".", 1)
            else:
                raise ToolExecutionError(f"Invalid tool name format: {name}")

            if server_id not in self.wrapped_servers:
                raise ToolExecutionError(f"Unknown server: {server_id}")

            config = self.wrapped_servers[server_id]
            result = await self._execute_wrapped_tool(tool_name, server_id, config, arguments)

            return [TextContent(type="text", text=str(result))]

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            raise ToolExecutionError(f"Tool call failed: {str(e)}")

    async def _handle_list_resources(self) -> list[Resource]:
        """Handle list resources request."""
        # For now, return empty list - can be extended to aggregate resources
        return []

    async def _handle_read_resource(self, uri: str) -> list[TextContent]:
        """Handle read resource request."""
        # For now, return empty list - can be extended to proxy resource requests
        return []

    async def shutdown(self) -> None:
        """Shutdown the proxy wrapper."""
        logger.info("Shutting down MCP Proxy Wrapper...")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the proxy wrapper is initialized."""
        return self._initialized

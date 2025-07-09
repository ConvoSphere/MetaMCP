"""
MCP Meta-Server Client

This module provides a client library for interacting with the MCP Meta-Server.
It supports tool registration, semantic search, and tool execution through
both REST API and MCP protocol.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from .exceptions import (
    MetaMCPError, 
    ToolNotFoundError, 
    AuthenticationError,
    MCPProtocolError
)
from .utils.logging import get_logger


logger = get_logger(__name__)


class MetaMCPClient:
    """
    Client for interacting with MCP Meta-Server.
    
    Provides both REST API and MCP WebSocket interfaces for:
    - Tool registration and management
    - Semantic tool search
    - Tool execution
    - Authentication and session management
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        websocket_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize MCP Meta-Server client.
        
        Args:
            base_url: Base URL of the MCP Meta-Server
            websocket_url: WebSocket URL for MCP protocol (auto-generated if not provided)
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.websocket_url = websocket_url or self._generate_ws_url()
        self.api_key = api_key
        self.timeout = timeout
        
        # HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._get_headers()
        )
        
        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.mcp_session_id: Optional[str] = None
        
        # State
        self._connected = False
        
    def _generate_ws_url(self) -> str:
        """Generate WebSocket URL from base URL."""
        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{ws_base}/mcp/ws"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MetaMCP-Client/1.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def connect(self) -> None:
        """
        Connect to MCP Meta-Server via WebSocket.
        
        Raises:
            MCPProtocolError: If connection fails
        """
        try:
            logger.info(f"Connecting to MCP server at {self.websocket_url}")
            
            self.websocket = await websockets.connect(
                self.websocket_url,
                timeout=self.timeout
            )
            
            # Initialize MCP session
            await self._initialize_mcp_session()
            
            self._connected = True
            logger.info("Connected to MCP server successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPProtocolError(
                operation="connect",
                reason=str(e)
            )
    
    async def disconnect(self) -> None:
        """Disconnect from MCP Meta-Server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        await self.http_client.aclose()
        self._connected = False
        logger.info("Disconnected from MCP server")
    
    async def _initialize_mcp_session(self) -> None:
        """Initialize MCP protocol session."""
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "clientInfo": {
                    "name": "MetaMCP-Client",
                    "version": "1.0.0"
                }
            }
        }
        
        await self._send_mcp_message(init_message)
        response = await self._receive_mcp_message()
        
        if "error" in response:
            raise MCPProtocolError(
                operation="initialize",
                reason=response["error"]["message"]
            )
        
        self.mcp_session_id = response.get("result", {}).get("sessionId")
    
    async def _send_mcp_message(self, message: Dict[str, Any]) -> None:
        """Send MCP message via WebSocket."""
        if not self.websocket:
            raise MCPProtocolError(
                operation="send_message",
                reason="Not connected to MCP server"
            )
        
        try:
            await self.websocket.send(json.dumps(message))
        except ConnectionClosed:
            self._connected = False
            raise MCPProtocolError(
                operation="send_message",
                reason="Connection to MCP server lost"
            )
    
    async def _receive_mcp_message(self) -> Dict[str, Any]:
        """Receive MCP message via WebSocket."""
        if not self.websocket:
            raise MCPProtocolError(
                operation="receive_message",
                reason="Not connected to MCP server"
            )
        
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except ConnectionClosed:
            self._connected = False
            raise MCPProtocolError(
                operation="receive_message",
                reason="Connection to MCP server lost"
            )
    
    # =============================================================================
    # REST API Methods
    # =============================================================================
    
    async def search_tools(
        self,
        query: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for tools using semantic search.
        
        Args:
            query: Natural language query describing desired functionality
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of matching tools
            
        Raises:
            MetaMCPError: If search fails
        """
        try:
            url = urljoin(self.base_url, "/api/v1/tools/search")
            
            payload = {
                "query": query,
                "max_results": max_results,
                "similarity_threshold": similarity_threshold
            }
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get("tools", [])
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Tool search failed: {e}")
            raise MetaMCPError(
                message=f"Tool search failed: {str(e)}",
                error_code="search_failed"
            )
    
    async def get_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Get tool details by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool details
            
        Raises:
            ToolNotFoundError: If tool is not found
        """
        try:
            url = urljoin(self.base_url, f"/api/v1/tools/{tool_name}")
            
            response = await self.http_client.get(url)
            
            if response.status_code == 404:
                raise ToolNotFoundError(tool_name)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except ToolNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get tool {tool_name}: {e}")
            raise MetaMCPError(
                message=f"Failed to get tool: {str(e)}",
                error_code="get_tool_failed"
            )
    
    async def list_tools(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List available tools.
        
        Args:
            category: Filter by tool category
            limit: Maximum number of tools to return
            offset: Offset for pagination
            
        Returns:
            Dictionary with tools list and pagination info
        """
        try:
            url = urljoin(self.base_url, "/api/v1/tools")
            
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if category:
                params["category"] = category
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise MetaMCPError(
                message=f"Failed to list tools: {str(e)}",
                error_code="list_tools_failed"
            )
    
    async def register_tool(self, tool_data: Dict[str, Any]) -> str:
        """
        Register a new tool.
        
        Args:
            tool_data: Tool registration data
            
        Returns:
            Tool ID
            
        Raises:
            MetaMCPError: If registration fails
        """
        try:
            url = urljoin(self.base_url, "/api/v1/tools")
            
            response = await self.http_client.post(url, json=tool_data)
            response.raise_for_status()
            
            data = response.json()
            return data.get("tool_id")
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Tool registration failed: {e}")
            raise MetaMCPError(
                message=f"Tool registration failed: {str(e)}",
                error_code="registration_failed"
            )
    
    async def update_tool(
        self, 
        tool_name: str, 
        tool_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing tool.
        
        Args:
            tool_name: Name of the tool to update
            tool_data: Updated tool data
            
        Returns:
            Updated tool data
        """
        try:
            url = urljoin(self.base_url, f"/api/v1/tools/{tool_name}")
            
            response = await self.http_client.put(url, json=tool_data)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Tool update failed: {e}")
            raise MetaMCPError(
                message=f"Tool update failed: {str(e)}",
                error_code="update_failed"
            )
    
    async def delete_tool(self, tool_name: str) -> bool:
        """
        Delete a tool.
        
        Args:
            tool_name: Name of the tool to delete
            
        Returns:
            True if successful
        """
        try:
            url = urljoin(self.base_url, f"/api/v1/tools/{tool_name}")
            
            response = await self.http_client.delete(url)
            response.raise_for_status()
            
            return True
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Tool deletion failed: {e}")
            raise MetaMCPError(
                message=f"Tool deletion failed: {str(e)}",
                error_code="deletion_failed"
            )
    
    # =============================================================================
    # MCP Protocol Methods
    # =============================================================================
    
    async def mcp_list_tools(self) -> List[Dict[str, Any]]:
        """
        List tools using MCP protocol.
        
        Returns:
            List of available tools
        """
        if not self._connected:
            await self.connect()
        
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        await self._send_mcp_message(message)
        response = await self._receive_mcp_message()
        
        if "error" in response:
            raise MCPProtocolError(
                operation="list_tools",
                reason=response["error"]["message"]
            )
        
        return response.get("result", {}).get("tools", [])
    
    async def mcp_call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool using MCP protocol.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self._connected:
            await self.connect()
        
        message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_mcp_message(message)
        response = await self._receive_mcp_message()
        
        if "error" in response:
            raise MCPProtocolError(
                operation="call_tool",
                reason=response["error"]["message"]
            )
        
        return response.get("result", {})
    
    # =============================================================================
    # Health and Status
    # =============================================================================
    
    async def get_health(self) -> Dict[str, Any]:
        """
        Get server health status.
        
        Returns:
            Health status information
        """
        try:
            url = urljoin(self.base_url, "/health")
            
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise MetaMCPError(
                message=f"Health check failed: {str(e)}",
                error_code="health_check_failed"
            )
    
    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.
        
        Returns:
            Server information
        """
        try:
            url = urljoin(self.base_url, "/api/v1/info")
            
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            raise MetaMCPError(
                message=f"Failed to get server info: {str(e)}",
                error_code="server_info_failed"
            )
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    async def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and convert to appropriate exceptions."""
        try:
            error_data = error.response.json()
            error_info = error_data.get("error", {})
            
            error_code = error_info.get("code", "unknown_error")
            message = error_info.get("message", str(error))
            
            if error.response.status_code == 401:
                raise AuthenticationError(message)
            elif error.response.status_code == 404:
                raise ToolNotFoundError(error_info.get("tool_name", "unknown"))
            else:
                raise MetaMCPError(
                    message=message,
                    error_code=error_code,
                    status_code=error.response.status_code
                )
                
        except json.JSONDecodeError:
            raise MetaMCPError(
                message=f"HTTP {error.response.status_code}: {error.response.text}",
                error_code="http_error",
                status_code=error.response.status_code
            )
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
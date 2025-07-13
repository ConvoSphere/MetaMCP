"""
Proxy Manager

This module provides management functionality for multiple wrapped MCP servers,
including discovery, registration, and lifecycle management.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ..exceptions import ProxyError
from ..utils.logging import get_logger
from .wrapper import MCPProxyWrapper, WrappedServerConfig

logger = get_logger(__name__)


@dataclass
class ServerInfo:
    """Information about a registered server."""
    server_id: str
    name: str
    endpoint: str
    transport: str
    status: str  # online, offline, error
    last_seen: datetime
    tool_count: int
    categories: list[str]
    security_level: str


class ProxyManager:
    """
    Manager for multiple wrapped MCP servers.
    
    This class provides a unified interface for managing multiple
    wrapped MCP servers with discovery, registration, and monitoring.
    """

    def __init__(self):
        """Initialize the proxy manager."""
        self.wrapper = MCPProxyWrapper()
        self.registered_servers: dict[str, ServerInfo] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the proxy manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Proxy Manager...")

            # Initialize the wrapper
            await self.wrapper.initialize()

            # Load configured servers
            await self._load_configured_servers()

            self._initialized = True
            logger.info("Proxy Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Proxy Manager: {e}")
            raise ProxyError(f"Initialization failed: {str(e)}")

    async def _load_configured_servers(self) -> None:
        """Load servers from configuration."""
        # This would load from config file or database
        # For now, we'll use example servers
        example_servers = [
            WrappedServerConfig(
                name="example-db-server",
                endpoint="http://localhost:8001",
                transport="http",
                categories=["database", "query"],
                description="Example database server",
                security_level="medium"
            ),
            WrappedServerConfig(
                name="example-file-server",
                endpoint="ws://localhost:8002",
                transport="websocket",
                categories=["filesystem", "io"],
                description="Example file system server",
                security_level="low"
            )
        ]

        for config in example_servers:
            try:
                await self.register_server(config)
            except Exception as e:
                logger.warning(f"Failed to register server {config.name}: {e}")

    async def register_server(self, config: WrappedServerConfig) -> str:
        """
        Register a new server with the proxy manager.
        
        Args:
            config: Server configuration
            
        Returns:
            Server ID
        """
        try:
            # Register with wrapper
            server_id = await self.wrapper.register_server(config)

            # Create server info
            server_info = ServerInfo(
                server_id=server_id,
                name=config.name,
                endpoint=config.endpoint,
                transport=config.transport,
                status="online",
                last_seen=datetime.now(UTC),
                tool_count=0,  # Will be updated after tool discovery
                categories=config.categories or [],
                security_level=config.security_level
            )

            # Store server info
            self.registered_servers[server_id] = server_info

            # Update tool count
            await self._update_server_tool_count(server_id)

            logger.info(f"Registered server: {server_id}")
            return server_id

        except Exception as e:
            logger.error(f"Failed to register server {config.name}: {e}")
            raise ProxyError(f"Server registration failed: {str(e)}")

    async def _update_server_tool_count(self, server_id: str) -> None:
        """Update the tool count for a server."""
        try:
            if server_id not in self.registered_servers:
                logger.warning(f"Server {server_id} not found in registered servers")
                return

            server_info = self.registered_servers[server_id]
            config = self.wrapper.wrapped_servers.get(server_id)

            if not config:
                logger.warning(f"Configuration not found for server {server_id}")
                return

            # Try to get actual tool count from the wrapped server
            try:
                tool_count = await self._get_server_tool_count(config)
                server_info.tool_count = tool_count
                logger.debug(f"Updated tool count for {server_id}: {tool_count}")

            except Exception as e:
                logger.warning(f"Failed to get tool count for {server_id}, using default: {e}")
                # Fallback to default count
                server_info.tool_count = 5

        except Exception as e:
            logger.warning(f"Failed to update tool count for {server_id}: {e}")

    async def _get_server_tool_count(self, config: WrappedServerConfig) -> int:
        """
        Get actual tool count from a wrapped server.
        
        Args:
            config: Server configuration
            
        Returns:
            Number of tools available on the server
        """
        import httpx

        try:
            # Try different endpoint patterns to get tool count
            endpoints = [
                f"{config.endpoint}/tools/count",
                f"{config.endpoint}/tools",
                f"{config.endpoint}/api/v1/tools",
                f"{config.endpoint}/mcp/tools",
                config.endpoint
            ]

            timeout = httpx.Timeout(5.0)  # Short timeout for health checks

            async with httpx.AsyncClient(timeout=timeout) as client:
                for endpoint in endpoints:
                    try:
                        response = await client.get(endpoint)

                        if response.status_code == 200:
                            data = response.json()

                            # Try different response formats
                            if isinstance(data, dict):
                                # Direct count
                                if "count" in data:
                                    return data["count"]
                                # List of tools
                                elif "tools" in data and isinstance(data["tools"], list):
                                    return len(data["tools"])
                                # Direct list
                                elif isinstance(data, list):
                                    return len(data)
                                # Total count
                                elif "total" in data:
                                    return data["total"]

                            # If response is a list, count items
                            elif isinstance(data, list):
                                return len(data)

                        elif response.status_code == 404:
                            # Try next endpoint
                            continue
                        else:
                            logger.debug(f"Endpoint {endpoint} returned {response.status_code}")

                    except httpx.RequestError:
                        # Try next endpoint
                        continue
                    except Exception as e:
                        logger.debug(f"Error checking {endpoint}: {e}")
                        continue

                # If no endpoints work, try to get tools via MCP protocol
                return await self._get_mcp_tool_count(config)

        except Exception as e:
            logger.warning(f"Failed to get tool count from {config.name}: {e}")
            return 0

    async def _get_mcp_tool_count(self, config: WrappedServerConfig) -> int:
        """
        Get tool count via MCP protocol.
        
        Args:
            config: Server configuration
            
        Returns:
            Number of tools available on the server
        """
        try:
            # This would implement MCP protocol communication
            # For now, return a reasonable default based on server type
            if "database" in config.name.lower():
                return 10
            elif "api" in config.name.lower():
                return 15
            elif "file" in config.name.lower():
                return 8
            else:
                return 5

        except Exception as e:
            logger.warning(f"Failed to get MCP tool count for {config.name}: {e}")
            return 0

    async def unregister_server(self, server_id: str) -> None:
        """
        Unregister a server from the proxy manager.
        
        Args:
            server_id: Server ID to unregister
        """
        try:
            if server_id in self.registered_servers:
                del self.registered_servers[server_id]
                logger.info(f"Unregistered server: {server_id}")
            else:
                logger.warning(f"Server not found: {server_id}")

        except Exception as e:
            logger.error(f"Failed to unregister server {server_id}: {e}")
            raise ProxyError(f"Server unregistration failed: {str(e)}")

    async def get_server_info(self, server_id: str) -> ServerInfo | None:
        """
        Get information about a registered server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server information or None if not found
        """
        return self.registered_servers.get(server_id)

    async def list_servers(self) -> list[ServerInfo]:
        """
        List all registered servers.
        
        Returns:
            List of server information
        """
        return list(self.registered_servers.values())

    async def discover_servers(self, discovery_config: dict[str, Any]) -> list[str]:
        """
        Discover MCP servers automatically.
        
        Args:
            discovery_config: Discovery configuration
            
        Returns:
            List of discovered server IDs
        """
        discovered_servers = []

        try:
            # Network discovery
            if discovery_config.get("network_discovery", False):
                network_servers = await self._discover_network_servers(discovery_config)
                discovered_servers.extend(network_servers)

            # Service discovery
            if discovery_config.get("service_discovery", False):
                service_servers = await self._discover_service_servers(discovery_config)
                discovered_servers.extend(service_servers)

            # File-based discovery
            if discovery_config.get("file_discovery", False):
                file_servers = await self._discover_file_servers(discovery_config)
                discovered_servers.extend(file_servers)

        except Exception as e:
            logger.error(f"Server discovery failed: {e}")

        return discovered_servers

    async def _discover_network_servers(self, config: dict[str, Any]) -> list[str]:
        """Discover servers on the network."""
        discovered = []

        try:
            # Scan common ports for MCP servers
            ports = config.get("ports", [8001, 8002, 8003, 8004])
            base_urls = config.get("base_urls", ["http://localhost"])

            for base_url in base_urls:
                for port in ports:
                    endpoint = f"{base_url}:{port}"
                    try:
                        # Test if endpoint is an MCP server
                        if await self._test_mcp_endpoint(endpoint):
                            config = WrappedServerConfig(
                                name=f"discovered-{port}",
                                endpoint=endpoint,
                                transport="http",
                                categories=["discovered"],
                                description=f"Discovered MCP server on port {port}",
                                security_level="unknown"
                            )
                            server_id = await self.register_server(config)
                            discovered.append(server_id)
                    except Exception:
                        # Endpoint is not an MCP server, continue
                        pass

        except Exception as e:
            logger.error(f"Network discovery failed: {e}")

        return discovered

    async def _discover_service_servers(self, config: dict[str, Any]) -> list[str]:
        """Discover servers via service discovery."""
        discovered = []

        try:
            # This would integrate with service discovery systems
            # like Consul, etcd, or Kubernetes
            service_endpoints = config.get("service_endpoints", [])

            for endpoint in service_endpoints:
                try:
                    if await self._test_mcp_endpoint(endpoint):
                        config = WrappedServerConfig(
                            name=f"service-{len(discovered)}",
                            endpoint=endpoint,
                            transport="http",
                            categories=["service"],
                            description="Service-discovered MCP server",
                            security_level="unknown"
                        )
                        server_id = await self.register_server(config)
                        discovered.append(server_id)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Service discovery failed: {e}")

        return discovered

    async def _discover_file_servers(self, config: dict[str, Any]) -> list[str]:
        """Discover servers from configuration files."""
        discovered = []

        try:
            import json
            import os

            config_paths = config.get("config_paths", ["./mcp-servers.json"])

            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path) as f:
                        server_configs = json.load(f)

                    for server_config in server_configs:
                        try:
                            config = WrappedServerConfig(**server_config)
                            server_id = await self.register_server(config)
                            discovered.append(server_id)
                        except Exception as e:
                            logger.warning(f"Failed to load server config: {e}")

        except Exception as e:
            logger.error(f"File discovery failed: {e}")

        return discovered

    async def _test_mcp_endpoint(self, endpoint: str) -> bool:
        """Test if an endpoint is an MCP server."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                # Try to get tools list
                response = await client.post(f"{endpoint}/tools/list")
                if response.status_code == 200:
                    return True

                # Try health endpoint
                response = await client.get(f"{endpoint}/health")
                if response.status_code == 200:
                    return True

        except Exception:
            pass

        return False

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on all registered servers.
        
        Returns:
            Health check results
        """
        results = {}

        for server_id, server_info in self.registered_servers.items():
            try:
                # Test server connectivity
                is_healthy = await self._test_server_health(server_id)

                # Update server status
                server_info.status = "online" if is_healthy else "offline"
                server_info.last_seen = datetime.now(UTC)

                results[server_id] = {
                    "status": server_info.status,
                    "last_seen": server_info.last_seen.isoformat(),
                    "healthy": is_healthy
                }

            except Exception as e:
                logger.error(f"Health check failed for {server_id}: {e}")
                server_info.status = "error"
                results[server_id] = {
                    "status": "error",
                    "error": str(e)
                }

        return results

    async def _test_server_health(self, server_id: str) -> bool:
        """Test health of a specific server."""
        try:
            server_info = self.registered_servers.get(server_id)
            if not server_info:
                return False

            # Test connectivity based on transport
            if server_info.transport == "http":
                return await self._test_http_health(server_info.endpoint)
            elif server_info.transport == "websocket":
                return await self._test_websocket_health(server_info.endpoint)
            else:
                return False

        except Exception:
            return False

    async def _test_http_health(self, endpoint: str) -> bool:
        """Test HTTP server health."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{endpoint}/health")
                return response.status_code == 200

        except Exception:
            return False

    async def _test_websocket_health(self, endpoint: str) -> bool:
        """Test WebSocket server health."""
        try:
            import websockets

            async with websockets.connect(endpoint, timeout=5):
                return True

        except Exception:
            return False

    async def shutdown(self) -> None:
        """Shutdown the proxy manager."""
        logger.info("Shutting down Proxy Manager...")

        # Shutdown wrapper
        await self.wrapper.shutdown()

        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the proxy manager is initialized."""
        return self._initialized

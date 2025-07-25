"""
Server Discovery

This module provides automatic discovery of MCP servers
using various discovery mechanisms like network scanning,
service discovery, and configuration files.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ..exceptions import ServerDiscoveryError
from ..utils.logging import get_logger
from .wrapper import WrappedServerConfig

logger = get_logger(__name__)


@dataclass
class DiscoveryConfig:
    """Configuration for server discovery."""

    network_discovery: bool = True
    service_discovery: bool = False
    file_discovery: bool = True
    ports: list[int] = None
    base_urls: list[str] = None
    config_paths: list[str] = None
    service_endpoints: list[str] = None
    timeout: int = 5
    max_concurrent: int = 10

    def __post_init__(self):
        if self.ports is None:
            self.ports = [8001, 8002, 8003, 8004, 8005]
        if self.base_urls is None:
            self.base_urls = ["http://localhost", "http://127.0.0.1"]
        if self.config_paths is None:
            self.config_paths = ["./mcp-servers.json", "./config/mcp-servers.json"]
        if self.service_endpoints is None:
            self.service_endpoints = []


@dataclass
class DiscoveredServer:
    """Information about a discovered server."""

    endpoint: str
    transport: str
    name: str
    description: str = ""
    categories: list[str] = None
    security_level: str = "unknown"
    discovered_at: datetime = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = ["discovered"]
        if self.discovered_at is None:
            self.discovered_at = datetime.now(UTC)
        if self.metadata is None:
            self.metadata = {}


class ServerDiscovery:
    """
    Automatic discovery of MCP servers.

    This class provides various mechanisms for discovering
    MCP servers including network scanning, service discovery,
    and configuration file parsing.
    """

    def __init__(self):
        """Initialize the server discovery."""
        self.discovered_servers: list[DiscoveredServer] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the server discovery."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Server Discovery...")
            self._initialized = True
            logger.info("Server Discovery initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Server Discovery: {e}")
            raise ServerDiscoveryError(f"Initialization failed: {str(e)}")

    async def discover_servers(self, config: DiscoveryConfig) -> list[DiscoveredServer]:
        """
        Discover MCP servers using the provided configuration.

        Args:
            config: Discovery configuration

        Returns:
            List of discovered servers
        """
        discovered = []

        try:
            # Network discovery
            if config.network_discovery:
                network_servers = await self._discover_network_servers(config)
                discovered.extend(network_servers)

            # Service discovery
            if config.service_discovery:
                service_servers = await self._discover_service_servers(config)
                discovered.extend(service_servers)

            # File-based discovery
            if config.file_discovery:
                file_servers = await self._discover_file_servers(config)
                discovered.extend(file_servers)

            # Update discovered servers list
            self.discovered_servers.extend(discovered)

            logger.info(f"Discovered {len(discovered)} MCP servers")

        except Exception as e:
            logger.error(f"Server discovery failed: {e}")
            raise ServerDiscoveryError(f"Discovery failed: {str(e)}")

        return discovered

    async def _discover_network_servers(
        self, config: DiscoveryConfig
    ) -> list[DiscoveredServer]:
        """Discover servers on the network."""
        discovered = []

        try:
            # Create tasks for concurrent scanning
            tasks = []
            for base_url in config.base_urls:
                for port in config.ports:
                    endpoint = f"{base_url}:{port}"
                    task = self._test_endpoint(endpoint, config.timeout)
                    tasks.append((endpoint, task))

            # Execute tasks with concurrency limit
            semaphore = asyncio.Semaphore(config.max_concurrent)

            async def limited_test(
                endpoint: str, task: asyncio.Task
            ) -> DiscoveredServer | None:
                async with semaphore:
                    try:
                        is_mcp = await task
                        if is_mcp:
                            return await self._create_discovered_server(
                                endpoint, "http"
                            )
                    except Exception as e:
                        logger.debug(f"Failed to test {endpoint}: {e}")
                    return None

            # Run all tests concurrently
            results = await asyncio.gather(
                *[limited_test(endpoint, task) for endpoint, task in tasks],
                return_exceptions=True,
            )

            # Collect successful discoveries
            for result in results:
                if isinstance(result, DiscoveredServer):
                    discovered.append(result)

        except Exception as e:
            logger.error(f"Network discovery failed: {e}")

        return discovered

    async def _discover_service_servers(
        self, config: DiscoveryConfig
    ) -> list[DiscoveredServer]:
        """Discover servers via service discovery."""
        discovered = []

        try:
            for endpoint in config.service_endpoints:
                try:
                    is_mcp = await self._test_endpoint(endpoint, config.timeout)
                    if is_mcp:
                        server = await self._create_discovered_server(endpoint, "http")
                        discovered.append(server)
                except Exception as e:
                    logger.debug(f"Failed to test service endpoint {endpoint}: {e}")

        except Exception as e:
            logger.error(f"Service discovery failed: {e}")

        return discovered

    async def _discover_file_servers(
        self, config: DiscoveryConfig
    ) -> list[DiscoveredServer]:
        """Discover servers from configuration files."""
        discovered = []

        try:
            for config_path in config.config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path) as f:
                            server_configs = json.load(f)

                        for server_config in server_configs:
                            try:
                                # Validate required fields
                                if "endpoint" not in server_config:
                                    logger.warning(
                                        f"Missing endpoint in server config: {server_config}"
                                    )
                                    continue

                                # Create discovered server from config
                                server = DiscoveredServer(
                                    endpoint=server_config["endpoint"],
                                    transport=server_config.get("transport", "http"),
                                    name=server_config.get(
                                        "name", f"file-{len(discovered)}"
                                    ),
                                    description=server_config.get("description", ""),
                                    categories=server_config.get(
                                        "categories", ["file"]
                                    ),
                                    security_level=server_config.get(
                                        "security_level", "unknown"
                                    ),
                                    metadata=server_config.get("metadata", {}),
                                )
                                discovered.append(server)

                            except Exception as e:
                                logger.warning(f"Failed to parse server config: {e}")

                    except Exception as e:
                        logger.warning(f"Failed to read config file {config_path}: {e}")

        except Exception as e:
            logger.error(f"File discovery failed: {e}")

        return discovered

    async def _test_endpoint(self, endpoint: str, timeout: int) -> bool:
        """Test if an endpoint is an MCP server."""
        try:
            # Try HTTP endpoints
            if endpoint.startswith(("http://", "https://")):
                return await self._test_http_endpoint(endpoint, timeout)
            elif endpoint.startswith(("ws://", "wss://")):
                return await self._test_websocket_endpoint(endpoint, timeout)
            else:
                # Assume HTTP if no protocol specified
                return await self._test_http_endpoint(f"http://{endpoint}", timeout)

        except Exception:
            return False

    async def _test_http_endpoint(self, endpoint: str, timeout: int) -> bool:
        """Test if an HTTP endpoint is an MCP server."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try tools/list endpoint
                try:
                    response = await client.post(f"{endpoint}/tools/list")
                    if response.status_code == 200:
                        return True
                except Exception:
                    pass

                # Try health endpoint
                try:
                    response = await client.get(f"{endpoint}/health")
                    if response.status_code == 200:
                        return True
                except Exception:
                    pass

                # Try root endpoint
                try:
                    response = await client.get(endpoint)
                    if response.status_code == 200:
                        # Check if response contains MCP indicators
                        content = response.text.lower()
                        if "mcp" in content or "tools" in content:
                            return True
                except Exception:
                    pass

        except Exception:
            pass

        return False

    async def _test_websocket_endpoint(self, endpoint: str, timeout: int) -> bool:
        """Test if a WebSocket endpoint is an MCP server."""
        try:
            import websockets

            async with websockets.connect(endpoint, timeout=timeout) as websocket:
                # Send a simple ping or tools/list request
                try:
                    request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {},
                    }
                    await websocket.send(json.dumps(request))
                    response = await websocket.recv()
                    result = json.loads(response)

                    if "result" in result and "error" not in result:
                        return True

                except Exception:
                    pass

        except Exception:
            pass

        return False

    async def _create_discovered_server(
        self, endpoint: str, transport: str
    ) -> DiscoveredServer:
        """Create a discovered server from endpoint information."""
        # Extract name from endpoint
        name = self._extract_name_from_endpoint(endpoint)

        # Determine categories based on endpoint
        categories = self._determine_categories(endpoint)

        return DiscoveredServer(
            endpoint=endpoint,
            transport=transport,
            name=name,
            description=f"Discovered MCP server at {endpoint}",
            categories=categories,
            security_level="unknown",
        )

    def _extract_name_from_endpoint(self, endpoint: str) -> str:
        """Extract a name from the endpoint URL."""
        try:
            # Remove protocol
            if "://" in endpoint:
                endpoint = endpoint.split("://", 1)[1]

            # Remove port
            if ":" in endpoint:
                endpoint = endpoint.split(":", 1)[0]

            # Remove path
            if "/" in endpoint:
                endpoint = endpoint.split("/", 1)[0]

            # Replace dots with dashes
            name = endpoint.replace(".", "-")

            return f"discovered-{name}"

        except Exception:
            return f"discovered-{hash(endpoint) % 10000}"

    def _determine_categories(self, endpoint: str) -> list[str]:
        """Determine categories based on endpoint."""
        categories = ["discovered"]

        endpoint_lower = endpoint.lower()

        # Add categories based on endpoint characteristics
        if "localhost" in endpoint_lower or "127.0.0.1" in endpoint_lower:
            categories.append("local")

        if "api" in endpoint_lower:
            categories.append("api")

        if "db" in endpoint_lower or "database" in endpoint_lower:
            categories.append("database")

        if "file" in endpoint_lower or "fs" in endpoint_lower:
            categories.append("filesystem")

        if "web" in endpoint_lower or "http" in endpoint_lower:
            categories.append("web")

        return categories

    async def get_discovered_servers(self) -> list[DiscoveredServer]:
        """
        Get all discovered servers.

        Returns:
            List of discovered servers
        """
        return self.discovered_servers.copy()

    async def clear_discovered_servers(self) -> None:
        """Clear the list of discovered servers."""
        self.discovered_servers.clear()

    async def convert_to_wrapped_config(
        self, discovered: DiscoveredServer
    ) -> WrappedServerConfig:
        """
        Convert a discovered server to a wrapped server configuration.

        Args:
            discovered: Discovered server information

        Returns:
            Wrapped server configuration
        """
        return WrappedServerConfig(
            name=discovered.name,
            endpoint=discovered.endpoint,
            transport=discovered.transport,
            categories=discovered.categories,
            description=discovered.description,
            security_level=discovered.security_level,
            metadata=discovered.metadata,
        )

    async def shutdown(self) -> None:
        """Shutdown the server discovery."""
        logger.info("Shutting down Server Discovery...")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the server discovery is initialized."""
        return self._initialized

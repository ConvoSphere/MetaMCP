"""
MCP Multi-Server Load Balancer

This module provides load balancing capabilities for multiple MCP servers,
including health checking, failover, and intelligent load distribution.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ServerStatus(Enum):
    """Server status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    CONSISTENT_HASH = "consistent_hash"


@dataclass
class ServerConfig:
    """Configuration for a server in the load balancer."""

    id: str
    name: str
    endpoint: str
    transport_type: str
    weight: int = 100
    max_connections: int = 1000
    health_check_interval: float = 30.0
    health_check_timeout: float = 5.0
    health_check_path: str = "/health"
    failover_threshold: int = 3
    recovery_threshold: int = 2
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerHealth:
    """Health information for a server."""

    server_id: str
    status: ServerStatus
    last_check: float
    response_time: float
    error_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    active_connections: int = 0


class HealthChecker:
    """Manages health checking for servers."""

    def __init__(self, config: ServerConfig):
        """Initialize health checker."""
        self.config = config
        self.health = ServerHealth(
            server_id=config.id,
            status=ServerStatus.OFFLINE,
            last_check=0.0,
            response_time=0.0,
        )
        self._check_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start health checking."""
        if self._running:
            return

        self._running = True
        self._check_task = asyncio.create_task(self._health_check_loop())
        logger.info(f"Started health checker for server {self.config.name}")

    async def stop(self) -> None:
        """Stop health checking."""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped health checker for server {self.config.name}")

    async def _health_check_loop(self) -> None:
        """Health check loop."""
        while self._running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {self.config.name}: {e}")
                await asyncio.sleep(self.config.health_check_interval)

    async def _perform_health_check(self) -> None:
        """Perform a health check."""
        start_time = time.time()

        try:
            # Perform health check based on transport type
            if self.config.transport_type == "http":
                success = await self._http_health_check()
            elif self.config.transport_type == "websocket":
                success = await self._websocket_health_check()
            elif self.config.transport_type == "stdio":
                success = await self._stdio_health_check()
            else:
                success = False

            response_time = time.time() - start_time
            self.health.response_time = response_time
            self.health.last_check = start_time

            if success:
                await self._handle_success()
            else:
                await self._handle_failure()

        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            await self._handle_failure()

    async def _http_health_check(self) -> bool:
        """Perform HTTP health check."""
        try:
            import httpx

            async with httpx.AsyncClient(
                timeout=self.config.health_check_timeout
            ) as client:
                url = f"{self.config.endpoint}{self.config.health_check_path}"
                response = await client.get(url)

                return response.status_code == 200

        except Exception as e:
            logger.debug(f"HTTP health check failed for {self.config.name}: {e}")
            return False

    async def _websocket_health_check(self) -> bool:
        """Perform WebSocket health check."""
        try:
            import websockets

            async with websockets.connect(
                self.config.endpoint, timeout=self.config.health_check_timeout
            ) as websocket:
                # Send ping
                pong_waiter = await websocket.ping()
                await pong_waiter
                return True

        except Exception as e:
            logger.debug(f"WebSocket health check failed for {self.config.name}: {e}")
            return False

    async def _stdio_health_check(self) -> bool:
        """Perform stdio health check."""
        try:
            import subprocess

            # Check if process is running
            process = subprocess.run(
                ["pgrep", "-f", self.config.endpoint],
                capture_output=True,
                timeout=self.config.health_check_timeout,
            )

            return process.returncode == 0

        except Exception as e:
            logger.debug(f"Stdio health check failed for {self.config.name}: {e}")
            return False

    async def _handle_success(self) -> None:
        """Handle successful health check."""
        self.health.success_count += 1
        self.health.consecutive_successes += 1
        self.health.consecutive_failures = 0

        # Update status based on consecutive successes
        if self.health.consecutive_successes >= self.config.recovery_threshold:
            if self.health.status != ServerStatus.HEALTHY:
                self.health.status = ServerStatus.HEALTHY
                logger.info(f"Server {self.config.name} is now healthy")

        logger.debug(f"Health check successful for {self.config.name}")

    async def _handle_failure(self) -> None:
        """Handle failed health check."""
        self.health.error_count += 1
        self.health.consecutive_failures += 1
        self.health.consecutive_successes = 0

        # Update status based on consecutive failures
        if self.health.consecutive_failures >= self.config.failover_threshold:
            if self.health.status != ServerStatus.UNHEALTHY:
                self.health.status = ServerStatus.UNHEALTHY
                logger.warning(f"Server {self.config.name} is now unhealthy")

        logger.debug(f"Health check failed for {self.config.name}")

    async def get_health_status(self) -> ServerHealth:
        """Get current health status."""
        return self.health

    async def update_connection_count(self, count: int) -> None:
        """Update active connection count."""
        self.health.active_connections = count


class LoadBalancer:
    """Multi-server load balancer for MCP."""

    def __init__(
        self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    ):
        """Initialize load balancer."""
        self.strategy = strategy
        self.servers: dict[str, ServerConfig] = {}
        self.health_checkers: dict[str, HealthChecker] = {}
        self.current_index = 0
        self._lock = asyncio.Lock()
        self._running = False

    async def add_server(self, config: ServerConfig) -> None:
        """Add a server to the load balancer."""
        async with self._lock:
            self.servers[config.id] = config

            # Create health checker
            health_checker = HealthChecker(config)
            self.health_checkers[config.id] = health_checker

            if self._running:
                await health_checker.start()

            logger.info(f"Added server {config.name} to load balancer")

    async def remove_server(self, server_id: str) -> None:
        """Remove a server from the load balancer."""
        async with self._lock:
            if server_id in self.servers:
                del self.servers[server_id]

                if server_id in self.health_checkers:
                    await self.health_checkers[server_id].stop()
                    del self.health_checkers[server_id]

                logger.info(f"Removed server {server_id} from load balancer")

    async def get_server(self, client_id: str = None) -> ServerConfig | None:
        """Get a server based on the load balancing strategy."""
        async with self._lock:
            healthy_servers = await self._get_healthy_servers()

            if not healthy_servers:
                logger.warning("No healthy servers available")
                return None

            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return await self._round_robin_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return await self._least_connections_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return await self._weighted_round_robin_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return await self._least_response_time_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.IP_HASH:
                return await self._ip_hash_select(healthy_servers, client_id)
            elif self.strategy == LoadBalancingStrategy.CONSISTENT_HASH:
                return await self._consistent_hash_select(healthy_servers, client_id)
            else:
                return healthy_servers[0]

    async def _get_healthy_servers(self) -> list[ServerConfig]:
        """Get list of healthy servers."""
        healthy_servers = []

        for server_id, config in self.servers.items():
            if not config.enabled:
                continue

            health_checker = self.health_checkers.get(server_id)
            if health_checker:
                health = await health_checker.get_health_status()
                if health.status == ServerStatus.HEALTHY:
                    healthy_servers.append(config)

        return healthy_servers

    async def _round_robin_select(self, servers: list[ServerConfig]) -> ServerConfig:
        """Round robin server selection."""
        if not servers:
            return None

        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server

    async def _least_connections_select(
        self, servers: list[ServerConfig]
    ) -> ServerConfig:
        """Least connections server selection."""
        if not servers:
            return None

        min_connections = float("inf")
        selected_server = None

        for server in servers:
            health_checker = self.health_checkers.get(server.id)
            if health_checker:
                health = await health_checker.get_health_status()
                if health.active_connections < min_connections:
                    min_connections = health.active_connections
                    selected_server = server

        return selected_server

    async def _weighted_round_robin_select(
        self, servers: list[ServerConfig]
    ) -> ServerConfig:
        """Weighted round robin server selection."""
        if not servers:
            return None

        # Calculate total weight
        total_weight = sum(server.weight for server in servers)

        # Use current index to select server
        current_weight = self.current_index % total_weight
        self.current_index += 1

        # Find server based on weight
        for server in servers:
            current_weight -= server.weight
            if current_weight < 0:
                return server

        return servers[0]

    async def _least_response_time_select(
        self, servers: list[ServerConfig]
    ) -> ServerConfig:
        """Least response time server selection."""
        if not servers:
            return None

        min_response_time = float("inf")
        selected_server = None

        for server in servers:
            health_checker = self.health_checkers.get(server.id)
            if health_checker:
                health = await health_checker.get_health_status()
                if health.response_time < min_response_time:
                    min_response_time = health.response_time
                    selected_server = server

        return selected_server

    async def _ip_hash_select(
        self, servers: list[ServerConfig], client_id: str
    ) -> ServerConfig:
        """IP hash server selection."""
        if not servers or not client_id:
            return servers[0] if servers else None

        # Simple hash of client ID
        hash_value = hash(client_id)
        index = hash_value % len(servers)
        return servers[index]

    async def _consistent_hash_select(
        self, servers: list[ServerConfig], client_id: str
    ) -> ServerConfig:
        """Consistent hash server selection."""
        if not servers or not client_id:
            return servers[0] if servers else None

        # Simple consistent hashing implementation
        hash_value = hash(client_id)

        # Create virtual nodes for better distribution
        virtual_nodes = []
        for server in servers:
            for i in range(3):  # 3 virtual nodes per server
                virtual_hash = hash(f"{server.id}-{i}")
                virtual_nodes.append((virtual_hash, server))

        # Sort virtual nodes
        virtual_nodes.sort(key=lambda x: x[0])

        # Find the first virtual node with hash >= client hash
        for virtual_hash, server in virtual_nodes:
            if virtual_hash >= hash_value:
                return server

        # Wrap around to first server
        return virtual_nodes[0][1]

    async def get_server_health(self, server_id: str) -> ServerHealth | None:
        """Get health status for a specific server."""
        health_checker = self.health_checkers.get(server_id)
        if health_checker:
            return await health_checker.get_health_status()
        return None

    async def get_all_health_status(self) -> dict[str, ServerHealth]:
        """Get health status for all servers."""
        health_status = {}
        for server_id, health_checker in self.health_checkers.items():
            health_status[server_id] = await health_checker.get_health_status()
        return health_status

    async def update_server_connection_count(self, server_id: str, count: int) -> None:
        """Update connection count for a server."""
        health_checker = self.health_checkers.get(server_id)
        if health_checker:
            await health_checker.update_connection_count(count)

    async def start(self) -> None:
        """Start the load balancer."""
        if self._running:
            return

        self._running = True

        # Start all health checkers
        for health_checker in self.health_checkers.values():
            await health_checker.start()

        logger.info("Load balancer started")

    async def stop(self) -> None:
        """Stop the load balancer."""
        if not self._running:
            return

        self._running = False

        # Stop all health checkers
        for health_checker in self.health_checkers.values():
            await health_checker.stop()

        logger.info("Load balancer stopped")

    async def get_statistics(self) -> dict[str, Any]:
        """Get load balancer statistics."""
        total_servers = len(self.servers)
        healthy_servers = len(await self._get_healthy_servers())

        total_connections = 0
        total_requests = 0

        for health_checker in self.health_checkers.values():
            health = await health_checker.get_health_status()
            total_connections += health.active_connections
            total_requests += health.total_requests

        return {
            "strategy": self.strategy.value,
            "total_servers": total_servers,
            "healthy_servers": healthy_servers,
            "unhealthy_servers": total_servers - healthy_servers,
            "total_connections": total_connections,
            "total_requests": total_requests,
            "health_check_interval": 30.0,  # Default interval
        }


class LoadBalancedMCPClient:
    """MCP client with load balancing capabilities."""

    def __init__(self, load_balancer: LoadBalancer):
        """Initialize load balanced client."""
        self.load_balancer = load_balancer
        self.active_connections: dict[str, Any] = {}
        self.client_id = str(uuid.uuid4())

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Send request through load balancer."""
        # Get server from load balancer
        server = await self.load_balancer.get_server(self.client_id)
        if not server:
            raise RuntimeError("No healthy servers available")

        try:
            # Create connection if needed
            connection = await self._get_connection(server)

            # Send request
            response = await self._send_request_to_server(connection, request)

            # Update statistics
            await self._update_server_stats(server.id, success=True)

            return response

        except Exception:
            # Update statistics
            await self._update_server_stats(server.id, success=False)
            raise

    async def _get_connection(self, server: ServerConfig) -> Any:
        """Get or create connection to server."""
        if server.id in self.active_connections:
            return self.active_connections[server.id]

        # Create new connection based on transport type
        if server.transport_type == "websocket":
            connection = await self._create_websocket_connection(server)
        elif server.transport_type == "http":
            connection = await self._create_http_connection(server)
        elif server.transport_type == "stdio":
            connection = await self._create_stdio_connection(server)
        else:
            raise ValueError(f"Unsupported transport type: {server.transport_type}")

        self.active_connections[server.id] = connection
        return connection

    async def _create_websocket_connection(self, server: ServerConfig) -> Any:
        """Create WebSocket connection."""
        import websockets

        return await websockets.connect(server.endpoint)

    async def _create_http_connection(self, server: ServerConfig) -> Any:
        """Create HTTP connection."""
        import httpx

        return httpx.AsyncClient(base_url=server.endpoint)

    async def _create_stdio_connection(self, server: ServerConfig) -> Any:
        """Create stdio connection."""
        import subprocess

        return subprocess.Popen(
            server.endpoint.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    async def _send_request_to_server(
        self, connection: Any, request: dict[str, Any]
    ) -> dict[str, Any]:
        """Send request to server."""
        # This would be implemented based on the connection type
        # For now, we'll return a mock response
        return {"status": "success", "data": "mock_response"}

    async def _update_server_stats(self, server_id: str, success: bool) -> None:
        """Update server statistics."""
        # Update connection count
        connection_count = len(self.active_connections)
        await self.load_balancer.update_server_connection_count(
            server_id, connection_count
        )

    async def close(self) -> None:
        """Close all connections."""
        for connection in self.active_connections.values():
            try:
                if hasattr(connection, "close"):
                    await connection.close()
                elif hasattr(connection, "terminate"):
                    connection.terminate()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

        self.active_connections.clear()

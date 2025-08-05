"""
Tests for MCP Load Balancer

Tests the load balancing functionality including health checking, server selection
strategies, failover mechanisms, and load distribution.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metamcp.mcp.load_balancer import (
    HealthChecker,
    LoadBalancer,
    LoadBalancedMCPClient,
    LoadBalancingStrategy,
    ServerConfig,
    ServerHealth,
    ServerStatus,
)


class TestServerConfig:
    """Test ServerConfig functionality."""
    
    def test_server_config_creation(self):
        """Test creating a ServerConfig."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http",
            weight=100,
            max_connections=1000,
            health_check_interval=30.0,
            health_check_timeout=5.0,
            health_check_path="/health",
            failover_threshold=3,
            recovery_threshold=2,
            enabled=True
        )
        
        assert config.id == "server-1"
        assert config.name == "Test Server"
        assert config.endpoint == "http://localhost:8000"
        assert config.transport_type == "http"
        assert config.weight == 100
        assert config.max_connections == 1000
        assert config.enabled is True
    
    def test_server_config_defaults(self):
        """Test ServerConfig default values."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        assert config.weight == 100
        assert config.max_connections == 1000
        assert config.health_check_interval == 30.0
        assert config.health_check_timeout == 5.0
        assert config.failover_threshold == 3
        assert config.recovery_threshold == 2
        assert config.enabled is True
        assert config.metadata == {}


class TestServerHealth:
    """Test ServerHealth functionality."""
    
    def test_server_health_creation(self):
        """Test creating a ServerHealth."""
        health = ServerHealth(
            server_id="server-1",
            status=ServerStatus.HEALTHY,
            last_check=time.time(),
            response_time=0.1,
            error_count=5,
            success_count=95,
            consecutive_failures=0,
            consecutive_successes=10,
            total_requests=100,
            active_connections=5
        )
        
        assert health.server_id == "server-1"
        assert health.status == ServerStatus.HEALTHY
        assert health.response_time == 0.1
        assert health.error_count == 5
        assert health.success_count == 95
        assert health.consecutive_failures == 0
        assert health.consecutive_successes == 10
        assert health.total_requests == 100
        assert health.active_connections == 5


class TestHealthChecker:
    """Test HealthChecker functionality."""
    
    @pytest.mark.asyncio
    async def test_health_checker_creation(self):
        """Test creating a HealthChecker."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        checker = HealthChecker(config)
        
        assert checker.config == config
        assert checker.health.server_id == "server-1"
        assert checker.health.status == ServerStatus.OFFLINE
        assert checker._running is False
    
    @pytest.mark.asyncio
    async def test_health_checker_start_stop(self):
        """Test starting and stopping health checker."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        checker = HealthChecker(config)
        
        # Start health checker
        await checker.start()
        assert checker._running is True
        assert checker._check_task is not None
        
        # Stop health checker
        await checker.stop()
        assert checker._running is False
    
    @pytest.mark.asyncio
    async def test_http_health_check_success(self):
        """Test successful HTTP health check."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        checker = HealthChecker(config)
        
        # Mock httpx
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            success = await checker._http_health_check()
            assert success is True
    
    @pytest.mark.asyncio
    async def test_http_health_check_failure(self):
        """Test failed HTTP health check."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        checker = HealthChecker(config)
        
        # Mock httpx with exception
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection failed")
            
            success = await checker._http_health_check()
            assert success is False
    
    @pytest.mark.asyncio
    async def test_websocket_health_check_success(self):
        """Test successful WebSocket health check."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="ws://localhost:8080",
            transport_type="websocket"
        )
        
        checker = HealthChecker(config)
        
        # Mock websockets
        mock_websocket = AsyncMock()
        mock_pong = AsyncMock()
        mock_websocket.ping.return_value = mock_pong
        
        with patch('websockets.connect') as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            
            success = await checker._websocket_health_check()
            assert success is True
    
    @pytest.mark.asyncio
    async def test_stdio_health_check_success(self):
        """Test successful stdio health check."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="python -m metamcp.mcp.server",
            transport_type="stdio"
        )
        
        checker = HealthChecker(config)
        
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        
        with patch('subprocess.run', return_value=mock_process):
            success = await checker._stdio_health_check()
            assert success is True
    
    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test handling successful health check."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http",
            recovery_threshold=2
        )
        
        checker = HealthChecker(config)
        
        # Simulate consecutive failures
        checker.health.consecutive_failures = 3
        checker.health.status = ServerStatus.UNHEALTHY
        
        # Handle success
        await checker._handle_success()
        
        assert checker.health.consecutive_failures == 0
        assert checker.health.consecutive_successes == 1
        assert checker.health.success_count == 1
        
        # Handle more successes to reach recovery threshold
        await checker._handle_success()
        
        assert checker.health.consecutive_successes == 2
        assert checker.health.status == ServerStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_handle_failure(self):
        """Test handling failed health check."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http",
            failover_threshold=3
        )
        
        checker = HealthChecker(config)
        
        # Simulate consecutive successes
        checker.health.consecutive_successes = 5
        checker.health.status = ServerStatus.HEALTHY
        
        # Handle failure
        await checker._handle_failure()
        
        assert checker.health.consecutive_successes == 0
        assert checker.health.consecutive_failures == 1
        assert checker.health.error_count == 1
        
        # Handle more failures to reach failover threshold
        await checker._handle_failure()
        await checker._handle_failure()
        
        assert checker.health.consecutive_failures == 3
        assert checker.health.status == ServerStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_get_health_status(self):
        """Test getting health status."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        checker = HealthChecker(config)
        
        health = await checker.get_health_status()
        
        assert health.server_id == "server-1"
        assert health.status == ServerStatus.OFFLINE
        assert health.last_check == 0.0
        assert health.response_time == 0.0
    
    @pytest.mark.asyncio
    async def test_update_connection_count(self):
        """Test updating connection count."""
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        checker = HealthChecker(config)
        
        await checker.update_connection_count(10)
        
        assert checker.health.active_connections == 10


class TestLoadBalancer:
    """Test LoadBalancer functionality."""
    
    @pytest.mark.asyncio
    async def test_load_balancer_creation(self):
        """Test creating a LoadBalancer."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        assert balancer.strategy == LoadBalancingStrategy.ROUND_ROBIN
        assert len(balancer.servers) == 0
        assert len(balancer.health_checkers) == 0
        assert balancer.current_index == 0
        assert balancer._running is False
    
    @pytest.mark.asyncio
    async def test_add_server(self):
        """Test adding a server to the load balancer."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        assert "server-1" in balancer.servers
        assert "server-1" in balancer.health_checkers
        assert balancer.servers["server-1"] == config
    
    @pytest.mark.asyncio
    async def test_remove_server(self):
        """Test removing a server from the load balancer."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        assert "server-1" in balancer.servers
        
        await balancer.remove_server("server-1")
        assert "server-1" not in balancer.servers
        assert "server-1" not in balancer.health_checkers
    
    @pytest.mark.asyncio
    async def test_get_healthy_servers(self):
        """Test getting healthy servers."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Healthy Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Unhealthy Server",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        health_checker1 = balancer.health_checkers["server-1"]
        health_checker1.health.status = ServerStatus.HEALTHY
        
        health_checker2 = balancer.health_checkers["server-2"]
        health_checker2.health.status = ServerStatus.UNHEALTHY
        
        healthy_servers = await balancer._get_healthy_servers()
        
        assert len(healthy_servers) == 1
        assert healthy_servers[0].id == "server-1"
    
    @pytest.mark.asyncio
    async def test_round_robin_selection(self):
        """Test round robin server selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        for checker in balancer.health_checkers.values():
            checker.health.status = ServerStatus.HEALTHY
        
        # Test round robin selection
        server1 = await balancer._round_robin_select([config1, config2])
        assert server1.id == "server-1"
        
        server2 = await balancer._round_robin_select([config1, config2])
        assert server2.id == "server-2"
        
        server3 = await balancer._round_robin_select([config1, config2])
        assert server3.id == "server-1"  # Wraps around
    
    @pytest.mark.asyncio
    async def test_least_connections_selection(self):
        """Test least connections server selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status and connection counts
        health_checker1 = balancer.health_checkers["server-1"]
        health_checker1.health.status = ServerStatus.HEALTHY
        health_checker1.health.active_connections = 10
        
        health_checker2 = balancer.health_checkers["server-2"]
        health_checker2.health.status = ServerStatus.HEALTHY
        health_checker2.health.active_connections = 5
        
        # Test least connections selection
        server = await balancer._least_connections_select([config1, config2])
        assert server.id == "server-2"  # Has fewer connections
    
    @pytest.mark.asyncio
    async def test_weighted_round_robin_selection(self):
        """Test weighted round robin server selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN)
        
        # Add servers with different weights
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http",
            weight=100
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http",
            weight=200
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        for checker in balancer.health_checkers.values():
            checker.health.status = ServerStatus.HEALTHY
        
        # Test weighted selection
        servers = []
        for _ in range(6):  # Test multiple selections
            server = await balancer._weighted_round_robin_selection([config1, config2])
            servers.append(server.id)
        
        # Should have more server-2 selections due to higher weight
        server2_count = servers.count("server-2")
        server1_count = servers.count("server-1")
        assert server2_count > server1_count
    
    @pytest.mark.asyncio
    async def test_least_response_time_selection(self):
        """Test least response time server selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.LEAST_RESPONSE_TIME)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status and response times
        health_checker1 = balancer.health_checkers["server-1"]
        health_checker1.health.status = ServerStatus.HEALTHY
        health_checker1.health.response_time = 0.2
        
        health_checker2 = balancer.health_checkers["server-2"]
        health_checker2.health.status = ServerStatus.HEALTHY
        health_checker2.health.response_time = 0.1
        
        # Test least response time selection
        server = await balancer._least_response_time_select([config1, config2])
        assert server.id == "server-2"  # Has lower response time
    
    @pytest.mark.asyncio
    async def test_ip_hash_selection(self):
        """Test IP hash server selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.IP_HASH)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        for checker in balancer.health_checkers.values():
            checker.health.status = ServerStatus.HEALTHY
        
        # Test IP hash selection
        client_id1 = "client-1"
        client_id2 = "client-2"
        
        server1 = await balancer._ip_hash_select([config1, config2], client_id1)
        server2 = await balancer._ip_hash_select([config1, config2], client_id2)
        
        # Same client should always get same server
        server1_again = await balancer._ip_hash_select([config1, config2], client_id1)
        assert server1.id == server1_again.id
    
    @pytest.mark.asyncio
    async def test_consistent_hash_selection(self):
        """Test consistent hash server selection."""
        balancer = LoadBalancer(LoadBalancingStrategy.CONSISTENT_HASH)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        for checker in balancer.health_checkers.values():
            checker.health.status = ServerStatus.HEALTHY
        
        # Test consistent hash selection
        client_id = "client-1"
        
        server1 = await balancer._consistent_hash_select([config1, config2], client_id)
        server2 = await balancer._consistent_hash_select([config1, config2], client_id)
        
        # Same client should always get same server
        assert server1.id == server2.id
    
    @pytest.mark.asyncio
    async def test_get_server_no_healthy_servers(self):
        """Test getting server when no healthy servers available."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Unhealthy Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        # Mock unhealthy status
        health_checker = balancer.health_checkers["server-1"]
        health_checker.health.status = ServerStatus.UNHEALTHY
        
        server = await balancer.get_server()
        assert server is None
    
    @pytest.mark.asyncio
    async def test_get_server_disabled_server(self):
        """Test getting server when server is disabled."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Disabled Server",
            endpoint="http://localhost:8000",
            transport_type="http",
            enabled=False
        )
        
        await balancer.add_server(config)
        
        # Mock healthy status
        health_checker = balancer.health_checkers["server-1"]
        health_checker.health.status = ServerStatus.HEALTHY
        
        server = await balancer.get_server()
        assert server is None
    
    @pytest.mark.asyncio
    async def test_get_server_health(self):
        """Test getting server health."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        health = await balancer.get_server_health("server-1")
        assert health is not None
        assert health.server_id == "server-1"
    
    @pytest.mark.asyncio
    async def test_get_all_health_status(self):
        """Test getting all health status."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        health_status = await balancer.get_all_health_status()
        
        assert len(health_status) == 2
        assert "server-1" in health_status
        assert "server-2" in health_status
    
    @pytest.mark.asyncio
    async def test_update_server_connection_count(self):
        """Test updating server connection count."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        await balancer.update_server_connection_count("server-1", 15)
        
        health_checker = balancer.health_checkers["server-1"]
        assert health_checker.health.active_connections == 15
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping the load balancer."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        # Start load balancer
        await balancer.start()
        assert balancer._running is True
        
        # Verify health checkers are started
        health_checker = balancer.health_checkers["server-1"]
        assert health_checker._running is True
        
        # Stop load balancer
        await balancer.stop()
        assert balancer._running is False
    
    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting load balancer statistics."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        config1 = ServerConfig(
            id="server-1",
            name="Healthy Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Unhealthy Server",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        health_checker1 = balancer.health_checkers["server-1"]
        health_checker1.health.status = ServerStatus.HEALTHY
        health_checker1.health.active_connections = 10
        health_checker1.health.total_requests = 100
        
        health_checker2 = balancer.health_checkers["server-2"]
        health_checker2.health.status = ServerStatus.UNHEALTHY
        health_checker2.health.active_connections = 5
        health_checker2.health.total_requests = 50
        
        stats = await balancer.get_statistics()
        
        assert stats["strategy"] == "round_robin"
        assert stats["total_servers"] == 2
        assert stats["healthy_servers"] == 1
        assert stats["unhealthy_servers"] == 1
        assert stats["total_connections"] == 15
        assert stats["total_requests"] == 150


class TestLoadBalancedMCPClient:
    """Test LoadBalancedMCPClient functionality."""
    
    @pytest.mark.asyncio
    async def test_client_creation(self):
        """Test creating a load balanced client."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        assert client.load_balancer == balancer
        assert len(client.active_connections) == 0
        assert client.client_id is not None
    
    @pytest.mark.asyncio
    async def test_send_request_no_servers(self):
        """Test sending request with no available servers."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        with pytest.raises(RuntimeError, match="No healthy servers available"):
            await client.send_request({"test": "data"})
    
    @pytest.mark.asyncio
    async def test_send_request_with_server(self):
        """Test sending request with available server."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        # Add a server
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        # Mock health status
        health_checker = balancer.health_checkers["server-1"]
        health_checker.health.status = ServerStatus.HEALTHY
        
        # Mock connection creation and request sending
        with patch.object(client, '_get_connection') as mock_get_conn, \
             patch.object(client, '_send_request_to_server') as mock_send, \
             patch.object(client, '_update_server_stats') as mock_update:
            
            mock_connection = MagicMock()
            mock_get_conn.return_value = mock_connection
            mock_send.return_value = {"response": "success"}
            
            response = await client.send_request({"test": "data"})
            
            assert response == {"response": "success"}
            mock_get_conn.assert_called_once()
            mock_send.assert_called_once()
            mock_update.assert_called_with("server-1", True)
    
    @pytest.mark.asyncio
    async def test_send_request_failure(self):
        """Test sending request with failure."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        # Add a server
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        # Mock health status
        health_checker = balancer.health_checkers["server-1"]
        health_checker.health.status = ServerStatus.HEALTHY
        
        # Mock connection creation with failure
        with patch.object(client, '_get_connection') as mock_get_conn, \
             patch.object(client, '_update_server_stats') as mock_update:
            
            mock_get_conn.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                await client.send_request({"test": "data"})
            
            mock_update.assert_called_with("server-1", False)
    
    @pytest.mark.asyncio
    async def test_get_connection_websocket(self):
        """Test getting WebSocket connection."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="ws://localhost:8080",
            transport_type="websocket"
        )
        
        # Mock websockets
        mock_websocket = AsyncMock()
        with patch('websockets.connect', return_value=mock_websocket):
            connection = await client._get_connection(config)
            assert connection == mock_websocket
            assert "server-1" in client.active_connections
    
    @pytest.mark.asyncio
    async def test_get_connection_http(self):
        """Test getting HTTP connection."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        # Mock httpx
        mock_client = AsyncMock()
        with patch('httpx.AsyncClient', return_value=mock_client):
            connection = await client._get_connection(config)
            assert connection == mock_client
            assert "server-1" in client.active_connections
    
    @pytest.mark.asyncio
    async def test_get_connection_stdio(self):
        """Test getting stdio connection."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="python -m metamcp.mcp.server",
            transport_type="stdio"
        )
        
        # Mock subprocess
        mock_process = MagicMock()
        with patch('subprocess.Popen', return_value=mock_process):
            connection = await client._get_connection(config)
            assert connection == mock_process
            assert "server-1" in client.active_connections
    
    @pytest.mark.asyncio
    async def test_get_connection_unsupported_transport(self):
        """Test getting connection with unsupported transport."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="invalid://localhost:8000",
            transport_type="invalid"
        )
        
        with pytest.raises(ValueError, match="Unsupported transport type"):
            await client._get_connection(config)
    
    @pytest.mark.asyncio
    async def test_update_server_stats(self):
        """Test updating server statistics."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        # Add a server
        config = ServerConfig(
            id="server-1",
            name="Test Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        await balancer.add_server(config)
        
        # Add a connection
        client.active_connections["server-1"] = MagicMock()
        
        await client._update_server_stats("server-1", True)
        
        # Verify connection count was updated
        health_checker = balancer.health_checkers["server-1"]
        assert health_checker.health.active_connections == 1
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(balancer)
        
        # Add mock connections
        mock_connection1 = MagicMock()
        mock_connection1.close = AsyncMock()
        client.active_connections["server-1"] = mock_connection1
        
        mock_connection2 = MagicMock()
        mock_connection2.terminate = MagicMock()
        client.active_connections["server-2"] = mock_connection2
        
        await client.close()
        
        assert len(client.active_connections) == 0
        mock_connection1.close.assert_called_once()
        mock_connection2.terminate.assert_called_once()


class TestLoadBalancerIntegration:
    """Integration tests for load balancer."""
    
    @pytest.mark.asyncio
    async def test_complete_load_balancing_workflow(self):
        """Test complete load balancing workflow."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add multiple servers
        config1 = ServerConfig(
            id="server-1",
            name="Server 1",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Server 2",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Mock health status
        for checker in balancer.health_checkers.values():
            checker.health.status = ServerStatus.HEALTHY
        
        # Start load balancer
        await balancer.start()
        
        # Test server selection
        servers = []
        for _ in range(4):
            server = await balancer.get_server()
            servers.append(server.id)
        
        # Should alternate between servers
        assert servers[0] == "server-1"
        assert servers[1] == "server-2"
        assert servers[2] == "server-1"
        assert servers[3] == "server-2"
        
        # Test statistics
        stats = await balancer.get_statistics()
        assert stats["total_servers"] == 2
        assert stats["healthy_servers"] == 2
        
        # Stop load balancer
        await balancer.stop()
    
    @pytest.mark.asyncio
    async def test_failover_scenario(self):
        """Test failover scenario."""
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add servers
        config1 = ServerConfig(
            id="server-1",
            name="Primary Server",
            endpoint="http://localhost:8000",
            transport_type="http"
        )
        
        config2 = ServerConfig(
            id="server-2",
            name="Backup Server",
            endpoint="http://localhost:8001",
            transport_type="http"
        )
        
        await balancer.add_server(config1)
        await balancer.add_server(config2)
        
        # Start with both servers healthy
        for checker in balancer.health_checkers.values():
            checker.health.status = ServerStatus.HEALTHY
        
        # Get server - should get first one
        server = await balancer.get_server()
        assert server.id == "server-1"
        
        # Simulate primary server failure
        health_checker1 = balancer.health_checkers["server-1"]
        health_checker1.health.status = ServerStatus.UNHEALTHY
        
        # Get server - should get backup server
        server = await balancer.get_server()
        assert server.id == "server-2"
        
        # Simulate primary server recovery
        health_checker1.health.status = ServerStatus.HEALTHY
        
        # Get server - should get primary server again
        server = await balancer.get_server()
        assert server.id == "server-1"
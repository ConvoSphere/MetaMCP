"""
Tests for MCP Transport Plugin System

Tests the transport plugin system including plugin registration, discovery,
custom transport implementations, and plugin management.
"""

import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metamcp.mcp.transport_plugins import (
    CustomTransportPlugin,
    HTTPTransportPlugin,
    LoadBalancedMCPClient,
    StdioTransportPlugin,
    TransportConfig,
    TransportPlugin,
    TransportPluginManager,
    TransportType,
    WebSocketTransportPlugin,
    discover_plugins,
    load_plugin_from_module,
)


class TestTransportConfig:
    """Test TransportConfig functionality."""

    def test_transport_config_creation(self):
        """Test creating a TransportConfig."""
        config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="test-websocket",
            version="1.0.0",
            description="Test WebSocket transport",
            config_schema={"type": "object"},
            default_config={"url": "ws://localhost:8080"},
            enabled=True,
            priority=100,
        )

        assert config.transport_type == TransportType.WEBSOCKET
        assert config.name == "test-websocket"
        assert config.version == "1.0.0"
        assert config.description == "Test WebSocket transport"
        assert config.enabled is True
        assert config.priority == 100

    def test_transport_config_defaults(self):
        """Test TransportConfig default values."""
        config = TransportConfig(
            transport_type=TransportType.HTTP,
            name="test-http",
            version="1.0.0",
            description="Test HTTP transport",
            config_schema={},
            default_config={},
        )

        assert config.enabled is True
        assert config.priority == 100
        assert config.metadata == {}


class TestTransportPlugin:
    """Test base TransportPlugin functionality."""

    def test_transport_plugin_creation(self):
        """Test creating a TransportPlugin."""
        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        plugin = CustomTransportPlugin(config)

        assert plugin.config == config
        assert plugin._initialized is False
        assert plugin._connected is False

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting plugin status."""
        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        plugin = CustomTransportPlugin(config)
        status = await plugin.get_status()

        assert status["name"] == "test-plugin"
        assert status["type"] == "custom"
        assert status["version"] == "1.0.0"
        assert status["initialized"] is False
        assert status["connected"] is False
        assert status["enabled"] is True


class TestWebSocketTransportPlugin:
    """Test WebSocketTransportPlugin functionality."""

    @pytest.mark.asyncio
    async def test_websocket_plugin_initialization(self):
        """Test WebSocket plugin initialization."""
        config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport",
            config_schema={},
            default_config={"url": "ws://localhost:8080"},
        )

        plugin = WebSocketTransportPlugin(config)

        # Mock websockets import
        with patch.dict("sys.modules", {"websockets": MagicMock()}):
            await plugin.initialize()
            assert plugin._initialized is True

    @pytest.mark.asyncio
    async def test_websocket_plugin_initialization_missing_dependency(self):
        """Test WebSocket plugin initialization without websockets library."""
        config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport",
            config_schema={},
            default_config={"url": "ws://localhost:8080"},
        )

        plugin = WebSocketTransportPlugin(config)

        # Test without websockets module
        with patch.dict("sys.modules", {}, clear=True):
            with pytest.raises(RuntimeError, match="websockets library not available"):
                await plugin.initialize()

    @pytest.mark.asyncio
    async def test_websocket_plugin_connection(self):
        """Test WebSocket plugin connection."""
        config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport",
            config_schema={},
            default_config={"url": "ws://localhost:8080"},
        )

        plugin = WebSocketTransportPlugin(config)

        # Mock websockets
        mock_websocket = AsyncMock()
        mock_websocket.closed = False

        with patch("websockets.connect", return_value=mock_websocket):
            await plugin.connect()
            assert plugin._connected is True
            assert plugin.websocket == mock_websocket

    @pytest.mark.asyncio
    async def test_websocket_plugin_send_receive(self):
        """Test WebSocket plugin send and receive."""
        config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport",
            config_schema={},
            default_config={"url": "ws://localhost:8080"},
        )

        plugin = WebSocketTransportPlugin(config)
        plugin._connected = True
        plugin.websocket = AsyncMock()
        plugin.websocket.closed = False

        # Test send
        message = {"test": "data"}
        await plugin.send_message(message)
        plugin.websocket.send.assert_called_once()

        # Test receive
        plugin.websocket.recv.return_value = '{"response": "data"}'
        response = await plugin.receive_message()
        assert response == {"response": "data"}

    @pytest.mark.asyncio
    async def test_websocket_plugin_disconnect(self):
        """Test WebSocket plugin disconnect."""
        config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport",
            config_schema={},
            default_config={"url": "ws://localhost:8080"},
        )

        plugin = WebSocketTransportPlugin(config)
        plugin._connected = True
        plugin.websocket = AsyncMock()

        await plugin.disconnect()

        assert plugin._connected is False
        assert plugin.websocket is None
        plugin.websocket.close.assert_called_once()


class TestHTTPTransportPlugin:
    """Test HTTPTransportPlugin functionality."""

    @pytest.mark.asyncio
    async def test_http_plugin_initialization(self):
        """Test HTTP plugin initialization."""
        config = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http",
            version="1.0.0",
            description="HTTP transport",
            config_schema={},
            default_config={"base_url": "http://localhost:8000"},
        )

        plugin = HTTPTransportPlugin(config)

        # Mock httpx
        mock_client = AsyncMock()
        with patch("httpx.AsyncClient", return_value=mock_client):
            await plugin.initialize()
            assert plugin._initialized is True
            assert plugin.session == mock_client

    @pytest.mark.asyncio
    async def test_http_plugin_connection(self):
        """Test HTTP plugin connection."""
        config = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http",
            version="1.0.0",
            description="HTTP transport",
            config_schema={},
            default_config={"base_url": "http://localhost:8000"},
        )

        plugin = HTTPTransportPlugin(config)
        plugin.session = AsyncMock()

        # Mock successful health check
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        plugin.session.get.return_value = mock_response

        await plugin.connect()
        assert plugin._connected is True

    @pytest.mark.asyncio
    async def test_http_plugin_send_receive(self):
        """Test HTTP plugin send and receive."""
        config = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http",
            version="1.0.0",
            description="HTTP transport",
            config_schema={},
            default_config={"base_url": "http://localhost:8000"},
        )

        plugin = HTTPTransportPlugin(config)
        plugin._connected = True
        plugin.session = AsyncMock()

        # Test send
        message = {"test": "data"}
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        plugin.session.post.return_value = mock_response

        await plugin.send_message(message)
        plugin.session.post.assert_called_once()

        # Test receive
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "data"}
        plugin.session.get.return_value = mock_response

        response = await plugin.receive_message()
        assert response == {"response": "data"}

    @pytest.mark.asyncio
    async def test_http_plugin_disconnect(self):
        """Test HTTP plugin disconnect."""
        config = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http",
            version="1.0.0",
            description="HTTP transport",
            config_schema={},
            default_config={"base_url": "http://localhost:8000"},
        )

        plugin = HTTPTransportPlugin(config)
        plugin.session = AsyncMock()

        await plugin.disconnect()

        assert plugin._connected is False
        assert plugin.session is None
        plugin.session.aclose.assert_called_once()


class TestStdioTransportPlugin:
    """Test StdioTransportPlugin functionality."""

    @pytest.mark.asyncio
    async def test_stdio_plugin_initialization(self):
        """Test stdio plugin initialization."""
        config = TransportConfig(
            transport_type=TransportType.STDIO,
            name="stdio",
            version="1.0.0",
            description="Stdio transport",
            config_schema={},
            default_config={"command": "python -m metamcp.mcp.server"},
        )

        plugin = StdioTransportPlugin(config)
        await plugin.initialize()

        assert plugin._initialized is True

    @pytest.mark.asyncio
    async def test_stdio_plugin_connection(self):
        """Test stdio plugin connection."""
        config = TransportConfig(
            transport_type=TransportType.STDIO,
            name="stdio",
            version="1.0.0",
            description="Stdio transport",
            config_schema={},
            default_config={"command": "python -m metamcp.mcp.server"},
        )

        plugin = StdioTransportPlugin(config)

        # Mock subprocess
        mock_process = MagicMock()
        with patch("subprocess.Popen", return_value=mock_process):
            await plugin.connect()
            assert plugin._connected is True
            assert plugin.process == mock_process

    @pytest.mark.asyncio
    async def test_stdio_plugin_send_receive(self):
        """Test stdio plugin send and receive."""
        config = TransportConfig(
            transport_type=TransportType.STDIO,
            name="stdio",
            version="1.0.0",
            description="Stdio transport",
            config_schema={},
            default_config={"command": "python -m metamcp.mcp.server"},
        )

        plugin = StdioTransportPlugin(config)
        plugin._connected = True
        plugin.process = MagicMock()
        plugin.process.stdin = MagicMock()
        plugin.process.stdout = MagicMock()
        plugin.process.stdout.readline.return_value = '{"response": "data"}\n'

        # Test send
        message = {"test": "data"}
        await plugin.send_message(message)
        plugin.process.stdin.write.assert_called_once()
        plugin.process.stdin.flush.assert_called_once()

        # Test receive
        response = await plugin.receive_message()
        assert response == {"response": "data"}

    @pytest.mark.asyncio
    async def test_stdio_plugin_disconnect(self):
        """Test stdio plugin disconnect."""
        config = TransportConfig(
            transport_type=TransportType.STDIO,
            name="stdio",
            version="1.0.0",
            description="Stdio transport",
            config_schema={},
            default_config={"command": "python -m metamcp.mcp.server"},
        )

        plugin = StdioTransportPlugin(config)
        plugin.process = MagicMock()
        plugin.process.wait.return_value = 0

        await plugin.disconnect()

        assert plugin._connected is False
        assert plugin.process is None
        plugin.process.terminate.assert_called_once()


class TestTransportPluginManager:
    """Test TransportPluginManager functionality."""

    @pytest.mark.asyncio
    async def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        manager = TransportPluginManager()

        await manager.initialize()

        assert manager._initialized is True
        assert len(manager.plugins) > 0  # Should have built-in plugins

    @pytest.mark.asyncio
    async def test_register_plugin(self):
        """Test registering a plugin."""
        manager = TransportPluginManager()

        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        assert "test-plugin" in manager.plugins
        assert "test-plugin" in manager.plugin_configs

    @pytest.mark.asyncio
    async def test_get_plugin(self):
        """Test getting a plugin."""
        manager = TransportPluginManager()

        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        plugin = await manager.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.config.name == "test-plugin"

    @pytest.mark.asyncio
    async def test_get_plugins_by_type(self):
        """Test getting plugins by type."""
        manager = TransportPluginManager()

        # Register multiple plugins of different types
        config1 = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket1",
            version="1.0.0",
            description="WebSocket 1",
            config_schema={},
            default_config={},
        )

        config2 = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket2",
            version="1.0.0",
            description="WebSocket 2",
            config_schema={},
            default_config={},
        )

        config3 = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http1",
            version="1.0.0",
            description="HTTP 1",
            config_schema={},
            default_config={},
        )

        await manager.register_plugin(config1, WebSocketTransportPlugin)
        await manager.register_plugin(config2, WebSocketTransportPlugin)
        await manager.register_plugin(config3, HTTPTransportPlugin)

        websocket_plugins = await manager.get_plugins_by_type(TransportType.WEBSOCKET)
        http_plugins = await manager.get_plugins_by_type(TransportType.HTTP)

        assert len(websocket_plugins) == 2
        assert len(http_plugins) == 1

    @pytest.mark.asyncio
    async def test_get_available_plugins(self):
        """Test getting available plugins information."""
        manager = TransportPluginManager()

        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        plugins_info = await manager.get_available_plugins()

        assert len(plugins_info) > 0
        test_plugin_info = next(p for p in plugins_info if p["name"] == "test-plugin")
        assert test_plugin_info["type"] == "custom"
        assert test_plugin_info["version"] == "1.0.0"
        assert test_plugin_info["enabled"] is True

    @pytest.mark.asyncio
    async def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins."""
        manager = TransportPluginManager()

        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        # Disable plugin
        success = await manager.disable_plugin("test-plugin")
        assert success is True
        assert manager.plugin_configs["test-plugin"].enabled is False

        # Enable plugin
        success = await manager.enable_plugin("test-plugin")
        assert success is True
        assert manager.plugin_configs["test-plugin"].enabled is True

    @pytest.mark.asyncio
    async def test_create_transport_connection(self):
        """Test creating transport connections."""
        manager = TransportPluginManager()

        # Register a custom plugin
        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
            priority=200,  # Higher priority
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        # Create connection
        connection = await manager.create_transport_connection(TransportType.CUSTOM)

        assert connection is not None
        assert connection.config.name == "test-plugin"

    @pytest.mark.asyncio
    async def test_create_transport_connection_no_plugins(self):
        """Test creating transport connection with no available plugins."""
        manager = TransportPluginManager()

        # Try to create connection without registering any plugins
        connection = await manager.create_transport_connection(TransportType.CUSTOM)

        assert connection is None

    @pytest.mark.asyncio
    async def test_create_transport_connection_disabled_plugin(self):
        """Test creating transport connection with disabled plugin."""
        manager = TransportPluginManager()

        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
            enabled=False,
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        # Try to create connection with disabled plugin
        connection = await manager.create_transport_connection(TransportType.CUSTOM)

        assert connection is None

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test shutting down the plugin manager."""
        manager = TransportPluginManager()

        config = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            config_schema={},
            default_config={},
        )

        await manager.register_plugin(config, CustomTransportPlugin)

        # Mock the plugin's disconnect method
        plugin = manager.plugins["test-plugin"]
        plugin.disconnect = AsyncMock()

        await manager.shutdown()

        assert manager._initialized is False
        plugin.disconnect.assert_called_once()


class TestLoadBalancedMCPClient:
    """Test LoadBalancedMCPClient functionality."""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        """Test creating a load balanced client."""
        from metamcp.mcp.load_balancer import LoadBalancer, LoadBalancingStrategy

        load_balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(load_balancer)

        assert client.load_balancer == load_balancer
        assert len(client.active_connections) == 0
        assert client.client_id is not None

    @pytest.mark.asyncio
    async def test_send_request_no_servers(self):
        """Test sending request with no available servers."""
        from metamcp.mcp.load_balancer import LoadBalancer, LoadBalancingStrategy

        load_balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(load_balancer)

        with pytest.raises(RuntimeError, match="No healthy servers available"):
            await client.send_request({"test": "data"})

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        from metamcp.mcp.load_balancer import LoadBalancer, LoadBalancingStrategy

        load_balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        client = LoadBalancedMCPClient(load_balancer)

        # Add a mock connection
        mock_connection = MagicMock()
        mock_connection.close = AsyncMock()
        client.active_connections["test-server"] = mock_connection

        await client.close()

        assert len(client.active_connections) == 0
        mock_connection.close.assert_called_once()


class TestPluginDiscovery:
    """Test plugin discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_plugins_empty_directory(self):
        """Test discovering plugins in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugins = await discover_plugins(temp_dir)
            assert len(plugins) == 0

    @pytest.mark.asyncio
    async def test_discover_plugins_with_valid_plugin(self):
        """Test discovering plugins with valid plugin file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a valid plugin file
            plugin_content = """
from metamcp.mcp.transport_plugins import TransportPlugin, TransportConfig, TransportType

class TestPlugin(TransportPlugin):
    async def initialize(self):
        self._initialized = True
    
    async def connect(self):
        self._connected = True
    
    async def disconnect(self):
        self._connected = False
    
    async def send_message(self, message):
        pass
    
    async def receive_message(self):
        return None
    
    async def is_connected(self):
        return self._connected
"""

            plugin_file = temp_dir + "/test_plugin.py"
            with open(plugin_file, "w") as f:
                f.write(plugin_content)

            plugins = await discover_plugins(temp_dir)
            assert len(plugins) == 1
            assert plugins[0].__name__ == "TestPlugin"

    @pytest.mark.asyncio
    async def test_load_plugin_from_module(self):
        """Test loading plugin from module."""
        # Test with a mock module
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.TestPlugin = CustomTransportPlugin
            mock_import.return_value = mock_module

            plugin_class = await load_plugin_from_module("test.module", "TestPlugin")
            assert plugin_class == CustomTransportPlugin

    @pytest.mark.asyncio
    async def test_load_plugin_from_module_invalid_class(self):
        """Test loading invalid plugin class from module."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.InvalidPlugin = str  # Not a TransportPlugin
            mock_import.return_value = mock_module

            with pytest.raises(ValueError, match="is not a TransportPlugin subclass"):
                await load_plugin_from_module("test.module", "InvalidPlugin")


class TestTransportPluginIntegration:
    """Integration tests for transport plugins."""

    @pytest.mark.asyncio
    async def test_complete_plugin_workflow(self):
        """Test complete plugin workflow."""
        manager = TransportPluginManager()

        # Register multiple plugins
        config1 = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport",
            config_schema={},
            default_config={"url": "ws://localhost:8080"},
        )

        config2 = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http",
            version="1.0.0",
            description="HTTP transport",
            config_schema={},
            default_config={"base_url": "http://localhost:8000"},
        )

        await manager.register_plugin(config1, WebSocketTransportPlugin)
        await manager.register_plugin(config2, HTTPTransportPlugin)

        # Get available plugins
        plugins_info = await manager.get_available_plugins()
        assert len(plugins_info) >= 2

        # Get plugins by type
        websocket_plugins = await manager.get_plugins_by_type(TransportType.WEBSOCKET)
        http_plugins = await manager.get_plugins_by_type(TransportType.HTTP)

        assert len(websocket_plugins) >= 1
        assert len(http_plugins) >= 1

        # Test plugin status
        websocket_plugin = websocket_plugins[0]
        status = await websocket_plugin.get_status()
        assert status["name"] == "websocket"
        assert status["type"] == "websocket"

        # Cleanup
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_plugin_priority_selection(self):
        """Test plugin selection based on priority."""
        manager = TransportPluginManager()

        # Register plugins with different priorities
        config1 = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="low-priority",
            version="1.0.0",
            description="Low priority plugin",
            config_schema={},
            default_config={},
            priority=50,
        )

        config2 = TransportConfig(
            transport_type=TransportType.CUSTOM,
            name="high-priority",
            version="1.0.0",
            description="High priority plugin",
            config_schema={},
            default_config={},
            priority=200,
        )

        await manager.register_plugin(config1, CustomTransportPlugin)
        await manager.register_plugin(config2, CustomTransportPlugin)

        # Create connection - should select high priority plugin
        connection = await manager.create_transport_connection(TransportType.CUSTOM)

        assert connection is not None
        assert connection.config.name == "high-priority"

        # Cleanup
        await manager.shutdown()

"""
MCP Transport Plugin System

This module provides a plugin system for extensible transport layers,
allowing custom transport implementations to be easily integrated.
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..utils.logging import get_logger
from .load_balancer import LoadBalancedMCPClient

logger = get_logger(__name__)


class TransportType(Enum):
    """Supported transport types."""

    WEBSOCKET = "websocket"
    HTTP = "http"
    STDIO = "stdio"
    GRPC = "grpc"
    MQTT = "mqtt"
    REDIS = "redis"
    CUSTOM = "custom"


@dataclass
class TransportConfig:
    """Configuration for transport plugins."""

    transport_type: TransportType
    name: str
    version: str
    description: str
    config_schema: dict[str, Any]
    default_config: dict[str, Any]
    enabled: bool = True
    priority: int = 100


class TransportPlugin(ABC):
    """Base class for transport plugins."""

    def __init__(self, config: TransportConfig):
        """Initialize transport plugin."""
        self.config = config
        self._initialized = False
        self._connected = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the transport plugin."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from transport."""
        pass

    @abstractmethod
    async def send_message(self, message: dict[str, Any]) -> None:
        """Send a message via the transport."""
        pass

    @abstractmethod
    async def receive_message(self) -> dict[str, Any] | None:
        """Receive a message from the transport."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if transport is connected."""
        pass

    async def get_status(self) -> dict[str, Any]:
        """Get transport status."""
        return {
            "name": self.config.name,
            "type": self.config.transport_type.value,
            "version": self.config.version,
            "initialized": self._initialized,
            "connected": self._connected,
            "enabled": self.config.enabled,
        }


class WebSocketTransportPlugin(TransportPlugin):
    """WebSocket transport plugin implementation."""

    def __init__(self, config: TransportConfig):
        """Initialize WebSocket transport."""
        super().__init__(config)
        self.websocket = None
        self.url = config.default_config.get("url", "ws://localhost:8080")

    async def initialize(self) -> None:
        """Initialize WebSocket transport."""
        try:
            import websockets

            self._initialized = True
            logger.info(f"WebSocket transport {self.config.name} initialized")
        except ImportError:
            raise RuntimeError("websockets library not available")

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        try:
            import websockets

            self.websocket = await websockets.connect(self.url)
            self._connected = True
            logger.info(f"Connected to WebSocket server: {self.url}")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self._connected = False
            logger.info("Disconnected from WebSocket server")

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send message via WebSocket."""
        if not self._connected:
            raise RuntimeError("WebSocket not connected")

        import json

        await self.websocket.send(json.dumps(message))

    async def receive_message(self) -> dict[str, Any] | None:
        """Receive message from WebSocket."""
        if not self._connected:
            return None

        try:
            import json

            message = await self.websocket.recv()
            return json.loads(message)
        except Exception as e:
            logger.error(f"Error receiving WebSocket message: {e}")
            return None

    async def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self.websocket and not self.websocket.closed


class HTTPTransportPlugin(TransportPlugin):
    """HTTP transport plugin implementation."""

    def __init__(self, config: TransportConfig):
        """Initialize HTTP transport."""
        super().__init__(config)
        self.base_url = config.default_config.get("base_url", "http://localhost:8000")
        self.session = None

    async def initialize(self) -> None:
        """Initialize HTTP transport."""
        try:
            import httpx

            self.session = httpx.AsyncClient()
            self._initialized = True
            logger.info(f"HTTP transport {self.config.name} initialized")
        except ImportError:
            raise RuntimeError("httpx library not available")

    async def connect(self) -> None:
        """Establish HTTP connection."""
        try:
            # Test connection
            response = await self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            self._connected = True
            logger.info(f"Connected to HTTP server: {self.base_url}")
        except Exception as e:
            logger.error(f"HTTP connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect HTTP transport."""
        if self.session:
            await self.session.aclose()
            self.session = None
            self._connected = False
            logger.info("Disconnected from HTTP server")

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send message via HTTP."""
        if not self._connected:
            raise RuntimeError("HTTP transport not connected")

        try:
            response = await self.session.post(
                f"{self.base_url}/mcp/message", json=message
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error sending HTTP message: {e}")
            raise

    async def receive_message(self) -> dict[str, Any] | None:
        """Receive message from HTTP (polling)."""
        if not self._connected:
            return None

        try:
            response = await self.session.get(f"{self.base_url}/mcp/messages")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error receiving HTTP message: {e}")
            return None

    async def is_connected(self) -> bool:
        """Check if HTTP transport is connected."""
        return self._connected and self.session is not None


class StdioTransportPlugin(TransportPlugin):
    """Stdio transport plugin implementation."""

    def __init__(self, config: TransportConfig):
        """Initialize stdio transport."""
        super().__init__(config)
        self.process = None

    async def initialize(self) -> None:
        """Initialize stdio transport."""
        self._initialized = True
        logger.info(f"Stdio transport {self.config.name} initialized")

    async def connect(self) -> None:
        """Start stdio process."""
        try:
            import subprocess

            command = self.config.default_config.get(
                "command", "python -m metamcp.mcp.server"
            )
            cmd_parts = command.split()

            self.process = subprocess.Popen(
                cmd_parts,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self._connected = True
            logger.info(f"Started stdio process: {command}")
        except Exception as e:
            logger.error(f"Stdio connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Stop stdio process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None
                self._connected = False
                logger.info("Stopped stdio process")

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send message via stdio."""
        if not self._connected:
            raise RuntimeError("Stdio transport not connected")

        try:
            import json

            message_str = json.dumps(message) + "\n"
            self.process.stdin.write(message_str)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending stdio message: {e}")
            raise

    async def receive_message(self) -> dict[str, Any] | None:
        """Receive message from stdio."""
        if not self._connected:
            return None

        try:
            import json

            line = self.process.stdout.readline()
            if line:
                return json.loads(line.strip())
            return None
        except Exception as e:
            logger.error(f"Error receiving stdio message: {e}")
            return None

    async def is_connected(self) -> bool:
        """Check if stdio transport is connected."""
        return self._connected and self.process and self.process.poll() is None


class TransportPluginManager:
    """Manages transport plugins."""

    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: dict[str, TransportPlugin] = {}
        self.plugin_configs: dict[str, TransportConfig] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the plugin manager."""
        if self._initialized:
            return

        # Register built-in plugins
        await self._register_builtin_plugins()

        # Load custom plugins
        await self._load_custom_plugins()

        self._initialized = True
        logger.info("Transport plugin manager initialized")

    async def _register_builtin_plugins(self) -> None:
        """Register built-in transport plugins."""
        # WebSocket plugin
        websocket_config = TransportConfig(
            transport_type=TransportType.WEBSOCKET,
            name="websocket",
            version="1.0.0",
            description="WebSocket transport for MCP",
            config_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "WebSocket URL"},
                    "timeout": {"type": "number", "description": "Connection timeout"},
                },
                "required": ["url"],
            },
            default_config={"url": "ws://localhost:8080", "timeout": 30.0},
        )

        # HTTP plugin
        http_config = TransportConfig(
            transport_type=TransportType.HTTP,
            name="http",
            version="1.0.0",
            description="HTTP transport for MCP",
            config_schema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "HTTP base URL"},
                    "timeout": {"type": "number", "description": "Request timeout"},
                },
                "required": ["base_url"],
            },
            default_config={"base_url": "http://localhost:8000", "timeout": 30.0},
        )

        # Stdio plugin
        stdio_config = TransportConfig(
            transport_type=TransportType.STDIO,
            name="stdio",
            version="1.0.0",
            description="Stdio transport for MCP",
            config_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {"type": "number", "description": "Process timeout"},
                },
                "required": ["command"],
            },
            default_config={"command": "python -m metamcp.mcp.server", "timeout": 30.0},
        )

        # Register plugins
        await self.register_plugin(websocket_config, WebSocketTransportPlugin)
        await self.register_plugin(http_config, HTTPTransportPlugin)
        await self.register_plugin(stdio_config, StdioTransportPlugin)

    async def _load_custom_plugins(self) -> None:
        """Load custom plugins from configuration."""
        # This would load custom plugins from config files or environment
        # For now, we'll just log that this is available
        logger.info("Custom plugin loading available")

    async def register_plugin(
        self, config: TransportConfig, plugin_class: type[TransportPlugin]
    ) -> None:
        """Register a transport plugin."""
        try:
            plugin = plugin_class(config)
            await plugin.initialize()

            self.plugins[config.name] = plugin
            self.plugin_configs[config.name] = config

            logger.info(f"Registered transport plugin: {config.name}")

        except Exception as e:
            logger.error(f"Failed to register plugin {config.name}: {e}")

    async def get_plugin(self, name: str) -> TransportPlugin | None:
        """Get a plugin by name."""
        return self.plugins.get(name)

    async def get_plugins_by_type(
        self, transport_type: TransportType
    ) -> list[TransportPlugin]:
        """Get all plugins of a specific type."""
        plugins = []
        for plugin in self.plugins.values():
            if plugin.config.transport_type == transport_type:
                plugins.append(plugin)
        return plugins

    async def get_available_plugins(self) -> list[dict[str, Any]]:
        """Get information about all available plugins."""
        plugins_info = []
        for name, plugin in self.plugins.items():
            config = self.plugin_configs[name]
            plugins_info.append(
                {
                    "name": name,
                    "type": config.transport_type.value,
                    "version": config.version,
                    "description": config.description,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "status": await plugin.get_status(),
                }
            )
        return plugins_info

    async def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        if name in self.plugins:
            self.plugin_configs[name].enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False

    async def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        if name in self.plugins:
            self.plugin_configs[name].enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False

    async def create_transport_connection(
        self, transport_type: TransportType, config: dict[str, Any] = None
    ) -> TransportPlugin | None:
        """Create a transport connection."""
        plugins = await self.get_plugins_by_type(transport_type)

        if not plugins:
            logger.error(f"No plugins available for transport type: {transport_type}")
            return None

        # Get the highest priority enabled plugin
        enabled_plugins = [p for p in plugins if p.config.enabled]
        if not enabled_plugins:
            logger.error(f"No enabled plugins for transport type: {transport_type}")
            return None

        plugin = max(enabled_plugins, key=lambda p: p.config.priority)

        try:
            await plugin.connect()
            logger.info(
                f"Created transport connection using plugin: {plugin.config.name}"
            )
            return plugin
        except Exception as e:
            logger.error(f"Failed to create transport connection: {e}")
            return None

    async def shutdown(self) -> None:
        """Shutdown all plugins."""
        for name, plugin in self.plugins.items():
            try:
                await plugin.disconnect()
                logger.info(f"Disconnected plugin: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting plugin {name}: {e}")

        self._initialized = False
        logger.info("Transport plugin manager shutdown complete")


class CustomTransportPlugin(TransportPlugin):
    """Example custom transport plugin."""

    def __init__(self, config: TransportConfig):
        """Initialize custom transport."""
        super().__init__(config)
        self.custom_connection = None

    async def initialize(self) -> None:
        """Initialize custom transport."""
        # Custom initialization logic
        self._initialized = True
        logger.info(f"Custom transport {self.config.name} initialized")

    async def connect(self) -> None:
        """Establish custom connection."""
        # Custom connection logic
        self._connected = True
        logger.info(f"Connected to custom transport: {self.config.name}")

    async def disconnect(self) -> None:
        """Disconnect custom transport."""
        self._connected = False
        logger.info(f"Disconnected from custom transport: {self.config.name}")

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send message via custom transport."""
        if not self._connected:
            raise RuntimeError("Custom transport not connected")

        # Custom send logic
        logger.debug(f"Sent message via custom transport: {message}")

    async def receive_message(self) -> dict[str, Any] | None:
        """Receive message from custom transport."""
        if not self._connected:
            return None

        # Custom receive logic
        return None

    async def is_connected(self) -> bool:
        """Check if custom transport is connected."""
        return self._connected


# Plugin discovery and loading utilities
async def discover_plugins(plugin_path: str = None) -> list[type[TransportPlugin]]:
    """Discover transport plugins in a directory."""
    plugins = []

    if not plugin_path:
        return plugins

    try:
        import importlib.util
        import os

        for filename in os.listdir(plugin_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                file_path = os.path.join(plugin_path, filename)

                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for TransportPlugin subclasses
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, TransportPlugin)
                        and obj != TransportPlugin
                    ):
                        plugins.append(obj)
                        logger.info(f"Discovered plugin: {obj.__name__}")

    except Exception as e:
        logger.error(f"Error discovering plugins: {e}")

    return plugins


async def load_plugin_from_module(
    module_name: str, class_name: str
) -> type[TransportPlugin]:
    """Load a plugin class from a module."""
    try:
        module = importlib.import_module(module_name)
        plugin_class = getattr(module, class_name)

        if not issubclass(plugin_class, TransportPlugin):
            raise ValueError(f"{class_name} is not a TransportPlugin subclass")

        return plugin_class

    except Exception as e:
        logger.error(f"Error loading plugin {module_name}.{class_name}: {e}")
        raise

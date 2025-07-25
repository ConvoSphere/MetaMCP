"""
MCP Proxy Module

This module provides proxy functionality for wrapping arbitrary MCP servers
with MetaMCP's enhanced features like semantic search, security, and monitoring.
"""

from .discovery import ServerDiscovery
from .interceptor import ToolCallInterceptor
from .manager import ProxyManager
from .wrapper import MCPProxyWrapper, WrappedServerConfig

__all__ = [
    "MCPProxyWrapper",
    "ProxyManager",
    "ToolCallInterceptor",
    "ServerDiscovery",
    "WrappedServerConfig",
]

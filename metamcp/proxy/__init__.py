"""
MCP Proxy Module

This module provides proxy functionality for wrapping arbitrary MCP servers
with MetaMCP's enhanced features like semantic search, security, and monitoring.
"""

from .wrapper import MCPProxyWrapper
from .manager import ProxyManager
from .interceptor import ToolCallInterceptor
from .discovery import ServerDiscovery

__all__ = [
    "MCPProxyWrapper",
    "ProxyManager", 
    "ToolCallInterceptor",
    "ServerDiscovery"
] 
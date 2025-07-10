"""
MCP Meta-Server - A dynamic tool proxy for AI agents

This package provides a Model Context Protocol (MCP) compatible server that acts as an
intelligent proxy and tool registry for AI agents. It enables dynamic tool discovery
through semantic search and provides enterprise-grade security and policy management.

Key Features:
- MCP Protocol compatibility
- Semantic tool discovery with vector search
- Policy-based access control
- Tool registry and management
- LLM integration for tool descriptions
- Enterprise security features
"""

__version__ = "1.0.0"
__author__ = "MetaMCP Team"
__email__ = "team@metamcp.org"
__license__ = "MIT"
__description__ = "A dynamic MCP Meta-Server for AI agents with semantic tool discovery"

# Core exports
from .client import MetaMCPClient
from .config import Settings, get_settings

# Exception classes
from .exceptions import (
    MCPProtocolError,
    MetaMCPError,
    PolicyViolationError,
    ToolNotFoundError,
    VectorSearchError,
)

# Security exports
from .security.auth import AuthManager
from .security.policies import PolicyEngine
from .server import MetaMCPServer
from .tools.models import Tool, ToolCapability, ToolCategory

# Tool-related exports
from .tools.registry import ToolRegistry
from .utils.helpers import create_tool_embedding, validate_tool_schema

# Utilities
from .utils.logging import get_logger

# Vector search exports
from .vector.client import VectorSearchClient
from .vector.models import EmbeddingModel, SearchResult

__all__ = [
    # Core
    "MetaMCPServer",
    "MetaMCPClient",
    "Settings",
    "get_settings",

    # Exceptions
    "MetaMCPError",
    "ToolNotFoundError",
    "PolicyViolationError",
    "VectorSearchError",
    "MCPProtocolError",

    # Tools
    "ToolRegistry",
    "Tool",
    "ToolCategory",
    "ToolCapability",

    # Vector Search
    "VectorSearchClient",
    "SearchResult",
    "EmbeddingModel",

    # Security
    "AuthManager",
    "PolicyEngine",

    # Utilities
    "get_logger",
    "create_tool_embedding",
    "validate_tool_schema",

    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
]

# Module-level logger
import logging

_logger = logging.getLogger(__name__)

def get_version() -> str:
    """Get the current version of MetaMCP."""
    return __version__

def get_info() -> dict:
    """Get package information."""
    return {
        "name": "metamcp",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "description": __description__,
    }

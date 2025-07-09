"""
API modules for MCP Meta-Server

This package contains FastAPI routers and related components for the REST API.
"""

from .router import create_api_router

__all__ = ["create_api_router"]
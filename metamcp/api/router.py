"""
Main API Router for MCP Meta-Server

This module creates and configures the main FastAPI router with all endpoints
for tool management, search, health checks, and administrative functions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional

from ..config import get_settings
from ..exceptions import MetaMCPError
from ..utils.logging import get_logger
from .tools import tools_router
from .health import health_router
from .auth import auth_router


logger = get_logger(__name__)
settings = get_settings()


def create_api_router() -> APIRouter:
    """
    Create and configure the main API router.
    
    Returns:
        Configured FastAPI router
    """
    # Create main router
    router = APIRouter()
    
    # Include sub-routers
    router.include_router(
        tools_router,
        prefix="/tools",
        tags=["tools"]
    )
    
    router.include_router(
        health_router,
        prefix="/health",
        tags=["health"]
    )
    
    router.include_router(
        auth_router,
        prefix="/auth",
        tags=["authentication"]
    )
    
    # Add root endpoints
    @router.get("/", summary="API Root")
    async def api_root():
        """Get API information."""
        return {
            "name": "MCP Meta-Server API",
            "version": "1.0.0",
            "description": "A dynamic MCP Meta-Server for AI agents with semantic tool discovery",
            "docs_url": "/docs",
            "health_url": "/health"
        }
    
    @router.get("/info", summary="Server Information")
    async def server_info():
        """Get detailed server information."""
        return {
            "server": {
                "name": "MCP Meta-Server",
                "version": "1.0.0",
                "environment": "production" if settings.is_production() else "development",
                "features": {
                    "mcp_protocol": True,
                    "semantic_search": True,
                    "policy_engine": True,
                    "admin_ui": settings.admin_ui_enabled,
                    "metrics": settings.metrics_enabled
                }
            },
            "api": {
                "version": "v1",
                "base_path": "/api/v1",
                "documentation": "/docs" if settings.api_docs_enabled else None
            },
            "capabilities": {
                "tool_registry": True,
                "vector_search": True,
                "llm_integration": True,
                "authentication": True,
                "authorization": True,
                "audit_logging": settings.audit_log_enabled
            }
        }
    
    return router
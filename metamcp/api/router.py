"""
API Router

This module provides the main FastAPI router configuration
and includes all API endpoints.
"""

from fastapi import APIRouter

from .auth import auth_router
from .composition import composition_router
from .health import health_router
from .oauth import router as oauth_router
from .proxy import router as proxy_router
from .tools import tools_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(oauth_router)
router.include_router(tools_router)
router.include_router(proxy_router)
router.include_router(composition_router)


def create_api_router() -> APIRouter:
    """
    Create and configure the main API router.
    
    Returns:
        APIRouter: Configured router with all endpoints
    """
    return router

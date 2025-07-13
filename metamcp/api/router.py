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

# Include all sub-routers with proper prefixes
router.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
router.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
router.include_router(oauth_router, prefix="/api/v1/oauth", tags=["OAuth"])
router.include_router(tools_router, prefix="/api/v1/tools", tags=["Tools"])
router.include_router(proxy_router, prefix="/api/v1/proxy", tags=["Proxy"])
router.include_router(composition_router, prefix="/api/v1/composition", tags=["Composition"])


def create_api_router() -> APIRouter:
    """
    Create and configure the main API router.
    
    Returns:
        APIRouter: Configured router with all endpoints
    """
    return router

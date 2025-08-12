"""
API v1 Router

This module provides the v1 API router with all existing endpoints.
"""

from fastapi import APIRouter

# Import existing routers
from ..admin import admin_router
from ..auth import auth_router
from ..composition import composition_router
from ..health import health_router
from ..oauth import router as oauth_router
from ..proxy import router as proxy_router
from ..tools import tools_router


def create_v1_router() -> APIRouter:
    """
    Create and configure the v1 API router.

    Returns:
        APIRouter: Configured v1 router with all endpoints
    """
    router = APIRouter()

    # Include all existing routers as v1 endpoints
    router.include_router(auth_router, prefix="/auth", tags=["Authentication v1"])
    router.include_router(health_router, prefix="/health", tags=["Health v1"])
    router.include_router(oauth_router, prefix="/oauth", tags=["OAuth v1"])
    router.include_router(tools_router, prefix="/tools", tags=["Tools v1"])
    router.include_router(proxy_router, prefix="/proxy", tags=["Proxy v1"])
    router.include_router(
        composition_router, prefix="/composition", tags=["Composition v1"]
    )
    router.include_router(admin_router, prefix="/admin", tags=["Admin v1"])

    return router

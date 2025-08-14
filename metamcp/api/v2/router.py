"""
API v2 Router

This module provides the v2 API router with enhanced features and improved endpoints.
"""

from fastapi import APIRouter

from .admin import admin_router
from .analytics import analytics_router

# Import v2 specific routers
from .auth import auth_router
from .composition import composition_router
from .health import health_router
from .tools import tools_router


def create_v2_router() -> APIRouter:
    """
    Create and configure the v2 API router with enhanced features.

    Returns:
        APIRouter: Configured v2 router with enhanced endpoints
    """
    router = APIRouter()

    # Include v2 routers with enhanced features
    router.include_router(auth_router, prefix="/auth", tags=["Authentication v2"])
    router.include_router(health_router, prefix="/health", tags=["Health v2"])
    router.include_router(tools_router, prefix="/tools", tags=["Tools v2"])
    router.include_router(
        composition_router, prefix="/composition", tags=["Composition v2"]
    )
    router.include_router(admin_router, prefix="/admin", tags=["Admin v2"])
    router.include_router(analytics_router, prefix="/analytics", tags=["Analytics v2"])

    return router

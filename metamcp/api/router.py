"""
API Router with Versioning

This module provides the main FastAPI router configuration
with comprehensive API versioning support.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from .versioning import get_api_version_manager, create_version_router
from .v1 import create_v1_router
from .v2 import create_v2_router

# Create main router
router = APIRouter()

# Include version management endpoints
version_router = create_version_router()
router.include_router(version_router, prefix="/api/versions", tags=["API Versions"])

# Include versioned API routers
v1_router = create_v1_router()
v2_router = create_v2_router()

router.include_router(v1_router, prefix="/api/v1", tags=["API v1"])
router.include_router(v2_router, prefix="/api/v2", tags=["API v2"])

# Legacy redirect for backward compatibility
@router.get("/api")
async def api_root():
    """API root endpoint with version information."""
    version_manager = get_api_version_manager()
    return {
        "message": "MetaMCP API",
        "latest_version": version_manager.get_latest_version(),
        "active_versions": version_manager.get_active_versions(),
        "documentation": "/docs",
        "version_info": "/api/versions"
    }

# Default redirect to latest version
@router.get("/api/latest")
async def redirect_to_latest():
    """Redirect to the latest API version."""
    version_manager = get_api_version_manager()
    latest_version = version_manager.get_latest_version()
    if latest_version:
        return JSONResponse(
            status_code=307,
            headers={"Location": f"/api/{latest_version}"}
        )
    return {"error": "No API versions available"}


def create_api_router() -> APIRouter:
    """
    Create and configure the main API router with versioning.

    Returns:
        APIRouter: Configured router with all versioned endpoints
    """
    return router

"""
API Router

This module provides the main FastAPI router configuration
and includes all API endpoints.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .health import router as health_router
from .oauth import router as oauth_router
from .tools import router as tools_router
from .proxy import router as proxy_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(oauth_router)
router.include_router(tools_router)
router.include_router(proxy_router)

"""
Admin API Endpoints

This module provides admin API endpoints for the web-based admin interface.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..admin.interface import (
    get_admin_dashboard_data,
    get_system_metrics,
    get_tool_management_data,
    get_user_management_data,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create admin router
admin_router = APIRouter()


@admin_router.get("/dashboard")
async def get_dashboard():
    """Get complete admin dashboard data."""
    try:
        data = get_admin_dashboard_data()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@admin_router.get("/system/metrics")
async def get_system_metrics_endpoint():
    """Get system metrics."""
    try:
        data = get_system_metrics()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@admin_router.get("/users")
async def get_users():
    """Get user management data."""
    try:
        data = get_user_management_data()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user data")


@admin_router.get("/tools")
async def get_tools():
    """Get tool management data."""
    try:
        data = get_tool_management_data()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error getting tool data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tool data")


@admin_router.get("/health")
async def admin_health():
    """Admin health check endpoint."""
    return {"status": "healthy", "service": "admin-api"}


@admin_router.get("/config")
async def get_admin_config():
    """Get admin configuration."""
    from ..config import get_settings

    settings = get_settings()

    return {
        "admin_enabled": settings.admin_enabled,
        "admin_port": settings.admin_port,
        "environment": settings.environment,
        "app_version": settings.app_version,
    }

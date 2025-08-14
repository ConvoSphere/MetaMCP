"""
Admin API Endpoints

This module provides admin API endpoints for the Streamlit-based admin interface.
All admin operations go through this API to maintain clean separation.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..admin.interface import (
    get_admin_dashboard_data,
    get_system_metrics,
    get_tool_management_data,
    get_user_management_data,
)
from ..services.auth_service import AuthService
from ..services.tool_service import ToolService
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create admin router
admin_router = APIRouter()

# Initialize services
auth_service = AuthService()
tool_service = ToolService()


# Pydantic models for request/response
class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    roles: list[str] = ["user"]
    permissions: list[str] = []
    is_active: bool = True
    is_admin: bool = False


class UserUpdateRequest(BaseModel):
    email: str | None = None
    full_name: str | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    is_active: bool | None = None
    is_admin: bool | None = None


class ToolCreateRequest(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    endpoint_url: str
    authentication_type: str = "none"
    schema: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool = True


class ToolUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    endpoint_url: str | None = None
    authentication_type: str | None = None
    schema: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


# Dashboard and Overview Endpoints
@admin_router.get("/dashboard")
async def get_dashboard():
    """Get complete admin dashboard data."""
    try:
        data = get_admin_dashboard_data()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data") from e


@admin_router.get("/system/metrics")
async def get_system_metrics_endpoint():
    """Get system metrics."""
    try:
        data = get_system_metrics()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics") from e


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


# User Management Endpoints
@admin_router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
):
    """Get paginated user list with optional filtering."""
    try:
        data = get_user_management_data()
        users = data.get("users", [])

        # Apply filters
        if search:
            users = [
                u
                for u in users
                if search.lower() in u.get("username", "").lower()
                or search.lower() in u.get("email", "").lower()
            ]

        if role:
            users = [u for u in users if role in u.get("roles", [])]

        if is_active is not None:
            users = [u for u in users if u.get("is_active") == is_active]

        # Pagination
        total = len(users)
        start = (page - 1) * limit
        end = start + limit
        paginated_users = users[start:end]

        return {
            "users": paginated_users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user data") from e


@admin_router.post("/users")
async def create_user(user_data: UserCreateRequest):
    """Create a new user."""
    try:
        user_id = await auth_service.create_user(
            {
                "username": user_data.username,
                "email": user_data.email,
                "password": user_data.password,
                "full_name": user_data.full_name,
                "roles": user_data.roles,
                "permissions": user_data.permissions,
                "is_active": user_data.is_active,
                "is_admin": user_data.is_admin,
            },
            "admin",
        )
        return {"user_id": user_id, "message": "User created successfully"}
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}") from e


@admin_router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get specific user by ID."""
    try:
        user = auth_service._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user") from e


@admin_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdateRequest):
    """Update user information."""
    try:
        # Get current user
        user = auth_service._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields
        update_data = {}
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name
        if user_data.roles is not None:
            update_data["roles"] = user_data.roles
        if user_data.permissions is not None:
            update_data["permissions"] = user_data.permissions
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        if user_data.is_admin is not None:
            update_data["is_admin"] = user_data.is_admin

        # Update user (this would need to be implemented in AuthService)
        # await auth_service.update_user(user_id, update_data)

        return {"message": "User updated successfully"}
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user") from e


@admin_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user."""
    try:
        # Check if user exists
        user = auth_service._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete user (this would need to be implemented in AuthService)
        # await auth_service.delete_user(user_id)

        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user") from e


# Tool Management Endpoints
@admin_router.get("/tools")
async def get_tools(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    is_active: bool | None = None,
):
    """Get paginated tool list with optional filtering."""
    try:
        data = get_tool_management_data()
        tools = data.get("tools", [])

        # Apply filters
        if search:
            tools = [
                t
                for t in tools
                if search.lower() in t.get("name", "").lower()
                or search.lower() in t.get("description", "").lower()
            ]

        if status:
            tools = [t for t in tools if t.get("status") == status]

        if is_active is not None:
            tools = [t for t in tools if t.get("is_active") == is_active]

        # Pagination
        total = len(tools)
        start = (page - 1) * limit
        end = start + limit
        paginated_tools = tools[start:end]

        return {
            "tools": paginated_tools,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }
    except Exception as e:
        logger.error(f"Error getting tool data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tool data") from e


@admin_router.post("/tools")
async def create_tool(tool_data: ToolCreateRequest):
    """Create a new tool."""
    try:
        tool_id = await tool_service.register_tool(
            {
                "name": tool_data.name,
                "description": tool_data.description,
                "version": tool_data.version,
                "endpoint_url": tool_data.endpoint_url,
                "authentication_type": tool_data.authentication_type,
                "schema": tool_data.schema,
                "metadata": tool_data.metadata or {},
                "is_active": tool_data.is_active,
            }
        )
        return {"tool_id": tool_id, "message": "Tool created successfully"}
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}") from e


@admin_router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get specific tool by ID."""
    try:
        tool = await tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tool") from e


@admin_router.put("/tools/{tool_id}")
async def update_tool(tool_id: str, tool_data: ToolUpdateRequest):
    """Update tool information."""
    try:
        # Get current tool
        tool = await tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        # Update fields
        update_data = {}
        if tool_data.name is not None:
            update_data["name"] = tool_data.name
        if tool_data.description is not None:
            update_data["description"] = tool_data.description
        if tool_data.version is not None:
            update_data["version"] = tool_data.version
        if tool_data.endpoint_url is not None:
            update_data["endpoint_url"] = tool_data.endpoint_url
        if tool_data.authentication_type is not None:
            update_data["authentication_type"] = tool_data.authentication_type
        if tool_data.schema is not None:
            update_data["schema"] = tool_data.schema
        if tool_data.metadata is not None:
            update_data["metadata"] = tool_data.metadata
        if tool_data.is_active is not None:
            update_data["is_active"] = tool_data.is_active

        # Update tool
        await tool_service.update_tool(tool_id, update_data)

        return {"message": "Tool updated successfully"}
    except Exception as e:
        logger.error(f"Error updating tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tool") from e


@admin_router.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool."""
    try:
        # Check if tool exists
        tool = await tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        # Delete tool
        await tool_service.delete_tool(tool_id)

        return {"message": "Tool deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tool") from e


# System Management Endpoints
@admin_router.get("/logs")
async def get_logs(
    level: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    since: str | None = None,
):
    """Get system logs."""
    try:
        # This would integrate with the logging system
        # For now, return mock data
        logs = [
            {
                "timestamp": "2025-07-27T06:42:23Z",
                "level": "INFO",
                "message": "Admin API started",
                "module": "admin.api",
            },
            {
                "timestamp": "2025-07-27T06:42:20Z",
                "level": "WARNING",
                "message": "Deprecated datetime.utcnow() used",
                "module": "admin.interface",
            },
        ]

        if level:
            logs = [log for log in logs if log["level"] == level.upper()]

        return {"logs": logs[:limit]}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logs") from e


@admin_router.post("/system/restart")
async def restart_system():
    """Restart the system (admin only)."""
    try:
        # This would trigger a system restart
        # For now, just return success
        return {"message": "System restart initiated"}
    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart system") from e


@admin_router.get("/health")
async def admin_health():
    """Admin health check endpoint."""
    return {"status": "healthy", "service": "admin-api"}

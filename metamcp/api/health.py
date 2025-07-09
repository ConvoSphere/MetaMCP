"""
Health Check API Router

This module provides health check endpoints for monitoring the MCP Meta-Server
and its components.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..config import get_settings
from ..exceptions import MetaMCPError
from ..utils.logging import get_logger


logger = get_logger(__name__)
settings = get_settings()

# Create router
health_router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================

class HealthStatus(BaseModel):
    """Health status model."""
    healthy: bool
    timestamp: str
    version: str
    uptime: Optional[float] = None
    error: Optional[str] = None


class ComponentHealth(BaseModel):
    """Component health status model."""
    healthy: bool
    timestamp: str
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DetailedHealthResponse(BaseModel):
    """Detailed health response model."""
    overall: HealthStatus
    components: Dict[str, ComponentHealth]
    system: Dict[str, Any]


# =============================================================================
# Dependencies
# =============================================================================

async def get_mcp_server():
    """Get MCP server instance from FastAPI app state."""
    # This will be injected by the main application
    pass


# =============================================================================
# API Endpoints
# =============================================================================

@health_router.get(
    "",
    response_model=HealthStatus,
    summary="Basic health check"
)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns basic health status of the server.
    """
    try:
        return HealthStatus(
            healthy=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            uptime=None  # TODO: Calculate actual uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthStatus(
            healthy=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            error=str(e)
        )


@health_router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed health check"
)
async def detailed_health_check(mcp_server = Depends(get_mcp_server)):
    """
    Detailed health check endpoint.
    
    Returns comprehensive health status of all components.
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Get component health status
        if mcp_server and mcp_server.is_initialized:
            component_status = await mcp_server.get_health_status()
        else:
            component_status = {
                "server": ComponentHealth(
                    healthy=False,
                    timestamp=timestamp,
                    error="Server not initialized"
                ).dict()
            }
        
        # Determine overall health
        overall_healthy = all(
            status.get("healthy", False) 
            for status in component_status.values()
        )
        
        # System information
        system_info = {
            "timestamp": timestamp,
            "timezone": str(timezone.utc),
            "debug_mode": settings.debug,
            "log_level": settings.log_level.value,
            "metrics_enabled": settings.metrics_enabled,
            "audit_enabled": settings.audit_log_enabled
        }
        
        return DetailedHealthResponse(
            overall=HealthStatus(
                healthy=overall_healthy,
                timestamp=timestamp,
                version="1.0.0"
            ),
            components={
                name: ComponentHealth(**status) 
                for name, status in component_status.items()
            },
            system=system_info
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        return DetailedHealthResponse(
            overall=HealthStatus(
                healthy=False,
                timestamp=timestamp,
                version="1.0.0",
                error=str(e)
            ),
            components={},
            system={"error": str(e)}
        )


@health_router.get(
    "/readiness",
    response_model=HealthStatus,
    summary="Readiness check"
)
async def readiness_check(mcp_server = Depends(get_mcp_server)):
    """
    Readiness check endpoint.
    
    Returns whether the server is ready to accept requests.
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Check if server is initialized and ready
        ready = (
            mcp_server is not None and
            mcp_server.is_initialized and
            not mcp_server.is_shutting_down
        )
        
        return HealthStatus(
            healthy=ready,
            timestamp=timestamp,
            version="1.0.0",
            error=None if ready else "Server not ready"
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return HealthStatus(
            healthy=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            error=str(e)
        )


@health_router.get(
    "/liveness",
    response_model=HealthStatus,
    summary="Liveness check"
)
async def liveness_check():
    """
    Liveness check endpoint.
    
    Returns whether the server process is alive and responsive.
    """
    try:
        return HealthStatus(
            healthy=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return HealthStatus(
            healthy=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            error=str(e)
        )


@health_router.get(
    "/components/{component_name}",
    response_model=ComponentHealth,
    summary="Component health check"
)
async def component_health_check(
    component_name: str,
    mcp_server = Depends(get_mcp_server)
):
    """
    Check health of a specific component.
    
    Args:
        component_name: Name of the component to check
        
    Returns:
        Health status of the specified component
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if not mcp_server or not mcp_server.is_initialized:
            return ComponentHealth(
                healthy=False,
                timestamp=timestamp,
                error="Server not initialized"
            )
        
        # Get all component health status
        health_status = await mcp_server.get_health_status()
        
        # Check if requested component exists
        if component_name not in health_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component '{component_name}' not found"
            )
        
        component_status = health_status[component_name]
        
        return ComponentHealth(
            healthy=component_status.get("healthy", False),
            timestamp=component_status.get("timestamp", timestamp),
            error=component_status.get("error"),
            details=component_status.get("details")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Component health check failed for {component_name}: {e}")
        return ComponentHealth(
            healthy=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=str(e)
        )
"""
Health Check API Router

This module provides health check endpoints for monitoring the
MCP Meta-Server status and component health.
"""

import time
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create router
health_router = APIRouter()

# Server start time for uptime calculation
_server_start_time = time.time()


# =============================================================================
# Pydantic Models
# =============================================================================

class HealthStatus(BaseModel):
    """Health status response model."""
    healthy: bool
    timestamp: str
    version: str
    uptime: float | None = None
    error: str | None = None


class ComponentHealth(BaseModel):
    """Component health status model."""
    name: str
    status: str
    response_time: float | None = None
    error: str | None = None


class DetailedHealthStatus(BaseModel):
    """Detailed health status response model."""
    overall_healthy: bool
    timestamp: str
    version: str
    uptime: float
    components: list[ComponentHealth]


# =============================================================================
# Health Check Functions
# =============================================================================

def get_uptime() -> float:
    """Calculate server uptime in seconds."""
    return time.time() - _server_start_time


def format_uptime(seconds: float) -> str:
    """Format uptime in human readable format."""
    if seconds < 0:
        return f"{int(seconds)}s"

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


async def check_database_health() -> ComponentHealth:
    """Check database connectivity."""
    start_time = time.time()

    try:
        # TODO: Implement actual database health check
        # For now, return mock healthy status
        response_time = time.time() - start_time

        return ComponentHealth(
            name="database",
            status="healthy",
            response_time=response_time
        )
    except Exception as e:
        return ComponentHealth(
            name="database",
            status="unhealthy",
            response_time=time.time() - start_time,
            error=str(e)
        )


async def check_vector_db_health() -> ComponentHealth:
    """Check vector database connectivity."""
    start_time = time.time()

    try:
        # TODO: Implement actual vector database health check
        # For now, return mock healthy status
        response_time = time.time() - start_time

        return ComponentHealth(
            name="vector_database",
            status="healthy",
            response_time=response_time
        )
    except Exception as e:
        return ComponentHealth(
            name="vector_database",
            status="unhealthy",
            response_time=time.time() - start_time,
            error=str(e)
        )


async def check_llm_service_health() -> ComponentHealth:
    """Check LLM service connectivity."""
    start_time = time.time()

    try:
        # TODO: Implement actual LLM service health check
        # For now, return mock healthy status
        response_time = time.time() - start_time

        return ComponentHealth(
            name="llm_service",
            status="healthy",
            response_time=response_time
        )
    except Exception as e:
        return ComponentHealth(
            name="llm_service",
            status="unhealthy",
            response_time=time.time() - start_time,
            error=str(e)
        )


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
    "/",
    response_model=HealthStatus,
    summary="Basic health check"
)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns basic health status of the server.
    """
    try:
        uptime_seconds = get_uptime()

        return HealthStatus(
            healthy=True,
            timestamp=datetime.now(UTC).isoformat(),
            version="1.0.0",
            uptime=uptime_seconds
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthStatus(
            healthy=False,
            timestamp=datetime.now(UTC).isoformat(),
            version="1.0.0",
            error=str(e)
        )


@health_router.get(
    "/detailed",
    response_model=DetailedHealthStatus,
    summary="Detailed health check"
)
async def detailed_health_check():
    """
    Detailed health check endpoint.
    
    Returns detailed health status of all components.
    """
    try:
        # Check all components
        components = []

        # Database health
        db_health = await check_database_health()
        components.append(db_health)

        # Vector database health
        vector_health = await check_vector_db_health()
        components.append(vector_health)

        # LLM service health
        llm_health = await check_llm_service_health()
        components.append(llm_health)

        # Determine overall health
        overall_healthy = all(comp.status == "healthy" for comp in components)
        uptime_seconds = get_uptime()

        return DetailedHealthStatus(
            overall_healthy=overall_healthy,
            timestamp=datetime.now(UTC).isoformat(),
            version="1.0.0",
            uptime=uptime_seconds,
            components=components
        )

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@health_router.get(
    "/ready",
    summary="Readiness probe"
)
async def readiness_probe():
    """
    Readiness probe endpoint.
    
    Returns 200 if the service is ready to accept requests.
    """
    try:
        # Check if all critical components are ready
        db_health = await check_database_health()
        vector_health = await check_vector_db_health()

        if db_health.status != "healthy" or vector_health.status != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )

        return {"status": "ready"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@health_router.get(
    "/live",
    summary="Liveness probe"
)
async def liveness_probe():
    """
    Liveness probe endpoint.
    
    Returns 200 if the service is alive and responsive.
    """
    try:
        # Simple liveness check - just verify the service is responding
        uptime_seconds = get_uptime()

        return {
            "status": "alive",
            "uptime": uptime_seconds,
            "uptime_formatted": format_uptime(uptime_seconds)
        }

    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not alive: {str(e)}"
        )


@health_router.get(
    "/info",
    summary="Service information"
)
async def service_info():
    """
    Get service information.
    
    Returns detailed information about the service.
    """
    try:
        uptime_seconds = get_uptime()

        return {
            "service": "MetaMCP",
            "version": "1.0.0",
            "uptime": uptime_seconds,
            "uptime_formatted": format_uptime(uptime_seconds),
            "start_time": datetime.fromtimestamp(_server_start_time, UTC).isoformat(),
            "current_time": datetime.now(UTC).isoformat(),
            "environment": settings.environment,
            "debug": settings.debug
        }

    except Exception as e:
        logger.error(f"Service info failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service info: {str(e)}"
        )

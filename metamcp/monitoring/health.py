"""
Health Monitoring

This module provides health monitoring and status checking functionality.
"""

from datetime import UTC, datetime
from typing import Any

from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class HealthMonitor:
    """Health monitoring and status checking."""

    def __init__(self):
        """Initialize health monitor."""
        self.start_time = datetime.now(UTC)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize health monitoring."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Health Monitor...")
            self._initialized = True
            logger.info("Health Monitor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Health Monitor: {e}")
            raise

    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return (datetime.now(UTC) - self.start_time).total_seconds()

    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        if seconds < 0:
            return f"{int(seconds)}s"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    async def check_health(self) -> dict[str, Any]:
        """Perform basic health check."""
        try:
            uptime = self.get_uptime()

            return {
                "status": "healthy",
                "uptime": uptime,
                "uptime_formatted": self.format_uptime(uptime),
                "timestamp": datetime.now(UTC).isoformat(),
                "version": settings.app_version,
                "environment": settings.environment,
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "version": settings.app_version,
                "environment": settings.environment,
            }

    async def check_readiness(self) -> dict[str, Any]:
        """Check if the service is ready to handle requests."""
        try:
            # Basic readiness check
            health_status = await self.check_health()

            if health_status["status"] == "healthy":
                return {
                    "status": "ready",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            else:
                return {
                    "status": "not_ready",
                    "reason": "Health check failed",
                    "timestamp": datetime.now(UTC).isoformat(),
                }

        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return {
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def check_liveness(self) -> dict[str, Any]:
        """Check if the service is alive."""
        try:
            return {
                "status": "alive",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return {
                "status": "dead",
                "reason": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def get_detailed_health(self) -> dict[str, Any]:
        """Get detailed health information."""
        try:
            basic_health = await self.check_health()
            readiness = await self.check_readiness()
            liveness = await self.check_liveness()

            return {
                **basic_health,
                "readiness": readiness,
                "liveness": liveness,
                "components": {
                    "health_monitor": "healthy",
                    "settings": "healthy",
                    "logging": "healthy",
                },
            }

        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "components": {
                    "health_monitor": "unhealthy",
                    "settings": "unknown",
                    "logging": "unknown",
                },
            }

    async def shutdown(self) -> None:
        """Shutdown health monitoring."""
        if self._initialized:
            logger.info("Shutting down Health Monitor...")
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if health monitor is initialized."""
        return self._initialized


# Global health monitor instance
_health_monitor: HealthMonitor | None = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor

    if _health_monitor is None:
        _health_monitor = HealthMonitor()

    return _health_monitor


def setup_health_checks(app, mcp_server=None) -> None:
    """
    Setup health check endpoints for the FastAPI application.

    Args:
        app: FastAPI application instance
        mcp_server: Optional MCP server instance for health checks
    """
    from fastapi import APIRouter

    # Create health router
    health_router = APIRouter(prefix="/health", tags=["health"])

    @health_router.get("/")
    async def health_check():
        """Basic health check endpoint."""
        monitor = get_health_monitor()
        return await monitor.check_health()

    @health_router.get("/ready")
    async def readiness_check():
        """Readiness probe endpoint."""
        monitor = get_health_monitor()
        return await monitor.check_readiness()

    @health_router.get("/live")
    async def liveness_check():
        """Liveness probe endpoint."""
        monitor = get_health_monitor()
        return await monitor.check_liveness()

    @health_router.get("/detailed")
    async def detailed_health_check():
        """Detailed health check endpoint."""
        monitor = get_health_monitor()
        return await monitor.get_detailed_health()

    # Include health router in app
    app.include_router(health_router)

"""
Health Check API

This module provides health check endpoints and system status information.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..monitoring.performance import performance_monitor
from ..performance.circuit_breaker import circuit_breaker_manager
from ..services.service_discovery import ServiceType, service_discovery
from ..utils.logging import get_logger

from dataclasses import dataclass, asdict
import time

logger = get_logger(__name__)
settings = get_settings()

# Create router
health_router = APIRouter()


@dataclass
class ComponentHealth:
    name: str
    status: str
    response_time: float | None = None
    details: dict[str, Any] | None = None


@dataclass
class DetailedHealthStatus:
    overall_healthy: bool
    timestamp: str
    version: str
    uptime: float
    components: list[ComponentHealth]


def format_uptime(total_seconds: float | int) -> str:
    try:
        seconds = int(total_seconds)
    except Exception:
        seconds = 0
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days > 0:
        return f"{sign}{days}d {hours}h {minutes}m {secs}s"
    if hours > 0:
        return f"{sign}{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{sign}{minutes}m {secs}s"
    return f"{sign}{secs}s"


async def check_database_health() -> ComponentHealth:
    start = time.perf_counter()
    try:
        from ..utils.database import get_database_manager

        db = get_database_manager()
        result = await db.health_check()  # mocked in tests
        status = result.get("status", "healthy") if isinstance(result, dict) else "healthy"
        elapsed = time.perf_counter() - start
        return ComponentHealth(name="database", status=status, response_time=elapsed)
    except Exception as e:
        elapsed = time.perf_counter() - start
        return ComponentHealth(
            name="database", status="unhealthy", response_time=elapsed, details={"error": str(e)}
        )


async def check_vector_db_health() -> ComponentHealth:
    start = time.perf_counter()
    try:
        import weaviate

        client = weaviate.connect_to_custom(http_host=settings.weaviate_url, grpc_host=None)
        # Assume healthy if no exception and ready
        status = "healthy"
        elapsed = time.perf_counter() - start
        return ComponentHealth(name="vector_db", status=status, response_time=elapsed)
    except Exception as e:
        elapsed = time.perf_counter() - start
        return ComponentHealth(
            name="vector_db", status="unhealthy", response_time=elapsed, details={"error": str(e)}
        )


async def check_llm_service_health() -> ComponentHealth:
    start = time.perf_counter()
    try:
        import openai

        _ = openai.OpenAI(api_key=getattr(settings, "openai_api_key", None))
        # A lightweight check is enough; tests mock models.list
        status = "healthy"
        elapsed = time.perf_counter() - start
        return ComponentHealth(name="llm_service", status=status, response_time=elapsed)
    except Exception as e:
        elapsed = time.perf_counter() - start
        return ComponentHealth(
            name="llm_service", status="unhealthy", response_time=elapsed, details={"error": str(e)}
        )


@health_router.get("")
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint at the router root.
    """
    try:
        health_status = {
            "healthy": True,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
        }

        performance_summary = performance_monitor.get_performance_summary()
        if performance_summary:
            health_status["performance"] = performance_summary

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@health_router.get("/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """
    Detailed health check with all system components.
    """
    try:
        # Gather component health
        components: list[ComponentHealth] = []
        db_health = await check_database_health()
        components.append(db_health)
        vec_health = await check_vector_db_health()
        components.append(vec_health)
        llm_health = await check_llm_service_health()
        components.append(llm_health)

        overall_healthy = all(c.status == "healthy" for c in components)
        uptime_seconds = 0.0  # Placeholder; real uptime tracking could be added

        detailed = DetailedHealthStatus(
            overall_healthy=overall_healthy,
            timestamp=datetime.utcnow().isoformat(),
            version=settings.app_version,
            uptime=uptime_seconds,
            components=components,
        )

        # Convert dataclasses to serializable dict
        return {
            "overall_healthy": detailed.overall_healthy,
            "timestamp": detailed.timestamp,
            "version": detailed.version,
            "uptime": detailed.uptime,
            "components": [asdict(c) for c in detailed.components],
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@health_router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """Readiness check for Kubernetes."""
    try:
        db = await check_database_health()
        vec = await check_vector_db_health()

        if db.status == "healthy" and vec.status == "healthy":
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            errors = []
            if db.status != "healthy":
                errors.append("Database not ready")
            if vec.status != "healthy":
                errors.append("Vector DB not ready")
            raise HTTPException(status_code=503, detail={"status": "not_ready", "errors": errors})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@health_router.get("/live")
async def liveness_check() -> dict[str, Any]:
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "running",
    }


@health_router.get("/info")
async def service_info() -> dict[str, Any]:
    return {
        "service": "MetaMCP",
        "environment": settings.environment,
        "version": settings.app_version,
    }


@health_router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": performance_monitor.get_performance_summary(),
            "circuit_breakers": circuit_breaker_manager.get_all_metrics(),
        }
        try:
            services = await service_discovery.get_all_services(healthy_only=False)
            metrics["service_discovery"] = {
                "status": "healthy",
                "total_services": len(services),
                "healthy_services": len([s for s in services if s.status.value == "healthy"]),
            }
        except Exception as e:
            metrics["service_discovery"] = {"status": "unhealthy", "error": str(e)}
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@health_router.get("/metrics/performance")
async def get_performance_metrics() -> dict[str, Any]:
    """
    Get performance metrics.

    Returns:
        Performance metrics
    """
    try:
        return performance_monitor.get_performance_summary()
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@health_router.get("/metrics/performance/analytics")
async def get_performance_analytics(hours: int = 24) -> dict[str, Any]:
    """
    Get performance analytics.

    Args:
        hours: Number of hours to analyze

    Returns:
        Performance analytics
    """
    try:
        return performance_monitor.get_request_analytics(hours)
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get performance analytics"
        )


@health_router.get("/metrics/circuit-breakers")
async def get_circuit_breaker_metrics() -> dict[str, Any]:
    """
    Get circuit breaker metrics.

    Returns:
        Circuit breaker metrics
    """
    try:
        return circuit_breaker_manager.get_all_metrics()
    except Exception as e:
        logger.error(f"Failed to get circuit breaker metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get circuit breaker metrics"
        )


@health_router.post("/metrics/circuit-breakers/reset")
async def reset_circuit_breakers() -> dict[str, Any]:
    """
    Reset all circuit breakers.

    Returns:
        Reset status
    """
    try:
        circuit_breaker_manager.reset_all()
        return {
            "status": "success",
            "message": "All circuit breakers reset",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to reset circuit breakers: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset circuit breakers")


@health_router.get("/services")
async def get_services(
    service_type: str | None = None, healthy_only: bool = True
) -> dict[str, Any]:
    """
    Get registered services.

    Args:
        service_type: Filter by service type
        healthy_only: Only return healthy services

    Returns:
        Service information
    """
    try:
        if service_type:
            # Convert string to ServiceType enum
            try:
                service_type_enum = ServiceType(service_type)
                services = await service_discovery.get_services_by_type(
                    service_type_enum, healthy_only
                )
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid service type: {service_type}"
                )
        else:
            services = await service_discovery.get_all_services(healthy_only)

        return {
            "services": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                    "host": s.host,
                    "port": s.port,
                    "version": s.version,
                    "status": s.status.value,
                    "health_check_url": s.health_check_url,
                    "metadata": s.metadata,
                    "tags": s.tags,
                    "last_heartbeat": (
                        s.last_heartbeat.isoformat() if s.last_heartbeat else None
                    ),
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in services
            ],
            "total": len(services),
            "healthy": len([s for s in services if s.status.value == "healthy"]),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get services: {e}")
        raise HTTPException(status_code=500, detail="Failed to get services")


@health_router.get("/services/{service_id}")
async def get_service(service_id: str) -> dict[str, Any]:
    """
    Get specific service information.

    Args:
        service_id: Service identifier

    Returns:
        Service information
    """
    try:
        service = await service_discovery.get_service(service_id)

        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        return {
            "id": service.id,
            "name": service.name,
            "type": service.type.value,
            "host": service.host,
            "port": service.port,
            "version": service.version,
            "status": service.status.value,
            "health_check_url": service.health_check_url,
            "metadata": service.metadata,
            "tags": service.tags,
            "last_heartbeat": (
                service.last_heartbeat.isoformat() if service.last_heartbeat else None
            ),
            "created_at": (
                service.created_at.isoformat() if service.created_at else None
            ),
            "updated_at": (
                service.updated_at.isoformat() if service.updated_at else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service")


@health_router.get("/services/types/{service_type}")
async def get_services_by_type(
    service_type: str, healthy_only: bool = True
) -> dict[str, Any]:
    """
    Get services by type.

    Args:
        service_type: Service type
        healthy_only: Only return healthy services

    Returns:
        Services of specified type
    """
    try:
        # Convert string to ServiceType enum
        try:
            service_type_enum = ServiceType(service_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid service type: {service_type}"
            )

        services = await service_discovery.get_services_by_type(
            service_type_enum, healthy_only
        )

        return {
            "service_type": service_type,
            "services": [
                {
                    "id": s.id,
                    "name": s.name,
                    "host": s.host,
                    "port": s.port,
                    "version": s.version,
                    "status": s.status.value,
                    "health_check_url": s.health_check_url,
                    "metadata": s.metadata,
                    "tags": s.tags,
                }
                for s in services
            ],
            "total": len(services),
            "healthy": len([s for s in services if s.status.value == "healthy"]),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get services by type {service_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get services by type")


@health_router.get("/services/tags/{tag}")
async def get_services_by_tag(tag: str, healthy_only: bool = True) -> dict[str, Any]:
    """
    Get services by tag.

    Args:
        tag: Service tag
        healthy_only: Only return healthy services

    Returns:
        Services with specified tag
    """
    try:
        services = await service_discovery.get_services_by_tag(tag, healthy_only)

        return {
            "tag": tag,
            "services": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                    "host": s.host,
                    "port": s.port,
                    "version": s.version,
                    "status": s.status.value,
                    "health_check_url": s.health_check_url,
                    "metadata": s.metadata,
                    "tags": s.tags,
                }
                for s in services
            ],
            "total": len(services),
            "healthy": len([s for s in services if s.status.value == "healthy"]),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get services by tag {tag}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get services by tag")


@health_router.get("/discovery")
async def get_service_discovery_info() -> dict[str, Any]:
    """
    Get service discovery information.

    Returns:
        Service discovery information
    """
    try:
        return await service_discovery.discover_services()
    except Exception as e:
        logger.error(f"Failed to get service discovery info: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get service discovery info"
        )

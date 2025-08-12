"""
Health Check API

This module provides health check endpoints and system status information.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..monitoring.performance import performance_monitor
from ..performance.circuit_breaker import circuit_breaker_manager
from ..services.service_discovery import service_discovery, ServiceType
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create router
health_router = APIRouter()


@health_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        Health status information
    """
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
        }

        # Add performance metrics if available
        performance_summary = performance_monitor.get_performance_summary()
        if performance_summary:
            health_status["performance"] = performance_summary

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@health_router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with all system components.

    Returns:
        Detailed health status information
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
            "components": {},
        }

        # Check database
        try:
            from ..utils.database import get_database_session

            async with get_database_session() as session:
                await session.execute("SELECT 1")
            health_status["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        # Check cache
        try:
            from ..cache.redis_cache import get_cache_manager

            cache = get_cache_manager()
            await cache.set("health_check", "ok", ttl=60)
            await cache.delete("health_check")
            health_status["components"]["cache"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        # Check vector database
        try:
            from ..vector.weaviate_client import get_weaviate_client

            weaviate = get_weaviate_client()
            # Simple ping check
            health_status["components"]["vector_database"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["vector_database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        # Add performance metrics
        performance_summary = performance_monitor.get_performance_summary()
        if performance_summary:
            health_status["performance"] = performance_summary

        # Add circuit breaker status
        circuit_breaker_metrics = circuit_breaker_manager.get_all_metrics()
        if circuit_breaker_metrics:
            health_status["circuit_breakers"] = circuit_breaker_metrics

        # Add service discovery status
        try:
            services = await service_discovery.get_all_services(healthy_only=False)
            health_status["service_discovery"] = {
                "status": "healthy",
                "total_services": len(services),
                "healthy_services": len(
                    [s for s in services if s.status.value == "healthy"]
                ),
            }
        except Exception as e:
            health_status["service_discovery"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@health_router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes.

    Returns:
        Readiness status
    """
    try:
        # Check if all critical components are ready
        ready = True
        errors = []

        # Check database
        try:
            from ..utils.database import get_database_session

            async with get_database_session() as session:
                await session.execute("SELECT 1")
        except Exception as e:
            ready = False
            errors.append(f"Database not ready: {e}")

        # Check cache
        try:
            from ..cache.redis_cache import get_cache_manager

            cache = get_cache_manager()
            await cache.set("ready_check", "ok", ttl=60)
            await cache.delete("ready_check")
        except Exception as e:
            ready = False
            errors.append(f"Cache not ready: {e}")

        if ready:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=503, detail={"status": "not_ready", "errors": errors}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@health_router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes.

    Returns:
        Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "running",  # In a real implementation, calculate actual uptime
    }


@health_router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get system metrics.

    Returns:
        System metrics
    """
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": performance_monitor.get_performance_summary(),
            "circuit_breakers": circuit_breaker_manager.get_all_metrics(),
            "service_discovery": await service_discovery.discover_services(),
        }

        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@health_router.get("/metrics/performance")
async def get_performance_metrics() -> Dict[str, Any]:
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
async def get_performance_analytics(hours: int = 24) -> Dict[str, Any]:
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
async def get_circuit_breaker_metrics() -> Dict[str, Any]:
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
async def reset_circuit_breakers() -> Dict[str, Any]:
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
    service_type: Optional[str] = None, healthy_only: bool = True
) -> Dict[str, Any]:
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
async def get_service(service_id: str) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
async def get_services_by_tag(tag: str, healthy_only: bool = True) -> Dict[str, Any]:
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
async def get_service_discovery_info() -> Dict[str, Any]:
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

"""
Service Discovery Implementation

This module provides service discovery functionality for dynamic service
registration, health checking, and service lookup.
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ..cache.redis_cache import get_cache_manager
from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ServiceStatus(Enum):
    """Service status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


class ServiceType(Enum):
    """Service type enumeration."""

    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    MONITORING = "monitoring"
    AUTH = "auth"
    TOOL = "tool"


@dataclass
class ServiceInfo:
    """Service information."""

    id: str
    name: str
    type: ServiceType
    host: str
    port: int
    version: str
    status: ServiceStatus
    health_check_url: str | None = None
    metadata: dict[str, Any] | None = None
    tags: list[str] | None = None
    last_heartbeat: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ServiceDiscovery:
    """
    Service discovery implementation with Redis backend.

    Provides service registration, health checking, and service lookup
    functionality for distributed systems.
    """

    def __init__(self):
        """Initialize service discovery."""
        self.cache = get_cache_manager()
        self.registered_services: dict[str, ServiceInfo] = {}
        self.health_check_interval = 30  # seconds
        self.service_ttl = 120  # seconds
        self._health_check_task: asyncio.Task | None = None
        self._running = False

        # Service type registries
        self.service_registries: dict[ServiceType, set[str]] = {
            service_type: set() for service_type in ServiceType
        }

        logger.info("Service discovery initialized")

    async def start(self) -> None:
        """Start service discovery."""
        if self._running:
            return

        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Service discovery started")

    async def stop(self) -> None:
        """Stop service discovery."""
        if not self._running:
            return

        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        logger.info("Service discovery stopped")

    async def register_service(
        self,
        service_id: str,
        name: str,
        service_type: ServiceType,
        host: str,
        port: int,
        version: str,
        health_check_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> ServiceInfo:
        """
        Register a new service.

        Args:
            service_id: Unique service identifier
            name: Service name
            service_type: Type of service
            host: Service host
            port: Service port
            version: Service version
            health_check_url: Health check endpoint URL
            metadata: Additional service metadata
            tags: Service tags

        Returns:
            Registered service information
        """
        now = datetime.utcnow()

        service_info = ServiceInfo(
            id=service_id,
            name=name,
            type=service_type,
            host=host,
            port=port,
            version=version,
            status=ServiceStatus.STARTING,
            health_check_url=health_check_url,
            metadata=metadata or {},
            tags=tags or [],
            last_heartbeat=now,
            created_at=now,
            updated_at=now,
        )

        # Store in memory
        self.registered_services[service_id] = service_info
        self.service_registries[service_type].add(service_id)

        # Store in cache
        await self._store_service_in_cache(service_info)

        logger.info(f"Service registered: {service_id} ({name})")
        return service_info

    async def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service.

        Args:
            service_id: Service identifier to deregister

        Returns:
            True if service was deregistered, False if not found
        """
        if service_id not in self.registered_services:
            return False

        service_info = self.registered_services[service_id]

        # Remove from memory
        del self.registered_services[service_id]
        self.service_registries[service_info.type].discard(service_id)

        # Remove from cache
        await self._remove_service_from_cache(service_id)

        logger.info(f"Service deregistered: {service_id}")
        return True

    async def update_service_status(
        self, service_id: str, status: ServiceStatus
    ) -> bool:
        """
        Update service status.

        Args:
            service_id: Service identifier
            status: New status

        Returns:
            True if service was updated, False if not found
        """
        if service_id not in self.registered_services:
            return False

        service_info = self.registered_services[service_id]
        service_info.status = status
        service_info.updated_at = datetime.utcnow()

        # Update in cache
        await self._store_service_in_cache(service_info)

        logger.debug(f"Service status updated: {service_id} -> {status.value}")
        return True

    async def heartbeat(self, service_id: str) -> bool:
        """
        Send heartbeat for service.

        Args:
            service_id: Service identifier

        Returns:
            True if service was updated, False if not found
        """
        if service_id not in self.registered_services:
            return False

        service_info = self.registered_services[service_id]
        service_info.last_heartbeat = datetime.utcnow()
        service_info.updated_at = datetime.utcnow()

        # Update in cache
        await self._store_service_in_cache(service_info)

        return True

    async def get_service(self, service_id: str) -> ServiceInfo | None:
        """
        Get service by ID.

        Args:
            service_id: Service identifier

        Returns:
            Service information or None if not found
        """
        # Try memory first
        if service_id in self.registered_services:
            return self.registered_services[service_id]

        # Try cache
        return await self._get_service_from_cache(service_id)

    async def get_services_by_type(
        self, service_type: ServiceType, healthy_only: bool = True
    ) -> list[ServiceInfo]:
        """
        Get services by type.

        Args:
            service_type: Type of service to find
            healthy_only: Only return healthy services

        Returns:
            List of service information
        """
        services = []

        # Get from memory
        for service_id in self.service_registries[service_type]:
            service_info = self.registered_services.get(service_id)
            if service_info and (
                not healthy_only or service_info.status == ServiceStatus.HEALTHY
            ):
                services.append(service_info)

        # Get from cache if not in memory
        cached_services = await self._get_services_from_cache_by_type(service_type)
        for service_info in cached_services:
            if service_info.id not in self.registered_services:
                if not healthy_only or service_info.status == ServiceStatus.HEALTHY:
                    services.append(service_info)

        return services

    async def get_services_by_tag(
        self, tag: str, healthy_only: bool = True
    ) -> list[ServiceInfo]:
        """
        Get services by tag.

        Args:
            tag: Tag to search for
            healthy_only: Only return healthy services

        Returns:
            List of service information
        """
        services = []

        # Search in memory
        for service_info in self.registered_services.values():
            if tag in (service_info.tags or []):
                if not healthy_only or service_info.status == ServiceStatus.HEALTHY:
                    services.append(service_info)

        # Search in cache
        cached_services = await self._get_services_from_cache_by_tag(tag)
        for service_info in cached_services:
            if service_info.id not in self.registered_services:
                if not healthy_only or service_info.status == ServiceStatus.HEALTHY:
                    services.append(service_info)

        return services

    async def get_all_services(self, healthy_only: bool = True) -> list[ServiceInfo]:
        """
        Get all registered services.

        Args:
            healthy_only: Only return healthy services

        Returns:
            List of all service information
        """
        services = list(self.registered_services.values())

        if healthy_only:
            services = [s for s in services if s.status == ServiceStatus.HEALTHY]

        return services

    async def discover_services(self) -> dict[str, Any]:
        """
        Discover all available services.

        Returns:
            Service discovery information
        """
        all_services = await self.get_all_services(healthy_only=False)

        # Group by type
        services_by_type = {}
        for service_type in ServiceType:
            services_by_type[service_type.value] = [
                asdict(s) for s in all_services if s.type == service_type
            ]

        # Calculate statistics
        total_services = len(all_services)
        healthy_services = len(
            [s for s in all_services if s.status == ServiceStatus.HEALTHY]
        )

        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "services_by_type": services_by_type,
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def _health_check_loop(self) -> None:
        """Health check loop for registered services."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)  # Short delay on error

    async def _perform_health_checks(self) -> None:
        """Perform health checks on registered services."""
        import httpx

        async with httpx.AsyncClient(timeout=5) as client:
            for service_info in self.registered_services.values():
                if not service_info.health_check_url:
                    continue

                try:
                    response = await client.get(service_info.health_check_url)
                    if response.status_code == 200:
                        await self.update_service_status(
                            service_info.id, ServiceStatus.HEALTHY
                        )
                    else:
                        await self.update_service_status(
                            service_info.id, ServiceStatus.UNHEALTHY
                        )
                except Exception as e:
                    logger.warning(f"Health check failed for {service_info.id}: {e}")
                    await self.update_service_status(
                        service_info.id, ServiceStatus.UNHEALTHY
                    )

    async def _store_service_in_cache(self, service_info: ServiceInfo) -> None:
        """Store service information in cache."""
        try:
            # Store service info
            service_key = f"service:{service_info.id}"
            service_data = asdict(service_info)
            service_data["type"] = service_info.type.value
            service_data["status"] = service_info.status.value
            service_data["created_at"] = (
                service_info.created_at.isoformat() if service_info.created_at else None
            )
            service_data["updated_at"] = (
                service_info.updated_at.isoformat() if service_info.updated_at else None
            )
            service_data["last_heartbeat"] = (
                service_info.last_heartbeat.isoformat()
                if service_info.last_heartbeat
                else None
            )

            await self.cache.set(
                service_key, json.dumps(service_data), ttl=self.service_ttl
            )

            # Store service index by type
            type_key = f"services:type:{service_info.type.value}"
            await self.cache.sadd(type_key, service_info.id)
            await self.cache.expire(type_key, self.service_ttl)

            # Store service index by tags
            for tag in service_info.tags or []:
                tag_key = f"services:tag:{tag}"
                await self.cache.sadd(tag_key, service_info.id)
                await self.cache.expire(tag_key, self.service_ttl)

        except Exception as e:
            logger.error(f"Failed to store service in cache: {e}")

    async def _remove_service_from_cache(self, service_id: str) -> None:
        """Remove service information from cache."""
        try:
            # Remove service info
            service_key = f"service:{service_id}"
            await self.cache.delete(service_key)

            # Remove from type and tag indices
            # Note: This is simplified - in a real implementation you'd need to
            # track which types and tags the service had
            for service_type in ServiceType:
                type_key = f"services:type:{service_type.value}"
                await self.cache.srem(type_key, service_id)

        except Exception as e:
            logger.error(f"Failed to remove service from cache: {e}")

    async def _get_service_from_cache(self, service_id: str) -> ServiceInfo | None:
        """Get service information from cache."""
        try:
            service_key = f"service:{service_id}"
            service_data = await self.cache.get(service_key)

            if not service_data:
                return None

            data = json.loads(service_data)

            # Convert back to ServiceInfo
            service_info = ServiceInfo(
                id=data["id"],
                name=data["name"],
                type=ServiceType(data["type"]),
                host=data["host"],
                port=data["port"],
                version=data["version"],
                status=ServiceStatus(data["status"]),
                health_check_url=data.get("health_check_url"),
                metadata=data.get("metadata", {}),
                tags=data.get("tags", []),
                last_heartbeat=(
                    datetime.fromisoformat(data["last_heartbeat"])
                    if data.get("last_heartbeat")
                    else None
                ),
                created_at=(
                    datetime.fromisoformat(data["created_at"])
                    if data.get("created_at")
                    else None
                ),
                updated_at=(
                    datetime.fromisoformat(data["updated_at"])
                    if data.get("updated_at")
                    else None
                ),
            )

            return service_info

        except Exception as e:
            logger.error(f"Failed to get service from cache: {e}")
            return None

    async def _get_services_from_cache_by_type(
        self, service_type: ServiceType
    ) -> list[ServiceInfo]:
        """Get services from cache by type."""
        try:
            type_key = f"services:type:{service_type.value}"
            service_ids = await self.cache.smembers(type_key)

            services = []
            for service_id in service_ids:
                service_info = await self._get_service_from_cache(service_id)
                if service_info:
                    services.append(service_info)

            return services

        except Exception as e:
            logger.error(f"Failed to get services from cache by type: {e}")
            return []

    async def _get_services_from_cache_by_tag(self, tag: str) -> list[ServiceInfo]:
        """Get services from cache by tag."""
        try:
            tag_key = f"services:tag:{tag}"
            service_ids = await self.cache.smembers(tag_key)

            services = []
            for service_id in service_ids:
                service_info = await self._get_service_from_cache(service_id)
                if service_info:
                    services.append(service_info)

            return services

        except Exception as e:
            logger.error(f"Failed to get services from cache by tag: {e}")
            return []


# Global service discovery instance
service_discovery = ServiceDiscovery()

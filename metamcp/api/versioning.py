"""
API Versioning System

This module provides API versioning capabilities with proper routing,
version management, and deprecation handling.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.routing import APIRoute

from ..utils.logging import get_logger

logger = get_logger(__name__)


class VersionStatus(Enum):
    """API version status."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


@dataclass
class APIVersion:
    """API version information."""

    version: str
    status: VersionStatus
    release_date: datetime
    deprecation_date: datetime | None = None
    sunset_date: datetime | None = None
    description: str = ""
    breaking_changes: list[str] = None
    new_features: list[str] = None
    bug_fixes: list[str] = None

    def __post_init__(self):
        if self.breaking_changes is None:
            self.breaking_changes = []
        if self.new_features is None:
            self.new_features = []
        if self.bug_fixes is None:
            self.bug_fixes = []

    def is_deprecated(self) -> bool:
        """Check if version is deprecated."""
        if self.status == VersionStatus.DEPRECATED:
            return True
        if self.deprecation_date and datetime.utcnow() >= self.deprecation_date:
            return True
        return False

    def is_sunset(self) -> bool:
        """Check if version is sunset."""
        if self.status == VersionStatus.SUNSET:
            return True
        if self.sunset_date and datetime.utcnow() >= self.sunset_date:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "status": self.status.value,
            "release_date": self.release_date.isoformat(),
            "deprecation_date": (
                self.deprecation_date.isoformat() if self.deprecation_date else None
            ),
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "description": self.description,
            "breaking_changes": self.breaking_changes,
            "new_features": self.new_features,
            "bug_fixes": self.bug_fixes,
            "is_deprecated": self.is_deprecated(),
            "is_sunset": self.is_sunset(),
        }


class VersionedAPIRoute(APIRoute):
    """Versioned API route with version information."""

    def __init__(self, *args, version: str = "v1", **kwargs):
        super().__init__(*args, **kwargs)
        self.version = version


class APIVersionManager:
    """
    API Version Manager.

    Manages API versions, routing, and deprecation.
    """

    def __init__(self):
        """Initialize API Version Manager."""
        self.versions: dict[str, APIVersion] = {}
        self.routers: dict[str, APIRouter] = {}
        self.default_version = "v1"
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the API Version Manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing API Version Manager...")

            # Initialize default versions
            await self._initialize_default_versions()

            self._initialized = True
            logger.info("API Version Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API Version Manager: {e}")
            raise

    def register_version(self, version: APIVersion) -> None:
        """Register a new API version."""
        self.versions[version.version] = version
        logger.info(f"Registered API version: {version.version}")

    def get_router(self, version: str) -> APIRouter | None:
        """Get router for a specific version."""
        return self.routers.get(version)

    def get_latest_version(self) -> str | None:
        """Get the latest API version."""
        if not self.versions:
            return None

        # Sort by release date and return the latest
        sorted_versions = sorted(
            self.versions.values(), key=lambda v: v.release_date, reverse=True
        )

        # Return the latest active version
        for version in sorted_versions:
            if not version.is_sunset():
                return version.version

        return None

    def get_active_versions(self) -> list[str]:
        """Get list of active API versions."""
        active_versions = []
        for version in self.versions.values():
            if not version.is_deprecated() and not version.is_sunset():
                active_versions.append(version.version)
        return sorted(active_versions)

    def get_deprecated_versions(self) -> list[str]:
        """Get list of deprecated API versions."""
        deprecated_versions = []
        for version in self.versions.values():
            if version.is_deprecated() and not version.is_sunset():
                deprecated_versions.append(version.version)
        return sorted(deprecated_versions)

    def get_sunset_versions(self) -> list[str]:
        """Get list of sunset API versions."""
        sunset_versions = []
        for version in self.versions.values():
            if version.is_sunset():
                sunset_versions.append(version.version)
        return sorted(sunset_versions)

    def deprecate_version(
        self, version: str, deprecation_date: datetime | None = None
    ) -> bool:
        """Deprecate an API version."""
        if version not in self.versions:
            return False

        api_version = self.versions[version]
        api_version.status = VersionStatus.DEPRECATED
        if deprecation_date:
            api_version.deprecation_date = deprecation_date

        logger.warning(f"API version {version} has been deprecated")
        return True

    def sunset_version(self, version: str, sunset_date: datetime | None = None) -> bool:
        """Sunset an API version."""
        if version not in self.versions:
            return False

        api_version = self.versions[version]
        api_version.status = VersionStatus.SUNSET
        if sunset_date:
            api_version.sunset_date = sunset_date

        logger.warning(f"API version {version} has been sunset")
        return True

    def get_version_info(self, version: str) -> dict[str, Any] | None:
        """Get information about a specific version."""
        if version not in self.versions:
            return None

        return self.versions[version].to_dict()

    def list_versions(self, include_sunset: bool = False) -> list[dict[str, Any]]:
        """List all API versions."""
        versions = []
        for version in self.versions.values():
            if include_sunset or not version.is_sunset():
                versions.append(version.to_dict())

        return sorted(versions, key=lambda v: v["version"])

    def add_deprecation_headers(self, response: Response, version: str) -> None:
        """Add deprecation headers to response."""
        if version not in self.versions:
            return

        api_version = self.versions[version]
        if api_version.is_deprecated():
            response.headers["X-API-Version-Deprecated"] = "true"
            if api_version.deprecation_date:
                response.headers["X-API-Version-Deprecation-Date"] = (
                    api_version.deprecation_date.isoformat()
                )

            # Suggest latest version
            latest_version = self.get_latest_version()
            if latest_version:
                response.headers["X-API-Version-Latest"] = latest_version

    def validate_version(self, version: str) -> bool:
        """Validate if a version exists and is not sunset."""
        if version not in self.versions:
            return False

        api_version = self.versions[version]
        return not api_version.is_sunset()

    async def _initialize_default_versions(self) -> None:
        """Initialize default API versions."""
        now = datetime.utcnow()

        # Register v1
        v1_version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=now - timedelta(days=30),
            description="Initial API version with core functionality",
            new_features=[
                "Basic authentication",
                "Tool management",
                "Health checks",
                "OAuth integration",
                "Admin interface",
            ],
        )
        self.register_version(v1_version)

        # Register v2
        v2_version = APIVersion(
            version="v2",
            status=VersionStatus.ACTIVE,
            release_date=now,
            description="Enhanced API version with improved features",
            new_features=[
                "Enhanced authentication with session management",
                "Advanced tool search and filtering",
                "Comprehensive analytics",
                "Improved health checks",
                "Enhanced error handling",
                "Performance metrics",
            ],
            breaking_changes=[
                "Changed response format for some endpoints",
                "Updated authentication flow",
                "Modified tool creation parameters",
            ],
        )
        self.register_version(v2_version)

    async def shutdown(self) -> None:
        """Shutdown the API Version Manager."""
        self._initialized = False
        logger.info("API Version Manager shutdown")

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized


# Global instance
_version_manager = APIVersionManager()


def get_api_version_manager() -> APIVersionManager:
    """Get the global API version manager instance."""
    return _version_manager


async def version_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to handle API versioning.

    This middleware:
    - Detects API version from URL path
    - Validates version existence
    - Adds deprecation headers
    - Handles version routing
    """
    version_manager = get_api_version_manager()

    # Extract version from path
    path = request.url.path
    version = None

    # Check for version in path (e.g., /api/v1/tools)
    if path.startswith("/api/"):
        parts = path.split("/")
        if len(parts) >= 3 and parts[2].startswith("v"):
            version = parts[2]

    # If no version specified, use default
    if not version:
        version = version_manager.default_version

    # Validate version
    if not version_manager.validate_version(version):
        raise HTTPException(
            status_code=404,
            detail=f"API version '{version}' not found or has been sunset",
        )

    # Process request
    response = await call_next(request)

    # Add deprecation headers
    version_manager.add_deprecation_headers(response, version)

    return response


def create_version_router() -> APIRouter:
    """Create router for version management endpoints."""
    router = APIRouter()

    @router.get("/")
    async def list_versions(include_sunset: bool = False):
        """List all API versions."""
        version_manager = get_api_version_manager()
        return {
            "versions": version_manager.list_versions(include_sunset),
            "latest_version": version_manager.get_latest_version(),
            "active_versions": version_manager.get_active_versions(),
        }

    @router.get("/{version}")
    async def get_version_info(version: str):
        """Get information about a specific version."""
        version_manager = get_api_version_manager()
        info = version_manager.get_version_info(version)
        if not info:
            raise HTTPException(status_code=404, detail="Version not found")
        return info

    @router.get("/latest")
    async def get_latest_version():
        """Get the latest API version."""
        version_manager = get_api_version_manager()
        latest = version_manager.get_latest_version()
        if not latest:
            raise HTTPException(status_code=404, detail="No versions available")
        return {"latest_version": latest}

    return router

"""
API Versioning System

This module provides API versioning capabilities with proper routing,
version management, and deprecation handling.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from fastapi import APIRouter, Request, Response, HTTPException
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
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    description: str = ""
    breaking_changes: List[str] = None
    new_features: List[str] = None
    bug_fixes: List[str] = None

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "status": self.status.value,
            "release_date": self.release_date.isoformat(),
            "deprecation_date": self.deprecation_date.isoformat() if self.deprecation_date else None,
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "description": self.description,
            "breaking_changes": self.breaking_changes,
            "new_features": self.new_features,
            "bug_fixes": self.bug_fixes,
            "is_deprecated": self.is_deprecated(),
            "is_sunset": self.is_sunset()
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
        self.versions: Dict[str, APIVersion] = {}
        self.routers: Dict[str, APIRouter] = {}
        self.default_version = "v1"
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the API version manager."""
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
        """
        Register a new API version.
        
        Args:
            version: API version to register
        """
        self.versions[version.version] = version
        
        # Create router for this version
        prefix = f"/api/{version.version}"
        self.routers[version.version] = APIRouter(prefix=prefix)
        
        logger.info(f"Registered API version: {version.version}")

    def get_router(self, version: str) -> Optional[APIRouter]:
        """
        Get router for a specific version.
        
        Args:
            version: Version to get router for
            
        Returns:
            APIRouter for the version or None if not found
        """
        return self.routers.get(version)

    def get_latest_version(self) -> Optional[str]:
        """
        Get the latest API version.
        
        Returns:
            Latest version string or None if no versions
        """
        if not self.versions:
            return None
        
        # Sort by release date and return latest
        sorted_versions = sorted(
            self.versions.values(),
            key=lambda v: v.release_date,
            reverse=True
        )
        
        return sorted_versions[0].version

    def get_active_versions(self) -> List[str]:
        """
        Get all active API versions.
        
        Returns:
            List of active version strings
        """
        return [
            version for version, info in self.versions.items()
            if not info.is_sunset()
        ]

    def get_deprecated_versions(self) -> List[str]:
        """
        Get all deprecated API versions.
        
        Returns:
            List of deprecated version strings
        """
        return [
            version for version, info in self.versions.items()
            if info.is_deprecated() and not info.is_sunset()
        ]

    def get_sunset_versions(self) -> List[str]:
        """
        Get all sunset API versions.
        
        Returns:
            List of sunset version strings
        """
        return [
            version for version, info in self.versions.items()
            if info.is_sunset()
        ]

    def deprecate_version(self, version: str, deprecation_date: Optional[datetime] = None) -> bool:
        """
        Deprecate an API version.
        
        Args:
            version: Version to deprecate
            deprecation_date: Deprecation date (defaults to 6 months from now)
            
        Returns:
            True if version was deprecated, False if not found
        """
        if version not in self.versions:
            return False
        
        if deprecation_date is None:
            deprecation_date = datetime.utcnow() + timedelta(days=180)  # 6 months
        
        self.versions[version].status = VersionStatus.DEPRECATED
        self.versions[version].deprecation_date = deprecation_date
        
        logger.info(f"Deprecated API version: {version} (effective: {deprecation_date})")
        
        return True

    def sunset_version(self, version: str, sunset_date: Optional[datetime] = None) -> bool:
        """
        Sunset an API version.
        
        Args:
            version: Version to sunset
            sunset_date: Sunset date (defaults to 1 year from now)
            
        Returns:
            True if version was sunset, False if not found
        """
        if version not in self.versions:
            return False
        
        if sunset_date is None:
            sunset_date = datetime.utcnow() + timedelta(days=365)  # 1 year
        
        self.versions[version].status = VersionStatus.SUNSET
        self.versions[version].sunset_date = sunset_date
        
        logger.info(f"Sunset API version: {version} (effective: {sunset_date})")
        
        return True

    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """
        Get version information.
        
        Args:
            version: Version to get info for
            
        Returns:
            Version information or None if not found
        """
        if version not in self.versions:
            return None
        
        return self.versions[version].to_dict()

    def list_versions(self, include_sunset: bool = False) -> List[Dict[str, Any]]:
        """
        List all versions.
        
        Args:
            include_sunset: Include sunset versions
            
        Returns:
            List of version information
        """
        versions = []
        for version_info in self.versions.values():
            if not include_sunset and version_info.is_sunset():
                continue
            versions.append(version_info.to_dict())
        
        return sorted(versions, key=lambda v: v["release_date"], reverse=True)

    def add_deprecation_headers(self, response: Response, version: str) -> None:
        """
        Add deprecation headers to response.
        
        Args:
            response: FastAPI response object
            version: API version
        """
        if version not in self.versions:
            return
        
        version_info = self.versions[version]
        
        if version_info.is_deprecated():
            response.headers["Deprecation"] = "true"
            if version_info.deprecation_date:
                response.headers["Sunset"] = version_info.deprecation_date.isoformat()
            
            # Add warning header
            latest_version = self.get_latest_version()
            if latest_version:
                response.headers["Warning"] = f'299 - "This API version is deprecated. Use {latest_version} instead."'

    def validate_version(self, version: str) -> bool:
        """
        Validate if a version is available.
        
        Args:
            version: Version to validate
            
        Returns:
            True if version is available, False otherwise
        """
        if version not in self.versions:
            return False
        
        version_info = self.versions[version]
        
        # Check if version is sunset
        if version_info.is_sunset():
            return False
        
        return True

    async def _initialize_default_versions(self) -> None:
        """Initialize default API versions."""
        # Version 1.0
        v1 = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Initial API version with core functionality",
            new_features=[
                "Core MCP server functionality",
                "Tool registry and discovery",
                "Basic authentication and authorization",
                "Resource limits and monitoring"
            ]
        )
        self.register_version(v1)

        # Version 1.1 (future)
        v1_1 = APIVersion(
            version="v1.1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow() + timedelta(days=30),
            description="Enhanced API with additional features",
            new_features=[
                "Advanced resource monitoring",
                "Enhanced tool validation",
                "Improved error handling"
            ],
            bug_fixes=[
                "Fixed memory leak in long-running executions",
                "Improved API response times"
            ]
        )
        self.register_version(v1_1)

    async def shutdown(self) -> None:
        """Shutdown the API version manager."""
        logger.info("Shutting down API Version Manager")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the API version manager is initialized."""
        return self._initialized


# Global instance
_api_version_manager: Optional[APIVersionManager] = None


def get_api_version_manager() -> APIVersionManager:
    """Get the global API version manager instance."""
    global _api_version_manager
    if _api_version_manager is None:
        _api_version_manager = APIVersionManager()
    return _api_version_manager


# Middleware for version handling
async def version_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to handle API versioning.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/endpoint
        
    Returns:
        FastAPI response
    """
    # Extract version from path
    path = request.url.path
    version = None
    
    # Check for version in path: /api/v1/...
    if path.startswith("/api/"):
        parts = path.split("/")
        if len(parts) >= 3 and parts[2].startswith("v"):
            version = parts[2]
    
    # Validate version if present
    if version:
        version_manager = get_api_version_manager()
        if not version_manager.validate_version(version):
            raise HTTPException(
                status_code=400,
                detail=f"API version '{version}' is not available or has been sunset"
            )
    
    # Process request
    response = await call_next(request)
    
    # Add deprecation headers if needed
    if version:
        version_manager.add_deprecation_headers(response, version)
    
    return response


# API endpoints for version management
def create_version_router() -> APIRouter:
    """Create router for version management endpoints."""
    router = APIRouter(prefix="/api/versions", tags=["API Versions"])
    
    @router.get("/")
    async def list_versions(include_sunset: bool = False):
        """List all API versions."""
        version_manager = get_api_version_manager()
        return {
            "versions": version_manager.list_versions(include_sunset),
            "latest_version": version_manager.get_latest_version(),
            "active_versions": version_manager.get_active_versions(),
            "deprecated_versions": version_manager.get_deprecated_versions()
        }
    
    @router.get("/{version}")
    async def get_version_info(version: str):
        """Get specific version information."""
        version_manager = get_api_version_manager()
        info = version_manager.get_version_info(version)
        
        if not info:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return info
    
    @router.get("/latest")
    async def get_latest_version():
        """Get latest API version information."""
        version_manager = get_api_version_manager()
        latest = version_manager.get_latest_version()
        
        if not latest:
            raise HTTPException(status_code=404, detail="No versions available")
        
        return version_manager.get_version_info(latest)
    
    return router
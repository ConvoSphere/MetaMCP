"""
API Versioning Strategy

This module provides comprehensive API versioning with middleware,
version compatibility checks, and deprecation warnings.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from ..utils.logging import get_logger

logger = get_logger(__name__)


class VersionStatus(Enum):
    """API version status."""
    CURRENT = "current"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


@dataclass
class VersionInfo:
    """Version information."""
    version: str
    status: VersionStatus
    release_date: datetime
    sunset_date: Optional[datetime] = None
    deprecation_date: Optional[datetime] = None
    min_client_version: Optional[str] = None
    max_client_version: Optional[str] = None
    breaking_changes: Optional[List[str]] = None
    new_features: Optional[List[str]] = None
    bug_fixes: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.breaking_changes is None:
            self.breaking_changes = []
        if self.new_features is None:
            self.new_features = []
        if self.bug_fixes is None:
            self.bug_fixes = []


class APIVersionManager:
    """Manages API versioning and compatibility."""
    
    def __init__(self):
        """Initialize API version manager."""
        self.logger = get_logger(__name__)
        self.versions: Dict[str, VersionInfo] = {}
        self.current_version = "v1"
        self.default_version = "v1"
        
        # Initialize with default versions
        self._initialize_default_versions()
    
    def _initialize_default_versions(self):
        """Initialize with default API versions."""
        now = datetime.utcnow()
        
        # v1 - Current stable version
        self.add_version(VersionInfo(
            version="v1",
            status=VersionStatus.CURRENT,
            release_date=now - timedelta(days=30),
            new_features=["Initial API release"],
            bug_fixes=[],
            breaking_changes=[]
        ))
        
        # v2 - Future version (placeholder)
        self.add_version(VersionInfo(
            version="v2",
            status=VersionStatus.CURRENT,
            release_date=now + timedelta(days=30),
            deprecation_date=now + timedelta(days=90),
            new_features=["Enhanced error handling", "Rate limiting"],
            bug_fixes=[],
            breaking_changes=[]
        ))
    
    def add_version(self, version_info: VersionInfo):
        """Add a new API version."""
        self.versions[version_info.version] = version_info
        self.logger.info(f"Added API version: {version_info.version} ({version_info.status.value})")
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """Get version information."""
        return self.versions.get(version)
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        version_info = self.get_version_info(version)
        if not version_info:
            return False
        
        now = datetime.utcnow()
        
        # Check if version is sunset
        if version_info.sunset_date and now > version_info.sunset_date:
            return False
        
        return True
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated."""
        version_info = self.get_version_info(version)
        if not version_info:
            return False
        
        now = datetime.utcnow()
        return (version_info.deprecation_date and now > version_info.deprecation_date) or \
               version_info.status == VersionStatus.DEPRECATED
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported versions."""
        return [v for v in self.versions.keys() if self.is_version_supported(v)]
    
    def get_current_version(self) -> str:
        """Get current API version."""
        return self.current_version
    
    def get_latest_version(self) -> str:
        """Get latest API version."""
        supported_versions = self.get_supported_versions()
        if not supported_versions:
            return self.current_version
        
        # Sort by version number and return latest
        sorted_versions = sorted(supported_versions, key=self._parse_version)
        return sorted_versions[-1]
    
    def _parse_version(self, version: str) -> tuple[int, ...]:
        """Parse version string for comparison."""
        # Extract version numbers (e.g., "v1.2.3" -> (1, 2, 3))
        match = re.match(r'v?(\d+)(?:\.(\d+))?(?:\.(\d+))?', version)
        if match:
            return tuple(int(x) for x in match.groups() if x is not None)
        return (0,)
    
    def check_compatibility(self, client_version: str, server_version: str) -> tuple[bool, str]:
        """Check client-server version compatibility."""
        client_info = self.get_version_info(client_version)
        server_info = self.get_version_info(server_version)
        
        if not client_info or not server_info:
            return False, "Version not found"
        
        # Check if client version is within supported range
        if server_info.min_client_version:
            if self._parse_version(client_version) < self._parse_version(server_info.min_client_version):
                return False, f"Client version {client_version} is too old. Minimum required: {server_info.min_client_version}"
        
        if server_info.max_client_version:
            if self._parse_version(client_version) > self._parse_version(server_info.max_client_version):
                return False, f"Client version {client_version} is too new. Maximum supported: {server_info.max_client_version}"
        
        return True, "Compatible"
    
    def get_deprecation_warning(self, version: str) -> Optional[str]:
        """Get deprecation warning for version."""
        version_info = self.get_version_info(version)
        if not version_info or not self.is_version_deprecated(version):
            return None
        
        warning = f"API version {version} is deprecated"
        
        if version_info.sunset_date:
            warning += f" and will be sunset on {version_info.sunset_date.strftime('%Y-%m-%d')}"
        
        warning += ". Please upgrade to a newer version."
        
        return warning


class APIVersionMiddleware:
    """FastAPI middleware for API versioning."""
    
    def __init__(self, version_manager: APIVersionManager):
        """Initialize API version middleware."""
        self.version_manager = version_manager
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Any, call_next):
        """Process request with version checking."""
        # Extract version from request
        version = self._extract_version(request)
        
        # Check if version is supported
        if not self.version_manager.is_version_supported(version):
            return self._create_version_error_response(
                f"API version {version} is not supported",
                400,
                supported_versions=self.version_manager.get_supported_versions()
            )
        
        # Check for deprecation warning
        deprecation_warning = self.version_manager.get_deprecation_warning(version)
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        response.headers["X-API-Version"] = version
        response.headers["X-API-Latest-Version"] = self.version_manager.get_latest_version()
        
        if deprecation_warning:
            response.headers["X-API-Deprecation-Warning"] = deprecation_warning
            self.logger.warning(f"Deprecated API version used: {version}")
        
        return response
    
    def _extract_version(self, request: Any) -> str:
        """Extract API version from request."""
        # Try to get version from URL path
        path = str(request.url.path)
        version_match = re.search(r'/api/(v\d+)/', path)
        if version_match:
            return version_match.group(1)
        
        # Try to get version from header
        version_header = request.headers.get('X-API-Version')
        if version_header:
            return version_header
        
        # Try to get version from query parameter
        version_param = request.query_params.get('version')
        if version_param:
            return version_param
        
        # Default to current version
        return self.version_manager.get_current_version()
    
    def _create_version_error_response(self, message: str, status_code: int, 
                                    supported_versions: List[str] = None) -> Any:
        """Create version error response."""
        from fastapi.responses import JSONResponse
        
        error_response = {
            "error": "version_error",
            "message": message,
            "supported_versions": supported_versions or []
        }
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={
                "X-API-Latest-Version": self.version_manager.get_latest_version(),
                "X-API-Supported-Versions": ", ".join(supported_versions or [])
            }
        )


class VersionMigrationHelper:
    """Helper for API version migrations."""
    
    def __init__(self, version_manager: APIVersionManager):
        """Initialize version migration helper."""
        self.version_manager = version_manager
        self.logger = get_logger(__name__)
    
    def create_migration_guide(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Create migration guide between versions."""
        from_info = self.version_manager.get_version_info(from_version)
        to_info = self.version_manager.get_version_info(to_version)
        
        if not from_info or not to_info:
            return {"error": "Version not found"}
        
        guide = {
            "from_version": from_version,
            "to_version": to_version,
            "breaking_changes": to_info.breaking_changes or [],
            "new_features": to_info.new_features or [],
            "bug_fixes": to_info.bug_fixes or [],
            "migration_steps": []
        }
        
        # Add migration steps based on breaking changes
        breaking_changes = to_info.breaking_changes or []
        for change in breaking_changes:
            guide["migration_steps"].append({
                "type": "breaking_change",
                "description": change,
                "action_required": True
            })
        
        return guide
    
    def validate_migration(self, current_version: str, target_version: str) -> tuple[bool, List[str]]:
        """Validate if migration is possible."""
        issues = []
        
        # Check if versions exist
        if not self.version_manager.get_version_info(current_version):
            issues.append(f"Current version {current_version} not found")
        
        if not self.version_manager.get_version_info(target_version):
            issues.append(f"Target version {target_version} not found")
        
        # Check if target version is supported
        if not self.version_manager.is_version_supported(target_version):
            issues.append(f"Target version {target_version} is not supported")
        
        return len(issues) == 0, issues


# Global version manager instance
version_manager = APIVersionManager()


def create_version_middleware() -> APIVersionMiddleware:
    """Create API version middleware."""
    return APIVersionMiddleware(version_manager)


def get_version_info(version: str) -> Optional[VersionInfo]:
    """Get version information."""
    return version_manager.get_version_info(version)


def is_version_supported(version: str) -> bool:
    """Check if version is supported."""
    return version_manager.is_version_supported(version)


def get_supported_versions() -> List[str]:
    """Get list of supported versions."""
    return version_manager.get_supported_versions() 
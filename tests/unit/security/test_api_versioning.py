"""
Tests for API Versioning System
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from metamcp.api.versioning import (
    APIVersionManager,
    APIVersion,
    VersionStatus,
    get_api_version_manager,
)


class TestAPIVersionManager:
    """Test API Version Manager functionality."""

    @pytest.fixture
    async def version_manager(self):
        """Create API version manager instance."""
        manager = APIVersionManager()
        await manager.initialize()
        yield manager
        await manager.shutdown()

    def test_register_version(self, version_manager):
        """Test version registration."""
        # Create a new version
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Test version",
            new_features=["Feature 1", "Feature 2"],
        )

        # Register the version
        version_manager.register_version(version)

        # Check version was registered
        assert "v2.0" in version_manager.versions
        assert version_manager.versions["v2.0"] == version

        # Check router was created
        assert "v2.0" in version_manager.routers
        router = version_manager.routers["v2.0"]
        assert router.prefix == "/api/v2.0"

    def test_get_router(self, version_manager):
        """Test getting router for version."""
        # Register a version
        version = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        version_manager.register_version(version)

        # Get router
        router = version_manager.get_router("v2.0")
        assert router is not None
        assert router.prefix == "/api/v2.0"

        # Get non-existent router
        router = version_manager.get_router("v3.0")
        assert router is None

    def test_get_latest_version(self, version_manager):
        """Test getting latest version."""
        # Register versions with different release dates
        v1 = APIVersion(
            version="v1.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow() - timedelta(days=30),
        )
        v2 = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )

        version_manager.register_version(v1)
        version_manager.register_version(v2)

        # Get latest version
        latest = version_manager.get_latest_version()
        assert latest == "v2.0"

    def test_get_active_versions(self, version_manager):
        """Test getting active versions."""
        # Register versions with different statuses
        v1 = APIVersion(
            version="v1.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        v2 = APIVersion(
            version="v2.0",
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow(),
        )
        v3 = APIVersion(
            version="v3.0", status=VersionStatus.SUNSET, release_date=datetime.utcnow()
        )

        version_manager.register_version(v1)
        version_manager.register_version(v2)
        version_manager.register_version(v3)

        # Get active versions
        active_versions = version_manager.get_active_versions()
        assert "v1.0" in active_versions
        assert "v2.0" in active_versions  # Deprecated but not sunset
        assert "v3.0" not in active_versions  # Sunset

    def test_get_deprecated_versions(self, version_manager):
        """Test getting deprecated versions."""
        # Register versions with different statuses
        v1 = APIVersion(
            version="v1.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        v2 = APIVersion(
            version="v2.0",
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow(),
        )
        v3 = APIVersion(
            version="v3.0", status=VersionStatus.SUNSET, release_date=datetime.utcnow()
        )

        version_manager.register_version(v1)
        version_manager.register_version(v2)
        version_manager.register_version(v3)

        # Get deprecated versions
        deprecated_versions = version_manager.get_deprecated_versions()
        assert "v1.0" not in deprecated_versions
        assert "v2.0" in deprecated_versions
        assert "v3.0" not in deprecated_versions  # Sunset, not deprecated

    def test_get_sunset_versions(self, version_manager):
        """Test getting sunset versions."""
        # Register versions with different statuses
        v1 = APIVersion(
            version="v1.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        v2 = APIVersion(
            version="v2.0",
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow(),
        )
        v3 = APIVersion(
            version="v3.0", status=VersionStatus.SUNSET, release_date=datetime.utcnow()
        )

        version_manager.register_version(v1)
        version_manager.register_version(v2)
        version_manager.register_version(v3)

        # Get sunset versions
        sunset_versions = version_manager.get_sunset_versions()
        assert "v1.0" not in sunset_versions
        assert "v2.0" not in sunset_versions
        assert "v3.0" in sunset_versions

    def test_deprecate_version(self, version_manager):
        """Test version deprecation."""
        # Register a version
        version = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        version_manager.register_version(version)

        # Deprecate the version
        success = version_manager.deprecate_version("v2.0")
        assert success is True

        # Check version is deprecated
        version_info = version_manager.versions["v2.0"]
        assert version_info.status == VersionStatus.DEPRECATED
        assert version_info.deprecation_date is not None

        # Test deprecating non-existent version
        success = version_manager.deprecate_version("v3.0")
        assert success is False

    def test_sunset_version(self, version_manager):
        """Test version sunset."""
        # Register a version
        version = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        version_manager.register_version(version)

        # Sunset the version
        success = version_manager.sunset_version("v2.0")
        assert success is True

        # Check version is sunset
        version_info = version_manager.versions["v2.0"]
        assert version_info.status == VersionStatus.SUNSET
        assert version_info.sunset_date is not None

        # Test sunsetting non-existent version
        success = version_manager.sunset_version("v3.0")
        assert success is False

    def test_get_version_info(self, version_manager):
        """Test getting version information."""
        # Register a version
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Test version",
            new_features=["Feature 1"],
        )
        version_manager.register_version(version)

        # Get version info
        info = version_manager.get_version_info("v2.0")
        assert info is not None
        assert info["version"] == "v2.0"
        assert info["status"] == VersionStatus.ACTIVE.value
        assert info["description"] == "Test version"
        assert info["new_features"] == ["Feature 1"]
        assert info["is_deprecated"] is False
        assert info["is_sunset"] is False

        # Get non-existent version info
        info = version_manager.get_version_info("v3.0")
        assert info is None

    def test_list_versions(self, version_manager):
        """Test listing versions."""
        # Register multiple versions
        v1 = APIVersion(
            version="v1.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow() - timedelta(days=30),
        )
        v2 = APIVersion(
            version="v2.0", status=VersionStatus.SUNSET, release_date=datetime.utcnow()
        )

        version_manager.register_version(v1)
        version_manager.register_version(v2)

        # List all versions (excluding sunset)
        versions = version_manager.list_versions(include_sunset=False)
        assert len(versions) == 1
        assert versions[0]["version"] == "v1.0"

        # List all versions (including sunset)
        versions = version_manager.list_versions(include_sunset=True)
        assert len(versions) == 2

    def test_validate_version(self, version_manager):
        """Test version validation."""
        # Register a version
        version = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        version_manager.register_version(version)

        # Valid version
        is_valid = version_manager.validate_version("v2.0")
        assert is_valid is True

        # Non-existent version
        is_valid = version_manager.validate_version("v3.0")
        assert is_valid is False

        # Sunset version
        version_manager.sunset_version("v2.0")
        is_valid = version_manager.validate_version("v2.0")
        assert is_valid is False

    def test_global_instance(self):
        """Test global API version manager instance."""
        # Get global instance
        manager1 = get_api_version_manager()
        manager2 = get_api_version_manager()

        # Should be the same instance
        assert manager1 is manager2


class TestAPIVersion:
    """Test APIVersion model."""

    def test_version_creation(self):
        """Test APIVersion object creation."""
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Test version",
            new_features=["Feature 1", "Feature 2"],
            bug_fixes=["Bug fix 1"],
        )

        assert version.version == "v2.0"
        assert version.status == VersionStatus.ACTIVE
        assert version.description == "Test version"
        assert version.new_features == ["Feature 1", "Feature 2"]
        assert version.bug_fixes == ["Bug fix 1"]
        assert version.breaking_changes == []

    def test_is_deprecated(self):
        """Test deprecated status checking."""
        # Active version
        version = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        assert version.is_deprecated() is False

        # Deprecated version
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow(),
        )
        assert version.is_deprecated() is True

        # Version with deprecation date in past
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            deprecation_date=datetime.utcnow() - timedelta(days=1),
        )
        assert version.is_deprecated() is True

    def test_is_sunset(self):
        """Test sunset status checking."""
        # Active version
        version = APIVersion(
            version="v2.0", status=VersionStatus.ACTIVE, release_date=datetime.utcnow()
        )
        assert version.is_sunset() is False

        # Sunset version
        version = APIVersion(
            version="v2.0", status=VersionStatus.SUNSET, release_date=datetime.utcnow()
        )
        assert version.is_sunset() is True

        # Version with sunset date in past
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            sunset_date=datetime.utcnow() - timedelta(days=1),
        )
        assert version.is_sunset() is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        version = APIVersion(
            version="v2.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Test version",
            new_features=["Feature 1"],
        )

        version_dict = version.to_dict()

        assert version_dict["version"] == "v2.0"
        assert version_dict["status"] == VersionStatus.ACTIVE.value
        assert version_dict["description"] == "Test version"
        assert version_dict["new_features"] == ["Feature 1"]
        assert version_dict["is_deprecated"] is False
        assert version_dict["is_sunset"] is False
        assert "release_date" in version_dict

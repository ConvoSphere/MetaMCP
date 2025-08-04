"""
Tests for API Versioning System

This module contains unit tests for the API versioning functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from metamcp.api.versioning import (
    APIVersion,
    VersionStatus,
    APIVersionManager,
    get_api_version_manager,
    version_middleware
)
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestAPIVersion:
    """Test APIVersion class."""

    def test_version_creation(self):
        """Test creating an API version."""
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Test version"
        )
        
        assert version.version == "v1"
        assert version.status == VersionStatus.ACTIVE
        assert version.description == "Test version"
        assert version.breaking_changes == []
        assert version.new_features == []
        assert version.bug_fixes == []

    def test_version_is_deprecated(self):
        """Test deprecated version detection."""
        # Not deprecated
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        assert not version.is_deprecated()
        
        # Deprecated by status
        version.status = VersionStatus.DEPRECATED
        assert version.is_deprecated()
        
        # Deprecated by date
        version.status = VersionStatus.ACTIVE
        version.deprecation_date = datetime.utcnow() - timedelta(days=1)
        assert version.is_deprecated()

    def test_version_is_sunset(self):
        """Test sunset version detection."""
        # Not sunset
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        assert not version.is_sunset()
        
        # Sunset by status
        version.status = VersionStatus.SUNSET
        assert version.is_sunset()
        
        # Sunset by date
        version.status = VersionStatus.ACTIVE
        version.sunset_date = datetime.utcnow() - timedelta(days=1)
        assert version.is_sunset()

    def test_version_to_dict(self):
        """Test version serialization."""
        now = datetime.utcnow()
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=now,
            description="Test version",
            new_features=["feature1", "feature2"]
        )
        
        data = version.to_dict()
        
        assert data["version"] == "v1"
        assert data["status"] == "active"
        assert data["description"] == "Test version"
        assert data["new_features"] == ["feature1", "feature2"]
        assert data["is_deprecated"] is False
        assert data["is_sunset"] is False


class TestAPIVersionManager:
    """Test APIVersionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh version manager for each test."""
        return APIVersionManager()

    @pytest.mark.asyncio
    async def test_initialization(self, manager):
        """Test manager initialization."""
        assert not manager.is_initialized
        
        await manager.initialize()
        
        assert manager.is_initialized
        assert "v1" in manager.versions
        assert "v2" in manager.versions

    def test_register_version(self, manager):
        """Test version registration."""
        version = APIVersion(
            version="v3",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        
        manager.register_version(version)
        
        assert "v3" in manager.versions
        assert manager.versions["v3"] == version

    def test_get_latest_version(self, manager):
        """Test getting latest version."""
        # Add versions with different release dates
        v1 = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow() - timedelta(days=30)
        )
        v2 = APIVersion(
            version="v2",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        
        manager.register_version(v1)
        manager.register_version(v2)
        
        latest = manager.get_latest_version()
        assert latest == "v2"

    def test_get_active_versions(self, manager):
        """Test getting active versions."""
        v1 = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        v2 = APIVersion(
            version="v2",
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow()
        )
        v3 = APIVersion(
            version="v3",
            status=VersionStatus.SUNSET,
            release_date=datetime.utcnow()
        )
        
        manager.register_version(v1)
        manager.register_version(v2)
        manager.register_version(v3)
        
        active = manager.get_active_versions()
        assert "v1" in active
        assert "v2" not in active  # Deprecated
        assert "v3" not in active  # Sunset

    def test_deprecate_version(self, manager):
        """Test version deprecation."""
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        manager.register_version(version)
        
        success = manager.deprecate_version("v1")
        assert success is True
        assert manager.versions["v1"].status == VersionStatus.DEPRECATED

    def test_sunset_version(self, manager):
        """Test version sunset."""
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        manager.register_version(version)
        
        success = manager.sunset_version("v1")
        assert success is True
        assert manager.versions["v1"].status == VersionStatus.SUNSET

    def test_validate_version(self, manager):
        """Test version validation."""
        # Valid version
        version = APIVersion(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        manager.register_version(version)
        assert manager.validate_version("v1") is True
        
        # Sunset version
        manager.sunset_version("v1")
        assert manager.validate_version("v1") is False
        
        # Non-existent version
        assert manager.validate_version("v999") is False

    def test_add_deprecation_headers(self, manager):
        """Test deprecation header addition."""
        from fastapi.responses import Response
        
        version = APIVersion(
            version="v1",
            status=VersionStatus.DEPRECATED,
            release_date=datetime.utcnow(),
            deprecation_date=datetime.utcnow() + timedelta(days=30)
        )
        manager.register_version(version)
        
        # Add a latest version
        latest_version = APIVersion(
            version="v2",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow()
        )
        manager.register_version(latest_version)
        
        response = Response()
        manager.add_deprecation_headers(response, "v1")
        
        assert response.headers["X-API-Version-Deprecated"] == "true"
        assert "X-API-Version-Deprecation-Date" in response.headers
        assert response.headers["X-API-Version-Latest"] == "v2"


class TestVersionMiddleware:
    """Test version middleware."""

    @pytest.mark.asyncio
    async def test_version_detection(self):
        """Test version detection from URL."""
        from fastapi import Request
        
        # Mock request
        request = Mock(spec=Request)
        request.url.path = "/api/v2/tools"
        
        # Mock call_next
        call_next = Mock()
        call_next.return_value = Mock()
        
        # Mock version manager
        with patch('metamcp.api.versioning.get_api_version_manager') as mock_get_manager:
            manager = Mock()
            manager.default_version = "v1"
            manager.validate_version.return_value = True
            mock_get_manager.return_value = manager
            
            await version_middleware(request, call_next)
            
            # Should detect v2 from URL
            manager.validate_version.assert_called_with("v2")

    @pytest.mark.asyncio
    async def test_default_version(self):
        """Test default version when no version specified."""
        from fastapi import Request
        
        # Mock request without version
        request = Mock(spec=Request)
        request.url.path = "/api/tools"
        
        # Mock call_next
        call_next = Mock()
        call_next.return_value = Mock()
        
        # Mock version manager
        with patch('metamcp.api.versioning.get_api_version_manager') as mock_get_manager:
            manager = Mock()
            manager.default_version = "v1"
            manager.validate_version.return_value = True
            mock_get_manager.return_value = manager
            
            await version_middleware(request, call_next)
            
            # Should use default version
            manager.validate_version.assert_called_with("v1")

    @pytest.mark.asyncio
    async def test_invalid_version(self):
        """Test handling of invalid version."""
        from fastapi import Request
        
        # Mock request
        request = Mock(spec=Request)
        request.url.path = "/api/v999/tools"
        
        # Mock call_next
        call_next = Mock()
        
        # Mock version manager
        with patch('metamcp.api.versioning.get_api_version_manager') as mock_get_manager:
            manager = Mock()
            manager.default_version = "v1"
            manager.validate_version.return_value = False
            mock_get_manager.return_value = manager
            
            with pytest.raises(HTTPException) as exc_info:
                await version_middleware(request, call_next)
            
            assert exc_info.value.status_code == 404


class TestVersionEndpoints:
    """Test version management endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI
        from metamcp.api.versioning import create_version_router
        
        app = FastAPI()
        app.include_router(create_version_router(), prefix="/api/versions")
        return TestClient(app)

    def test_list_versions(self, client):
        """Test listing versions endpoint."""
        with patch('metamcp.api.versioning.get_api_version_manager') as mock_get_manager:
            manager = Mock()
            manager.list_versions.return_value = [
                {
                    "version": "v1",
                    "status": "active",
                    "is_deprecated": False,
                    "is_sunset": False
                }
            ]
            manager.get_latest_version.return_value = "v2"
            manager.get_active_versions.return_value = ["v1", "v2"]
            mock_get_manager.return_value = manager
            
            response = client.get("/api/versions/")
            
            assert response.status_code == 200
            data = response.json()
            assert "versions" in data
            assert "latest_version" in data
            assert "active_versions" in data

    def test_get_version_info(self, client):
        """Test getting version info endpoint."""
        with patch('metamcp.api.versioning.get_api_version_manager') as mock_get_manager:
            manager = Mock()
            manager.get_version_info.return_value = {
                "version": "v1",
                "status": "active",
                "is_deprecated": False,
                "is_sunset": False
            }
            mock_get_manager.return_value = manager
            
            response = client.get("/api/versions/v1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "v1"
            assert data["status"] == "active"

    def test_get_latest_version(self, client):
        """Test getting latest version endpoint."""
        with patch('metamcp.api.versioning.get_api_version_manager') as mock_get_manager:
            manager = Mock()
            manager.get_latest_version.return_value = "v2"
            mock_get_manager.return_value = manager
            
            response = client.get("/api/versions/latest")
            
            assert response.status_code == 200
            data = response.json()
            assert data["latest_version"] == "v2"


def test_get_api_version_manager():
    """Test getting the global version manager."""
    manager = get_api_version_manager()
    assert isinstance(manager, APIVersionManager)
    
    # Should return the same instance
    manager2 = get_api_version_manager()
    assert manager is manager2
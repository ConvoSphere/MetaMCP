"""
Health Monitoring Tests

Tests for the health monitoring system including uptime calculation,
health checks, and component status monitoring.
"""

import time
from datetime import UTC, datetime

import pytest
from unittest.mock import AsyncMock, patch
from metamcp.api.health import (
    check_database_health,
    check_vector_db_health,
    check_llm_service_health,
    get_uptime,
    format_uptime,
)


class TestUptimeFunctions:
    """Test uptime utility functions."""

    def test_get_uptime(self):
        """Test getting uptime."""
        uptime = get_uptime()
        assert isinstance(uptime, float)
        assert uptime >= 0

    def test_format_uptime_seconds(self):
        """Test formatting uptime in seconds."""
        result = format_uptime(30)
        assert "30 seconds" in result

    def test_format_uptime_minutes(self):
        """Test formatting uptime in minutes."""
        result = format_uptime(90)
        assert "1 minute" in result

    def test_format_uptime_hours(self):
        """Test formatting uptime in hours."""
        result = format_uptime(3660)
        assert "1 hour" in result

    def test_format_uptime_days(self):
        """Test formatting uptime in days."""
        result = format_uptime(86400)
        assert "1 day" in result


class TestComponentHealthChecks:
    """Test component health check functions."""

    @pytest.mark.asyncio
    @patch("metamcp.utils.database.get_database_manager")
    async def test_check_database_health_success(self, mock_get_db_manager):
        """Test successful database health check."""
        # Mock database manager
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {
            "status": "healthy",
            "response_time": 0.001,
            "test_query_result": 1,
            "pool_stats": {"size": 10, "idle_size": 8}
        }
        mock_get_db_manager.return_value = mock_db_manager

        health = await check_database_health()

        assert health.name == "database"
        assert health.status == "healthy"
        assert health.response_time is not None
        assert health.response_time >= 0
        assert health.error is None

    @pytest.mark.asyncio
    @patch("metamcp.vector.client.get_vector_client")
    async def test_check_vector_db_health_success(self, mock_get_vector_client):
        """Test successful vector database health check."""
        # Mock vector client
        mock_vector_client = AsyncMock()
        mock_vector_client.health_check.return_value = {
            "status": "healthy",
            "response_time": 0.001
        }
        mock_get_vector_client.return_value = mock_vector_client

        health = await check_vector_db_health()

        assert health.name == "vector_database"
        assert health.status == "healthy"
        assert health.response_time is not None
        assert health.response_time >= 0
        assert health.error is None

    @pytest.mark.asyncio
    @patch("metamcp.llm.service.get_llm_service")
    async def test_check_llm_service_health_success(self, mock_get_llm_service):
        """Test successful LLM service health check."""
        # Mock LLM service
        mock_llm_service = AsyncMock()
        mock_llm_service.health_check.return_value = {
            "status": "healthy",
            "response_time": 0.001
        }
        mock_get_llm_service.return_value = mock_llm_service

        health = await check_llm_service_health()

        assert health.name == "llm_service"
        assert health.status == "healthy"
        assert health.response_time is not None
        assert health.response_time >= 0
        assert health.error is None


class TestHealthEndpoints:
    """Test health check API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from metamcp.main import create_app

        app = create_app()
        return TestClient(app)

    @patch("metamcp.utils.database.get_database_manager")
    @patch("metamcp.vector.client.get_vector_client")
    @patch("metamcp.llm.service.get_llm_service")
    def test_basic_health_check(self, mock_get_llm_service, mock_get_vector_client, mock_get_db_manager, client):
        """Test basic health check endpoint."""
        # Mock all services to return healthy
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_db_manager.return_value = mock_db_manager

        mock_vector_client = AsyncMock()
        mock_vector_client.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_vector_client.return_value = mock_vector_client

        mock_llm_service = AsyncMock()
        mock_llm_service.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_llm_service.return_value = mock_llm_service

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert data["healthy"] is True
        assert data["version"] == "1.0.0"
        assert data["uptime"] >= 0

    @patch("metamcp.utils.database.get_database_manager")
    @patch("metamcp.vector.client.get_vector_client")
    @patch("metamcp.llm.service.get_llm_service")
    def test_detailed_health_check(self, mock_get_llm_service, mock_get_vector_client, mock_get_db_manager, client):
        """Test detailed health check endpoint."""
        # Mock all services to return healthy
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_db_manager.return_value = mock_db_manager

        mock_vector_client = AsyncMock()
        mock_vector_client.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_vector_client.return_value = mock_vector_client

        mock_llm_service = AsyncMock()
        mock_llm_service.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_llm_service.return_value = mock_llm_service

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "overall_healthy" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "components" in data
        assert isinstance(data["components"], list)
        assert len(data["components"]) > 0

        # Check component structure
        for component in data["components"]:
            assert "name" in component
            assert "status" in component
            assert "response_time" in component

    @patch("metamcp.utils.database.get_database_manager")
    @patch("metamcp.vector.client.get_vector_client")
    @patch("metamcp.llm.service.get_llm_service")
    def test_readiness_probe(self, mock_get_llm_service, mock_get_vector_client, mock_get_db_manager, client):
        """Test readiness probe endpoint."""
        # Mock all services to return healthy
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_db_manager.return_value = mock_db_manager

        mock_vector_client = AsyncMock()
        mock_vector_client.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_vector_client.return_value = mock_vector_client

        mock_llm_service = AsyncMock()
        mock_llm_service.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_llm_service.return_value = mock_llm_service

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ready"

    def test_liveness_probe(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"

    def test_service_info(self, client):
        """Test service info endpoint."""
        response = client.get("/api/v1/health/info")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "uptime" in data
        assert "start_time" in data
        assert "environment" in data
        assert "dependencies" in data


class TestHealthErrorHandling:
    """Test health check error handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from metamcp.main import create_app

        app = create_app()
        return TestClient(app)

    @patch("metamcp.utils.database.get_database_manager")
    def test_health_check_with_error(self, mock_get_db_manager, client):
        """Test health check when database is unhealthy."""
        # Mock database to return unhealthy
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_get_db_manager.return_value = mock_db_manager

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()
        assert data["healthy"] is False

    @patch("metamcp.utils.database.get_database_manager")
    @patch("metamcp.vector.client.get_vector_client")
    @patch("metamcp.llm.service.get_llm_service")
    def test_detailed_health_check_with_errors(self, mock_get_llm_service, mock_get_vector_client, mock_get_db_manager, client):
        """Test detailed health check with component errors."""
        # Mock services to return mixed health status
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_db_manager.return_value = mock_db_manager

        mock_vector_client = AsyncMock()
        mock_vector_client.health_check.return_value = {"status": "unhealthy", "error": "Connection timeout"}
        mock_get_vector_client.return_value = mock_vector_client

        mock_llm_service = AsyncMock()
        mock_llm_service.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_llm_service.return_value = mock_llm_service

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_healthy"] is False

        # Check that unhealthy components are reported
        component_names = [comp["name"] for comp in data["components"]]
        assert "vector_database" in component_names


class TestHealthMetrics:
    """Test health check metrics and accuracy."""

    def test_uptime_accuracy(self):
        """Test uptime calculation accuracy."""
        import time
        start_time = time.time()
        uptime = get_uptime()
        end_time = time.time()

        # Uptime should be within reasonable bounds
        assert uptime >= 0
        assert uptime <= (end_time - start_time + 1)  # Allow 1 second tolerance

    def test_uptime_formatting_edge_cases(self):
        """Test uptime formatting with edge cases."""
        # Test zero uptime
        result = format_uptime(0)
        assert "0 seconds" in result

        # Test very large uptime
        result = format_uptime(999999999)
        assert "day" in result or "hour" in result or "minute" in result


class TestHealthComponentIntegration:
    """Test health check component integration."""

    @pytest.mark.asyncio
    @patch("metamcp.utils.database.get_database_manager")
    @patch("metamcp.vector.client.get_vector_client")
    @patch("metamcp.llm.service.get_llm_service")
    async def test_all_components_healthy(self, mock_get_llm_service, mock_get_vector_client, mock_get_db_manager):
        """Test when all components are healthy."""
        # Mock all services to return healthy
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_db_manager.return_value = mock_db_manager

        mock_vector_client = AsyncMock()
        mock_vector_client.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_vector_client.return_value = mock_vector_client

        mock_llm_service = AsyncMock()
        mock_llm_service.health_check.return_value = {"status": "healthy", "response_time": 0.001}
        mock_get_llm_service.return_value = mock_llm_service

        db_health = await check_database_health()
        vector_health = await check_vector_db_health()
        llm_health = await check_llm_service_health()

        components = [db_health, vector_health, llm_health]

        # All components should be healthy in test environment
        for component in components:
            assert component.status == "healthy"
            assert component.response_time >= 0
            assert component.error is None

    def test_health_check_response_structure(self):
        """Test health check response structure consistency."""
        from metamcp.api.health import HealthComponent

        # Test health component structure
        component = HealthComponent(
            name="test",
            status="healthy",
            response_time=0.001,
            error=None
        )

        assert component.name == "test"
        assert component.status == "healthy"
        assert component.response_time == 0.001
        assert component.error is None

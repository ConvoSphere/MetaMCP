"""
Health Monitoring Tests

Tests for the health monitoring system including uptime calculation,
health checks, and component status monitoring.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from metamcp.api.health import (
    format_uptime,
    check_database_health,
    check_vector_db_health,
    check_llm_service_health,
    health_router,
)
from metamcp.utils.database import get_database_manager


class TestUptimeFunctions:
    """Test uptime formatting functions."""

    def test_format_uptime_seconds(self):
        """Test formatting uptime in seconds."""
        result = format_uptime(30)
        assert "30s" in result

    def test_format_uptime_minutes(self):
        """Test formatting uptime in minutes."""
        result = format_uptime(90)
        assert "1m 30s" in result

    def test_format_uptime_hours(self):
        """Test formatting uptime in hours."""
        result = format_uptime(3660)
        assert "1h 1m 0s" in result

    def test_format_uptime_days(self):
        """Test formatting uptime in days."""
        result = format_uptime(86400)
        assert "1d 0h 0m 0s" in result


class TestComponentHealthChecks:
    """Test individual component health checks."""

    @pytest.mark.asyncio
    @patch("metamcp.utils.database.get_database_manager")
    async def test_check_database_health_success(self, mock_get_db_manager):
        """Test successful database health check."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy", "response_time": 0.1}
        mock_get_db_manager.return_value = mock_db_manager

        result = await check_database_health()

        assert result.name == "database"
        assert result.status == "healthy"
        assert result.response_time is not None

    @pytest.mark.asyncio
    @patch("metamcp.config.get_settings")
    async def test_check_vector_db_health_success(self, mock_get_settings):
        """Test successful vector database health check."""
        mock_settings = Mock()
        mock_settings.weaviate_url = "http://localhost:8080"
        mock_get_settings.return_value = mock_settings

        with patch("weaviate.connect_to_custom") as mock_weaviate:
            mock_client = Mock()
            mock_client.is_ready.return_value = True
            mock_client.get_meta.return_value = Mock(version="1.0.0")
            mock_weaviate.return_value = mock_client

            result = await check_vector_db_health()

            assert result.name == "vector_db"
            assert result.status == "healthy"
            assert result.response_time is not None

    @pytest.mark.asyncio
    @patch("metamcp.config.get_settings")
    async def test_check_llm_service_health_success(self, mock_get_settings):
        """Test successful LLM service health check."""
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        with patch("openai.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_client.models.list.return_value = Mock(data=[Mock(id="gpt-3.5-turbo")])
            mock_openai.return_value = mock_client

            result = await check_llm_service_health()

            assert result.name == "llm_service"
            assert result.status == "healthy"
            assert result.response_time is not None


class TestHealthEndpoints:
    """Test health check API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(health_router, prefix="/api/v1/health")
        return TestClient(app)

    @patch("metamcp.utils.database.get_database_manager")
    def test_basic_health_check(self, mock_get_db_manager, client):
        """Test basic health check endpoint."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy"}
        mock_get_db_manager.return_value = mock_db_manager

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert "timestamp" in data
        assert "version" in data

    @patch("metamcp.utils.database.get_database_manager")
    def test_detailed_health_check(self, mock_get_db_manager, client):
        """Test detailed health check endpoint."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy"}
        mock_get_db_manager.return_value = mock_db_manager

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "overall_healthy" in data
        assert "components" in data
        assert "uptime" in data

    @patch("metamcp.utils.database.get_database_manager")
    def test_readiness_probe(self, mock_get_db_manager, client):
        """Test readiness probe endpoint."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy"}
        mock_get_db_manager.return_value = mock_db_manager

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "ready" in data

    def test_service_info(self, client):
        """Test service info endpoint."""
        response = client.get("/api/v1/health/info")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "environment" in data
        assert "version" in data


class TestHealthErrorHandling:
    """Test health check error handling."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(health_router, prefix="/api/v1/health")
        return TestClient(app)

    @patch("metamcp.utils.database.get_database_manager")
    def test_health_check_with_error(self, mock_get_db_manager, client):
        """Test health check when database is unhealthy."""
        # Mock database to return unhealthy
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_get_db_manager.return_value = mock_db_manager

        response = client.get("/api/v1/health")

        # The health check should still return 200 but with healthy=False
        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is False

    @patch("metamcp.utils.database.get_database_manager")
    def test_detailed_health_check_with_errors(self, mock_get_db_manager, client):
        """Test detailed health check with component errors."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_get_db_manager.return_value = mock_db_manager

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_healthy"] is False
        assert len(data["components"]) > 0


class TestHealthMetrics:
    """Test health check metrics and formatting."""

    def test_uptime_formatting_edge_cases(self):
        """Test uptime formatting with edge cases."""
        # Test zero uptime
        result = format_uptime(0)
        assert "0s" in result

        # Test negative uptime
        result = format_uptime(-30)
        assert "-30s" in result

        # Test very large uptime
        result = format_uptime(999999)
        assert "d" in result  # Should show days


class TestHealthComponentIntegration:
    """Test integration between health check components."""

    @pytest.mark.asyncio
    @patch("metamcp.utils.database.get_database_manager")
    @patch("metamcp.config.get_settings")
    async def test_all_components_healthy(self, mock_get_settings, mock_get_db_manager):
        """Test when all components are healthy."""
        # Mock database
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy"}
        mock_get_db_manager.return_value = mock_db_manager

        # Mock settings
        mock_settings = Mock()
        mock_settings.weaviate_url = "http://localhost:8080"
        mock_settings.openai_api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        # Mock external services
        with patch("weaviate.connect_to_custom") as mock_weaviate, \
             patch("openai.OpenAI") as mock_openai:
            
            mock_weaviate_client = Mock()
            mock_weaviate_client.is_ready.return_value = True
            mock_weaviate_client.get_meta.return_value = Mock(version="1.0.0")
            mock_weaviate.return_value = mock_weaviate_client

            mock_openai_client = Mock()
            mock_openai_client.models.list.return_value = Mock(data=[Mock(id="gpt-3.5-turbo")])
            mock_openai.return_value = mock_openai_client

            # Test all health checks
            db_health = await check_database_health()
            vector_health = await check_vector_db_health()
            llm_health = await check_llm_service_health()

            assert db_health.status == "healthy"
            assert vector_health.status == "healthy"
            assert llm_health.status == "healthy"

    def test_health_check_response_structure(self):
        """Test health check response structure consistency."""
        from metamcp.api.health import ComponentHealth, DetailedHealthStatus

        # Test ComponentHealth structure
        component = ComponentHealth(
            name="test",
            status="healthy",
            response_time=0.1
        )
        assert component.name == "test"
        assert component.status == "healthy"
        assert component.response_time == 0.1

        # Test DetailedHealthStatus structure
        detailed = DetailedHealthStatus(
            overall_healthy=True,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            uptime=3600.0,
            components=[component]
        )
        assert detailed.overall_healthy is True
        assert len(detailed.components) == 1

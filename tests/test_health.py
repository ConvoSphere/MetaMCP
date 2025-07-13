"""
Health Monitoring Tests

Tests for the health monitoring system including uptime calculation,
health checks, and component status monitoring.
"""

import pytest
import time
from datetime import datetime, UTC
from unittest.mock import Mock, patch

from fastapi import HTTPException

from metamcp.api.health import (
    get_uptime,
    format_uptime,
    check_database_health,
    check_vector_db_health,
    check_llm_service_health
)


class TestUptimeFunctions:
    """Test uptime calculation and formatting."""
    
    def test_get_uptime(self):
        """Test uptime calculation."""
        uptime = get_uptime()
        assert uptime >= 0
        assert isinstance(uptime, float)
    
    def test_format_uptime_seconds(self):
        """Test uptime formatting for seconds."""
        formatted = format_uptime(45)
        assert formatted == "45s"
    
    def test_format_uptime_minutes(self):
        """Test uptime formatting for minutes."""
        formatted = format_uptime(125)  # 2 minutes 5 seconds
        assert formatted == "2m 5s"
    
    def test_format_uptime_hours(self):
        """Test uptime formatting for hours."""
        formatted = format_uptime(7325)  # 2 hours 2 minutes 5 seconds
        assert formatted == "2h 2m 5s"
    
    def test_format_uptime_days(self):
        """Test uptime formatting for days."""
        formatted = format_uptime(90000)  # 1 day 1 hour
        assert formatted == "1d 1h 0m 0s"


class TestComponentHealthChecks:
    """Test component health check functions."""
    
    @pytest.mark.asyncio
    async def test_check_database_health_success(self):
        """Test successful database health check."""
        health = await check_database_health()
        
        assert health.name == "database"
        assert health.status == "healthy"
        assert health.response_time is not None
        assert health.response_time >= 0
        assert health.error is None
    
    @pytest.mark.asyncio
    async def test_check_vector_db_health_success(self):
        """Test successful vector database health check."""
        health = await check_vector_db_health()
        
        assert health.name == "vector_database"
        assert health.status == "healthy"
        assert health.response_time is not None
        assert health.response_time >= 0
        assert health.error is None
    
    @pytest.mark.asyncio
    async def test_check_llm_service_health_success(self):
        """Test successful LLM service health check."""
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
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
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
    
    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
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
    
    def test_readiness_probe(self, client):
        """Test readiness probe endpoint."""
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
        assert "uptime" in data
        assert "uptime_formatted" in data
        assert data["status"] == "alive"
        assert data["uptime"] >= 0
        assert isinstance(data["uptime_formatted"], str)
    
    def test_service_info(self, client):
        """Test service information endpoint."""
        response = client.get("/api/v1/health/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "uptime" in data
        assert "uptime_formatted" in data
        assert "start_time" in data
        assert "current_time" in data
        assert "environment" in data
        assert "debug" in data
        
        assert data["service"] == "MetaMCP"
        assert data["version"] == "1.0.0"
        assert data["uptime"] >= 0
        assert isinstance(data["uptime_formatted"], str)
        assert isinstance(data["start_time"], str)
        assert isinstance(data["current_time"], str)


class TestHealthErrorHandling:
    """Test health check error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from metamcp.main import create_app
        
        app = create_app()
        return TestClient(app)
    
    def test_health_check_with_error(self, client):
        """Test health check when components are unhealthy."""
        # This test would require mocking unhealthy components
        # For now, we test the basic structure
        response = client.get("/api/v1/health")
        
        # Should still return 200 even if some components are unhealthy
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
    
    def test_detailed_health_check_with_errors(self, client):
        """Test detailed health check with component errors."""
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        
        # Check that all components have proper structure
        for component in data["components"]:
            assert "name" in component
            assert "status" in component
            assert "response_time" in component
            assert component["status"] in ["healthy", "unhealthy"]


class TestHealthMetrics:
    """Test health metrics and monitoring."""
    
    def test_uptime_accuracy(self):
        """Test uptime calculation accuracy."""
        start_time = time.time()
        uptime1 = get_uptime()
        time.sleep(0.1)  # Small delay
        uptime2 = get_uptime()
        
        # Uptime should increase
        assert uptime2 > uptime1
        
        # Difference should be approximately the sleep time
        diff = uptime2 - uptime1
        assert 0.05 <= diff <= 0.15  # Allow some tolerance
    
    def test_uptime_formatting_edge_cases(self):
        """Test uptime formatting edge cases."""
        # Zero uptime
        assert format_uptime(0) == "0s"
        
        # Very large uptime
        large_uptime = 999999  # About 11.5 days
        formatted = format_uptime(large_uptime)
        assert "d" in formatted
        
        # Negative uptime (should handle gracefully)
        assert format_uptime(-1) == "-1s"


class TestHealthComponentIntegration:
    """Test health component integration."""
    
    @pytest.mark.asyncio
    async def test_all_components_healthy(self):
        """Test when all components are healthy."""
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
        """Test health check response structure."""
        from metamcp.api.health import HealthStatus, ComponentHealth
        
        # Test HealthStatus structure
        health_status = HealthStatus(
            healthy=True,
            timestamp=datetime.now(UTC).isoformat(),
            version="1.0.0",
            uptime=100.0
        )
        
        assert health_status.healthy is True
        assert health_status.version == "1.0.0"
        assert health_status.uptime == 100.0
        
        # Test ComponentHealth structure
        component_health = ComponentHealth(
            name="test_component",
            status="healthy",
            response_time=0.1
        )
        
        assert component_health.name == "test_component"
        assert component_health.status == "healthy"
        assert component_health.response_time == 0.1
        assert component_health.error is None 
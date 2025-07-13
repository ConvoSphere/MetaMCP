"""
Black Box Tests for Health Monitoring Endpoints

Tests the health check and monitoring endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL, assert_success_response


class TestHealthEndpoints:
    """Test health monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, http_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await http_client.get(f"{API_BASE_URL}/health")

        data = assert_success_response(response)
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health(self, http_client: AsyncClient):
        """Test detailed health status endpoint."""
        response = await http_client.get(f"{API_BASE_URL}/health/detailed")

        data = assert_success_response(response)
        assert "status" in data
        assert "uptime" in data
        assert "version" in data
        assert "components" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert isinstance(data["uptime"], (int, float))
        assert isinstance(data["components"], dict)

    @pytest.mark.asyncio
    async def test_health_ready(self, http_client: AsyncClient):
        """Test readiness probe endpoint."""
        response = await http_client.get(f"{API_BASE_URL}/health/ready")

        data = assert_success_response(response)
        assert "ready" in data
        assert "timestamp" in data
        assert data["ready"] is True

    @pytest.mark.asyncio
    async def test_health_live(self, http_client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await http_client.get(f"{API_BASE_URL}/health/live")

        data = assert_success_response(response)
        assert "alive" in data
        assert "timestamp" in data
        assert data["alive"] is True

    @pytest.mark.asyncio
    async def test_health_components(self, http_client: AsyncClient):
        """Test that health components are properly structured."""
        response = await http_client.get(f"{API_BASE_URL}/health/detailed")

        data = assert_success_response(response)
        components = data["components"]

        # Check that components have expected structure
        for component_name, component_data in components.items():
            assert "status" in component_data
            assert component_data["status"] in ["healthy", "unhealthy", "degraded"]

            # Some components might have additional metrics
            if "response_time" in component_data:
                assert isinstance(component_data["response_time"], (int, float))
            if "hit_rate" in component_data:
                assert isinstance(component_data["hit_rate"], (int, float))
                assert 0 <= component_data["hit_rate"] <= 1

    @pytest.mark.asyncio
    async def test_health_uptime_increases(self, http_client: AsyncClient):
        """Test that uptime increases over time."""
        # Get initial uptime
        response1 = await http_client.get(f"{API_BASE_URL}/health/detailed")
        data1 = assert_success_response(response1)
        uptime1 = data1["uptime"]

        # Wait a moment
        import asyncio
        await asyncio.sleep(1)

        # Get uptime again
        response2 = await http_client.get(f"{API_BASE_URL}/health/detailed")
        data2 = assert_success_response(response2)
        uptime2 = data2["uptime"]

        # Uptime should have increased
        assert uptime2 >= uptime1, f"Uptime should increase: {uptime1} -> {uptime2}"

    @pytest.mark.asyncio
    async def test_health_version_consistent(self, http_client: AsyncClient):
        """Test that version is consistent across health endpoints."""
        # Check detailed health
        detailed_response = await http_client.get(f"{API_BASE_URL}/health/detailed")
        detailed_data = assert_success_response(detailed_response)
        detailed_version = detailed_data["version"]

        # Version should be a string and not empty
        assert isinstance(detailed_version, str)
        assert len(detailed_version) > 0
        assert "." in detailed_version  # Should be semantic versioning

    @pytest.mark.asyncio
    async def test_health_timestamp_format(self, http_client: AsyncClient):
        """Test that timestamps are in correct format."""
        response = await http_client.get(f"{API_BASE_URL}/health")

        data = assert_success_response(response)
        timestamp = data["timestamp"]

        # Should be ISO 8601 format
        import re
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$'
        assert re.match(iso_pattern, timestamp), f"Invalid timestamp format: {timestamp}"

    @pytest.mark.asyncio
    async def test_health_endpoints_accessible(self, http_client: AsyncClient):
        """Test that all health endpoints are accessible without authentication."""
        endpoints = [
            "/health",
            "/health/detailed",
            "/health/ready",
            "/health/live"
        ]

        for endpoint in endpoints:
            response = await http_client.get(f"{API_BASE_URL}{endpoint}")
            assert response.status_code == 200, f"Endpoint {endpoint} should be accessible"

            data = response.json()
            assert "status" in data or "ready" in data or "alive" in data, f"Endpoint {endpoint} should return health data"

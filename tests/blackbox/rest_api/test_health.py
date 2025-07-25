"""
Black Box Tests for Health Monitoring Endpoints

Tests the health check and monitoring endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL


class TestHealthEndpoints:
    """Test health monitoring endpoints for actual API response format."""

    @pytest.mark.asyncio
    async def test_health_check(self, http_client: AsyncClient):
        """Test basic health check endpoint (should return 'healthy': true)."""
        response = await http_client.get(f"{API_BASE_URL}health/")
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert isinstance(data["healthy"], bool)
        assert data["healthy"] is True
        assert "timestamp" in data
        assert "uptime" in data

    @pytest.mark.asyncio
    async def test_detailed_health(self, http_client: AsyncClient):
        """Test detailed health status endpoint (should return health details)."""
        response = await http_client.get(f"{API_BASE_URL}health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "overall_healthy" in data
        assert "uptime" in data
        assert "components" in data
        assert "timestamp" in data
        assert isinstance(data["components"], list)

    @pytest.mark.asyncio
    async def test_health_ready(self, http_client: AsyncClient):
        """Test readiness probe endpoint (should return 'ready': true)."""
        response = await http_client.get(f"{API_BASE_URL}health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_live(self, http_client: AsyncClient):
        """Test liveness probe endpoint (should return 'alive': true)."""
        response = await http_client.get(f"{API_BASE_URL}health/live")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"

    @pytest.mark.asyncio
    async def test_health_components(self, http_client: AsyncClient):
        """Test that health components are properly structured."""
        response = await http_client.get(f"{API_BASE_URL}health/detailed")
        assert response.status_code == 200
        data = response.json()
        components = data["components"]
        assert isinstance(components, list)
        for component in components:
            assert "name" in component
            assert "status" in component
            assert component["status"] in ["healthy", "unhealthy", "degraded"]
            # Optional metrics
            if "response_time" in component:
                assert isinstance(component["response_time"], int | float)

    @pytest.mark.asyncio
    async def test_health_uptime_increases(self, http_client: AsyncClient):
        """Test that uptime increases over time."""
        response1 = await http_client.get(f"{API_BASE_URL}health/detailed")
        assert response1.status_code == 200
        data1 = response1.json()
        uptime1 = data1["uptime"]
        import asyncio

        await asyncio.sleep(1)
        response2 = await http_client.get(f"{API_BASE_URL}health/detailed")
        assert response2.status_code == 200
        data2 = response2.json()
        uptime2 = data2["uptime"]
        assert uptime2 >= uptime1, f"Uptime should increase: {uptime1} -> {uptime2}"

    @pytest.mark.asyncio
    async def test_health_version_consistent(self, http_client: AsyncClient):
        """Test that version is consistent across health endpoints."""
        detailed_response = await http_client.get(f"{API_BASE_URL}health/detailed")
        assert detailed_response.status_code == 200
        detailed_data = detailed_response.json()
        detailed_version = detailed_data["version"]
        assert isinstance(detailed_version, str)
        assert len(detailed_version) > 0
        assert "." in detailed_version  # Should be semantic versioning

    @pytest.mark.asyncio
    async def test_health_timestamp_format(self, http_client: AsyncClient):
        """Test that timestamps are in correct ISO 8601 format."""
        response = await http_client.get(f"{API_BASE_URL}health/")
        assert response.status_code == 200
        data = response.json()
        timestamp = data["timestamp"]
        import re

        iso_pattern = (
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$"
        )
        assert re.match(
            iso_pattern, timestamp
        ), f"Invalid timestamp format: {timestamp}"

    @pytest.mark.asyncio
    async def test_health_endpoints_accessible(self, http_client: AsyncClient):
        """Test that all health endpoints are accessible without authentication."""
        endpoints = ["health/", "health/detailed", "health/ready", "health/live"]
        for endpoint in endpoints:
            response = await http_client.get(f"{API_BASE_URL}{endpoint}")
            assert (
                response.status_code == 200
            ), f"Endpoint {endpoint} should be accessible"
            data = response.json()
            assert any(
                k in data for k in ["healthy", "status", "overall_healthy"]
            ), f"Endpoint {endpoint} should return health data"

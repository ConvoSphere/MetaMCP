"""
Black Box Tests for Proxy API Endpoints

Tests the proxy server registration, discovery, and management endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL

PROXY_SERVER = {
    "name": "test_proxy_server",
    "endpoint": "http://localhost:9000",
    "transport": "http",
    "auth_required": False,
    "timeout": 10,
    "retry_attempts": 2,
    "security_level": "medium",
    "categories": ["test"],
    "description": "Test proxy server",
    "metadata": {"env": "test"},
}


class TestProxyEndpoints:
    """Test proxy server registration, listing, and discovery endpoints."""

    @pytest.mark.asyncio
    async def test_register_proxy_server(self, authenticated_client: AsyncClient):
        """Test registering a new proxy server."""
        response = await authenticated_client.post(
            f"{API_BASE_URL}proxy/servers", json=PROXY_SERVER
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "server_id" in data
        self.server_id = data["server_id"]

    @pytest.mark.asyncio
    async def test_list_proxy_servers(self, authenticated_client: AsyncClient):
        """Test listing all registered proxy servers."""
        response = await authenticated_client.get(f"{API_BASE_URL}proxy/servers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_proxy_server_info(self, authenticated_client: AsyncClient):
        """Test getting info for a specific proxy server (should fail if not registered)."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}proxy/servers/nonexistent_id"
        )
        assert response.status_code in [404, 400]
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_discover_proxy_servers(self, authenticated_client: AsyncClient):
        """Test discovering proxy servers."""
        discovery_config = {
            "network_discovery": True,
            "service_discovery": False,
            "file_discovery": False,
            "ports": [9000],
            "base_urls": ["http://localhost"],
            "config_paths": [],
            "service_endpoints": [],
            "timeout": 2,
            "max_concurrent": 2,
        }
        response = await authenticated_client.post(
            f"{API_BASE_URL}proxy/discovery", json=discovery_config
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "discovered_count" in data
        assert "servers" in data
        assert isinstance(data["servers"], list)

    @pytest.mark.asyncio
    async def test_get_discovered_proxy_servers(
        self, authenticated_client: AsyncClient
    ):
        """Test getting all discovered proxy servers."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}proxy/discovery/servers"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

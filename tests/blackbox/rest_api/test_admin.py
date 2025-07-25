"""
Black Box Tests for Admin API Endpoints

Tests the admin dashboard and management endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL


class TestAdminEndpoints:
    """Test admin dashboard and management endpoints."""

    @pytest.mark.asyncio
    async def test_get_admin_dashboard(self, authenticated_client: AsyncClient):
        """Test getting the admin dashboard data."""
        response = await authenticated_client.get(f"{API_BASE_URL}admin/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "users" in data or "system" in data or "tools" in data

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_unauthorized(self, http_client: AsyncClient):
        """Test getting the admin dashboard without authentication (should fail)."""
        response = await http_client.get(f"{API_BASE_URL}admin/dashboard")
        assert response.status_code in [401, 403]
        data = response.json()
        assert "error" in data or "detail" in data

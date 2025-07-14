"""
Black Box Tests for OAuth API Endpoints

Tests the OAuth configuration, initiation, and callback endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL

class TestOAuthEndpoints:
    """Test OAuth configuration, initiation, and callback endpoints."""

    @pytest.mark.asyncio
    async def test_get_oauth_config(self, authenticated_client: AsyncClient):
        """Test getting OAuth configuration."""
        response = await authenticated_client.get(f"{API_BASE_URL}oauth/config")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "agent_oauth_enabled" in data
        assert "supported_scopes" in data

    @pytest.mark.asyncio
    async def test_initiate_oauth_flow(self, authenticated_client: AsyncClient):
        """Test initiating OAuth flow (should fail for unknown provider)."""
        request_data = {"provider": "unknown", "is_agent": False}
        response = await authenticated_client.post(
            f"{API_BASE_URL}oauth/initiate",
            json=request_data
        )
        assert response.status_code in [400, 404]
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_oauth_callback_missing_params(self, authenticated_client: AsyncClient):
        """Test OAuth callback with missing parameters (should fail)."""
        response = await authenticated_client.get(f"{API_BASE_URL}oauth/callback/google")
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "detail" in data 
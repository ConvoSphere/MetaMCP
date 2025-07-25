"""
Black Box Tests for Authentication Endpoints

Tests the authentication and authorization endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import (
    API_BASE_URL,
    TEST_USER,
)


class TestAuthentication:
    """Test authentication endpoints with actual API response format."""

    @pytest.mark.asyncio
    async def test_login_success(self, http_client: AsyncClient):
        """Test successful login."""
        response = await http_client.post(f"{API_BASE_URL}auth/login", json=TEST_USER)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, http_client: AsyncClient):
        """Test login with invalid credentials."""
        response = await http_client.post(
            f"{API_BASE_URL}auth/login",
            json={"username": "invalid_user", "password": "wrong_password"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, http_client: AsyncClient):
        """Test login with missing required fields."""
        response = await http_client.post(
            f"{API_BASE_URL}auth/login", json={"username": "test_user"}
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_me_endpoint(self, authenticated_client: AsyncClient):
        """Test /auth/me endpoint with valid token."""
        response = await authenticated_client.get(f"{API_BASE_URL}auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "roles" in data
        assert "permissions" in data
        assert data["username"] == TEST_USER["username"]

    @pytest.mark.asyncio
    async def test_me_endpoint_unauthorized(self, http_client: AsyncClient):
        """Test /auth/me endpoint without authentication."""
        response = await http_client.get(f"{API_BASE_URL}auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_permissions_endpoint(self, authenticated_client: AsyncClient):
        """Test /auth/permissions endpoint."""
        response = await authenticated_client.get(f"{API_BASE_URL}auth/permissions")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "permissions" in data
        assert isinstance(data["permissions"], dict)

    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test logout endpoint."""
        response = await authenticated_client.post(f"{API_BASE_URL}auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token(self, authenticated_client: AsyncClient):
        """Test token refresh endpoint."""
        response = await authenticated_client.post(f"{API_BASE_URL}auth/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"


class TestAuthorization:
    """Test authorization and access control."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(
        self, authenticated_client: AsyncClient
    ):
        """Test accessing protected endpoint with valid token."""
        response = await authenticated_client.get(f"{API_BASE_URL}tools/")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, http_client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await http_client.get(f"{API_BASE_URL}tools/")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_protected_endpoint_invalid_token(self, http_client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        http_client.headers["Authorization"] = "Bearer invalid_token"
        response = await http_client.get(f"{API_BASE_URL}tools/")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

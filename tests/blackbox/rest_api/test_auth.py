"""
Black Box Tests for Authentication Endpoints

Tests the authentication and authorization endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL, TEST_USER, assert_success_response, assert_error_response


class TestAuthentication:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, http_client: AsyncClient):
        """Test successful login."""
        response = await http_client.post(
            f"{API_BASE_URL}/auth/login",
            json=TEST_USER
        )
        
        data = assert_success_response(response)
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["username"] == TEST_USER["username"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, http_client: AsyncClient):
        """Test login with invalid credentials."""
        response = await http_client.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "username": "invalid_user",
                "password": "wrong_password"
            }
        )
        
        assert_error_response(response, 401, "AUTHENTICATION_ERROR")
    
    @pytest.mark.asyncio
    async def test_login_missing_fields(self, http_client: AsyncClient):
        """Test login with missing required fields."""
        response = await http_client.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": "test_user"}
        )
        
        assert_error_response(response, 422, "VALIDATION_ERROR")
    
    @pytest.mark.asyncio
    async def test_me_endpoint(self, authenticated_client: AsyncClient):
        """Test /auth/me endpoint with valid token."""
        response = await authenticated_client.get(f"{API_BASE_URL}/auth/me")
        
        data = assert_success_response(response)
        assert "user_id" in data
        assert "username" in data
        assert "roles" in data
        assert "permissions" in data
        assert data["username"] == TEST_USER["username"]
    
    @pytest.mark.asyncio
    async def test_me_endpoint_unauthorized(self, http_client: AsyncClient):
        """Test /auth/me endpoint without authentication."""
        response = await http_client.get(f"{API_BASE_URL}/auth/me")
        
        assert_error_response(response, 401, "AUTHENTICATION_ERROR")
    
    @pytest.mark.asyncio
    async def test_permissions_endpoint(self, authenticated_client: AsyncClient):
        """Test /auth/permissions endpoint."""
        response = await authenticated_client.get(f"{API_BASE_URL}/auth/permissions")
        
        data = assert_success_response(response)
        assert "user_id" in data
        assert "username" in data
        assert "roles" in data
        assert "permissions" in data
        assert data["username"] == TEST_USER["username"]
    
    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test logout endpoint."""
        response = await authenticated_client.post(f"{API_BASE_URL}/auth/logout")
        
        data = assert_success_response(response)
        assert "message" in data
        assert "Successfully logged out" in data["message"]
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, authenticated_client: AsyncClient):
        """Test token refresh endpoint."""
        response = await authenticated_client.post(f"{API_BASE_URL}/auth/refresh")
        
        data = assert_success_response(response)
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"


class TestAuthorization:
    """Test authorization and access control."""
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, authenticated_client: AsyncClient):
        """Test accessing protected endpoint with valid token."""
        response = await authenticated_client.get(f"{API_BASE_URL}/tools")
        
        # Should succeed (200) or return empty list (200)
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, http_client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await http_client.get(f"{API_BASE_URL}/tools")
        
        assert_error_response(response, 401, "AUTHENTICATION_ERROR")
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_invalid_token(self, http_client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        http_client.headers["Authorization"] = "Bearer invalid_token"
        response = await http_client.get(f"{API_BASE_URL}/tools")
        
        assert_error_response(response, 401, "AUTHENTICATION_ERROR") 
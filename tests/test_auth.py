"""
Authentication Tests

Tests for the authentication system including JWT tokens, user authentication,
and permission management.
"""

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from metamcp.api.auth import (
    authenticate_user,
    create_access_token,
    pwd_context,
    users_db,
    verify_token,
)
from metamcp.config import get_settings
from metamcp.exceptions import AuthenticationError

settings = get_settings()


class TestJWTTokenFunctions:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "test_user"

    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        data = {"sub": "test_user"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "test_user"

        # Check expiry
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, UTC)
        now = datetime.now(UTC)

        # Token should expire in approximately 30 minutes
        assert exp_datetime > now
        assert exp_datetime <= now + timedelta(minutes=31)

    def test_verify_token_valid(self):
        """Test valid token verification."""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "test_user"

    def test_verify_token_invalid(self):
        """Test invalid token verification."""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            verify_token("invalid_token")

    def test_verify_token_expired(self):
        """Test expired token verification."""
        data = {"sub": "test_user", "exp": datetime.now(UTC) - timedelta(hours=1)}
        token = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)

        with pytest.raises(AuthenticationError):
            verify_token(token)

    def test_verify_token_blacklisted(self):
        """Test blacklisted token verification."""
        from metamcp.api.auth import token_blacklist

        data = {"sub": "test_user"}
        token = create_access_token(data)
        token_blacklist.add(token)

        with pytest.raises(AuthenticationError, match="Token has been revoked"):
            verify_token(token)


class TestUserAuthentication:
    """Test user authentication functions."""

    def test_authenticate_user_valid(self):
        """Test valid user authentication."""
        user = authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        assert user["user_id"] == "admin_user"

    def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username."""
        user = authenticate_user("nonexistent", "password")
        assert user is None

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        user = authenticate_user("admin", "wrongpassword")
        assert user is None

    def test_authenticate_user_empty_credentials(self):
        """Test authentication with empty credentials."""
        user = authenticate_user("", "")
        assert user is None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password"
        hashed = pwd_context.hash(password)

        assert hashed != password
        assert pwd_context.verify(password, hashed)
        assert not pwd_context.verify("wrong_password", hashed)


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from metamcp.main import create_app

        app = create_app()
        return TestClient(app)

    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": "",
            "password": ""
        })

        assert response.status_code == 401

    def test_get_current_user_info(self, client):
        """Test getting current user info."""
        # First login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Get user info
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "admin_user"
        assert data["username"] == "admin"
        assert "roles" in data
        assert "permissions" in data

    def test_get_current_user_invalid_token(self, client):
        """Test getting user info with invalid token."""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid_token"
        })

        assert response.status_code == 401

    def test_get_user_permissions(self, client):
        """Test getting user permissions."""
        # First login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Get permissions
        response = client.get("/api/v1/auth/permissions", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "admin_user"
        assert "permissions" in data
        assert "tools" in data["permissions"]
        assert "admin" in data["permissions"]

    def test_refresh_token(self, client):
        """Test token refresh."""
        # First login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Refresh token
        response = client.post("/api/v1/auth/refresh", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_logout(self, client):
        """Test logout functionality."""
        # First login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Logout
        response = client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestUserDatabase:
    """Test user database functionality."""

    def test_user_database_structure(self):
        """Test user database structure."""
        assert "admin" in users_db
        assert "user" in users_db

        admin_user = users_db["admin"]
        assert "username" in admin_user
        assert "hashed_password" in admin_user
        assert "user_id" in admin_user
        assert "roles" in admin_user
        assert "permissions" in admin_user

    def test_admin_user_permissions(self):
        """Test admin user permissions."""
        admin_user = users_db["admin"]
        assert "admin" in admin_user["roles"]
        assert "tools:read" in admin_user["permissions"]
        assert "tools:write" in admin_user["permissions"]
        assert "tools:execute" in admin_user["permissions"]
        assert "admin:manage" in admin_user["permissions"]

    def test_regular_user_permissions(self):
        """Test regular user permissions."""
        regular_user = users_db["user"]
        assert "user" in regular_user["roles"]
        assert "tools:read" in regular_user["permissions"]
        assert "tools:execute" in regular_user["permissions"]
        assert "admin:manage" not in regular_user["permissions"]


class TestAuthenticationError:
    """Test authentication error handling."""

    def test_authentication_error_creation(self):
        """Test AuthenticationError creation."""
        error = AuthenticationError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code == "authentication_error"

    def test_authentication_error_with_custom_code(self):
        """Test AuthenticationError with custom error code."""
        error = AuthenticationError("Test error", "custom_error")
        assert error.message == "Test error"
        assert error.error_code == "custom_error"

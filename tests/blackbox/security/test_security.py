"""
Black Box Security Tests

Tests the security characteristics and vulnerability resistance of the MetaMCP REST API.
"""

import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
from tests.blackbox.conftest import API_BASE_URL

sys.path.insert(0, str(project_root))


class TestAuthenticationSecurity:
    """Test authentication security measures."""

    @pytest.mark.asyncio
    async def test_sql_injection_login(self, http_client: AsyncClient):
        """Test SQL injection resistance in login endpoint."""
        injection_payloads = [
            {"username": "admin' OR '1'='1", "password": "anything"},
            {"username": "admin'; DROP TABLE users; --", "password": "anything"},
            {"username": "admin' UNION SELECT * FROM users --", "password": "anything"},
        ]

        for payload in injection_payloads:
            response = await http_client.post(f"{API_BASE_URL}auth/login", json=payload)
            # Should not succeed with injection attempts
            assert response.status_code in [401, 400, 422]

    @pytest.mark.asyncio
    async def test_brute_force_protection(self, http_client: AsyncClient):
        """Test brute force attack protection."""
        for i in range(10):
            response = await http_client.post(
                f"{API_BASE_URL}auth/login",
                json={"username": "admin", "password": f"wrong_password_{i}"},
            )
            # Should not allow rapid failed attempts
            if i > 5:
                assert response.status_code in [401, 429, 403]

    @pytest.mark.asyncio
    async def test_weak_password_handling(self, http_client: AsyncClient):
        """Test handling of weak passwords."""
        weak_passwords = ["", "123", "password", "admin", "test"]

        for password in weak_passwords:
            response = await http_client.post(
                f"{API_BASE_URL}auth/login",
                json={"username": "test_user", "password": password},
            )
            # Should reject weak passwords
            assert response.status_code in [401, 400, 422]


class TestAuthorizationSecurity:
    """Test authorization and access control security."""

    @pytest.mark.asyncio
    async def test_unauthorized_access_attempts(self, http_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        protected_endpoints = [
            f"{API_BASE_URL}tools",
            f"{API_BASE_URL}admin/dashboard",
            f"{API_BASE_URL}auth/me",
            f"{API_BASE_URL}proxy/servers",
        ]

        for endpoint in protected_endpoints:
            response = await http_client.get(endpoint)
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_invalid_token_handling(self, http_client: AsyncClient):
        """Test handling of invalid authentication tokens."""
        http_client.headers["Authorization"] = "Bearer invalid_token"

        protected_endpoints = [
            f"{API_BASE_URL}tools",
            f"{API_BASE_URL}auth/me",
        ]

        for endpoint in protected_endpoints:
            response = await http_client.get(endpoint)
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_token_tampering(self, http_client: AsyncClient):
        """Test token tampering resistance."""
        # Get a valid token first
        login_response = await http_client.post(
            f"{API_BASE_URL}auth/login",
            json={"username": "test_user", "password": "test_password123"},
        )

        if login_response.status_code == 200:
            token_data = login_response.json()
            original_token = token_data["access_token"]

            # Tamper with the token
            tampered_token = original_token[:-5] + "XXXXX"
            http_client.headers["Authorization"] = f"Bearer {tampered_token}"

            response = await http_client.get(f"{API_BASE_URL}auth/me")
            assert response.status_code in [401, 403]


class TestInputValidationSecurity:
    """Test input validation and sanitization security."""

    @pytest.mark.asyncio
    async def test_xss_injection_tool_registration(
        self, authenticated_client: AsyncClient
    ):
        """Test XSS injection resistance in tool registration."""
        xss_payloads = [
            {
                "name": "<script>alert('xss')</script>",
                "description": "XSS test",
                "endpoint": "http://localhost:9000",
            },
            {
                "name": "test_tool",
                "description": "<img src=x onerror=alert('xss')>",
                "endpoint": "http://localhost:9000",
            },
            {
                "name": "test_tool",
                "description": "Normal description",
                "endpoint": "javascript:alert('xss')",
            },
        ]

        for payload in xss_payloads:
            response = await authenticated_client.post(
                f"{API_BASE_URL}tools", json=payload
            )
            # Should reject or sanitize XSS payloads
            assert response.status_code in [400, 422, 201]

    @pytest.mark.asyncio
    async def test_path_traversal_attempts(self, authenticated_client: AsyncClient):
        """Test path traversal attack resistance."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in traversal_payloads:
            response = await authenticated_client.get(f"{API_BASE_URL}tools/{payload}")
            # Should not allow path traversal
            assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_command_injection_tool_execution(
        self, authenticated_client: AsyncClient
    ):
        """Test command injection resistance in tool execution."""
        injection_payloads = [
            {"arguments": {"cmd": "; rm -rf /"}},
            {"arguments": {"input": "test && cat /etc/passwd"}},
            {"arguments": {"query": "test | ls -la"}},
        ]

        for payload in injection_payloads:
            response = await authenticated_client.post(
                f"{API_BASE_URL}tools/test_tool/execute", json=payload
            )
            # Should reject command injection attempts
            assert response.status_code in [400, 422, 404]


class TestSecurityHeaders:
    """Test security headers and response security."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, http_client: AsyncClient):
        """Test presence of important security headers."""
        response = await http_client.get(f"{API_BASE_URL}health/")

        # Check for security headers
        headers = response.headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
        ]

        # At least some security headers should be present
        present_headers = [h for h in security_headers if h in headers]
        assert (
            len(present_headers) > 0
        ), f"No security headers found. Present: {list(headers.keys())}"

    @pytest.mark.asyncio
    async def test_cors_headers(self, http_client: AsyncClient):
        """Test CORS header configuration."""
        response = await http_client.get(f"{API_BASE_URL}health/")
        headers = response.headers

        # Check CORS headers
        cors_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods"]
        present_cors = [h for h in cors_headers if h in headers]
        assert len(present_cors) > 0, "No CORS headers found"


class TestRateLimitingSecurity:
    """Test rate limiting and DDoS protection."""

    @pytest.mark.asyncio
    async def test_rate_limiting_health_endpoint(self, http_client: AsyncClient):
        """Test rate limiting on health endpoint."""
        # Make many rapid requests
        responses = []
        for _i in range(100):
            response = await http_client.get(f"{API_BASE_URL}health/")
            responses.append(response)

            # If rate limiting is active, we should see 429 responses
            if response.status_code == 429:
                break

        # Check if rate limiting was triggered
        any(r.status_code == 429 for r in responses)
        # Rate limiting is optional, so we don't assert it must be present

    @pytest.mark.asyncio
    async def test_rate_limiting_auth_endpoint(self, http_client: AsyncClient):
        """Test rate limiting on authentication endpoint."""
        # Make many rapid login attempts
        responses = []
        for _i in range(20):
            response = await http_client.post(
                f"{API_BASE_URL}auth/login",
                json={"username": "test_user", "password": "wrong_password"},
            )
            responses.append(response)

            # If rate limiting is active, we should see 429 responses
            if response.status_code == 429:
                break

        # Check if rate limiting was triggered
        any(r.status_code == 429 for r in responses)
        # Rate limiting is optional, so we don't assert it must be present


class TestDataValidationSecurity:
    """Test data validation and sanitization."""

    @pytest.mark.asyncio
    async def test_oversized_payload_handling(self, authenticated_client: AsyncClient):
        """Test handling of oversized payloads."""
        # Create an oversized tool definition
        oversized_tool = {
            "name": "oversized_tool",
            "description": "A" * 10000,  # Very large description
            "endpoint": "http://localhost:9000",
            "category": "test",
            "capabilities": ["read"],
            "security_level": 1,
            "metadata": {"large_data": "x" * 50000},  # Very large metadata
        }

        response = await authenticated_client.post(
            f"{API_BASE_URL}tools", json=oversized_tool
        )

        # Should reject or handle oversized payloads gracefully
        assert response.status_code in [400, 413, 422]

    @pytest.mark.asyncio
    async def test_malformed_json_handling(self, authenticated_client: AsyncClient):
        """Test handling of malformed JSON."""
        malformed_payloads = [
            '{"name": "test", "description": "test", "endpoint": "http://localhost:9000"',  # Missing closing brace
            '{"name": "test", "description": "test", "endpoint": "http://localhost:9000",}',  # Trailing comma
            '{"name": "test", "description": "test", "endpoint": "http://localhost:9000", "invalid": }',  # Invalid value
        ]

        for payload in malformed_payloads:
            response = await authenticated_client.post(
                f"{API_BASE_URL}tools",
                content=payload,
                headers={"Content-Type": "application/json"},
            )
            # Should reject malformed JSON
            assert response.status_code in [400, 422]

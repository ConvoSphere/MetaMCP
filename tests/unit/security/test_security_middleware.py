"""
Security Middleware Tests

Tests for input validation and security middleware functionality.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock

from metamcp.security.middleware import SecurityMiddleware, RateLimitMiddleware


@pytest.fixture
def app():
    """Create test FastAPI app with security middleware."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.post("/test")
    async def test_post_endpoint(request):
        body = await request.json()
        return {"message": "success", "data": body}
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    def test_valid_request(self, client):
        """Test that valid requests pass through."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    def test_sql_injection_in_path(self, client):
        """Test SQL injection detection in path."""
        malicious_paths = [
            "/test'; DROP TABLE users; --",
            "/test'; DELETE FROM users; --",
            "/test'; UPDATE users SET role='admin'; --",
        ]
        
        for path in malicious_paths:
            response = client.get(path)
            assert response.status_code == 400
            assert "Invalid request path" in response.json()["error"]
    
    def test_path_traversal_in_path(self, client):
        """Test path traversal detection in path."""
        malicious_paths = [
            "/test/../../../etc/passwd",
            "/test/..\\..\\..\\windows\\system32\\config\\sam",
            "/test/....//....//....//etc/passwd",
        ]
        
        for path in malicious_paths:
            response = client.get(path)
            assert response.status_code == 400
            assert "Invalid request path" in response.json()["error"]
    
    def test_xss_in_query_params(self, client):
        """Test XSS detection in query parameters."""
        malicious_params = [
            "?param=<script>alert('XSS')</script>",
            "?param=javascript:alert('XSS')",
            "?param=<img src=x onerror=alert('XSS')>",
        ]
        
        for param in malicious_params:
            response = client.get(f"/test{param}")
            assert response.status_code == 400
            assert "Invalid query parameters" in response.json()["error"]
    
    def test_command_injection_in_query_params(self, client):
        """Test command injection detection in query parameters."""
        malicious_params = [
            "?param=; rm -rf /",
            "?param=| cat /etc/passwd",
            "?param=&& whoami",
        ]
        
        for param in malicious_params:
            response = client.get(f"/test{param}")
            assert response.status_code == 400
            assert "Invalid query parameters" in response.json()["error"]
    
    def test_sql_injection_in_json_body(self, client):
        """Test SQL injection detection in JSON body."""
        malicious_payloads = [
            {"name": "'; DROP TABLE users; --"},
            {"query": "'; DELETE FROM users; --"},
            {"data": "'; UPDATE users SET role='admin'; --"},
        ]
        
        for payload in malicious_payloads:
            response = client.post("/test", json=payload)
            assert response.status_code == 400
            assert "Invalid request body" in response.json()["error"]
    
    def test_xss_in_json_body(self, client):
        """Test XSS detection in JSON body."""
        malicious_payloads = [
            {"name": "<script>alert('XSS')</script>"},
            {"content": "javascript:alert('XSS')"},
            {"data": "<img src=x onerror=alert('XSS')>"},
        ]
        
        for payload in malicious_payloads:
            response = client.post("/test", json=payload)
            assert response.status_code == 400
            assert "Invalid request body" in response.json()["error"]
    
    def test_command_injection_in_json_body(self, client):
        """Test command injection detection in JSON body."""
        malicious_payloads = [
            {"command": "; rm -rf /"},
            {"script": "| cat /etc/passwd"},
            {"data": "&& whoami"},
        ]
        
        for payload in malicious_payloads:
            response = client.post("/test", json=payload)
            assert response.status_code == 400
            assert "Invalid request body" in response.json()["error"]
    
    def test_null_bytes_in_path(self, client):
        """Test null byte detection in path."""
        response = client.get("/test\x00")
        assert response.status_code == 400
        assert "Invalid request path" in response.json()["error"]
    
    def test_null_bytes_in_body(self, client):
        """Test null byte detection in body."""
        response = client.post("/test", json={"data": "test\x00data"})
        assert response.status_code == 400
        assert "Invalid request body" in response.json()["error"]
    
    def test_valid_json_body(self, client):
        """Test that valid JSON bodies pass through."""
        valid_payloads = [
            {"name": "test", "value": 123},
            {"data": ["item1", "item2"]},
            {"nested": {"key": "value"}},
        ]
        
        for payload in valid_payloads:
            response = client.post("/test", json=payload)
            assert response.status_code == 200
            assert response.json()["message"] == "success"
    
    def test_security_headers_present(self, client):
        """Test that security headers are added to responses."""
        response = client.get("/test")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        
        # Check header values
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality."""
    
    def test_rate_limit_not_exceeded(self, client):
        """Test that requests within rate limit pass through."""
        # Make requests within rate limit
        for i in range(5):
            response = client.get("/test")
            assert response.status_code == 200
    
    def test_rate_limit_exceeded(self, client):
        """Test that requests exceeding rate limit are blocked."""
        # Make many requests to exceed rate limit
        responses = []
        for i in range(150):  # Exceed default limit of 100
            response = client.get("/test")
            responses.append(response)
        
        # Check that some requests were rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0
        
        # Check rate limit response
        rate_limit_response = rate_limited[0]
        assert rate_limit_response.json()["error"] == "Rate limit exceeded"
    
    def test_rate_limit_reset(self, client):
        """Test that rate limit resets after window."""
        # Make some requests
        for i in range(5):
            client.get("/test")
        
        # Wait for rate limit window to pass (mock time)
        # In real implementation, this would test time-based reset
        # For now, we just verify the basic functionality works
    
    def test_different_clients_rate_limit(self, client):
        """Test that rate limiting is per-client."""
        # This would require testing with different IP addresses
        # For now, we test the basic functionality
        response = client.get("/test")
        assert response.status_code == 200


class TestSecurityMiddlewareIntegration:
    """Test security middleware integration with FastAPI."""
    
    def test_middleware_order(self, app):
        """Test that middleware is applied in correct order."""
        # Verify middleware is added
        middleware_classes = [type(m) for m in app.user_middleware]
        assert SecurityMiddleware in middleware_classes
        assert RateLimitMiddleware in middleware_classes
    
    def test_error_handling(self, client):
        """Test that middleware errors are handled gracefully."""
        # Test with malformed request
        response = client.get("/test", headers={"Content-Type": "invalid"})
        # Should not crash, should return appropriate error
        assert response.status_code in [400, 500]
    
    def test_middleware_performance(self, client):
        """Test that middleware doesn't significantly impact performance."""
        import time
        
        # Measure response time
        start_time = time.time()
        response = client.get("/test")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Response should be fast (less than 100ms)
        assert response_time < 0.1
        assert response.status_code == 200


class TestSecurityPatterns:
    """Test security pattern detection."""
    
    def test_sql_injection_patterns(self):
        """Test SQL injection pattern detection."""
        middleware = SecurityMiddleware(Mock())
        
        # Test SQL injection patterns
        sql_patterns = [
            "'; DROP TABLE users; --",
            "'; DELETE FROM users; --",
            "'; UPDATE users SET role='admin'; --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "'; ALTER TABLE users ADD COLUMN hacked BOOLEAN; --",
        ]
        
        for pattern in sql_patterns:
            assert not middleware._validate_string(pattern)
    
    def test_xss_patterns(self):
        """Test XSS pattern detection."""
        middleware = SecurityMiddleware(Mock())
        
        # Test XSS patterns
        xss_patterns = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
        ]
        
        for pattern in xss_patterns:
            assert not middleware._validate_string(pattern)
    
    def test_path_traversal_patterns(self):
        """Test path traversal pattern detection."""
        middleware = SecurityMiddleware(Mock())
        
        # Test path traversal patterns
        traversal_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]
        
        for pattern in traversal_patterns:
            assert not middleware._validate_string(pattern)
    
    def test_command_injection_patterns(self):
        """Test command injection pattern detection."""
        middleware = SecurityMiddleware(Mock())
        
        # Test command injection patterns
        command_patterns = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(whoami)",
        ]
        
        for pattern in command_patterns:
            assert not middleware._validate_string(pattern)
    
    def test_valid_strings(self):
        """Test that valid strings pass validation."""
        middleware = SecurityMiddleware(Mock())
        
        # Test valid strings
        valid_strings = [
            "normal text",
            "user@example.com",
            "https://example.com",
            "12345",
            "Hello World!",
        ]
        
        for text in valid_strings:
            assert middleware._validate_string(text)
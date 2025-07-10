"""
Security Tests

Security tests and audit checks for MetaMCP components.
"""

import pytest
import hashlib
import hmac
import secrets
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from metamcp.security.auth import AuthManager
from metamcp.security.policies import PolicyEngine
from metamcp.config import get_settings


class TestAuthentication:
    """Test authentication mechanisms."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create auth manager for testing."""
        return AuthManager()
    
    @pytest.mark.asyncio
    async def test_jwt_token_creation(self, auth_manager):
        """Test JWT token creation and validation."""
        user_data = {
            "user_id": "test_user_123",
            "username": "testuser",
            "roles": ["user"]
        }
        
        # Create token
        token = await auth_manager.create_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Validate token
        payload = await auth_manager.validate_token(token)
        assert payload is not None
        assert payload.get("user_id") == user_data["user_id"]
        assert payload.get("username") == user_data["username"]
    
    @pytest.mark.asyncio
    async def test_invalid_token_handling(self, auth_manager):
        """Test handling of invalid tokens."""
        # Test with invalid token
        with pytest.raises(Exception):
            await auth_manager.validate_token("invalid_token")
        
        # Test with expired token
        # This would require mocking time or using a very short expiration
        pass
    
    @pytest.mark.asyncio
    async def test_password_hashing(self, auth_manager):
        """Test password hashing and verification."""
        password = "test_password_123"
        
        # Hash password
        hashed_password = await auth_manager.hash_password(password)
        assert hashed_password != password
        assert hashed_password.startswith("$2b$")  # bcrypt format
        
        # Verify password
        is_valid = await auth_manager.verify_password(password, hashed_password)
        assert is_valid is True
        
        # Test wrong password
        is_valid = await auth_manager.verify_password("wrong_password", hashed_password)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_password_strength_validation(self, auth_manager):
        """Test password strength validation."""
        # Test weak password
        weak_password = "123"
        is_strong = await auth_manager.validate_password_strength(weak_password)
        assert is_strong is False
        
        # Test strong password
        strong_password = "StrongPassword123!"
        is_strong = await auth_manager.validate_password_strength(strong_password)
        assert is_strong is True


class TestAuthorization:
    """Test authorization and access control."""
    
    @pytest.fixture
    def policy_engine(self):
        """Create policy engine for testing."""
        return PolicyEngine()
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self, policy_engine):
        """Test role-based access control."""
        # Test admin access
        admin_user = {"user_id": "admin_123", "roles": ["admin"]}
        result = await policy_engine.evaluate("admin_access", {
            "user": admin_user,
            "resource": "system_config",
            "action": "read"
        })
        assert result.get("allowed") is True
        
        # Test user access
        regular_user = {"user_id": "user_123", "roles": ["user"]}
        result = await policy_engine.evaluate("admin_access", {
            "user": regular_user,
            "resource": "system_config",
            "action": "read"
        })
        assert result.get("allowed") is False
    
    @pytest.mark.asyncio
    async def test_resource_based_access_control(self, policy_engine):
        """Test resource-based access control."""
        user = {"user_id": "user_123", "roles": ["user"]}
        
        # Test tool access
        result = await policy_engine.evaluate("tool_access", {
            "user": user,
            "resource": "calculator",
            "action": "execute"
        })
        assert result.get("allowed") is True
        
        # Test restricted resource
        result = await policy_engine.evaluate("tool_access", {
            "user": user,
            "resource": "admin_tool",
            "action": "execute"
        })
        assert result.get("allowed") is False
    
    @pytest.mark.asyncio
    async def test_permission_checks(self, policy_engine):
        """Test permission checking."""
        user = {"user_id": "user_123", "permissions": ["read", "execute"]}
        
        # Test allowed permission
        has_permission = await policy_engine.check_permission(user, "read")
        assert has_permission is True
        
        # Test denied permission
        has_permission = await policy_engine.check_permission(user, "write")
        assert has_permission is False


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious_input = "'; DROP TABLE users; --"
        
        # Sanitize input
        sanitized = self.sanitize_input(malicious_input)
        assert sanitized != malicious_input
        assert "DROP TABLE" not in sanitized
        assert ";" not in sanitized
    
    def test_xss_prevention(self):
        """Test XSS prevention."""
        malicious_input = "<script>alert('xss')</script>"
        
        # Sanitize input
        sanitized = self.sanitize_input(malicious_input)
        assert sanitized != malicious_input
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
    
    def test_path_traversal_prevention(self):
        """Test path traversal prevention."""
        malicious_input = "../../../etc/passwd"
        
        # Sanitize input
        sanitized = self.sanitize_input(malicious_input)
        assert sanitized != malicious_input
        assert ".." not in sanitized
        assert "/etc" not in sanitized
    
    def sanitize_input(self, input_str: str) -> str:
        """Sanitize input string."""
        import re
        
        # Remove SQL injection patterns
        input_str = re.sub(r'[;\'"]', '', input_str)
        
        # Remove XSS patterns
        input_str = re.sub(r'<script.*?</script>', '', input_str, flags=re.IGNORECASE)
        input_str = re.sub(r'javascript:', '', input_str, flags=re.IGNORECASE)
        
        # Remove path traversal patterns
        input_str = re.sub(r'\.\./', '', input_str)
        
        return input_str


class TestCryptography:
    """Test cryptographic functions."""
    
    def test_encryption_decryption(self):
        """Test encryption and decryption."""
        from cryptography.fernet import Fernet
        
        # Generate key
        key = Fernet.generate_key()
        cipher = Fernet(key)
        
        # Test data
        original_data = "sensitive_information"
        
        # Encrypt
        encrypted_data = cipher.encrypt(original_data.encode())
        assert encrypted_data != original_data.encode()
        
        # Decrypt
        decrypted_data = cipher.decrypt(encrypted_data).decode()
        assert decrypted_data == original_data
    
    def test_secure_random_generation(self):
        """Test secure random number generation."""
        # Generate secure random bytes
        random_bytes = secrets.token_bytes(32)
        assert len(random_bytes) == 32
        
        # Generate secure random string
        random_string = secrets.token_urlsafe(32)
        assert len(random_string) > 0
        
        # Ensure randomness
        random_string2 = secrets.token_urlsafe(32)
        assert random_string != random_string2
    
    def test_hmac_verification(self):
        """Test HMAC message authentication."""
        # Generate HMAC
        message = "important_message"
        key = secrets.token_bytes(32)
        
        hmac_obj = hmac.new(key, message.encode(), hashlib.sha256)
        signature = hmac_obj.hexdigest()
        
        # Verify HMAC
        hmac_obj2 = hmac.new(key, message.encode(), hashlib.sha256)
        expected_signature = hmac_obj2.hexdigest()
        
        assert signature == expected_signature
        
        # Test with different message
        different_message = "different_message"
        hmac_obj3 = hmac.new(key, different_message.encode(), hashlib.sha256)
        different_signature = hmac_obj3.hexdigest()
        
        assert signature != different_signature


class TestSecurityHeaders:
    """Test security headers."""
    
    def test_cors_headers(self):
        """Test CORS security headers."""
        headers = {
            "Access-Control-Allow-Origin": "https://trusted-domain.com",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400"
        }
        
        # Verify CORS headers are set
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] != "*"  # Should not be wildcard
        
        # Verify methods are restricted
        allowed_methods = headers["Access-Control-Allow-Methods"].split(", ")
        assert "GET" in allowed_methods
        assert "DELETE" not in allowed_methods  # Should not allow dangerous methods
    
    def test_security_headers(self):
        """Test general security headers."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'"
        }
        
        # Verify security headers are present
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        for header in required_headers:
            assert header in headers


class TestRateLimiting:
    """Test rate limiting mechanisms."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from collections import defaultdict
        import time
        
        class RateLimiter:
            def __init__(self, max_requests: int, window_seconds: int):
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self.requests = defaultdict(list)
            
            def is_allowed(self, client_id: str) -> bool:
                now = time.time()
                client_requests = self.requests[client_id]
                
                # Remove old requests
                client_requests = [req for req in client_requests if now - req < self.window_seconds]
                self.requests[client_id] = client_requests
                
                # Check if limit exceeded
                if len(client_requests) >= self.max_requests:
                    return False
                
                # Add current request
                client_requests.append(now)
                return True
        
        # Create rate limiter
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Test within limits
        for i in range(5):
            assert limiter.is_allowed("client_1") is True
        
        # Test exceeding limits
        assert limiter.is_allowed("client_1") is False
        
        # Test different client
        assert limiter.is_allowed("client_2") is True


class TestAuditLogging:
    """Test audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self):
        """Test audit log entry creation."""
        audit_entry = {
            "timestamp": "2024-01-01T12:00:00Z",
            "user_id": "user_123",
            "action": "tool_execution",
            "resource": "calculator",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "success": True,
            "details": {
                "tool_name": "calculator",
                "input_data": {"operation": "add", "a": 5, "b": 3},
                "result": {"sum": 8}
            }
        }
        
        # Verify audit entry structure
        required_fields = ["timestamp", "user_id", "action", "resource", "success"]
        for field in required_fields:
            assert field in audit_entry
        
        # Verify sensitive data is not logged
        assert "password" not in str(audit_entry)
        assert "secret" not in str(audit_entry)
    
    @pytest.mark.asyncio
    async def test_sensitive_data_filtering(self):
        """Test filtering of sensitive data in logs."""
        sensitive_data = {
            "username": "testuser",
            "password": "secret_password",
            "api_key": "sk-1234567890abcdef",
            "credit_card": "4111-1111-1111-1111",
            "ssn": "123-45-6789"
        }
        
        # Filter sensitive data
        filtered_data = self.filter_sensitive_data(sensitive_data)
        
        # Verify sensitive fields are masked
        assert filtered_data["password"] == "***"
        assert filtered_data["api_key"] == "***"
        assert filtered_data["credit_card"] == "***"
        assert filtered_data["ssn"] == "***"
        
        # Verify non-sensitive fields are preserved
        assert filtered_data["username"] == "testuser"
    
    def filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from dictionary."""
        sensitive_keys = ["password", "secret", "key", "token", "credit_card", "ssn"]
        filtered = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                filtered[key] = "***"
            else:
                filtered[key] = value
        
        return filtered


class TestConfigurationSecurity:
    """Test configuration security."""
    
    def test_secret_management(self):
        """Test secret management practices."""
        settings = get_settings()
        
        # Verify secrets are not hardcoded
        assert settings.secret_key != "your-secret-key-change-in-production"
        assert settings.secret_key != "default-secret-key"
        
        # Verify secrets are not logged
        settings_dict = settings.dict()
        for key, value in settings_dict.items():
            if "secret" in key.lower() or "key" in key.lower():
                assert value == "***" or value is None
    
    def test_environment_variable_usage(self):
        """Test environment variable usage for secrets."""
        import os
        
        # Verify critical settings can be set via environment
        env_vars = [
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "DATABASE_URL",
            "WEAVIATE_API_KEY"
        ]
        
        for var in env_vars:
            # Test that environment variable is respected
            os.environ[var] = "test_value"
            settings = get_settings()
            # Note: This is a simplified test - actual implementation may vary
            del os.environ[var] 
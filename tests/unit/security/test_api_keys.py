"""
Tests for API Key Management System
"""

from datetime import datetime, timedelta

import pytest

from metamcp.security.api_keys import APIKey, APIKeyManager, get_api_key_manager


class TestAPIKeyManager:
    """Test API Key Manager functionality."""

    @pytest.fixture
    async def api_key_manager(self):
        """Create API key manager instance."""
        manager = APIKeyManager()
        await manager.initialize()
        yield manager
        await manager.shutdown()

    def test_generate_api_key(self, api_key_manager):
        """Test API key generation."""
        # Generate API key
        api_key = api_key_manager.generate_api_key(
            name="Test Service",
            owner="test-service",
            permissions=["read", "write"],
            expires_in_days=30,
        )

        # Check key format
        assert api_key.startswith("mcp_")
        assert len(api_key) > 40  # Should be reasonably long

        # Check that key is stored
        assert len(api_key_manager.keys) == 1

        # Get the stored key record
        key_record = list(api_key_manager.keys.values())[0]
        assert key_record.name == "Test Service"
        assert key_record.owner == "test-service"
        assert key_record.permissions == ["read", "write"]
        assert key_record.is_active is True

    def test_validate_api_key(self, api_key_manager):
        """Test API key validation."""
        # Generate a key
        api_key = api_key_manager.generate_api_key(
            name="Test Service", owner="test-service", permissions=["read"]
        )

        # Validate the key
        key_record = api_key_manager.validate_api_key(api_key)
        assert key_record is not None
        assert key_record.name == "Test Service"

        # Test invalid key
        invalid_key = api_key_manager.validate_api_key("invalid_key")
        assert invalid_key is None

        # Test key without prefix
        invalid_key = api_key_manager.validate_api_key("some_random_key")
        assert invalid_key is None

    def test_check_permission(self, api_key_manager):
        """Test permission checking."""
        # Generate key with specific permissions
        api_key = api_key_manager.generate_api_key(
            name="Test Service", owner="test-service", permissions=["read", "write"]
        )

        # Check permissions
        assert api_key_manager.check_permission(api_key, "read") is True
        assert api_key_manager.check_permission(api_key, "write") is True
        assert api_key_manager.check_permission(api_key, "admin") is False

        # Test with invalid key
        assert api_key_manager.check_permission("invalid_key", "read") is False

    def test_revoke_api_key(self, api_key_manager):
        """Test API key revocation."""
        # Generate a key
        api_key = api_key_manager.generate_api_key(
            name="Test Service", owner="test-service", permissions=["read"]
        )

        # Get key ID
        key_id = list(api_key_manager.keys.keys())[0]

        # Revoke the key
        success = api_key_manager.revoke_api_key(key_id)
        assert success is True

        # Check that key is no longer active
        key_record = api_key_manager.keys[key_id]
        assert key_record.is_active is False

        # Test revoking non-existent key
        success = api_key_manager.revoke_api_key("non_existent")
        assert success is False

    def test_list_api_keys(self, api_key_manager):
        """Test listing API keys."""
        # Generate multiple keys
        api_key_manager.generate_api_key("Service A", "service-a", ["read"])
        api_key_manager.generate_api_key("Service B", "service-b", ["write"])

        # List all keys
        keys = api_key_manager.list_api_keys()
        assert len(keys) == 2

        # List keys for specific owner
        keys = api_key_manager.list_api_keys(owner="service-a")
        assert len(keys) == 1
        assert keys[0]["owner"] == "service-a"

    def test_key_expiration(self, api_key_manager):
        """Test API key expiration."""
        # Generate key with short expiration
        api_key = api_key_manager.generate_api_key(
            name="Test Service",
            owner="test-service",
            permissions=["read"],
            expires_in_days=1,
        )

        # Key should be valid initially
        key_record = api_key_manager.validate_api_key(api_key)
        assert key_record is not None

        # Manually set expiration to past
        key_record.expires_at = datetime.utcnow() - timedelta(days=1)

        # Key should now be invalid
        key_record = api_key_manager.validate_api_key(api_key)
        assert key_record is None

    def test_last_used_tracking(self, api_key_manager):
        """Test last used timestamp tracking."""
        # Generate a key
        api_key = api_key_manager.generate_api_key(
            name="Test Service", owner="test-service", permissions=["read"]
        )

        # Get key record
        key_record = api_key_manager.validate_api_key(api_key)
        assert key_record.last_used is not None

        # Store original last_used
        original_last_used = key_record.last_used

        # Wait a bit and validate again
        import time

        time.sleep(0.1)

        # Validate again
        key_record = api_key_manager.validate_api_key(api_key)
        assert key_record.last_used > original_last_used

    def test_global_instance(self):
        """Test global API key manager instance."""
        # Get global instance
        manager1 = get_api_key_manager()
        manager2 = get_api_key_manager()

        # Should be the same instance
        assert manager1 is manager2


class TestAPIKey:
    """Test API Key model."""

    def test_api_key_creation(self):
        """Test API Key object creation."""
        key = APIKey(
            key_id="test_key_123",
            key_hash="abc123",
            name="Test Key",
            owner="test-owner",
            permissions=["read"],
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used=None,
            is_active=True,
        )

        assert key.key_id == "test_key_123"
        assert key.name == "Test Key"
        assert key.owner == "test-owner"
        assert key.permissions == ["read"]
        assert key.is_active is True

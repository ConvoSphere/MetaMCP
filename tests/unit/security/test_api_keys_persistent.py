"""
Tests for persistent API Key management.

This module tests the database-backed API key management functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from metamcp.exceptions import APIKeyError
from metamcp.security.api_keys import APIKey, APIKeyManager


class TestAPIKeyManagerPersistent:
    """Test API Key Manager with database persistence."""

    @pytest.fixture
    async def api_key_manager(self):
        """Create API key manager instance."""
        manager = APIKeyManager()
        # Mock session factory
        manager._session_factory = AsyncMock()
        manager._initialized = True
        return manager

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = AsyncMock()
        return session

    async def test_initialize_success(self, api_key_manager):
        """Test successful initialization."""
        # Reset initialization
        api_key_manager._initialized = False

        # Mock session factory
        mock_session_factory = AsyncMock()
        api_key_manager._session_factory = mock_session_factory

        # Mock session
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        # Mock successful query
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        await api_key_manager.initialize()

        assert api_key_manager._initialized is True
        mock_session_factory.assert_called_once()

    async def test_initialize_failure(self, api_key_manager):
        """Test initialization failure."""
        # Reset initialization
        api_key_manager._initialized = False

        # Mock session factory that raises exception
        mock_session_factory = AsyncMock()
        mock_session_factory.side_effect = Exception("Database connection failed")
        api_key_manager._session_factory = mock_session_factory

        with pytest.raises(APIKeyError, match="Failed to initialize API key manager"):
            await api_key_manager.initialize()

    async def test_generate_api_key_success(self, api_key_manager, mock_session):
        """Test successful API key generation."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Generate API key
        api_key = api_key_manager.generate_api_key(
            name="test_key",
            owner="test_user",
            permissions=["read", "write"],
            expires_in_days=30,
        )

        # Verify API key format
        assert api_key.startswith("mcp_")
        assert len(api_key) > 32

        # Verify database save was called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_generate_api_key_not_initialized(self):
        """Test API key generation when not initialized."""
        manager = APIKeyManager()

        with pytest.raises(APIKeyError, match="API Key Manager not initialized"):
            manager.generate_api_key("test", "user", ["read"])

    async def test_validate_api_key_success(self, api_key_manager, mock_session):
        """Test successful API key validation."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock database result
        mock_key_record = MagicMock()
        mock_key_record.id = "test_id"
        mock_key_record.key_hash = "test_hash"
        mock_key_record.name = "test_key"
        mock_key_record.user_id = "test_user"
        mock_key_record.permissions = ["read", "write"]
        mock_key_record.created_at = datetime.utcnow()
        mock_key_record.expires_at = datetime.utcnow() + timedelta(days=30)
        mock_key_record.last_used = None
        mock_key_record.is_active = True

        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_key_record
        )

        # Test validation (we need to mock the hash generation)
        import hashlib

        test_key = "mcp_test_key_123"
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()

        # Mock the hash to match our test
        mock_key_record.key_hash = key_hash

        result = await api_key_manager.validate_api_key(test_key)

        assert result is not None
        assert result.key_id == "test_id"
        assert result.name == "test_key"
        assert result.owner == "test_user"
        assert result.permissions == ["read", "write"]

    async def test_validate_api_key_expired(self, api_key_manager, mock_session):
        """Test validation of expired API key."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock expired key record
        mock_key_record = MagicMock()
        mock_key_record.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
        mock_key_record.is_active = True

        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_key_record
        )

        result = await api_key_manager.validate_api_key("mcp_test_key")

        assert result is None

    async def test_validate_api_key_inactive(self, api_key_manager, mock_session):
        """Test validation of inactive API key."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock inactive key record
        mock_key_record = MagicMock()
        mock_key_record.is_active = False

        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_key_record
        )

        result = await api_key_manager.validate_api_key("mcp_test_key")

        assert result is None

    async def test_validate_api_key_not_found(self, api_key_manager, mock_session):
        """Test validation of non-existent API key."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock no result found
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await api_key_manager.validate_api_key("mcp_nonexistent_key")

        assert result is None

    async def test_revoke_api_key_success(self, api_key_manager, mock_session):
        """Test successful API key revocation."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock key record
        mock_key_record = MagicMock()
        mock_key_record.is_active = True

        mock_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_key_record
        )

        result = await api_key_manager.revoke_api_key("test_key_id")

        assert result is True
        assert mock_key_record.is_active is False
        mock_session.commit.assert_called_once()

    async def test_revoke_api_key_not_found(self, api_key_manager, mock_session):
        """Test revocation of non-existent API key."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock no result found
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await api_key_manager.revoke_api_key("nonexistent_key_id")

        assert result is False

    async def test_list_api_keys_success(self, api_key_manager, mock_session):
        """Test successful API key listing."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock key records
        mock_key_record1 = MagicMock()
        mock_key_record1.id = "key1"
        mock_key_record1.name = "Test Key 1"
        mock_key_record1.user_id = "user1"
        mock_key_record1.permissions = ["read"]
        mock_key_record1.created_at = datetime.utcnow()
        mock_key_record1.expires_at = datetime.utcnow() + timedelta(days=30)
        mock_key_record1.last_used = None
        mock_key_record1.is_active = True

        mock_key_record2 = MagicMock()
        mock_key_record2.id = "key2"
        mock_key_record2.name = "Test Key 2"
        mock_key_record2.user_id = "user2"
        mock_key_record2.permissions = ["write"]
        mock_key_record2.created_at = datetime.utcnow()
        mock_key_record2.expires_at = None
        mock_key_record2.last_used = datetime.utcnow()
        mock_key_record2.is_active = True

        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            mock_key_record1,
            mock_key_record2,
        ]

        result = await api_key_manager.list_api_keys()

        assert len(result) == 2
        assert result[0]["key_id"] == "key1"
        assert result[0]["name"] == "Test Key 1"
        assert result[1]["key_id"] == "key2"
        assert result[1]["name"] == "Test Key 2"

    async def test_list_api_keys_filtered(self, api_key_manager, mock_session):
        """Test API key listing with owner filter."""
        # Mock session factory
        api_key_manager._session_factory.return_value.__aenter__.return_value = (
            mock_session
        )

        # Mock key record
        mock_key_record = MagicMock()
        mock_key_record.id = "key1"
        mock_key_record.name = "Test Key"
        mock_key_record.user_id = "user1"
        mock_key_record.permissions = ["read"]
        mock_key_record.created_at = datetime.utcnow()
        mock_key_record.expires_at = None
        mock_key_record.last_used = None
        mock_key_record.is_active = True

        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            mock_key_record
        ]

        result = await api_key_manager.list_api_keys(owner="user1")

        assert len(result) == 1
        assert result[0]["key_id"] == "key1"
        assert result[0]["owner"] == "user1"

    async def test_check_permission_success(self, api_key_manager):
        """Test permission checking."""
        # Mock validate_api_key to return a key with permissions
        mock_key = APIKey(
            key_id="test_id",
            key_hash="test_hash",
            name="test_key",
            owner="test_user",
            permissions=["read", "write"],
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used=None,
            is_active=True,
        )

        api_key_manager.validate_api_key = AsyncMock(return_value=mock_key)

        result = api_key_manager.check_permission("mcp_test_key", "read")

        assert result is True

    async def test_check_permission_failure(self, api_key_manager):
        """Test permission checking failure."""
        # Mock validate_api_key to return None
        api_key_manager.validate_api_key = AsyncMock(return_value=None)

        result = api_key_manager.check_permission("mcp_invalid_key", "read")

        assert result is False

    async def test_shutdown(self, api_key_manager):
        """Test API key manager shutdown."""
        await api_key_manager.shutdown()

        assert api_key_manager._initialized is False

    def test_is_initialized_property(self, api_key_manager):
        """Test is_initialized property."""
        assert api_key_manager.is_initialized is True

        api_key_manager._initialized = False
        assert api_key_manager.is_initialized is False

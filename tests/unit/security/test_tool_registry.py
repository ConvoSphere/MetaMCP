"""
Tests for Tool Registry Security System
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from metamcp.security.tool_registry import (
    ToolRegistrySecurity,
    Developer,
    get_tool_registry_security,
)


class TestToolRegistrySecurity:
    """Test Tool Registry Security functionality."""

    @pytest.fixture
    async def tool_registry_security(self):
        """Create tool registry security instance."""
        security = ToolRegistrySecurity()
        await security.initialize()
        yield security
        await security.shutdown()

    def test_register_developer(self, tool_registry_security):
        """Test developer registration."""
        # Register a developer
        developer_id = tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )

        # Check developer was registered
        assert developer_id is not None
        assert developer_id.startswith("dev_testdev_")

        # Check developer info
        developer_info = tool_registry_security.get_developer_info(developer_id)
        assert developer_info is not None
        assert developer_info["username"] == "testdev"
        assert developer_info["email"] == "test@example.com"
        assert developer_info["organization"] == "Test Org"
        assert developer_info["is_verified"] is False
        assert developer_info["is_active"] is True

    def test_duplicate_developer_registration(self, tool_registry_security):
        """Test duplicate developer registration."""
        # Register first developer
        tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )

        # Try to register with same email
        with pytest.raises(Exception) as exc_info:
            tool_registry_security.register_developer(
                username="testdev2", email="test@example.com", organization="Test Org 2"
            )
        assert "already registered" in str(exc_info.value)

        # Try to register with same username
        with pytest.raises(Exception) as exc_info:
            tool_registry_security.register_developer(
                username="testdev", email="test2@example.com", organization="Test Org 2"
            )
        assert "already registered" in str(exc_info.value)

    def test_verify_developer(self, tool_registry_security):
        """Test developer verification."""
        # Register a developer
        developer_id = tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )

        # Developer should not be verified initially
        developer_info = tool_registry_security.get_developer_info(developer_id)
        assert developer_info["is_verified"] is False

        # Verify the developer
        success = tool_registry_security.verify_developer(developer_id)
        assert success is True

        # Developer should now be verified
        developer_info = tool_registry_security.get_developer_info(developer_id)
        assert developer_info["is_verified"] is True

        # Test verifying non-existent developer
        success = tool_registry_security.verify_developer("non_existent")
        assert success is False

    def test_can_register_tool(self, tool_registry_security):
        """Test tool registration permissions."""
        # Register a developer
        developer_id = tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )

        # Unverified developer should not be able to register tools
        can_register = tool_registry_security.can_register_tool(developer_id)
        assert can_register is False

        # Verify the developer
        tool_registry_security.verify_developer(developer_id)

        # Verified developer should be able to register tools
        can_register = tool_registry_security.can_register_tool(developer_id)
        assert can_register is True

        # Test non-existent developer
        can_register = tool_registry_security.can_register_tool("non_existent")
        assert can_register is False

    def test_register_tool_creation(self, tool_registry_security):
        """Test tool creation registration."""
        # Register and verify a developer
        developer_id = tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )
        tool_registry_security.verify_developer(developer_id)

        # Register tool creation
        tool_id = "test_tool_123"
        success = tool_registry_security.register_tool_creation(developer_id, tool_id)
        assert success is True

        # Check that tool is registered
        developer_info = tool_registry_security.get_developer_info(developer_id)
        assert tool_id in developer_info["tools_created"]

        # Test registering same tool again
        success = tool_registry_security.register_tool_creation(developer_id, tool_id)
        assert success is True  # Should not fail, just not duplicate

        # Test registering tool for non-existent developer
        success = tool_registry_security.register_tool_creation(
            "non_existent", "tool_456"
        )
        assert success is False

    def test_can_manage_tool(self, tool_registry_security):
        """Test tool management permissions."""
        # Register and verify a developer
        developer_id = tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )
        tool_registry_security.verify_developer(developer_id)

        # Register tool creation
        tool_id = "test_tool_123"
        tool_registry_security.register_tool_creation(developer_id, tool_id)

        # Developer should be able to manage their own tool
        can_manage = tool_registry_security.can_manage_tool(developer_id, tool_id)
        assert can_manage is True

        # Developer should not be able to manage other tools
        can_manage = tool_registry_security.can_manage_tool(developer_id, "other_tool")
        assert can_manage is False

    def test_validate_tool_registration(self, tool_registry_security):
        """Test tool registration validation."""
        # Valid tool data
        valid_tool = {
            "name": "Test Tool",
            "description": "A test tool",
            "version": "1.0.0",
            "author": "testdev",
            "security_level": 1,
        }

        is_valid = tool_registry_security.validate_tool_registration(valid_tool)
        assert is_valid is True

        # Invalid tool data - missing required field
        invalid_tool = {
            "name": "Test Tool",
            "description": "A test tool",
            "version": "1.0.0",
            # Missing author
        }

        is_valid = tool_registry_security.validate_tool_registration(invalid_tool)
        assert is_valid is False

        # Invalid tool data - invalid security level
        invalid_tool = {
            "name": "Test Tool",
            "description": "A test tool",
            "version": "1.0.0",
            "author": "testdev",
            "security_level": 15,  # Too high
        }

        is_valid = tool_registry_security.validate_tool_registration(invalid_tool)
        assert is_valid is False

        # Invalid tool data - invalid version
        invalid_tool = {
            "name": "Test Tool",
            "description": "A test tool",
            "version": "invalid_version",
            "author": "testdev",
        }

        is_valid = tool_registry_security.validate_tool_registration(invalid_tool)
        assert is_valid is False

    def test_list_developers(self, tool_registry_security):
        """Test listing developers."""
        # Register multiple developers
        dev1_id = tool_registry_security.register_developer(
            "dev1", "dev1@test.com", "Org1"
        )
        dev2_id = tool_registry_security.register_developer(
            "dev2", "dev2@test.com", "Org2"
        )

        # Verify one developer
        tool_registry_security.verify_developer(dev1_id)

        # List all developers
        developers = tool_registry_security.list_developers()
        assert len(developers) == 2

        # List only verified developers
        verified_developers = tool_registry_security.list_developers(verified_only=True)
        assert len(verified_developers) == 1
        assert verified_developers[0]["username"] == "dev1"

    def test_deactivate_developer(self, tool_registry_security):
        """Test developer deactivation."""
        # Register a developer
        developer_id = tool_registry_security.register_developer(
            username="testdev", email="test@example.com", organization="Test Org"
        )

        # Developer should be active initially
        developer_info = tool_registry_security.get_developer_info(developer_id)
        assert developer_info["is_active"] is True

        # Deactivate developer
        success = tool_registry_security.deactivate_developer(developer_id)
        assert success is True

        # Developer should now be inactive
        developer_info = tool_registry_security.get_developer_info(developer_id)
        assert developer_info["is_active"] is False

        # Test deactivating non-existent developer
        success = tool_registry_security.deactivate_developer("non_existent")
        assert success is False

    def test_global_instance(self):
        """Test global tool registry security instance."""
        # Get global instance
        security1 = get_tool_registry_security()
        security2 = get_tool_registry_security()

        # Should be the same instance
        assert security1 is security2


class TestDeveloper:
    """Test Developer model."""

    def test_developer_creation(self):
        """Test Developer object creation."""
        developer = Developer(
            developer_id="dev_123",
            username="testdev",
            email="test@example.com",
            organization="Test Org",
            is_verified=False,
            registration_date=datetime.utcnow(),
            tools_created=[],
            is_active=True,
        )

        assert developer.developer_id == "dev_123"
        assert developer.username == "testdev"
        assert developer.email == "test@example.com"
        assert developer.organization == "Test Org"
        assert developer.is_verified is False
        assert developer.is_active is True
        assert developer.tools_created == []

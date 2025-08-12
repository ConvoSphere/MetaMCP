"""
Integration Tests for Security Features

This module tests the integration of all security features:
- API Key Management
- Tool Registry Security
- Resource Limits
- API Versioning
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from metamcp.security.api_keys import get_api_key_manager
from metamcp.security.tool_registry import get_tool_registry_security
from metamcp.security.resource_limits import get_resource_limit_manager, ResourceLimits
from metamcp.api.versioning import get_api_version_manager


class TestSecurityIntegration:
    """Integration tests for security features."""

    @pytest.fixture
    async def security_managers(self):
        """Initialize all security managers."""
        # Initialize API Key Manager
        api_key_manager = get_api_key_manager()
        await api_key_manager.initialize()

        # Initialize Tool Registry Security
        tool_registry = get_tool_registry_security()
        await tool_registry.initialize()

        # Initialize Resource Limit Manager
        resource_manager = get_resource_limit_manager()
        await resource_manager.initialize()

        # Initialize API Version Manager
        version_manager = get_api_version_manager()
        await version_manager.initialize()

        yield {
            "api_key_manager": api_key_manager,
            "tool_registry": tool_registry,
            "resource_manager": resource_manager,
            "version_manager": version_manager,
        }

        # Cleanup
        await api_key_manager.shutdown()
        await tool_registry.shutdown()
        await resource_manager.shutdown()
        await version_manager.shutdown()

    async def test_complete_workflow(self, security_managers):
        """Test complete security workflow."""
        api_key_manager = security_managers["api_key_manager"]
        tool_registry = security_managers["tool_registry"]
        resource_manager = security_managers["resource_manager"]
        version_manager = security_managers["version_manager"]

        # Step 1: Register a developer
        developer_id = tool_registry.register_developer(
            username="integration_test_dev",
            email="integration@test.com",
            organization="Integration Test Org",
        )
        assert developer_id is not None

        # Step 2: Verify the developer
        success = tool_registry.verify_developer(developer_id)
        assert success is True

        # Step 3: Generate API key for the developer
        api_key = api_key_manager.generate_api_key(
            name="Integration Test Key",
            owner=developer_id,
            permissions=["resource_management", "tool_registry"],
            expires_in_days=30,
        )
        assert api_key.startswith("mcp_")

        # Step 4: Validate API key
        key_record = api_key_manager.validate_api_key(api_key)
        assert key_record is not None
        assert key_record.owner == developer_id

        # Step 5: Check permissions
        assert api_key_manager.check_permission(api_key, "resource_management") is True
        assert api_key_manager.check_permission(api_key, "tool_registry") is True
        assert api_key_manager.check_permission(api_key, "admin") is False

        # Step 6: Start a tool execution with resource limits
        custom_limits = ResourceLimits(
            cpu_time_soft=10,
            cpu_time_hard=20,
            memory_usage_soft=100,
            memory_usage_hard=200,
        )

        execution_id = resource_manager.start_execution(
            tool_id="integration_test_tool",
            user_id=developer_id,
            custom_limits=custom_limits,
        )
        assert execution_id is not None

        # Step 7: Update execution metrics
        success = resource_manager.update_execution_metrics(
            execution_id, cpu_time=15.0, memory_usage=150.0, api_calls=25
        )
        assert success is True

        # Step 8: Check soft limits (should be exceeded)
        soft_violations = resource_manager.check_soft_limits(execution_id)
        assert soft_violations["cpu_time"] is True
        assert soft_violations["memory_usage"] is True

        # Step 9: End execution
        success = resource_manager.end_execution(execution_id, status="completed")
        assert success is True

        # Step 10: Register tool creation
        tool_id = "integration_test_tool_123"
        success = tool_registry.register_tool_creation(developer_id, tool_id)
        assert success is True

        # Step 11: Verify developer can manage their tool
        can_manage = tool_registry.can_manage_tool(developer_id, tool_id)
        assert can_manage is True

        # Step 12: Check API versioning
        latest_version = version_manager.get_latest_version()
        assert latest_version is not None

        active_versions = version_manager.get_active_versions()
        assert len(active_versions) > 0

    async def test_security_violations(self, security_managers):
        """Test security violation scenarios."""
        api_key_manager = security_managers["api_key_manager"]
        tool_registry = security_managers["tool_registry"]
        resource_manager = security_managers["resource_manager"]

        # Test 1: Unverified developer cannot register tools
        developer_id = tool_registry.register_developer(
            username="unverified_dev",
            email="unverified@test.com",
            organization="Test Org",
        )

        can_register = tool_registry.can_register_tool(developer_id)
        assert can_register is False

        # Test 2: Invalid API key has no permissions
        assert api_key_manager.check_permission("invalid_key", "read") is False

        # Test 3: Resource limits are enforced
        execution_id = resource_manager.start_execution(
            tool_id="test_tool", user_id="user_123"
        )

        # Exceed hard limits
        resource_manager.update_execution_metrics(
            execution_id,
            cpu_time=100.0,  # Exceeds default hard limit of 60
            memory_usage=2048.0,  # Exceeds default hard limit of 1024
        )

        hard_violations = resource_manager.check_hard_limits(execution_id)
        assert hard_violations["cpu_time"] is True
        assert hard_violations["memory_usage"] is True

    async def test_concurrent_executions(self, security_managers):
        """Test concurrent execution limits."""
        resource_manager = security_managers["resource_manager"]

        # Start multiple executions for same user
        execution_ids = []
        for i in range(12):  # Exceeds hard limit of 10
            execution_id = resource_manager.start_execution(
                tool_id=f"tool_{i}", user_id="user_123"
            )
            execution_ids.append(execution_id)

        # Check that hard limit is exceeded for all executions
        for execution_id in execution_ids:
            hard_violations = resource_manager.check_hard_limits(execution_id)
            assert hard_violations["concurrent_executions"] is True

    async def test_api_key_expiration(self, security_managers):
        """Test API key expiration."""
        api_key_manager = security_managers["api_key_manager"]

        # Generate key with short expiration
        api_key = api_key_manager.generate_api_key(
            name="Short-lived Key",
            owner="test_owner",
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

    async def test_tool_validation(self, security_managers):
        """Test tool registration validation."""
        tool_registry = security_managers["tool_registry"]

        # Valid tool
        valid_tool = {
            "name": "Valid Tool",
            "description": "A valid tool",
            "version": "1.0.0",
            "author": "testdev",
            "security_level": 1,
        }
        assert tool_registry.validate_tool_registration(valid_tool) is True

        # Invalid tool - missing required field
        invalid_tool = {
            "name": "Invalid Tool",
            "description": "An invalid tool",
            "version": "1.0.0",
            # Missing author
        }
        assert tool_registry.validate_tool_registration(invalid_tool) is False

        # Invalid tool - invalid security level
        invalid_tool = {
            "name": "Invalid Tool",
            "description": "An invalid tool",
            "version": "1.0.0",
            "author": "testdev",
            "security_level": 15,  # Too high
        }
        assert tool_registry.validate_tool_registration(invalid_tool) is False

    async def test_version_lifecycle(self, security_managers):
        """Test API version lifecycle."""
        version_manager = security_managers["version_manager"]

        # Create a test version
        from metamcp.api.versioning import APIVersion, VersionStatus

        test_version = APIVersion(
            version="test_v1.0",
            status=VersionStatus.ACTIVE,
            release_date=datetime.utcnow(),
            description="Test version for lifecycle",
        )

        version_manager.register_version(test_version)

        # Test deprecation
        success = version_manager.deprecate_version("test_v1.0")
        assert success is True

        version_info = version_manager.get_version_info("test_v1.0")
        assert version_info["is_deprecated"] is True

        # Test sunset
        success = version_manager.sunset_version("test_v1.0")
        assert success is True

        version_info = version_manager.get_version_info("test_v1.0")
        assert version_info["is_sunset"] is True

        # Version should no longer be valid
        is_valid = version_manager.validate_version("test_v1.0")
        assert is_valid is False

    async def test_error_handling(self, security_managers):
        """Test error handling scenarios."""
        api_key_manager = security_managers["api_key_manager"]
        tool_registry = security_managers["tool_registry"]
        resource_manager = security_managers["resource_manager"]

        # Test 1: Non-existent execution
        info = resource_manager.get_execution_info("non_existent")
        assert info is None

        # Test 2: Non-existent developer
        info = tool_registry.get_developer_info("non_existent")
        assert info is None

        # Test 3: Revoke non-existent API key
        success = api_key_manager.revoke_api_key("non_existent")
        assert success is False

        # Test 4: End non-existent execution
        success = resource_manager.end_execution("non_existent", "completed")
        assert success is False

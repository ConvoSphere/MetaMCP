"""
Tests for Advanced Policy Engine Features

This module tests the advanced policy engine features including
predefined policies, versioning, IP filtering, and rate limiting.
"""

from unittest.mock import MagicMock

import pytest

from metamcp.config import PolicyEngineType
from metamcp.security.policies import PolicyEngine
from metamcp.security.policy_tester import (
    PolicyTestCase,
    PolicyTester,
    PolicyTestResult,
)
from metamcp.security.rate_limiting import (
    RateLimitConfig,
    RateLimiter,
    RateLimitStrategy,
)


class TestPolicyEngineAdvanced:
    """Test advanced policy engine features."""

    @pytest.fixture
    async def policy_engine(self):
        """Create a policy engine instance."""
        engine = PolicyEngine(PolicyEngineType.INTERNAL)
        await engine.initialize()
        return engine

    @pytest.fixture
    def mock_opa_response(self):
        """Mock OPA response."""
        return {"result": True}

    async def test_predefined_policies_loaded(self, policy_engine):
        """Test that predefined policies are loaded."""
        # Check that predefined policies are loaded
        assert "tool_access" in policy_engine.active_policies
        assert "rate_limiting" in policy_engine.active_policies
        assert "data_access" in policy_engine.active_policies
        assert "ip_filtering" in policy_engine.active_policies
        assert "resource_quota" in policy_engine.active_policies

    async def test_policy_versioning(self, policy_engine):
        """Test policy versioning functionality."""
        # Create a new policy
        policy_content = """
        package test.policy
        
        default allow = false
        
        allow {
            input.user.role == "admin"
        }
        """

        version_id = await policy_engine.create_policy(
            "test_policy", policy_content, "Test policy for versioning", "test_user"
        )

        assert version_id is not None
        assert "test_policy" in policy_engine.policy_versions

        # Update the policy
        updated_content = """
        package test.policy
        
        default allow = false
        
        allow {
            input.user.role == "admin"
        }
        
        allow {
            input.user.role == "user"
            input.action == "read"
        }
        """

        new_version_id = await policy_engine.update_policy(
            "test_policy", updated_content, "Updated test policy", "test_user"
        )

        assert new_version_id != version_id
        assert len(policy_engine.policy_versions["test_policy"]) == 2

    async def test_ip_filtering(self, policy_engine):
        """Test IP filtering functionality."""
        # Add IP to whitelist
        await policy_engine.add_ip_to_whitelist("192.168.1.100")
        await policy_engine.add_ip_to_blacklist("10.0.0.50")

        # Test whitelist
        assert await policy_engine._check_ip_access("192.168.1.100") == True
        assert await policy_engine._check_ip_access("192.168.1.101") == False

        # Test blacklist
        assert await policy_engine._check_ip_access("10.0.0.50") == False

        # Test normal IP
        assert await policy_engine._check_ip_access("172.16.0.1") == True

        # Remove IPs
        await policy_engine.remove_ip_from_whitelist("192.168.1.100")
        await policy_engine.remove_ip_from_blacklist("10.0.0.50")

        # Test after removal
        assert await policy_engine._check_ip_access("192.168.1.100") == True
        assert await policy_engine._check_ip_access("10.0.0.50") == True

    async def test_rate_limiting_integration(self, policy_engine):
        """Test rate limiting integration with policy engine."""
        # Test rate limiting with context
        context = {"rate_limit_key": "test_user", "limit": 5}

        # Make multiple requests
        for i in range(5):
            result = await policy_engine.check_access(
                "test_user", "tool:calculator", "read", context
            )
            assert result == True

        # Next request should be rate limited
        result = await policy_engine.check_access(
            "test_user", "tool:calculator", "read", context
        )
        assert result == False

    async def test_resource_quota_integration(self, policy_engine):
        """Test resource quota integration with policy engine."""
        # Test resource quota with context
        context = {"quota_key": "test_user", "usage": 950, "limit": 1000}

        # Should be allowed
        result = await policy_engine.check_access(
            "test_user", "data:user:profile", "read", context
        )
        assert result == True

        # Exceed quota
        context["usage"] = 1100
        result = await policy_engine.check_access(
            "test_user", "data:user:profile", "read", context
        )
        assert result == False

    async def test_advanced_access_check_with_context(self, policy_engine):
        """Test advanced access checking with full context."""
        context = {
            "ip": "192.168.1.100",
            "rate_limit_key": "user1",
            "limit": 10,
            "quota_key": "user1",
            "usage": 500,
            "limit": 1000,
        }

        # Add IP to whitelist
        await policy_engine.add_ip_to_whitelist("192.168.1.100")

        # Test access with all context
        result = await policy_engine.check_access(
            "user1", "tool:calculator", "read", context
        )
        assert result == True

    async def test_policy_activation(self, policy_engine):
        """Test policy version activation."""
        # Create multiple versions
        await policy_engine.create_policy(
            "activation_test", "package test\nallow = true", "Version 1", "test_user"
        )

        await policy_engine.create_policy(
            "activation_test", "package test\nallow = false", "Version 2", "test_user"
        )

        # Get versions
        versions = await policy_engine.get_policy_versions("activation_test")
        assert len(versions) == 2

        # Activate first version
        success = await policy_engine.activate_policy_version(
            "activation_test", versions[0].version
        )
        assert success == True

    async def test_get_ip_lists(self, policy_engine):
        """Test getting IP lists."""
        # Add some IPs
        await policy_engine.add_ip_to_whitelist("192.168.1.100")
        await policy_engine.add_ip_to_blacklist("10.0.0.50")

        # Get lists
        lists = await policy_engine.get_ip_lists()

        assert "192.168.1.100" in lists["whitelist"]
        assert "10.0.0.50" in lists["blacklist"]

    async def test_policy_engine_shutdown(self, policy_engine):
        """Test policy engine shutdown."""
        await policy_engine.shutdown()
        assert policy_engine.is_initialized == True  # Should still be initialized


class TestPolicyTester:
    """Test policy testing functionality."""

    @pytest.fixture
    async def policy_engine(self):
        """Create a policy engine instance."""
        engine = PolicyEngine(PolicyEngineType.INTERNAL)
        await engine.initialize()
        return engine

    @pytest.fixture
    async def policy_tester(self, policy_engine):
        """Create a policy tester instance."""
        tester = PolicyTester(policy_engine)
        await tester.add_predefined_test_cases()
        return tester

    async def test_policy_syntax_validation(self, policy_tester):
        """Test policy syntax validation."""
        # Valid policy
        valid_policy = """
        package test.policy
        
        default allow = false
        
        allow {
            input.user.role == "admin"
        }
        """

        is_valid, errors = await policy_tester.validate_policy_syntax(valid_policy)
        assert is_valid == True
        assert len(errors) == 0

        # Invalid policy
        invalid_policy = """
        package test.policy
        
        default allow = false
        
        allow {
            input.user.role == "admin"
        """

        is_valid, errors = await policy_tester.validate_policy_syntax(invalid_policy)
        assert is_valid == False
        assert len(errors) > 0

    async def test_add_test_case(self, policy_tester):
        """Test adding test cases."""
        test_case = PolicyTestCase(
            name="custom_test",
            description="Custom test case",
            input_data={
                "user": {"id": "test_user", "role": "user"},
                "resource": "tool:test",
                "action": "read",
            },
            expected_result=True,
            tags=["custom"],
        )

        await policy_tester.add_test_case("tool_access", test_case)
        assert "custom_test" in [
            tc.name for tc in policy_tester.test_cases["tool_access"]
        ]

    async def test_run_test_case(self, policy_tester):
        """Test running a single test case."""
        test_case = PolicyTestCase(
            name="single_test",
            description="Single test case",
            input_data={
                "user": {"id": "user1", "role": "user"},
                "resource": "tool:calculator",
                "action": "read",
            },
            expected_result=True,
        )

        result = await policy_tester.run_test_case(test_case, "tool_access")
        assert isinstance(result, PolicyTestResult)
        assert result.test_case == test_case
        assert result.execution_time > 0

    async def test_run_policy_tests(self, policy_tester):
        """Test running all tests for a policy."""
        results = await policy_tester.run_policy_tests("tool_access")
        assert len(results) > 0

        for result in results:
            assert isinstance(result, PolicyTestResult)
            assert result.execution_time > 0

    async def test_run_all_tests(self, policy_tester):
        """Test running all tests for all policies."""
        all_results = await policy_tester.run_all_tests()
        assert len(all_results) > 0

        for policy_name, results in all_results.items():
            assert len(results) > 0

    async def test_generate_test_report(self, policy_tester):
        """Test test report generation."""
        # Run some tests first
        await policy_tester.run_policy_tests("tool_access")

        report = await policy_tester.generate_test_report(policy_tester.test_results)

        assert "summary" in report
        assert "policy_results" in report
        assert "coverage" in report
        assert "failed_tests" in report
        assert "generated_at" in report

    async def test_validate_policy_with_tests(self, policy_tester):
        """Test policy validation with tests."""
        # Valid policy
        valid_policy = """
        package tool_access
        
        default allow = false
        
        allow {
            input.action == "read"
            input.resource = startswith("tool:")
            input.user.role == "user"
        }
        """

        is_valid, errors = await policy_tester.validate_policy_with_tests(
            valid_policy, "tool_access"
        )
        assert is_valid == True
        assert len(errors) == 0

    async def test_export_test_results(self, policy_tester):
        """Test test results export."""
        # Run some tests first
        await policy_tester.run_policy_tests("tool_access")

        # Export as JSON
        json_export = await policy_tester.export_test_results("json")
        assert json_export is not None
        assert len(json_export) > 0

        # Export as CSV
        csv_export = await policy_tester.export_test_results("csv")
        assert csv_export is not None
        assert len(csv_export) > 0

    async def test_get_test_statistics(self, policy_tester):
        """Test test statistics."""
        # Run some tests first
        await policy_tester.run_policy_tests("tool_access")

        stats = await policy_tester.get_test_statistics()

        assert "total_tests" in stats
        assert "passed_tests" in stats
        assert "failed_tests" in stats
        assert "success_rate" in stats
        assert "average_execution_time" in stats
        assert "tag_statistics" in stats


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    async def rate_limiter(self):
        """Create a rate limiter instance."""
        limiter = RateLimiter()
        await limiter.initialize()
        yield limiter
        await limiter.shutdown()

    async def test_add_rate_limit(self, rate_limiter):
        """Test adding rate limit configuration."""
        config = RateLimitConfig(
            key="test_user",
            limit=10,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)
        assert "test_user" in rate_limiter.limiters

    async def test_fixed_window_rate_limiting(self, rate_limiter):
        """Test fixed window rate limiting."""
        config = RateLimitConfig(
            key="fixed_test",
            limit=5,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)

        # Make requests within limit
        for i in range(5):
            result = await rate_limiter.check_rate_limit("fixed_test")
            assert result.allowed == True

        # Next request should be blocked
        result = await rate_limiter.check_rate_limit("fixed_test")
        assert result.allowed == False
        assert result.retry_after is not None

    async def test_sliding_window_rate_limiting(self, rate_limiter):
        """Test sliding window rate limiting."""
        config = RateLimitConfig(
            key="sliding_test",
            limit=3,
            window_seconds=10,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)

        # Make requests within limit
        for i in range(3):
            result = await rate_limiter.check_rate_limit("sliding_test")
            assert result.allowed == True

        # Next request should be blocked
        result = await rate_limiter.check_rate_limit("sliding_test")
        assert result.allowed == False

    async def test_token_bucket_rate_limiting(self, rate_limiter):
        """Test token bucket rate limiting."""
        config = RateLimitConfig(
            key="token_test",
            limit=10,
            window_seconds=60,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
        )

        await rate_limiter.add_rate_limit(config)

        # Initial tokens should be available
        result = await rate_limiter.check_rate_limit("token_test", cost=5)
        assert result.allowed == True

        # Use remaining tokens
        result = await rate_limiter.check_rate_limit("token_test", cost=5)
        assert result.allowed == True

        # Should be blocked
        result = await rate_limiter.check_rate_limit("token_test", cost=1)
        assert result.allowed == False

    async def test_leaky_bucket_rate_limiting(self, rate_limiter):
        """Test leaky bucket rate limiting."""
        config = RateLimitConfig(
            key="leaky_test",
            limit=5,
            window_seconds=10,
            strategy=RateLimitStrategy.LEAKY_BUCKET,
        )

        await rate_limiter.add_rate_limit(config)

        # Fill the bucket
        for i in range(5):
            result = await rate_limiter.check_rate_limit("leaky_test")
            assert result.allowed == True

        # Should be blocked
        result = await rate_limiter.check_rate_limit("leaky_test")
        assert result.allowed == False

    async def test_reset_rate_limit(self, rate_limiter):
        """Test resetting rate limits."""
        config = RateLimitConfig(
            key="reset_test",
            limit=5,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)

        # Use up the limit
        for i in range(5):
            await rate_limiter.check_rate_limit("reset_test")

        # Should be blocked
        result = await rate_limiter.check_rate_limit("reset_test")
        assert result.allowed == False

        # Reset
        success = await rate_limiter.reset_rate_limit("reset_test")
        assert success == True

        # Should be allowed again
        result = await rate_limiter.check_rate_limit("reset_test")
        assert result.allowed == True

    async def test_get_rate_limit_status(self, rate_limiter):
        """Test getting rate limit status."""
        config = RateLimitConfig(
            key="status_test",
            limit=10,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)

        # Make a request
        await rate_limiter.check_rate_limit("status_test")

        # Get status
        status = await rate_limiter.get_rate_limit_status("status_test")
        assert status is not None
        assert status["key"] == "status_test"
        assert status["limit"] == 10
        assert status["strategy"] == "fixed_window"

    async def test_get_statistics(self, rate_limiter):
        """Test getting rate limiter statistics."""
        config = RateLimitConfig(
            key="stats_test",
            limit=5,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)

        # Make some requests
        for i in range(3):
            await rate_limiter.check_rate_limit("stats_test")

        # Get statistics
        stats = await rate_limiter.get_statistics()
        assert "total_rate_limits" in stats
        assert "total_requests" in stats
        assert "allowed_requests" in stats
        assert "blocked_requests" in stats
        assert "success_rate" in stats

    async def test_remove_rate_limit(self, rate_limiter):
        """Test removing rate limits."""
        config = RateLimitConfig(
            key="remove_test",
            limit=5,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW,
        )

        await rate_limiter.add_rate_limit(config)
        assert "remove_test" in rate_limiter.limiters

        # Remove
        success = await rate_limiter.remove_rate_limit("remove_test")
        assert success == True
        assert "remove_test" not in rate_limiter.limiters


class TestRateLimitMiddleware:
    """Test rate limit middleware."""

    @pytest.fixture
    async def rate_limiter(self):
        """Create a rate limiter instance."""
        limiter = RateLimiter()
        await limiter.initialize()
        yield limiter
        await limiter.shutdown()

    @pytest.fixture
    def middleware(self, rate_limiter):
        """Create rate limit middleware."""
        from metamcp.security.rate_limiting import RateLimitMiddleware

        return RateLimitMiddleware(rate_limiter)

    async def test_middleware_extract_api_key(self, middleware):
        """Test middleware API key extraction."""
        # Mock request with API key
        mock_request = MagicMock()
        mock_request.headers = {"X-API-Key": "test_key"}

        key = middleware._extract_rate_limit_key(mock_request)
        assert key == "api_key:test_key"

    async def test_middleware_extract_user_id(self, middleware):
        """Test middleware user ID extraction."""
        # Mock request with user ID
        mock_request = MagicMock()
        mock_request.state.user_id = "test_user"
        mock_request.headers = {}

        key = middleware._extract_rate_limit_key(mock_request)
        assert key == "user:test_user"

    async def test_middleware_extract_ip(self, middleware):
        """Test middleware IP extraction."""
        # Mock request with IP
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        delattr(mock_request.state, "user_id")

        key = middleware._extract_rate_limit_key(mock_request)
        assert key == "ip:192.168.1.100"

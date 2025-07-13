"""
Black Box Tests for Complex Workflows

Tests complex integration scenarios involving both REST and MCP APIs.
"""

import json

import pytest
import websockets
from httpx import AsyncClient

from ..conftest import API_BASE_URL, TEST_TOOL, WS_URL, assert_success_response


class TestToolRegistrationAndExecution:
    """Test complete workflow from tool registration to execution."""

    @pytest.mark.asyncio
    async def test_register_and_execute_via_rest(self, authenticated_client: AsyncClient):
        """Test registering a tool via REST API and executing it."""
        # Step 1: Register tool via REST API
        register_response = await authenticated_client.post(
            f"{API_BASE_URL}/tools",
            json=TEST_TOOL
        )

        register_data = assert_success_response(register_response)
        tool_id = register_data["tool_id"]

        # Step 2: Verify tool is accessible via REST API
        get_response = await authenticated_client.get(
            f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
        )

        get_data = assert_success_response(get_response)
        assert get_data["name"] == TEST_TOOL["name"]
        assert get_data["description"] == TEST_TOOL["description"]

        # Step 3: Execute tool via REST API
        execution_data = {
            "arguments": {
                "operation": "add",
                "a": 10,
                "b": 5
            }
        }

        execute_response = await authenticated_client.post(
            f"{API_BASE_URL}/tools/{TEST_TOOL['name']}/execute",
            json=execution_data
        )

        execute_data = assert_success_response(execute_response)
        assert execute_data["tool_name"] == TEST_TOOL["name"]
        assert execute_data["input_data"] == execution_data["arguments"]
        assert "output_data" in execute_data
        assert "status" in execute_data

        # Step 4: Cleanup
        delete_response = await authenticated_client.delete(
            f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
        )
        assert delete_response.status_code == 200

    @pytest.mark.asyncio
    async def test_register_via_rest_access_via_mcp(self, authenticated_client: AsyncClient):
        """Test registering a tool via REST API and accessing it via MCP."""
        # Step 1: Register tool via REST API
        register_response = await authenticated_client.post(
            f"{API_BASE_URL}/tools",
            json=TEST_TOOL
        )

        register_data = assert_success_response(register_response)
        tool_id = register_data["tool_id"]

        try:
            # Step 2: Access tool via MCP WebSocket
            async with websockets.connect(WS_URL, timeout=30.0) as websocket:
                # Initialize MCP session
                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "1.0.0",
                        "clientInfo": {
                            "name": "IntegrationTestClient",
                            "version": "1.0.0"
                        }
                    }
                }

                await websocket.send(json.dumps(init_message))
                init_response = await websocket.recv()
                init_data = json.loads(init_response)

                if "error" not in init_data:
                    # List tools via MCP
                    list_message = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }

                    await websocket.send(json.dumps(list_message))
                    list_response = await websocket.recv()
                    list_data = json.loads(list_response)

                    if "result" in list_data:
                        tools = list_data["result"]["tools"]
                        # Should find our registered tool
                        test_tool_found = any(tool["name"] == TEST_TOOL["name"] for tool in tools)
                        assert test_tool_found, f"Registered tool not found in MCP tools list: {tools}"

        finally:
            # Cleanup: Delete tool via REST API
            delete_response = await authenticated_client.delete(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
            )
            assert delete_response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self, authenticated_client: AsyncClient):
        """Test concurrent tool operations across REST and MCP APIs."""
        import asyncio

        # Create multiple test tools
        test_tools = []
        for i in range(3):
            tool = TEST_TOOL.copy()
            tool["name"] = f"test_calculator_{i}"
            tool["description"] = f"Test calculator {i}"
            test_tools.append(tool)

        # Register all tools concurrently
        register_tasks = []
        for tool in test_tools:
            task = authenticated_client.post(
                f"{API_BASE_URL}/tools",
                json=tool
            )
            register_tasks.append(task)

        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)

        # Check all registrations succeeded
        for i, result in enumerate(register_results):
            if isinstance(result, Exception):
                pytest.fail(f"Tool registration {i} failed: {result}")
            assert result.status_code == 200

        try:
            # Execute all tools concurrently
            execution_tasks = []
            for tool in test_tools:
                execution_data = {
                    "arguments": {
                        "operation": "add",
                        "a": i,
                        "b": i + 1
                    }
                }
                task = authenticated_client.post(
                    f"{API_BASE_URL}/tools/{tool['name']}/execute",
                    json=execution_data
                )
                execution_tasks.append(task)

            execution_results = await asyncio.gather(*execution_tasks, return_exceptions=True)

            # Check all executions succeeded
            for i, result in enumerate(execution_results):
                if isinstance(result, Exception):
                    pytest.fail(f"Tool execution {i} failed: {result}")
                assert result.status_code == 200

        finally:
            # Cleanup: Delete all tools concurrently
            delete_tasks = []
            for tool in test_tools:
                task = authenticated_client.delete(
                    f"{API_BASE_URL}/tools/{tool['name']}"
                )
                delete_tasks.append(task)

            delete_results = await asyncio.gather(*delete_tasks, return_exceptions=True)

            # Check all deletions succeeded
            for i, result in enumerate(delete_results):
                if isinstance(result, Exception):
                    pytest.fail(f"Tool deletion {i} failed: {result}")
                assert result.status_code == 200


class TestAuthenticationWorkflows:
    """Test authentication workflows across APIs."""

    @pytest.mark.asyncio
    async def test_authentication_token_consistency(self, http_client: AsyncClient):
        """Test that authentication tokens work consistently across endpoints."""
        # Step 1: Login and get token
        login_response = await http_client.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": "test_user", "password": "test_password123"}
        )

        if login_response.status_code == 200:
            token_data = login_response.json()["data"]
            access_token = token_data["access_token"]

            # Step 2: Use token for multiple operations
            http_client.headers["Authorization"] = f"Bearer {access_token}"

            # Test user info
            me_response = await http_client.get(f"{API_BASE_URL}/auth/me")
            assert me_response.status_code == 200

            # Test permissions
            permissions_response = await http_client.get(f"{API_BASE_URL}/auth/permissions")
            assert permissions_response.status_code == 200

            # Test tool operations
            tools_response = await http_client.get(f"{API_BASE_URL}/tools")
            assert tools_response.status_code in [200, 404]  # 404 if no tools exist

            # Step 3: Test token refresh
            refresh_response = await http_client.post(f"{API_BASE_URL}/auth/refresh")
            assert refresh_response.status_code == 200

            # Step 4: Test logout
            logout_response = await http_client.post(f"{API_BASE_URL}/auth/logout")
            assert logout_response.status_code == 200

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, http_client: AsyncClient):
        """Test authentication error handling across endpoints."""
        # Test protected endpoints without authentication
        protected_endpoints = [
            f"{API_BASE_URL}/auth/me",
            f"{API_BASE_URL}/auth/permissions",
            f"{API_BASE_URL}/tools",
            f"{API_BASE_URL}/tools/search?q=test"
        ]

        for endpoint in protected_endpoints:
            response = await http_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

            data = response.json()
            assert "error" in data
            assert data["error"] == "AUTHENTICATION_ERROR"

        # Test with invalid token
        http_client.headers["Authorization"] = "Bearer invalid_token"

        for endpoint in protected_endpoints:
            response = await http_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should reject invalid token"

            data = response.json()
            assert "error" in data
            assert data["error"] == "AUTHENTICATION_ERROR"


class TestErrorHandlingWorkflows:
    """Test error handling across different scenarios."""

    @pytest.mark.asyncio
    async def test_service_unavailable_handling(self, http_client: AsyncClient):
        """Test handling when service components are unavailable."""
        # Test health endpoints when service is down
        # This would require stopping the service, which is not practical in black box tests
        # Instead, test that health endpoints return proper structure

        health_endpoints = [
            f"{API_BASE_URL}/health",
            f"{API_BASE_URL}/health/detailed",
            f"{API_BASE_URL}/health/ready",
            f"{API_BASE_URL}/health/live"
        ]

        for endpoint in health_endpoints:
            response = await http_client.get(endpoint)
            assert response.status_code == 200, f"Health endpoint {endpoint} should be accessible"

            data = response.json()
            # Should have appropriate health status fields
            assert any(field in data for field in ["status", "ready", "alive"]), f"Health endpoint {endpoint} should return health status"

    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, authenticated_client: AsyncClient):
        """Test rate limiting behavior (if implemented)."""
        # Make multiple rapid requests to test rate limiting
        import asyncio

        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = authenticated_client.get(f"{API_BASE_URL}/tools")
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that all requests were handled (either success or rate limit)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Request {i} failed with exception: {result}")

            # Should be either 200 (success) or 429 (rate limited)
            assert result.status_code in [200, 404, 429], f"Request {i} returned unexpected status: {result.status_code}"

            if result.status_code == 429:
                data = result.json()
                assert "error" in data
                assert "rate limit" in data["error"].lower() or "too many requests" in data["error"].lower()


class TestDataConsistency:
    """Test data consistency across different APIs and operations."""

    @pytest.mark.asyncio
    async def test_tool_data_consistency(self, authenticated_client: AsyncClient):
        """Test that tool data is consistent across REST API operations."""
        # Register a tool
        register_response = await authenticated_client.post(
            f"{API_BASE_URL}/tools",
            json=TEST_TOOL
        )

        register_data = assert_success_response(register_response)
        tool_id = register_data["tool_id"]

        try:
            # Get tool data
            get_response = await authenticated_client.get(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
            )

            get_data = assert_success_response(get_response)

            # Verify data consistency
            assert get_data["name"] == TEST_TOOL["name"]
            assert get_data["description"] == TEST_TOOL["description"]
            assert get_data["category"] == TEST_TOOL["category"]
            assert get_data["endpoint"] == TEST_TOOL["endpoint"]
            assert get_data["capabilities"] == TEST_TOOL["capabilities"]
            assert get_data["security_level"] == TEST_TOOL["security_level"]
            assert get_data["schema"] == TEST_TOOL["schema"]
            assert get_data["metadata"] == TEST_TOOL["metadata"]
            assert get_data["version"] == TEST_TOOL["version"]
            assert get_data["author"] == TEST_TOOL["author"]
            assert get_data["tags"] == TEST_TOOL["tags"]

            # Update tool
            update_data = {
                "description": "Updated description",
                "category": "updated_category"
            }

            update_response = await authenticated_client.put(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}",
                json=update_data
            )

            update_result = assert_success_response(update_response)

            # Verify updated data is consistent
            assert update_result["description"] == update_data["description"]
            assert update_result["category"] == update_data["category"]

            # Get tool again and verify consistency
            get_updated_response = await authenticated_client.get(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
            )

            get_updated_data = assert_success_response(get_updated_response)
            assert get_updated_data["description"] == update_data["description"]
            assert get_updated_data["category"] == update_data["category"]

        finally:
            # Cleanup
            delete_response = await authenticated_client.delete(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
            )
            assert delete_response.status_code == 200

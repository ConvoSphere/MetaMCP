"""
Black Box Integration Tests for End-to-End Workflows

Tests complete user journeys and workflows in the MetaMCP REST API.
"""

import time

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL, TEST_TOOL, TEST_USER


class TestUserWorkflows:
    """Test complete user workflows and journeys."""

    @pytest.mark.asyncio
    async def test_complete_tool_lifecycle(self, http_client: AsyncClient):
        """Test complete tool lifecycle: register -> search -> execute -> delete."""
        # Step 1: Login
        login_response = await http_client.post(
            f"{API_BASE_URL}auth/login", json=TEST_USER
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Set authentication header
        http_client.headers["Authorization"] = f"Bearer {access_token}"

        # Step 2: Register tool
        tool_data = TEST_TOOL.copy()
        tool_data["name"] = f"workflow_test_tool_{int(time.time())}"

        register_response = await http_client.post(
            f"{API_BASE_URL}tools", json=tool_data
        )
        assert register_response.status_code in [200, 201]
        register_data = register_response.json()
        tool_id = register_data["tool_id"]

        # Step 3: List tools (should include our tool)
        list_response = await http_client.get(f"{API_BASE_URL}tools")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert "tools" in list_data
        tools = list_data["tools"]
        tool_found = any(tool["name"] == tool_data["name"] for tool in tools)
        assert tool_found, f"Registered tool not found in list: {tool_data['name']}"

        # Step 4: Get tool details
        get_response = await http_client.get(f"{API_BASE_URL}tools/{tool_data['name']}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == tool_data["name"]
        assert get_data["description"] == tool_data["description"]

        # Step 5: Execute tool
        execution_data = {"arguments": {"operation": "add", "a": 5, "b": 3}}
        execute_response = await http_client.post(
            f"{API_BASE_URL}tools/{tool_data['name']}/execute", json=execution_data
        )
        assert execute_response.status_code == 200
        execute_data = execute_response.json()
        assert execute_data["tool_name"] == tool_data["name"]
        assert "status" in execute_data

        # Step 6: Search for tool
        search_response = await http_client.get(
            f"{API_BASE_URL}tools/search?q={tool_data['name']}"
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert "results" in search_data
        search_results = search_data["results"]
        search_found = any(
            result["name"] == tool_data["name"] for result in search_results
        )
        assert search_found, f"Tool not found in search results: {tool_data['name']}"

        # Step 7: Delete tool
        delete_response = await http_client.delete(
            f"{API_BASE_URL}tools/{tool_data['name']}"
        )
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert "message" in delete_data

    @pytest.mark.asyncio
    async def test_authentication_workflow(self, http_client: AsyncClient):
        """Test complete authentication workflow: login -> access protected -> logout."""
        # Step 1: Login
        login_response = await http_client.post(
            f"{API_BASE_URL}auth/login", json=TEST_USER
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Set authentication header
        http_client.headers["Authorization"] = f"Bearer {access_token}"

        # Step 2: Access protected endpoint
        me_response = await http_client.get(f"{API_BASE_URL}auth/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert "user_id" in me_data
        assert "username" in me_data
        assert me_data["username"] == TEST_USER["username"]

        # Step 3: Get permissions
        permissions_response = await http_client.get(f"{API_BASE_URL}auth/permissions")
        assert permissions_response.status_code == 200
        permissions_data = permissions_response.json()
        assert "user_id" in permissions_data
        assert "permissions" in permissions_data

        # Step 4: Refresh token
        refresh_response = await http_client.post(f"{API_BASE_URL}auth/refresh")
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"

        # Step 5: Logout
        logout_response = await http_client.post(f"{API_BASE_URL}auth/logout")
        assert logout_response.status_code == 200
        logout_data = logout_response.json()
        assert "message" in logout_data

    @pytest.mark.asyncio
    async def test_admin_workflow(self, http_client: AsyncClient):
        """Test admin workflow: login as admin -> access admin dashboard."""
        # Step 1: Login as admin
        admin_login_response = await http_client.post(
            f"{API_BASE_URL}auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert admin_login_response.status_code == 200
        admin_token_data = admin_login_response.json()
        admin_access_token = admin_token_data["access_token"]

        # Set authentication header
        http_client.headers["Authorization"] = f"Bearer {admin_access_token}"

        # Step 2: Access admin dashboard
        dashboard_response = await http_client.get(f"{API_BASE_URL}admin/dashboard")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        assert isinstance(dashboard_data, dict)


class TestErrorHandlingWorkflows:
    """Test error handling in complete workflows."""

    @pytest.mark.asyncio
    async def test_authentication_failure_workflow(self, http_client: AsyncClient):
        """Test workflow with authentication failures."""
        # Try to access protected endpoint without authentication
        protected_endpoints = [
            f"{API_BASE_URL}tools",
            f"{API_BASE_URL}admin/dashboard",
            f"{API_BASE_URL}auth/me",
        ]

        for endpoint in protected_endpoints:
            response = await http_client.get(endpoint)
            assert response.status_code in [401, 403]

        # Try to login with wrong credentials
        wrong_credentials = [
            {"username": "nonexistent", "password": "wrong"},
            {"username": "test_user", "password": "wrong_password"},
            {"username": "", "password": ""},
        ]

        for credentials in wrong_credentials:
            response = await http_client.post(
                f"{API_BASE_URL}auth/login", json=credentials
            )
            assert response.status_code in [401, 400, 422]

    @pytest.mark.asyncio
    async def test_tool_workflow_with_errors(self, http_client: AsyncClient):
        """Test tool workflow with various error conditions."""
        # Login first
        login_response = await http_client.post(
            f"{API_BASE_URL}auth/login", json=TEST_USER
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]
        http_client.headers["Authorization"] = f"Bearer {access_token}"

        # Try to register tool with missing fields
        incomplete_tool = {"name": "incomplete_tool"}
        register_response = await http_client.post(
            f"{API_BASE_URL}tools", json=incomplete_tool
        )
        assert register_response.status_code in [400, 422]

        # Try to get non-existent tool
        get_response = await http_client.get(f"{API_BASE_URL}tools/nonexistent_tool")
        assert get_response.status_code == 404

        # Try to execute non-existent tool
        execute_data = {"arguments": {"param": "value"}}
        execute_response = await http_client.post(
            f"{API_BASE_URL}tools/nonexistent_tool/execute", json=execute_data
        )
        assert execute_response.status_code == 404


class TestConcurrentWorkflows:
    """Test concurrent workflow execution."""

    @pytest.mark.asyncio
    async def test_concurrent_user_sessions(self, http_client: AsyncClient):
        """Test multiple concurrent user sessions."""

        async def user_session(user_id: int):
            # Login
            login_response = await http_client.post(
                f"{API_BASE_URL}auth/login", json=TEST_USER
            )
            if login_response.status_code != 200:
                return False

            token_data = login_response.json()
            access_token = token_data["access_token"]

            # Create authenticated client
            auth_headers = {"Authorization": f"Bearer {access_token}"}

            # Access protected endpoint
            me_response = await http_client.get(
                f"{API_BASE_URL}auth/me", headers=auth_headers
            )
            if me_response.status_code != 200:
                return False

            # List tools
            tools_response = await http_client.get(
                f"{API_BASE_URL}tools", headers=auth_headers
            )
            if tools_response.status_code not in [200, 404]:
                return False

            return True

        # Run multiple concurrent sessions
        import asyncio

        tasks = [user_session(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most sessions should succeed
        success_count = sum(1 for r in results if r is True)
        assert (
            success_count >= 3
        ), f"Only {success_count}/5 concurrent sessions succeeded"

    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self, http_client: AsyncClient):
        """Test concurrent tool operations."""
        # Login first
        login_response = await http_client.post(
            f"{API_BASE_URL}auth/login", json=TEST_USER
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        async def tool_operation(operation_id: int):
            tool_data = {
                "name": f"concurrent_tool_{operation_id}_{int(pytest.time.time())}",
                "description": f"Concurrent test tool {operation_id}",
                "endpoint": f"http://localhost:900{operation_id}",
                "category": "concurrent",
                "capabilities": ["read"],
                "security_level": 1,
            }

            # Register tool
            register_response = await http_client.post(
                f"{API_BASE_URL}tools", json=tool_data, headers=auth_headers
            )

            if register_response.status_code not in [200, 201]:
                return False

            # Get tool details
            get_response = await http_client.get(
                f"{API_BASE_URL}tools/{tool_data['name']}", headers=auth_headers
            )

            if get_response.status_code != 200:
                return False

            return True

        # Run concurrent tool operations
        import asyncio

        tasks = [tool_operation(i) for i in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most operations should succeed
        success_count = sum(1 for r in results if r is True)
        assert (
            success_count >= 2
        ), f"Only {success_count}/3 concurrent tool operations succeeded"


class TestDataConsistencyWorkflows:
    """Test data consistency across workflows."""

    @pytest.mark.asyncio
    async def test_tool_data_consistency(self, http_client: AsyncClient):
        """Test that tool data remains consistent across operations."""
        # Login
        login_response = await http_client.post(
            f"{API_BASE_URL}auth/login", json=TEST_USER
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]
        http_client.headers["Authorization"] = f"Bearer {access_token}"

        # Register tool
        tool_data = TEST_TOOL.copy()
        tool_data["name"] = f"consistency_test_tool_{int(pytest.time.time())}"

        register_response = await http_client.post(
            f"{API_BASE_URL}tools", json=tool_data
        )
        assert register_response.status_code in [200, 201]

        # Get tool details multiple times
        for i in range(3):
            get_response = await http_client.get(
                f"{API_BASE_URL}tools/{tool_data['name']}"
            )
            assert get_response.status_code == 200
            get_data = get_response.json()

            # Data should be consistent
            assert get_data["name"] == tool_data["name"]
            assert get_data["description"] == tool_data["description"]
            assert get_data["category"] == tool_data["category"]

        # Cleanup
        delete_response = await http_client.delete(
            f"{API_BASE_URL}tools/{tool_data['name']}"
        )
        assert delete_response.status_code == 200

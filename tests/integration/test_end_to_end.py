"""
End-to-End Integration Tests for MetaMCP

These tests verify complete workflows across all components including:
- User authentication and authorization
- Tool registration and management
- Tool execution and search
- API integration and error handling
- Cross-component data consistency
"""

import asyncio
import json
import time
from typing import Dict, List

import pytest
import pytest_asyncio
from httpx import AsyncClient

from metamcp.services.auth_service import AuthService
from metamcp.services.tool_service import ToolService
from metamcp.services.search_service import SearchService


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest_asyncio.fixture
    async def setup_services(self, test_settings):
        """Set up all services for integration testing."""
        self.auth_service = AuthService(settings=test_settings)
        self.tool_service = ToolService(settings=test_settings)
        self.search_service = SearchService(settings=test_settings)
        
        # Create test users
        self.admin_user = await self.auth_service.create_user({
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Admin User",
            "is_active": True,
            "is_admin": True,
        })
        
        self.regular_user = await self.auth_service.create_user({
            "username": "user",
            "email": "user@example.com",
            "password": "user123",
            "full_name": "Regular User",
            "is_active": True,
            "is_admin": False,
        })
        
        yield
        
        # Cleanup
        await self._cleanup_test_data()
    
    async def _cleanup_test_data(self):
        """Clean up test data after tests."""
        # This would typically involve database cleanup
        pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, setup_services, async_client):
        """Test complete user workflow from registration to tool execution."""
        
        # 1. User Authentication
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data["data"]
        token = token_data["data"]["access_token"]
        
        # 2. Get User Info
        headers = {"Authorization": f"Bearer {token}"}
        user_info_response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert user_info_response.status_code == 200
        user_info = user_info_response.json()["data"]
        assert user_info["username"] == "user"
        
        # 3. Register a Tool
        tool_data = {
            "name": "Test Calculator",
            "description": "A simple calculator for testing",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "subtract"]},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "result": {"type": "number"}
                }
            },
            "endpoints": [
                {
                    "url": "http://localhost:8001/calculate",
                    "method": "POST",
                    "timeout": 30
                }
            ],
            "tags": ["math", "calculator"],
            "category": "utility"
        }
        
        register_response = await async_client.post(
            "/api/v1/tools/register",
            json=tool_data,
            headers=headers
        )
        assert register_response.status_code == 200
        tool_id = register_response.json()["data"]["tool_id"]
        
        # 4. Search for Tools
        search_response = await async_client.post(
            "/api/v1/tools/search",
            json={"query": "calculator", "limit": 10},
            headers=headers
        )
        assert search_response.status_code == 200
        search_results = search_response.json()["data"]["tools"]
        assert len(search_results) > 0
        assert any(tool["name"] == "Test Calculator" for tool in search_results)
        
        # 5. Execute Tool
        execution_response = await async_client.post(
            f"/api/v1/tools/{tool_id}/execute",
            json={
                "operation": "add",
                "a": 5,
                "b": 3
            },
            headers=headers
        )
        assert execution_response.status_code == 200
        execution_result = execution_response.json()["data"]
        assert "result" in execution_result
        assert "execution_time" in execution_result
        
        # 6. Get Tool Details
        tool_details_response = await async_client.get(
            f"/api/v1/tools/{tool_id}",
            headers=headers
        )
        assert tool_details_response.status_code == 200
        tool_details = tool_details_response.json()["data"]
        assert tool_details["name"] == "Test Calculator"
        
        # 7. Update Tool
        updated_tool_data = {
            "description": "Updated calculator description",
            "version": "1.1.0"
        }
        update_response = await async_client.put(
            f"/api/v1/tools/{tool_id}",
            json=updated_tool_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        # 8. Verify Update
        updated_details_response = await async_client.get(
            f"/api/v1/tools/{tool_id}",
            headers=headers
        )
        assert updated_details_response.status_code == 200
        updated_details = updated_details_response.json()["data"]
        assert updated_details["description"] == "Updated calculator description"
        assert updated_details["version"] == "1.1.0"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_workflow(self, setup_services, async_client):
        """Test admin-specific workflows."""
        
        # 1. Admin Login
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        admin_token = login_response.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 2. Get System Statistics
        stats_response = await async_client.get("/api/v1/admin/stats", headers=admin_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]
        assert "total_users" in stats
        assert "total_tools" in stats
        assert "active_sessions" in stats
        
        # 3. Get All Users
        users_response = await async_client.get("/api/v1/admin/users", headers=admin_headers)
        assert users_response.status_code == 200
        users = users_response.json()["data"]["users"]
        assert len(users) >= 2  # admin and regular user
        
        # 4. Get All Tools
        tools_response = await async_client.get("/api/v1/admin/tools", headers=admin_headers)
        assert tools_response.status_code == 200
        tools = tools_response.json()["data"]["tools"]
        assert isinstance(tools, list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, setup_services, async_client):
        """Test error handling in complete workflows."""
        
        # 1. Invalid Authentication
        invalid_login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrong"
        })
        assert invalid_login_response.status_code == 401
        
        # 2. Valid Login
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Access Non-existent Tool
        nonexistent_tool_response = await async_client.get(
            "/api/v1/tools/nonexistent-tool-id",
            headers=headers
        )
        assert nonexistent_tool_response.status_code == 404
        
        # 4. Execute Non-existent Tool
        execute_nonexistent_response = await async_client.post(
            "/api/v1/tools/nonexistent-tool-id/execute",
            json={"test": "data"},
            headers=headers
        )
        assert execute_nonexistent_response.status_code == 404
        
        # 5. Invalid Token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        invalid_token_response = await async_client.get("/api/v1/auth/me", headers=invalid_headers)
        assert invalid_token_response.status_code == 401
        
        # 6. Missing Token
        no_token_response = await async_client.get("/api/v1/auth/me")
        assert no_token_response.status_code == 401
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, setup_services, async_client):
        """Test concurrent operations and race conditions."""
        
        # Login
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create multiple tools concurrently
        tool_data_template = {
            "name": "Concurrent Tool {i}",
            "description": "Tool created for concurrent testing",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [{"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}],
            "tags": ["concurrent"],
            "category": "test"
        }
        
        async def register_tool(i: int):
            tool_data = tool_data_template.copy()
            tool_data["name"] = f"Concurrent Tool {i}"
            response = await async_client.post(
                "/api/v1/tools/register",
                json=tool_data,
                headers=headers
            )
            return response
        
        # Register 5 tools concurrently
        tasks = [register_tool(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # Verify all registrations succeeded
        for response in responses:
            assert response.status_code == 200
        
        # Search for all concurrent tools
        search_response = await async_client.post(
            "/api/v1/tools/search",
            json={"query": "concurrent", "limit": 10},
            headers=headers
        )
        assert search_response.status_code == 200
        search_results = search_response.json()["data"]["tools"]
        assert len(search_results) >= 5
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_consistency(self, setup_services, async_client):
        """Test data consistency across different operations."""
        
        # Login
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Register tool
        tool_data = {
            "name": "Consistency Test Tool",
            "description": "Tool for testing data consistency",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [{"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}],
            "tags": ["consistency"],
            "category": "test"
        }
        
        register_response = await async_client.post(
            "/api/v1/tools/register",
            json=tool_data,
            headers=headers
        )
        assert register_response.status_code == 200
        tool_id = register_response.json()["data"]["tool_id"]
        
        # Get tool details multiple times and verify consistency
        details_responses = []
        for _ in range(3):
            response = await async_client.get(f"/api/v1/tools/{tool_id}", headers=headers)
            assert response.status_code == 200
            details_responses.append(response.json()["data"])
        
        # Verify all responses are identical
        first_response = details_responses[0]
        for response in details_responses[1:]:
            assert response == first_response
        
        # Search for the tool multiple times
        search_responses = []
        for _ in range(3):
            response = await async_client.post(
                "/api/v1/tools/search",
                json={"query": "Consistency Test Tool", "limit": 10},
                headers=headers
            )
            assert response.status_code == 200
            search_responses.append(response.json()["data"]["tools"])
        
        # Verify search results are consistent
        first_search = search_responses[0]
        for search_result in search_responses[1:]:
            assert len(search_result) == len(first_search)
            # Check that the same tool is found in all searches
            tool_names = [tool["name"] for tool in search_result]
            assert "Consistency Test Tool" in tool_names
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_workflow(self, setup_services, async_client):
        """Test performance characteristics of complete workflows."""
        
        # Login
        login_response = await async_client.post("/api/v1/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Measure registration performance
        tool_data = {
            "name": "Performance Test Tool",
            "description": "Tool for performance testing",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [{"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}],
            "tags": ["performance"],
            "category": "test"
        }
        
        start_time = time.time()
        register_response = await async_client.post(
            "/api/v1/tools/register",
            json=tool_data,
            headers=headers
        )
        registration_time = time.time() - start_time
        
        assert register_response.status_code == 200
        assert registration_time < 2.0  # Should complete within 2 seconds
        
        tool_id = register_response.json()["data"]["tool_id"]
        
        # Measure search performance
        start_time = time.time()
        search_response = await async_client.post(
            "/api/v1/tools/search",
            json={"query": "performance", "limit": 10},
            headers=headers
        )
        search_time = time.time() - start_time
        
        assert search_response.status_code == 200
        assert search_time < 1.0  # Should complete within 1 second
        
        # Measure tool details retrieval performance
        start_time = time.time()
        details_response = await async_client.get(f"/api/v1/tools/{tool_id}", headers=headers)
        details_time = time.time() - start_time
        
        assert details_response.status_code == 200
        assert details_time < 0.5  # Should complete within 0.5 seconds


class TestCrossComponentIntegration:
    """Test integration between different components."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_auth_tool_integration(self, test_settings):
        """Test integration between authentication and tool services."""
        
        auth_service = AuthService(settings=test_settings)
        tool_service = ToolService(settings=test_settings)
        
        # Create user
        user_data = {
            "username": "integration_user",
            "email": "integration@example.com",
            "password": "password123",
            "full_name": "Integration User",
            "is_active": True,
            "is_admin": False,
        }
        
        user = await auth_service.create_user(user_data)
        assert user["username"] == "integration_user"
        
        # Create token
        token_data = {"sub": user["username"], "permissions": user["permissions"]}
        token = await auth_service.create_access_token(token_data)
        
        # Verify token
        payload = await auth_service.verify_token(token)
        assert payload["sub"] == "integration_user"
        
        # Register tool with user context
        tool_data = {
            "name": "Integration Test Tool",
            "description": "Tool for testing auth integration",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [{"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}],
            "tags": ["integration"],
            "category": "test"
        }
        
        tool_id = await tool_service.register_tool(tool_data, user["username"])
        assert tool_id is not None
        
        # Get tool with user context
        tool = await tool_service.get_tool(tool_id, user["username"])
        assert tool is not None
        assert tool["name"] == "Integration Test Tool"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_tool_integration(self, test_settings):
        """Test integration between search and tool services."""
        
        tool_service = ToolService(settings=test_settings)
        search_service = SearchService(settings=test_settings)
        
        # Register multiple tools
        tools_data = [
            {
                "name": "Search Tool 1",
                "description": "First search test tool",
                "version": "1.0.0",
                "author": "Test Author",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "endpoints": [{"url": "http://localhost:8001/test1", "method": "POST", "timeout": 30}],
                "tags": ["search", "test"],
                "category": "utility"
            },
            {
                "name": "Search Tool 2",
                "description": "Second search test tool",
                "version": "1.0.0",
                "author": "Test Author",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "endpoints": [{"url": "http://localhost:8001/test2", "method": "POST", "timeout": 30}],
                "tags": ["search", "test"],
                "category": "utility"
            }
        ]
        
        tool_ids = []
        for tool_data in tools_data:
            tool_id = await tool_service.register_tool(tool_data, "testuser")
            tool_ids.append(tool_id)
        
        # Search for tools
        search_query = {
            "query": "search test",
            "filters": {"category": "utility"},
            "limit": 10,
            "offset": 0
        }
        
        search_results = await search_service.search_tools(search_query)
        assert len(search_results["tools"]) >= 2
        
        # Verify search results match registered tools
        found_tool_names = [tool["name"] for tool in search_results["tools"]]
        assert "Search Tool 1" in found_tool_names
        assert "Search Tool 2" in found_tool_names
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation(self, test_settings):
        """Test error propagation across components."""
        
        auth_service = AuthService(settings=test_settings)
        tool_service = ToolService(settings=test_settings)
        
        # Test invalid token handling
        with pytest.raises(Exception):
            await auth_service.verify_token("invalid-token")
        
        # Test non-existent tool access
        tool = await tool_service.get_tool("non-existent-id", "testuser")
        assert tool is None
        
        # Test invalid tool execution
        result = await tool_service.execute_tool("non-existent-id", {}, "testuser")
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()


class TestDataPersistence:
    """Test data persistence across operations."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_persistence_workflow(self, test_settings):
        """Test that data persists correctly across operations."""
        
        auth_service = AuthService(settings=test_settings)
        tool_service = ToolService(settings=test_settings)
        
        # Create user
        user_data = {
            "username": "persistence_user",
            "email": "persistence@example.com",
            "password": "password123",
            "full_name": "Persistence User",
            "is_active": True,
            "is_admin": False,
        }
        
        user = await auth_service.create_user(user_data)
        
        # Register tool
        tool_data = {
            "name": "Persistence Test Tool",
            "description": "Tool for testing data persistence",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [{"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}],
            "tags": ["persistence"],
            "category": "test"
        }
        
        tool_id = await tool_service.register_tool(tool_data, user["username"])
        
        # Verify tool persists
        tool = await tool_service.get_tool(tool_id, user["username"])
        assert tool is not None
        assert tool["name"] == "Persistence Test Tool"
        
        # Update tool
        updated_data = {"description": "Updated description"}
        await tool_service.update_tool(tool_id, updated_data, user["username"])
        
        # Verify update persists
        updated_tool = await tool_service.get_tool(tool_id, user["username"])
        assert updated_tool["description"] == "Updated description"
        
        # Delete tool
        await tool_service.delete_tool(tool_id, user["username"])
        
        # Verify deletion persists
        deleted_tool = await tool_service.get_tool(tool_id, user["username"])
        assert deleted_tool is None 
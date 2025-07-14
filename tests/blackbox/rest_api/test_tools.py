"""
Black Box Tests for Tool Management Endpoints

Tests the tool registration, execution, and management endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import (
    API_BASE_URL,
    TEST_TOOL,
)

class TestToolRegistration:
    """Test tool registration endpoints with actual API response format."""

    @pytest.mark.asyncio
    async def test_register_tool_success(self, authenticated_client: AsyncClient):
        """Test successful tool registration."""
        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/",
            json=TEST_TOOL
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "tool_id" in data
        assert "message" in data
        assert "registered successfully" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_register_tool_duplicate(self, authenticated_client: AsyncClient):
        """Test registering duplicate tool."""
        # Register tool first time
        response1 = await authenticated_client.post(
            f"{API_BASE_URL}tools/",
            json=TEST_TOOL
        )
        assert response1.status_code in [200, 201]
        # Try to register same tool again
        response2 = await authenticated_client.post(
            f"{API_BASE_URL}tools",
            json=TEST_TOOL
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_register_tool_missing_fields(self, authenticated_client: AsyncClient):
        """Test registering tool with missing required fields."""
        incomplete_tool = {
            "name": "incomplete_tool"
            # Missing description and endpoint
        }
        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/",
            json=incomplete_tool
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_register_tool_unauthorized(self, http_client: AsyncClient):
        """Test registering tool without authentication."""
        response = await http_client.post(
            f"{API_BASE_URL}tools/",
            json=TEST_TOOL
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

class TestToolRetrieval:
    """Test tool retrieval endpoints with actual API response format."""

    @pytest.mark.asyncio
    async def test_get_tool_success(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test getting tool by name."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}tools/{TEST_TOOL['name']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_TOOL["name"]
        assert data["description"] == TEST_TOOL["description"]
        assert data["category"] == TEST_TOOL["category"]
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, authenticated_client: AsyncClient):
        """Test getting non-existent tool."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}tools/nonexistent_tool"
        )
        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_list_tools(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test listing tools."""
        response = await authenticated_client.get(f"{API_BASE_URL}tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert isinstance(data["tools"], list)
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_tools_with_category_filter(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test listing tools with category filter."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}tools?category={TEST_TOOL['category']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total" in data
        tools = data["tools"]
        test_tool_found = any(tool["name"] == TEST_TOOL["name"] for tool in tools)
        assert test_tool_found, f"Test tool not found in filtered results: {tools}"

class TestToolExecution:
    """Test tool execution endpoints with actual API response format."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test successful tool execution."""
        execution_data = {
            "arguments": {
                "operation": "add",
                "a": 5,
                "b": 3
            }
        }
        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/{TEST_TOOL['name']}/execute",
            json=execution_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_name"] == TEST_TOOL["name"]
        assert data["input_data"] == execution_data["arguments"]
        assert "status" in data
        assert "execution_time" in data
        assert "executed_by" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, authenticated_client: AsyncClient):
        """Test executing non-existent tool."""
        execution_data = {
            "arguments": {"param": "value"}
        }
        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/nonexistent_tool/execute",
            json=execution_data
        )
        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_execute_tool_invalid_arguments(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test executing tool with invalid arguments."""
        execution_data = {
            "arguments": {
                "invalid_param": "value"
            }
        }
        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/{TEST_TOOL['name']}/execute",
            json=execution_data
        )
        assert response.status_code in [400, 422, 500]

class TestToolSearch:
    """Test tool search endpoints with actual API response format."""

    @pytest.mark.asyncio
    async def test_search_tools(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test tool search."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}tools/search?q=calculator"
        )
        assert response.status_code == 200
        data = response.json()
        assert "search_id" in data
        assert "query" in data
        assert "search_type" in data
        assert "results" in data
        assert "total" in data
        assert "search_time" in data
        assert "timestamp" in data
        assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_search_tools_with_filters(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test tool search with additional filters."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}tools/search?q=calculator&max_results=5&similarity_threshold=0.5&search_type=hybrid"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "hybrid"
        assert len(data["results"]) <= 5

class TestToolManagement:
    """Test tool management operations with actual API response format."""

    @pytest.mark.asyncio
    async def test_update_tool(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test updating tool."""
        update_data = {
            "description": "Updated calculator description",
            "category": "updated_category"
        }
        response = await authenticated_client.put(
            f"{API_BASE_URL}tools/{TEST_TOOL['name']}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["category"] == update_data["category"]
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_delete_tool(self, authenticated_client: AsyncClient, test_tool_id: str):
        """Test deleting tool."""
        response = await authenticated_client.delete(
            f"{API_BASE_URL}tools/{TEST_TOOL['name']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

"""
Tool Registry Tests

Tests for the tool registry operations including registration, listing,
searching, updating, and deletion of tools.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch

from fastapi import HTTPException

from metamcp.api.tools import (
    mock_tools,
    _create_tool_id,
    _get_tool_by_name,
    _filter_tools_by_category,
    _paginate_tools,
    _search_tools_simple
)
from metamcp.exceptions import ToolNotFoundError, ValidationError


class TestToolRegistryFunctions:
    """Test tool registry helper functions."""
    
    def test_create_tool_id(self):
        """Test tool ID creation."""
        tool_id = _create_tool_id()
        assert tool_id is not None
        assert isinstance(tool_id, str)
        assert len(tool_id) > 0
        
        # Should be unique
        another_id = _create_tool_id()
        assert tool_id != another_id
    
    def test_get_tool_by_name(self):
        """Test getting tool by name."""
        # Clear mock tools
        mock_tools.clear()
        
        # Add a test tool
        test_tool = {
            "id": "test-id",
            "name": "test_tool",
            "description": "Test tool",
            "endpoint": "http://localhost:8001",
            "category": "test",
            "capabilities": ["read"],
            "security_level": 1,
            "schema": {},
            "metadata": {},
            "version": "1.0.0",
            "author": "test",
            "tags": ["test"],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "is_active": True
        }
        mock_tools["test-id"] = test_tool
        
        # Test finding existing tool
        found_tool = _get_tool_by_name("test_tool")
        assert found_tool is not None
        assert found_tool["name"] == "test_tool"
        
        # Test finding non-existent tool
        not_found = _get_tool_by_name("nonexistent")
        assert not_found is None
    
    def test_filter_tools_by_category(self):
        """Test filtering tools by category."""
        tools = [
            {"name": "tool1", "category": "database"},
            {"name": "tool2", "category": "api"},
            {"name": "tool3", "category": "database"},
            {"name": "tool4", "category": None}
        ]
        
        # Filter by database category
        database_tools = _filter_tools_by_category(tools, "database")
        assert len(database_tools) == 2
        assert all(tool["category"] == "database" for tool in database_tools)
        
        # Filter by api category
        api_tools = _filter_tools_by_category(tools, "api")
        assert len(api_tools) == 1
        assert api_tools[0]["category"] == "api"
        
        # No filter
        all_tools = _filter_tools_by_category(tools, None)
        assert len(all_tools) == 4
    
    def test_paginate_tools(self):
        """Test tool pagination."""
        tools = [
            {"name": "tool1"},
            {"name": "tool2"},
            {"name": "tool3"},
            {"name": "tool4"},
            {"name": "tool5"}
        ]
        
        # Test first page
        page1 = _paginate_tools(tools, 0, 2)
        assert len(page1) == 2
        assert page1[0]["name"] == "tool1"
        assert page1[1]["name"] == "tool2"
        
        # Test second page
        page2 = _paginate_tools(tools, 2, 2)
        assert len(page2) == 2
        assert page2[0]["name"] == "tool3"
        assert page2[1]["name"] == "tool4"
        
        # Test last page
        page3 = _paginate_tools(tools, 4, 2)
        assert len(page3) == 1
        assert page3[0]["name"] == "tool5"
        
        # Test empty page
        empty_page = _paginate_tools(tools, 10, 2)
        assert len(empty_page) == 0
    
    def test_search_tools_simple(self):
        """Test simple tool search."""
        tools = [
            {"name": "database_query", "description": "Query database", "tags": ["db", "sql"]},
            {"name": "api_client", "description": "Make API calls", "tags": ["http", "rest"]},
            {"name": "file_processor", "description": "Process files", "tags": ["file", "io"]}
        ]
        
        # Search by name
        results = _search_tools_simple("database", tools)
        assert len(results) == 1
        assert results[0]["name"] == "database_query"
        
        # Search by description
        results = _search_tools_simple("API", tools)
        assert len(results) == 1
        assert results[0]["name"] == "api_client"
        
        # Search by tags
        results = _search_tools_simple("sql", tools)
        assert len(results) == 1
        assert results[0]["name"] == "database_query"
        
        # Search with no results
        results = _search_tools_simple("nonexistent", tools)
        assert len(results) == 0
        
        # Case insensitive search
        results = _search_tools_simple("DATABASE", tools)
        assert len(results) == 1


class TestToolEndpoints:
    """Test tool API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from metamcp.main import create_app
        
        app = create_app()
        return TestClient(app)
    
    def test_register_tool_success(self, client):
        """Test successful tool registration."""
        tool_data = {
            "name": "test_tool",
            "description": "Test tool for testing",
            "endpoint": "http://localhost:8001",
            "category": "test",
            "capabilities": ["read", "write"],
            "security_level": 2,
            "schema": {"input": {}, "output": {}},
            "metadata": {"version": "1.0.0"},
            "version": "1.0.0",
            "author": "test_author",
            "tags": ["test", "api"]
        }
        
        response = client.post("/api/v1/tools", json=tool_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "tool_id" in data
        assert "message" in data
        assert data["message"] == "Tool registered successfully"
    
    def test_register_tool_duplicate_name(self, client):
        """Test tool registration with duplicate name."""
        tool_data = {
            "name": "duplicate_tool",
            "description": "First tool",
            "endpoint": "http://localhost:8001"
        }
        
        # Register first tool
        response1 = client.post("/api/v1/tools", json=tool_data)
        assert response1.status_code == 201
        
        # Try to register tool with same name
        response2 = client.post("/api/v1/tools", json=tool_data)
        assert response2.status_code == 400
        data = response2.json()
        assert "error" in data
    
    def test_list_tools(self, client):
        """Test listing tools."""
        # Register a test tool first
        tool_data = {
            "name": "list_test_tool",
            "description": "Tool for testing list",
            "endpoint": "http://localhost:8001"
        }
        client.post("/api/v1/tools", json=tool_data)
        
        # List tools
        response = client.get("/api/v1/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert isinstance(data["tools"], list)
    
    def test_list_tools_with_pagination(self, client):
        """Test listing tools with pagination."""
        # Register multiple tools
        for i in range(5):
            tool_data = {
                "name": f"pagination_tool_{i}",
                "description": f"Tool {i} for pagination test",
                "endpoint": f"http://localhost:800{i}"
            }
            client.post("/api/v1/tools", json=tool_data)
        
        # Test pagination
        response = client.get("/api/v1/tools?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) <= 2
        assert data["total"] >= 5
    
    def test_list_tools_with_category_filter(self, client):
        """Test listing tools with category filter."""
        # Register tools with different categories
        categories = ["database", "api", "file"]
        for category in categories:
            tool_data = {
                "name": f"{category}_tool",
                "description": f"Tool for {category}",
                "endpoint": "http://localhost:8001",
                "category": category
            }
            client.post("/api/v1/tools", json=tool_data)
        
        # Filter by database category
        response = client.get("/api/v1/tools?category=database")
        assert response.status_code == 200
        data = response.json()
        assert all(tool["category"] == "database" for tool in data["tools"])
    
    def test_get_tool_details(self, client):
        """Test getting tool details."""
        # Register a test tool
        tool_data = {
            "name": "detail_test_tool",
            "description": "Tool for detail test",
            "endpoint": "http://localhost:8001",
            "category": "test",
            "capabilities": ["read"],
            "security_level": 1,
            "schema": {"input": {}, "output": {}},
            "metadata": {"test": "data"},
            "version": "1.0.0",
            "author": "test_author",
            "tags": ["test"]
        }
        client.post("/api/v1/tools", json=tool_data)
        
        # Get tool details
        response = client.get("/api/v1/tools/detail_test_tool")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "detail_test_tool"
        assert data["description"] == "Tool for detail test"
        assert data["endpoint"] == "http://localhost:8001"
        assert data["category"] == "test"
        assert "capabilities" in data
        assert "security_level" in data
        assert "schema" in data
        assert "metadata" in data
        assert "version" in data
        assert "author" in data
        assert "tags" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "is_active" in data
    
    def test_get_nonexistent_tool(self, client):
        """Test getting details of non-existent tool."""
        response = client.get("/api/v1/tools/nonexistent_tool")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_update_tool(self, client):
        """Test updating tool."""
        # Register a test tool
        tool_data = {
            "name": "update_test_tool",
            "description": "Original description",
            "endpoint": "http://localhost:8001"
        }
        client.post("/api/v1/tools", json=tool_data)
        
        # Update tool
        update_data = {
            "description": "Updated description",
            "category": "updated_category",
            "capabilities": ["read", "write"],
            "security_level": 3
        }
        
        response = client.put("/api/v1/tools/update_test_tool", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["category"] == "updated_category"
        assert "read" in data["capabilities"]
        assert "write" in data["capabilities"]
        assert data["security_level"] == 3
    
    def test_update_nonexistent_tool(self, client):
        """Test updating non-existent tool."""
        update_data = {
            "description": "Updated description"
        }
        
        response = client.put("/api/v1/tools/nonexistent_tool", json=update_data)
        assert response.status_code == 404
    
    def test_delete_tool(self, client):
        """Test deleting tool."""
        # Register a test tool
        tool_data = {
            "name": "delete_test_tool",
            "description": "Tool to be deleted",
            "endpoint": "http://localhost:8001"
        }
        client.post("/api/v1/tools", json=tool_data)
        
        # Delete tool
        response = client.delete("/api/v1/tools/delete_test_tool")
        assert response.status_code == 204
        
        # Verify tool is no longer active
        get_response = client.get("/api/v1/tools/delete_test_tool")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["is_active"] is False
    
    def test_delete_nonexistent_tool(self, client):
        """Test deleting non-existent tool."""
        response = client.delete("/api/v1/tools/nonexistent_tool")
        assert response.status_code == 404
    
    def test_search_tools(self, client):
        """Test searching tools."""
        # Register test tools
        tools = [
            {
                "name": "database_query",
                "description": "Query database with SQL",
                "endpoint": "http://localhost:8001",
                "tags": ["database", "sql"]
            },
            {
                "name": "api_client",
                "description": "Make HTTP API calls",
                "endpoint": "http://localhost:8002",
                "tags": ["http", "rest"]
            },
            {
                "name": "file_processor",
                "description": "Process files and documents",
                "endpoint": "http://localhost:8003",
                "tags": ["file", "io"]
            }
        ]
        
        for tool in tools:
            client.post("/api/v1/tools", json=tool)
        
        # Search for database tools
        search_data = {
            "query": "database",
            "max_results": 10,
            "similarity_threshold": 0.7
        }
        
        response = client.post("/api/v1/tools/search", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "query" in data
        assert "total" in data
        assert "search_time" in data
        assert len(data["tools"]) > 0
    
    def test_execute_tool(self, client):
        """Test tool execution."""
        # Register a test tool
        tool_data = {
            "name": "execute_test_tool",
            "description": "Tool for execution test",
            "endpoint": "http://localhost:8001"
        }
        client.post("/api/v1/tools", json=tool_data)
        
        # Execute tool
        execution_data = {
            "input_data": {"param1": "value1", "param2": "value2"},
            "async_execution": False
        }
        
        response = client.post("/api/v1/tools/execute_test_tool/execute", json=execution_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "tool_name" in data
        assert "input_data" in data
        assert "status" in data
        assert "result" in data
        assert "execution_time" in data
        assert "executed_by" in data
        assert "timestamp" in data
    
    def test_execute_nonexistent_tool(self, client):
        """Test executing non-existent tool."""
        execution_data = {
            "input_data": {"param1": "value1"},
            "async_execution": False
        }
        
        response = client.post("/api/v1/tools/nonexistent_tool/execute", json=execution_data)
        assert response.status_code == 404


class TestToolRegistryMock:
    """Test mock tool registry functionality."""
    
    def test_mock_tools_storage(self):
        """Test mock tools storage."""
        # Clear mock tools
        mock_tools.clear()
        
        # Add a test tool
        test_tool = {
            "id": "test-id",
            "name": "test_tool",
            "description": "Test tool",
            "endpoint": "http://localhost:8001",
            "is_active": True
        }
        mock_tools["test-id"] = test_tool
        
        # Verify tool is stored
        assert "test-id" in mock_tools
        assert mock_tools["test-id"]["name"] == "test_tool"
        
        # Verify tool can be retrieved by name
        found_tool = _get_tool_by_name("test_tool")
        assert found_tool is not None
        assert found_tool["id"] == "test-id"
    
    def test_mock_tools_soft_delete(self):
        """Test soft delete functionality."""
        # Clear mock tools
        mock_tools.clear()
        
        # Add a test tool
        test_tool = {
            "id": "delete-test-id",
            "name": "delete_test_tool",
            "description": "Tool to be deleted",
            "endpoint": "http://localhost:8001",
            "is_active": True
        }
        mock_tools["delete-test-id"] = test_tool
        
        # Soft delete the tool
        test_tool["is_active"] = False
        test_tool["updated_at"] = datetime.now(UTC).isoformat()
        test_tool["deleted_by"] = "test_user"
        
        # Verify tool is marked as inactive
        assert test_tool["is_active"] is False
        assert "deleted_by" in test_tool
        assert "updated_at" in test_tool 
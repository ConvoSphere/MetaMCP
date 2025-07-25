"""
Service Layer Tests

Tests for the service layer components including ToolService, AuthService,
and SearchService with proper mocking and error handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from metamcp.exceptions import AuthenticationError, ToolNotFoundError, ValidationError
from metamcp.services.auth_service import AuthService
from metamcp.services.search_service import SearchService
from metamcp.services.tool_service import ToolService


class TestToolService:
    """Test ToolService functionality."""

    @pytest.fixture
    def tool_service(self):
        """Create ToolService instance."""
        return ToolService()

    @pytest.fixture
    def sample_tool_data(self):
        """Sample tool data for testing."""
        return {
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
            "tags": ["test", "api"],
        }

    async def test_register_tool_success(self, tool_service, sample_tool_data):
        """Test successful tool registration."""
        user_id = "test_user"

        tool_id = await tool_service.register_tool(sample_tool_data, user_id)

        assert tool_id is not None
        assert isinstance(tool_id, str)
        assert len(tool_id) > 0

        # Verify tool was stored
        tool = tool_service._get_tool_by_name("test_tool")
        assert tool is not None
        assert tool["name"] == "test_tool"
        assert tool["description"] == "Test tool for testing"
        assert tool["created_by"] == user_id
        assert tool["is_active"] is True

    async def test_register_tool_duplicate_name(self, tool_service, sample_tool_data):
        """Test tool registration with duplicate name."""
        user_id = "test_user"

        # Register first tool
        await tool_service.register_tool(sample_tool_data, user_id)

        # Try to register tool with same name
        with pytest.raises(ValidationError, match="already exists"):
            await tool_service.register_tool(sample_tool_data, user_id)

    async def test_register_tool_missing_required_fields(self, tool_service):
        """Test tool registration with missing required fields."""
        incomplete_data = {
            "name": "test_tool"
            # Missing description and endpoint
        }

        with pytest.raises(ValidationError, match="Missing required field"):
            await tool_service.register_tool(incomplete_data, "test_user")

    async def test_get_tool_success(self, tool_service, sample_tool_data):
        """Test getting tool by name."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        tool = await tool_service.get_tool("test_tool")

        assert tool is not None
        assert tool["name"] == "test_tool"
        assert tool["description"] == "Test tool for testing"

    async def test_get_tool_not_found(self, tool_service):
        """Test getting non-existent tool."""
        with pytest.raises(ToolNotFoundError):
            await tool_service.get_tool("nonexistent_tool")

    async def test_list_tools(self, tool_service, sample_tool_data):
        """Test listing tools."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        # Add another tool
        second_tool = sample_tool_data.copy()
        second_tool["name"] = "test_tool_2"
        await tool_service.register_tool(second_tool, user_id)

        result = await tool_service.list_tools()

        assert "tools" in result
        assert "total" in result
        assert "offset" in result
        assert "limit" in result
        assert result["total"] == 2
        assert len(result["tools"]) == 2

    async def test_list_tools_with_category_filter(
        self, tool_service, sample_tool_data
    ):
        """Test listing tools with category filter."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        # Add tool with different category
        second_tool = sample_tool_data.copy()
        second_tool["name"] = "api_tool"
        second_tool["category"] = "api"
        await tool_service.register_tool(second_tool, user_id)

        # Filter by test category
        result = await tool_service.list_tools(category="test")
        assert result["total"] == 1
        assert result["tools"][0]["category"] == "test"

        # Filter by api category
        result = await tool_service.list_tools(category="api")
        assert result["total"] == 1
        assert result["tools"][0]["category"] == "api"

    async def test_update_tool(self, tool_service, sample_tool_data):
        """Test updating tool."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        update_data = {
            "description": "Updated description",
            "category": "updated_category",
            "capabilities": ["read", "write", "execute"],
            "security_level": 3,
        }

        updated_tool = await tool_service.update_tool("test_tool", update_data, user_id)

        assert updated_tool["description"] == "Updated description"
        assert updated_tool["category"] == "updated_category"
        assert "execute" in updated_tool["capabilities"]
        assert updated_tool["security_level"] == 3
        assert updated_tool["updated_by"] == user_id

    async def test_update_nonexistent_tool(self, tool_service):
        """Test updating non-existent tool."""
        update_data = {"description": "Updated description"}

        with pytest.raises(ToolNotFoundError):
            await tool_service.update_tool("nonexistent_tool", update_data, "test_user")

    async def test_delete_tool(self, tool_service, sample_tool_data):
        """Test deleting tool."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        # Verify tool exists and is active
        tool = await tool_service.get_tool("test_tool")
        assert tool["is_active"] is True

        # Delete tool
        await tool_service.delete_tool("test_tool", user_id)

        # Verify tool is now inactive
        tool = await tool_service.get_tool("test_tool")
        assert tool["is_active"] is False
        assert tool["deleted_by"] == user_id

    async def test_delete_nonexistent_tool(self, tool_service):
        """Test deleting non-existent tool."""
        with pytest.raises(ToolNotFoundError):
            await tool_service.delete_tool("nonexistent_tool", "test_user")

    async def test_search_tools(self, tool_service, sample_tool_data):
        """Test searching tools."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        # Add another tool with different description
        second_tool = sample_tool_data.copy()
        second_tool["name"] = "database_tool"
        second_tool["description"] = "Database query tool"
        await tool_service.register_tool(second_tool, user_id)

        # Search for database tools
        results = await tool_service.search_tools("database")
        assert len(results) > 0

        # Search for non-existent tools
        results = await tool_service.search_tools("nonexistent")
        assert len(results) == 0

    @patch("httpx.AsyncClient")
    async def test_execute_tool_success(
        self, mock_httpx_client, tool_service, sample_tool_data
    ):
        """Test successful tool execution."""
        user_id = "test_user"
        await tool_service.register_tool(sample_tool_data, user_id)

        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.text = '{"result": "success"}'

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client

        arguments = {"param1": "value1", "param2": "value2"}

        result = await tool_service.execute_tool("test_tool", arguments, user_id)

        assert result["tool_name"] == "test_tool"
        assert result["input_data"] == arguments
        assert result["status"] == "success"
        assert result["executed_by"] == user_id
        assert "execution_time" in result
        assert "timestamp" in result

    async def test_execute_nonexistent_tool(self, tool_service):
        """Test executing non-existent tool."""
        arguments = {"param1": "value1"}

        with pytest.raises(ToolNotFoundError):
            await tool_service.execute_tool("nonexistent_tool", arguments, "test_user")

    def test_get_execution_history(self, tool_service, sample_tool_data):
        """Test getting execution history."""
        # Add some execution history
        tool_service.execution_history = [
            {"tool_name": "test_tool", "timestamp": "2023-01-01T00:00:00Z"},
            {"tool_name": "test_tool", "timestamp": "2023-01-02T00:00:00Z"},
        ]

        history = tool_service.get_execution_history()
        assert len(history) == 2

    def test_get_tool_statistics(self, tool_service, sample_tool_data):
        """Test getting tool statistics."""
        # Add some tools
        tool_service.tools = {
            "tool1": {"name": "tool1", "category": "database", "is_active": True},
            "tool2": {"name": "tool2", "category": "api", "is_active": True},
            "tool3": {"name": "tool3", "category": "database", "is_active": False},
        }

        stats = tool_service.get_tool_statistics()

        assert stats["total_tools"] == 3
        assert stats["active_tools"] == 2
        assert "database" in stats["categories"]
        assert stats["categories"]["database"] == 1
        assert stats["categories"]["api"] == 1


class TestAuthService:
    """Test AuthService functionality."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance."""
        return AuthService()

    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication."""
        user = await auth_service.authenticate_user("admin", "admin123")

        assert user is not None
        assert user["username"] == "admin"
        assert user["user_id"] == "admin_user"
        assert "admin" in user["roles"]

    async def test_authenticate_user_invalid_credentials(self, auth_service):
        """Test authentication with invalid credentials."""
        user = await auth_service.authenticate_user("admin", "wrongpassword")
        assert user is None

    async def test_authenticate_user_nonexistent(self, auth_service):
        """Test authentication with non-existent user."""
        user = await auth_service.authenticate_user("nonexistent", "password")
        assert user is None

    async def test_create_access_token(self, auth_service):
        """Test access token creation."""
        data = {"sub": "test_user"}
        token = await auth_service.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_verify_token_valid(self, auth_service):
        """Test valid token verification."""
        data = {"sub": "test_user"}
        token = await auth_service.create_access_token(data)

        payload = await auth_service.verify_token(token)
        assert payload["sub"] == "test_user"

    async def test_verify_token_invalid(self, auth_service):
        """Test invalid token verification."""
        with pytest.raises(AuthenticationError):
            await auth_service.verify_token("invalid_token")

    async def test_verify_token_blacklisted(self, auth_service):
        """Test blacklisted token verification."""
        data = {"sub": "test_user"}
        token = await auth_service.create_access_token(data)

        # Add token to blacklist
        auth_service.token_blacklist.add(token)

        with pytest.raises(AuthenticationError, match="revoked"):
            await auth_service.verify_token(token)

    async def test_get_current_user(self, auth_service):
        """Test getting current user from token."""
        data = {"sub": "admin"}
        token = await auth_service.create_access_token(data)

        user = await auth_service.get_current_user(token)

        assert user is not None
        assert user["username"] == "admin"
        assert user["user_id"] == "admin_user"

    async def test_get_current_user_invalid_token(self, auth_service):
        """Test getting current user with invalid token."""
        with pytest.raises(AuthenticationError):
            await auth_service.get_current_user("invalid_token")

    async def test_revoke_token(self, auth_service):
        """Test token revocation."""
        data = {"sub": "test_user"}
        token = await auth_service.create_access_token(data)

        # Verify token is valid
        payload = await auth_service.verify_token(token)
        assert payload["sub"] == "test_user"

        # Revoke token
        await auth_service.revoke_token(token)

        # Verify token is now invalid
        with pytest.raises(AuthenticationError, match="revoked"):
            await auth_service.verify_token(token)

    async def test_get_user_permissions(self, auth_service):
        """Test getting user permissions."""
        permissions = await auth_service.get_user_permissions("admin_user")

        assert permissions["user_id"] == "admin_user"
        assert permissions["username"] == "admin"
        assert "roles" in permissions
        assert "permissions" in permissions
        assert "admin" in permissions["roles"]

    async def test_check_permission_admin(self, auth_service):
        """Test permission checking for admin user."""
        # Admin users should have all permissions
        has_permission = await auth_service.check_permission(
            "admin_user", "tools", "read"
        )
        assert has_permission is True

        has_permission = await auth_service.check_permission(
            "admin_user", "admin", "manage"
        )
        assert has_permission is True

    async def test_check_permission_regular_user(self, auth_service):
        """Test permission checking for regular user."""
        # Regular users have limited permissions
        has_permission = await auth_service.check_permission(
            "regular_user", "tools", "read"
        )
        assert has_permission is True

        has_permission = await auth_service.check_permission(
            "regular_user", "admin", "manage"
        )
        assert has_permission is False

    async def test_create_user(self, auth_service):
        """Test user creation."""
        user_data = {
            "username": "new_user",
            "password": "newpassword123",
            "roles": ["user"],
            "permissions": {"tools": ["read", "execute"], "admin": []},
        }

        user_id = await auth_service.create_user(user_data, "admin_user")

        assert user_id is not None
        assert isinstance(user_id, str)

        # Verify user was created
        user = auth_service.users.get("new_user")
        assert user is not None
        assert user["username"] == "new_user"
        assert user["created_by"] == "admin_user"

    async def test_create_user_duplicate_username(self, auth_service):
        """Test user creation with duplicate username."""
        user_data = {"username": "admin", "password": "password123"}  # Already exists

        with pytest.raises(ValidationError, match="already exists"):
            await auth_service.create_user(user_data, "admin_user")

    async def test_update_user(self, auth_service):
        """Test user update."""
        user_id = "admin_user"
        update_data = {
            "roles": ["admin", "superuser"],
            "permissions": {
                "tools": ["read", "write", "execute"],
                "admin": ["manage", "configure"],
            },
        }

        updated_user = await auth_service.update_user(
            user_id, update_data, "admin_user"
        )

        assert "superuser" in updated_user["roles"]
        assert "configure" in updated_user["permissions"]["admin"]
        assert updated_user["updated_by"] == "admin_user"

    async def test_deactivate_user(self, auth_service):
        """Test user deactivation."""
        user_id = "regular_user"

        # Verify user is active
        user = auth_service._get_user_by_id(user_id)
        assert user["is_active"] is True

        # Deactivate user
        await auth_service.deactivate_user(user_id, "admin_user")

        # Verify user is now inactive
        user = auth_service._get_user_by_id(user_id)
        assert user["is_active"] is False
        assert user["deactivated_by"] == "admin_user"

    def test_get_login_history(self, auth_service):
        """Test getting login history."""
        # Add some login history
        auth_service.login_history = [
            {
                "username": "admin",
                "successful": True,
                "timestamp": "2023-01-01T00:00:00Z",
            },
            {
                "username": "user",
                "successful": False,
                "timestamp": "2023-01-02T00:00:00Z",
            },
        ]

        history = auth_service.get_login_history()
        assert len(history) == 2

    def test_get_user_statistics(self, auth_service):
        """Test getting user statistics."""
        stats = auth_service.get_user_statistics()

        assert "total_users" in stats
        assert "active_users" in stats
        assert "roles" in stats
        assert "total_logins" in stats
        assert "successful_logins" in stats
        assert "failed_logins" in stats


class TestSearchService:
    """Test SearchService functionality."""

    @pytest.fixture
    def search_service(self):
        """Create SearchService instance."""
        return SearchService()

    async def test_search_tools_semantic(self, search_service):
        """Test semantic search."""
        query = "database query"
        max_results = 5
        similarity_threshold = 0.7

        results = await search_service.search_tools(
            query=query,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            search_type="semantic",
        )

        assert "search_id" in results
        assert results["query"] == query
        assert results["search_type"] == "semantic"
        assert "results" in results
        assert "total" in results
        assert "search_time" in results
        assert "timestamp" in results

    async def test_search_tools_keyword(self, search_service):
        """Test keyword search."""
        query = "API client"
        max_results = 3

        results = await search_service.search_tools(
            query=query, max_results=max_results, search_type="keyword"
        )

        assert results["search_type"] == "keyword"
        assert len(results["results"]) <= max_results

    async def test_search_tools_hybrid(self, search_service):
        """Test hybrid search."""
        query = "file processing"
        max_results = 10
        similarity_threshold = 0.6

        results = await search_service.search_tools(
            query=query,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            search_type="hybrid",
        )

        assert results["search_type"] == "hybrid"
        assert "results" in results

    async def test_search_tools_invalid_type(self, search_service):
        """Test search with invalid search type."""
        with pytest.raises(Exception, match="Unsupported search type"):
            await search_service.search_tools(query="test", search_type="invalid_type")

    def test_calculate_similarity(self, search_service):
        """Test similarity calculation."""
        query = "database query"
        tool = {
            "name": "database_query",
            "description": "Query database with SQL",
            "tags": ["database", "sql"],
        }

        similarity = search_service._calculate_similarity(query, tool)

        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.0  # Should have some similarity

    def test_calculate_similarity_no_match(self, search_service):
        """Test similarity calculation with no match."""
        query = "completely different"
        tool = {
            "name": "database_query",
            "description": "Query database with SQL",
            "tags": ["database", "sql"],
        }

        similarity = search_service._calculate_similarity(query, tool)

        assert similarity == 0.0

    def test_get_available_tools(self, search_service):
        """Test getting available tools."""
        tools = search_service._get_available_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        for tool in tools:
            assert "id" in tool
            assert "name" in tool
            assert "description" in tool
            assert "category" in tool
            assert "tags" in tool

    def test_generate_search_id(self, search_service):
        """Test search ID generation."""
        search_id = search_service._generate_search_id()

        assert isinstance(search_id, str)
        assert len(search_id) > 0

    def test_update_search_metrics(self, search_service):
        """Test search metrics update."""
        initial_metrics = search_service.search_metrics.copy()

        # Update metrics with successful search
        search_service._update_search_metrics(0.5, True)

        assert (
            search_service.search_metrics["total_searches"]
            == initial_metrics["total_searches"] + 1
        )
        assert (
            search_service.search_metrics["successful_searches"]
            == initial_metrics["successful_searches"] + 1
        )
        assert search_service.search_metrics["average_response_time"] > 0.0

    def test_get_search_history(self, search_service):
        """Test getting search history."""
        # Add some search history
        search_service.search_history = [
            {"search_id": "search1", "query": "database", "status": "completed"},
            {"search_id": "search2", "query": "api", "status": "completed"},
        ]

        history = search_service.get_search_history()
        assert len(history) == 2

    def test_get_search_metrics(self, search_service):
        """Test getting search metrics."""
        metrics = search_service.get_search_metrics()

        assert "total_searches" in metrics
        assert "successful_searches" in metrics
        assert "failed_searches" in metrics
        assert "average_response_time" in metrics

    def test_get_search_statistics(self, search_service):
        """Test getting search statistics."""
        # Add some search history
        search_service.search_history = [
            {
                "search_id": "search1",
                "query": "database",
                "status": "completed",
                "duration": 0.1,
            },
            {
                "search_id": "search2",
                "query": "api",
                "status": "completed",
                "duration": 0.2,
            },
            {
                "search_id": "search3",
                "query": "file",
                "status": "failed",
                "duration": 0.0,
            },
        ]

        stats = search_service.get_search_statistics()

        assert stats["total_searches"] == 3
        assert stats["successful_searches"] == 2
        assert stats["failed_searches"] == 1
        assert stats["success_rate"] == 2 / 3
        assert "search_types" in stats
        assert "recent_queries" in stats

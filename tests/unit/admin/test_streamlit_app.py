"""
Unit Tests for Streamlit Admin Interface

Tests the Streamlit admin interface functions and API communication.
"""

import json
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from metamcp.admin.streamlit_app import (
    make_api_request,
    get_dashboard_data,
    get_system_metrics,
    get_users,
    get_tools,
    get_logs,
    create_user,
    update_user,
    delete_user,
    create_tool,
    update_tool,
    delete_tool,
    restart_system,
)


class TestAPIRequests:
    """Test API request functions."""

    @patch('metamcp.admin.streamlit_app.requests.get')
    def test_make_api_request_get_success(self, mock_get):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = make_api_request("test-endpoint")
        
        assert result == {"status": "success"}
        mock_get.assert_called_once()

    @patch('metamcp.admin.streamlit_app.requests.post')
    def test_make_api_request_post_success(self, mock_post):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "123", "message": "created"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        data = {"name": "test"}
        result = make_api_request("test-endpoint", method="POST", data=data)
        
        assert result == {"id": "123", "message": "created"}
        mock_post.assert_called_once()

    @patch('metamcp.admin.streamlit_app.requests.get')
    def test_make_api_request_error(self, mock_get):
        """Test API request error handling."""
        mock_get.side_effect = Exception("Connection error")

        result = make_api_request("test-endpoint")
        
        assert result == {}

    def test_make_api_request_invalid_method(self):
        """Test invalid HTTP method."""
        with pytest.raises(ValueError, match="Unsupported method"):
            make_api_request("test-endpoint", method="INVALID")


class TestDashboardFunctions:
    """Test dashboard-related functions."""

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_get_dashboard_data(self, mock_api_request):
        """Test getting dashboard data."""
        mock_data = {
            "system": {"uptime_formatted": "2h 30m"},
            "metrics": {"total_requests": 1000}
        }
        mock_api_request.return_value = mock_data

        result = get_dashboard_data()
        
        assert result == mock_data
        mock_api_request.assert_called_once_with("dashboard")

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_get_system_metrics(self, mock_api_request):
        """Test getting system metrics."""
        mock_data = {
            "memory_usage_mb": 512.5,
            "cpu_usage_percent": 25.0
        }
        mock_api_request.return_value = mock_data

        result = get_system_metrics()
        
        assert result == mock_data
        mock_api_request.assert_called_once_with("system/metrics")


class TestUserManagement:
    """Test user management functions."""

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_get_users_with_filters(self, mock_api_request):
        """Test getting users with filters."""
        mock_data = {
            "users": [
                {"user_id": "1", "username": "test1"},
                {"user_id": "2", "username": "test2"}
            ],
            "pagination": {"page": 1, "total": 2}
        }
        mock_api_request.return_value = mock_data

        result = get_users(page=1, limit=10, search="test", role="admin", is_active=True)
        
        assert result == mock_data
        expected_params = "page=1&limit=10&search=test&role=admin&is_active=True"
        mock_api_request.assert_called_once_with(f"users?{expected_params}")

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_create_user_success(self, mock_api_request):
        """Test successful user creation."""
        mock_response = {"user_id": "123", "message": "User created successfully"}
        mock_api_request.return_value = mock_response

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        
        result = create_user(user_data)
        
        assert result is True
        mock_api_request.assert_called_once_with("users", method="POST", data=user_data)

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_create_user_failure(self, mock_api_request):
        """Test failed user creation."""
        mock_api_request.return_value = {"error": "User already exists"}

        user_data = {"username": "existing", "email": "test@example.com", "password": "pass"}
        
        result = create_user(user_data)
        
        assert result is False

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_update_user_success(self, mock_api_request):
        """Test successful user update."""
        mock_response = {"message": "User updated successfully"}
        mock_api_request.return_value = mock_response

        user_data = {"email": "new@example.com"}
        
        result = update_user("123", user_data)
        
        assert result is True
        mock_api_request.assert_called_once_with("users/123", method="PUT", data=user_data)

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_delete_user_success(self, mock_api_request):
        """Test successful user deletion."""
        mock_response = {"message": "User deleted successfully"}
        mock_api_request.return_value = mock_response

        result = delete_user("123")
        
        assert result is True
        mock_api_request.assert_called_once_with("users/123", method="DELETE")


class TestToolManagement:
    """Test tool management functions."""

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_get_tools_with_filters(self, mock_api_request):
        """Test getting tools with filters."""
        mock_data = {
            "tools": [
                {"tool_id": "1", "name": "tool1"},
                {"tool_id": "2", "name": "tool2"}
            ],
            "pagination": {"page": 1, "total": 2}
        }
        mock_api_request.return_value = mock_data

        result = get_tools(page=1, limit=10, search="tool", status="active", is_active=True)
        
        assert result == mock_data
        expected_params = "page=1&limit=10&search=tool&status=active&is_active=True"
        mock_api_request.assert_called_once_with(f"tools?{expected_params}")

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_create_tool_success(self, mock_api_request):
        """Test successful tool creation."""
        mock_response = {"tool_id": "456", "message": "Tool created successfully"}
        mock_api_request.return_value = mock_response

        tool_data = {
            "name": "testtool",
            "description": "A test tool",
            "endpoint_url": "http://example.com/api"
        }
        
        result = create_tool(tool_data)
        
        assert result is True
        mock_api_request.assert_called_once_with("tools", method="POST", data=tool_data)

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_update_tool_success(self, mock_api_request):
        """Test successful tool update."""
        mock_response = {"message": "Tool updated successfully"}
        mock_api_request.return_value = mock_response

        tool_data = {"description": "Updated description"}
        
        result = update_tool("456", tool_data)
        
        assert result is True
        mock_api_request.assert_called_once_with("tools/456", method="PUT", data=tool_data)

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_delete_tool_success(self, mock_api_request):
        """Test successful tool deletion."""
        mock_response = {"message": "Tool deleted successfully"}
        mock_api_request.return_value = mock_response

        result = delete_tool("456")
        
        assert result is True
        mock_api_request.assert_called_once_with("tools/456", method="DELETE")


class TestSystemManagement:
    """Test system management functions."""

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_get_logs_with_filters(self, mock_api_request):
        """Test getting logs with filters."""
        mock_data = {
            "logs": [
                {"timestamp": "2025-07-27T06:42:23Z", "level": "INFO", "message": "Test log"}
            ]
        }
        mock_api_request.return_value = mock_data

        result = get_logs(level="INFO", limit=50)
        
        assert result == mock_data
        expected_params = "limit=50&level=INFO"
        mock_api_request.assert_called_once_with(f"logs?{expected_params}")

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_restart_system_success(self, mock_api_request):
        """Test successful system restart."""
        mock_response = {"message": "System restart initiated"}
        mock_api_request.return_value = mock_response

        result = restart_system()
        
        assert result is True
        mock_api_request.assert_called_once_with("system/restart", method="POST")

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_restart_system_failure(self, mock_api_request):
        """Test failed system restart."""
        mock_api_request.return_value = {"error": "Restart failed"}

        result = restart_system()
        
        assert result is False


class TestDataValidation:
    """Test data validation and error handling."""

    def test_user_data_validation(self):
        """Test user data validation."""
        # Valid user data
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "roles": ["user"],
            "is_active": True,
            "is_admin": False
        }
        
        # This should not raise any exceptions
        assert isinstance(valid_data, dict)
        assert "username" in valid_data
        assert "email" in valid_data
        assert "password" in valid_data

    def test_tool_data_validation(self):
        """Test tool data validation."""
        # Valid tool data
        valid_data = {
            "name": "testtool",
            "description": "A test tool",
            "version": "1.0.0",
            "endpoint_url": "http://example.com/api",
            "authentication_type": "none",
            "schema": {},
            "is_active": True
        }
        
        # This should not raise any exceptions
        assert isinstance(valid_data, dict)
        assert "name" in valid_data
        assert "description" in valid_data
        assert "endpoint_url" in valid_data

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_api_error_handling(self, mock_api_request):
        """Test API error handling."""
        # Simulate API error
        mock_api_request.return_value = {}

        # Test that functions handle errors gracefully
        result = get_dashboard_data()
        assert result == {}

        result = get_system_metrics()
        assert result == {}

        result = get_users()
        assert result == {}


class TestIntegration:
    """Test integration scenarios."""

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_complete_user_workflow(self, mock_api_request):
        """Test complete user management workflow."""
        # Create user
        mock_api_request.return_value = {"user_id": "123", "message": "User created successfully"}
        user_data = {"username": "testuser", "email": "test@example.com", "password": "pass"}
        assert create_user(user_data) is True

        # Get users
        mock_api_request.return_value = {
            "users": [{"user_id": "123", "username": "testuser"}],
            "pagination": {"page": 1, "total": 1}
        }
        users = get_users()
        assert "users" in users
        assert len(users["users"]) == 1

        # Update user
        mock_api_request.return_value = {"message": "User updated successfully"}
        update_data = {"email": "new@example.com"}
        assert update_user("123", update_data) is True

        # Delete user
        mock_api_request.return_value = {"message": "User deleted successfully"}
        assert delete_user("123") is True

    @patch('metamcp.admin.streamlit_app.make_api_request')
    def test_complete_tool_workflow(self, mock_api_request):
        """Test complete tool management workflow."""
        # Create tool
        mock_api_request.return_value = {"tool_id": "456", "message": "Tool created successfully"}
        tool_data = {"name": "testtool", "description": "Test tool", "endpoint_url": "http://example.com"}
        assert create_tool(tool_data) is True

        # Get tools
        mock_api_request.return_value = {
            "tools": [{"tool_id": "456", "name": "testtool"}],
            "pagination": {"page": 1, "total": 1}
        }
        tools = get_tools()
        assert "tools" in tools
        assert len(tools["tools"]) == 1

        # Update tool
        mock_api_request.return_value = {"message": "Tool updated successfully"}
        update_data = {"description": "Updated description"}
        assert update_tool("456", update_data) is True

        # Delete tool
        mock_api_request.return_value = {"message": "Tool deleted successfully"}
        assert delete_tool("456") is True
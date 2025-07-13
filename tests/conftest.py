"""
Pytest Configuration

This module provides pytest configuration and shared fixtures
for testing the MetaMCP application.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from metamcp.config import get_settings, reload_settings
from metamcp.llm.service import LLMService
from metamcp.monitoring.telemetry import TelemetryManager
from metamcp.security.auth import AuthManager
from metamcp.security.policies import PolicyEngine
from metamcp.tools.registry import ToolRegistry
from metamcp.vector.client import VectorSearchClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def mock_telemetry():
    """Mock telemetry manager."""
    telemetry = Mock(spec=TelemetryManager)
    telemetry.record_request = Mock()
    telemetry.record_tool_execution = Mock()
    telemetry.record_vector_search = Mock()
    telemetry.trace_operation = AsyncMock()
    telemetry.is_initialized = True
    return telemetry


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    registry = Mock(spec=ToolRegistry)
    registry.list_tools = AsyncMock(return_value=[])
    registry.execute_tool = AsyncMock(return_value={"result": "test"})
    registry.search_tools = AsyncMock(return_value=[])
    registry.is_initialized = True
    return registry


@pytest.fixture
def mock_vector_client():
    """Mock vector search client."""
    client = Mock(spec=VectorSearchClient)
    client.search = AsyncMock(return_value=[])
    client.add_documents = AsyncMock()
    client.is_initialized = True
    return client


@pytest.fixture
def mock_auth_manager():
    """Mock authentication manager."""
    auth = Mock(spec=AuthManager)
    auth.validate_token = Mock(return_value="test_user")
    auth.create_token = Mock(return_value="test_token")
    auth.is_initialized = True
    return auth


@pytest.fixture
def mock_policy_engine():
    """Mock policy engine."""
    policy = Mock(spec=PolicyEngine)
    policy.evaluate = AsyncMock(return_value={"allowed": True})
    policy.is_initialized = True
    return policy


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    llm = Mock(spec=LLMService)
    llm.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    llm.generate_text = AsyncMock(return_value="test response")
    llm.is_initialized = True
    return llm


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return {
        "name": "test_calculator",
        "description": "A simple calculator tool",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        },
        "categories": ["math", "calculation"],
        "tags": ["calculator", "math"]
    }


@pytest.fixture
def sample_search_query():
    """Sample search query for testing."""
    return "mathematical calculation tool"


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test_user_123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "execute"]
    }


@pytest.fixture
def sample_request_data():
    """Sample request data for testing."""
    return {
        "method": "POST",
        "path": "/api/tools/execute",
        "headers": {
            "authorization": "Bearer test_token",
            "content-type": "application/json"
        },
        "body": {
            "tool_name": "test_calculator",
            "arguments": {
                "operation": "add",
                "a": 5,
                "b": 3
            }
        }
    }


@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application."""
    app = Mock()
    app.add_middleware = Mock()
    app.include_router = Mock()
    app.exception_handler = Mock()
    return app


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "app_name": "MetaMCP Test",
        "app_version": "1.0.0-test",
        "debug": True,
        "environment": "test",
        "telemetry_enabled": False,
        "vector_search_enabled": False,
        "policy_enforcement_enabled": False,
        "database_url": "sqlite:///:memory:",
        "weaviate_url": "http://localhost:8080",
        "openai_api_key": "test_key",
        "secret_key": "test_secret_key",
        "opa_url": "http://localhost:8181"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """Setup test environment."""
    # Override settings for testing
    for key, value in test_config.items():
        if hasattr(get_settings(), key):
            setattr(get_settings(), key, value)

    yield

    # Cleanup
    reload_settings()


@pytest.fixture
def async_client():
    """Async HTTP client for testing."""
    import httpx
    return httpx.AsyncClient()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.receive_text = AsyncMock(return_value='{"type": "test"}')
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


# Test utilities
def create_mock_response(status_code: int = 200, content: dict[str, Any] = None):
    """Create a mock response."""
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=content or {})
    return response


def create_mock_request(method: str = "GET", path: str = "/", headers: dict[str, str] = None):
    """Create a mock request."""
    request = Mock()
    request.method = method
    request.url.path = path
    request.headers = headers or {}
    return request


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Mark tests without explicit marker as unit tests
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)

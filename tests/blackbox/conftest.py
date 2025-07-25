"""
Black Box Test Configuration

Common fixtures and utilities for black box testing of MetaMCP container.
"""

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
import websockets
from websockets.exceptions import ConnectionClosed

# Test Configuration
BASE_URL = "http://localhost:8000"
import uuid

API_BASE_URL = f"{BASE_URL}/api/v1/"
WS_URL = f"{BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')}/mcp/ws"

# Test Data
TEST_USER = {"username": "admin", "password": "admin123"}

TEST_TOOL = {
    "name": f"test_calculator_{uuid.uuid4().hex[:8]}",
    "description": "Simple calculator for testing",
    "endpoint": "http://localhost:8001",
    "category": "math",
    "capabilities": ["read", "execute"],
    "security_level": 1,
    "schema": {
        "input": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
            },
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "output": {"result": {"type": "number"}},
    },
    "metadata": {"version": "1.0.0"},
    "version": "1.0.0",
    "author": "test_author",
    "tags": ["test", "calculator"],
}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for REST API testing."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def authenticated_client(
    http_client: httpx.AsyncClient,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client with authentication token."""
    # Login to get token
    login_response = await http_client.post(
        f"{API_BASE_URL}/auth/login", json=TEST_USER
    )

    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        http_client.headers["Authorization"] = f"Bearer {token}"

    yield http_client


@pytest.fixture
async def websocket_connection() -> (
    AsyncGenerator[websockets.WebSocketServerProtocol, None]
):
    """WebSocket connection for MCP protocol testing."""
    try:
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize MCP session
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "BlackBoxTestClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            if "error" in response_data:
                pytest.fail(f"MCP initialization failed: {response_data['error']}")

            yield websocket

    except ConnectionClosed:
        pytest.fail("WebSocket connection closed unexpectedly")
    except Exception as e:
        pytest.fail(f"Failed to establish WebSocket connection: {e}")


@pytest.fixture
async def test_tool_id(
    authenticated_client: httpx.AsyncClient,
) -> AsyncGenerator[str, None]:
    """Register a test tool and return its ID."""
    # Register test tool
    response = await authenticated_client.post(f"{API_BASE_URL}/tools", json=TEST_TOOL)

    if response.status_code == 200:
        tool_id = response.json()["data"]["tool_id"]
        yield tool_id

        # Cleanup: delete test tool
        try:
            await authenticated_client.delete(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
            )
        except Exception:
            pass  # Ignore cleanup errors
    else:
        pytest.fail(f"Failed to register test tool: {response.text}")


def wait_for_service(max_retries: int = 30, delay: float = 2.0) -> bool:
    """Wait for the MetaMCP service to be ready."""
    for i in range(max_retries):
        try:
            response = httpx.get(f"{API_BASE_URL}health", timeout=5.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass

        if i < max_retries - 1:
            time.sleep(delay)

    return False


def assert_success_response(
    response: httpx.Response, expected_status: int = 200
) -> dict[str, Any]:
    """Assert that response is successful and return JSON data."""
    assert (
        response.status_code == expected_status
    ), f"Expected {expected_status}, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "success", f"Expected success status, got: {data}"
    return data["data"]


def assert_error_response(
    response: httpx.Response, expected_status: int, expected_error: str = None
) -> dict[str, Any]:
    """Assert that response is an error and return error data."""
    assert (
        response.status_code == expected_status
    ), f"Expected {expected_status}, got {response.status_code}: {response.text}"
    data = response.json()
    assert "error" in data, f"Expected error in response, got: {data}"
    if expected_error:
        assert (
            data["error"] == expected_error
        ), f"Expected error '{expected_error}', got '{data['error']}'"
    return data

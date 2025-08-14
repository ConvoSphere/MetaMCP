"""
Black Box Tests for MCP Protocol

Tests the MCP WebSocket protocol implementation of MetaMCP container.
"""

import asyncio
import json
import time

import pytest
import websockets

from ..conftest import WS_URL


class TestMCPConnection:
    """Test MCP WebSocket connection and initialization."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test basic WebSocket connection."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Connection should be established
            assert websocket.open
            assert not websocket.closed

    @pytest.mark.asyncio
    async def test_mcp_initialization(self):
        """Test MCP protocol initialization."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Send initialization message
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Check response structure
            assert "jsonrpc" in response_data
            assert response_data["jsonrpc"] == "2.0"
            assert "id" in response_data
            assert response_data["id"] == 1

            # Should be success or error, not both
            has_result = "result" in response_data
            has_error = "error" in response_data
            assert (
                has_result != has_error
            ), "Response should have either result or error, not both"

            if has_result:
                result = response_data["result"]
                assert "protocolVersion" in result
                assert "capabilities" in result
            elif has_error:
                error = response_data["error"]
                assert "code" in error
                assert "message" in error

    @pytest.mark.asyncio
    async def test_mcp_initialization_invalid_version(self):
        """Test MCP initialization with invalid protocol version."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "invalid_version",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Should return error for invalid protocol version
            assert "error" in response_data
            error = response_data["error"]
            assert "code" in error
            assert "message" in error

    @pytest.mark.asyncio
    async def test_mcp_initialization_missing_params(self):
        """Test MCP initialization with missing parameters."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                # Missing params
            }

            await websocket.send(json.dumps(init_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Should return error for missing parameters
            assert "error" in response_data
            error = response_data["error"]
            assert "code" in error
            assert "message" in error


class TestMCPTools:
    """Test MCP tool operations."""

    @pytest.mark.asyncio
    async def test_mcp_list_tools(self):
        """Test MCP tools/list operation."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()
            init_data = json.loads(init_response)

            # Should be successful initialization
            assert "result" in init_data

            # List tools
            list_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }

            await websocket.send(json.dumps(list_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Check response structure
            assert "jsonrpc" in response_data
            assert response_data["jsonrpc"] == "2.0"
            assert "id" in response_data
            assert response_data["id"] == 2

            # Should have result with tools array
            assert "result" in response_data
            result = response_data["result"]
            assert "tools" in result
            assert isinstance(result["tools"], list)

    @pytest.mark.asyncio
    async def test_mcp_call_tool(self):
        """Test MCP tools/call operation."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Call tool (assuming a test tool exists)
            call_message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "test_tool",
                    "arguments": {"param1": "value1"},
                },
            }

            await websocket.send(json.dumps(call_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Check response structure
            assert "jsonrpc" in response_data
            assert response_data["jsonrpc"] == "2.0"
            assert "id" in response_data
            assert response_data["id"] == 3

            # Should have result or error
            has_result = "result" in response_data
            has_error = "error" in response_data
            assert has_result or has_error

    @pytest.mark.asyncio
    async def test_mcp_invalid_method(self):
        """Test MCP with invalid method."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send invalid method
            invalid_message = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "invalid_method",
                "params": {},
            }

            await websocket.send(json.dumps(invalid_message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Should return method not found error
            assert "error" in response_data
            error = response_data["error"]
            assert "code" in error
            assert error["code"] == -32601  # Method not found


class TestMCPErrorHandling:
    """Test MCP error handling."""

    @pytest.mark.asyncio
    async def test_mcp_malformed_json(self):
        """Test MCP with malformed JSON."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Send malformed JSON
            await websocket.send('{"invalid": json}')
            response = await websocket.recv()
            response_data = json.loads(response)

            # Should return parse error
            assert "error" in response_data
            error = response_data["error"]
            assert "code" in error
            assert error["code"] == -32700  # Parse error

    @pytest.mark.asyncio
    async def test_mcp_missing_jsonrpc(self):
        """Test MCP with missing jsonrpc field."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            message = {"id": 1, "method": "initialize", "params": {}}
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Should return invalid request error
            assert "error" in response_data
            error = response_data["error"]
            assert "code" in error
            assert error["code"] == -32600  # Invalid request

    @pytest.mark.asyncio
    async def test_mcp_concurrent_requests(self):
        """Test MCP with concurrent requests."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send multiple concurrent requests
            requests = []
            for i in range(5):
                request = {
                    "jsonrpc": "2.0",
                    "id": i + 2,
                    "method": "tools/list",
                    "params": {},
                }
                requests.append(request)

            # Send all requests concurrently
            send_tasks = [websocket.send(json.dumps(req)) for req in requests]
            await asyncio.gather(*send_tasks)

            # Receive all responses
            responses = []
            for _ in range(5):
                response = await websocket.recv()
                responses.append(json.loads(response))

            # Verify all responses have correct structure
            for i, response in enumerate(responses):
                assert "jsonrpc" in response
                assert response["jsonrpc"] == "2.0"
                assert "id" in response
                assert response["id"] == i + 2
                assert "result" in response or "error" in response


class TestMCPConcurrency:
    """Test MCP concurrency and performance."""

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test multiple concurrent WebSocket connections."""
        connections = []
        try:
            # Create multiple connections
            for i in range(3):
                websocket = await websockets.connect(WS_URL, timeout=30.0)
                connections.append(websocket)

                # Initialize each connection
                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "1.0.0",
                        "clientInfo": {"name": f"TestClient{i}", "version": "1.0.0"},
                    },
                }

                await websocket.send(json.dumps(init_message))
                response = await websocket.recv()
                response_data = json.loads(response)

                # Verify successful initialization
                assert "result" in response_data

            # Send concurrent requests from all connections
            request_tasks = []
            for i, websocket in enumerate(connections):
                request = {
                    "jsonrpc": "2.0",
                    "id": i + 1,
                    "method": "tools/list",
                    "params": {},
                }
                task = asyncio.create_task(websocket.send(json.dumps(request)))
                request_tasks.append(task)

            await asyncio.gather(*request_tasks)

            # Receive responses from all connections
            response_tasks = []
            for websocket in connections:
                task = asyncio.create_task(websocket.recv())
                response_tasks.append(task)

            responses = await asyncio.gather(*response_tasks)

            # Verify all responses
            for response in responses:
                response_data = json.loads(response)
                assert "jsonrpc" in response_data
                assert response_data["jsonrpc"] == "2.0"
                assert "result" in response_data or "error" in response_data

        finally:
            # Clean up connections
            for websocket in connections:
                await websocket.close()

    @pytest.mark.asyncio
    async def test_connection_limits(self):
        """Test connection limits and rate limiting."""
        connections = []
        max_connections = 10

        try:
            # Try to create many connections
            for i in range(max_connections):
                try:
                    websocket = await websockets.connect(WS_URL, timeout=10.0)
                    connections.append(websocket)

                    # Quick initialization test
                    init_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "1.0.0",
                            "clientInfo": {
                                "name": f"TestClient{i}",
                                "version": "1.0.0",
                            },
                        },
                    }

                    await websocket.send(json.dumps(init_message))
                    response = await websocket.recv()
                    response_data = json.loads(response)

                    # Verify successful initialization
                    assert "result" in response_data

                except Exception:
                    # Connection limit reached or other error
                    # logger.warning(f"Connection {i} failed: {e}") # Original code had this line commented out
                    break

            # Verify we can handle multiple connections
            assert (
                len(connections) > 0
            ), "Should be able to establish at least one connection"

        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_concurrent_tool_executions(self):
        """Test concurrent tool executions on single connection."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send multiple tool execution requests concurrently
            execution_requests = []
            for i in range(3):
                request = {
                    "jsonrpc": "2.0",
                    "id": i + 2,
                    "method": "tools/call",
                    "params": {
                        "name": "test_tool",
                        "arguments": {"param": f"value{i}"},
                    },
                }
                execution_requests.append(request)

            # Send all requests concurrently
            send_tasks = [websocket.send(json.dumps(req)) for req in execution_requests]
            await asyncio.gather(*send_tasks)

            # Receive all responses
            responses = []
            for _ in range(3):
                response = await websocket.recv()
                responses.append(json.loads(response))

            # Verify all responses
            for i, response in enumerate(responses):
                assert "jsonrpc" in response
                assert response["jsonrpc"] == "2.0"
                assert "id" in response
                assert response["id"] == i + 2
                assert "result" in response or "error" in response

    @pytest.mark.asyncio
    async def test_rapid_requests(self):
        """Test rapid successive requests."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send rapid successive requests
            start_time = time.time()
            for i in range(10):
                request = {
                    "jsonrpc": "2.0",
                    "id": i + 2,
                    "method": "tools/list",
                    "params": {},
                }

                await websocket.send(json.dumps(request))
                response = await websocket.recv()
                response_data = json.loads(response)

                # Verify response
                assert "jsonrpc" in response_data
                assert response_data["jsonrpc"] == "2.0"
                assert "id" in response_data
                assert response_data["id"] == i + 2

            end_time = time.time()
            duration = end_time - start_time

            # Verify reasonable performance (should complete within 5 seconds)
            assert duration < 5.0, f"Rapid requests took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_mixed_request_types(self):
        """Test mixed request types in concurrent scenario."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send mixed request types concurrently
            requests = [
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "test_tool", "arguments": {}},
                },
                {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}},
                {"jsonrpc": "2.0", "id": 5, "method": "prompts/list", "params": {}},
            ]

            # Send all requests concurrently
            send_tasks = [websocket.send(json.dumps(req)) for req in requests]
            await asyncio.gather(*send_tasks)

            # Receive all responses
            responses = []
            for _ in range(4):
                response = await websocket.recv()
                responses.append(json.loads(response))

            # Verify all responses
            for i, response in enumerate(responses):
                assert "jsonrpc" in response
                assert response["jsonrpc"] == "2.0"
                assert "id" in response
                assert response["id"] == i + 2
                assert "result" in response or "error" in response


class TestMCPStress:
    """Test MCP under stress conditions."""

    @pytest.mark.asyncio
    async def test_large_payload_handling(self):
        """Test handling of large payloads."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send request with large payload
            large_payload = "x" * 10000  # 10KB payload
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "test_tool",
                    "arguments": {"large_data": large_payload},
                },
            }

            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            response_data = json.loads(response)

            # Verify response
            assert "jsonrpc" in response_data
            assert response_data["jsonrpc"] == "2.0"
            assert "id" in response_data
            assert response_data["id"] == 2

    @pytest.mark.asyncio
    async def test_connection_stability(self):
        """Test connection stability over time."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {"name": "TestMCPClient", "version": "1.0.0"},
                },
            }

            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()

            # Send requests over time to test stability
            for i in range(20):
                request = {
                    "jsonrpc": "2.0",
                    "id": i + 2,
                    "method": "tools/list",
                    "params": {},
                }

                await websocket.send(json.dumps(request))
                response = await websocket.recv()
                response_data = json.loads(response)

                # Verify response
                assert "jsonrpc" in response_data
                assert response_data["jsonrpc"] == "2.0"
                assert "id" in response_data
                assert response_data["id"] == i + 2

                # Small delay between requests
                await asyncio.sleep(0.1)

            # Verify connection is still open
            assert websocket.open
            assert not websocket.closed

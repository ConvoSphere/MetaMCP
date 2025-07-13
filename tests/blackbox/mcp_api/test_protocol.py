"""
Black Box Tests for MCP Protocol

Tests the MCP WebSocket protocol implementation of MetaMCP container.
"""

import json
import pytest
import websockets
from websockets.exceptions import ConnectionClosed

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
                    "clientInfo": {
                        "name": "TestMCPClient",
                        "version": "1.0.0"
                    }
                }
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
            assert has_result != has_error, "Response should have either result or error, not both"
            
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
                    "clientInfo": {
                        "name": "TestMCPClient",
                        "version": "1.0.0"
                    }
                }
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
                "method": "initialize"
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
    """Test MCP tools protocol methods."""
    
    @pytest.mark.asyncio
    async def test_mcp_list_tools(self):
        """Test MCP tools/list method."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize first
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {
                        "name": "TestMCPClient",
                        "version": "1.0.0"
                    }
                }
            }
            
            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            
            # Only proceed if initialization was successful
            if "error" not in init_data:
                # List tools
                list_message = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                await websocket.send(json.dumps(list_message))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Check response structure
                assert "jsonrpc" in response_data
                assert response_data["jsonrpc"] == "2.0"
                assert "id" in response_data
                assert response_data["id"] == 2
                
                if "result" in response_data:
                    result = response_data["result"]
                    assert "tools" in result
                    assert isinstance(result["tools"], list)
                    
                    # Check tool structure if tools exist
                    for tool in result["tools"]:
                        assert "name" in tool
                        assert "description" in tool
                        assert "inputSchema" in tool
                        assert "outputSchema" in tool
                elif "error" in response_data:
                    # Error is acceptable if no tools are available
                    error = response_data["error"]
                    assert "code" in error
                    assert "message" in error
    
    @pytest.mark.asyncio
    async def test_mcp_call_tool(self):
        """Test MCP tools/call method."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize first
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {
                        "name": "TestMCPClient",
                        "version": "1.0.0"
                    }
                }
            }
            
            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            
            # Only proceed if initialization was successful
            if "error" not in init_data:
                # Call a non-existent tool
                call_message = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "nonexistent_tool",
                        "arguments": {
                            "param1": "value1"
                        }
                    }
                }
                
                await websocket.send(json.dumps(call_message))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Should return error for non-existent tool
                assert "error" in response_data
                error = response_data["error"]
                assert "code" in error
                assert "message" in error
    
    @pytest.mark.asyncio
    async def test_mcp_invalid_method(self):
        """Test MCP with invalid method."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Initialize first
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "clientInfo": {
                        "name": "TestMCPClient",
                        "version": "1.0.0"
                    }
                }
            }
            
            await websocket.send(json.dumps(init_message))
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            
            # Only proceed if initialization was successful
            if "error" not in init_data:
                # Call invalid method
                invalid_message = {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "invalid/method",
                    "params": {}
                }
                
                await websocket.send(json.dumps(invalid_message))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Should return error for invalid method
                assert "error" in response_data
                error = response_data["error"]
                assert "code" in error
                assert "message" in error


class TestMCPErrorHandling:
    """Test MCP protocol error handling."""
    
    @pytest.mark.asyncio
    async def test_mcp_malformed_json(self):
        """Test MCP with malformed JSON."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Send malformed JSON
            await websocket.send('{"invalid": json}')
            
            # Should handle gracefully (might close connection or send error)
            try:
                response = await websocket.recv()
                response_data = json.loads(response)
                assert "error" in response_data
            except (ConnectionClosed, json.JSONDecodeError):
                # Connection might be closed for malformed JSON
                pass
    
    @pytest.mark.asyncio
    async def test_mcp_missing_jsonrpc(self):
        """Test MCP message without jsonrpc field."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            message = {
                "id": 1,
                "method": "initialize",
                "params": {}
            }
            
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # Should return error for missing jsonrpc
            assert "error" in response_data
            error = response_data["error"]
            assert "code" in error
            assert "message" in error
    
    @pytest.mark.asyncio
    async def test_mcp_concurrent_requests(self):
        """Test MCP with concurrent requests."""
        async with websockets.connect(WS_URL, timeout=30.0) as websocket:
            # Send multiple requests concurrently
            messages = [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "1.0.0",
                        "clientInfo": {
                            "name": "TestMCPClient",
                            "version": "1.0.0"
                        }
                    }
                },
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
            ]
            
            # Send all messages
            for message in messages:
                await websocket.send(json.dumps(message))
            
            # Receive all responses
            responses = []
            for _ in range(len(messages)):
                response = await websocket.recv()
                responses.append(json.loads(response))
            
            # Check that we got responses for all requests
            assert len(responses) == len(messages)
            
            # Check that each response has the correct ID
            for i, response in enumerate(responses):
                assert "id" in response
                assert response["id"] == i + 1 
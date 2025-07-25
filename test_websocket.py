#!/usr/bin/env python3
"""Simple WebSocket test for MCP endpoint."""

import asyncio

import websockets


async def test_websocket():
    """Test WebSocket connection to MCP endpoint."""
    try:
        async with websockets.connect('ws://localhost:8000/mcp/ws'):
            print("WebSocket connection successful!")
            return True
    except Exception as e:
        print(f"WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    print(f"Test result: {result}")

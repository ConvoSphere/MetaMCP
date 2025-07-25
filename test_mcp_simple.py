#!/usr/bin/env python3
"""Simple MCP endpoint test without WebSocket."""

import asyncio
import httpx

async def test_mcp_endpoints():
    """Test MCP HTTP endpoints."""
    async with httpx.AsyncClient() as client:
        # Test MCP tools endpoint
        try:
            response = await client.get("http://localhost:9000/mcp/tools")
            print(f"MCP tools endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
        except Exception as e:
            print(f"MCP tools endpoint error: {e}")
        
        # Test MCP root endpoint
        try:
            response = await client.get("http://localhost:9000/mcp/")
            print(f"MCP root endpoint: {response.status_code}")
        except Exception as e:
            print(f"MCP root endpoint error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_endpoints()) 
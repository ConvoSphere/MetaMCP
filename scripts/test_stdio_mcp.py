#!/usr/bin/env python3
"""
Stdio MCP Transport Test Script

This script tests the stdio transport functionality of the MetaMCP server.
It can be used to verify that the stdio MCP server works correctly.
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict


class StdioMCPTester:
    """Test client for stdio MCP transport."""

    def __init__(self):
        """Initialize the tester."""
        self.test_results = []

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the stdio MCP server and receive response."""
        try:
            # Send message to stdout (which should be connected to the server's stdin)
            message_str = json.dumps(message) + "\n"
            sys.stdout.write(message_str)
            sys.stdout.flush()

            # Read response from stdin (which should be connected to the server's stdout)
            response_line = sys.stdin.readline()
            if not response_line:
                raise Exception("No response received from server")

            response = json.loads(response_line.strip())
            return response

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
        except Exception as e:
            raise Exception(f"Communication error: {e}")

    async def test_initialization(self) -> bool:
        """Test MCP initialization."""
        print("Testing MCP initialization...")

        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "clientInfo": {"name": "StdioMCPTester", "version": "1.0.0"},
            },
        }

        try:
            response = await self.send_message(message)

            if "error" in response:
                print(f"❌ Initialization failed: {response['error']}")
                return False

            if "result" in response:
                result = response["result"]
                print(f"✅ Initialization successful")
                print(f"   Protocol Version: {result.get('protocolVersion')}")
                print(f"   Server Info: {result.get('serverInfo')}")
                return True

            print("❌ Unexpected response format")
            return False

        except Exception as e:
            print(f"❌ Initialization test failed: {e}")
            return False

    async def test_list_tools(self) -> bool:
        """Test tools/list operation."""
        print("Testing tools/list...")

        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        try:
            response = await self.send_message(message)

            if "error" in response:
                print(f"❌ List tools failed: {response['error']}")
                return False

            if "result" in response:
                result = response["result"]
                tools = result.get("tools", [])
                print(f"✅ List tools successful - Found {len(tools)} tools")

                for tool in tools[:3]:  # Show first 3 tools
                    print(
                        f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}"
                    )

                if len(tools) > 3:
                    print(f"   ... and {len(tools) - 3} more tools")

                return True

            print("❌ Unexpected response format")
            return False

        except Exception as e:
            print(f"❌ List tools test failed: {e}")
            return False

    async def test_call_tool(self) -> bool:
        """Test tools/call operation."""
        print("Testing tools/call...")

        message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {"param1": "value1", "param2": "value2"},
            },
        }

        try:
            response = await self.send_message(message)

            if "error" in response:
                print(f"❌ Call tool failed: {response['error']}")
                return False

            if "result" in response:
                result = response["result"]
                content = result.get("content", [])
                print(f"✅ Call tool successful")
                print(f"   Content: {content}")
                return True

            print("❌ Unexpected response format")
            return False

        except Exception as e:
            print(f"❌ Call tool test failed: {e}")
            return False

    async def test_list_resources(self) -> bool:
        """Test resources/list operation."""
        print("Testing resources/list...")

        message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {},
        }

        try:
            response = await self.send_message(message)

            if "error" in response:
                print(f"❌ List resources failed: {response['error']}")
                return False

            if "result" in response:
                result = response["result"]
                resources = result.get("resources", [])
                print(
                    f"✅ List resources successful - Found {len(resources)} resources"
                )
                return True

            print("❌ Unexpected response format")
            return False

        except Exception as e:
            print(f"❌ List resources test failed: {e}")
            return False

    async def test_list_prompts(self) -> bool:
        """Test prompts/list operation."""
        print("Testing prompts/list...")

        message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "prompts/list",
            "params": {},
        }

        try:
            response = await self.send_message(message)

            if "error" in response:
                print(f"❌ List prompts failed: {response['error']}")
                return False

            if "result" in response:
                result = response["result"]
                prompts = result.get("prompts", [])
                print(f"✅ List prompts successful - Found {len(prompts)} prompts")
                return True

            print("❌ Unexpected response format")
            return False

        except Exception as e:
            print(f"❌ List prompts test failed: {e}")
            return False

    async def test_invalid_method(self) -> bool:
        """Test invalid method handling."""
        print("Testing invalid method...")

        message = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "invalid_method",
            "params": {},
        }

        try:
            response = await self.send_message(message)

            if "error" in response:
                error = response["error"]
                if error.get("code") == -32601:  # Method not found
                    print("✅ Invalid method correctly rejected")
                    return True
                else:
                    print(f"❌ Unexpected error code: {error.get('code')}")
                    return False

            print("❌ Expected error for invalid method")
            return False

        except Exception as e:
            print(f"❌ Invalid method test failed: {e}")
            return False

    async def test_malformed_json(self) -> bool:
        """Test malformed JSON handling."""
        print("Testing malformed JSON...")

        try:
            # Send malformed JSON
            sys.stdout.write('{"invalid": json}\n')
            sys.stdout.flush()

            response_line = sys.stdin.readline()
            if not response_line:
                print("❌ No response for malformed JSON")
                return False

            response = json.loads(response_line.strip())

            if "error" in response:
                error = response["error"]
                if error.get("code") == -32700:  # Parse error
                    print("✅ Malformed JSON correctly rejected")
                    return True
                else:
                    print(f"❌ Unexpected error code: {error.get('code')}")
                    return False

            print("❌ Expected error for malformed JSON")
            return False

        except Exception as e:
            print(f"❌ Malformed JSON test failed: {e}")
            return False

    async def run_all_tests(self) -> None:
        """Run all tests."""
        print("🚀 Starting Stdio MCP Transport Tests")
        print("=" * 50)

        tests = [
            ("Initialization", self.test_initialization),
            ("List Tools", self.test_list_tools),
            ("Call Tool", self.test_call_tool),
            ("List Resources", self.test_list_resources),
            ("List Prompts", self.test_list_prompts),
            ("Invalid Method", self.test_invalid_method),
            ("Malformed JSON", self.test_malformed_json),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 30)

            try:
                result = await test_func()
                if result:
                    passed += 1
                    self.test_results.append((test_name, True, None))
                else:
                    self.test_results.append((test_name, False, "Test failed"))
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
                self.test_results.append((test_name, False, str(e)))

        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)

        for test_name, success, error in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if error:
                print(f"   Error: {error}")

        print(f"\n🎯 Overall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Stdio MCP transport is working correctly.")
            sys.exit(0)
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
            sys.exit(1)


async def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Stdio MCP Transport Test Script")
        print("")
        print(
            "This script tests the stdio transport functionality of the MetaMCP server."
        )
        print("It should be run with stdin/stdout connected to the MCP server.")
        print("")
        print("Usage:")
        print("  python test_stdio_mcp.py")
        print("")
        print("Example with server:")
        print("  python -m metamcp.mcp.server | python test_stdio_mcp.py")
        return

    tester = StdioMCPTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

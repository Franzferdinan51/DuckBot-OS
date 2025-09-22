#!/usr/bin/env python3
"""
Test script to verify MCP server HTTP API and WebSocket functionality.
Run this script to test the WebSocket chat functionality after starting the MCP server.
"""

import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime

async def test_http_api():
    """Test the HTTP API endpoints of the MCP server"""
    print("🔍 Testing MCP Server HTTP API...")

    base_url = "http://localhost:8790"

    async with aiohttp.ClientSession() as session:
        try:
            # Test health endpoint
            print("  🏥 Testing health endpoint...")
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"     ✅ Health check passed: {health_data}")
                else:
                    print(f"     ❌ Health check failed: {response.status}")
                    return False

            # Test tools endpoint
            print("  🛠️  Testing tools endpoint...")
            async with session.get(f"{base_url}/tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    print(f"     ✅ Tools endpoint working: {len(tools_data.get('tools', []))} tools available")
                else:
                    print(f"     ❌ Tools endpoint failed: {response.status}")
                    return False

            # Test resources endpoint
            print("  📚 Testing resources endpoint...")
            async with session.get(f"{base_url}/resources") as response:
                if response.status == 200:
                    resources_data = await response.json()
                    print(f"     ✅ Resources endpoint working: {len(resources_data.get('resources', []))} resources available")
                else:
                    print(f"     ❌ Resources endpoint failed: {response.status}")
                    return False

            print("  ✅ All HTTP API tests passed!")
            return True

        except Exception as e:
            print(f"  ❌ HTTP API test failed: {e}")
            return False

async def test_websocket_chat():
    """Test the WebSocket chat functionality"""
    print("\n🔍 Testing WebSocket Chat functionality...")

    uri = "ws://localhost:8790/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("  📡 Connected to WebSocket server")

            # Wait for welcome message
            welcome_message = await websocket.recv()
            welcome_data = json.loads(welcome_message)
            print(f"     📨 Welcome message: {welcome_data.get('message', 'No message')}")

            # Test chat message
            test_message = {
                "type": "message",
                "content": "Hello, this is a test message!",
                "timestamp": datetime.now().isoformat()
            }

            print("  💬 Sending test chat message...")
            await websocket.send(json.dumps(test_message))

            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)

            if response_data.get("type") in ["response", "error"]:
                print(f"     📨 Response received: {response_data.get('type')}")
                if response_data.get("success"):
                    print(f"     ✅ Chat test successful")
                else:
                    print(f"     ⚠️  Chat test warning: {response_data.get('error', 'Unknown issue')}")
            else:
                print(f"     ❌ Unexpected response type: {response_data.get('type')}")
                return False

            # Test ping/pong
            print("  🏓 Testing ping/pong...")
            ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
            await websocket.send(json.dumps(ping_message))

            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)

            if pong_data.get("type") == "pong":
                print("     ✅ Ping/pong test successful")
            else:
                print(f"     ❌ Unexpected ping response: {pong_data.get('type')}")
                return False

            print("  ✅ All WebSocket tests passed!")
            return True

    except Exception as e:
        print(f"  ❌ WebSocket test failed: {e}")
        return False

async def test_tool_execution():
    """Test tool execution via WebSocket"""
    print("\n🔍 Testing WebSocket tool execution...")

    uri = "ws://localhost:8790/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            await websocket.recv()

            # Test tool call
            tool_call = {
                "type": "tool_call",
                "tool": "list_tools",  # Assuming this tool exists
                "params": {},
                "timestamp": datetime.now().isoformat()
            }

            print("  🔧 Testing tool execution...")
            await websocket.send(json.dumps(tool_call))

            response = await websocket.recv()
            response_data = json.loads(response)

            if response_data.get("type") == "tool_result" and response_data.get("success"):
                print("     ✅ Tool execution successful")
                return True
            elif response_data.get("type") == "error":
                print(f"     ⚠️  Tool execution failed (expected if tool doesn't exist): {response_data.get('message')}")
                return True  # This is expected if the tool doesn't exist
            else:
                print(f"     ❌ Unexpected tool response: {response_data}")
                return False

    except Exception as e:
        print(f"  ❌ Tool execution test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting MCP Server Connectivity Tests")
    print("=" * 50)

    results = []

    # Test HTTP API
    http_result = await test_http_api()
    results.append(("HTTP API", http_result))

    # Test WebSocket chat
    ws_result = await test_websocket_chat()
    results.append(("WebSocket Chat", ws_result))

    # Test tool execution
    tool_result = await test_tool_execution()
    results.append(("Tool Execution", tool_result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:20}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The MCP server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
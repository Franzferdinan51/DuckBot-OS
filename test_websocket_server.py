#!/usr/bin/env python3
"""
Test WebSocket Server Functionality
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import websockets
    from simple_websocket_server import DuckBotWebSocketServer
    print("WebSocket imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_server():
    """Test WebSocket server functionality"""
    print("\nTesting WebSocket Server Implementation...")

    # Test 1: Server initialization
    print("\n1. Testing server initialization...")
    try:
        server = DuckBotWebSocketServer(mcp_port=8791, chat_port=8792)
        print("Server initialization successful")
        print(f"   - MCP Port: {server.mcp_port}")
        print(f"   - Chat Port: {server.chat_port}")
        print(f"   - Running state: {server.running}")
    except Exception as e:
        print(f"Server initialization failed: {e}")
        return False

    # Test 2: Command handling
    print("\n2. Testing command handling...")
    try:
        response = await server.handle_command("get_status")
        print("Command handling successful")
        print(f"   - Response type: {response.get('type')}")
        print(f"   - Status: {response.get('status')}")
    except Exception as e:
        print(f"Command handling failed: {e}")
        return False

    # Test 3: Chat message handling
    print("\n3. Testing chat message handling...")
    try:
        response = await server.handle_chat_message("Hello DuckBot")
        print("Chat message handling successful")
        print(f"   - Response type: {response.get('type')}")
        print(f"   - Message length: {len(response.get('message', ''))}")
    except Exception as e:
        print(f"Chat message handling failed: {e}")
        return False

    # Test 4: Invalid command handling
    print("\n4. Testing invalid command handling...")
    try:
        response = await server.handle_command("invalid_command")
        print("Invalid command handling successful")
        print(f"   - Error response: {response.get('status')}")
    except Exception as e:
        print(f"Invalid command handling failed: {e}")
        return False

    return True

async def test_websocket_connectivity():
    """Test WebSocket connectivity"""
    print("\nTesting WebSocket Connectivity...")

    # Start a test server
    server = DuckBotWebSocketServer(mcp_port=8793, chat_port=8794)

    # Start server in background
    server_task = asyncio.create_task(server.start_server())

    # Give server time to start
    await asyncio.sleep(1)

    try:
        # Test MCP connection
        print("\n1. Testing MCP WebSocket connection...")
        async with websockets.connect("ws://localhost:8793") as websocket:
            print("MCP connection established")

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            ping_data = json.loads(response)
            print(f"Ping successful: {ping_data.get('type')}")

            # Send status request
            await websocket.send(json.dumps({"type": "status"}))
            response = await websocket.recv()
            status_data = json.loads(response)
            print(f"Status request successful: {status_data.get('type')}")

            # Send command
            await websocket.send(json.dumps({"type": "command", "command": "get_status"}))
            response = await websocket.recv()
            command_data = json.loads(response)
            print(f"Command successful: {command_data.get('type')}")

    except Exception as e:
        print(f"MCP connection test failed: {e}")
        return False

    try:
        # Test Chat connection
        print("\n2. Testing Chat WebSocket connection...")
        async with websockets.connect("ws://localhost:8794") as websocket:
            print("Chat connection established")

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            ping_data = json.loads(response)
            print(f"Ping successful: {ping_data.get('type')}")

            # Send chat message
            await websocket.send(json.dumps({"type": "message", "message": "Hello"}))
            response = await websocket.recv()
            chat_data = json.loads(response)
            print(f"Chat message successful: {chat_data.get('type')}")

    except Exception as e:
        print(f"Chat connection test failed: {e}")
        return False

    # Stop server
    await server.stop_server()
    server_task.cancel()

    try:
        await server_task
    except asyncio.CancelledError:
        pass

    return True

def test_performance_characteristics():
    """Test performance characteristics"""
    print("\nTesting Performance Characteristics...")

    import psutil
    import time

    # Test memory usage of server instance
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    try:
        server = DuckBotWebSocketServer(mcp_port=8795, chat_port=8796)

        # Test command processing speed
        start_time = time.time()
        for i in range(100):
            asyncio.run(server.handle_command("get_status"))
        end_time = time.time()

        avg_time = (end_time - start_time) / 100
        print(f"Average command processing time: {avg_time:.4f} seconds")

        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = end_memory - start_memory
        print(f"Memory usage increase: {memory_increase:.2f} MB")

        return True

    except Exception as e:
        print(f"Performance test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Starting WebSocket Server Test Suite")
    print("=" * 50)

    tests = [
        ("Server Implementation", test_websocket_server),
        ("WebSocket Connectivity", test_websocket_connectivity),
        ("Performance Characteristics", test_performance_characteristics)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\nRunning {test_name} Tests...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            print(f"{status} {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"FAIL {test_name}: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")

    passed = sum(results.values())
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    return passed == total

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite error: {e}")
        sys.exit(1)
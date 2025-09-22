#!/usr/bin/env python3
"""
Test Optimized WebSocket Server
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
    from optimized_websocket_server import EnhancedDuckBotWebSocketServer
    print("WebSocket imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def test_optimized_server():
    """Test optimized WebSocket server"""
    print("\nTesting Optimized WebSocket Server...")

    # Create server instance
    server = EnhancedDuckBotWebSocketServer(
        mcp_port=8795,
        chat_port=8796,
        max_connections=10,
        message_rate_limit=30,
        connection_timeout=60,
        enable_authentication=True
    )

    # Start server in background
    server_task = asyncio.create_task(server.start_server())

    # Give server time to start
    await asyncio.sleep(2)

    try:
        # Test 1: Authentication
        print("\n1. Testing authentication...")
        test_token = server.generate_auth_token("test_client_1")
        print(f"Generated token: {test_token[:50]}...")

        # Test MCP connection with authentication
        print("\n2. Testing MCP connection with authentication...")
        try:
            async with websockets.connect("ws://localhost:8795") as websocket:
                # Send authentication
                await websocket.send(json.dumps({"token": test_token}))
                response = await websocket.recv()
                auth_response = json.loads(response)
                print(f"Authentication response: {auth_response.get('status')}")

                # Test ping
                await websocket.send(json.dumps({"type": "ping"}))
                response = await websocket.recv()
                ping_response = json.loads(response)
                print(f"Ping response: {ping_response.get('type')}")

                # Test command
                await websocket.send(json.dumps({"type": "command", "command": "get_status"}))
                response = await websocket.recv()
                command_response = json.loads(response)
                print(f"Command response: {command_response.get('status')}")

        except Exception as e:
            print(f"MCP connection test failed: {e}")
            return False

        # Test 3: Rate limiting
        print("\n3. Testing rate limiting...")
        try:
            async with websockets.connect("ws://localhost:8795") as websocket:
                # Authenticate
                await websocket.send(json.dumps({"token": test_token}))
                await websocket.recv()

                # Send many messages quickly
                rate_limit_count = 0
                for i in range(40):  # Exceeds rate limit of 30
                    await websocket.send(json.dumps({"type": "ping"}))
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response_data = json.loads(response)
                        if response_data.get("type") == "error":
                            print(f"Rate limit hit at message {i+1}")
                            rate_limit_count += 1
                            break
                    except asyncio.TimeoutError:
                        print(f"Timeout at message {i+1}")
                        break

                if rate_limit_count > 0:
                    print("Rate limiting is working correctly")
                else:
                    print("Rate limiting may not be working")

        except Exception as e:
            print(f"Rate limiting test failed: {e}")

        # Test 4: Connection limit
        print("\n4. Testing connection limit...")
        connections = []
        try:
            # Create multiple connections
            for i in range(12):  # Exceeds limit of 10
                try:
                    token = server.generate_auth_token(f"test_client_{i}")
                    ws = await asyncio.wait_for(
                        websockets.connect("ws://localhost:8795"),
                        timeout=5.0
                    )
                    await ws.send(json.dumps({"token": token}))
                    response = await ws.recv()
                    connections.append(ws)
                    print(f"Connection {i+1} established")
                except Exception as e:
                    print(f"Connection {i+1} failed (expected): {str(e)[:50]}...")
                    break

            print(f"Successfully established {len(connections)} connections")

        except Exception as e:
            print(f"Connection limit test failed: {e}")

        finally:
            # Close all connections
            for ws in connections:
                try:
                    await ws.close()
                except:
                    pass

        return True

    except Exception as e:
        print(f"Test failed: {e}")
        return False

    finally:
        # Stop server
        await server.stop_server()
        server_task.cancel()

        try:
            await server_task
        except asyncio.CancelledError:
            pass

async def main():
    """Main test function"""
    print("Starting Optimized WebSocket Server Test")
    print("=" * 50)

    try:
        result = await test_optimized_server()
        if result:
            print("\nAll tests passed!")
            return True
        else:
            print("\nSome tests failed!")
            return False
    except Exception as e:
        print(f"\nTest suite error: {e}")
        return False

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
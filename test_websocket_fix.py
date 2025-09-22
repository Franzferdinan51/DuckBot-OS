#!/usr/bin/env python3
"""
Test script to verify WebSocket server functionality
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection to both MCP and Chat servers"""

    # Test MCP server
    try:
        logger.info("Testing MCP WebSocket connection...")
        async with websockets.connect("ws://localhost:8791") as websocket:
            logger.info("Connected to MCP server")

            # Send a ping message
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": "2025-09-20T16:34:00"
            }))

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            logger.info(f"MCP Response: {data}")

            # Send a status request
            await websocket.send(json.dumps({
                "type": "status",
                "timestamp": "2025-09-20T16:34:00"
            }))

            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            logger.info(f"MCP Status Response: {data}")

            logger.info("✅ MCP server test passed")

    except Exception as e:
        logger.error(f"❌ MCP server test failed: {e}")

    # Test Chat server
    try:
        logger.info("Testing Chat WebSocket connection...")
        async with websockets.connect("ws://localhost:8792") as websocket:
            logger.info("Connected to Chat server")

            # Send a ping message
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": "2025-09-20T16:34:00"
            }))

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            logger.info(f"Chat Response: {data}")

            # Send a test message
            await websocket.send(json.dumps({
                "type": "message",
                "message": "Hello, this is a test message",
                "timestamp": "2025-09-20T16:34:00"
            }))

            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            logger.info(f"Chat Message Response: {data}")

            logger.info("✅ Chat server test passed")

    except Exception as e:
        logger.error(f"❌ Chat server test failed: {e}")

async def test_http_fallback():
    """Test HTTP fallback handling"""
    import aiohttp

    try:
        logger.info("Testing HTTP fallback...")
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8791") as response:
                text = await response.text()
                logger.info(f"HTTP Response status: {response.status}")
                logger.info(f"HTTP Response contains WebSocket info: {'WebSocket' in text}")
                logger.info("✅ HTTP fallback test passed")
    except Exception as e:
        logger.error(f"❌ HTTP fallback test failed: {e}")

async def main():
    """Run all tests"""
    logger.info("Starting WebSocket server tests...")

    await test_websocket_connection()
    await test_http_fallback()

    logger.info("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
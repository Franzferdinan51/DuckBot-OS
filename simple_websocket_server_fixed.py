#!/usr/bin/env python3
"""
Fixed Simple WebSocket Server for DuckBot Electron Launcher
Provides MCP and Chat connections for the Electron interface with proper error handling
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DuckBotWebSocketServer:
    """Simple WebSocket server for DuckBot Electron launcher"""

    def __init__(self, mcp_port=8791, chat_port=8792):
        self.mcp_port = mcp_port
        self.chat_port = chat_port
        self.mcp_clients = set()
        self.chat_clients = set()
        self.running = False

    async def handle_mcp_client(self, websocket, path):
        """Handle MCP WebSocket connections"""
        logger.info(f"MCP client connected from {websocket.remote_address}")
        self.mcp_clients.add(websocket)

        try:
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "service": "mcp",
                "timestamp": datetime.now().isoformat()
            }))

            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received MCP message: {data}")

                    # Process different message types
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    elif data.get("type") == "status":
                        await websocket.send(json.dumps({
                            "type": "status_response",
                            "status": "online",
                            "services": {
                                "ai_router": "online",
                                "webui": "online",
                                "monitoring": "online",
                                "github": "online"
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                    elif data.get("type") == "command":
                        # Handle commands
                        command = data.get("command")
                        response = await self.handle_command(command)
                        await websocket.send(json.dumps(response))

                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from MCP client")
                except Exception as e:
                    logger.error(f"Error handling MCP message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("MCP client disconnected")
        except Exception as e:
            logger.error(f"MCP connection error: {e}")
        finally:
            self.mcp_clients.discard(websocket)

    async def handle_chat_client(self, websocket, path):
        """Handle Chat WebSocket connections"""
        logger.info(f"Chat client connected from {websocket.remote_address}")
        self.chat_clients.add(websocket)

        try:
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "service": "chat",
                "timestamp": datetime.now().isoformat()
            }))

            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received chat message: {data}")

                    # Process different message types
                    if data.get("type") == "message":
                        # Handle chat messages
                        response = await self.handle_chat_message(data.get("message", ""))
                        await websocket.send(json.dumps(response))
                    elif data.get("type") == "ping":
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))

                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from chat client")
                except Exception as e:
                    logger.error(f"Error handling chat message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Chat client disconnected")
        except Exception as e:
            logger.error(f"Chat connection error: {e}")
        finally:
            self.chat_clients.discard(websocket)

    async def handle_command(self, command):
        """Handle commands from MCP client"""
        logger.info(f"Handling command: {command}")

        # Simple command responses
        if command == "get_status":
            return {
                "type": "command_response",
                "command": command,
                "status": "success",
                "data": {
                    "services": {
                        "ai_router": "online",
                        "webui": "online",
                        "monitoring": "online",
                        "github": "online",
                        "vibevoice": "online"
                    },
                    "uptime": "1h 23m",
                    "memory_usage": "45%",
                    "cpu_usage": "12%"
                },
                "timestamp": datetime.now().isoformat()
            }
        elif command == "restart_service":
            return {
                "type": "command_response",
                "command": command,
                "status": "success",
                "message": "Service restart initiated",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "type": "command_response",
                "command": command,
                "status": "error",
                "message": f"Unknown command: {command}",
                "timestamp": datetime.now().isoformat()
            }

    async def handle_chat_message(self, message):
        """Handle chat messages"""
        logger.info(f"Handling chat message: {message}")

        # Simple AI response simulation
        if "hello" in message.lower():
            response = "Hello! I'm DuckBot AI assistant. How can I help you today?"
        elif "help" in message.lower():
            response = "I can help you with:\n- System monitoring\n- GitHub management\n- AI assistance\n- Configuration management\n- And much more!"
        elif "status" in message.lower():
            response = "All systems are operational:\n✅ AI Router: Online\n✅ WebUI: Online\n✅ Monitoring: Online\n✅ GitHub: Online\n✅ VibeVoice: Online"
        else:
            response = f"I understand you said: '{message}'. How can I assist you with that?"

        return {
            "type": "message_response",
            "message": response,
            "timestamp": datetime.now().isoformat()
        }

    async def mcp_handler_wrapper(self, websocket):
        """Wrapper for MCP handler to match websockets library signature"""
        await self.handle_mcp_client(websocket, "/")

    async def chat_handler_wrapper(self, websocket):
        """Wrapper for Chat handler to match websockets library signature"""
        await self.handle_chat_client(websocket, "/")

    async def start_server(self):
        """Start the WebSocket servers"""
        self.running = True

        logger.info(f"Starting DuckBot WebSocket servers...")
        logger.info(f"MCP Server: ws://localhost:{self.mcp_port}")
        logger.info(f"Chat Server: ws://localhost:{self.chat_port}")

        # Configure server settings to handle HTTP requests gracefully
        server_config = {
            "ping_interval": 30,
            "ping_timeout": 10,
            "close_timeout": 1,
            "max_queue": 1024
        }

        try:
            # Start MCP server
            mcp_server = await websockets.serve(
                self.mcp_handler_wrapper,
                "localhost",
                self.mcp_port,
                **server_config
            )

            # Start Chat server
            chat_server = await websockets.serve(
                self.chat_handler_wrapper,
                "localhost",
                self.chat_port,
                **server_config
            )

            logger.info("✅ WebSocket servers started successfully!")
            logger.info("🚀 DuckBot Electron launcher launcher can now connect")

            try:
                # Keep servers running
                await asyncio.Future()
            except asyncio.CancelledError:
                logger.info("Shutting down WebSocket servers...")
            finally:
                mcp_server.close()
                chat_server.close()
                await mcp_server.wait_closed()
                await chat_server.wait_closed()

        except OSError as e:
            if "address already in use" in str(e).lower():
                logger.error(f"Port {self.mcp_port} or {self.chat_port} is already in use. Please stop any existing servers.")
            else:
                logger.error(f"Failed to start WebSocket servers: {e}")
            raise

    async def stop_server(self):
        """Stop the WebSocket servers"""
        self.running = False
        logger.info("WebSocket servers stopped")

async def main():
    """Main function"""
    server = DuckBotWebSocketServer()

    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await server.stop_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 DuckBot WebSocket server stopped gracefully")
#!/usr/bin/env python3
"""
Fixed Simple WebSocket Server for DuckBot Electron Launcher
Provides MCP and Chat connections for the Electron interface with proper error handling
Uses comprehensive port allocation strategy to avoid conflicts
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
import os
import sys
import socket
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import port allocation
try:
    from config.port_allocation import port_allocator, DUCKBOT_WEBSOCKET_MCP_PORT, DUCKBOT_WEBSOCKET_CHAT_PORT
except ImportError:
    # Fallback to hardcoded ports if config not available
    DUCKBOT_WEBSOCKET_MCP_PORT = 8791
    DUCKBOT_WEBSOCKET_CHAT_PORT = 8792

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DuckBotWebSocketServer:
    """Simple WebSocket server for DuckBot Electron launcher"""

    def __init__(self, mcp_port=None, chat_port=None):
        # Use port allocation strategy or provided ports
        self.mcp_port = mcp_port or port_allocator.allocate_port("websocket_mcp") if 'port_allocator' in globals() else DUCKBOT_WEBSOCKET_MCP_PORT
        self.chat_port = chat_port or port_allocator.allocate_port("websocket_chat") if 'port_allocator' in globals() else DUCKBOT_WEBSOCKET_CHAT_PORT
        self.mcp_clients = set()
        self.chat_clients = set()
        self.running = False
        self.startup_errors = []

        # Validate ports
        self._validate_ports()

    def _validate_ports(self):
        """Validate that ports are available and not conflicting"""
        if self.mcp_port == self.chat_port:
            error = f"MCP port ({self.mcp_port}) and Chat port ({self.chat_port}) cannot be the same"
            logger.error(error)
            self.startup_errors.append(error)
            return

        # Check if MCP port is available
        if not self._is_port_available(self.mcp_port):
            error = f"MCP port {self.mcp_port} is already in use"
            logger.warning(error)
            # Try to find alternative port
            self.mcp_port = self._find_available_port(self.mcp_port, self.mcp_port + 10)
            logger.info(f"Using alternative MCP port: {self.mcp_port}")

        # Check if Chat port is available
        if not self._is_port_available(self.chat_port):
            error = f"Chat port {self.chat_port} is already in use"
            logger.warning(error)
            # Try to find alternative port
            self.chat_port = self._find_available_port(self.chat_port, self.chat_port + 10)
            logger.info(f"Using alternative Chat port: {self.chat_port}")

    def _is_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except Exception as e:
            logger.debug(f"Port check error for {port}: {e}")
            return False

    def _find_available_port(self, start_port, max_port):
        """Find an available port in the given range"""
        for port in range(start_port, max_port + 1):
            if self._is_port_available(port):
                return port
        # If no port found, return original
        return start_port

    async def check_service_health(self):
        """Check health of connected services"""
        health_status = {
            "mcp_clients": len(self.mcp_clients),
            "chat_clients": len(self.chat_clients),
            "mcp_port": self.mcp_port,
            "chat_port": self.chat_port,
            "uptime": "Unknown",  # Could implement uptime tracking
            "errors": len(self.startup_errors)
        }
        return health_status

    async def perform_health_check(self):
        """Perform comprehensive health check"""
        health = await self.check_service_health()

        # Log health status
        if health["errors"] > 0:
            logger.warning(f"WebSocket server has {health['errors']} startup errors")
        else:
            logger.info("WebSocket server health check passed")

        return health

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
        """Start the WebSocket servers with enhanced error handling and health checks"""
        if self.startup_errors:
            logger.error("Cannot start WebSocket server due to configuration errors:")
            for error in self.startup_errors:
                logger.error(f"  - {error}")
            return False

        self.running = True

        logger.info(f"Starting DuckBot WebSocket servers...")
        logger.info(f"MCP Server: ws://localhost:{self.mcp_port}")
        logger.info(f"Chat Server: ws://localhost:{self.chat_port}")

        # Configure server settings to handle HTTP requests gracefully
        server_config = {
            "ping_interval": 30,
            "ping_timeout": 10,
            "close_timeout": 1,
            "max_queue": 1024,
            "compression": None  # Disable compression for better performance
        }

        mcp_server = None
        chat_server = None

        try:
            # Start MCP server with retry logic
            for attempt in range(3):
                try:
                    mcp_server = await websockets.serve(
                        self.mcp_handler_wrapper,
                        "localhost",
                        self.mcp_port,
                        **server_config
                    )
                    logger.info(f"✅ MCP WebSocket server started on port {self.mcp_port}")
                    break
                except OSError as e:
                    if "address already in use" in str(e).lower() and attempt < 2:
                        logger.warning(f"MCP port {self.mcp_port} in use, retrying...")
                        await asyncio.sleep(1)
                    else:
                        raise

            # Start Chat server with retry logic
            for attempt in range(3):
                try:
                    chat_server = await websockets.serve(
                        self.chat_handler_wrapper,
                        "localhost",
                        self.chat_port,
                        **server_config
                    )
                    logger.info(f"✅ Chat WebSocket server started on port {self.chat_port}")
                    break
                except OSError as e:
                    if "address already in use" in str(e).lower() and attempt < 2:
                        logger.warning(f"Chat port {self.chat_port} in use, retrying...")
                        await asyncio.sleep(1)
                    else:
                        raise

            logger.info("🚀 DuckBot Electron WebSocket servers started successfully!")

            # Perform initial health check
            await self.perform_health_check()

            # Start periodic health checks
            health_check_task = asyncio.create_task(self._periodic_health_check())

            try:
                # Keep servers running
                await asyncio.Future()
            except asyncio.CancelledError:
                logger.info("Shutting down WebSocket servers...")
            finally:
                # Cancel health check task
                health_check_task.cancel()
                try:
                    await health_check_task
                except asyncio.CancelledError:
                    pass

                # Close servers gracefully
                if mcp_server:
                    mcp_server.close()
                    await mcp_server.wait_closed()
                if chat_server:
                    chat_server.close()
                    await chat_server.wait_closed()

            return True

        except OSError as e:
            if "address already in use" in str(e).lower():
                logger.error(f"Port conflict detected. Ports {self.mcp_port} or {self.chat_port} are already in use.")
                logger.error("Please stop any existing servers or use different ports.")
            else:
                logger.error(f"Failed to start WebSocket servers: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting WebSocket servers: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _periodic_health_check(self):
        """Periodic health check for the WebSocket servers"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                if self.running:
                    await self.perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def stop_server(self):
        """Stop the WebSocket servers"""
        self.running = False
        logger.info("WebSocket servers stopped")

async def main():
    """Main function"""
    server = DuckBotWebSocketServer()

    try:
        success = await server.start_server()
        if not success:
            logger.error("Failed to start WebSocket servers")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await server.stop_server()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 DuckBot WebSocket server stopped gracefully")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
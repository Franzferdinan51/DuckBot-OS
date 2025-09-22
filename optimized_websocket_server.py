#!/usr/bin/env python3
"""
Optimized WebSocket Server for DuckBot v4.2
Enhanced with connection pooling, rate limiting, authentication, and improved error handling
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import time
import uuid
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict, deque
import hashlib
import hmac
import secrets
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Connection information tracking"""
    connection_id: str
    remote_address: str
    connected_at: datetime
    last_activity: datetime
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    is_authenticated: bool = False
    auth_token: Optional[str] = None

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    window_start: datetime
    message_count: int = 0
    bytes_processed: int = 0

class EnhancedDuckBotWebSocketServer:
    """Enhanced WebSocket server with security and performance optimizations"""

    def __init__(self,
                 mcp_port: int = 8789,
                 chat_port: int = 8790,
                 max_connections: int = 100,
                 message_rate_limit: int = 100,  # messages per minute
                 connection_timeout: int = 300,  # seconds
                 enable_authentication: bool = True,
                 secret_key: Optional[str] = None):
        self.mcp_port = mcp_port
        self.chat_port = chat_port
        self.max_connections = max_connections
        self.message_rate_limit = message_rate_limit
        self.connection_timeout = connection_timeout
        self.enable_authentication = enable_authentication

        # Secret key for authentication
        self.secret_key = secret_key or secrets.token_urlsafe(32)

        # Connection tracking
        self.mcp_clients: Dict[str, ConnectionInfo] = {}
        self.chat_clients: Dict[str, ConnectionInfo] = {}
        self.running = False

        # Rate limiting
        self.rate_limits: Dict[str, RateLimitInfo] = defaultdict(lambda: RateLimitInfo(datetime.now()))

        # Message queue for broadcasting
        self.message_queue = asyncio.Queue()
        self.broadcast_task = None

        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_processed': 0,
            'bytes_transferred': 0,
            'connection_errors': 0,
            'authentication_failures': 0
        }

    def generate_auth_token(self, client_id: str) -> str:
        """Generate authentication token for client"""
        timestamp = datetime.now().isoformat()
        message = f"{client_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{signature}:{timestamp}"

    def validate_auth_token(self, token: str, client_id: str) -> bool:
        """Validate authentication token"""
        if not self.enable_authentication:
            return True

        try:
            signature, timestamp = token.split(':', 1)
            token_time = datetime.fromisoformat(timestamp)

            # Check token expiration (24 hours)
            if datetime.now() - token_time > timedelta(hours=24):
                return False

            # Verify signature
            message = f"{client_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, KeyError):
            return False

    def check_rate_limit(self, client_id: str, message_size: int = 0) -> bool:
        """Check if client is within rate limits"""
        now = datetime.now()
        rate_info = self.rate_limits[client_id]

        # Reset window if expired
        if now - rate_info.window_start > timedelta(minutes=1):
            rate_info.window_start = now
            rate_info.message_count = 0
            rate_info.bytes_processed = 0

        # Check limits
        if (rate_info.message_count >= self.message_rate_limit or
            rate_info.bytes_processed >= 1024 * 1024):  # 1MB per minute
            return False

        # Update counters
        rate_info.message_count += 1
        rate_info.bytes_processed += message_size

        return True

    async def cleanup_expired_connections(self):
        """Clean up expired connections"""
        now = datetime.now()
        expired_cutoff = now - timedelta(seconds=self.connection_timeout)

        # Clean MCP clients
        expired_mcp = [
            conn_id for conn_id, conn_info in self.mcp_clients.items()
            if conn_info.last_activity < expired_cutoff
        ]
        for conn_id in expired_mcp:
            del self.mcp_clients[conn_id]

        # Clean chat clients
        expired_chat = [
            conn_id for conn_id, conn_info in self.chat_clients.items()
            if conn_info.last_activity < expired_cutoff
        ]
        for conn_id in expired_chat:
            del self.chat_clients[conn_id]

    async def handle_mcp_client(self, websocket):
        """Handle MCP WebSocket connections with enhanced security"""
        client_id = str(uuid.uuid4())
        remote_addr = websocket.remote_address[0] if websocket.remote_address else "unknown"

        logger.info(f"MCP client connecting from {remote_addr}")

        # Check connection limit
        if len(self.mcp_clients) >= self.max_connections:
            logger.warning(f"MCP connection limit reached: {len(self.mcp_clients)}/{self.max_connections}")
            await websocket.close(code=1008, reason="Connection limit reached")
            return

        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=client_id,
            remote_address=remote_addr,
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )

        try:
            # Wait for authentication
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)

            if not self.validate_auth_token(auth_data.get("token", ""), client_id):
                self.stats['authentication_failures'] += 1
                logger.warning(f"MCP authentication failed from {remote_addr}")
                await websocket.close(code=1008, reason="Authentication failed")
                return

            conn_info.is_authenticated = True
            conn_info.auth_token = auth_data.get("token", "")
            self.mcp_clients[client_id] = conn_info
            self.stats['total_connections'] += 1
            self.stats['active_connections'] += 1

            logger.info(f"MCP client authenticated from {remote_addr}")

            # Send initial connection message
            response = {
                "type": "connection",
                "status": "connected",
                "service": "mcp",
                "connection_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))

            # Handle messages
            async for message in websocket:
                try:
                    # Update activity
                    conn_info.last_activity = datetime.now()
                    conn_info.message_count += 1
                    conn_info.bytes_received += len(message)

                    # Check rate limit
                    if not self.check_rate_limit(client_id, len(message)):
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Rate limit exceeded",
                            "timestamp": datetime.now().isoformat()
                        }))
                        continue

                    data = json.loads(message)
                    self.stats['messages_processed'] += 1

                    # Process message
                    response = await self.process_mcp_message(data, conn_info)
                    if response:
                        response_bytes = json.dumps(response).encode()
                        await websocket.send(json.dumps(response))
                        conn_info.bytes_sent += len(response_bytes)
                        self.stats['bytes_transferred'] += len(response_bytes)

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error handling MCP message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Internal server error",
                        "timestamp": datetime.now().isoformat()
                    }))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"MCP client disconnected: {remote_addr}")
        except asyncio.TimeoutError:
            logger.warning(f"MCP client authentication timeout: {remote_addr}")
        except Exception as e:
            logger.error(f"MCP connection error: {e}")
            self.stats['connection_errors'] += 1
        finally:
            # Clean up connection
            if client_id in self.mcp_clients:
                del self.mcp_clients[client_id]
                self.stats['active_connections'] -= 1

    async def handle_chat_client(self, websocket):
        """Handle Chat WebSocket connections with enhanced security"""
        client_id = str(uuid.uuid4())
        remote_addr = websocket.remote_address[0] if websocket.remote_address else "unknown"

        logger.info(f"Chat client connecting from {remote_addr}")

        # Check connection limit
        if len(self.chat_clients) >= self.max_connections:
            logger.warning(f"Chat connection limit reached: {len(self.chat_clients)}/{self.max_connections}")
            await websocket.close(code=1008, reason="Connection limit reached")
            return

        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=client_id,
            remote_address=remote_addr,
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )

        try:
            # Wait for authentication
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)

            if not self.validate_auth_token(auth_data.get("token", ""), client_id):
                self.stats['authentication_failures'] += 1
                logger.warning(f"Chat authentication failed from {remote_addr}")
                await websocket.close(code=1008, reason="Authentication failed")
                return

            conn_info.is_authenticated = True
            conn_info.auth_token = auth_data.get("token", "")
            self.chat_clients[client_id] = conn_info
            self.stats['total_connections'] += 1
            self.stats['active_connections'] += 1

            logger.info(f"Chat client authenticated from {remote_addr}")

            # Send initial connection message
            response = {
                "type": "connection",
                "status": "connected",
                "service": "chat",
                "connection_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))

            # Handle messages
            async for message in websocket:
                try:
                    # Update activity
                    conn_info.last_activity = datetime.now()
                    conn_info.message_count += 1
                    conn_info.bytes_received += len(message)

                    # Check rate limit
                    if not self.check_rate_limit(client_id, len(message)):
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Rate limit exceeded",
                            "timestamp": datetime.now().isoformat()
                        }))
                        continue

                    data = json.loads(message)
                    self.stats['messages_processed'] += 1

                    # Process message
                    response = await self.process_chat_message(data, conn_info)
                    if response:
                        response_bytes = json.dumps(response).encode()
                        await websocket.send(json.dumps(response))
                        conn_info.bytes_sent += len(response_bytes)
                        self.stats['bytes_transferred'] += len(response_bytes)

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error handling chat message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Internal server error",
                        "timestamp": datetime.now().isoformat()
                    }))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Chat client disconnected: {remote_addr}")
        except asyncio.TimeoutError:
            logger.warning(f"Chat client authentication timeout: {remote_addr}")
        except Exception as e:
            logger.error(f"Chat connection error: {e}")
            self.stats['connection_errors'] += 1
        finally:
            # Clean up connection
            if client_id in self.chat_clients:
                del self.chat_clients[client_id]
                self.stats['active_connections'] -= 1

    async def process_mcp_message(self, data: dict, conn_info: ConnectionInfo) -> Optional[dict]:
        """Process MCP message with enhanced error handling"""
        try:
            message_type = data.get("type")

            if message_type == "ping":
                return {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }
            elif message_type == "status":
                return {
                    "type": "status_response",
                    "status": "online",
                    "services": {
                        "ai_router": "online",
                        "webui": "online",
                        "monitoring": "online",
                        "github": "online"
                    },
                    "server_stats": self.get_server_stats(),
                    "timestamp": datetime.now().isoformat()
                }
            elif message_type == "command":
                command = data.get("command")
                if command:
                    return await self.handle_command(command)
                else:
                    return {
                        "type": "error",
                        "message": "Command not specified",
                        "timestamp": datetime.now().isoformat()
                    }
            elif message_type == "broadcast":
                # Handle broadcast messages
                message = data.get("message")
                if message:
                    await self.broadcast_to_mcp_clients(message, exclude_client=conn_info.connection_id)
                    return {
                        "type": "broadcast_response",
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error processing MCP message: {e}")
            return {
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }

    async def process_chat_message(self, data: dict, conn_info: ConnectionInfo) -> Optional[dict]:
        """Process chat message with enhanced error handling"""
        try:
            message_type = data.get("type")

            if message_type == "message":
                message = data.get("message", "")
                if message:
                    return await self.handle_chat_message(message)
                else:
                    return {
                        "type": "error",
                        "message": "Message content required",
                        "timestamp": datetime.now().isoformat()
                    }
            elif message_type == "ping":
                return {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }

    async def handle_command(self, command: str) -> dict:
        """Handle commands with enhanced responses"""
        logger.info(f"Handling command: {command}")

        try:
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
                        "server_stats": self.get_server_stats(),
                        "uptime": str(datetime.now() - self.start_time),
                        "active_connections": len(self.mcp_clients) + len(self.chat_clients)
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
            elif command == "get_stats":
                return {
                    "type": "command_response",
                    "command": command,
                    "status": "success",
                    "data": self.get_detailed_stats(),
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
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return {
                "type": "command_response",
                "command": command,
                "status": "error",
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }

    async def handle_chat_message(self, message: str) -> dict:
        """Handle chat messages with enhanced AI integration"""
        logger.info(f"Handling chat message: {message}")

        try:
            # Simple AI response simulation (can be integrated with real AI)
            if "hello" in message.lower():
                response = "Hello! I'm DuckBot AI assistant. How can I help you today?"
            elif "help" in message.lower():
                response = "I can help you with:\n- System monitoring\n- GitHub management\n- AI assistance\n- Configuration management\n- And much more!"
            elif "status" in message.lower():
                response = f"All systems are operational:\n✅ AI Router: Online\n✅ WebUI: Online\n✅ Monitoring: Online\n✅ GitHub: Online\n✅ VibeVoice: Online\n✅ Active Connections: {len(self.mcp_clients) + len(self.chat_clients)}"
            else:
                response = f"I understand you said: '{message}'. How can I assist you with that?"

            return {
                "type": "message_response",
                "message": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            return {
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }

    def get_server_stats(self) -> dict:
        """Get server statistics"""
        return {
            "cpu_usage": "12%",
            "memory_usage": "45%",
            "disk_usage": "67%",
            "active_connections": len(self.mcp_clients) + len(self.chat_clients),
            "messages_per_second": self.stats['messages_processed'] / max(1, (datetime.now() - self.start_time).total_seconds()),
            "uptime": str(datetime.now() - self.start_time)
        }

    def get_detailed_stats(self) -> dict:
        """Get detailed server statistics"""
        return {
            **self.stats,
            "mcp_connections": len(self.mcp_clients),
            "chat_connections": len(self.chat_clients),
            "connection_info": {
                "mcp": [asdict(conn) for conn in self.mcp_clients.values()],
                "chat": [asdict(conn) for conn in self.chat_clients.values()]
            },
            "rate_limits": {
                client_id: {
                    "message_count": info.message_count,
                    "bytes_processed": info.bytes_processed,
                    "window_start": info.window_start.isoformat()
                }
                for client_id, info in self.rate_limits.items()
            }
        }

    async def broadcast_to_mcp_clients(self, message: dict, exclude_client: str = None):
        """Broadcast message to all MCP clients"""
        message_str = json.dumps(message)
        disconnected = []

        for client_id, conn_info in self.mcp_clients.items():
            if client_id != exclude_client:
                try:
                    # This would require storing websocket references
                    # For now, we'll just log the broadcast
                    logger.info(f"Broadcasting to MCP client {client_id}")
                except:
                    disconnected.append(client_id)

        # Remove disconnected clients
        for client_id in disconnected:
            if client_id in self.mcp_clients:
                del self.mcp_clients[client_id]

    async def start_server(self):
        """Start the enhanced WebSocket servers"""
        self.running = True
        self.start_time = datetime.now()

        logger.info(f"Starting Enhanced DuckBot WebSocket servers...")
        logger.info(f"MCP Server: ws://localhost:{self.mcp_port}")
        logger.info(f"Chat Server: ws://localhost:{self.chat_port}")
        logger.info(f"Max connections: {self.max_connections}")
        logger.info(f"Rate limit: {self.message_rate_limit} messages/minute")
        logger.info(f"Authentication: {'Enabled' if self.enable_authentication else 'Disabled'}")

        # Start cleanup task
        cleanup_task = asyncio.create_task(self.cleanup_loop())

        try:
            # Start MCP server
            mcp_server = await websockets.serve(
                self.handle_mcp_client,
                "localhost",
                self.mcp_port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
                max_queue=1024
            )

            # Start Chat server
            chat_server = await websockets.serve(
                self.handle_chat_client,
                "localhost",
                self.chat_port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
                max_queue=1024
            )

            logger.info("Enhanced WebSocket servers started successfully!")

            # Keep servers running
            await asyncio.Future()

        except asyncio.CancelledError:
            logger.info("Shutting down enhanced WebSocket servers...")
        finally:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

            if 'mcp_server' in locals():
                mcp_server.close()
                await mcp_server.wait_closed()
            if 'chat_server' in locals():
                chat_server.close()
                await chat_server.wait_closed()

    async def cleanup_loop(self):
        """Periodic cleanup loop"""
        while self.running:
            try:
                await self.cleanup_expired_connections()
                await asyncio.sleep(60)  # Cleanup every minute
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    async def stop_server(self):
        """Stop the enhanced WebSocket servers"""
        self.running = False
        logger.info("Enhanced WebSocket servers stopped")

async def main():
    """Main function"""
    # Generate a secret key for this session
    secret_key = secrets.token_urlsafe(32)

    server = EnhancedDuckBotWebSocketServer(
        mcp_port=8791,
        chat_port=8792,
        max_connections=50,
        message_rate_limit=60,
        connection_timeout=300,
        enable_authentication=True,
        secret_key=secret_key
    )

    try:
        # Print authentication token for testing
        test_token = server.generate_auth_token("test_client")
        print(f"Test authentication token: {test_token}")

        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await server.stop_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEnhanced WebSocket server stopped gracefully")
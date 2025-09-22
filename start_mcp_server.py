#!/usr/bin/env python3
"""
DuckBot MCP Server Startup Script
Handles proper initialization and startup of the MCP server with error handling
Uses comprehensive port allocation strategy to avoid conflicts
"""

import asyncio
import logging
import sys
import os
import socket
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import port allocation
try:
    from config.port_allocation import port_allocator, DUCKBOT_MCP_SERVER_PORT
except ImportError:
    # Fallback to hardcoded port if config not available
    DUCKBOT_MCP_SERVER_PORT = 8794

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'mcp_server_startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def _is_port_available(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            result = s.connect_ex(('localhost', port))
            return result != 0
    except Exception:
        return False

def _find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port"""
    for offset in range(max_attempts):
        port = start_port + offset
        if _is_port_available(port):
            return port
    return start_port  # Fallback to original

async def start_mcp_server(host="127.0.0.1", port=None):
    """Start the MCP server with proper error handling and port allocation"""
    try:
        # Use port allocation strategy or provided port
        if port is None:
            port = port_allocator.allocate_port("mcp_server") if 'port_allocator' in globals() else DUCKBOT_MCP_SERVER_PORT

        logger.info(f"Starting DuckBot MCP Server on {host}:{port}...")

        # Check if port is available
        if not _is_port_available(port):
            logger.warning(f"Port {port} is already in use, finding alternative...")
            port = _find_available_port(port)
            logger.info(f"Using port {port} for MCP server")

        # Import here to handle any import errors gracefully
        try:
            from duckbot.integrations.mcp_server import DuckBotMCPServer, MCP_AVAILABLE, DUCKBOT_INTEGRATIONS_AVAILABLE

            logger.info(f"MCP Available: {MCP_AVAILABLE}")
            logger.info(f"DuckBot Integrations Available: {DUCKBOT_INTEGRATIONS_AVAILABLE}")

            if not MCP_AVAILABLE:
                logger.warning("MCP library not available - server will run in fallback mode")

            # Create and start server
            server = DuckBotMCPServer()

            # Try to initialize the server first
            try:
                await server.initialize_mcp_server()
                logger.info("MCP Server initialized successfully")
            except Exception as e:
                logger.warning(f"MCP Server initialization failed: {e}")
                logger.info("Continuing with fallback mode")

            # Start the server with enhanced error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    current_port = port + attempt  # Try specified port and next two
                    await server.start(host=host, port=current_port)
                    logger.info(f"MCP Server started successfully on {host}:{current_port}")
                    return server
                except Exception as e:
                    if "Address already in use" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Port {current_port} is in use, trying port {current_port + 1}...")
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"Failed to start MCP server: {e}")
                        return None

        except ImportError as e:
            logger.error(f"Failed to import MCP server: {e}")
            import traceback
            logger.error(f"Import error traceback: {traceback.format_exc()}")
            return None

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        import traceback
        logger.error(f"General exception traceback: {traceback.format_exc()}")
        return None

async def main():
    """Main startup function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DuckBot MCP Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=None, help=f'Port to bind to (default: {DUCKBOT_MCP_SERVER_PORT})')
    parser.add_argument('--mcp-only', action='store_true', help='Run in MCP-only mode')

    args = parser.parse_args()

    # Use provided port or default from allocation
    port = args.port if args.port else DUCKBOT_MCP_SERVER_PORT

    logger.info(f"=== DuckBot MCP Server Startup ===")
    logger.info(f"Host: {args.host}, Port: {port}")

    # Check if logs directory exists
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    try:
        server = await start_mcp_server(host=args.host, port=port)
        if server:
            logger.info(f"MCP Server is running on {args.host}:{port}")
            # Keep the server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down MCP server...")
                await server.stop()
        else:
            logger.error("Failed to start MCP server")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP Server startup interrupted")
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}")
        sys.exit(1)
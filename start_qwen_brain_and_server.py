#!/usr/bin/env python3
"""
Combined Qwen3-Omni Brain and Server startup script
This script starts both the model and the API server in one process
"""

import asyncio
import sys
import os
import time
import signal
import socket

# Add current directory to path
sys.path.append(os.getcwd())

from duckbot.core.qwen3_omni_integration import qwen3_omni_integration
from qwen3_omni_server import app, uvicorn

def get_local_ip():
    """Get local IP address for network access"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "127.0.0.1"

def get_mcp_server_info():
    """Get MCP server connection information"""
    try:
        from config.port_allocation import DUCKBOT_MCP_SERVER_PORT
        port = DUCKBOT_MCP_SERVER_PORT
    except ImportError:
        port = 8794

    local_ip = get_local_ip()
    return {
        "local_url": f"http://localhost:{port}",
        "network_url": f"http://{local_ip}:{port}",
        "local_ws": f"ws://localhost:{port}",
        "network_ws": f"ws://{local_ip}:{port}",
        "port": port
    }

async def start_brain_and_server():
    """Start the Qwen3-Omni AI Brain and API server"""
    try:
        print('=== QWEN3-OMNI AI BRAIN + SERVER STARTING ===')
        print(f'Model path: {qwen3_omni_integration.config.model_id}')
        device_attr = getattr(qwen3_omni_integration, 'device', 'auto')
        print(f'Device: {device_attr}')
        print('')

        print('Loading Qwen3-Omni model with Flash Attention 2...')
        start_time = time.time()
        result = await qwen3_omni_integration.load_model()
        load_time = time.time() - start_time

        if result:
            print(f'+ Qwen3-Omni model loaded successfully in {load_time:.1f}s!')
            status = qwen3_omni_integration.get_status()
            print(f'  - Available: {status["available"]}')
            print(f'  - Device: {status["device"]}')
            print(f'  - Flash Attention: {status["flash_attention"]}')
            print(f'  - Load Time: {status.get("load_time", "N/A")}s')
            memory_info = status.get("memory_available", {})
            if memory_info:
                print(f'  - Memory: {memory_info}')
            else:
                print('  - Memory: Not available')
        else:
            print('X Failed to load Qwen3-Omni model!')
            return

        print('')
        print('QWEN3-OMNI AI BRAIN IS READY!')
        print('Starting API server on http://localhost:5000')
        print('')
        # Add MCP server information
        mcp_info = get_mcp_server_info()
        print('🔌 MCP Server Connection Information:')
        print(f'   Type: STDIO (Standard Input/Output) - Primary Mode')
        print(f'   Fallback: HTTP Server (Port 8000)')
        print(f'   Local Access:    {mcp_info["local_url"]}')
        print(f'   Network Access:  {mcp_info["network_url"]}')
        print(f'   WebSocket Local:  {mcp_info["local_ws"]}')
        print(f'   WebSocket Network: {mcp_info["network_ws"]}')
        print('')
        print('   STDIO mode for direct process communication')
        print('   HTTP fallback available at localhost:8000')
        print('   Connect external MCP clients using these addresses')
        print('')
        print('Press Ctrl+C to exit.')
        print('')

        # Configure uvicorn to run in the same process
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=5000,
            log_level="info",
            access_log=True
        )

        server = uvicorn.Server(config)

        # Start the server
        await server.serve()

    except KeyboardInterrupt:
        print('\nQwen3-Omni AI Brain + Server stopped by user.')
    except Exception as e:
        print(f'Error starting Qwen3-Omni AI Brain + Server: {e}')
        import traceback
        traceback.print_exc()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f'\nQwen3-Omni AI Brain + Server received signal {signum}, shutting down...')
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the brain and server
    asyncio.run(start_brain_and_server())
#!/usr/bin/env python3
"""
DuckBot Electron Startup Orchestrator
Manages the coordinated startup of all required services for the DuckBot Electron app:
1. MCP Server with WebSocket support
2. React Development Server
3. Enhanced WebUI Backend
4. Service coordination and health monitoring
"""

import asyncio
import logging
import subprocess
import sys
import os
import time
import json
import signal
from pathlib import Path
from typing import Dict, Optional, Any, List
import socket
import urllib.request
import urllib.error

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'electron_orchestrator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ServiceProcess:
    """Manages a single service process"""

    def __init__(self, name: str, command: List[str], cwd: str = None,
                 env: Dict[str, str] = None, health_check_url: str = None):
        self.name = name
        self.command = command
        self.cwd = cwd or str(project_root)
        self.env = env or {}
        self.health_check_url = health_check_url
        self.process = None
        self.startup_time = None
        self.is_running = False
        self.retry_count = 0
        self.max_retries = 3

    async def start(self) -> bool:
        """Start the service process"""
        try:
            logger.info(f"Starting {self.name}...")

            # Prepare environment
            env = {**os.environ, **self.env}

            # Start process
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                cwd=self.cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.startup_time = time.time()
            self.is_running = True

            # Start output monitoring
            asyncio.create_task(self._monitor_output())

            logger.info(f"{self.name} started with PID {self.process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            self.retry_count += 1
            return False

    async def stop(self):
        """Stop the service process"""
        if self.process and not self.process.returncode:
            try:
                self.process.terminate()
                await asyncio.sleep(2)
                if self.process.returncode is None:
                    self.process.kill()
                logger.info(f"{self.name} stopped")
            except Exception as e:
                logger.error(f"Error stopping {self.name}: {e}")

        self.is_running = False

    async def _monitor_output(self):
        """Monitor process output"""
        if not self.process:
            return

        try:
            async for line in self.process.stdout:
                line_str = line.decode().strip()
                if line_str:
                    logger.info(f"[{self.name}] {line_str}")

            async for line in self.process.stderr:
                line_str = line.decode().strip()
                if line_str:
                    logger.error(f"[{self.name} ERROR] {line_str}")

        except Exception as e:
            logger.error(f"Error monitoring {self.name} output: {e}")

        # Process has terminated
        self.is_running = False
        logger.warning(f"{self.name} process terminated")

    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        if not self.health_check_url or not self.is_running:
            return self.is_running

        try:
            async with asyncio.timeout(5):
                reader, writer = await asyncio.open_connection(
                    self.health_check_url.split(':')[1][2:],
                    int(self.health_check_url.split(':')[2])
                )
                writer.close()
                await writer.wait_closed()
                return True
        except:
            return False

class ElectronOrchestrator:
    """Orchestrates the startup of all required services"""

    def __init__(self):
        self.services: Dict[str, ServiceProcess] = {}
        self.shutdown_requested = False

    def add_service(self, name: str, service: ServiceProcess):
        """Add a service to the orchestrator"""
        self.services[name] = service

    async def start_services(self, startup_order: List[str]) -> bool:
        """Start all services in the specified order"""
        logger.info("=== Starting DuckBot Electron Services ===")

        for service_name in startup_order:
            if service_name not in self.services:
                logger.error(f"Service {service_name} not found")
                continue

            service = self.services[service_name]

            # Start the service
            success = await service.start()
            if not success:
                logger.error(f"Failed to start {service_name}")
                return False

            # Wait for service to be ready
            if service.health_check_url:
                logger.info(f"Waiting for {service_name} to be ready...")
                wait_time = 0
                max_wait = 30  # 30 seconds

                while wait_time < max_wait:
                    if await service.health_check():
                        logger.info(f"{service_name} is ready!")
                        break
                    await asyncio.sleep(1)
                    wait_time += 1

                if wait_time >= max_wait:
                    logger.error(f"{service_name} failed to become ready within {max_wait} seconds")
                    return False

            # Small delay between service startups
            await asyncio.sleep(2)

        logger.info("=== All services started successfully ===")
        return True

    async def monitor_services(self):
        """Monitor all services and restart if needed"""
        while not self.shutdown_requested:
            for name, service in self.services.items():
                if not service.is_running and service.retry_count < service.max_retries:
                    logger.warning(f"Service {name} is not running, attempting restart...")
                    await service.start()

                # Periodic health check
                if service.is_running and service.health_check_url:
                    if not await service.health_check():
                        logger.warning(f"Service {name} health check failed")
                        await service.stop()
                        if service.retry_count < service.max_retries:
                            await service.start()

            await asyncio.sleep(10)  # Check every 10 seconds

    async def shutdown(self):
        """Shutdown all services"""
        logger.info("=== Shutting down DuckBot Electron Services ===")
        self.shutdown_requested = True

        for name, service in self.services.items():
            await service.stop()

        logger.info("=== All services stopped ===")

def is_port_available(port: int) -> bool:
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except OSError:
        return False

def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port"""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    return start_port  # Return original if none found

async def main():
    """Main orchestration function"""
    # Find available ports
    mcp_port = find_available_port(8791)
    react_port = find_available_port(3000)
    webui_port = find_available_port(8787)

    logger.info(f"Using ports: MCP={mcp_port}, React={react_port}, WebUI={webui_port}")

    # Create orchestrator
    orchestrator = ElectronOrchestrator()

    # Ensure logs directory exists
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Create services
    services = {
        'mcp_server': ServiceProcess(
            name='MCP Server',
            command=[sys.executable, 'start_mcp_server.py', '--host', '127.0.0.1', '--port', str(mcp_port)],
            env={
                'DUCKBOT_MCP_MODE': 'electron',
                'PYTHONPATH': str(project_root)
            },
            health_check_url=f'http://127.0.0.1:{mcp_port}/health'
        ),
        'react_server': ServiceProcess(
            name='React Development Server',
            command=['npm', 'start'],
            cwd=str(project_root / 'duckbot' / 'react-webui'),
            env={
                'BROWSER': 'none',
                'PORT': str(react_port)
            },
            health_check_url=f'http://127.0.0.1:{react_port}'
        ),
        'webui_backend': ServiceProcess(
            name='Enhanced WebUI Backend',
            command=[sys.executable, '-m', 'duckbot.enhanced_webui', '--host', '127.0.0.1', '--port', str(webui_port)],
            env={
                'PYTHONPATH': str(project_root)
            },
            health_check_url=f'http://127.0.0.1:{webui_port}/health'
        )
    }

    # Add services to orchestrator
    for name, service in services.items():
        orchestrator.add_service(name, service)

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(orchestrator.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start services in order
        startup_order = ['webui_backend', 'mcp_server', 'react_server']
        success = await orchestrator.start_services(startup_order)

        if success:
            logger.info("=== DuckBot Electron Services Ready ===")
            logger.info(f"MCP Server: http://127.0.0.1:{mcp_port}")
            logger.info(f"React Dev Server: http://127.0.0.1:{react_port}")
            logger.info(f"WebUI Backend: http://127.0.0.1:{webui_port}")

            # Create service configuration file for Electron app
            config = {
                'services': {
                    'mcp_server': {
                        'port': mcp_port,
                        'url': f'http://127.0.0.1:{mcp_port}'
                    },
                    'react_server': {
                        'port': react_port,
                        'url': f'http://127.0.0.1:{react_port}'
                    },
                    'webui_backend': {
                        'port': webui_port,
                        'url': f'http://127.0.0.1:{webui_port}'
                    }
                },
                'timestamp': time.time()
            }

            config_file = project_root / 'duckbot' / 'react-webui' / 'services_config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Service configuration saved to {config_file}")

            # Start monitoring
            await orchestrator.monitor_services()
        else:
            logger.error("Failed to start all services")
            await orchestrator.shutdown()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
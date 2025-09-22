#!/usr/bin/env python3
"""
DuckBot Service Startup Coordinator
Manages coordinated startup of all services with proper port allocation and dependency management
"""

import asyncio
import logging
import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import port allocation
try:
    from config.port_allocation import port_allocator, DuckBotPortAllocator
except ImportError:
    print("Warning: Port allocation config not found, using defaults")
    # Create minimal fallback
    class DuckBotPortAllocator:
        def allocate_port(self, service): return {"websocket_mcp": 8791, "websocket_chat": 8792, "mcp_server": 8794}.get(service, 8000)
    port_allocator = DuckBotPortAllocator()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    FAILED = "failed"

@dataclass
class ServiceConfig:
    """Service configuration"""
    name: str
    command: List[str]
    port: int
    depends_on: List[str] = None
    startup_delay: float = 0.0
    health_check_url: Optional[str] = None
    required: bool = True
    env_vars: Dict[str, str] = None

@dataclass
class ServiceInstance:
    """Service instance with runtime state"""
    config: ServiceConfig
    process: Optional[subprocess.Popen] = None
    status: ServiceStatus = ServiceStatus.STOPPED
    startup_time: Optional[float] = None
    last_health_check: Optional[float] = None
    health_status: bool = False
    restart_count: int = 0

class ServiceStartupCoordinator:
    """Coordinates startup and management of DuckBot services"""

    def __init__(self):
        self.services: Dict[str, ServiceInstance] = {}
        self.startup_order: List[str] = []
        self.shutdown_requested = False
        self.port_allocator = port_allocator
        self.allocated_ports = set()

    def configure_services(self) -> List[ServiceConfig]:
        """Configure all services with proper port allocation"""
        services = []

        # Core services (must start first)
        services.append(ServiceConfig(
            name="webui",
            command=[sys.executable, "-m", "duckbot.enhanced_webui", "--host", "127.0.0.1"],
            port=self.port_allocator.allocate_port("webui"),
            required=True,
            health_check_url="http://127.0.0.1:{port}/health"
        ))

        services.append(ServiceConfig(
            name="monitoring",
            command=[sys.executable, "ai_ecosystem_manager.py", "--host", "127.0.0.1"],
            port=self.port_allocator.allocate_port("monitoring"),
            required=True,
            health_check_url="http://127.0.0.1:{port}/health"
        ))

        # WebSocket services
        services.append(ServiceConfig(
            name="websocket_mcp",
            command=[sys.executable, "simple_websocket_server.py"],
            port=self.port_allocator.allocate_port("websocket_mcp"),
            depends_on=["webui", "monitoring"],
            required=True,
            startup_delay=2.0
        ))

        services.append(ServiceConfig(
            name="mcp_server",
            command=[sys.executable, "start_mcp_server.py", "--host", "127.0.0.1"],
            port=self.port_allocator.allocate_port("mcp_server"),
            depends_on=["websocket_mcp"],
            required=True,
            startup_delay=1.0
        ))

        # Development services (optional)
        services.append(ServiceConfig(
            name="react_dev",
            command=["npm", "start"],
            port=self.port_allocator.allocate_port("react_dev"),
            depends_on=["webui"],
            required=False,
            startup_delay=3.0,
            env_vars={"BROWSER": "none", "PORT": "3000"}
        ))

        return services

    def determine_startup_order(self, services: List[ServiceConfig]) -> List[str]:
        """Determine service startup order based on dependencies"""
        # Create dependency graph
        graph = {}
        for service in services:
            graph[service.name] = service.depends_on or []

        # Topological sort
        visited = set()
        temp_visited = set()
        order = []

        def visit(service_name):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            if service_name in visited:
                return

            temp_visited.add(service_name)
            for dep in graph.get(service_name, []):
                if dep in graph:
                    visit(dep)
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)

        for service in services:
            if service.name not in visited:
                visit(service.name)

        return order

    async def start_service(self, service: ServiceConfig) -> bool:
        """Start a single service"""
        if service.name in self.services:
            instance = self.services[service.name]
            if instance.status == ServiceStatus.RUNNING:
                logger.info(f"Service {service.name} is already running")
                return True

        logger.info(f"Starting service: {service.name} on port {service.port}")

        # Prepare environment
        env = os.environ.copy()
        if service.env_vars:
            env.update(service.env_vars)

        # Add port to command if not already present
        command = service.command.copy()
        if "--port" not in command and service.port:
            command.extend(["--port", str(service.port)])

        try:
            # Create service instance
            instance = ServiceInstance(config=service, status=ServiceStatus.STARTING)
            self.services[service.name] = instance

            # Apply startup delay if specified
            if service.startup_delay > 0:
                logger.info(f"Delaying startup of {service.name} by {service.startup_delay}s")
                await asyncio.sleep(service.startup_delay)

            # Start the process
            process = subprocess.Popen(
                command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )

            instance.process = process
            instance.startup_time = time.time()

            # Wait a moment for startup
            await asyncio.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                instance.status = ServiceStatus.RUNNING
                logger.info(f"✅ Service {service.name} started successfully (PID: {process.pid})")

                # Start health monitoring
                asyncio.create_task(self._monitor_service_health(service.name))
                return True
            else:
                instance.status = ServiceStatus.FAILED
                logger.error(f"❌ Service {service.name} failed to start (exit code: {process.returncode})")
                return False

        except Exception as e:
            if service.name in self.services:
                self.services[service.name].status = ServiceStatus.ERROR
            logger.error(f"❌ Failed to start service {service.name}: {e}")
            return False

    async def stop_service(self, service_name: str, force: bool = False) -> bool:
        """Stop a single service"""
        if service_name not in self.services:
            logger.warning(f"Service {service_name} not found")
            return False

        instance = self.services[service_name]
        if instance.status != ServiceStatus.RUNNING:
            logger.info(f"Service {service_name} is not running")
            return True

        logger.info(f"Stopping service: {service_name}")
        instance.status = ServiceStatus.STOPPING

        try:
            if instance.process:
                if os.name == 'nt':
                    # Windows
                    instance.process.terminate()
                else:
                    # Unix/Linux
                    instance.process.terminate()

                # Wait for graceful shutdown
                try:
                    instance.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if force:
                        instance.process.kill()
                        instance.process.wait()
                    else:
                        logger.warning(f"Service {service_name} did not stop gracefully")
                        return False

            instance.status = ServiceStatus.STOPPED
            logger.info(f"✅ Service {service_name} stopped successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to stop service {service_name}: {e}")
            instance.status = ServiceStatus.ERROR
            return False

    async def _monitor_service_health(self, service_name: str):
        """Monitor service health"""
        if service_name not in self.services:
            return

        instance = self.services[service_name]
        config = instance.config

        while instance.status == ServiceStatus.RUNNING and not self.shutdown_requested:
            try:
                # Simple health check - just verify process is running
                if instance.process and instance.process.poll() is not None:
                    logger.warning(f"Service {service_name} process has stopped unexpectedly")
                    instance.status = ServiceStatus.ERROR
                    instance.health_status = False
                    break

                # For HTTP services, try HTTP health check
                if config.health_check_url:
                    try:
                        import aiohttp
                        url = config.health_check_url.format(port=config.port)
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                            async with session.get(url) as response:
                                instance.health_status = response.status < 400
                    except:
                        instance.health_status = False
                else:
                    instance.health_status = True

                instance.last_health_check = time.time()

                # Log health status every 5 minutes
                if int(time.time()) % 300 == 0:
                    status = "healthy" if instance.health_status else "unhealthy"
                    logger.info(f"Service {service_name} is {status}")

            except Exception as e:
                logger.error(f"Health check error for {service_name}: {e}")
                instance.health_status = False

            await asyncio.sleep(30)  # Check every 30 seconds

    async def start_all_services(self) -> bool:
        """Start all services in proper order"""
        logger.info("=== Starting DuckBot Service Ecosystem ===")

        # Configure services
        service_configs = self.configure_services()
        self.startup_order = self.determine_startup_order(service_configs)

        logger.info(f"Service startup order: {' -> '.join(self.startup_order)}")

        # Start services in order
        successful_starts = 0
        failed_services = []

        for service_name in self.startup_order:
            if self.shutdown_requested:
                logger.info("Shutdown requested, stopping service startup")
                break

            # Find service config
            service_config = next((s for s in service_configs if s.name == service_name), None)
            if not service_config:
                logger.error(f"Service config not found for {service_name}")
                failed_services.append(service_name)
                continue

            # Start the service
            success = await self.start_service(service_config)
            if success:
                successful_starts += 1
            else:
                failed_services.append(service_name)
                if service_config.required:
                    logger.error(f"Required service {service_name} failed to start")
                    break

        logger.info(f"=== Service Startup Complete ===")
        logger.info(f"Started: {successful_starts}/{len(service_configs)} services")

        if failed_services:
            logger.error(f"Failed services: {', '.join(failed_services)}")

        return len(failed_services) == 0 or all(
            not self.services[name].config.required for name in failed_services
        )

    async def stop_all_services(self):
        """Stop all services in reverse order"""
        logger.info("=== Stopping DuckBot Service Ecosystem ===")

        self.shutdown_requested = True

        # Stop services in reverse order
        for service_name in reversed(self.startup_order):
            if service_name in self.services:
                await self.stop_service(service_name)

        logger.info("=== All Services Stopped ===")

    async def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all services"""
        status = {}
        for name, instance in self.services.items():
            status[name] = {
                "status": instance.status.value,
                "port": instance.config.port,
                "health": instance.health_status,
                "uptime": time.time() - instance.startup_time if instance.startup_time else 0,
                "restart_count": instance.restart_count,
                "required": instance.config.required
            }
        return status

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        if service_name not in self.services:
            logger.error(f"Service {service_name} not found")
            return False

        logger.info(f"Restarting service: {service_name}")
        instance = self.services[service_name]
        instance.restart_count += 1

        # Stop the service
        await self.stop_service(service_name, force=True)

        # Start it again
        return await self.start_service(instance.config)

async def main():
    """Main function"""
    coordinator = ServiceStartupCoordinator()

    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(coordinator.stop_all_services())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start all services
        success = await coordinator.start_all_services()

        if success:
            logger.info("🚀 DuckBot service ecosystem started successfully!")

            # Keep running until shutdown
            try:
                while not coordinator.shutdown_requested:
                    await asyncio.sleep(1)

                    # Log status every 5 minutes
                    if int(time.time()) % 300 == 0:
                        status = await coordinator.get_service_status()
                        running = sum(1 for s in status.values() if s["status"] == "running")
                        logger.info(f"Service status: {running} services running")
            except asyncio.CancelledError:
                pass
        else:
            logger.error("❌ Failed to start some required services")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

    finally:
        await coordinator.stop_all_services()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 DuckBot service coordinator stopped gracefully")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
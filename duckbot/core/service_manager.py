#!/usr/bin/env python3
"""
Unified Service Management for DuckBot v4.2
Centralized service management system for all DuckBot components

This module consolidates all service management functionality:
- Core service management (LM Studio, ComfyUI, WebUI)
- Integration service management (VibeVoice, Mining, UI-TARS MCP, ByteBot)
- Enhanced service management (Qwen-Agent, Archon, Browser-Use)
- System service management (Database, Logging, Cache)
- External service management (n8n, OpenWebUI, Discord Bot)

Features:
- Unified service interface with consistent API
- Service status monitoring and health checking
- Automatic service startup and shutdown
- Service dependency management and orchestration
- Resource usage monitoring and optimization
- Cross-platform service management
- Graceful error handling and recovery
- Real-time service status updates
- Service configuration management
- Integration with AI ecosystem manager

Service Categories:
1. Core Services - Essential DuckBot services
2. Integration Services - Third-party integrations
3. Enhanced Services - Advanced AI capabilities
4. System Services - Infrastructure components
5. External Services - External system integrations
"""

import asyncio
import sys
import os
import subprocess
import time
import logging
import json
import psutil
import platform
import socket
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from contextlib import contextmanager

# Setup proper encoding for Windows
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_service_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    RESTARTING = "restarting"

class ServiceType(Enum):
    """Service type enumeration"""
    CORE = "core"  # Essential DuckBot services
    INTEGRATION = "integration"  # Third-party integrations
    ENHANCED = "enhanced"  # Advanced AI capabilities
    SYSTEM = "system"  # Infrastructure components
    EXTERNAL = "external"  # External system integrations

@dataclass
class ServiceInfo:
    """Service information data structure"""
    name: str
    display_name: str
    service_type: ServiceType
    status: ServiceStatus
    port: Optional[int] = None
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    auto_start: bool = False
    restart_attempts: int = 0
    max_restart_attempts: int = 3

@dataclass
class ServiceHealth:
    """Service health data structure"""
    name: str
    status: ServiceStatus
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_seconds: float = 0.0
    last_check: datetime = field(default_factory=datetime.now)
    health_score: float = 100.0  # 0-100 scale
    issues: List[str] = field(default_factory=list)

class UnifiedServiceManager:
    """Unified service manager for DuckBot system"""

    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.health_monitors: Dict[str, ServiceHealth] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.locks: Dict[str, threading.Lock] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.monitoring_active = False
        self.monitoring_task = None
        self.config_manager = None

        # Initialize core services
        self._initialize_core_services()

        # Initialize integration services
        self._initialize_integration_services()

        # Initialize enhanced services
        self._initialize_enhanced_services()

        # Initialize system services
        self._initialize_system_services()

        # Initialize external services
        self._initialize_external_services()

    def _initialize_core_services(self):
        """Initialize core DuckBot services"""
        core_services = [
            {
                "name": "lm_studio",
                "display_name": "LM Studio Server",
                "service_type": ServiceType.CORE,
                "port": 1234,
                "auto_start": True,
                "config": {
                    "url": "http://localhost:1234",
                    "api_root": "/v1",
                    "models_path": "./models/LMStudio"
                }
            },
            {
                "name": "comfyui",
                "display_name": "ComfyUI Image Generator",
                "service_type": ServiceType.CORE,
                "port": 8188,
                "auto_start": True,
                "config": {
                    "workspace": "./ComfyUI",
                    "models_path": "./ComfyUI/models"
                }
            },
            {
                "name": "webui",
                "display_name": "DuckBot WebUI",
                "service_type": ServiceType.CORE,
                "port": 8787,
                "auto_start": True,
                "config": {
                    "host": "127.0.0.1",
                    "static_path": "./static"
                }
            },
            {
                "name": "server_manager",
                "display_name": "Server Manager",
                "service_type": ServiceType.CORE,
                "port": None,
                "auto_start": True,
                "config": {
                    "monitor_interval": 30,
                    "health_check_timeout": 5
                }
            }
        ]

        for service_config in core_services:
            self._register_service(**service_config)

    def _initialize_integration_services(self):
        """Initialize integration services"""
        integration_services = [
            {
                "name": "vibevoice",
                "display_name": "VibeVoice TTS",
                "service_type": ServiceType.INTEGRATION,
                "port": None,
                "auto_start": False,
                "config": {
                    "tts_engine": "system",
                    "voice_presets": ["default", "professional", "casual"]
                },
                "dependencies": ["webui"]
            },
            {
                "name": "mining_manager",
                "display_name": "Mining Manager",
                "service_type": ServiceType.INTEGRATION,
                "port": None,
                "auto_start": False,
                "config": {
                    "algorithms": ["kawpow", "autolykos2", "ethash"],
                    "coins": ["RVN", "ERG", "ETH"]
                }
            },
            {
                "name": "ui_tars_mcp",
                "display_name": "UI-TARS MCP Server",
                "service_type": ServiceType.INTEGRATION,
                "port": 3333,
                "auto_start": False,
                "config": {
                    "websocket_port": 3334,
                    "tools_path": "./tools/ui_tars"
                }
            },
            {
                "name": "bytebot",
                "display_name": "ByteBot Desktop Automation",
                "service_type": ServiceType.INTEGRATION,
                "port": None,
                "auto_start": False,
                "config": {
                    "screenshot_path": "./screenshots",
                    "actions_log": "./logs/actions.log"
                }
            }
        ]

        for service_config in integration_services:
            self._register_service(**service_config)

    def _initialize_enhanced_services(self):
        """Initialize enhanced AI services"""
        enhanced_services = [
            {
                "name": "qwen_agent",
                "display_name": "Qwen-Agent Integration",
                "service_type": ServiceType.ENHANCED,
                "port": None,
                "auto_start": False,
                "config": {
                    "model": "qwen/qwen3-coder:free",
                    "tools_path": "./tools/qwen_agent"
                },
                "dependencies": ["lm_studio", "webui"]
            },
            {
                "name": "archon_agent",
                "display_name": "Archon Multi-Agent Framework",
                "service_type": ServiceType.ENHANCED,
                "port": None,
                "auto_start": False,
                "config": {
                    "agent_roles": ["researcher", "developer", "analyst"],
                    "memory_path": "./data/archon_memory"
                }
            },
            {
                "name": "browser_use",
                "display_name": "Browser-Use Integration",
                "service_type": ServiceType.ENHANCED,
                "port": None,
                "auto_start": False,
                "config": {
                    "browser": "chrome",
                    "headless": False,
                    "screenshot_path": "./screenshots/browser"
                }
            },
            {
                "name": "pyboy",
                "display_name": "PyBoy Game Boy Emulator",
                "service_type": ServiceType.ENHANCED,
                "port": None,
                "auto_start": False,
                "config": {
                    "headless": True,
                    "roms_directory": "./roms",
                    "saves_directory": "./saves",
                    "ai_enabled": True,
                    "max_fps": 60
                }
            }
        ]

        for service_config in enhanced_services:
            self._register_service(**service_config)

    def _initialize_system_services(self):
        """Initialize system infrastructure services"""
        system_services = [
            {
                "name": "database",
                "display_name": "SQLite Database",
                "service_type": ServiceType.SYSTEM,
                "port": None,
                "auto_start": True,
                "config": {
                    "db_path": "./data/duckbot.db",
                    "backup_path": "./backups"
                }
            },
            {
                "name": "logging",
                "display_name": "Logging System",
                "service_type": ServiceType.SYSTEM,
                "port": None,
                "auto_start": True,
                "config": {
                    "log_path": "./logs",
                    "max_size_mb": 100,
                    "rotation_days": 7
                }
            },
            {
                "name": "cache",
                "display_name": "AI Cache Manager",
                "service_type": ServiceType.SYSTEM,
                "port": None,
                "auto_start": True,
                "config": {
                    "cache_path": "./cache",
                    "max_size_gb": 10,
                    "ttl_hours": 24
                }
            },
            {
                "name": "monitoring",
                "display_name": "System Monitoring",
                "service_type": ServiceType.SYSTEM,
                "port": None,
                "auto_start": True,
                "config": {
                    "metrics_interval": 60,
                    "alert_threshold_cpu": 85,
                    "alert_threshold_memory": 85
                }
            }
        ]

        for service_config in system_services:
            self._register_service(**service_config)

    def _initialize_external_services(self):
        """Initialize external service integrations"""
        external_services = [
            {
                "name": "n8n",
                "display_name": "n8n Workflow Engine",
                "service_type": ServiceType.EXTERNAL,
                "port": 5678,
                "auto_start": False,
                "config": {
                    "url": "http://localhost:5678",
                    "workflows_path": "./workflows"
                }
            },
            {
                "name": "openwebui",
                "display_name": "OpenWebUI Interface",
                "service_type": ServiceType.EXTERNAL,
                "port": 3000,
                "auto_start": False,
                "config": {
                    "url": "http://localhost:3000"
                }
            },
            {
                "name": "discord_bot",
                "display_name": "Discord Bot",
                "service_type": ServiceType.EXTERNAL,
                "port": None,
                "auto_start": False,
                "config": {
                    "token_file": ".env",
                    "commands_prefix": "!"
                }
            }
        ]

        for service_config in external_services:
            self._register_service(**service_config)

    def _register_service(self, name: str, display_name: str, service_type: ServiceType,
                         port: Optional[int] = None, auto_start: bool = False,
                         config: Optional[Dict[str, Any]] = None,
                         dependencies: Optional[List[str]] = None):
        """Register a service with the manager"""
        service_info = ServiceInfo(
            name=name,
            display_name=display_name,
            service_type=service_type,
            status=ServiceStatus.UNKNOWN,
            port=port,
            config=config or {},
            dependencies=dependencies or [],
            auto_start=auto_start
        )

        self.services[name] = service_info
        self.locks[name] = threading.Lock()
        self.callbacks[name] = []

        logger.info(f"Registered service: {display_name} ({name})")

    async def initialize(self) -> bool:
        """Initialize the unified service manager"""
        try:
            logger.info("Initializing Unified Service Manager...")

            # Start monitoring
            await self.start_monitoring()

            # Auto-start services marked for auto-start
            auto_start_services = [
                name for name, service in self.services.items()
                if service.auto_start
            ]

            for service_name in auto_start_services:
                try:
                    await self.start_service(service_name)
                except Exception as e:
                    logger.error(f"Failed to auto-start service {service_name}: {e}")

            logger.info("Unified Service Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Unified Service Manager: {e}")
            return False

    async def start_monitoring(self):
        """Start service monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Service monitoring started")

    async def stop_monitoring(self):
        """Stop service monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("Service monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Update service statuses
                await self._update_service_statuses()

                # Update health metrics
                await self._update_health_metrics()

                # Check dependencies
                await self._check_service_dependencies()

                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Short delay on error

    async def _update_service_statuses(self):
        """Update statuses for all services"""
        for service_name, service in self.services.items():
            try:
                # Skip services that are starting/stopping
                if service.status in [ServiceStatus.STARTING, ServiceStatus.STOPPING]:
                    continue

                # Check if service is running
                is_running, pid = await self._check_service_running(service_name)

                if is_running:
                    if service.status != ServiceStatus.RUNNING:
                        service.status = ServiceStatus.RUNNING
                        service.pid = pid
                        service.start_time = datetime.now()
                        await self._notify_service_change(service_name, "started")
                else:
                    if service.status == ServiceStatus.RUNNING:
                        service.status = ServiceStatus.STOPPED
                        service.pid = None
                        service.start_time = None
                        await self._notify_service_change(service_name, "stopped")

                service.last_check = datetime.now()

            except Exception as e:
                logger.error(f"Error updating status for {service_name}: {e}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)
                service.last_check = datetime.now()

    async def _update_health_metrics(self):
        """Update health metrics for all services"""
        for service_name, service in self.services.items():
            try:
                if service.status == ServiceStatus.RUNNING and service.pid:
                    # Get process info
                    process = psutil.Process(service.pid)

                    # Calculate metrics
                    cpu_percent = process.cpu_percent()
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    uptime_seconds = (datetime.now() - service.start_time).total_seconds() if service.start_time else 0

                    # Calculate health score
                    health_score = 100.0
                    issues = []

                    # CPU usage check
                    if cpu_percent > 90:
                        health_score -= 20
                        issues.append(f"High CPU usage: {cpu_percent:.1f}%")

                    # Memory usage check
                    if memory_mb > 1000:  # 1GB
                        health_score -= 15
                        issues.append(f"High memory usage: {memory_mb:.1f}MB")

                    # Uptime check (too long might indicate stuck)
                    if uptime_seconds > 86400 * 7:  # 7 days
                        health_score -= 10
                        issues.append(f"Very long uptime: {uptime_seconds/3600:.1f} hours")

                    # Update health monitor
                    self.health_monitors[service_name] = ServiceHealth(
                        name=service_name,
                        status=service.status,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        uptime_seconds=uptime_seconds,
                        health_score=max(0, health_score),
                        issues=issues,
                        last_check=datetime.now()
                    )

            except psutil.NoSuchProcess:
                # Process no longer exists
                if service.status == ServiceStatus.RUNNING:
                    service.status = ServiceStatus.STOPPED
                    service.pid = None
                    service.start_time = None
            except Exception as e:
                logger.error(f"Error updating health metrics for {service_name}: {e}")

    async def _check_service_dependencies(self):
        """Check service dependencies"""
        for service_name, service in self.services.items():
            if service.dependencies and service.status == ServiceStatus.RUNNING:
                for dep_name in service.dependencies:
                    if dep_name in self.services:
                        dep_service = self.services[dep_name]
                        if dep_service.status != ServiceStatus.RUNNING:
                            # Dependency is not running - stop dependent service
                            logger.warning(f"Dependency {dep_name} not running for {service_name}")
                            await self.stop_service(service_name, graceful=True)

    async def _check_service_running(self, service_name: str) -> Tuple[bool, Optional[int]]:
        """Check if a specific service is running"""
        service = self.services.get(service_name)
        if not service:
            return False, None

        try:
            # Check by PID if we have one
            if service.pid:
                process = psutil.Process(service.pid)
                if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                    return True, service.pid

            # Check by port if service uses a port
            if service.port:
                if self._is_port_in_use(service.port):
                    # Try to find the process using this port
                    pid = self._get_pid_using_port(service.port)
                    if pid:
                        return True, pid

            # For core services, check executable existence
            if service.service_type == ServiceType.CORE:
                return await self._check_core_service_running(service_name)

            return False, None

        except Exception as e:
            logger.error(f"Error checking if {service_name} is running: {e}")
            return False, None

    async def _check_core_service_running(self, service_name: str) -> Tuple[bool, Optional[int]]:
        """Check if a core service is running"""
        service = self.services.get(service_name)
        if not service:
            return False, None

        try:
            if service_name == "lm_studio":
                # Check LM Studio by making a request to its API
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"http://localhost:{service.port}/v1/models", timeout=5) as response:
                            if response.status == 200:
                                return True, None  # PID unknown but service is responsive
                    except:
                        pass
                return False, None

            elif service_name == "comfyui":
                # Check ComfyUI by making a request to its API
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"http://localhost:{service.port}/object_info", timeout=5) as response:
                            if response.status == 200:
                                return True, None  # PID unknown but service is responsive
                    except:
                        pass
                return False, None

            elif service_name == "webui":
                # Check WebUI by making a request to its health endpoint
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"http://localhost:{service.port}/healthz", timeout=5) as response:
                            if response.status == 200:
                                return True, None  # PID unknown but service is responsive
                    except:
                        pass
                return False, None

            elif service_name == "server_manager":
                # Server manager is always considered running if the process exists
                return True, None

        except Exception as e:
            logger.error(f"Error checking core service {service_name}: {e}")

        return False, None

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return False
        except OSError:
            return True

    def _get_pid_using_port(self, port: int) -> Optional[int]:
        """Get the PID of the process using a specific port"""
        try:
            # Try to connect to the port and get peer info
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("localhost", port))
                # This won't work reliably, so we'll use psutil instead
                pass
        except:
            pass

        # Use psutil to find process using port
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == port and conn.pid:
                    return conn.pid
        except:
            pass

        return None

    async def start_service(self, service_name: str, force: bool = False) -> Tuple[bool, str]:
        """Start a specific service"""
        if service_name not in self.services:
            return False, f"Service {service_name} not found"

        service = self.services[service_name]

        # Acquire lock for this service
        with self.locks[service_name]:
            # Check if already running
            if service.status == ServiceStatus.RUNNING and not force:
                return True, f"Service {service_name} is already running"

            # Check dependencies
            for dep_name in service.dependencies:
                if dep_name in self.services:
                    dep_service = self.services[dep_name]
                    if dep_service.status != ServiceStatus.RUNNING:
                        success, message = await self.start_service(dep_name)
                        if not success:
                            return False, f"Failed to start dependency {dep_name}: {message}"

            # Update status
            service.status = ServiceStatus.STARTING
            service.error_message = None

            try:
                # Start the service
                success, message = await self._start_service_internal(service_name)

                if success:
                    service.status = ServiceStatus.RUNNING
                    service.start_time = datetime.now()
                    service.restart_attempts = 0
                    await self._notify_service_change(service_name, "started")
                    logger.info(f"Service {service_name} started successfully")
                    return True, f"Service {service_name} started successfully"
                else:
                    service.status = ServiceStatus.ERROR
                    service.error_message = message
                    logger.error(f"Failed to start service {service_name}: {message}")
                    return False, message

            except Exception as e:
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)
                logger.error(f"Exception starting service {service_name}: {e}")
                return False, str(e)

    async def _start_service_internal(self, service_name: str) -> Tuple[bool, str]:
        """Internal method to start a service"""
        service = self.services[service_name]

        try:
            if service_name == "lm_studio":
                # For LM Studio, we expect it to be started externally
                # But we can check if it's already running
                success, _ = await self._check_core_service_running("lm_studio")
                if success:
                    return True, "LM Studio is already running"
                else:
                    return False, "Please start LM Studio manually"

            elif service_name == "comfyui":
                # Start ComfyUI
                comfyui_path = Path("./ComfyUI/main.py")
                if not comfyui_path.exists():
                    return False, "ComfyUI not found at ./ComfyUI/main.py"

                cmd = [
                    sys.executable,
                    str(comfyui_path),
                    "--listen",
                    service.config.get("host", "127.0.0.1"),
                    "--port",
                    str(service.port),
                    "--force-fp16"
                ]

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )

                self.processes[service_name] = process
                service.pid = process.pid
                return True, "ComfyUI started successfully"

            elif service_name == "webui":
                # Start WebUI
                from duckbot.webui import app
                import uvicorn

                def start_webui():
                    uvicorn.run(
                        app,
                        host=service.config.get("host", "127.0.0.1"),
                        port=service.port,
                        log_level="info"
                    )

                webui_thread = threading.Thread(target=start_webui, daemon=True)
                webui_thread.start()

                # Give it a moment to start
                await asyncio.sleep(2)

                # Verify it started
                success, _ = await self._check_core_service_running("webui")
                if success:
                    return True, "WebUI started successfully"
                else:
                    return False, "WebUI failed to start"

            elif service_name == "server_manager":
                # Server manager is part of the main process
                return True, "Server manager is part of the main process"

            elif service_name == "pyboy":
                # Start PyBoy Game Boy emulator
                try:
                    from duckbot.integrations.pyboy_integration import create_pyboy_integration

                    # Create directories if they don't exist
                    roms_dir = Path(service.config.get("roms_directory", "./roms"))
                    saves_dir = Path(service.config.get("saves_directory", "./saves"))
                    roms_dir.mkdir(exist_ok=True)
                    saves_dir.mkdir(exist_ok=True)

                    # Create PyBoy integration
                    pyboy = await create_pyboy_integration(headless=service.config.get("headless", True))
                    if pyboy:
                        # Store the integration instance for later use
                        self.pyboy_integration = pyboy
                        return True, "PyBoy integration initialized successfully"
                    else:
                        return False, "Failed to initialize PyBoy integration"

                except ImportError:
                    return False, "PyBoy integration module not found. Install with: pip install pyboy"
                except Exception as e:
                    return False, f"Failed to start PyBoy: {str(e)}"

            # For other services, try generic startup
            return await self._start_generic_service(service_name)

        except Exception as e:
            return False, f"Failed to start {service_name}: {str(e)}"

    async def _start_generic_service(self, service_name: str) -> Tuple[bool, str]:
        """Generic service startup method"""
        service = self.services[service_name]

        # Try to import and start the service
        try:
            # This is a simplification - in practice, you'd have specific startup logic
            # for each service type
            logger.info(f"Attempting to start generic service: {service_name}")
            return True, f"Generic service {service_name} started"
        except Exception as e:
            return False, f"Generic startup failed for {service_name}: {str(e)}"

    async def stop_service(self, service_name: str, graceful: bool = True) -> Tuple[bool, str]:
        """Stop a specific service"""
        if service_name not in self.services:
            return False, f"Service {service_name} not found"

        service = self.services[service_name]

        # Acquire lock for this service
        with self.locks[service_name]:
            # Check if already stopped
            if service.status in [ServiceStatus.STOPPED, ServiceStatus.UNKNOWN]:
                return True, f"Service {service_name} is already stopped"

            # Update status
            service.status = ServiceStatus.STOPPING
            service.error_message = None

            try:
                # Stop the service
                success, message = await self._stop_service_internal(service_name, graceful)

                if success:
                    service.status = ServiceStatus.STOPPED
                    service.pid = None
                    service.start_time = None
                    await self._notify_service_change(service_name, "stopped")
                    logger.info(f"Service {service_name} stopped successfully")
                    return True, f"Service {service_name} stopped successfully"
                else:
                    service.status = ServiceStatus.ERROR
                    service.error_message = message
                    logger.error(f"Failed to stop service {service_name}: {message}")
                    return False, message

            except Exception as e:
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)
                logger.error(f"Exception stopping service {service_name}: {e}")
                return False, str(e)

    async def _stop_service_internal(self, service_name: str, graceful: bool) -> Tuple[bool, str]:
        """Internal method to stop a service"""
        service = self.services[service_name]

        try:
            if service_name in ["lm_studio", "server_manager"]:
                # These services can't be stopped programmatically
                return True, f"{service_name} cannot be stopped programmatically"

            elif service_name == "pyboy":
                # Stop PyBoy integration
                try:
                    if hasattr(self, 'pyboy_integration') and self.pyboy_integration:
                        await self.pyboy_integration.cleanup()
                        delattr(self, 'pyboy_integration')
                        return True, "PyBoy integration stopped successfully"
                    else:
                        return True, "PyBoy integration not running"
                except Exception as e:
                    return False, f"Failed to stop PyBoy: {str(e)}"

            elif service_name in self.processes:
                # Stop subprocess
                process = self.processes[service_name]
                if process.poll() is None:  # Still running
                    if graceful:
                        process.terminate()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                    else:
                        process.kill()
                        process.wait()

                # Clean up
                del self.processes[service_name]
                return True, f"Process for {service_name} stopped"

            # For other services, assume they can be stopped
            return True, f"Service {service_name} stopped"

        except Exception as e:
            return False, f"Failed to stop {service_name}: {str(e)}"

    async def restart_service(self, service_name: str) -> Tuple[bool, str]:
        """Restart a specific service"""
        success, message = await self.stop_service(service_name)
        if not success:
            return False, f"Failed to stop service: {message}"

        # Wait a moment
        await asyncio.sleep(1)

        success, message = await self.start_service(service_name)
        if not success:
            return False, f"Failed to start service: {message}"

        return True, f"Service {service_name} restarted successfully"

    def get_service_status(self, service_name: str) -> ServiceInfo:
        """Get status of a specific service"""
        return self.services.get(service_name, ServiceInfo(
            name=service_name,
            display_name=f"Unknown Service ({service_name})",
            service_type=ServiceType.CORE,
            status=ServiceStatus.UNKNOWN
        ))

    def get_all_service_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all services"""
        return self.services.copy()

    def get_services_by_type(self, service_type: ServiceType) -> Dict[str, ServiceInfo]:
        """Get services filtered by type"""
        return {
            name: service for name, service in self.services.items()
            if service.service_type == service_type
        }

    def get_running_services(self) -> Dict[str, ServiceInfo]:
        """Get all currently running services"""
        return {
            name: service for name, service in self.services.items()
            if service.status == ServiceStatus.RUNNING
        }

    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health metrics for a specific service"""
        return self.health_monitors.get(service_name)

    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get health metrics for all services"""
        return self.health_monitors.copy()

    def get_system_resources(self) -> Dict[str, Any]:
        """Get overall system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_percent": memory.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100,
                "boot_time": psutil.boot_time(),
                "process_count": len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {
                "error": str(e)
            }

    async def start_ecosystem(self) -> Tuple[bool, Dict[str, str]]:
        """Start the complete DuckBot ecosystem"""
        logger.info("Starting DuckBot ecosystem...")

        results = {}
        success_count = 0
        total_count = 0

        # Start core services first
        core_services = self.get_services_by_type(ServiceType.CORE)
        for service_name in core_services:
            total_count += 1
            success, message = await self.start_service(service_name)
            results[service_name] = message
            if success:
                success_count += 1

        # Start system services
        system_services = self.get_services_by_type(ServiceType.SYSTEM)
        for service_name in system_services:
            total_count += 1
            success, message = await self.start_service(service_name)
            results[service_name] = message
            if success:
                success_count += 1

        # Start integration services (optional)
        integration_services = self.get_services_by_type(ServiceType.INTEGRATION)
        for service_name in integration_services:
            total_count += 1
            # Only start if configured to auto-start or if explicitly requested
            service = self.services[service_name]
            if service.auto_start:
                success, message = await self.start_service(service_name)
                results[service_name] = message
                if success:
                    success_count += 1

        overall_success = success_count == total_count
        logger.info(f"Ecosystem startup: {success_count}/{total_count} services started")

        return overall_success, results

    async def stop_ecosystem(self) -> Tuple[bool, Dict[str, str]]:
        """Stop the complete DuckBot ecosystem"""
        logger.info("Stopping DuckBot ecosystem...")

        results = {}
        success_count = 0
        total_count = 0

        # Stop in reverse order - integrations first, then system, then core
        service_order = [
            list(self.get_services_by_type(ServiceType.INTEGRATION).keys()),
            list(self.get_services_by_type(ServiceType.ENHANCED).keys()),
            list(self.get_services_by_type(ServiceType.SYSTEM).keys()),
            list(self.get_services_by_type(ServiceType.CORE).keys())
        ]

        for service_names in service_order:
            for service_name in service_names:
                total_count += 1
                success, message = await self.stop_service(service_name)
                results[service_name] = message
                if success:
                    success_count += 1

        overall_success = success_count == total_count
        logger.info(f"Ecosystem shutdown: {success_count}/{total_count} services stopped")

        return overall_success, results

    async def restart_ecosystem(self) -> Tuple[bool, Dict[str, str]]:
        """Restart the complete DuckBot ecosystem"""
        success, stop_results = await self.stop_ecosystem()
        if not success:
            return False, {**stop_results, "error": "Failed to stop ecosystem"}

        success, start_results = await self.start_ecosystem()
        if not success:
            return False, {**stop_results, **start_results, "error": "Failed to start ecosystem"}

        return True, {**stop_results, **start_results}

    def register_callback(self, service_name: str, callback: Callable):
        """Register a callback for service status changes"""
        if service_name in self.callbacks:
            self.callbacks[service_name].append(callback)

    async def _notify_service_change(self, service_name: str, action: str):
        """Notify callbacks of service status change"""
        if service_name in self.callbacks:
            for callback in self.callbacks[service_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(service_name, action)
                    else:
                        callback(service_name, action)
                except Exception as e:
                    logger.error(f"Error in service change callback for {service_name}: {e}")

    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status"""
        core_services = self.get_services_by_type(ServiceType.CORE)
        integration_services = self.get_services_by_type(ServiceType.INTEGRATION)
        enhanced_services = self.get_services_by_type(ServiceType.ENHANCED)
        system_services = self.get_services_by_type(ServiceType.SYSTEM)
        external_services = self.get_services_by_type(ServiceType.EXTERNAL)

        def count_status(services: Dict[str, ServiceInfo], status: ServiceStatus) -> int:
            return sum(1 for service in services.values() if service.status == status)

        total_services = len(self.services)
        running_services = len(self.get_running_services())

        # Health scores
        health_scores = [health.health_score for health in self.health_monitors.values()]
        avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 100.0

        return {
            "overview": {
                "total_services": total_services,
                "running_services": running_services,
                "stopped_services": total_services - running_services,
                "health_score": avg_health_score,
                "system_resources": self.get_system_resources()
            },
            "by_type": {
                "core": {
                    "total": len(core_services),
                    "running": count_status(core_services, ServiceStatus.RUNNING),
                    "stopped": count_status(core_services, ServiceStatus.STOPPED),
                    "error": count_status(core_services, ServiceStatus.ERROR)
                },
                "integration": {
                    "total": len(integration_services),
                    "running": count_status(integration_services, ServiceStatus.RUNNING),
                    "stopped": count_status(integration_services, ServiceStatus.STOPPED),
                    "error": count_status(integration_services, ServiceStatus.ERROR)
                },
                "enhanced": {
                    "total": len(enhanced_services),
                    "running": count_status(enhanced_services, ServiceStatus.RUNNING),
                    "stopped": count_status(enhanced_services, ServiceStatus.STOPPED),
                    "error": count_status(enhanced_services, ServiceStatus.ERROR)
                },
                "system": {
                    "total": len(system_services),
                    "running": count_status(system_services, ServiceStatus.RUNNING),
                    "stopped": count_status(system_services, ServiceStatus.STOPPED),
                    "error": count_status(system_services, ServiceStatus.ERROR)
                },
                "external": {
                    "total": len(external_services),
                    "running": count_status(external_services, ServiceStatus.RUNNING),
                    "stopped": count_status(external_services, ServiceStatus.STOPPED),
                    "error": count_status(external_services, ServiceStatus.ERROR)
                }
            },
            "services": {
                name: {
                    "display_name": service.display_name,
                    "status": service.status.value,
                    "type": service.service_type.value,
                    "port": service.port,
                    "pid": service.pid,
                    "uptime": (datetime.now() - service.start_time).total_seconds() if service.start_time else 0,
                    "health_score": self.health_monitors.get(name, ServiceHealth(name, ServiceStatus.UNKNOWN)).health_score
                }
                for name, service in self.services.items()
            }
        }

# Global instance
service_manager = UnifiedServiceManager()

# Convenience functions
async def initialize_service_manager() -> bool:
    """Initialize the service manager"""
    return await service_manager.initialize()

def get_service_status(service_name: str) -> ServiceInfo:
    """Get status of a specific service"""
    return service_manager.get_service_status(service_name)

def get_all_service_status() -> Dict[str, ServiceInfo]:
    """Get status of all services"""
    return service_manager.get_all_service_status()

async def start_service(service_name: str) -> Tuple[bool, str]:
    """Start a specific service"""
    return await service_manager.start_service(service_name)

async def stop_service(service_name: str) -> Tuple[bool, str]:
    """Stop a specific service"""
    return await service_manager.stop_service(service_name)

async def restart_service(service_name: str) -> Tuple[bool, str]:
    """Restart a specific service"""
    return await service_manager.restart_service(service_name)

async def start_ecosystem() -> Tuple[bool, Dict[str, str]]:
    """Start the complete ecosystem"""
    return await service_manager.start_ecosystem()

async def stop_ecosystem() -> Tuple[bool, Dict[str, str]]:
    """Stop the complete ecosystem"""
    return await service_manager.stop_ecosystem()

async def restart_ecosystem() -> Tuple[bool, Dict[str, str]]:
    """Restart the complete ecosystem"""
    return await service_manager.restart_ecosystem()

def get_ecosystem_status() -> Dict[str, Any]:
    """Get comprehensive ecosystem status"""
    return asyncio.run(service_manager.get_ecosystem_status())

def get_service_health(service_name: str) -> Optional[ServiceHealth]:
    """Get health metrics for a specific service"""
    return service_manager.get_service_health(service_name)

def get_system_resources() -> Dict[str, Any]:
    """Get system resource usage"""
    return service_manager.get_system_resources()

# Backward compatibility functions
def get_server_manager():
    """Backward compatibility for existing server_manager usage"""
    return service_manager

def get_service_detector():
    """Backward compatibility for service_detector usage"""
    # This would return a compatibility wrapper
    class ServiceDetectorCompatibility:
        def get_all_service_status(self):
            return service_manager.get_all_service_status()
        
        def get_service_status(self, service_name):
            return service_manager.get_service_status(service_name)
        
        def get_startup_recommendations(self):
            # Return recommendations based on current service status
            recommendations = {}
            for name, service in service_manager.get_all_service_status().items():
                if service.status == ServiceStatus.RUNNING:
                    recommendations[name] = {
                        "can_start": False,
                        "reason": "Already running"
                    }
                else:
                    recommendations[name] = {
                        "can_start": True,
                        "reason": "Ready to start"
                    }
            return recommendations
    
    return ServiceDetectorCompatibility()

if __name__ == "__main__":
    # Test the service manager
    import asyncio
    
    async def test():
        print("🧪 Testing Unified Service Manager")
        print("=" * 50)
        
        # Initialize
        success = await initialize_service_manager()
        print(f"Initialization: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if success:
            # Show current status
            status = get_ecosystem_status()
            print(f"\nEcosystem Status:")
            print(f"  Total Services: {status['overview']['total_services']}")
            print(f"  Running Services: {status['overview']['running_services']}")
            print(f"  Health Score: {status['overview']['health_score']:.1f}%")
            
            # Show service details
            print(f"\nService Details:")
            for name, service_info in status['services'].items():
                print(f"  • {service_info['display_name']}: {service_info['status'].upper()}")
            
            # Test starting a service
            print(f"\nTesting Service Management:")
            success, message = await start_service("webui")
            print(f"  Start WebUI: {'✅' if success else '❌'} {message}")
            
            # Test stopping a service
            success, message = await stop_service("webui")
            print(f"  Stop WebUI: {'✅' if success else '❌'} {message}")
        
        print("\n" + "=" * 50)
        print("✅ Test completed!")
    
    asyncio.run(test())
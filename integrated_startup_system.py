#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Integrated Startup System v4.2
Unified orchestrator for coordinating Electron launcher, MCP server, and modular launcher
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import yaml
import sqlite3
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'integrated_startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    RESTARTING = "restarting"
    DEGRADED = "degraded"

class StartupPhase(Enum):
    """Startup phase enumeration"""
    INITIALIZATION = "initialization"
    ENVIRONMENT_CHECK = "environment_check"
    PORT_ALLOCATION = "port_allocation"
    SERVICE_DISCOVERY = "service_discovery"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    SERVICE_STARTUP = "service_startup"
    HEALTH_VERIFICATION = "health_verification"
    READY = "ready"

@dataclass
class ServiceDependency:
    """Service dependency definition"""
    service_name: str
    required: bool = True
    startup_delay: int = 0
    health_check: bool = True
    fallback_action: Optional[str] = None

@dataclass
class ServiceConfig:
    """Unified service configuration"""
    name: str
    display_name: str
    service_type: str
    command: str
    working_dir: str
    ports: List[int] = field(default_factory=list)
    dependencies: List[ServiceDependency] = field(default_factory=list)
    health_endpoint: Optional[str] = None
    startup_timeout: int = 60
    auto_restart: bool = True
    max_restarts: int = 3
    restart_delay: int = 30
    critical: bool = False
    environment_vars: Dict[str, str] = field(default_factory=dict)

@dataclass
class StartupProgress:
    """Startup progress tracking"""
    phase: StartupPhase
    progress: float  # 0.0 to 1.0
    message: str
    service: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

@dataclass
class SystemHealth:
    """System health status"""
    overall_health: str  # "healthy", "degraded", "critical"
    services: Dict[str, Dict[str, Any]]
    system_metrics: Dict[str, Any]
    last_updated: datetime = field(default_factory=datetime.now)

class IntegratedStartupOrchestrator:
    """Main orchestrator for integrated startup system"""

    def __init__(self):
        self.project_root = project_root
        self.config_dir = project_root / "config"
        self.logs_dir = project_root / "logs"
        self.services: Dict[str, ServiceConfig] = {}
        self.service_processes: Dict[str, subprocess.Popen] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.allocated_ports: Dict[int, str] = {}
        self.startup_progress: List[StartupProgress] = []
        self.health_status: SystemHealth = None
        self.shutdown_requested = False
        self.startup_complete = False

        # Configuration
        self.config_file = self.config_dir / "integrated_startup_config.yaml"
        self.db_path = project_root / "integrated_startup_state.db"

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.health_monitor_thread = None

        # Initialize
        self._ensure_directories()
        self._load_configuration()
        self._init_database()

        logger.info("Integrated Startup Orchestrator initialized")

    def _ensure_directories(self):
        """Ensure required directories exist"""
        for directory in [self.config_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)

    def _load_configuration(self):
        """Load startup configuration"""
        default_config = {
            'services': {
                'mcp_server': {
                    'name': 'mcp_server',
                    'display_name': 'MCP Server',
                    'service_type': 'mcp',
                    'command': 'python start_mcp_server.py',
                    'working_dir': str(self.project_root),
                    'ports': [8790],
                    'health_endpoint': 'http://localhost:8790/',
                    'startup_timeout': 30,
                    'auto_restart': True,
                    'max_restarts': 3,
                    'restart_delay': 15,
                    'critical': True,
                    'dependencies': []
                },
                'enhanced_webui': {
                    'name': 'enhanced_webui',
                    'display_name': 'Enhanced WebUI',
                    'service_type': 'web_ui',
                    'command': 'python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787',
                    'working_dir': str(self.project_root),
                    'ports': [8787],
                    'health_endpoint': 'http://localhost:8787/',
                    'startup_timeout': 60,
                    'auto_restart': True,
                    'max_restarts': 5,
                    'restart_delay': 30,
                    'critical': True,
                    'dependencies': []
                },
                'electron_launcher': {
                    'name': 'electron_launcher',
                    'display_name': 'Electron Launcher',
                    'service_type': 'desktop',
                    'command': 'npm start',
                    'working_dir': str(self.project_root / 'duckbot' / 'react-webui'),
                    'ports': [3000],
                    'startup_timeout': 45,
                    'auto_restart': False,
                    'max_restarts': 2,
                    'restart_delay': 60,
                    'critical': False,
                    'dependencies': [
                        {
                            'service_name': 'enhanced_webui',
                            'required': True,
                            'startup_delay': 10
                        }
                    ]
                },
                'modular_launcher': {
                    'name': 'modular_launcher',
                    'display_name': 'Modular Launcher',
                    'service_type': 'orchestrator',
                    'command': 'python launcher_main.py',
                    'working_dir': str(self.project_root),
                    'ports': [],
                    'startup_timeout': 30,
                    'auto_restart': True,
                    'max_restarts': 3,
                    'restart_delay': 20,
                    'critical': False,
                    'dependencies': [
                        {
                            'service_name': 'mcp_server',
                            'required': True,
                            'startup_delay': 5
                        }
                    ]
                }
            },
            'port_ranges': {
                'mcp_server': [8790, 8799],
                'web_ui': [8780, 8789],
                'monitoring': [8890, 8899],
                'dynamic': [9000, 9999]
            },
            'startup': {
                'parallel_services': 3,
                'health_check_interval': 30,
                'startup_timeout': 300,
                'dependency_check_timeout': 60
            }
        }

        if not self.config_file.exists():
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(default_config, f, default_flow_style=False)
            logger.info("Created default integrated startup configuration")

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)

            # Load service configurations
            for service_name, service_data in config['services'].items():
                dependencies = []
                for dep_data in service_data.get('dependencies', []):
                    if isinstance(dep_data, dict):
                        dependencies.append(ServiceDependency(**dep_data))
                    else:
                        dependencies.append(ServiceDependency(service_name=dep_data))

                self.services[service_name] = ServiceConfig(
                    **{k: v for k, v in service_data.items() if k != 'dependencies'},
                    dependencies=dependencies
                )

            logger.info(f"Loaded configuration for {len(self.services)} services")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fall back to default configuration
            for service_name, service_data in default_config['services'].items():
                self.services[service_name] = ServiceConfig(**service_data)

    def _init_database(self):
        """Initialize SQLite database for persistent state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS startup_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phase TEXT NOT NULL,
                        service TEXT,
                        message TEXT,
                        progress REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        error TEXT
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS service_states (
                        service_name TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        pid INTEGER,
                        start_time DATETIME,
                        last_health_check DATETIME,
                        health_status TEXT,
                        restart_count INTEGER DEFAULT 0
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS port_allocations (
                        port INTEGER PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        allocated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _log_startup_event(self, phase: StartupPhase, message: str, progress: float,
                          service: Optional[str] = None, error: Optional[str] = None):
        """Log startup event to database and memory"""
        event = StartupProgress(
            phase=phase,
            progress=progress,
            message=message,
            service=service,
            error=error
        )

        self.startup_progress.append(event)

        # Log to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO startup_events (phase, service, message, progress, error) VALUES (?, ?, ?, ?, ?)",
                    (phase.value, service, message, progress, error)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log startup event: {e}")

        # Log to console
        if error:
            logger.error(f"[{phase.value}] {service or 'System'}: {message} - {error}")
        else:
            logger.info(f"[{phase.value}] {service or 'System'}: {message}")

    async def _check_environment(self) -> bool:
        """Check system environment and dependencies"""
        self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK, "Starting environment validation", 0.1)

        try:
            # Check Python
            result = subprocess.run([sys.executable, '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK,
                                      "Python not available", 0.1, error="Python check failed")
                return False

            self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK,
                                  f"Python {result.stdout.strip()} available", 0.3)

            # Check Node.js (required for Electron)
            try:
                result = subprocess.run(['node', '--version'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK,
                                          f"Node.js {result.stdout.strip()} available", 0.5)
                else:
                    self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK,
                                          "Node.js not found", 0.5, error="Node.js required for Electron launcher")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK,
                                      "Node.js not found", 0.5, error="Node.js required for Electron launcher")

            # Check required directories
            required_dirs = [self.config_dir, self.logs_dir, self.project_root / "duckbot"]
            for dir_path in required_dirs:
                if not dir_path.exists():
                    self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK,
                                          f"Required directory missing: {dir_path}", 0.7,
                                          error=f"Directory not found: {dir_path}")
                    return False

            self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK, "Environment validation completed", 1.0)
            return True

        except Exception as e:
            self._log_startup_event(StartupPhase.ENVIRONMENT_CHECK, "Environment validation failed", 0.0,
                                  error=str(e))
            return False

    async def _allocate_ports(self) -> bool:
        """Allocate ports for services"""
        self._log_startup_event(StartupPhase.PORT_ALLOCATION, "Starting port allocation", 0.0)

        try:
            allocated_count = 0
            total_ports = sum(len(service.ports) for service in self.services.values())

            for service_name, service_config in self.services.items():
                for port in service_config.ports:
                    if self._is_port_available(port):
                        self.allocated_ports[port] = service_name

                        # Log to database
                        try:
                            with sqlite3.connect(self.db_path) as conn:
                                conn.execute(
                                    "INSERT OR REPLACE INTO port_allocations (port, service_name) VALUES (?, ?)",
                                    (port, service_name)
                                )
                                conn.commit()
                        except Exception as e:
                            logger.error(f"Failed to log port allocation: {e}")

                        allocated_count += 1
                        progress = (allocated_count / total_ports) if total_ports > 0 else 1.0
                        self._log_startup_event(StartupPhase.PORT_ALLOCATION,
                                              f"Allocated port {port} for {service_name}", progress, service_name)
                    else:
                        self._log_startup_event(StartupPhase.PORT_ALLOCATION,
                                              f"Port {port} already in use", progress, service_name,
                                              error=f"Port conflict: {port}")
                        return False

            self._log_startup_event(StartupPhase.PORT_ALLOCATION, "Port allocation completed", 1.0)
            return True

        except Exception as e:
            self._log_startup_event(StartupPhase.PORT_ALLOCATION, "Port allocation failed", 0.0, error=str(e))
            return False

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0
        except Exception:
            return False

    async def _resolve_dependencies(self) -> bool:
        """Resolve service dependencies"""
        self._log_startup_event(StartupPhase.DEPENDENCY_RESOLUTION, "Starting dependency resolution", 0.0)

        try:
            dependency_graph = {}
            for service_name, service_config in self.services.items():
                dependency_graph[service_name] = [
                    dep.service_name for dep in service_config.dependencies if dep.required
                ]

            # Topological sort for startup order
            startup_order = self._topological_sort(dependency_graph)

            if not startup_order:
                self._log_startup_event(StartupPhase.DEPENDENCY_RESOLUTION,
                                      "Circular dependency detected", 0.0,
                                      error="Circular dependencies in service configuration")
                return False

            self._log_startup_event(StartupPhase.DEPENDENCY_RESOLUTION,
                                  f"Dependency resolution completed - startup order: {startup_order}", 1.0)
            return True

        except Exception as e:
            self._log_startup_event(StartupPhase.DEPENDENCY_RESOLUTION,
                                  "Dependency resolution failed", 0.0, error=str(e))
            return False

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort on dependency graph"""
        try:
            from collections import deque

            in_degree = {node: 0 for node in graph}
            for node in graph:
                for neighbor in graph[node]:
                    if neighbor in in_degree:
                        in_degree[neighbor] += 1

            queue = deque([node for node in in_degree if in_degree[node] == 0])
            result = []

            while queue:
                node = queue.popleft()
                result.append(node)

                for neighbor in graph.get(node, []):
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)

            if len(result) != len(graph):
                return None  # Circular dependency

            return result

        except Exception as e:
            logger.error(f"Topological sort failed: {e}")
            return None

    async def _start_service(self, service_name: str, service_config: ServiceConfig) -> bool:
        """Start a single service"""
        try:
            self.service_status[service_name] = ServiceStatus.STARTING
            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                  f"Starting {service_config.display_name}", 0.5, service_name)

            # Check dependencies
            for dep in service_config.dependencies:
                if dep.required and dep.service_name in self.service_status:
                    dep_status = self.service_status[dep.service_name]
                    if dep_status != ServiceStatus.RUNNING:
                        self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                              f"Dependency {dep.service_name} not running", 0.5,
                                              service_name, error=f"Required dependency not available: {dep.service_name}")
                        return False

                if dep.startup_delay > 0:
                    await asyncio.sleep(dep.startup_delay)

            # Start the service
            env = os.environ.copy()
            env.update(service_config.environment_vars)
            env['DUCKBOT_SERVICE_NAME'] = service_name

            # Ensure working directory exists
            working_dir = Path(service_config.working_dir)
            if not working_dir.exists():
                working_dir.mkdir(parents=True, exist_ok=True)

            # Create log file
            log_file = self.logs_dir / f"{service_name}.log"

            process = subprocess.Popen(
                service_config.command,
                shell=True,
                cwd=str(working_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.service_processes[service_name] = process

            # Log service start
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO service_states (service_name, status, pid, start_time) VALUES (?, ?, ?, ?)",
                        (service_name, ServiceStatus.STARTING.value, process.pid, datetime.now())
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to log service state: {e}")

            # Start log reader thread
            threading.Thread(target=self._read_service_logs, args=(service_name, process, log_file),
                           daemon=True).start()

            # Wait for startup timeout
            start_time = time.time()
            while time.time() - start_time < service_config.startup_timeout:
                if process.poll() is not None:
                    # Process terminated
                    self.service_status[service_name] = ServiceStatus.FAILED
                    self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                          f"{service_config.display_name} process terminated", 1.0,
                                          service_name, error=f"Process exited with code: {process.returncode}")
                    return False

                # Check health endpoint if available
                if service_config.health_endpoint:
                    try:
                        response = requests.get(service_config.health_endpoint, timeout=5)
                        if response.status_code < 400:
                            self.service_status[service_name] = ServiceStatus.RUNNING
                            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                                  f"{service_config.display_name} started successfully", 1.0,
                                                  service_name)
                            return True
                    except requests.RequestException:
                        pass

                await asyncio.sleep(1)

            # Timeout reached
            self.service_status[service_name] = ServiceStatus.DEGRADED
            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                  f"{service_config.display_name} startup timeout", 1.0,
                                  service_name, error="Startup timeout reached")
            return False

        except Exception as e:
            self.service_status[service_name] = ServiceStatus.FAILED
            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                  f"Failed to start {service_config.display_name}", 1.0,
                                  service_name, error=str(e))
            return False

    def _read_service_logs(self, service_name: str, process: subprocess.Popen, log_file: Path):
        """Read and log service output"""
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            f.write(line)
                            f.flush()

                            # Forward to main logger
                            if "ERROR" in line.upper() or "CRITICAL" in line.upper():
                                logger.error(f"[{service_name}] {line.strip()}")
                            else:
                                logger.info(f"[{service_name}] {line.strip()}")
        except Exception as e:
            logger.error(f"Failed to read {service_name} logs: {e}")

    async def _verify_health(self) -> bool:
        """Verify health of all running services"""
        self._log_startup_event(StartupPhase.HEALTH_VERIFICATION, "Starting health verification", 0.0)

        try:
            healthy_count = 0
            total_services = len([s for s in self.service_status.values() if s == ServiceStatus.RUNNING])

            for service_name, status in self.service_status.items():
                if status == ServiceStatus.RUNNING:
                    service_config = self.services.get(service_name)
                    if service_config and service_config.health_endpoint:
                        try:
                            response = requests.get(service_config.health_endpoint, timeout=10)
                            if response.status_code < 400:
                                healthy_count += 1
                                self._log_startup_event(StartupPhase.HEALTH_VERIFICATION,
                                                      f"{service_config.display_name} health check passed",
                                                      healthy_count / total_services, service_name)
                            else:
                                self.service_status[service_name] = ServiceStatus.DEGRADED
                                self._log_startup_event(StartupPhase.HEALTH_VERIFICATION,
                                                      f"{service_config.display_name} health check failed",
                                                      healthy_count / total_services, service_name,
                                                      error=f"HTTP {response.status_code}")
                        except requests.RequestException as e:
                            self.service_status[service_name] = ServiceStatus.DEGRADED
                            self._log_startup_event(StartupPhase.HEALTH_VERIFICATION,
                                                  f"{service_config.display_name} health check failed",
                                                  healthy_count / total_services, service_name,
                                                  error=str(e))

            health_percentage = (healthy_count / total_services) if total_services > 0 else 0
            self._log_startup_event(StartupPhase.HEALTH_VERIFICATION,
                                  f"Health verification completed ({healthy_count}/{total_services} healthy)", 1.0)

            return health_percentage >= 0.8  # 80% healthy threshold

        except Exception as e:
            self._log_startup_event(StartupPhase.HEALTH_VERIFICATION, "Health verification failed", 0.0,
                                  error=str(e))
            return False

    async def _start_services_parallel(self) -> bool:
        """Start services in parallel based on dependency resolution"""
        self._log_startup_event(StartupPhase.SERVICE_STARTUP, "Starting services in parallel", 0.0)

        try:
            # Get dependency-resolved startup order
            dependency_graph = {}
            for service_name, service_config in self.services.items():
                dependency_graph[service_name] = [
                    dep.service_name for dep in service_config.dependencies if dep.required
                ]

            startup_order = self._topological_sort(dependency_graph)
            if not startup_order:
                return False

            # Start services in batches based on dependency levels
            started_services = set()
            total_services = len(self.services)

            for level, service_batch in enumerate(self._group_by_dependency_level(startup_order, dependency_graph)):
                batch_progress = (level + 1) / len(self._group_by_dependency_level(startup_order, dependency_graph))

                # Start services in this batch in parallel
                tasks = []
                for service_name in service_batch:
                    if service_name in self.services and service_name not in started_services:
                        task = asyncio.create_task(self._start_service(service_name, self.services[service_name]))
                        tasks.append(task)

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        service_name = service_batch[i]
                        if isinstance(result, Exception) or not result:
                            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                                  f"Failed to start service in batch", batch_progress,
                                                  service_name, error=str(result) if isinstance(result, Exception) else "Unknown error")
                        else:
                            started_services.add(service_name)
                            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                                  f"Service started successfully", batch_progress, service_name)

            progress = len(started_services) / total_services
            self._log_startup_event(StartupPhase.SERVICE_STARTUP,
                                  f"Parallel service startup completed ({len(started_services)}/{total_services})", progress)

            return len(started_services) >= total_services * 0.8  # 80% success threshold

        except Exception as e:
            self._log_startup_event(StartupPhase.SERVICE_STARTUP, "Parallel service startup failed", 0.0,
                                  error=str(e))
            return False

    def _group_by_dependency_level(self, startup_order: List[str], dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
        """Group services by dependency level for parallel startup"""
        levels = []
        remaining = set(startup_order)

        while remaining:
            current_level = []
            for service in list(remaining):
                dependencies = dependency_graph.get(service, [])
                if all(dep not in remaining for dep in dependencies):
                    current_level.append(service)

            if not current_level:
                break  # Circular dependency or all remaining services have unresolved dependencies

            levels.append(current_level)
            remaining -= set(current_level)

        return levels

    async def startup(self) -> bool:
        """Main startup sequence"""
        self._log_startup_event(StartupPhase.INITIALIZATION, "Starting integrated startup sequence", 0.0)

        try:
            # Phase 1: Environment Check
            if not await self._check_environment():
                self._log_startup_event(StartupPhase.INITIALIZATION, "Environment check failed", 0.1,
                                      error="Environment validation failed")
                return False

            # Phase 2: Port Allocation
            if not await self._allocate_ports():
                self._log_startup_event(StartupPhase.INITIALIZATION, "Port allocation failed", 0.2,
                                      error="Port allocation failed")
                return False

            # Phase 3: Dependency Resolution
            if not await self._resolve_dependencies():
                self._log_startup_event(StartupPhase.INITIALIZATION, "Dependency resolution failed", 0.3,
                                      error="Dependency resolution failed")
                return False

            # Phase 4: Service Startup
            if not await self._start_services_parallel():
                self._log_startup_event(StartupPhase.INITIALIZATION, "Service startup failed", 0.8,
                                      error="Service startup failed")
                return False

            # Phase 5: Health Verification
            if not await self._verify_health():
                self._log_startup_event(StartupPhase.INITIALIZATION, "Health verification failed", 0.9,
                                      error="Health verification failed")
                return False

            # Startup complete
            self.startup_complete = True
            self._log_startup_event(StartupPhase.READY, "Integrated startup sequence completed", 1.0)

            # Start health monitoring
            self._start_health_monitoring()

            return True

        except Exception as e:
            self._log_startup_event(StartupPhase.INITIALIZATION, "Startup sequence failed", 0.0,
                                  error=str(e))
            return False

    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def monitor_loop():
            while not self.shutdown_requested:
                try:
                    asyncio.run(self._update_health_status())
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(60)  # Back off on error

        self.health_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.health_monitor_thread.start()
        logger.info("Health monitoring started")

    async def _update_health_status(self):
        """Update system health status"""
        try:
            services_health = {}
            healthy_count = 0

            for service_name, status in self.service_status.items():
                service_config = self.services.get(service_name)
                service_health = {
                    'status': status.value,
                    'pid': self.service_processes.get(service_name, {}).get('pid') if service_name in self.service_processes else None,
                    'uptime': None,
                    'health_check': None
                }

                if status == ServiceStatus.RUNNING and service_config:
                    # Check health endpoint
                    if service_config.health_endpoint:
                        try:
                            response = requests.get(service_config.health_endpoint, timeout=5)
                            service_health['health_check'] = {
                                'status': 'healthy' if response.status_code < 400 else 'unhealthy',
                                'status_code': response.status_code,
                                'response_time': response.elapsed.total_seconds()
                            }
                            if response.status_code < 400:
                                healthy_count += 1
                        except requests.RequestException:
                            service_health['health_check'] = {
                                'status': 'unhealthy',
                                'error': 'Connection failed'
                            }

                services_health[service_name] = service_health

            # Calculate overall health
            total_services = len(self.service_status)
            health_percentage = (healthy_count / total_services) if total_services > 0 else 0

            if health_percentage >= 0.8:
                overall_health = "healthy"
            elif health_percentage >= 0.5:
                overall_health = "degraded"
            else:
                overall_health = "critical"

            # Get system metrics
            import psutil
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': time.time() - self.startup_progress[0].timestamp.timestamp() if self.startup_progress else 0
            }

            self.health_status = SystemHealth(
                overall_health=overall_health,
                services=services_health,
                system_metrics=system_metrics
            )

            # Update database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    for service_name, health in services_health.items():
                        conn.execute(
                            "UPDATE service_states SET status = ?, last_health_check = ?, health_status = ? WHERE service_name = ?",
                            (health['status'], datetime.now(), health.get('health_check', {}).get('status'), service_name)
                        )
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to update service states: {e}")

        except Exception as e:
            logger.error(f"Failed to update health status: {e}")

    def get_startup_progress(self) -> List[Dict[str, Any]]:
        """Get current startup progress"""
        return [asdict(progress) for progress in self.startup_progress]

    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        if not self.health_status:
            return {"overall_health": "unknown", "services": {}, "system_metrics": {}}

        return asdict(self.health_status)

    def get_service_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of specific service or all services"""
        if service_name:
            status = self.service_status.get(service_name)
            process = self.service_processes.get(service_name)
            return {
                'name': service_name,
                'status': status.value if status else 'unknown',
                'pid': process.pid if process else None,
                'running': process and process.poll() is None if process else False
            }
        else:
            return {
                service_name: {
                    'status': status.value if status else 'unknown',
                    'pid': self.service_processes.get(service_name, {}).get('pid') if service_name in self.service_processes else None,
                    'running': self.service_processes.get(service_name, {}).poll() is None if service_name in self.service_processes else False
                }
                for service_name, status in self.service_status.items()
            }

    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        try:
            if service_name not in self.service_processes:
                logger.warning(f"Service {service_name} not found")
                return False

            process = self.service_processes[service_name]
            if process.poll() is None:
                # Process is running, stop it
                if sys.platform == "win32":
                    subprocess.run(['taskkill', '/pid', str(process.pid), '/f', '/t'],
                                  capture_output=True, timeout=10)
                else:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()

            # Clean up
            del self.service_processes[service_name]
            self.service_status[service_name] = ServiceStatus.STOPPED

            # Release ports
            ports_to_release = [port for port, service in self.allocated_ports.items() if service == service_name]
            for port in ports_to_release:
                del self.allocated_ports[port]

            # Update database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM port_allocations WHERE service_name = ?", (service_name,))
                    conn.execute("UPDATE service_states SET status = ? WHERE service_name = ?",
                               (ServiceStatus.STOPPED.value, service_name))
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to update database for service stop: {e}")

            logger.info(f"Service {service_name} stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            await self.stop_service(service_name)
            await asyncio.sleep(2)  # Brief delay

            if service_name in self.services:
                return await self._start_service(service_name, self.services[service_name])
            else:
                logger.error(f"Service configuration not found for {service_name}")
                return False

        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False

    async def shutdown(self):
        """Graceful shutdown of all services"""
        self._log_startup_event(StartupPhase.READY, "Initiating graceful shutdown", 1.0)
        self.shutdown_requested = True

        try:
            # Stop all services in reverse dependency order
            for service_name in reversed(list(self.service_processes.keys())):
                await self.stop_service(service_name)

            # Stop health monitoring
            if self.health_monitor_thread and self.health_monitor_thread.is_alive():
                self.health_monitor_thread.join(timeout=5)

            # Shutdown executor
            self.executor.shutdown(wait=True)

            logger.info("Integrated shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def setup_signal_handlers(orchestrator: IntegratedStartupOrchestrator):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.run(orchestrator.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)

async def main():
    """Main entry point"""
    try:
        # Initialize orchestrator
        orchestrator = IntegratedStartupOrchestrator()

        # Setup signal handlers
        setup_signal_handlers(orchestrator)

        logger.info("Starting DuckBot Integrated Startup System v4.2")

        # Run startup sequence
        success = await orchestrator.startup()

        if success:
            logger.info("🎉 Integrated startup completed successfully!")

            # Print status
            print("\n" + "="*60)
            print("🤖 DUCKBOT INTEGRATED STARTUP SYSTEM v4.2")
            print("="*60)
            print(f"✅ Startup Status: SUCCESS")
            print(f"🔧 Services Running: {sum(1 for s in orchestrator.service_status.values() if s == ServiceStatus.RUNNING)}/{len(orchestrator.services)}")
            print(f"🌐 Overall Health: {orchestrator.health_status.overall_health if orchestrator.health_status else 'Unknown'}")
            print(f"📝 Log Directory: {orchestrator.logs_dir}")
            print("="*60)

            # Keep running until shutdown
            try:
                while not orchestrator.shutdown_requested:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
        else:
            logger.error("❌ Integrated startup failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error in integrated startup: {e}")
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            await orchestrator.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Integrated startup system interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service management module for the modular launcher
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

import sys
from pathlib import Path

# Add launcher directory to Python path for imports
launcher_dir = Path(__file__).parent.parent
sys.path.insert(0, str(launcher_dir))

from models.service_config import ServiceConfig, ServiceInstance, ServiceStatus, PortConfig, ServiceType

class ServiceState(Enum):
    """Service lifecycle states"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RESTARTING = "restarting"

@dataclass
class ServiceHealth:
    """Service health information"""
    is_healthy: bool = False
    response_time: float = 0.0
    last_check: float = 0.0
    error_message: Optional[str] = None
    restart_count: int = 0

class ServiceManager:
    """Manages service lifecycle and monitoring"""

    def __init__(self, logger: logging.Logger, port_manager, config_manager):
        self.logger = logger
        self.port_manager = port_manager
        self.config_manager = config_manager
        self.project_root = Path(__file__).parent.parent.parent

        self.services: Dict[str, ServiceInstance] = {}
        self.service_states: Dict[str, ServiceState] = {}
        self.service_health: Dict[str, ServiceHealth] = {}
        self.service_processes: Dict[str, subprocess.Popen] = {}
        self.service_threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()

        self.health_check_interval = 30  # seconds
        self.max_restart_attempts = 3
        self.restart_cooldown = 60  # seconds

        self._monitoring_thread = None
        self._running = False

    def discover_services(self) -> bool:
        """Discover all available services from configuration"""
        try:
            self.logger.info("Discovering services...")

            # Get all service configurations
            service_configs = self.config_manager.services

            with self.lock:
                for service_name, config in service_configs.items():
                    if config.enabled:
                        self.services[service_name] = ServiceInstance(config)
                        self.service_states[service_name] = ServiceState.IDLE
                        self.service_health[service_name] = ServiceHealth()

            self.logger.info(f"Discovered {len(self.services)} services")
            return True

        except Exception as e:
            self.logger.error(f"Service discovery failed: {e}")
            return False

    def validate_dependencies(self, service_names: List[str]) -> bool:
        """Validate service dependencies before starting"""
        self.logger.info(f"Validating dependencies for services: {service_names}")

        # Build dependency graph
        dependency_graph = {}
        for service_name in service_names:
            if service_name in self.services:
                service_config = self.services[service_name].config
                dependency_graph[service_name] = service_config.dependencies

        # Check for circular dependencies
        if self._has_circular_dependencies(dependency_graph):
            self.logger.error("Circular dependency detected")
            return False

        # Check if all dependencies are available
        for service_name, dependencies in dependency_graph.items():
            for dep in dependencies:
                if dep not in self.services:
                    self.logger.error(f"Service {service_name} depends on non-existent service: {dep}")
                    return False

        self.logger.info("Dependency validation passed")
        return True

    def _has_circular_dependencies(self, graph: Dict[str, List[str]]) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def start_services(self, service_names: List[str]) -> bool:
        """Start multiple services in dependency order"""
        try:
            self.logger.info(f"Starting services: {service_names}")

            # Get startup order based on dependencies
            startup_order = self._resolve_startup_order(service_names)
            self.logger.info(f"Service startup order: {startup_order}")

            # Start monitoring if not already running
            if not self._running:
                self._start_monitoring()

            # Start services in order
            success_count = 0
            for service_name in startup_order:
                if self.start_service(service_name):
                    success_count += 1
                else:
                    self.logger.error(f"Failed to start service: {service_name}")

            total_services = len(service_names)
            success_rate = success_count / total_services if total_services > 0 else 0

            self.logger.info(f"Started {success_count}/{total_services} services ({success_rate:.1%})")
            return success_rate > 0

        except Exception as e:
            self.logger.error(f"Service startup failed: {e}")
            return False

    def _resolve_startup_order(self, service_names: List[str]) -> List[str]:
        """Resolve service startup order based on dependencies"""
        # Simple topological sort
        graph = {}
        for service_name in service_names:
            if service_name in self.services:
                service_config = self.services[service_name].config
                graph[service_name] = [
                    dep for dep in service_config.dependencies
                    if dep in service_names
                ]

        # Topological sort
        visited = set()
        temp_visited = set()
        result = []

        def visit(node):
            if node in temp_visited:
                return  # Skip cycles
            if node in visited:
                return

            temp_visited.add(node)

            for neighbor in graph.get(node, []):
                visit(neighbor)

            temp_visited.remove(node)
            visited.add(node)
            result.append(node)

        for node in service_names:
            if node not in visited:
                visit(node)

        return result

    def start_service(self, service_name: str) -> bool:
        """Start a single service"""
        if service_name not in self.services:
            self.logger.error(f"Service not found: {service_name}")
            return False

        service_instance = self.services[service_name]

        with self.lock:
            if self.service_states[service_name] in [ServiceState.RUNNING, ServiceState.STARTING]:
                self.logger.info(f"Service {service_name} already starting or running")
                return True

            self.service_states[service_name] = ServiceState.STARTING

        try:
            # Allocate ports
            if not self._allocate_service_ports(service_name):
                self.logger.error(f"Failed to allocate ports for service: {service_name}")
                with self.lock:
                    self.service_states[service_name] = ServiceState.ERROR
                return False

            # Setup environment
            env = self._setup_service_environment(service_name)

            # Prepare command
            command = self._prepare_service_command(service_name)

            # Start the service process
            working_dir = self._get_service_working_dir(service_name)
            log_file = self._get_service_log_file(service_name)

            self.logger.info(f"Starting service {service_name}: {command}")

            with open(log_file, 'a', encoding='utf-8') as log_f:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=working_dir,
                    env=env,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )

            # Store process information
            with self.lock:
                self.service_processes[service_name] = process
                service_instance.process_id = process.pid
                service_instance.start_time = time.time()
                self.service_states[service_name] = ServiceState.RUNNING

            self.logger.info(f"Service {service_name} started with PID {process.pid}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start service {service_name}: {e}")
            with self.lock:
                self.service_states[service_name] = ServiceState.ERROR
                service_instance.error_message = str(e)
            return False

    def _allocate_service_ports(self, service_name: str) -> bool:
        """Allocate ports for a service"""
        service_config = self.services[service_name].config

        for port_config in service_config.ports:
            health_url = f"http://localhost:{port_config.number}{port_config.health_endpoint}"
            if not self.port_manager.request_port(
                port_config.number, service_name, health_url
            ):
                self.logger.error(f"Failed to allocate port {port_config.number} for service {service_name}")
                return False

        return True

    def _setup_service_environment(self, service_name: str) -> Dict[str, str]:
        """Setup environment variables for a service"""
        env = os.environ.copy()

        # Add service-specific environment variables
        service_config = self.services[service_name].config

        # Apply service environment variables
        for key, value in service_config.env_vars.items():
            # Substitute environment variables in values
            env_value = os.path.expandvars(value)
            env[key] = env_value

        # Add launcher-specific environment
        env["DUCKBOT_SERVICE_NAME"] = service_name
        env["DUCKBOT_SERVICE_TYPE"] = service_config.type.value
        env["DUCKBOT_LAUNCHER_ROOT"] = str(self.project_root)

        return env

    def _prepare_service_command(self, service_name: str) -> str:
        """Prepare the command for starting a service"""
        service_config = self.services[service_name].config

        # Get Python command
        python_cmd = os.environ.get("PYTHON_CMD", "python")

        # Substitute variables in command
        command = service_config.command.replace("python", python_cmd)

        return command

    def _get_service_working_dir(self, service_name: str) -> str:
        """Get working directory for a service"""
        service_config = self.services[service_name].config

        if service_config.working_dir:
            # Handle relative paths
            work_dir = Path(service_config.working_dir)
            if not work_dir.is_absolute():
                work_dir = self.project_root / work_dir
            return str(work_dir)
        else:
            return str(self.project_root)

    def _get_service_log_file(self, service_name: str) -> str:
        """Get log file path for a service"""
        service_config = self.services[service_name].config

        if service_config.log_file:
            # Handle relative paths
            log_file = Path(service_config.log_file)
            if not log_file.is_absolute():
                log_file = self.project_root / log_file
            return str(log_file)
        else:
            log_dir = self.project_root / "logs"
            log_dir.mkdir(exist_ok=True)
            return str(log_dir / f"{service_name}.log")

    def stop_services(self, service_names: List[str] = None) -> bool:
        """Stop multiple services"""
        if service_names is None:
            service_names = list(self.services.keys())

        self.logger.info(f"Stopping services: {service_names}")

        success_count = 0
        for service_name in service_names:
            if self.stop_service(service_name):
                success_count += 1

        total_services = len(service_names)
        success_rate = success_count / total_services if total_services > 0 else 0

        self.logger.info(f"Stopped {success_count}/{total_services} services ({success_rate:.1%})")
        return success_rate > 0

    def stop_service(self, service_name: str) -> bool:
        """Stop a single service"""
        if service_name not in self.services:
            self.logger.warning(f"Service not found: {service_name}")
            return True  # Consider non-existent services as stopped

        with self.lock:
            current_state = self.service_states[service_name]
            if current_state in [ServiceState.STOPPED, ServiceState.STOPPING]:
                self.logger.info(f"Service {service_name} already stopped or stopping")
                return True

            self.service_states[service_name] = ServiceState.STOPPING

        try:
            # Get the process
            process = self.service_processes.get(service_name)
            if process:
                # Try graceful shutdown first
                if os.name == 'nt':
                    # Windows
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    # Unix-like
                    process.send_signal(signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    process.kill()
                    process.wait()

            # Release ports
            service_config = self.services[service_name].config
            for port_config in service_config.ports:
                self.port_manager.release_port(port_config.number, service_name)

            # Update service state
            with self.lock:
                self.service_states[service_name] = ServiceState.STOPPED
                service_instance = self.services[service_name]
                service_instance.process_id = None
                service_instance.status = ServiceStatus.STOPPED

            # Clean up process reference
            if service_name in self.service_processes:
                del self.service_processes[service_name]

            self.logger.info(f"Service {service_name} stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop service {service_name}: {e}")
            with self.lock:
                self.service_states[service_name] = ServiceState.ERROR
            return False

    def get_service_status(self, service_name: str = None) -> Dict[str, Any]:
        """Get status of a specific service or all services"""
        if service_name:
            if service_name not in self.services:
                return None

            service_instance = self.services[service_name]
            return {
                "name": service_name,
                "display_name": service_instance.config.display_name,
                "state": self.service_states[service_name].value,
                "status": service_instance.status.value,
                "process_id": service_instance.process_id,
                "start_time": service_instance.start_time,
                "uptime": time.time() - service_instance.start_time if service_instance.start_time else 0,
                "restart_count": service_instance.restart_count,
                "error_message": service_instance.error_message,
                "health": {
                    "is_healthy": self.service_health[service_name].is_healthy,
                    "response_time": self.service_health[service_name].response_time,
                    "last_check": self.service_health[service_name].last_check
                }
            }
        else:
            # Get status of all services
            status = {}
            with self.lock:
                for service_name, service_instance in self.services.items():
                    status[service_name] = {
                        "display_name": service_instance.config.display_name,
                        "state": self.service_states[service_name].value,
                        "status": service_instance.status.value,
                        "process_id": service_instance.process_id,
                        "start_time": service_instance.start_time,
                        "uptime": time.time() - service_instance.start_time if service_instance.start_time else 0,
                        "restart_count": service_instance.restart_count,
                        "error_message": service_instance.error_message,
                        "health": {
                            "is_healthy": self.service_health[service_name].is_healthy,
                            "response_time": self.service_health[service_name].response_time,
                            "last_check": self.service_health[service_name].last_check
                        }
                    }
            return status

    def get_available_services(self) -> List[ServiceConfig]:
        """Get list of all available service configurations"""
        with self.lock:
            return [service_instance.config for service_instance in self.services.values()]

    def _start_monitoring(self):
        """Start the service monitoring thread"""
        self._running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        self.logger.info("Service monitoring started")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                self._perform_health_checks()
                self._check_service_crashes()
                self._perform_auto_restart()
                time.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)  # Brief pause before retrying

    def _perform_health_checks(self):
        """Perform health checks on all running services"""
        current_time = time.time()

        with self.lock:
            for service_name, service_instance in self.services.items():
                if self.service_states[service_name] == ServiceState.RUNNING:
                    self._check_service_health(service_name, current_time)

    def _check_service_health(self, service_name: str, current_time: float):
        """Check health of a specific service"""
        service_instance = self.services[service_name]
        health_info = self.service_health[service_name]
        service_config = service_instance.config

        try:
            # Check if process is still running
            process = self.service_processes.get(service_name)
            if process and process.poll() is not None:
                # Process has terminated
                self.logger.warning(f"Service {service_name} process has terminated")
                self.service_states[service_name] = ServiceState.ERROR
                service_instance.error_message = "Process terminated unexpectedly"
                return

            # Perform health check if configured
            if service_config.health_check:
                health_ok = self._perform_custom_health_check(service_name, service_config.health_check)
            else:
                # Default health check: check if ports are responding
                health_ok = True
                for port_config in service_config.ports:
                    if port_config.check_health:
                        if not self._check_port_health(port_config.number):
                            health_ok = False
                            break

            # Update health information
            health_info.is_healthy = health_ok
            health_info.last_check = current_time

            if health_ok:
                service_instance.status = ServiceStatus.RUNNING
            else:
                service_instance.status = ServiceStatus.ERROR
                self.logger.warning(f"Service {service_name} health check failed")

        except Exception as e:
            self.logger.error(f"Health check error for service {service_name}: {e}")
            health_info.is_healthy = False
            health_info.last_check = current_time
            health_info.error_message = str(e)

    def _perform_custom_health_check(self, service_name: str, health_check: str) -> bool:
        """Perform custom health check for a service"""
        try:
            if health_check.startswith("http"):
                # HTTP health check
                import requests
                response = requests.get(health_check, timeout=5)
                return response.status_code < 400
            else:
                # Command-based health check
                result = subprocess.run(
                    health_check,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0

        except Exception as e:
            self.logger.debug(f"Custom health check failed for {service_name}: {e}")
            return False

    def _check_port_health(self, port: int) -> bool:
        """Check if a port is responding"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def _check_service_crashes(self):
        """Check for crashed services"""
        with self.lock:
            for service_name, service_instance in self.services.items():
                if self.service_states[service_name] == ServiceState.RUNNING:
                    process = self.service_processes.get(service_name)
                    if process and process.poll() is not None:
                        self.logger.error(f"Service {service_name} has crashed")
                        self.service_states[service_name] = ServiceState.ERROR
                        service_instance.error_message = "Process crashed"

    def _perform_auto_restart(self):
        """Perform automatic restart of failed services"""
        current_time = time.time()

        with self.lock:
            for service_name, service_instance in self.services.items():
                if (self.service_states[service_name] == ServiceState.ERROR and
                    service_instance.config.auto_restart and
                    service_instance.restart_count < self.max_restart_attempts):

                    # Check cooldown period
                    last_restart_time = service_instance.start_time or 0
                    if current_time - last_restart_time >= self.restart_cooldown:
                        self.logger.info(f"Auto-restarting service: {service_name}")
                        self.service_states[service_name] = ServiceState.RESTARTING
                        service_instance.restart_count += 1

                        # Start the service in a separate thread
                        restart_thread = threading.Thread(
                            target=self._restart_service,
                            args=(service_name,),
                            daemon=True
                        )
                        restart_thread.start()

    def _restart_service(self, service_name: str):
        """Restart a service (called in separate thread)"""
        try:
            # Stop the service
            self.stop_service(service_name)

            # Brief pause
            time.sleep(2)

            # Start the service
            self.start_service(service_name)

        except Exception as e:
            self.logger.error(f"Failed to restart service {service_name}: {e}")

    def shutdown(self):
        """Shutdown all services"""
        self.logger.info("Shutting down service manager...")

        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=10)

        # Stop all services
        self.stop_services()

        self.logger.info("Service manager shutdown complete")

    # Async compatibility methods for modular launcher
    async def start_service(self, service_name: str, service_config: Dict, log_file: Path):
        """Start a specific service (async compatibility method)"""
        return await self._start_service_async(service_name, service_config, log_file)

    async def _start_service_async(self, service_name: str, service_config: Dict, log_file: Path):
        """Start a service asynchronously"""
        try:
            # Convert dict config to ServiceConfig
            config = ServiceConfig(
                name=service_name,
                display_name=service_config.get("name", service_name),
                type=ServiceType.UTILITY,
                description=f"Service: {service_name}",
                command=service_config.get("command", ""),
                working_dir=service_config.get("working_dir", ""),
                env_vars=service_config.get("env_vars", {}),
                dependencies=service_config.get("dependencies", []),
                auto_restart=service_config.get("auto_restart", False)
            )

            # Add port config if needed
            if service_config.get("port"):
                config.ports.append(PortConfig(
                    number=service_config["port"],
                    name=f"{service_name}_port",
                    required=True,
                    check_health=True
                ))

            # Create service instance
            service_instance = ServiceInstance(config)

            with self.lock:
                if service_name in self.service_processes and self.service_processes[service_name].poll() is None:
                    self.logger.info(f"Service {service_name} is already running")
                    return self.service_processes[service_name]

                self.services[service_name] = service_instance
                self.service_states[service_name] = ServiceState.STARTING

            # Prepare command
            command = config.command
            if isinstance(command, list):
                command = " ".join(command)

            # Start the service process
            working_dir = self._get_service_working_dir(service_name)

            self.logger.info(f"Starting service {service_name}: {command}")

            with open(log_file, 'a', encoding='utf-8') as log_f:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=working_dir,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )

            with self.lock:
                self.service_processes[service_name] = process
                service_instance.process_id = process.pid
                service_instance.start_time = time.time()
                self.service_states[service_name] = ServiceState.RUNNING

            self.logger.info(f"Service {service_name} started with PID {process.pid}")
            return process

        except Exception as e:
            self.logger.error(f"Failed to start service {service_name}: {e}")
            with self.lock:
                if service_name in self.service_states:
                    self.service_states[service_name] = ServiceState.ERROR
            return None

    async def stop_service(self, service_name: str, process=None):
        """Stop a specific service (async compatibility method)"""
        try:
            if service_name in self.service_processes:
                await self._stop_service_async(service_name)
            else:
                # Simple process termination
                if process and process.poll() is None:
                    if os.name == 'nt':
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        process.send_signal(signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop service {service_name}: {e}")
            return False

    async def _stop_service_async(self, service_name: str):
        """Stop a service asynchronously"""
        return self.stop_service(service_name)

    async def check_health(self, service_name: str, process) -> bool:
        """Check health of a service (async compatibility method)"""
        try:
            if process and process.poll() is None:
                # Process is running
                if service_name in self.services:
                    service_config = self.services[service_name].config
                    # Check ports
                    for port_config in service_config.ports:
                        if not self._check_port_health(port_config.number):
                            return False
                return True
            return False
        except Exception as e:
            self.logger.error(f"Health check failed for {service_name}: {e}")
            return False
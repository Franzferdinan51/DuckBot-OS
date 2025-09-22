#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port management module for the modular launcher
"""

import socket
import threading
import time
import logging
import requests
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import sys
from pathlib import Path

# Add launcher directory to Python path for imports
launcher_dir = Path(__file__).parent.parent
sys.path.insert(0, str(launcher_dir))

from models.service_config import PortConfig

@dataclass
class PortInfo:
    """Port information and status"""
    number: int
    name: str
    in_use: bool = False
    service_name: Optional[str] = None
    health_check_url: Optional[str] = None
    last_check: Optional[float] = None
    health_status: bool = False

class PortManager:
    """Manages port allocation and conflict resolution"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.ports: Dict[int, PortInfo] = {}
        self.lock = threading.Lock()
        self.health_check_interval = 30  # seconds
        self._health_check_thread = None
        self._running = False

    def initialize(self) -> bool:
        """Initialize port management"""
        try:
            self.logger.info("Initializing port manager...")

            # Define default port mappings
            default_ports = {
                8787: PortInfo(8787, "Enhanced WebUI"),
                8788: PortInfo(8788, "Enhanced WebUI Dashboard"),
                8789: PortInfo(8789, "System Monitoring"),
                8790: PortInfo(8790, "Modern WebUI"),
                3000: PortInfo(3000, "Open WebUI"),
                7799: PortInfo(7799, "UI-TARS Automation"),
                7788: PortInfo(7788, "Browser Automation"),
                8000: PortInfo(8000, "MCP Server"),
                1234: PortInfo(1234, "LM Studio"),
                11434: PortInfo(11434, "Ollama"),
                8080: PortInfo(8080, "DuckBotOS"),
                5000: PortInfo(5000, "Development Server"),
                9000: PortInfo(9000, "API Gateway")
            }

            self.ports = default_ports
            self._scan_ports()
            self._start_health_checks()

            self.logger.info("Port manager initialized")
            return True

        except Exception as e:
            self.logger.error(f"Port manager initialization failed: {e}")
            return False

    def _scan_ports(self):
        """Scan all defined ports for current usage"""
        self.logger.info("Scanning ports...")

        with self.lock:
            for port_num, port_info in self.ports.items():
                port_info.in_use = self._is_port_in_use(port_num)
                if port_info.in_use:
                    self.logger.info(f"Port {port_num} ({port_info.name}) is in use")

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def request_port(self, port_num: int, service_name: str, health_url: str = None) -> bool:
        """Request a port for a service"""
        with self.lock:
            if port_num not in self.ports:
                self.logger.warning(f"Port {port_num} not defined in port mappings")
                # Add it dynamically
                self.ports[port_num] = PortInfo(port_num, f"Dynamic Port for {service_name}")

            port_info = self.ports[port_num]

            if port_info.in_use and port_info.service_name != service_name:
                self.logger.error(f"Port {port_num} already in use by {port_info.service_name}")
                return False

            port_info.service_name = service_name
            port_info.health_check_url = health_url
            port_info.in_use = True

            self.logger.info(f"Port {port_num} allocated to {service_name}")
            return True

    def release_port(self, port_num: int, service_name: str) -> bool:
        """Release a port from a service"""
        with self.lock:
            if port_num not in self.ports:
                self.logger.warning(f"Port {port_num} not found in port mappings")
                return False

            port_info = self.ports[port_num]

            if port_info.service_name != service_name:
                self.logger.warning(f"Port {port_num} not allocated to {service_name}")
                return False

            # Check if port is still actually in use
            if not self._is_port_in_use(port_num):
                port_info.in_use = False
                port_info.service_name = None
                port_info.health_check_url = None
                port_info.health_status = False
                self.logger.info(f"Port {port_num} released from {service_name}")
                return True
            else:
                self.logger.warning(f"Port {port_num} still in use despite release request")
                return False

    def find_available_port(self, preferred_port: int = None, start_range: int = 8000, end_range: int = 9000) -> int:
        """Find an available port in the specified range"""
        if preferred_port and not self._is_port_in_use(preferred_port):
            return preferred_port

        with self.lock:
            for port in range(start_range, end_range):
                if port not in self.ports or not self.ports[port].in_use:
                    if not self._is_port_in_use(port):
                        return port

        return None

    def get_port_status(self) -> Dict[str, any]:
        """Get status of all managed ports"""
        with self.lock:
            return {
                port_num: {
                    "name": info.name,
                    "in_use": info.in_use,
                    "service_name": info.service_name,
                    "health_status": info.health_status,
                    "last_check": info.last_check
                }
                for port_num, info in self.ports.items()
            }

    def _start_health_checks(self):
        """Start background health check thread"""
        self._running = True
        self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()
        self.logger.info("Port health check thread started")

    def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            try:
                self._perform_health_checks()
                time.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                time.sleep(5)  # Brief pause before retrying

    def _perform_health_checks(self):
        """Perform health checks on all active ports"""
        with self.lock:
            for port_num, port_info in self.ports.items():
                if port_info.in_use and port_info.health_check_url:
                    self._check_port_health(port_info)

    def _check_port_health(self, port_info: PortInfo):
        """Check health of a specific port"""
        try:
            if port_info.health_check_url.startswith("http"):
                response = requests.get(
                    port_info.health_check_url,
                    timeout=5,
                    allow_redirects=False
                )
                port_info.health_status = response.status_code < 400
            else:
                # Basic TCP connection check
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    result = sock.connect_ex(('127.0.0.1', port_info.number))
                    port_info.health_status = result == 0

            port_info.last_check = time.time()

        except Exception as e:
            port_info.health_status = False
            port_info.last_check = time.time()
            self.logger.debug(f"Health check failed for port {port_info.number}: {e}")

    def resolve_conflicts(self) -> Dict[str, any]:
        """Resolve port conflicts and suggest alternatives"""
        conflicts = []
        alternatives = {}

        with self.lock:
            for port_num, port_info in self.ports.items():
                if port_info.in_use and port_info.service_name:
                    # Verify the port is actually responding
                    if not port_info.health_status:
                        conflicts.append({
                            "port": port_num,
                            "service": port_info.service_name,
                            "issue": "not_responding"
                        })

        # Suggest alternatives for conflicting ports
        for conflict in conflicts:
            port_num = conflict["port"]
            alternative = self.find_available_port(start_range=port_num + 1, end_range=port_num + 100)
            if alternative:
                alternatives[port_num] = alternative

        return {
            "conflicts": conflicts,
            "alternatives": alternatives,
            "resolution_suggestions": self._generate_resolution_suggestions(conflicts, alternatives)
        }

    def _generate_resolution_suggestions(self, conflicts: List[Dict], alternatives: Dict) -> List[str]:
        """Generate human-readable resolution suggestions"""
        suggestions = []

        for conflict in conflicts:
            port = conflict["port"]
            service = conflict["service"]
            issue = conflict["issue"]

            if issue == "not_responding":
                if port in alternatives:
                    suggestions.append(
                        f"Service '{service}' on port {port} is not responding. "
                        f"Consider moving to port {alternatives[port]}."
                    )
                else:
                    suggestions.append(
                        f"Service '{service}' on port {port} is not responding. "
                        f"Check if the service is running properly."
                    )

        return suggestions

    def shutdown(self):
        """Shutdown the port manager"""
        self._running = False
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
        self.logger.info("Port manager shutdown complete")

    # Async compatibility methods for modular launcher
    async def reserve_port(self, port_num: int) -> bool:
        """Reserve a port for a service (async compatibility method)"""
        return self.request_port(port_num, "unknown_service")

    def get_available_ports(self) -> List[int]:
        """Get list of available ports"""
        available_ports = []
        with self.lock:
            for port_num, port_info in self.ports.items():
                if not port_info.in_use:
                    available_ports.append(port_num)
        return available_ports
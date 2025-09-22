#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service configuration models for the modular launcher
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class ServiceType(Enum):
    """Service type enumeration"""
    WEB_UI = "web_ui"
    AI_SERVICE = "ai_service"
    MONITORING = "monitoring"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    UTILITY = "utility"

class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class PortConfig:
    """Port configuration"""
    number: int
    name: str
    required: bool = True
    check_health: bool = True
    health_endpoint: str = "/"

@dataclass
class ServiceConfig:
    """Individual service configuration"""
    name: str
    display_name: str
    type: ServiceType
    description: str
    command: str
    working_dir: str = ""
    env_vars: Dict[str, str] = field(default_factory=dict)
    ports: List[PortConfig] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    health_check: Optional[str] = None
    startup_timeout: int = 30
    auto_restart: bool = False
    log_file: str = ""
    enabled: bool = True

@dataclass
class LaunchMode:
    """Launch mode configuration"""
    name: str
    display_name: str
    description: str
    services: List[str]
    env_vars: Dict[str, str] = field(default_factory=dict)
    pre_launch: List[str] = field(default_factory=list)
    post_launch: List[str] = field(default_factory=list)
    priority: int = 0
    icon: str = "🚀"

@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    python_required: bool = True
    python_version_min: str = "3.8"
    node_required: bool = False
    node_version_min: str = "16.0"
    required_packages: List[str] = field(default_factory=list)
    optional_packages: List[str] = field(default_factory=list)
    env_files: List[str] = field(default_factory=list)
    path_extensions: List[str] = field(default_factory=list)

@dataclass
class ServiceInstance:
    """Running service instance"""
    config: ServiceConfig
    process_id: Optional[int] = None
    status: ServiceStatus = ServiceStatus.STOPPED
    start_time: Optional[float] = None
    last_health_check: Optional[float] = None
    health_status: bool = False
    restart_count: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.config.name,
            "display_name": self.config.display_name,
            "status": self.status.value,
            "process_id": self.process_id,
            "start_time": self.start_time,
            "last_health_check": self.last_health_check,
            "health_status": self.health_status,
            "restart_count": self.restart_count,
            "error_message": self.error_message,
            "ports": [port.number for port in self.config.ports]
        }
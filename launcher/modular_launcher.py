#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Modular Launcher - Core Architecture
A clean, maintainable replacement for the monolithic batch file
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import psutil
import socket
import time
from concurrent.futures import ThreadPoolExecutor

# Add duckbot to path
sys.path.insert(0, str(Path(__file__).parent))

from core.service_manager import ServiceManager
from core.port_manager import PortManager
from core.environment_manager import EnvironmentManager
from core.config_manager import ConfigManager
from core.error_handler import ErrorHandler, ErrorLevel, ErrorCategory
from core.launcher_ui import LauncherUI

@dataclass
class LauncherConfig:
    """Configuration for the modular launcher"""
    base_dir: Path
    config_dir: Path
    logs_dir: Path
    temp_dir: Path

    # Service configurations
    webui_port: int = 8787
    monitoring_port: int = 8789
    ai_router_port: int = 8790

    # Feature flags
    enable_auto_restart: bool = True
    enable_health_monitoring: bool = True
    enable_auto_port_management: bool = True
    enable_detailed_logging: bool = True

    # Performance settings
    max_concurrent_services: int = 5
    service_timeout_seconds: int = 30
    health_check_interval: int = 30

class LaunchMode(Enum):
    """Standardized launch modes"""
    ULTIMATE = "ultimate"
    WEBUI_ONLY = "webui_only"
    MONITORING_ONLY = "monitoring_only"
    LOCAL_ONLY = "local_only"
    HYBRID = "hybrid"
    HEADLESS = "headless"
    DEVELOPER = "developer"
    MINIMAL = "minimal"

class ModularLauncher:
    """Main launcher class coordinating all modular components"""

    def __init__(self, config: LauncherConfig = None):
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()

        # Initialize core components
        self.env_manager = EnvironmentManager(self.logger)
        self.config_manager = ConfigManager(self.logger, self.config.config_dir)
        self.port_manager = PortManager(self.logger)
        self.service_manager = ServiceManager(self.logger, self.port_manager, self.config_manager)
        self.error_handler = ErrorHandler(self.logger)
        self.ui = LauncherUI(self.logger)

        # Initialize port manager
        self.port_manager.initialize()

        # Service registry
        self.services = self._register_services()

        # Runtime state
        self.running_services = {}
        self.current_launch_mode = None

    def _get_default_config(self) -> LauncherConfig:
        """Create default configuration"""
        base_dir = Path(__file__).parent
        return LauncherConfig(
            base_dir=base_dir,
            config_dir=base_dir / "config",
            logs_dir=base_dir / "logs",
            temp_dir=base_dir / "temp"
        )

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging system"""
        self.config.logs_dir.mkdir(exist_ok=True)

        logger = logging.getLogger("DuckBot.Launcher")
        logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # File handler
        file_handler = logging.FileHandler(
            self.config.logs_dir / "launcher.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def _register_services(self) -> Dict[str, Dict]:
        """Register all available services with their configurations"""
        return {
            "enhanced_webui": {
                "name": "Enhanced WebUI Dashboard",
                "command": ["python", "-m", "duckbot.ui.unified_webui"],
                "args": ["--host", "127.0.0.1", "--port", str(self.config.webui_port), "--mode", "classic"],
                "port": self.config.webui_port,
                "dependencies": ["environment_valid"],
                "essential": True,
                "auto_restart": True
            },
            "system_monitor": {
                "name": "System Monitoring Dashboard",
                "command": ["python", "-m", "duckbot.services.enhanced_monitoring_dashboard"],
                "args": ["--host", "127.0.0.1", "--port", str(self.config.monitoring_port)],
                "port": self.config.monitoring_port,
                "dependencies": ["environment_valid"],
                "essential": False,
                "auto_restart": True
            },
            "ai_router": {
                "name": "AI Router Service",
                "command": ["python", "-m", "duckbot.core.ai_provider_manager"],
                "args": ["--mode", "router"],
                "port": self.config.ai_router_port,
                "dependencies": ["environment_valid"],
                "essential": True,
                "auto_restart": True
            },
            "bytebot": {
                "name": "ByteBot Desktop Automation",
                "command": ["python", "-c", "from duckbot.integrations.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"],
                "args": [],
                "port": None,
                "dependencies": ["environment_valid"],
                "essential": False,
                "auto_restart": False
            },
            "discord_bot": {
                "name": "Discord Bot",
                "command": ["python", "-m", "duckbot.ui.discord_bot"],
                "args": [],
                "port": None,
                "dependencies": ["ai_router"],
                "essential": False,
                "auto_restart": True
            },
            "vibevoice": {
                "name": "VibeVoice TTS Service",
                "command": ["python", "-m", "duckbot.integrations.vibevoice_client"],
                "args": [],
                "port": None,
                "dependencies": ["environment_valid"],
                "essential": False,
                "auto_restart": True
            },
            "cost_tracker": {
                "name": "Cost Tracker",
                "command": ["python", "-m", "duckbot.core.cost_management"],
                "args": ["--mode", "monitor"],
                "port": None,
                "dependencies": ["environment_valid"],
                "essential": False,
                "auto_restart": True
            }
        }

    async def launch_mode(self, mode: LaunchMode, additional_args: List[str] = None) -> bool:
        """Launch DuckBot in specified mode"""
        self.current_launch_mode = mode
        self.logger.info(f"Launching DuckBot in {mode.value} mode")

        try:
            # Validate environment
            if not self.env_manager.validate_environment():
                self.logger.error("Environment validation failed")
                return False

            # Get service list for this mode
            services_to_launch = self._get_services_for_mode(mode)

            # Start services
            success = await self._start_services(services_to_launch)

            if success and self.config.enable_health_monitoring:
                # Start health monitoring
                asyncio.create_task(self._health_monitoring_loop())

            return success

        except Exception as e:
            self.error_handler.handle_error(
                ErrorLevel.ERROR,
                ErrorCategory.SERVICE,
                f"Failed to launch {mode.value} mode",
                {"error": str(e), "traceback": traceback.format_exc()}
            )
            return False

    def _get_services_for_mode(self, mode: LaunchMode) -> List[str]:
        """Get list of services to start for given mode"""
        mode_services = {
            LaunchMode.ULTIMATE: [
                "enhanced_webui", "system_monitor", "ai_router",
                "bytebot", "discord_bot", "vibevoice", "cost_tracker"
            ],
            LaunchMode.WEBUI_ONLY: ["enhanced_webui", "ai_router"],
            LaunchMode.MONITORING_ONLY: ["system_monitor", "ai_router"],
            LaunchMode.LOCAL_ONLY: ["enhanced_webui", "ai_router", "cost_tracker"],
            LaunchMode.HYBRID: ["enhanced_webui", "system_monitor", "ai_router"],
            LaunchMode.HEADLESS: ["ai_router", "cost_tracker"],
            LaunchMode.DEVELOPER: ["enhanced_webui", "system_monitor", "ai_router"],
            LaunchMode.MINIMAL: ["enhanced_webui", "ai_router"]
        }

        return mode_services.get(mode, ["enhanced_webui", "ai_router"])

    async def _start_services(self, service_names: List[str]) -> bool:
        """Start list of services with dependency management"""
        if not service_names:
            return True

        # Validate services exist
        invalid_services = [s for s in service_names if s not in self.services]
        if invalid_services:
            self.logger.error(f"Invalid services: {invalid_services}")
            return False

        # Start services with dependency resolution
        started_services = []

        for service_name in service_names:
            service_config = self.services[service_name]

            # Check dependencies
            if not self._check_dependencies(service_config.get("dependencies", [])):
                self.logger.error(f"Dependencies not met for {service_name}")
                continue

            # Manage ports
            if service_config.get("port"):
                if not await self.port_manager.reserve_port(service_config["port"]):
                    self.logger.error(f"Port {service_config['port']} not available for {service_name}")
                    continue

            # Start service
            try:
                process = await self.service_manager.start_service(
                    service_name,
                    service_config,
                    self.config.logs_dir / f"{service_name}.log"
                )

                if process:
                    self.running_services[service_name] = process
                    started_services.append(service_name)
                    self.logger.info(f"Started {service_name}")

                else:
                    self.logger.error(f"Failed to start {service_name}")

            except Exception as e:
                self.error_handler.handle_error(e, f"Error starting {service_name}")

        self.logger.info(f"Successfully started {len(started_services)}/{len(service_names)} services")
        return len(started_services) > 0

    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if dependencies are satisfied"""
        for dep in dependencies:
            if dep == "environment_valid":
                return self.env_manager.validate_environment()
            elif dep in self.running_services:
                return True
        return True

    async def _health_monitoring_loop(self):
        """Continuous health monitoring of running services"""
        while self.running_services:
            try:
                for service_name, process in list(self.running_services.items()):
                    if not await self.service_manager.check_health(service_name, process):
                        self.logger.warning(f"Service {service_name} unhealthy")

                        if self.services[service_name].get("auto_restart", False):
                            self.logger.info(f"Attempting to restart {service_name}")
                            await self._restart_service(service_name)

                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                self.error_handler.handle_error(e, "Health monitoring error")
                await asyncio.sleep(self.config.health_check_interval)

    async def _restart_service(self, service_name: str):
        """Restart a specific service"""
        if service_name not in self.running_services:
            return

        # Stop existing process
        process = self.running_services[service_name]
        await self.service_manager.stop_service(service_name, process)

        # Start new process
        service_config = self.services[service_name]
        new_process = await self.service_manager.start_service(
            service_name,
            service_config,
            self.config.logs_dir / f"{service_name}.log"
        )

        if new_process:
            self.running_services[service_name] = new_process
            self.logger.info(f"Restarted {service_name}")
        else:
            self.logger.error(f"Failed to restart {service_name}")

    async def stop_all_services(self):
        """Stop all running services"""
        self.logger.info("Stopping all services")

        for service_name, process in self.running_services.items():
            await self.service_manager.stop_service(service_name, process)

        self.running_services.clear()
        self.logger.info("All services stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current launcher status"""
        return {
            "launch_mode": self.current_launch_mode.value if self.current_launch_mode else None,
            "running_services": list(self.running_services.keys()),
            "service_count": len(self.running_services),
            "environment_valid": self.env_manager.is_environment_valid(),
            "ports_available": self.port_manager.get_available_ports()
        }

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DuckBot Modular Launcher")
    parser.add_argument("--mode", choices=[m.value for m in LaunchMode],
                       default="ultimate", help="Launch mode")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-ui", action="store_true", help="Run without UI")

    args = parser.parse_args()

    # Create launcher
    launcher = ModularLauncher()

    if args.no_ui:
        # Headless mode
        mode = LaunchMode(args.mode)
        success = await launcher.launch_mode(mode)
        if success:
            print(f"DuckBot started successfully in {mode.value} mode")
            print("Press Ctrl+C to stop")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await launcher.stop_all_services()
        else:
            print("Failed to start DuckBot")
            sys.exit(1)
    else:
        # UI mode
        await launcher.ui.run()

if __name__ == "__main__":
    asyncio.run(main())
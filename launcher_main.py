#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Modular Launcher Architecture
Main orchestrator for the enhanced launcher system
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modular components
from launcher.core.environment_manager import EnvironmentManager
from launcher.core.service_manager import ServiceManager
from launcher.core.port_manager import PortManager
from launcher.core.config_manager import ConfigManager
from launcher.core.error_handler import ErrorHandler
from launcher.core.launcher_ui import LauncherUI
from launcher.models.service_config import ServiceConfig, LaunchMode

@dataclass
class LauncherState:
    """Central launcher state management"""
    current_mode: str = "idle"
    active_services: List[str] = None
    environment_ready: bool = False
    last_error: Optional[str] = None
    start_time: float = None

    def __post_init__(self):
        if self.active_services is None:
            self.active_services = []
        if self.start_time is None:
            self.start_time = time.time()

class ModularLauncher:
    """Main launcher orchestrator"""

    def __init__(self):
        self.state = LauncherState()
        self.logger = self._setup_logging()
        self.env_manager = EnvironmentManager(self.logger)
        self.port_manager = PortManager(self.logger)
        self.config_manager = ConfigManager(self.logger)
        self.error_handler = ErrorHandler(self.logger)
        self.service_manager = ServiceManager(
            self.logger, self.port_manager, self.config_manager
        )
        self.ui = LauncherUI(self.logger)

        self.logger.info("Modular Launcher initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup centralized logging"""
        logger = logging.getLogger('DuckBotLauncher')
        logger.setLevel(logging.INFO)

        # Clear existing handlers to avoid conflicts
        logger.handlers.clear()

        # Create logs directory
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(
            log_dir / "launcher.log", encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Simple formatter that doesn't use 'category'
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Prevent propagation to avoid conflicts with root logger
        logger.propagate = False

        return logger

    def initialize(self) -> bool:
        """Initialize launcher environment"""
        try:
            self.logger.info("Initializing launcher environment...")

            # Validate environment
            if not self.env_manager.validate_environment():
                self.state.last_error = "Environment validation failed"
                return False

            # Load configurations
            if not self.config_manager.load_configurations():
                self.state.last_error = "Configuration loading failed"
                return False

            # Initialize port management
            if not self.port_manager.initialize():
                self.state.last_error = "Port management initialization failed"
                return False

            # Discover available services
            if not self.service_manager.discover_services():
                self.state.last_error = "Service discovery failed"
                return False

            self.state.environment_ready = True
            self.logger.info("Launcher environment initialized successfully")
            return True

        except Exception as e:
            self.state.last_error = str(e)
            self.logger.error(f"Initialization failed: {e}")
            return False

    def get_available_modes(self) -> List[LaunchMode]:
        """Get list of available launch modes"""
        return self.config_manager.get_launch_modes()

    def launch_mode(self, mode_name: str) -> bool:
        """Launch a specific mode"""
        try:
            self.logger.info(f"Launching mode: {mode_name}")
            self.state.current_mode = mode_name

            # Get mode configuration
            mode_config = self.config_manager.get_mode_config(mode_name)
            if not mode_config:
                self.state.last_error = f"Mode {mode_name} not found"
                return False

            # Validate dependencies
            if not self.service_manager.validate_dependencies(mode_config.services):
                self.state.last_error = "Service dependencies not met"
                return False

            # Start services
            success = self.service_manager.start_services(mode_config.services)
            if success:
                self.state.active_services = mode_config.services
                self.logger.info(f"Successfully launched mode: {mode_name}")
                return True
            else:
                self.state.last_error = "Failed to start services"
                return False

        except Exception as e:
            self.state.last_error = str(e)
            self.logger.error(f"Launch failed: {e}")
            return False

    def stop_services(self, service_names: List[str] = None) -> bool:
        """Stop specific or all services"""
        try:
            if service_names is None:
                service_names = self.state.active_services

            success = self.service_manager.stop_services(service_names)
            if success:
                # Update active services list
                self.state.active_services = [
                    s for s in self.state.active_services
                    if s not in service_names
                ]
                self.logger.info(f"Stopped services: {service_names}")
                return True
            else:
                return False

        except Exception as e:
            self.state.last_error = str(e)
            self.logger.error(f"Stop services failed: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "launcher": {
                "state": asdict(self.state),
                "uptime": time.time() - self.state.start_time
            },
            "services": self.service_manager.get_service_status(),
            "ports": self.port_manager.get_port_status(),
            "environment": self.env_manager.get_environment_status()
        }

    def run_interactive(self):
        """Run interactive launcher mode"""
        if not self.initialize():
            print(f"Initialization failed: {self.state.last_error}")
            return

        self.ui.show_welcome()

        while True:
            try:
                # Get available modes
                modes = self.get_available_modes()

                # Show menu
                choice = self.ui.show_main_menu(modes)

                if choice == "exit":
                    self.stop_services()
                    self.ui.show_goodbye()
                    break

                elif choice == "status":
                    status = self.get_system_status()
                    self.ui.show_status(status)

                elif choice == "stop":
                    self.stop_services()
                    self.ui.show_services_stopped()

                elif choice in modes:
                    success = self.launch_mode(choice)
                    if success:
                        self.ui.show_launch_success(choice)
                    else:
                        self.ui.show_launch_failed(choice, self.state.last_error)

                else:
                    self.ui.show_invalid_choice()

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nShutting down...")
                self.stop_services()
                break
            except Exception as e:
                self.logger.error(f"Interactive mode error: {e}")
                print(f"Error: {e}")
                input("Press Enter to continue...")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='DuckBot Modular Launcher')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('mode', nargs='?', help='Mode or service name')
    parser.add_argument('--list-services', action='store_true', help='List available services')
    parser.add_argument('--list-modes', action='store_true', help='List available launch modes')
    parser.add_argument('--service-status', help='Get status of specific service')
    parser.add_argument('--system-status', action='store_true', help='Get overall system status')

    args = parser.parse_args()

    # Handle commands that don't require a mode
    if args.list_services or args.list_modes or args.service_status or args.system_status:
        # These options don't require a command
        pass
    elif not args.command:
        show_help()
        return

    launcher = ModularLauncher()

    if not launcher.initialize():
        print(f"Initialization failed: {launcher.state.last_error}")
        return

    if args.command == 'service' and args.mode:
        # Launch specific service
        success = launcher.service_manager.start_service(args.mode)
        if success:
            print(f"Service {args.mode} started successfully")
        else:
            print(f"Failed to start service {args.mode}: {launcher.state.last_error}")

    elif args.command in launcher.get_available_modes():
        # Launch specific mode
        success = launcher.launch_mode(args.command)
        if success:
            print(f"Mode {args.command} started successfully")
        else:
            print(f"Failed to start mode {args.command}: {launcher.state.last_error}")

    elif args.list_services:
        # List available services
        services = launcher.service_manager.get_available_services()
        print(json.dumps([{
            'name': service.name,
            'display_name': service.display_name,
            'type': service.type.value,
            'description': service.description,
            'ports': [port.number for port in service.ports],
            'enabled': service.enabled
        } for service in services], indent=2))

    elif args.list_modes:
        # List available modes
        modes = launcher.get_available_modes()
        mode_configs = [launcher.config_manager.get_mode_config(mode) for mode in modes]
        print(json.dumps([{
            'name': mode.name,
            'display_name': mode.display_name,
            'description': mode.description,
            'services': mode.services,
            'priority': mode.priority,
            'icon': mode.icon
        } for mode in mode_configs if mode], indent=2))

    elif args.service_status:
        # Get service status
        status = launcher.service_manager.get_service_status(args.service_status)
        print(json.dumps(status, indent=2))

    elif args.system_status:
        # Get system status
        status = launcher.get_system_status()
        print(json.dumps(status, indent=2))

    else:
        # Default to interactive mode
        launcher.run_interactive()

def show_help():
    """Show help information"""
    help_text = """
DuckBot Modular Launcher - Version 1.0.0

USAGE:
    python launcher_main.py [COMMAND] [MODE] [OPTIONS]

COMMANDS:
    service <name>           Launch a specific service
    <mode_name>              Launch a specific mode (ultimate, enhanced_webui, etc.)

OPTIONS:
    --help                   Show this help message
    --list-services          List all available services
    --list-modes             List all available launch modes
    --service-status <name>  Get status of specific service
    --system-status          Get overall system status

AVAILABLE MODES:
    ultimate                 Ultimate Complete Mode
    enhanced_webui           Enhanced WebUI Mode
    monitoring               System Monitoring Mode
    local_only               Local Privacy Mode
    hybrid                   Hybrid Cloud+Local Mode
    duckbot_os               DuckBotOS Mode
    minimal                  Minimal Resource Mode
    developer                Developer Debug Mode

EXAMPLES:
    python launcher_main.py ultimate
    python launcher_main.py service enhanced_webui
    python launcher_main.py --list-services
    python launcher_main.py --service-status enhanced_webui
"""
    print(help_text)

if __name__ == "__main__":
    main()
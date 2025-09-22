#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management module for the modular launcher
"""

import json
import yaml
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
from pathlib import Path

# Add launcher directory to Python path for imports
launcher_dir = Path(__file__).parent.parent
sys.path.insert(0, str(launcher_dir))

from models.service_config import ServiceConfig, LaunchMode, PortConfig, ServiceType

class ConfigManager:
    """Manages service and mode configurations"""

    def __init__(self, logger: logging.Logger = None, config_dir: Path = None):
        self.logger = logger or logging.getLogger(__name__)
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = config_dir or self.project_root / "config"
        self.services: Dict[str, ServiceConfig] = {}
        self.launch_modes: Dict[str, LaunchMode] = {}
        self.global_config: Dict[str, Any] = {}

    def load_configurations(self) -> bool:
        """Load all configuration files"""
        try:
            self.logger.info("Loading configurations...")

            # Load global configuration
            self._load_global_config()

            # Load service configurations
            self._load_service_configs()

            # Load launch mode configurations
            self._load_launch_mode_configs()

            # Validate configurations
            if not self._validate_configurations():
                self.logger.error("Configuration validation failed")
                return False

            self.logger.info("Configurations loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Configuration loading failed: {e}")
            return False

    def _load_global_config(self):
        """Load global configuration from JSON and YAML files"""
        config_files = [
            "ai_config.json",
            "ecosystem_config.yaml",
            "unified_services_config.json",
            "hardware_config.json"
        ]

        for config_file in config_files:
            config_path = self.config_dir / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        if config_file.endswith('.json'):
                            config_data = json.load(f)
                        elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                            config_data = yaml.safe_load(f)
                        else:
                            continue

                    self.global_config.update(config_data)
                    self.logger.info(f"Loaded global config from: {config_file}")

                except Exception as e:
                    self.logger.warning(f"Failed to load config {config_file}: {e}")

    def _load_service_configs(self):
        """Load service configurations"""
        # Load predefined services
        predefined_services = self._get_predefined_services()
        self.services.update(predefined_services)

        # Load custom service configs if they exist
        custom_services_path = self.config_dir / "services.json"
        if custom_services_path.exists():
            try:
                with open(custom_services_path, 'r', encoding='utf-8') as f:
                    custom_services = json.load(f)
                    for service_data in custom_services:
                        service_config = self._dict_to_service_config(service_data)
                        self.services[service_config.name] = service_config
                self.logger.info("Loaded custom service configurations")
            except Exception as e:
                self.logger.warning(f"Failed to load custom services: {e}")

    def _load_launch_mode_configs(self):
        """Load launch mode configurations"""
        # Load predefined launch modes
        predefined_modes = self._get_predefined_launch_modes()
        self.launch_modes.update(predefined_modes)

        # Load custom mode configs if they exist
        custom_modes_path = self.config_dir / "launch_modes.json"
        if custom_modes_path.exists():
            try:
                with open(custom_modes_path, 'r', encoding='utf-8') as f:
                    custom_modes = json.load(f)
                    for mode_data in custom_modes:
                        mode_config = self._dict_to_launch_mode(mode_data)
                        self.launch_modes[mode_config.name] = mode_config
                self.logger.info("Loaded custom launch mode configurations")
            except Exception as e:
                self.logger.warning(f"Failed to load custom launch modes: {e}")

    def _get_predefined_services(self) -> Dict[str, ServiceConfig]:
        """Get predefined service configurations"""
        services = {
            "enhanced_webui": ServiceConfig(
                name="enhanced_webui",
                display_name="Enhanced WebUI",
                type=ServiceType.WEB_UI,
                description="Modern web interface with real-time updates",
                command="python -m duckbot.enhanced_webui",
                ports=[
                    PortConfig(8787, "Enhanced WebUI", health_endpoint="/")
                ],
                log_file="logs/enhanced_webui.log"
            ),
            "enhanced_dashboard": ServiceConfig(
                name="enhanced_dashboard",
                display_name="Enhanced Dashboard",
                type=ServiceType.WEB_UI,
                description="Enhanced monitoring dashboard",
                command="python duckbot/enhanced_webui.py --dashboard",
                ports=[
                    PortConfig(8788, "Enhanced Dashboard", health_endpoint="/api/status")
                ],
                log_file="logs/enhanced_dashboard.log"
            ),
            "system_monitoring": ServiceConfig(
                name="system_monitoring",
                display_name="System Monitoring",
                type=ServiceType.MONITORING,
                description="Real-time system metrics and performance tracking",
                command="python ai_ecosystem_manager.py",
                ports=[
                    PortConfig(8789, "System Monitoring", health_endpoint="/health")
                ],
                log_file="logs/system_monitoring.log"
            ),
            "open_webui": ServiceConfig(
                name="open_webui",
                display_name="Open WebUI",
                type=ServiceType.WEB_UI,
                description="Open WebUI chat interface",
                command="python -m duckbot.webui",
                ports=[
                    PortConfig(3000, "Open WebUI", health_endpoint="/")
                ],
                log_file="logs/open_webui.log"
            ),
            "modern_webui": ServiceConfig(
                name="modern_webui",
                display_name="Modern WebUI",
                type=ServiceType.WEB_UI,
                description="Modern React-based web interface",
                command="python duckbot/react-webui/server.py",
                ports=[
                    PortConfig(8790, "Modern WebUI", health_endpoint="/")
                ],
                log_file="logs/modern_webui.log"
            ),
            "ui_tars": ServiceConfig(
                name="ui_tars",
                display_name="UI-TARS Automation",
                type=ServiceType.AUTOMATION,
                description="GUI automation using UI-TARS",
                command="python duckbot/integrations/ui_tars_integration.py",
                ports=[
                    PortConfig(7799, "UI-TARS", health_endpoint="/health")
                ],
                log_file="logs/ui_tars.log"
            ),
            "browser_automation": ServiceConfig(
                name="browser_automation",
                display_name="Browser Automation",
                type=ServiceType.AUTOMATION,
                description="AI-powered web automation",
                command="python duckbot/integrations/browser_use_integration.py",
                ports=[
                    PortConfig(7788, "Browser Automation", health_endpoint="/health")
                ],
                log_file="logs/browser_automation.log"
            ),
            "mcp_server": ServiceConfig(
                name="mcp_server",
                display_name="MCP Server",
                type=ServiceType.INTEGRATION,
                description="Model Context Protocol server",
                command="python start_mcp_server.py",
                ports=[
                    PortConfig(8000, "MCP Server", health_endpoint="/health")
                ],
                log_file="logs/mcp_server.log"
            ),
            "ai_ecosystem": ServiceConfig(
                name="ai_ecosystem",
                display_name="AI Ecosystem Manager",
                type=ServiceType.AI_SERVICE,
                description="AI-powered ecosystem management",
                command="python core_ai/ai_ecosystem_manager.py",
                log_file="logs/ai_ecosystem.log"
            ),
            "local_ecosystem": ServiceConfig(
                name="local_ecosystem",
                display_name="Local Ecosystem",
                type=ServiceType.AI_SERVICE,
                description="Local-only AI ecosystem",
                command="python core_ai/start_local_ecosystem.py",
                env_vars={"AI_LOCAL_ONLY_MODE": "true"},
                log_file="logs/local_ecosystem.log"
            ),
            "duckbot_os": ServiceConfig(
                name="duckbot_os",
                display_name="DuckBotOS",
                type=ServiceType.WEB_UI,
                description="AI web operating system",
                command="python -m duckbot.webui --os-mode",
                ports=[
                    PortConfig(8080, "DuckBotOS", health_endpoint="/")
                ],
                log_file="logs/duckbot_os.log"
            ),
            "bytebot": ServiceConfig(
                name="bytebot",
                display_name="ByteBot Desktop Automation",
                type=ServiceType.AUTOMATION,
                description="Natural language desktop automation",
                command="python duckbot/integrations/bytebot_integration.py",
                log_file="logs/bytebot.log"
            ),
            "archon": ServiceConfig(
                name="archon",
                display_name="Archon Multi-Agent",
                type=ServiceType.AI_SERVICE,
                description="Advanced multi-agent orchestration",
                command="python duckbot/integrations/archon_integration.py",
                log_file="logs/archon.log"
            ),
            "charm_terminal": ServiceConfig(
                name="charm_terminal",
                display_name="Charm Terminal",
                type=ServiceType.UTILITY,
                description="Beautiful terminal interface",
                command="charm duckbot",
                log_file="logs/charm_terminal.log"
            ),
            "discord_bot": ServiceConfig(
                name="discord_bot",
                display_name="Discord Bot",
                type=ServiceType.INTEGRATION,
                description="Discord integration bot",
                command="python duckbot/ui/discord_bot.py",
                env_vars={"DISCORD_TOKEN": "${DISCORD_TOKEN}"},
                log_file="logs/discord_bot.log"
            ),
            "vibevoice": ServiceConfig(
                name="vibevoice",
                display_name="VibeVoice TTS",
                type=ServiceType.INTEGRATION,
                description="Text-to-speech integration",
                command="python duckbot/integrations/vibevoice_client.py",
                log_file="logs/vibevoice.log"
            ),
            "model_training": ServiceConfig(
                name="model_training",
                display_name="Model Training Studio",
                type=ServiceType.AI_SERVICE,
                description="Train and fine-tune AI models with GGUF and Hugging Face support",
                command="python launcher-modules/model-training/model_trainer.py",
                log_file="logs/model_training.log"
            )
        }
        
        return services

    def _get_predefined_launch_modes(self) -> Dict[str, LaunchMode]:
        """Get predefined launch mode configurations"""
        return {
            "ultimate": LaunchMode(
                name="ultimate",
                display_name="🚀 Ultimate Complete Mode",
                description="Complete enhanced mode with all integrations",
                services=[
                    "enhanced_webui", "enhanced_dashboard", "system_monitoring",
                    "open_webui", "modern_webui", "ai_ecosystem", "bytebot",
                    "archon", "ui_tars", "browser_automation", "mcp_server"
                ],
                priority=10,
                icon="🚀"
            ),
            "enhanced_webui": LaunchMode(
                name="enhanced_webui",
                display_name="🌐 Enhanced WebUI Mode",
                description="Modern web interface with real-time updates",
                services=["enhanced_webui", "enhanced_dashboard", "system_monitoring"],
                priority=8,
                icon="🌐"
            ),
            "monitoring": LaunchMode(
                name="monitoring",
                display_name="📊 System Monitoring Mode",
                description="Real-time system metrics and performance tracking",
                services=["system_monitoring", "enhanced_dashboard"],
                priority=7,
                icon="📊"
            ),
            "local_only": LaunchMode(
                name="local_only",
                display_name="🔒 Local Privacy Mode",
                description="Complete offline operation with LM Studio",
                services=["local_ecosystem", "enhanced_webui", "system_monitoring"],
                env_vars={"AI_LOCAL_ONLY_MODE": "true"},
                priority=9,
                icon="🔒"
            ),
            "hybrid": LaunchMode(
                name="hybrid",
                display_name="☁️ Hybrid Cloud+Local Mode",
                description="Intelligent local/cloud AI routing",
                services=["ai_ecosystem", "enhanced_webui", "system_monitoring"],
                env_vars={"AI_HYBRID_MODE": "true"},
                priority=8,
                icon="☁️"
            ),
            "duckbot_os": LaunchMode(
                name="duckbot_os",
                display_name="🖥️ DuckBotOS Mode",
                description="AI web operating system",
                services=["duckbot_os", "system_monitoring"],
                priority=6,
                icon="🖥️"
            ),
            "minimal": LaunchMode(
                name="minimal",
                display_name="⚡ Minimal Resource Mode",
                description="Essential services only for low-resource systems",
                services=["enhanced_webui", "system_monitoring"],
                priority=5,
                icon="⚡"
            ),
            "developer": LaunchMode(
                name="developer",
                display_name="🔧 Developer Debug Mode",
                description="Full debugging and development tools",
                services=["enhanced_webui", "system_monitoring", "ai_ecosystem"],
                env_vars={"DEBUG_MODE": "true"},
                priority=4,
                icon="🔧"
            ),
            "model_training": LaunchMode(
                name="model_training",
                display_name="🤖 Model Training Studio",
                description="Train and fine-tune AI models with GGUF and Hugging Face support",
                services=["model_training"],
                priority=7,
                icon="🤖"
            )
        }

    def _dict_to_service_config(self, data: Dict) -> ServiceConfig:
        """Convert dictionary to ServiceConfig"""
        ports = [
            PortConfig(**port_data) for port_data in data.get("ports", [])
        ]
        return ServiceConfig(
            name=data["name"],
            display_name=data["display_name"],
            type=ServiceType(data["type"]),
            description=data["description"],
            command=data["command"],
            working_dir=data.get("working_dir", ""),
            env_vars=data.get("env_vars", {}),
            ports=ports,
            dependencies=data.get("dependencies", []),
            health_check=data.get("health_check"),
            startup_timeout=data.get("startup_timeout", 30),
            auto_restart=data.get("auto_restart", False),
            log_file=data.get("log_file", ""),
            enabled=data.get("enabled", True)
        )

    def _dict_to_launch_mode(self, data: Dict) -> LaunchMode:
        """Convert dictionary to LaunchMode"""
        return LaunchMode(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            services=data["services"],
            env_vars=data.get("env_vars", {}),
            pre_launch=data.get("pre_launch", []),
            post_launch=data.get("post_launch", []),
            priority=data.get("priority", 0),
            icon=data.get("icon", "🚀")
        )

    def _validate_configurations(self) -> bool:
        """Validate all configurations"""
        self.logger.info("Validating configurations...")

        # Validate service configurations
        for service_name, service in self.services.items():
            if not self._validate_service_config(service):
                self.logger.error(f"Service configuration validation failed: {service_name}")
                return False

        # Validate launch mode configurations
        for mode_name, mode in self.launch_modes.items():
            if not self._validate_launch_mode_config(mode):
                self.logger.error(f"Launch mode configuration validation failed: {mode_name}")
                return False

        self.logger.info("Configuration validation passed")
        return True

    def _validate_service_config(self, service: ServiceConfig) -> bool:
        """Validate a single service configuration"""
        if not service.name or not service.command:
            return False

        # Check port conflicts
        service_ports = [port.number for port in service.ports]
        if len(service_ports) != len(set(service_ports)):
            return False  # Duplicate ports in service config

        # Check dependencies exist
        for dep in service.dependencies:
            if dep not in self.services:
                self.logger.warning(f"Service {service.name} depends on non-existent service: {dep}")

        return True

    def _validate_launch_mode_config(self, mode: LaunchMode) -> bool:
        """Validate a single launch mode configuration"""
        if not mode.name or not mode.services:
            return False

        # Check all services exist
        for service_name in mode.services:
            if service_name not in self.services:
                self.logger.warning(f"Launch mode {mode.name} references non-existent service: {service_name}")

        return True

    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get service configuration by name"""
        return self.services.get(service_name)

    def get_mode_config(self, mode_name: str) -> Optional[LaunchMode]:
        """Get launch mode configuration by name"""
        return self.launch_modes.get(mode_name)

    def get_launch_modes(self) -> List[str]:
        """Get list of available launch mode names"""
        return sorted(self.launch_modes.keys(), key=lambda x: self.launch_modes[x].priority, reverse=True)

    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        return self.global_config.copy()

    def save_configurations(self) -> bool:
        """Save current configurations to files"""
        try:
            # Save services configuration
            services_data = [
                {
                    "name": service.name,
                    "display_name": service.display_name,
                    "type": service.type.value,
                    "description": service.description,
                    "command": service.command,
                    "working_dir": service.working_dir,
                    "env_vars": service.env_vars,
                    "ports": [
                        {
                            "number": port.number,
                            "name": port.name,
                            "required": port.required,
                            "check_health": port.check_health,
                            "health_endpoint": port.health_endpoint
                        }
                        for port in service.ports
                    ],
                    "dependencies": service.dependencies,
                    "health_check": service.health_check,
                    "startup_timeout": service.startup_timeout,
                    "auto_restart": service.auto_restart,
                    "log_file": service.log_file,
                    "enabled": service.enabled
                }
                for service in self.services.values()
                if service.enabled
            ]

            with open(self.config_dir / "services.json", 'w', encoding='utf-8') as f:
                json.dump(services_data, f, indent=2)

            # Save launch modes configuration
            modes_data = [
                {
                    "name": mode.name,
                    "display_name": mode.display_name,
                    "description": mode.description,
                    "services": mode.services,
                    "env_vars": mode.env_vars,
                    "pre_launch": mode.pre_launch,
                    "post_launch": mode.post_launch,
                    "priority": mode.priority,
                    "icon": mode.icon
                }
                for mode in self.launch_modes.values()
            ]

            with open(self.config_dir / "launch_modes.json", 'w', encoding='utf-8') as f:
                json.dump(modes_data, f, indent=2)

            self.logger.info("Configurations saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configurations: {e}")
            return False
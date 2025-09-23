#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Unified Configuration System
Consolidates all configuration management into a single system
Replaces multiple JSON and YAML files with a centralized configuration manager
"""

import json
import yaml
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIProviderConfig:
    """Configuration for AI providers"""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    enabled: bool = True

@dataclass
class IntegrationConfig:
    """Configuration for integrations"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = None

@dataclass
class WebUIConfig:
    """Configuration for WebUI"""
    host: str = "127.0.0.1"
    port: int = 8787
    theme: str = "Soft"
    interface_mode: str = "classic"
    enable_websocket: bool = True
    enable_file_upload: bool = True
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    # Qwen3-Omni-UI Configuration
    qwen3_omni_ui_enabled: bool = True
    qwen3_omni_ui_host: str = "127.0.0.1"
    qwen3_omni_ui_port: int = 8788
    qwen3_omni_ws_port: int = 8796
    qwen3_omni_ws_path: str = "/ws"
    qwen3_omni_ui_debug: bool = False
    qwen3_omni_ui_max_concurrent: int = 50

@dataclass
class SystemConfig:
    """System-wide configuration"""
    log_level: str = "INFO"
    log_directory: str = "logs"
    temp_directory: str = "temp"
    enable_monitoring: bool = True
    monitoring_port: int = 8789
    enable_auto_update: bool = False
    max_memory_usage: int = 4 * 1024 * 1024 * 1024  # 4GB

@dataclass
class DuckBotConfig:
    """Main DuckBot configuration"""
    version: str = "4.2"
    ai_providers: Dict[str, AIProviderConfig] = None
    integrations: Dict[str, IntegrationConfig] = None
    webui: WebUIConfig = None
    system: SystemConfig = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.ai_providers is None:
            self.ai_providers = {}
        if self.integrations is None:
            self.integrations = {}
        if self.webui is None:
            self.webui = WebUIConfig()
        if self.system is None:
            self.system = SystemConfig()
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

class ConfigManager:
    """Unified configuration manager for DuckBot"""

    def __init__(self, config_path: str = "config/unified_config.json"):
        self.config_path = Path(config_path)
        self.config: DuckBotConfig = None
        self.ensure_config_directory()

    def ensure_config_directory(self):
        """Ensure configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> DuckBotConfig:
        """Load configuration from file"""
        if not self.config_path.exists():
            logger.info("No configuration file found, creating default")
            self.config = DuckBotConfig()
            self.save_config()
            return self.config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert to dataclass
            self.config = DuckBotConfig(
                version=data.get('version', '4.2'),
                created_at=data.get('created_at'),
                updated_at=datetime.now().isoformat()
            )

            # Load AI providers
            if 'ai_providers' in data:
                for name, provider_data in data['ai_providers'].items():
                    self.config.ai_providers[name] = AIProviderConfig(**provider_data)

            # Load integrations
            if 'integrations' in data:
                for name, integration_data in data['integrations'].items():
                    self.config.integrations[name] = IntegrationConfig(**integration_data)

            # Load WebUI config
            if 'webui' in data:
                self.config.webui = WebUIConfig(**data['webui'])

            # Load system config
            if 'system' in data:
                self.config.system = SystemConfig(**data['system'])

            logger.info(f"Loaded configuration from {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Creating default configuration")
            self.config = DuckBotConfig()
            self.save_config()
            return self.config

    def save_config(self):
        """Save configuration to file"""
        try:
            self.config.updated_at = datetime.now().isoformat()
            config_dict = asdict(self.config)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def migrate_legacy_configs(self):
        """Migrate configuration from legacy files"""
        legacy_files = [
            "ai_config.json",
            "enhanced_config.json",
            "provider_config.json",
            "hardware_config.json",
            "ecosystem_config.yaml",
            "livekit_config.yaml"
        ]

        migrated = []

        for filename in legacy_files:
            filepath = Path(filename)
            if filepath.exists():
                try:
                    if filename.endswith('.json'):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)

                    self._migrate_config_data(filename, data)
                    migrated.append(filename)

                    # Archive old file
                    archive_path = Path("config/archived") / filename
                    archive_path.parent.mkdir(exist_ok=True)
                    filepath.rename(archive_path)

                except Exception as e:
                    logger.error(f"Failed to migrate {filename}: {e}")

        if migrated:
            logger.info(f"Migrated {len(migrated)} legacy configuration files")
            self.save_config()

    def _migrate_config_data(self, filename: str, data: Dict[str, Any]):
        """Migrate data from legacy configuration file"""
        if filename == "ai_config.json":
            # Migrate AI providers
            for provider_name, provider_data in data.items():
                if isinstance(provider_data, dict):
                    self.config.ai_providers[provider_name] = AIProviderConfig(
                        name=provider_name,
                        **provider_data
                    )

        elif filename == "enhanced_config.json":
            # Migrate general settings
            if 'webui' in data:
                self.config.webui = WebUIConfig(**data['webui'])

        elif filename == "provider_config.json":
            # Migrate provider settings
            if 'providers' in data:
                for provider_name, provider_data in data['providers'].items():
                    self.config.ai_providers[provider_name] = AIProviderConfig(
                        name=provider_name,
                        **provider_data
                    )

        elif filename == "hardware_config.json":
            # Migrate to system config
            if 'system' in data:
                self.config.system = SystemConfig(**data['system'])

        elif filename == "ecosystem_config.yaml":
            # Migrate ecosystem settings
            if 'integrations' in data:
                for int_name, int_data in data['integrations'].items():
                    self.config.integrations[int_name] = IntegrationConfig(
                        name=int_name,
                        enabled=int_data.get('enabled', True),
                        config=int_data.get('config', {})
                    )

    def get_ai_provider(self, name: str) -> Optional[AIProviderConfig]:
        """Get AI provider configuration"""
        return self.config.ai_providers.get(name)

    def set_ai_provider(self, name: str, config: AIProviderConfig):
        """Set AI provider configuration"""
        self.config.ai_providers[name] = config
        self.save_config()

    def get_integration(self, name: str) -> Optional[IntegrationConfig]:
        """Get integration configuration"""
        return self.config.integrations.get(name)

    def set_integration(self, name: str, config: IntegrationConfig):
        """Set integration configuration"""
        self.config.integrations[name] = config
        self.save_config()

    def get_webui_config(self) -> WebUIConfig:
        """Get WebUI configuration"""
        return self.config.webui

    def set_webui_config(self, config: WebUIConfig):
        """Set WebUI configuration"""
        self.config.webui = config
        self.save_config()

    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        return self.config.system

    def set_system_config(self, config: SystemConfig):
        """Set system configuration"""
        self.config.system = config
        self.save_config()

    def export_config(self, format: str = 'json') -> str:
        """Export configuration as string"""
        if format.lower() == 'json':
            return json.dumps(asdict(self.config), indent=2, ensure_ascii=False)
        elif format.lower() == 'yaml':
            return yaml.dump(asdict(self.config), default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_config(self, config_str: str, format: str = 'json'):
        """Import configuration from string"""
        if format.lower() == 'json':
            data = json.loads(config_str)
        elif format.lower() == 'yaml':
            data = yaml.safe_load(config_str)
        else:
            raise ValueError(f"Unsupported import format: {format}")

        # Update configuration
        self.config = DuckBotConfig(**data)
        self.save_config()

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = DuckBotConfig()
        self.save_config()

    def backup_config(self) -> Path:
        """Create backup of current configuration"""
        backup_path = self.config_path.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration backed up to {backup_path}")
        return backup_path

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate required fields
        if not self.config.version:
            errors.append("Version is required")

        # Validate AI providers
        for name, provider in self.config.ai_providers.items():
            if provider.enabled and not provider.api_key:
                errors.append(f"API key required for enabled provider: {name}")

        # Validate ports
        if not (1 <= self.config.webui.port <= 65535):
            errors.append(f"Invalid WebUI port: {self.config.webui.port}")

        if not (1 <= self.config.system.monitoring_port <= 65535):
            errors.append(f"Invalid monitoring port: {self.config.system.monitoring_port}")

        return errors

# Global configuration instance
_config_manager = None

def get_config_manager(config_path: str = None) -> ConfigManager:
    """Get or create the global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path or "config/unified_config.json")
    return _config_manager

def get_config() -> DuckBotConfig:
    """Get the current configuration"""
    return get_config_manager().load_config()

def save_config():
    """Save the current configuration"""
    get_config_manager().save_config()

# Convenience functions
def get_ai_provider(name: str) -> Optional[AIProviderConfig]:
    """Get AI provider configuration"""
    return get_config_manager().get_ai_provider(name)

def get_integration(name: str) -> Optional[IntegrationConfig]:
    """Get integration configuration"""
    return get_config_manager().get_integration(name)

def get_webui_config() -> WebUIConfig:
    """Get WebUI configuration"""
    return get_config_manager().get_webui_config()

def get_system_config() -> SystemConfig:
    """Get system configuration"""
    return get_config_manager().get_system_config()

# Initialize default configuration on first import
if __name__ != "__main__":
    # Load configuration when module is imported
    try:
        get_config()
    except Exception as e:
        logger.warning(f"Failed to load initial configuration: {e}")
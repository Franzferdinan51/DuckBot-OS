"""
DuckBot Configuration Module
Unified configuration management system
"""

from .unified_config import (
    ConfigManager, DuckBotConfig, AIProviderConfig, IntegrationConfig,
    WebUIConfig, SystemConfig, get_config_manager, get_config,
    save_config, get_ai_provider, get_integration, get_webui_config,
    get_system_config
)

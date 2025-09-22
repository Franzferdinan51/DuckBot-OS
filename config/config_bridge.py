"""
DuckBot Configuration Bridge for Electron Launcher
Provides a bridge between the new centralized configuration system and the Electron launcher
"""

import json
import yaml
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import DuckBotConfigManager, get_config_manager, Environment
from config.unified_config import ConfigManager as UnifiedConfigManager

@dataclass
class ElectronLauncherConfig:
    """Electron-specific configuration derived from the main config"""

    # System settings
    debug_mode: bool = False
    log_level: str = "INFO"

    # Connection settings
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8789
    webui_port: int = 8787
    ai_router_port: int = 8790

    # Feature flags
    enable_ai_assistant: bool = True
    enable_notifications: bool = True
    enable_auto_reconnect: bool = True
    enable_auto_start_mcp: bool = True

    # UI settings
    theme: str = "dark"
    font_size: int = 14
    chat_position: str = "right"
    show_system_info: bool = True
    compact_mode: bool = False

    # Performance settings
    max_concurrent_services: int = 5
    service_timeout: int = 30
    health_check_interval: int = 30

    # Derived startup modes
    startup_modes: Dict[str, Dict[str, Any]] = None

class ConfigBridge:
    """Bridge between centralized configuration and Electron launcher"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration bridge"""
        self.logger = self._setup_logger()

        # Initialize configuration managers
        try:
            self.config_manager = get_config_manager(config_path)
            self.unified_manager = UnifiedConfigManager()

            # Load configurations
            self.duckbot_config = self.config_manager.config_data
            self.unified_config = self.unified_manager.load_config()

            self.logger.info("Configuration bridge initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration bridge: {e}")
            # Use defaults if configuration loading fails
            self.duckbot_config = {}
            self.unified_config = None

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for configuration bridge"""
        logger = logging.getLogger("DuckBot.ConfigBridge")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def get_electron_config(self) -> ElectronLauncherConfig:
        """Get Electron-specific configuration"""

        # Extract system settings
        system_config = self.duckbot_config.get('system', {})
        features = self.duckbot_config.get('features', {})
        network = self.duckbot_config.get('network', {})
        hardware = self.duckbot_config.get('hardware', {})

        # Get service configurations
        services = self.duckbot_config.get('services', {})

        # Extract port configurations
        webui_config = services.get('webui', {})
        monitoring_config = services.get('monitoring', {})
        ai_router_config = services.get('ai_router', {})

        # Build Electron configuration
        electron_config = ElectronLauncherConfig(
            debug_mode=system_config.get('debug_mode', False),
            log_level=system_config.get('log_level', 'INFO'),

            # Connection settings
            mcp_host=network.get('default_host', '127.0.0.1'),
            mcp_port=monitoring_config.get('default_port', 8789),
            webui_port=webui_config.get('default_port', 8787),
            ai_router_port=ai_router_config.get('default_port', 8790),

            # Feature flags
            enable_ai_assistant=features.get('ai_routing_enabled', True),
            enable_notifications=features.get('monitoring_enabled', True),
            enable_auto_reconnect=True,  # Always enable for better UX
            enable_auto_start_mcp=True,  # Always enable for better UX

            # Performance settings
            max_concurrent_services=hardware.get('max_concurrent_services', 5),
            service_timeout=30,
            health_check_interval=system_config.get('monitoring_interval', 30),

            # Derived startup modes
            startup_modes=self._build_startup_modes()
        )

        return electron_config

    def _build_startup_modes(self) -> Dict[str, Dict[str, Any]]:
        """Build startup modes configuration from centralized config"""

        services = self.duckbot_config.get('services', {})
        features = self.duckbot_config.get('features', {})
        ai_providers = self.duckbot_config.get('ai_providers', {})

        # Determine available services and their status
        startup_modes = {}

        # Ultimate Complete Mode
        startup_modes['ultimate'] = {
            'name': 'Ultimate Complete Mode',
            'description': 'Complete AI integration with all features',
            'icon': '🚀',
            'category': 'complete',
            'requires': self._get_enabled_provider_names(),
            'command': 'python start_ecosystem.py',
            'ports': self._get_service_ports(['webui', 'monitoring', 'ai_router']),
            'enabled': features.get('webui_enabled', True) and features.get('monitoring_enabled', True)
        }

        # Enhanced WebUI Mode
        if services.get('webui', {}).get('enabled', True):
            startup_modes['enhanced-webui'] = {
                'name': 'Enhanced WebUI',
                'description': 'Modern web interface with AI features',
                'icon': '🌐',
                'category': 'web',
                'requires': ['openrouter'] if ai_providers.get('openrouter', {}).get('enabled', False) else [],
                'command': f'python duckbot/enhanced_webui.py --port {services.get("webui", {}).get("default_port", 8787)}',
                'ports': [services.get('webui', {}).get('default_port', 8787)],
                'enabled': features.get('webui_enabled', True)
            }

        # System Monitoring Mode
        if services.get('monitoring', {}).get('enabled', True):
            startup_modes['monitoring'] = {
                'name': 'System Monitoring',
                'description': 'Real-time system metrics and performance',
                'icon': '📊',
                'category': 'monitoring',
                'requires': [],
                'command': f'python ai_ecosystem_manager.py --port {services.get("monitoring", {}).get("default_port", 8789)}',
                'ports': [services.get('monitoring', {}).get('default_port', 8789)],
                'enabled': features.get('monitoring_enabled', True)
            }

        # Local-Only Privacy Mode
        if features.get('local_only_mode', False):
            startup_modes['local-only'] = {
                'name': 'Local-Only Privacy Mode',
                'description': 'Complete offline operation with LM Studio',
                'icon': '🔒',
                'category': 'privacy',
                'requires': [],
                'command': 'python start_local_ecosystem.py',
                'ports': [services.get('webui', {}).get('default_port', 8787)],
                'enabled': features.get('local_only_mode', False)
            }

        # ByteBot Desktop Automation
        if features.get('desktop_automation_enabled', True):
            startup_modes['bytebot'] = {
                'name': 'ByteBot Desktop Automation',
                'description': 'Complete computer control with AI',
                'icon': '🤖',
                'category': 'automation',
                'requires': ['gemini'] if ai_providers.get('openrouter', {}).get('enabled', False) else [],
                'command': 'python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"',
                'ports': [],
                'enabled': features.get('desktop_automation_enabled', True)
            }

        # AI Router System
        if services.get('ai_router', {}).get('enabled', True) and features.get('ai_routing_enabled', True):
            startup_modes['ai-router'] = {
                'name': 'AI Router System',
                'description': 'Intelligent AI model selection',
                'icon': '🔀',
                'category': 'ai',
                'requires': self._get_enabled_provider_names(),
                'command': f'python duckbot/ai_router_gpt.py --port {services.get("ai_router", {}).get("default_port", 8790)}',
                'ports': [services.get('ai_router', {}).get('default_port', 8790)],
                'enabled': features.get('ai_routing_enabled', True)
            }

        # Add more modes based on available services and features
        if services.get('vibevoice', {}).get('enabled', True) and features.get('voice_enabled', True):
            startup_modes['vibevoice'] = {
                'name': 'Microsoft VibeVoice TTS',
                'description': 'Text-to-speech with Microsoft VibeVoice',
                'icon': '🎤',
                'category': 'voice',
                'requires': [],
                'command': 'python duckbot/vibevoice_integration.py',
                'ports': [],
                'enabled': features.get('voice_enabled', True)
            }

        # Model Training Module
        startup_modes['model_training'] = {
            'name': 'Model Training Studio',
            'description': 'Train and fine-tune AI models with GGUF and Hugging Face support',
            'icon': '🤖',
            'category': 'ai',
            'requires': [],
            'command': 'python launcher-modules/model-training/model_trainer.py',
            'ports': [],
            'enabled': True
        }

        # Discord Bot Mode
        startup_modes['discord-bot'] = {
            'name': 'Discord Bot with VibeVoice',
            'description': 'Discord integration with voice capabilities',
            'icon': '🎮',
            'category': 'communication',
            'requires': [],
            'command': 'python duckbot/discord_bot.py',
            'ports': [],
            'enabled': True
        }

        return startup_modes

    def _get_enabled_provider_names(self) -> List[str]:
        """Get list of enabled AI provider names"""
        providers = []
        ai_providers = self.duckbot_config.get('ai_providers', {})

        for name, config in ai_providers.items():
            if config.get('enabled', False):
                # Map internal names to display names
                if name == 'openrouter':
                    providers.append('openrouter')
                elif name == 'lm_studio':
                    providers.append('lm_studio')
                elif name == 'openai':
                    providers.append('openai')
                elif name == 'anthropic':
                    providers.append('anthropic')

        return providers

    def _get_service_ports(self, service_names: List[str]) -> List[int]:
        """Get ports for specified services"""
        ports = []
        services = self.duckbot_config.get('services', {})

        for service_name in service_names:
            service = services.get(service_name)
            if service:
                port = service.get('default_port')
                if port:
                    ports.append(port)

        return ports

    def get_api_keys_status(self) -> Dict[str, bool]:
        """Get status of API keys from unified configuration"""
        if not self.unified_config:
            return {
                'gemini': False,
                'openrouter': False,
                'zai': False,
                'zai_coding_plan': False
            }

        ai_providers = self.unified_config.ai_providers
        return {
            'gemini': bool(ai_providers.get('gemini', {}).get('api_key')),
            'openrouter': bool(ai_providers.get('openrouter', {}).get('api_key')),
            'zai': bool(ai_providers.get('zai', {}).get('api_key')),
            'zai_coding_plan': bool(ai_providers.get('zai', {}).get('api_key'))
        }

    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service"""
        service = self.config_manager.get_service_config(service_name)
        if not service:
            return None

        return {
            'name': service.name,
            'enabled': service.enabled,
            'host': service.default_host,
            'port': service.default_port,
            'health_endpoint': service.health_endpoint,
            'environment_vars': service.environment_vars,
            'status': service.status.value if service.status else 'unknown'
        }

    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        services = {}
        for service_name, service_config in self.config_manager.get_all_services().items():
            services[service_name] = self.get_service_config(service_name)

        return services

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        features = self.duckbot_config.get('features', {})
        return {
            'webui_enabled': features.get('webui_enabled', True),
            'monitoring_enabled': features.get('monitoring_enabled', True),
            'ai_routing_enabled': features.get('ai_routing_enabled', True),
            'local_ai_enabled': features.get('local_ai_enabled', True),
            'cloud_ai_enabled': features.get('cloud_ai_enabled', True),
            'desktop_automation_enabled': features.get('desktop_automation_enabled', True),
            'voice_enabled': features.get('voice_enabled', True),
            'local_only_mode': features.get('local_only_mode', False),
            'debug_mode': features.get('debug_mode', False)
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information from configuration"""
        system = self.duckbot_config.get('system', {})
        hardware = self.duckbot_config.get('hardware', {})

        return {
            'name': system.get('name', 'DuckBot Enhanced'),
            'version': system.get('version', '4.2'),
            'build_date': system.get('build_date', '2025-09-16'),
            'environment': self.config_manager.environment.value,
            'debug_mode': system.get('debug_mode', False),
            'log_level': system.get('log_level', 'INFO'),

            # Hardware requirements
            'min_ram_gb': hardware.get('min_ram_gb', 4),
            'recommended_ram_gb': hardware.get('recommended_ram_gb', 8),
            'gpu_enabled': hardware.get('gpu_enabled', True),
            'max_concurrent_services': hardware.get('max_concurrent_services', 10)
        }

    def export_for_electron(self) -> Dict[str, Any]:
        """Export all configuration in Electron-friendly format"""
        return {
            'electron_config': asdict(self.get_electron_config()),
            'api_keys_status': self.get_api_keys_status(),
            'services_status': self.get_all_services_status(),
            'feature_flags': self.get_feature_flags(),
            'system_info': self.get_system_info(),
            'config_path': str(self.config_manager.config_path)
        }

    def save_electron_config(self, output_path: str) -> None:
        """Save Electron-specific configuration to JSON file"""
        config_data = self.export_for_electron()

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Electron configuration saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save Electron configuration: {e}")
            raise

def get_config_bridge(config_path: Optional[str] = None) -> ConfigBridge:
    """Get global configuration bridge instance"""
    return ConfigBridge(config_path)

if __name__ == "__main__":
    # Test the configuration bridge
    bridge = get_config_bridge()
    electron_config = bridge.export_for_electron()

    print("Configuration Bridge Test")
    print("=" * 50)
    print(f"System: {electron_config['system_info']['name']} v{electron_config['system_info']['version']}")
    print(f"Environment: {electron_config['system_info']['environment']}")
    print(f"Enabled services: {len([s for s in electron_config['services_status'].values() if s['enabled']])}")
    print(f"Startup modes: {len(electron_config['electron_config']['startup_modes'])}")
    print(f"API keys configured: {sum(electron_config['api_keys_status'].values())}")

    # Save test configuration
    bridge.save_electron_config("config/electron_config.json")
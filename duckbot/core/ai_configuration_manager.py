#!/usr/bin/env python3
"""
AI Configuration Manager for DuckBot
Handles loading, validation, and management of AI provider configurations
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict, field
from dataclasses_json import dataclass_json
import yaml

logger = logging.getLogger(__name__)

@dataclass_json
@dataclass
class ProviderConfig:
    """Configuration for a single AI provider"""
    name: str
    enabled: bool = True
    url: str = ""
    default_model: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 60
    retry_attempts: int = 3
    type: str = "cloud"  # "local", "cloud", "internal", "tts"
    api_key_required: bool = False
    api_key_env: str = ""
    cost_per_1k_tokens: float = 0.0
    models: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass_json
@dataclass
class SystemConfig:
    """System-wide AI configuration"""
    default_provider: str = "lm_studio"
    fallback_chain: List[str] = field(default_factory=lambda: ["lm_studio", "openrouter", "gemini", "duckbot"])
    max_tokens: int = 512
    temperature: float = 0.2
    conversation_history_limit: int = 50
    decision_confidence_threshold: float = 0.7
    auto_action_enabled: bool = False
    enable_smart_routing: bool = True
    enable_cost_awareness: bool = True
    enable_local_only_mode: bool = False
    monitoring_interval: int = 30
    report_interval: int = 300
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

@dataclass_json
@dataclass
class RoutingConfig:
    """AI routing strategy configuration"""
    type: str = "smart"  # "smart", "round_robin", "priority", "cost_optimized"
    priority_order: List[str] = field(default_factory=lambda: ["lm_studio", "openrouter", "gemini", "duckbot"])
    cost_threshold: float = 0.01
    performance_threshold: float = 0.8
    reliability_weight: float = 0.3
    cost_weight: float = 0.4
    performance_weight: float = 0.3

@dataclass_json
@dataclass
class FallbackConfig:
    """Fallback mechanism configuration"""
    enabled: bool = True
    max_fallback_attempts: int = 3
    fallback_delay_ms: int = 1000
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_ms: int = 30000

class AIConfigurationManager:
    """Manages AI provider configurations and settings"""

    def __init__(self, config_path: str = None, env_path: str = None):
        self.config_path = config_path or str(Path(__file__).parent.parent / "config" / "ai_config.json")
        self.env_path = env_path or str(Path(__file__).parent.parent / ".env")

        # Load configurations
        self.providers: Dict[str, ProviderConfig] = {}
        self.system_config = SystemConfig()
        self.routing_config = RoutingConfig()
        self.fallback_config = FallbackConfig()

        self._load_configurations()
        self._load_environment_variables()
        self._validate_configurations()

    def _load_configurations(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Load providers
            for provider_name, provider_data in config_data.get("providers", {}).items():
                provider_config = ProviderConfig(
                    name=provider_name,
                    **provider_data
                )
                self.providers[provider_name] = provider_config

            # Load system config
            if "system_settings" in config_data:
                self.system_config = SystemConfig(**config_data["system_settings"])

            # Load routing config
            if "routing_strategy" in config_data:
                self.routing_config = RoutingConfig(**config_data["routing_strategy"])

            # Load fallback config
            if "fallback_config" in config_data:
                self.fallback_config = FallbackConfig(**config_data["fallback_config"])

            logger.info(f"Loaded {len(self.providers)} AI providers from configuration")

        except Exception as e:
            logger.error(f"Error loading AI configuration: {e}")
            self._load_default_config()

    def _load_default_config(self):
        """Load default configuration when file is missing"""
        self.providers = {
            "lm_studio": ProviderConfig(
                name="lm_studio",
                url="http://localhost:1234/v1",
                default_model="qwen3-30b-a3b-thinking-2507-deepseek-v3.1-distill",
                type="local",
                api_key_required=False
            ),
            "openrouter": ProviderConfig(
                name="openrouter",
                url="https://openrouter.ai/api/v1",
                default_model="qwen/qwen3-coder:free",
                type="cloud",
                api_key_required=True,
                api_key_env="OPENROUTER_API_KEY"
            )
        }
        logger.warning("Loaded default AI configuration")

    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_mappings = {
            "DEFAULT_AI_PROVIDER": ("system_config", "default_provider"),
            "AI_LOCAL_ONLY_MODE": ("system_config", "enable_local_only_mode"),
            "AI_MAX_TOKENS": ("system_config", "max_tokens"),
            "AI_TEMPERATURE": ("system_config", "temperature"),
            "AI_ENABLE_SMART_ROUTING": ("system_config", "enable_smart_routing"),
            "AI_ENABLE_COST_AWARENESS": ("system_config", "enable_cost_awareness"),
            "AI_ROUTING_TYPE": ("routing_config", "type"),
            "AI_MAX_FALLBACK_ATTEMPTS": ("fallback_config", "max_fallback_attempts"),
            "AI_ENABLE_CIRCUIT_BREAKER": ("fallback_config", "enable_circuit_breaker"),
        }

        for env_var, (config_obj, config_key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string to appropriate type
                if isinstance(getattr(self, config_obj).__class__.__annotations__[config_key], bool):
                    value = value.lower() in ['true', '1', 'yes', 'on']
                elif isinstance(getattr(self, config_obj).__class__.__annotations__[config_key], int):
                    value = int(value)
                elif isinstance(getattr(self, config_obj).__class__.__annotations__[config_key], float):
                    value = float(value)

                setattr(getattr(self, config_obj), config_key, value)

        # Load provider-specific environment variables
        for provider_name, provider_config in self.providers.items():
            # Check if provider is enabled via environment
            env_enabled = os.getenv(f"{provider_name.upper()}_ENABLED")
            if env_enabled is not None:
                provider_config.enabled = env_enabled.lower() in ['true', '1', 'yes', 'on']

            # Load API key
            if provider_config.api_key_required and provider_config.api_key_env:
                api_key = os.getenv(provider_config.api_key_env)
                if api_key:
                    provider_config.api_key = api_key

            # Load provider URL
            env_url = os.getenv(f"{provider_name.upper()}_URL")
            if env_url:
                provider_config.url = env_url

            # Load default model
            env_model = os.getenv(f"{provider_name.upper()}_MODEL")
            if env_model:
                provider_config.default_model = env_model

    def _validate_configurations(self):
        """Validate loaded configurations"""
        errors = []

        # Validate default provider exists
        if self.system_config.default_provider not in self.providers:
            errors.append(f"Default provider '{self.system_config.default_provider}' not found")

        # Validate providers
        for provider_name, provider_config in self.providers.items():
            if provider_config.enabled:
                # Check API key requirement
                if provider_config.api_key_required and not hasattr(provider_config, 'api_key'):
                    errors.append(f"Provider '{provider_name}' requires API key but none provided")

                # Check URL
                if not provider_config.url:
                    errors.append(f"Provider '{provider_name}' has no URL configured")

                # Check default model
                if not provider_config.default_model:
                    errors.append(f"Provider '{provider_name}' has no default model configured")

        # Validate fallback chain
        for provider in self.system_config.fallback_chain:
            if provider not in self.providers:
                errors.append(f"Fallback provider '{provider}' not found")

        if errors:
            logger.warning(f"Configuration validation errors: {errors}")
            # Disable problematic providers
            for error in errors:
                if "requires API key" in error:
                    provider_name = error.split("'")[1]
                    if provider_name in self.providers:
                        self.providers[provider_name].enabled = False
                        logger.warning(f"Disabled provider '{provider_name}' due to missing API key")

    def get_provider(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get provider configuration by name"""
        return self.providers.get(provider_name)

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled providers"""
        return [name for name, config in self.providers.items() if config.enabled]

    def get_provider_for_task(self, task_type: str, requirements: Dict[str, Any] = None) -> str:
        """Select the best provider for a given task"""
        if self.system_config.enable_local_only_mode:
            # Prefer local providers in local-only mode
            local_providers = [name for name in self.get_enabled_providers()
                             if self.providers[name].type == "local"]
            if local_providers:
                return local_providers[0]

        if self.routing_config.type == "priority":
            return self._select_by_priority(task_type, requirements)
        elif self.routing_config.type == "cost_optimized":
            return self._select_by_cost(task_type, requirements)
        elif self.routing_config.type == "round_robin":
            return self._select_by_round_robin(task_type, requirements)
        else:  # smart routing
            return self._select_smart(task_type, requirements)

    def _select_by_priority(self, task_type: str, requirements: Dict[str, Any] = None) -> str:
        """Select provider based on priority order"""
        for provider_name in self.routing_config.priority_order:
            provider_config = self.providers.get(provider_name)
            if provider_config and provider_config.enabled:
                if self._check_provider_suitable(provider_config, task_type, requirements):
                    return provider_name
        return self.system_config.default_provider

    def _select_by_cost(self, task_type: str, requirements: Dict[str, Any] = None) -> str:
        """Select provider based on cost optimization"""
        suitable_providers = []
        for provider_name, provider_config in self.providers.items():
            if provider_config.enabled and self._check_provider_suitable(provider_config, task_type, requirements):
                suitable_providers.append((provider_name, provider_config.cost_per_1k_tokens))

        if suitable_providers:
            # Sort by cost and return the cheapest
            suitable_providers.sort(key=lambda x: x[1])
            return suitable_providers[0][0]

        return self.system_config.default_provider

    def _select_by_round_robin(self, task_type: str, requirements: Dict[str, Any] = None) -> str:
        """Select provider using round-robin algorithm"""
        # Simple round-robin implementation
        enabled_providers = self.get_enabled_providers()
        if enabled_providers:
            # Use task type as a simple hash for selection
            index = hash(task_type) % len(enabled_providers)
            return enabled_providers[index]
        return self.system_config.default_provider

    def _select_smart(self, task_type: str, requirements: Dict[str, Any] = None) -> str:
        """Smart provider selection considering multiple factors"""
        scores = {}

        for provider_name, provider_config in self.providers.items():
            if not provider_config.enabled:
                continue

            score = 0.0

            # Performance score based on model capabilities
            if task_type in provider_config.models:
                model_info = provider_config.models[provider_config.default_model]
                score += model_info.get("performance_score", 50)

            # Cost factor (lower cost = higher score)
            cost_score = max(0, 100 - (provider_config.cost_per_1k_tokens * 10000))
            score += cost_score * self.routing_config.cost_weight

            # Provider type preference
            type_preference = {"local": 30, "internal": 25, "cloud": 20, "tts": 15}
            score += type_preference.get(provider_config.type, 10)

            # Apply weights
            score = (score * self.routing_config.performance_weight +
                    cost_score * self.routing_config.cost_weight)

            scores[provider_name] = score

        if scores:
            # Return provider with highest score
            return max(scores, key=scores.get)

        return self.system_config.default_provider

    def _check_provider_suitable(self, provider_config: ProviderConfig, task_type: str, requirements: Dict[str, Any] = None) -> bool:
        """Check if provider is suitable for the given task"""
        if not provider_config.enabled:
            return False

        # Check task type compatibility
        if task_type in ["text_to_speech", "voice_synthesis"]:
            return provider_config.type == "tts"

        return True

    def get_fallback_providers(self, current_provider: str) -> List[str]:
        """Get list of fallback providers in order"""
        if current_provider in self.system_config.fallback_chain:
            index = self.system_config.fallback_chain.index(current_provider)
            return self.system_config.fallback_chain[index + 1:]
        return self.system_config.fallback_chain

    def update_provider_config(self, provider_name: str, **kwargs):
        """Update provider configuration"""
        if provider_name in self.providers:
            provider_config = self.providers[provider_name]
            for key, value in kwargs.items():
                if hasattr(provider_config, key):
                    setattr(provider_config, key, value)

    def save_configuration(self, path: str = None):
        """Save current configuration to file"""
        if path is None:
            path = self.config_path

        config_data = {
            "default_provider": self.system_config.default_provider,
            "fallback_chain": self.system_config.fallback_chain,
            "providers": {name: asdict(config) for name, config in self.providers.items()},
            "system_settings": asdict(self.system_config),
            "routing_strategy": asdict(self.routing_config),
            "fallback_config": asdict(self.fallback_config)
        }

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            "default_provider": self.system_config.default_provider,
            "enabled_providers": self.get_enabled_providers(),
            "total_providers": len(self.providers),
            "local_only_mode": self.system_config.enable_local_only_mode,
            "smart_routing": self.system_config.enable_smart_routing,
            "cost_awareness": self.system_config.enable_cost_awareness,
            "routing_type": self.routing_config.type
        }

# Global instance
ai_config_manager = AIConfigurationManager()

# Convenience functions
def get_provider_config(provider_name: str) -> Optional[ProviderConfig]:
    """Get provider configuration"""
    return ai_config_manager.get_provider(provider_name)

def get_enabled_providers() -> List[str]:
    """Get list of enabled providers"""
    return ai_config_manager.get_enabled_providers()

def select_provider_for_task(task_type: str, requirements: Dict[str, Any] = None) -> str:
    """Select best provider for task"""
    return ai_config_manager.get_provider_for_task(task_type, requirements)

if __name__ == "__main__":
    # Test configuration manager
    logging.basicConfig(level=logging.INFO)
    config = AIConfigurationManager()
    print("Configuration Summary:")
    print(json.dumps(config.get_configuration_summary(), indent=2))
#!/usr/bin/env python3
"""
AI Configuration Validation and Management Utility
Validates AI provider configurations and provides management functions
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

# Import the configuration manager
try:
    from ..core.ai_configuration_manager import AIConfigurationManager, ProviderConfig
    from ..core.ai_provider_manager import AIProviderManager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: AI configuration modules not available")

# Import cost management
try:
    from ..core.cost_management import CostTracker
    COST_AVAILABLE = True
except ImportError:
    COST_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Configuration validation result"""
    is_valid: bool = True
    errors: List[str] = None
    warnings: List[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.recommendations is None:
            self.recommendations = []

class AIConfigValidator:
    """Validates and manages AI provider configurations"""

    def __init__(self):
        self.config_manager = AIConfigurationManager() if CONFIG_AVAILABLE else None
        self.cost_tracker = CostTracker() if COST_AVAILABLE else None

    def validate_configuration(self) -> ValidationResult:
        """Validate the entire AI configuration"""
        result = ValidationResult()

        if not self.config_manager:
            result.is_valid = False
            result.errors.append("Configuration manager not available")
            return result

        # Validate provider configurations
        for provider_name, provider_config in self.config_manager.providers.items():
            provider_result = self.validate_provider(provider_name, provider_config)
            result.errors.extend(provider_result.errors)
            result.warnings.extend(provider_result.warnings)
            result.recommendations.extend(provider_result.recommendations)

        # Validate system settings
        system_result = self.validate_system_settings()
        result.errors.extend(system_result.errors)
        result.warnings.extend(system_result.warnings)
        result.recommendations.extend(system_result.recommendations)

        # Validate environment variables
        env_result = self.validate_environment_variables()
        result.errors.extend(env_result.errors)
        result.warnings.extend(env_result.warnings)
        result.recommendations.extend(env_result.recommendations)

        result.is_valid = len(result.errors) == 0
        return result

    def validate_provider(self, provider_name: str, provider_config: ProviderConfig) -> ValidationResult:
        """Validate a specific provider configuration"""
        result = ValidationResult()

        # Check required fields
        if not provider_config.url:
            result.errors.append(f"Provider '{provider_name}' has no URL configured")

        if not provider_config.default_model:
            result.errors.append(f"Provider '{provider_name}' has no default model configured")

        # Check API key requirements
        if provider_config.api_key_required:
            if provider_config.api_key_env:
                api_key = os.getenv(provider_config.api_key_env)
                if not api_key:
                    result.errors.append(f"Provider '{provider_name}' requires API key '{provider_config.api_key_env}' but it's not set")
            else:
                result.warnings.append(f"Provider '{provider_name}' requires API key but no environment variable specified")

        # Check if provider is enabled but no models are configured
        if provider_config.enabled and not provider_config.models:
            result.warnings.append(f"Provider '{provider_name}' is enabled but has no models configured")

        # Check model configurations
        for model_name, model_config in provider_config.models.items():
            model_result = self.validate_model(provider_name, model_name, model_config)
            result.errors.extend(model_result.errors)
            result.warnings.extend(model_result.warnings)

        # Recommendations for optimization
        if provider_config.type == "cloud" and provider_config.cost_per_1k_tokens > 0.01:
            result.recommendations.append(f"Provider '{provider_name}' has high cost per 1K tokens - consider alternatives")

        if provider_config.type == "local" and not provider_config.url.startswith("http"):
            result.warnings.append(f"Provider '{provider_name}' is local but URL doesn't look valid")

        return result

    def validate_model(self, provider_name: str, model_name: str, model_config: Dict[str, Any]) -> ValidationResult:
        """Validate a specific model configuration"""
        result = ValidationResult()

        # Check required model fields
        if "name" not in model_config:
            result.errors.append(f"Model '{model_name}' for provider '{provider_name}' has no name")

        if "capabilities" not in model_config:
            result.warnings.append(f"Model '{model_name}' for provider '{provider_name}' has no capabilities defined")

        if "performance_score" not in model_config:
            result.warnings.append(f"Model '{model_name}' for provider '{provider_name}' has no performance score")

        # Check performance score range
        if "performance_score" in model_config:
            score = model_config["performance_score"]
            if not (0 <= score <= 100):
                result.warnings.append(f"Model '{model_name}' has invalid performance score: {score}")

        return result

    def validate_system_settings(self) -> ValidationResult:
        """Validate system-wide settings"""
        result = ValidationResult()

        if not self.config_manager:
            return result

        system_config = self.config_manager.system_config

        # Check default provider exists
        if system_config.default_provider not in self.config_manager.providers:
            result.errors.append(f"Default provider '{system_config.default_provider}' not found in configuration")

        # Check fallback chain
        for provider in system_config.fallback_chain:
            if provider not in self.config_manager.providers:
                result.warnings.append(f"Fallback provider '{provider}' not found in configuration")

        # Check local-only mode consistency
        if system_config.enable_local_only_mode:
            local_providers = [name for name, config in self.config_manager.providers.items()
                             if config.type == "local" and config.enabled]
            if not local_providers:
                result.warnings.append("Local-only mode enabled but no local providers are available")

        # Check confidence thresholds
        if not (0 <= system_config.decision_confidence_threshold <= 1):
            result.warnings.append(f"Decision confidence threshold should be between 0 and 1: {system_config.decision_confidence_threshold}")

        return result

    def validate_environment_variables(self) -> ValidationResult:
        """Validate environment variable configurations"""
        result = ValidationResult()

        # Check for API key environment variables
        required_env_vars = []
        if self.config_manager:
            for provider_name, provider_config in self.config_manager.providers.items():
                if provider_config.api_key_required and provider_config.api_key_env:
                    required_env_vars.append(provider_config.api_key_env)

        missing_env_vars = []
        for env_var in required_env_vars:
            if not os.getenv(env_var):
                missing_env_vars.append(env_var)

        if missing_env_vars:
            result.warnings.append(f"Missing required environment variables: {', '.join(missing_env_vars)}")

        # Check for common optional environment variables
        optional_env_vars = [
            "AI_LOCAL_ONLY_MODE",
            "DEFAULT_AI_PROVIDER",
            "AI_ENABLE_SMART_ROUTING",
            "AI_ENABLE_COST_AWARENESS"
        ]

        set_optional_vars = []
        for env_var in optional_env_vars:
            if os.getenv(env_var):
                set_optional_vars.append(env_var)

        if set_optional_vars:
            result.recommendations.append(f"Optional environment variables set: {', '.join(set_optional_vars)}")

        return result

    def generate_configuration_report(self) -> Dict[str, Any]:
        """Generate a comprehensive configuration report"""
        if not self.config_manager:
            return {"error": "Configuration manager not available"}

        report = {
            "summary": self.config_manager.get_configuration_summary(),
            "providers": {},
            "environment": {},
            "recommendations": [],
            "validation": asdict(self.validate_configuration())
        }

        # Add provider details
        for provider_name, provider_config in self.config_manager.providers.items():
            provider_info = {
                "enabled": provider_config.enabled,
                "type": provider_config.type,
                "api_key_required": provider_config.api_key_required,
                "has_api_key": bool(getattr(provider_config, 'api_key', None)),
                "default_model": provider_config.default_model,
                "url": provider_config.url,
                "cost_per_1k_tokens": provider_config.cost_per_1k_tokens,
                "models": list(provider_config.models.keys())
            }
            report["providers"][provider_name] = provider_info

        # Add environment variables
        env_vars_to_check = [
            "OPENROUTER_API_KEY",
            "GEMINI_API_KEY",
            "AI_LOCAL_ONLY_MODE",
            "DEFAULT_AI_PROVIDER",
            "AI_ENABLE_SMART_ROUTING",
            "AI_ENABLE_COST_AWARENESS"
        ]

        for env_var in env_vars_to_check:
            report["environment"][env_var] = os.getenv(env_var, "NOT_SET")

        # Add cost information if available
        if self.cost_tracker:
            try:
                summary = self.cost_tracker.get_usage_summary(30)
                report["cost_summary"] = {
                    "total_cost": summary.total_cost,
                    "total_tokens": summary.total_tokens,
                    "total_requests": summary.total_requests,
                    "by_provider": summary.by_provider,
                    "by_model": summary.by_model
                }
            except Exception as e:
                report["cost_summary"] = {"error": str(e)}

        return report

    def fix_configuration_issues(self, auto_fix: bool = False) -> List[str]:
        """Attempt to fix common configuration issues"""
        fixes_applied = []

        if not self.config_manager:
            fixes_applied.append("Cannot fix issues: Configuration manager not available")
            return fixes_applied

        # Fix missing default provider
        if self.config_manager.system_config.default_provider not in self.config_manager.providers:
            enabled_providers = self.config_manager.get_enabled_providers()
            if enabled_providers:
                self.config_manager.system_config.default_provider = enabled_providers[0]
                fixes_applied.append(f"Set default provider to '{enabled_providers[0]}'")

        # Fix invalid fallback chain
        valid_providers = list(self.config_manager.providers.keys())
        valid_fallback_chain = [p for p in self.config_manager.system_config.fallback_chain if p in valid_providers]

        if len(valid_fallback_chain) != len(self.config_manager.system_config.fallback_chain):
            self.config_manager.system_config.fallback_chain = valid_fallback_chain
            fixes_applied.append("Removed invalid providers from fallback chain")

        # Save configuration if auto_fix is enabled
        if auto_fix and fixes_applied:
            self.config_manager.save_configuration()
            fixes_applied.append("Configuration saved")

        return fixes_applied

    def get_provider_recommendations(self, task_type: str = "general") -> List[Dict[str, Any]]:
        """Get provider recommendations for specific task types"""
        if not self.config_manager:
            return []

        recommendations = []

        for provider_name, provider_config in self.config_manager.providers.items():
            if not provider_config.enabled:
                continue

            score = 0.0
            reasons = []

            # Base score
            if provider_config.type == "local":
                score += 80
                reasons.append("Local provider - no API costs")
            elif provider_config.type == "internal":
                score += 75
                reasons.append("Internal provider - fast and free")
            else:
                score += 50

            # Cost factor
            if provider_config.cost_per_1k_tokens == 0:
                score += 30
                reasons.append("Free usage")
            elif provider_config.cost_per_1k_tokens < 0.001:
                score += 20
                reasons.append("Low cost")
            elif provider_config.cost_per_1k_tokens < 0.01:
                score += 10
                reasons.append("Reasonable cost")

            # Task-specific scoring
            if task_type in ["coding", "development"]:
                if "coding" in provider_config.models.get(provider_config.default_model, {}).get("capabilities", []):
                    score += 15
                    reasons.append("Good for coding tasks")

            if task_type in ["text_to_speech", "tts"]:
                if provider_config.type == "tts":
                    score += 40
                    reasons.append("Specialized TTS provider")
                else:
                    score -= 20
                    reasons.append("Not suitable for TTS")

            recommendations.append({
                "provider": provider_name,
                "score": score,
                "reasons": reasons,
                "config": {
                    "type": provider_config.type,
                    "cost_per_1k_tokens": provider_config.cost_per_1k_tokens,
                    "default_model": provider_config.default_model
                }
            })

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

def main():
    """Main function for standalone execution"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="AI Configuration Validation Utility")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--report", action="store_true", help="Generate configuration report")
    parser.add_argument("--fix", action="store_true", help="Fix common configuration issues")
    parser.add_argument("--recommend", help="Get provider recommendations for task type")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    validator = AIConfigValidator()

    if args.validate:
        print("🔍 Validating AI configuration...")
        result = validator.validate_configuration()

        print(f"\n✅ Configuration is {'VALID' if result.is_valid else 'INVALID'}")

        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"   - {error}")

        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   - {warning}")

        if result.recommendations:
            print(f"\n💡 Recommendations ({len(result.recommendations)}):")
            for rec in result.recommendations:
                print(f"   - {rec}")

        sys.exit(0 if result.is_valid else 1)

    elif args.report:
        print("📊 Generating configuration report...")
        report = validator.generate_configuration_report()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {args.output}")
        else:
            print(json.dumps(report, indent=2))

    elif args.fix:
        print("🔧 Fixing configuration issues...")
        fixes = validator.fix_configuration_issues(auto_fix=True)

        if fixes:
            print(f"Applied {len(fixes)} fixes:")
            for fix in fixes:
                print(f"   - {fix}")
        else:
            print("No fixes needed")

    elif args.recommend:
        print(f"🎯 Getting provider recommendations for '{args.recommend}'...")
        recommendations = validator.get_provider_recommendations(args.recommend)

        print(f"\nTop recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec['provider']} (Score: {rec['score']:.1f})")
            for reason in rec['reasons']:
                print(f"   - {reason}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
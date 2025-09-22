#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Configuration Validator
Validates API keys and configuration for DuckBot v4.2
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api_key_manager import APIKeyManager, get_api_key_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Configuration validation system for DuckBot"""

    def __init__(self):
        self.api_manager = get_api_key_manager()
        self.validation_results = {}
        self.overall_status = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }

    def validate_api_keys(self) -> Dict[str, Any]:
        """Validate all API keys"""
        logger.info("Validating API keys...")
        return self.api_manager.validate_all_keys()

    def check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables"""
        logger.info("Checking environment variables...")

        required_vars = [
            "OPENROUTER_API_KEY",
            "DUCKBOT_LOG_LEVEL",
            "DUCKBOT_DATA_DIR",
            "DUCKBOT_CONFIG_DIR"
        ]

        optional_vars = [
            "DISCORD_TOKEN",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "GROQ_API_KEY",
            "ZAI_API_KEY",
            "GITHUB_TOKEN"
        ]

        results = {
            "required": {},
            "optional": {},
            "missing_required": [],
            "present_optional": []
        }

        for var in required_vars:
            value = os.getenv(var)
            results["required"][var] = {
                "present": bool(value),
                "value": value[:8] + "..." if value and len(value) > 8 else value
            }
            if not value:
                results["missing_required"].append(var)
                self.overall_status["errors"].append(f"Missing required environment variable: {var}")
                self.overall_status["valid"] = False

        for var in optional_vars:
            value = os.getenv(var)
            results["optional"][var] = {
                "present": bool(value),
                "value": value[:8] + "..." if value and len(value) > 8 else value
            }
            if value:
                results["present_optional"].append(var)

        return results

    def check_directory_structure(self) -> Dict[str, Any]:
        """Check required directory structure"""
        logger.info("Checking directory structure...")

        base_dir = Path(__file__).parent.parent
        required_dirs = [
            "config",
            "data",
            "logs",
            "duckbot",
            "docs"
        ]

        results = {
            "directories": {},
            "missing": [],
            "created": []
        }

        for dir_name in required_dirs:
            dir_path = base_dir / dir_name
            exists = dir_path.exists()
            results["directories"][dir_name] = {
                "path": str(dir_path),
                "exists": exists,
                "writable": dir_path.is_dir() and os.access(dir_path, os.W_OK) if exists else False
            }

            if not exists:
                results["missing"].append(dir_name)
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    results["directories"][dir_name]["exists"] = True
                    results["directories"][dir_name]["created"] = True
                    results["created"].append(dir_name)
                    logger.info(f"Created directory: {dir_path}")
                except Exception as e:
                    self.overall_status["errors"].append(f"Failed to create directory {dir_name}: {e}")
                    self.overall_status["valid"] = False

        return results

    def check_configuration_files(self) -> Dict[str, Any]:
        """Check configuration files"""
        logger.info("Checking configuration files...")

        config_dir = Path(__file__).parent
        required_files = [
            ".env",
            "ai_config.json",
            "enhanced_config.json",
            "ecosystem_config.yaml"
        ]

        results = {
            "files": {},
            "missing": [],
            "valid": [],
            "invalid": []
        }

        for file_name in required_files:
            file_path = config_dir / file_name
            exists = file_path.exists()
            results["files"][file_name] = {
                "path": str(file_path),
                "exists": exists,
                "size": file_path.stat().st_size if exists else 0,
                "readable": file_path.is_file() and os.access(file_path, os.R_OK) if exists else False
            }

            if not exists:
                results["missing"].append(file_name)
                self.overall_status["errors"].append(f"Missing configuration file: {file_name}")
                self.overall_status["valid"] = False
            else:
                try:
                    if file_name.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                        results["valid"].append(file_name)
                    elif file_name.endswith('.yaml') or file_name.endswith('.yml'):
                        import yaml
                        with open(file_path, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                        results["valid"].append(file_name)
                    else:
                        results["valid"].append(file_name)
                except Exception as e:
                    results["invalid"].append(file_name)
                    self.overall_status["errors"].append(f"Invalid configuration file {file_name}: {e}")
                    self.overall_status["valid"] = False

        return results

    def check_service_readiness(self) -> Dict[str, Any]:
        """Check if services are ready"""
        logger.info("Checking service readiness...")

        results = {
            "services": {},
            "ready": [],
            "not_ready": []
        }

        # Check LM Studio
        lm_studio_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
        try:
            import requests
            response = requests.get(f"{lm_studio_url}/models", timeout=5)
            if response.status_code == 200:
                results["services"]["lm_studio"] = {
                    "status": "ready",
                    "url": lm_studio_url,
                    "response_time": response.elapsed.total_seconds()
                }
                results["ready"].append("lm_studio")
            else:
                results["services"]["lm_studio"] = {
                    "status": "not_ready",
                    "url": lm_studio_url,
                    "error": f"HTTP {response.status_code}"
                }
                results["not_ready"].append("lm_studio")
        except Exception as e:
            results["services"]["lm_studio"] = {
                "status": "not_ready",
                "url": lm_studio_url,
                "error": str(e)
            }
            results["not_ready"].append("lm_studio")

        # Check Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                results["services"]["ollama"] = {
                    "status": "ready",
                    "url": ollama_url,
                    "response_time": response.elapsed.total_seconds()
                }
                results["ready"].append("ollama")
            else:
                results["services"]["ollama"] = {
                    "status": "not_ready",
                    "url": ollama_url,
                    "error": f"HTTP {response.status_code}"
                }
                results["not_ready"].append("ollama")
        except Exception as e:
            results["services"]["ollama"] = {
                "status": "not_ready",
                "url": ollama_url,
                "error": str(e)
            }
            results["not_ready"].append("ollama")

        return results

    def generate_recommendations(self) -> List[str]:
        """Generate configuration recommendations"""
        recommendations = []

        # Check API keys
        api_validations = self.validate_api_keys()
        required_keys_missing = [
            key for key, validation in api_validations.items()
            if self.api_manager.api_configs[key].required and validation.status.value == "missing"
        ]

        if required_keys_missing:
            recommendations.append(
                f"Configure required API keys: {', '.join(required_keys_missing)}"
            )

        # Check optional but recommended keys
        recommended_keys = [
            key for key, validation in api_validations.items()
            if not self.api_manager.api_configs[key].required and key in ["discord", "anthropic"]
            and validation.status.value == "missing"
        ]

        if recommended_keys:
            recommendations.append(
                f"Consider configuring these optional keys for enhanced functionality: {', '.join(recommended_keys)}"
            )

        # Check service readiness
        service_results = self.check_service_readiness()
        if "lm_studio" in service_results["not_ready"]:
            recommendations.append(
                "Start LM Studio for local AI model support (recommended for local-only mode)"
            )

        return recommendations

    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete configuration validation"""
        logger.info("Starting full configuration validation...")

        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "api_keys": {},
            "environment_variables": {},
            "directory_structure": {},
            "configuration_files": {},
            "service_readiness": {},
            "recommendations": []
        }

        # Run all validations
        validation_report["api_keys"] = self.validate_api_keys()
        validation_report["environment_variables"] = self.check_environment_variables()
        validation_report["directory_structure"] = self.check_directory_structure()
        validation_report["configuration_files"] = self.check_configuration_files()
        validation_report["service_readiness"] = self.check_service_readiness()
        validation_report["recommendations"] = self.generate_recommendations()

        # Determine overall status
        if self.overall_status["valid"]:
            validation_report["overall_status"] = "valid"
        elif self.overall_status["errors"]:
            validation_report["overall_status"] = "invalid"
        else:
            validation_report["overall_status"] = "warning"

        # Add status details
        validation_report["status_details"] = self.overall_status

        return validation_report

    def print_report(self, report: Dict[str, Any]):
        """Print validation report"""
        print("\n" + "=" * 70)
        print("🦆 DuckBot v4.2 Configuration Validation Report")
        print("=" * 70)
        print(f"Generated: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print("=" * 70)

        # API Keys Status
        print("\n🔑 API Keys Status:")
        for key_name, validation in report["api_keys"].items():
            config = self.api_manager.api_configs[key_name]
            status_icon = "✅" if validation.status.value == "valid" else "⚠️" if validation.status.value == "missing" else "❌"
            required_icon = "🔒" if config.required else "🔓"
            print(f"  {status_icon} {required_icon} {config.name}")
            if validation.status.value != "missing":
                print(f"      Status: {validation.status.value}")
            if validation.error_message:
                print(f"      Error: {validation.error_message}")

        # Environment Variables
        print("\n🌍 Environment Variables:")
        env_results = report["environment_variables"]
        if env_results["missing_required"]:
            print(f"  ❌ Missing required: {', '.join(env_results['missing_required'])}")
        if env_results["present_optional"]:
            print(f"  ✅ Configured optional: {', '.join(env_results['present_optional'])}")

        # Service Readiness
        print("\n🚀 Service Readiness:")
        service_results = report["service_readiness"]
        for service_name, service_info in service_results["services"].items():
            status_icon = "✅" if service_info["status"] == "ready" else "❌"
            print(f"  {status_icon} {service_name.upper()}: {service_info['status']}")
            if service_info["status"] == "ready":
                print(f"      Response time: {service_info['response_time']:.2f}s")

        # Recommendations
        if report["recommendations"]:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")

        print("\n" + "=" * 70)

def main():
    """Main entry point"""
    try:
        validator = ConfigValidator()
        report = validator.run_full_validation()
        validator.print_report(report)

        # Save report
        report_file = Path(__file__).parent / "validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📄 Detailed report saved to: {report_file}")

        # Exit with appropriate code
        if report["overall_status"] == "valid":
            print("✅ Configuration is valid!")
            return 0
        elif report["overall_status"] == "invalid":
            print("❌ Configuration has critical issues!")
            return 1
        else:
            print("⚠️  Configuration has warnings but is usable.")
            return 0

    except Exception as e:
        logger.error(f"Validation error: {e}")
        print(f"❌ Validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
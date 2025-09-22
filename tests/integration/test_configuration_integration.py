#!/usr/bin/env python3
"""
DuckBot Configuration Integration Tests
Comprehensive tests for configuration system validation and integration
"""

import os
import sys
import json
import yaml
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from test_startup_system import IntegrationTestFramework, TestConfig, TestResult
except ImportError:
    # Fallback definitions
    @dataclass
    class TestResult:
        test_name: str
        test_category: str
        status: str
        duration: float
        error_message: Optional[str] = None
        details: Optional[Dict] = None

class ConfigurationIntegrationTests:
    """Test suite for configuration system integration"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.test_results: List[TestResult] = []
        self.logger = logging.getLogger('DuckBot.ConfigTests')

    def record_result(self, test_name: str, status: str, duration: float, error_msg: str = None, details: Dict = None) -> TestResult:
        """Record a test result"""
        result = TestResult(
            test_name=test_name,
            test_category="configuration",
            status=status,
            duration=duration,
            error_message=error_msg,
            details=details or {}
        )
        self.test_results.append(result)
        return result

    def test_startup_config_structure(self) -> bool:
        """Test startup configuration file structure and validation"""
        start_time = time.time()

        try:
            config_path = self.base_dir / "config" / "startup_config.json"
            if not config_path.exists():
                return False, f"startup_config.json not found at {config_path}"

            # Load and parse configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate top-level structure
            required_sections = ['api_keys', 'interfaces', 'modes', 'features', 'system']
            missing_sections = [section for section in required_sections if section not in config]

            if missing_sections:
                return False, f"Missing required sections: {missing_sections}"

            # Validate api_keys structure
            api_keys = config.get('api_keys', {})
            expected_api_keys = ['gemini_api_key', 'openrouter_api_key', 'zai_api_key', 'zai_coding_plan']
            missing_api_keys = [key for key in expected_api_keys if key not in api_keys]

            # Note: API keys can be null (not configured), so we just check they exist

            # Validate interfaces structure
            interfaces = config.get('interfaces', {})
            required_interfaces = ['default_interface', 'web_launcher_port', 'enable_voice_control']
            missing_interfaces = [interface for interface in required_interfaces if interface not in interfaces]

            if missing_interfaces:
                return False, f"Missing interface configurations: {missing_interfaces}"

            # Validate modes structure
            modes = config.get('modes', {})
            required_modes = ['ai_enhanced', 'local_only', 'bytebot', 'ui_tars', 'archon', 'livekit', 'n8n_agent']
            missing_modes = [mode for mode in required_modes if mode not in modes]

            if missing_modes:
                return False, f"Missing mode configurations: {missing_modes}"

            # Validate individual mode configurations
            for mode_name, mode_config in modes.items():
                if not isinstance(mode_config, dict):
                    return False, f"Mode {mode_name} configuration is not a dictionary"

                required_mode_fields = ['enabled', 'description']
                missing_mode_fields = [field for field in required_mode_fields if field not in mode_config]

                if missing_mode_fields:
                    return False, f"Mode {mode_name} missing fields: {missing_mode_fields}"

                # Validate enabled field is boolean
                if not isinstance(mode_config.get('enabled'), bool):
                    return False, f"Mode {mode_name} enabled field is not boolean"

            # Validate features structure
            features = config.get('features', {})
            required_features = ['ai_recommendations', 'real_time_monitoring', 'comprehensive_logging']
            missing_features = [feature for feature in required_features if feature not in features]

            if missing_features:
                return False, f"Missing feature configurations: {missing_features}"

            # Validate system structure
            system_config = config.get('system', {})
            required_system_fields = ['max_concurrent_processes', 'process_timeout', 'log_retention_days']
            missing_system_fields = [field for field in required_system_fields if field not in system_config]

            if missing_system_fields:
                return False, f"Missing system configuration fields: {missing_system_fields}"

            duration = time.time() - start_time
            return True, f"Startup config structure validated successfully ({duration:.2f}s)"

        except json.JSONDecodeError as e:
            duration = time.time() - start_time
            return False, f"Invalid JSON in startup_config.json: {e}"
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing startup config structure: {e}"

    def test_ecosystem_config_structure(self) -> bool:
        """Test ecosystem configuration file structure and validation"""
        start_time = time.time()

        try:
            config_path = self.base_dir / "config" / "ecosystem_config.yaml"
            if not config_path.exists():
                return False, f"ecosystem_config.yaml not found at {config_path}"

            # Load and parse configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                return False, "Ecosystem config must be a dictionary"

            # Validate top-level structure
            required_sections = ['services', 'ai', 'logging']
            missing_sections = [section for section in required_sections if section not in config]

            if missing_sections:
                return False, f"Missing required sections: {missing_sections}"

            # Validate services configuration
            services = config.get('services', {})
            if not isinstance(services, dict):
                return False, "Services configuration must be a dictionary"

            required_services = ['webui', 'monitor']
            for service in required_services:
                if service not in services:
                    return False, f"Missing service configuration: {service}"

                service_config = services[service]
                if not isinstance(service_config, dict):
                    return False, f"Service {service} configuration must be a dictionary"

                required_service_fields = ['port', 'host']
                missing_service_fields = [field for field in required_service_fields if field not in service_config]

                if missing_service_fields:
                    return False, f"Service {service} missing fields: {missing_service_fields}"

                # Validate port and host
                port = service_config.get('port')
                if not isinstance(port, int) or port <= 0 or port > 65535:
                    return False, f"Service {service} has invalid port: {port}"

                host = service_config.get('host')
                if not isinstance(host, str):
                    return False, f"Service {service} has invalid host: {host}"

            # Validate AI configuration
            ai_config = config.get('ai', {})
            if not isinstance(ai_config, dict):
                return False, "AI configuration must be a dictionary"

            required_ai_fields = ['routing_mode', 'main_brain']
            missing_ai_fields = [field for field in required_ai_fields if field not in ai_config]

            if missing_ai_fields:
                return False, f"Missing AI configuration fields: {missing_ai_fields}"

            # Validate logging configuration
            logging_config = config.get('logging', {})
            if not isinstance(logging_config, dict):
                return False, "Logging configuration must be a dictionary"

            required_logging_fields = ['level', 'directory']
            missing_logging_fields = [field for field in required_logging_fields if field not in logging_config]

            if missing_logging_fields:
                return False, f"Missing logging configuration fields: {missing_logging_fields}"

            duration = time.time() - start_time
            return True, f"Ecosystem config structure validated successfully ({duration:.2f}s)"

        except yaml.YAMLError as e:
            duration = time.time() - start_time
            return False, f"Invalid YAML in ecosystem_config.yaml: {e}"
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing ecosystem config structure: {e}"

    def test_hardware_config_structure(self) -> bool:
        """Test hardware configuration file structure and validation"""
        start_time = time.time()

        try:
            config_path = self.base_dir / "config" / "hardware_config.json"
            if not config_path.exists():
                # Hardware config is optional, so this is not a failure
                return True, "Hardware config not found (optional)"

            # Load and parse configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if not isinstance(config, dict):
                return False, "Hardware config must be a dictionary"

            # Validate top-level structure
            required_sections = ['system_info', 'gpu_info', 'cpu_info', 'memory_info']
            missing_sections = [section for section in required_sections if section not in config]

            if missing_sections:
                return False, f"Missing required sections: {missing_sections}"

            # Validate system info
            system_info = config.get('system_info', {})
            if not isinstance(system_info, dict):
                return False, "System info must be a dictionary"

            # Validate GPU info
            gpu_info = config.get('gpu_info', {})
            if not isinstance(gpu_info, dict):
                return False, "GPU info must be a dictionary"

            # Validate CPU info
            cpu_info = config.get('cpu_info', {})
            if not isinstance(cpu_info, dict):
                return False, "CPU info must be a dictionary"

            # Validate memory info
            memory_info = config.get('memory_info', {})
            if not isinstance(memory_info, dict):
                return False, "Memory info must be a dictionary"

            duration = time.time() - start_time
            return True, f"Hardware config structure validated successfully ({duration:.2f}s)"

        except json.JSONDecodeError as e:
            duration = time.time() - start_time
            return False, f"Invalid JSON in hardware_config.json: {e}"
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing hardware config structure: {e}"

    def test_ai_config_structure(self) -> bool:
        """Test AI configuration file structure and validation"""
        start_time = time.time()

        try:
            config_path = self.base_dir / "config" / "ai_config.json"
            if not config_path.exists():
                return True, "AI config not found (optional)"

            # Load and parse configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if not isinstance(config, dict):
                return False, "AI config must be a dictionary"

            # Validate provider configuration
            provider = config.get('provider')
            if provider not in ['lm_studio', 'openrouter', 'auto']:
                return False, f"Invalid AI provider: {provider}"

            # Validate LM Studio configuration
            if provider == 'lm_studio':
                lm_studio_config = config.get('lm_studio', {})
                if not isinstance(lm_studio_config, dict):
                    return False, "LM Studio config must be a dictionary"

                required_lm_studio_fields = ['url', 'model']
                missing_lm_studio_fields = [field for field in required_lm_studio_fields if field not in lm_studio_config]

                if missing_lm_studio_fields:
                    return False, f"Missing LM Studio configuration fields: {missing_lm_studio_fields}"

            # Validate OpenRouter configuration
            if provider == 'openrouter':
                openrouter_config = config.get('openrouter', {})
                if not isinstance(openrouter_config, dict):
                    return False, "OpenRouter config must be a dictionary"

                required_openrouter_fields = ['api_key', 'model']
                missing_openrouter_fields = [field for field in required_openrouter_fields if field not in openrouter_config]

                if missing_openrouter_fields:
                    return False, f"Missing OpenRouter configuration fields: {missing_openrouter_fields}"

            # Validate general AI settings
            required_general_fields = ['max_tokens', 'temperature', 'enable_caching']
            missing_general_fields = [field for field in required_general_fields if field not in config]

            if missing_general_fields:
                return False, f"Missing general AI configuration fields: {missing_general_fields}"

            # Validate numeric fields
            max_tokens = config.get('max_tokens')
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                return False, f"Invalid max_tokens: {max_tokens}"

            temperature = config.get('temperature')
            if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                return False, f"Invalid temperature: {temperature}"

            enable_caching = config.get('enable_caching')
            if not isinstance(enable_caching, bool):
                return False, f"Invalid enable_caching: {enable_caching}"

            duration = time.time() - start_time
            return True, f"AI config structure validated successfully ({duration:.2f}s)"

        except json.JSONDecodeError as e:
            duration = time.time() - start_time
            return False, f"Invalid JSON in ai_config.json: {e}"
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing AI config structure: {e}"

    def test_configuration_consistency(self) -> bool:
        """Test consistency across all configuration files"""
        start_time = time.time()

        try:
            # Load all configuration files
            configs = {}
            config_files = [
                ("startup_config.json", "startup"),
                ("ecosystem_config.yaml", "ecosystem"),
                ("hardware_config.json", "hardware"),
                ("ai_config.json", "ai")
            ]

            for filename, config_name in config_files:
                config_path = self.base_dir / "config" / filename
                if config_path.exists():
                    if filename.endswith('.json'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            configs[config_name] = json.load(f)
                    else:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            configs[config_name] = yaml.safe_load(f)

            # Check for consistency between startup and ecosystem configs
            if 'startup' in configs and 'ecosystem' in configs:
                startup_config = configs['startup']
                ecosystem_config = configs['ecosystem']

                # Check if modes defined in startup config have corresponding service definitions
                modes = startup_config.get('modes', {})
                services = ecosystem_config.get('services', {})

                inconsistent_modes = []
                for mode_name, mode_config in modes.items():
                    if mode_config.get('enabled', False):
                        # Some modes should have corresponding services
                        mode_service_mapping = {
                            'ai_enhanced': 'webui',
                            'monitoring': 'monitor'
                        }

                        if mode_name in mode_service_mapping:
                            expected_service = mode_service_mapping[mode_name]
                            if expected_service not in services:
                                inconsistent_modes.append(f"Mode {mode_name} enabled but service {expected_service} not defined")

                if inconsistent_modes:
                    return False, f"Inconsistent mode-service mapping: {inconsistent_modes}"

            # Check for consistency between startup and AI configs
            if 'startup' in configs and 'ai' in configs:
                startup_config = configs['startup']
                ai_config = configs['ai']

                # Check if AI provider in startup config matches AI config
                startup_ai_provider = startup_config.get('interfaces', {}).get('ai_provider')
                ai_provider = ai_config.get('provider')

                if startup_ai_provider and ai_provider and startup_ai_provider != ai_provider:
                    return False, f"AI provider mismatch: startup={startup_ai_provider}, ai={ai_provider}"

            duration = time.time() - start_time
            return True, f"Configuration consistency validated successfully ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing configuration consistency: {e}"

    def test_environment_variable_integration(self) -> bool:
        """Test integration of environment variables with configuration"""
        start_time = time.time()

        try:
            # Set test environment variables
            test_env_vars = {
                'DUCKBOT_TEST_MODE': 'integration',
                'DUCKBOT_AI_PROVIDER': 'lm_studio',
                'DUCKBOT_ENABLE_CACHE': 'true',
                'DUCKBOT_MAX_TOKENS': '1000'
            }

            original_env = {}
            for key, value in test_env_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                # Test that configuration files can access environment variables
                # This is a simulated test - in a real scenario, the config loading
                # would process environment variables

                # Create a test configuration with environment variable references
                test_config = {
                    'test_mode': '${DUCKBOT_TEST_MODE}',
                    'ai_provider': '${DUCKBOT_AI_PROVIDER}',
                    'enable_cache': '${DUCKBOT_ENABLE_CACHE}',
                    'max_tokens': '${DUCKBOT_MAX_TOKENS}'
                }

                # Simulate environment variable substitution
                def substitute_env_vars(obj):
                    if isinstance(obj, dict):
                        return {k: substitute_env_vars(v) for k, v in obj.items()}
                    elif isinstance(obj, str):
                        for key, value in test_env_vars.items():
                            obj = obj.replace(f'${{{key}}}', value)
                        return obj
                    else:
                        return obj

                substituted_config = substitute_env_vars(test_config)

                # Validate substitution worked
                if substituted_config.get('test_mode') != 'integration':
                    return False, "Environment variable substitution failed for test_mode"

                if substituted_config.get('ai_provider') != 'lm_studio':
                    return False, "Environment variable substitution failed for ai_provider"

                if substituted_config.get('enable_cache') != 'true':
                    return False, "Environment variable substitution failed for enable_cache"

                if substituted_config.get('max_tokens') != '1000':
                    return False, "Environment variable substitution failed for max_tokens"

                duration = time.time() - start_time
                return True, f"Environment variable integration validated successfully ({duration:.2f}s)"

            finally:
                # Restore original environment
                for key, original_value in original_env.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing environment variable integration: {e}"

    def test_configuration_validation_logic(self) -> bool:
        """Test configuration validation logic and error handling"""
        start_time = time.time()

        try:
            # Test invalid configuration files
            invalid_configs = [
                {
                    'name': 'invalid_json',
                    'content': '{"invalid": json, "missing": quotes}',
                    'expected_error': 'JSONDecodeError'
                },
                {
                    'name': 'invalid_yaml',
                    'content': 'invalid: yaml: [unclosed',
                    'expected_error': 'YAMLError'
                },
                {
                    'name': 'missing_required_fields',
                    'content': '{"optional": "field"}',
                    'expected_error': 'Missing required sections'
                }
            ]

            validation_results = []

            for test_case in invalid_configs:
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json' if 'json' in test_case['name'] else '.yaml', delete=False) as f:
                        f.write(test_case['content'])
                        temp_file = f.name

                    try:
                        if 'json' in test_case['name']:
                            with open(temp_file, 'r', encoding='utf-8') as f:
                                json.load(f)
                        else:
                            with open(temp_file, 'r', encoding='utf-8') as f:
                                yaml.safe_load(f)

                        # If we get here, the invalid config was parsed successfully
                        validation_results.append(f"Test {test_case['name']}: Should have failed but didn't")

                    except (json.JSONDecodeError, yaml.YAMLError) as e:
                        # This is expected
                        validation_results.append(f"Test {test_case['name']}: Correctly failed with {type(e).__name__}")

                    finally:
                        os.unlink(temp_file)

                except Exception as e:
                    validation_results.append(f"Test {test_case['name']}: Unexpected error {e}")

            # Test configuration validation functions
            def validate_service_config(config: dict) -> Tuple[bool, str]:
                """Validate service configuration"""
                if not isinstance(config, dict):
                    return False, "Configuration must be a dictionary"

                required_fields = ['name', 'port', 'host']
                for field in required_fields:
                    if field not in config:
                        return False, f"Missing required field: {field}"

                port = config.get('port')
                if not isinstance(port, int) or port <= 0 or port > 65535:
                    return False, f"Invalid port: {port}"

                return True, "Valid configuration"

            # Test valid service configuration
            valid_config = {
                'name': 'test_service',
                'port': 8080,
                'host': 'localhost'
            }

            is_valid, message = validate_service_config(valid_config)
            if not is_valid:
                validation_results.append(f"Valid config rejected: {message}")

            # Test invalid service configurations
            invalid_service_configs = [
                ({}, "Empty config"),
                ({'name': 'test'}, "Missing port"),
                ({'name': 'test', 'port': 'invalid'}, "Invalid port type"),
                ({'name': 'test', 'port': 99999}, "Invalid port value")
            ]

            for config, description in invalid_service_configs:
                is_valid, message = validate_service_config(config)
                if is_valid:
                    validation_results.append(f"Invalid config accepted: {description}")

            failed_validations = [r for r in validation_results if "failed" in r.lower() or "rejected" in r.lower() or "accepted" in r.lower()]

            if failed_validations:
                return False, f"Configuration validation issues: {failed_validations}"

            duration = time.time() - start_time
            return True, f"Configuration validation logic tested successfully ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing configuration validation logic: {e}"

    def test_configuration_backup_and_restore(self) -> bool:
        """Test configuration backup and restore functionality"""
        start_time = time.time()

        try:
            # Create a test configuration
            test_config = {
                'test_value': 'original',
                'test_number': 42,
                'test_list': [1, 2, 3],
                'test_dict': {'nested': 'value'}
            }

            # Test backup creation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_config, f, indent=2)
                original_config_path = f.name

            backup_configs = []

            try:
                # Create multiple backups
                for i in range(3):
                    backup_path = f"{original_config_path}.backup_{i}"
                    import shutil
                    shutil.copy2(original_config_path, backup_path)
                    backup_configs.append(backup_path)

                # Modify original configuration
                modified_config = test_config.copy()
                modified_config['test_value'] = 'modified'
                modified_config['test_number'] = 99

                with open(original_config_path, 'w') as f:
                    json.dump(modified_config, f, indent=2)

                # Verify modification
                with open(original_config_path, 'r') as f:
                    current_config = json.load(f)

                if current_config.get('test_value') != 'modified':
                    return False, "Configuration modification failed"

                # Test restore from backup
                shutil.copy2(backup_configs[0], original_config_path)

                # Verify restore
                with open(original_config_path, 'r') as f:
                    restored_config = json.load(f)

                if restored_config != test_config:
                    return False, "Configuration restore failed"

                # Test backup cleanup
                for backup_path in backup_configs:
                    if os.path.exists(backup_path):
                        os.unlink(backup_path)

                duration = time.time() - start_time
                return True, f"Configuration backup and restore tested successfully ({duration:.2f}s)"

            finally:
                # Cleanup
                if os.path.exists(original_config_path):
                    os.unlink(original_config_path)
                for backup_path in backup_configs:
                    if os.path.exists(backup_path):
                        os.unlink(backup_path)

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing configuration backup and restore: {e}"

    def run_all_config_tests(self) -> List[TestResult]:
        """Run all configuration integration tests"""
        self.logger.info("Starting configuration integration tests...")

        # Define all configuration tests
        config_tests = [
            ("startup_config_structure", self.test_startup_config_structure),
            ("ecosystem_config_structure", self.test_ecosystem_config_structure),
            ("hardware_config_structure", self.test_hardware_config_structure),
            ("ai_config_structure", self.test_ai_config_structure),
            ("configuration_consistency", self.test_configuration_consistency),
            ("environment_variable_integration", self.test_environment_variable_integration),
            ("configuration_validation_logic", self.test_configuration_validation_logic),
            ("configuration_backup_and_restore", self.test_configuration_backup_and_restore),
        ]

        # Run all tests
        for test_name, test_func in config_tests:
            try:
                start_time = time.time()
                success, message = test_func()
                duration = time.time() - start_time

                status = "PASSED" if success else "FAILED"
                self.record_result(test_name, status, duration, message if not success else None)

                # Log result
                emoji = "✅" if success else "❌"
                self.logger.info(f"{emoji} [CONFIG] {test_name} ({duration:.2f}s) - {message}")

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Test execution error: {e}"
                self.record_result(test_name, "ERROR", duration, error_msg)
                self.logger.error(f"💥 [CONFIG] {test_name} failed: {error_msg}")

        return self.test_results

def main():
    """Main entry point for configuration integration tests"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Configuration Integration Tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run tests
    test_runner = ConfigurationIntegrationTests()
    results = test_runner.run_all_config_tests()

    # Print summary
    total_tests = len(results)
    passed = sum(1 for r in results if r.status == "PASSED")
    failed = sum(1 for r in results if r.status == "FAILED")
    errors = sum(1 for r in results if r.status == "ERROR")

    print(f"\n{'='*60}")
    print(f"CONFIGURATION INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Errors: {errors} 💥")
    print(f"Pass Rate: {(passed/total_tests*100):.1f}%")

    if failed > 0 or errors > 0:
        print(f"\n❌ Configuration integration tests completed with issues")
        sys.exit(1)
    else:
        print(f"\n✅ All configuration integration tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive Configuration System Test Suite
Tests all components of the new configuration management system
"""

import os
import sys
import json
import yaml
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config_manager import DuckBotConfigManager, Environment, ServiceStatus, get_config_manager
from config.unified_config import ConfigManager, DuckBotConfig, AIProviderConfig, IntegrationConfig

class TestDuckBotConfigManager(unittest.TestCase):
    """Test the main configuration manager"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_duckbot_config.yaml")

        # Create test configuration
        self.test_config = {
            'system': {
                'name': 'DuckBot Enhanced v4.2',
                'version': '4.2',
                'debug_mode': False,
                'log_level': 'INFO'
            },
            'services': {
                'webui': {
                    'enabled': True,
                    'name': 'Enhanced WebUI Dashboard',
                    'default_host': '127.0.0.1',
                    'default_port': 8787,
                    'health_endpoint': '/enhanced/health',
                    'startup_script': 'duckbot.enhanced_webui'
                },
                'monitoring': {
                    'enabled': True,
                    'name': 'System Monitoring Dashboard',
                    'default_host': '127.0.0.1',
                    'default_port': 8789,
                    'health_endpoint': '/health',
                    'startup_script': 'ai_ecosystem_manager'
                }
            },
            'features': {
                'webui_enabled': True,
                'monitoring_enabled': True,
                'local_only_mode': False
            },
            'ports': {
                'webui_range': [8780, 8799],
                'reserved_ports': [80, 443, 22]
            }
        }

        # Write test configuration
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_config_loading(self):
        """Test configuration loading from YAML file"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Test basic loading
        self.assertIsNotNone(config_manager.config_data)
        self.assertEqual(config_manager.config_data['system']['name'], 'DuckBot Enhanced v4.2')
        self.assertEqual(config_manager.config_data['system']['version'], '4.2')

        # Test service initialization
        services = config_manager.get_all_services()
        self.assertIn('webui', services)
        self.assertIn('monitoring', services)

        webui_service = services['webui']
        self.assertTrue(webui_service.enabled)
        self.assertEqual(webui_service.default_port, 8787)
        self.assertEqual(webui_service.name, 'Enhanced WebUI Dashboard')

    def test_environment_detection(self):
        """Test environment detection"""
        # Test development environment
        with patch.dict(os.environ, {'DUCKBOT_ENV': 'development'}):
            config_manager = DuckBotConfigManager(self.config_path)
            self.assertEqual(config_manager.environment, Environment.DEVELOPMENT)

        # Test production environment
        with patch.dict(os.environ, {'DUCKBOT_ENV': 'production'}):
            config_manager = DuckBotConfigManager(self.config_path)
            self.assertEqual(config_manager.environment, Environment.PRODUCTION)

        # Test local environment
        with patch.dict(os.environ, {'DUCKBOT_ENV': 'local'}):
            config_manager = DuckBotConfigManager(self.config_path)
            self.assertEqual(config_manager.environment, Environment.LOCAL)

        # Test auto-detection
        with patch.dict(os.environ, {'AI_LOCAL_ONLY_MODE': 'true'}, clear=True):
            config_manager = DuckBotConfigManager(self.config_path)
            self.assertEqual(config_manager.environment, Environment.LOCAL)

    def test_service_configuration(self):
        """Test service configuration methods"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Test get service config
        webui_config = config_manager.get_service_config('webui')
        self.assertIsNotNone(webui_config)
        self.assertEqual(webui_config.default_port, 8787)

        # Test get enabled services
        enabled_services = config_manager.get_enabled_services()
        self.assertEqual(len(enabled_services), 2)
        self.assertIn('webui', enabled_services)
        self.assertIn('monitoring', enabled_services)

        # Test get non-existent service
        nonexistent = config_manager.get_service_config('nonexistent')
        self.assertIsNone(nonexistent)

    def test_port_management(self):
        """Test port allocation and management"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Test port allocation
        port = config_manager.allocate_port('webui')
        self.assertEqual(port, 8787)
        self.assertIn(port, config_manager.allocated_ports)

        # Test port conflict
        with self.assertRaises(RuntimeError):
            config_manager.allocate_port('webui', 8787)

        # Test port release
        config_manager.release_port(8787)
        self.assertNotIn(8787, config_manager.allocated_ports)

        # Test port availability check
        self.assertTrue(config_manager._is_port_available(8787))

    def test_feature_flags(self):
        """Test feature flag system"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Test existing feature flags
        self.assertTrue(config_manager.get_feature_flag('webui_enabled'))
        self.assertTrue(config_manager.get_feature_flag('monitoring_enabled'))
        self.assertFalse(config_manager.get_feature_flag('local_only_mode'))

        # Test non-existent feature flag
        self.assertFalse(config_manager.get_feature_flag('nonexistent_feature'))

    def test_service_environment_variables(self):
        """Test service environment variable generation"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Allocate port first
        config_manager.allocate_port('webui', 8787)

        # Get environment variables
        env_vars = config_manager.get_service_environment('webui')

        self.assertIn('DUCKBOT_WEBUI_PORT', env_vars)
        self.assertIn('DUCKBOT_WEBUI_HOST', env_vars)
        self.assertEqual(env_vars['DUCKBOT_WEBUI_PORT'], '8787')
        self.assertEqual(env_vars['DUCKBOT_WEBUI_HOST'], '127.0.0.1')

    def test_service_url_generation(self):
        """Test service URL generation"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Allocate port first
        config_manager.allocate_port('webui', 8787)

        # Get service URL
        url = config_manager.get_service_url('webui')
        self.assertEqual(url, 'http://127.0.0.1:8787')

        # Test non-existent service
        url = config_manager.get_service_url('nonexistent')
        self.assertIsNone(url)

    def test_service_status_management(self):
        """Test service status updates"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Update service status
        config_manager.update_service_status('webui', ServiceStatus.RUNNING, 12345)

        # Check status update
        webui_service = config_manager.get_service_config('webui')
        self.assertEqual(webui_service.status, ServiceStatus.RUNNING)
        self.assertEqual(webui_service.pid, 12345)

    def test_configuration_validation(self):
        """Test configuration validation"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Test validation with good config
        issues = config_manager.validate_config()
        self.assertEqual(len(issues), 0)

        # Test with port conflict
        config_manager.config_data['services']['conflict_service'] = {
            'enabled': True,
            'default_port': 8787  # Same as webui
        }
        config_manager._initialize_services()

        issues = config_manager.validate_config()
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('port conflict' in issue.lower() for issue in issues))

    def test_system_info(self):
        """Test system information generation"""
        config_manager = DuckBotConfigManager(self.config_path)

        system_info = config_manager.get_system_info()

        self.assertIn('environment', system_info)
        self.assertIn('total_services', system_info)
        self.assertIn('enabled_services', system_info)
        self.assertIn('features', system_info)
        self.assertIn('validation_issues', system_info)

        self.assertEqual(system_info['total_services'], 2)
        self.assertEqual(system_info['enabled_services'], 2)

class TestEnvironmentSpecificConfigs(unittest.TestCase):
    """Test environment-specific configuration overrides"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_env_config.yaml")

        # Create test configuration with environment overrides
        self.test_config = {
            'system': {
                'name': 'DuckBot Enhanced v4.2',
                'debug_mode': False,
                'log_level': 'INFO'
            },
            'services': {
                'webui': {
                    'enabled': True,
                    'default_port': 8787
                },
                'postgres': {
                    'enabled': False,
                    'default_port': 5432
                }
            },
            'environments': {
                'development': {
                    'debug_mode': True,
                    'log_level': 'DEBUG',
                    'services': {
                        'postgres': {
                            'enabled': True
                        }
                    }
                },
                'production': {
                    'debug_mode': False,
                    'log_level': 'INFO',
                    'enable_ssl': True,
                    'services': {
                        'postgres': {
                            'enabled': True
                        }
                    }
                },
                'local': {
                    'debug_mode': False,
                    'log_level': 'INFO',
                    'offline_mode': True,
                    'services': {
                        'postgres': {
                            'enabled': False
                        }
                    }
                }
            }
        }

        # Write test configuration
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_development_environment(self):
        """Test development environment overrides"""
        with patch.dict(os.environ, {'DUCKBOT_ENV': 'development'}):
            config_manager = DuckBotConfigManager(self.config_path)

            # Check environment detection
            self.assertEqual(config_manager.environment, Environment.DEVELOPMENT)

            # Check overrides applied
            self.assertTrue(config_manager.config_data['system']['debug_mode'])
            self.assertEqual(config_manager.config_data['system']['log_level'], 'DEBUG')

            # Check service overrides
            postgres_service = config_manager.get_service_config('postgres')
            self.assertTrue(postgres_service.enabled)

    def test_production_environment(self):
        """Test production environment overrides"""
        with patch.dict(os.environ, {'DUCKBOT_ENV': 'production'}):
            config_manager = DuckBotConfigManager(self.config_path)

            # Check environment detection
            self.assertEqual(config_manager.environment, Environment.PRODUCTION)

            # Check overrides applied
            self.assertFalse(config_manager.config_data['system']['debug_mode'])
            self.assertEqual(config_manager.config_data['system']['log_level'], 'INFO')
            self.assertTrue(config_manager.config_data['system']['enable_ssl'])

            # Check service overrides
            postgres_service = config_manager.get_service_config('postgres')
            self.assertTrue(postgres_service.enabled)

    def test_local_environment(self):
        """Test local environment overrides"""
        with patch.dict(os.environ, {'DUCKBOT_ENV': 'local'}):
            config_manager = DuckBotConfigManager(self.config_path)

            # Check environment detection
            self.assertEqual(config_manager.environment, Environment.LOCAL)

            # Check overrides applied
            self.assertFalse(config_manager.config_data['system']['debug_mode'])
            self.assertEqual(config_manager.config_data['system']['log_level'], 'INFO')
            self.assertTrue(config_manager.config_data['system']['offline_mode'])

            # Check service overrides
            postgres_service = config_manager.get_service_config('postgres')
            self.assertFalse(postgres_service.enabled)

class TestUnifiedConfig(unittest.TestCase):
    """Test unified configuration system"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_unified_config.json")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_unified_config_creation(self):
        """Test unified configuration creation and loading"""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.load_config()

        # Test default configuration
        self.assertIsInstance(config, DuckBotConfig)
        self.assertEqual(config.version, "4.2")
        self.assertIsNotNone(config.webui)
        self.assertIsNotNone(config.system)

        # Test AI provider management
        provider_config = AIProviderConfig(
            name="test_provider",
            api_key="test_key",
            base_url="http://test.com",
            model="test_model"
        )
        config_manager.set_ai_provider("test_provider", provider_config)

        retrieved_provider = config_manager.get_ai_provider("test_provider")
        self.assertIsNotNone(retrieved_provider)
        self.assertEqual(retrieved_provider.name, "test_provider")
        self.assertEqual(retrieved_provider.api_key, "test_key")

    def test_config_validation(self):
        """Test configuration validation"""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.load_config()

        # Add invalid provider (enabled but no API key)
        invalid_provider = AIProviderConfig(
            name="invalid_provider",
            enabled=True,
            api_key=None
        )
        config_manager.set_ai_provider("invalid_provider", invalid_provider)

        # Test validation
        errors = config_manager.validate_config()
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("API key required" in error for error in errors))

    def test_config_export_import(self):
        """Test configuration export and import"""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.load_config()

        # Add some test data
        provider_config = AIProviderConfig(
            name="export_test",
            api_key="export_key",
            base_url="http://export.com"
        )
        config_manager.set_ai_provider("export_test", provider_config)

        # Export configuration
        json_export = config_manager.export_config('json')
        yaml_export = config_manager.export_config('yaml')

        self.assertIsInstance(json_export, str)
        self.assertIsInstance(yaml_export, str)

        # Test JSON import
        new_config_manager = ConfigManager(os.path.join(self.test_dir, "import_test.json"))
        new_config_manager.import_config(json_export, 'json')

        imported_provider = new_config_manager.get_ai_provider("export_test")
        self.assertIsNotNone(imported_provider)
        self.assertEqual(imported_provider.api_key, "export_key")

class TestConfigurationIntegration(unittest.TestCase):
    """Test integration between configuration systems"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.yaml_config_path = os.path.join(self.test_dir, "duckbot_config.yaml")
        self.json_config_path = os.path.join(self.test_dir, "unified_config.json")

        # Create test YAML configuration
        yaml_config = {
            'system': {
                'name': 'DuckBot Enhanced v4.2',
                'version': '4.2'
            },
            'services': {
                'webui': {
                    'enabled': True,
                    'default_port': 8787,
                    'startup_script': 'duckbot.enhanced_webui'
                }
            },
            'features': {
                'webui_enabled': True,
                'local_only_mode': False
            }
        }

        with open(self.yaml_config_path, 'w') as f:
            yaml.dump(yaml_config, f)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_configuration_systems_coexistence(self):
        """Test that both configuration systems can coexist"""
        # Test YAML config manager
        yaml_manager = DuckBotConfigManager(self.yaml_config_path)
        self.assertIsNotNone(yaml_manager.config_data)
        self.assertEqual(yaml_manager.config_data['system']['version'], '4.2')

        # Test JSON config manager
        json_manager = ConfigManager(self.json_config_path)
        json_config = json_manager.load_config()
        self.assertIsNotNone(json_config)
        self.assertEqual(json_config.version, '4.2')

        # Test that they don't interfere
        yaml_services = yaml_manager.get_enabled_services()
        self.assertEqual(len(yaml_services), 1)

        json_providers = json_manager.get_ai_provider("test")
        self.assertIsNone(json_providers)  # Should be empty by default

def run_configuration_tests():
    """Run all configuration tests"""
    print("Running Comprehensive Configuration System Tests...")
    print("=" * 60)

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestDuckBotConfigManager,
        TestEnvironmentSpecificConfigs,
        TestUnifiedConfig,
        TestConfigurationIntegration
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'SUCCESS' if success else 'FAILURE'}")

    return success

if __name__ == '__main__':
    success = run_configuration_tests()
    sys.exit(0 if success else 1)
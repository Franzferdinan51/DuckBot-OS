#!/usr/bin/env python3
"""
DuckBot Configuration System Test Suite
Comprehensive testing of the centralized configuration management system
"""

import unittest
import tempfile
import os
import json
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import (
    DuckBotConfigManager,
    ServiceConfig,
    Environment,
    ServiceStatus,
    get_config_manager,
    initialize_config
)

class TestDuckBotConfigManager(unittest.TestCase):
    """Test cases for DuckBotConfigManager"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary config file for testing
        self.test_config = {
            'system': {
                'name': 'DuckBot Test',
                'version': '4.2-test',
                'log_level': 'INFO'
            },
            'services': {
                'test_service': {
                    'name': 'Test Service',
                    'enabled': True,
                    'default_host': '127.0.0.1',
                    'default_port': 9000,
                    'startup_script': 'test_module.test_service',
                    'environment_vars': {
                        'TEST_VAR': 'test_value_{port}',
                        'TEST_HOST': '{host}'
                    }
                },
                'disabled_service': {
                    'name': 'Disabled Service',
                    'enabled': False,
                    'default_port': 9001
                }
            },
            'features': {
                'test_feature': True,
                'disabled_feature': False
            },
            'environments': {
                'test': {
                    'debug_mode': True,
                    'services': {
                        'test_service': {
                            'debug_mode': True
                        }
                    }
                }
            },
            'ai_providers': {
                'lm_studio': {
                    'enabled': True,
                    'url': 'http://localhost:1234/v1'
                }
            },
            'ports': {
                'reserved_ports': [80, 443],
                'webui_range': [9000, 9100]
            }
        }

        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        # Initialize config manager
        self.config_manager = DuckBotConfigManager(self.config_path)

    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_config_loading(self):
        """Test configuration loading"""
        self.assertEqual(self.config_manager.config_data['system']['name'], 'DuckBot Test')
        self.assertEqual(self.config_manager.config_data['system']['version'], '4.2-test')

    def test_service_initialization(self):
        """Test service configuration initialization"""
        services = self.config_manager.get_all_services()
        self.assertIn('test_service', services)
        self.assertIn('disabled_service', services)

        test_service = services['test_service']
        self.assertTrue(test_service.enabled)
        self.assertEqual(test_service.default_port, 9000)
        self.assertEqual(test_service.startup_script, 'test_module.test_service')

        disabled_service = services['disabled_service']
        self.assertFalse(disabled_service.enabled)

    def test_enabled_services(self):
        """Test getting enabled services"""
        enabled_services = self.config_manager.get_enabled_services()
        self.assertIn('test_service', enabled_services)
        self.assertNotIn('disabled_service', enabled_services)

    def test_port_allocation(self):
        """Test port allocation"""
        # Test allocating default port
        port = self.config_manager.allocate_port('test_service')
        self.assertEqual(port, 9000)

        # Test that port is marked as allocated
        self.assertIn(port, self.config_manager.allocated_ports)

        # Test port release
        self.config_manager.release_port(port)
        self.assertNotIn(port, self.config_manager.allocated_ports)

    def test_port_conflict(self):
        """Test port conflict handling"""
        # Allocate port for first service
        port1 = self.config_manager.allocate_port('test_service')

        # Try to allocate same port for different service
        port2 = self.config_manager.allocate_port('test_service', port1)
        self.assertNotEqual(port2, port1)

    def test_service_environment(self):
        """Test service environment variable generation"""
        env_vars = self.config_manager.get_service_environment('test_service')
        self.assertIn('TEST_VAR', env_vars)
        self.assertIn('TEST_HOST', env_vars)

        # Test template substitution
        self.assertEqual(env_vars['TEST_HOST'], '127.0.0.1')

    def test_feature_flags(self):
        """Test feature flag functionality"""
        self.assertTrue(self.config_manager.get_feature_flag('test_feature'))
        self.assertFalse(self.config_manager.get_feature_flag('disabled_feature'))
        self.assertFalse(self.config_manager.get_feature_flag('nonexistent_feature'))

    def test_service_url(self):
        """Test service URL generation"""
        url = self.config_manager.get_service_url('test_service')
        self.assertEqual(url, 'http://127.0.0.1:9000')

    def test_service_status_update(self):
        """Test service status updates"""
        self.config_manager.update_service_status('test_service', ServiceStatus.RUNNING, 1234)

        service = self.config_manager.get_service_config('test_service')
        self.assertEqual(service.status, ServiceStatus.RUNNING)
        self.assertEqual(service.pid, 1234)

    def test_config_validation(self):
        """Test configuration validation"""
        # Should pass with test config
        issues = self.config_manager.validate_config()
        self.assertEqual(len(issues), 0)

        # Add a conflicting port
        self.config_manager.config_data['services']['conflict_service'] = {
            'name': 'Conflict Service',
            'enabled': True,
            'default_port': 9000  # Same as test_service
        }
        self.config_manager._initialize_services()

        issues = self.config_manager.validate_config()
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('Port conflict' in issue for issue in issues))

    def test_environment_override(self):
        """Test environment-specific configuration"""
        # Create a config with environment override
        import tempfile
        import yaml
        import os

        test_config = self.test_config.copy()
        test_config['environments']['development'] = {
            'debug_mode': True,
            'services': {
                'test_service': {
                    'debug_mode': True
                }
            }
        }

        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, 'test_env_override_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)

        config_manager = DuckBotConfigManager(config_path, Environment.DEVELOPMENT)
        # Should have debug_mode from environment override
        self.assertTrue(config_manager.config_data.get('debug_mode', False))

    def test_config_export(self):
        """Test configuration export"""
        # Test JSON export
        json_path = os.path.join(self.temp_dir, 'export.json')
        self.config_manager.export_config_json(json_path)
        self.assertTrue(os.path.exists(json_path))

        # Verify exported content
        with open(json_path, 'r') as f:
            exported_data = json.load(f)
        self.assertEqual(exported_data['system']['name'], 'DuckBot Test')

    def test_system_info(self):
        """Test system information generation"""
        info = self.config_manager.get_system_info()
        self.assertIn('environment', info)
        self.assertIn('config_path', info)
        self.assertIn('total_services', info)
        self.assertIn('enabled_services', info)
        self.assertIn('validation_issues', info)

    def test_reserved_ports(self):
        """Test reserved port handling"""
        # Test that reserved ports are properly identified
        self.assertIn(80, self.config_manager.reserved_ports)
        self.assertIn(443, self.config_manager.reserved_ports)

        # Test that is_port_available returns False for reserved ports
        self.assertFalse(self.config_manager._is_port_available(80))
        self.assertFalse(self.config_manager._is_port_available(443))

        # Test that non-reserved ports return True (if not in use)
        self.assertTrue(self.config_manager._is_port_available(9999))

class TestEnvironmentDetection(unittest.TestCase):
    """Test environment detection functionality"""

    def test_environment_from_env_var(self):
        """Test environment detection from environment variable"""
        os.environ['DUCKBOT_ENV'] = 'production'
        config_manager = DuckBotConfigManager()
        self.assertEqual(config_manager.environment, Environment.PRODUCTION)

        # Clean up
        del os.environ['DUCKBOT_ENV']

    def test_local_mode_detection(self):
        """Test local mode detection"""
        os.environ['AI_LOCAL_ONLY_MODE'] = 'true'
        config_manager = DuckBotConfigManager()
        self.assertEqual(config_manager.environment, Environment.LOCAL)

        # Clean up
        del os.environ['AI_LOCAL_ONLY_MODE']

class TestGlobalInstance(unittest.TestCase):
    """Test global configuration manager instance"""

    def setUp(self):
        """Set up test environment"""
        # Reset global instance
        import config.config_manager
        config.config_manager._config_manager = None

    def test_get_config_manager(self):
        """Test global configuration manager getter"""
        cm1 = get_config_manager()
        cm2 = get_config_manager()
        self.assertIs(cm1, cm2)

    def test_initialize_config(self):
        """Test configuration initialization"""
        cm = initialize_config()
        self.assertIsNotNone(cm)
        self.assertIsInstance(cm, DuckBotConfigManager)

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""

    def setUp(self):
        """Set up test environment"""
        # Create a realistic test configuration
        self.test_config = {
            'system': {
                'name': 'DuckBot Integration Test',
                'version': '4.2-test',
                'log_level': 'INFO'
            },
            'services': {
                'webui': {
                    'name': 'Enhanced WebUI',
                    'enabled': True,
                    'default_host': '127.0.0.1',
                    'default_port': 8787,
                    'startup_script': 'duckbot.enhanced_webui',
                    'environment_vars': {
                        'DUCKBOT_WEBUI_PORT': '{port}',
                        'DUCKBOT_WEBUI_HOST': '{host}'
                    }
                },
                'monitoring': {
                    'name': 'System Monitoring',
                    'enabled': True,
                    'default_host': '127.0.0.1',
                    'default_port': 8789,
                    'startup_script': 'ai_ecosystem_manager',
                    'environment_vars': {
                        'HOST': '{host}',
                        'PORT': '{port}'
                    }
                },
                'lm_studio': {
                    'name': 'LM Studio',
                    'enabled': True,
                    'default_host': '127.0.0.1',
                    'default_port': 1234,
                    'external_service': True,
                    'health_endpoint': '/v1/models'
                }
            },
            'features': {
                'webui_enabled': True,
                'monitoring_enabled': True,
                'local_ai_enabled': True,
                'cloud_ai_enabled': False
            },
            'ports': {
                'reserved_ports': [80, 443, 22],
                'webui_range': [8780, 8799]
            }
        }

        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'integration_config.yaml')
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_service_startup_simulation(self):
        """Test simulated service startup scenario"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Simulate starting services
        services = config_manager.get_enabled_services()
        started_services = []

        for service_name, service in services.items():
            if not service.external_service:
                # Allocate port
                port = config_manager.allocate_port(service_name)
                service.current_port = port

                # Get environment variables
                env_vars = config_manager.get_service_environment(service_name)

                # Update status
                config_manager.update_service_status(service_name, ServiceStatus.RUNNING)
                started_services.append(service_name)

        # Verify all services started
        self.assertEqual(len(started_services), 2)  # webui and monitoring
        self.assertEqual(config_manager.services['webui'].status, ServiceStatus.RUNNING)
        self.assertEqual(config_manager.services['monitoring'].status, ServiceStatus.RUNNING)

    def test_port_allocation_range(self):
        """Test port allocation within specified ranges"""
        config_manager = DuckBotConfigManager(self.config_path)

        # Allocate ports for multiple services
        port1 = config_manager.allocate_port('webui')
        port2 = config_manager.allocate_port('monitoring')

        # Verify ports are in correct range
        self.assertGreaterEqual(port1, 8780)
        self.assertLessEqual(port1, 8799)
        self.assertGreaterEqual(port2, 8780)
        self.assertLessEqual(port2, 8799)

        # Verify ports are different
        self.assertNotEqual(port1, port2)

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDuckBotConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalInstance))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
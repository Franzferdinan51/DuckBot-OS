#!/usr/bin/env python3
"""
DuckBot WebSocket Configuration Test Suite
Comprehensive testing of WebSocket server configuration, port allocation, and service coordination
"""

import asyncio
import json
import logging
import sys
import os
import time
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
try:
    from config.port_allocation import DuckBotPortAllocator, DUCKBOT_WEBSOCKET_MCP_PORT, DUCKBOT_WEBSOCKET_CHAT_PORT, DUCKBOT_MCP_SERVER_PORT
    from simple_websocket_server import DuckBotWebSocketServer
    from websocket_health_monitor import WebSocketHealthMonitor
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    IMPORTS_AVAILABLE = False
    # Set fallback values
    DUCKBOT_WEBSOCKET_MCP_PORT = 8791
    DUCKBOT_WEBSOCKET_CHAT_PORT = 8792
    DUCKBOT_MCP_SERVER_PORT = 8794

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortAllocationTests(unittest.TestCase):
    """Test port allocation strategy"""

    def setUp(self):
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        self.allocator = DuckBotPortAllocator()

    def test_port_allocator_initialization(self):
        """Test that port allocator initializes correctly"""
        self.assertIsInstance(self.allocator, DuckBotPortAllocator)
        self.assertGreater(len(self.allocator.SERVICE_PORTS), 0)

    def test_service_port_allocation(self):
        """Test that service ports are allocated correctly"""
        mcp_port = self.allocator.get_service_port("websocket_mcp")
        chat_port = self.allocator.get_service_port("websocket_chat")
        mcp_server_port = self.allocator.get_service_port("mcp_server")

        self.assertEqual(mcp_port, DUCKBOT_WEBSOCKET_MCP_PORT)
        self.assertEqual(chat_port, DUCKBOT_WEBSOCKET_CHAT_PORT)
        self.assertEqual(mcp_server_port, DUCKBOT_MCP_SERVER_PORT)

    def test_port_conflict_detection(self):
        """Test that port conflicts are detected"""
        # This would normally check for conflicts, but we'll test the logic
        allocations = self.allocator.get_port_allocations()
        port_counts = {}

        for service, port in allocations.items():
            port_counts[port] = port_counts.get(port, 0) + 1

        # Check for conflicts (ports used by multiple services)
        conflicts = [port for port, count in port_counts.items() if count > 1]
        self.assertEqual(len(conflicts), 0, f"Port conflicts detected: {conflicts}")

    def test_port_availability_check(self):
        """Test port availability checking"""
        # Test with a known available port (hopefully)
        test_port = 9999  # Unlikely to be in use
        self.assertTrue(self.allocator._is_port_available(test_port))

        # Test with a known unavailable port (loopback)
        self.assertFalse(self.allocator._is_port_available(0))  # Invalid port

class WebSocketServerTests(unittest.TestCase):
    """Test WebSocket server functionality"""

    def setUp(self):
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        self.server = DuckBotWebSocketServer()

    def test_server_initialization(self):
        """Test WebSocket server initialization"""
        self.assertIsNotNone(self.server.mcp_port)
        self.assertIsNotNone(self.server.chat_port)
        self.assertNotEqual(self.server.mcp_port, self.server.chat_port)
        self.assertEqual(len(self.server.mcp_clients), 0)
        self.assertEqual(len(self.server.chat_clients), 0)

    def test_port_validation(self):
        """Test port validation logic"""
        # Test with same ports (should fail)
        server_conflict = DuckBotWebSocketServer(mcp_port=8000, chat_port=8000)
        self.assertGreater(len(server_conflict.startup_errors), 0)
        self.assertTrue(any("cannot be the same" in error for error in server_conflict.startup_errors))

    def test_health_check_methods(self):
        """Test health check functionality"""
        health = asyncio.run(self.server.check_service_health())
        self.assertIn("mcp_clients", health)
        self.assertIn("chat_clients", health)
        self.assertIn("mcp_port", health)
        self.assertIn("chat_port", health)

class HealthMonitorTests(unittest.TestCase):
    """Test health monitoring functionality"""

    def setUp(self):
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        self.monitor = WebSocketHealthMonitor()

    def test_monitor_initialization(self):
        """Test health monitor initialization"""
        self.assertIn("mcp_websocket", self.monitor.websocket_services)
        self.assertIn("chat_websocket", self.monitor.websocket_services)
        self.assertIn("mcp_server", self.monitor.http_services)
        self.assertIn("webui", self.monitor.http_services)

    def test_health_summary_generation(self):
        """Test health summary generation"""
        summary = self.monitor.get_health_summary()
        self.assertIn("timestamp", summary)
        self.assertIn("total_services", summary)
        self.assertIn("healthy_services", summary)
        self.assertIn("services", summary)

class IntegrationTests(unittest.TestCase):
    """Integration tests for the entire system"""

    def setUp(self):
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")

    def test_port_range_configuration(self):
        """Test that ports are in appropriate ranges"""
        allocator = DuckBotPortAllocator()

        # Check that WebSocket services are in WebSocket range
        websocket_range = allocator.PORT_RANGES["websocket"]
        mcp_port = allocator.get_service_port("websocket_mcp")
        chat_port = allocator.get_service_port("websocket_chat")

        self.assertTrue(websocket_range.start <= mcp_port <= websocket_range.end)
        self.assertTrue(websocket_range.start <= chat_port <= websocket_range.end)

    def test_service_url_generation(self):
        """Test service URL generation"""
        allocator = DuckBotPortAllocator()

        mcp_url = allocator.get_service_url("websocket_mcp")
        chat_url = allocator.get_service_url("websocket_chat")
        webui_url = allocator.get_service_url("webui")

        self.assertTrue(mcp_url.startswith("ws://"))
        self.assertTrue(chat_url.startswith("ws://"))
        self.assertTrue(webui_url.startswith("http://"))

    def test_environment_variable_override(self):
        """Test environment variable port override"""
        # Test with environment variable set
        test_port = 9999
        os.environ["DUCKBOT_WEBSOCKET_MCP_PORT"] = str(test_port)

        # Re-import to test override
        import importlib
        if 'config.port_allocation' in sys.modules:
            importlib.reload(sys.modules['config.port_allocation'])

        from config.port_allocation import get_port_from_env
        overridden_port = get_port_from_env("websocket_mcp", 8791)
        self.assertEqual(overridden_port, test_port)

        # Clean up
        del os.environ["DUCKBOT_WEBSOCKET_MCP_PORT"]

class NetworkTests(unittest.TestCase):
    """Network connectivity and port availability tests"""

    def test_port_availability_system_check(self):
        """Test system port availability"""
        def is_port_available(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    result = s.connect_ex(('localhost', port))
                    return result != 0
            except:
                return False

        # Test our default ports
        ports_to_test = [
            DUCKBOT_WEBSOCKET_MCP_PORT,
            DUCKBOT_WEBSOCKET_CHAT_PORT,
            DUCKBOT_MCP_SERVER_PORT,
            8787,  # WebUI
            8789,  # Monitoring
            3000,  # React dev
        ]

        port_status = {}
        for port in ports_to_test:
            port_status[port] = is_port_available(port)

        # Log results
        logger.info("Port availability check:")
        for port, available in port_status.items():
            status = "available" if available else "in use"
            logger.info(f"  Port {port}: {status}")

        # This test doesn't assert, just provides diagnostic info

    def test_websocket_libraries_available(self):
        """Test that required WebSocket libraries are available"""
        try:
            import websockets
            logger.info(f"websockets library available: {websockets.__version__}")
        except ImportError:
            self.fail("websockets library not available")

        try:
            import aiohttp
            logger.info(f"aiohttp library available: {aiohttp.__version__}")
        except ImportError:
            self.fail("aiohttp library not available")

class PerformanceTests(unittest.TestCase):
    """Performance and load tests"""

    def test_port_allocation_performance(self):
        """Test port allocation performance"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")

        allocator = DuckBotPortAllocator()
        start_time = time.time()

        # Allocate all ports
        allocations = allocator.get_port_allocations()

        end_time = time.time()
        allocation_time = end_time - start_time

        logger.info(f"Port allocation took {allocation_time:.4f} seconds for {len(allocations)} services")
        self.assertLess(allocation_time, 1.0, "Port allocation should be fast")

    def test_health_check_simulation(self):
        """Simulate health check performance"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")

        monitor = WebSocketHealthMonitor()
        start_time = time.time()

        # Simulate health checks (without actual network calls)
        for _ in range(10):
            # Just update timestamps to simulate work
            for service in monitor.websocket_services.values():
                service.last_check = time.time()

        end_time = time.time()
        simulation_time = end_time - start_time

        logger.info(f"Health check simulation took {simulation_time:.4f} seconds")
        self.assertLess(simulation_time, 0.1, "Health check simulation should be fast")

class ConfigurationValidationTests(unittest.TestCase):
    """Validate configuration files and settings"""

    def test_config_file_exists(self):
        """Test that configuration files exist"""
        config_files = [
            "config/port_allocation.py",
            "simple_websocket_server.py",
            "start_mcp_server.py",
            "websocket_health_monitor.py",
        ]

        for config_file in config_files:
            file_path = project_root / config_file
            self.assertTrue(file_path.exists(), f"Config file {config_file} should exist")

    def test_configuration_syntax(self):
        """Test that configuration files have valid syntax"""
        config_files = [
            "config/port_allocation.py",
            "simple_websocket_server.py",
            "start_mcp_server.py",
            "websocket_health_monitor.py",
        ]

        for config_file in config_files:
            file_path = project_root / config_file
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), str(file_path), 'exec')
            except SyntaxError as e:
                self.fail(f"Syntax error in {config_file}: {e}")

async def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("=== DuckBot WebSocket Configuration Test Suite ===")
    print()

    # Run the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        PortAllocationTests,
        WebSocketServerTests,
        HealthMonitorTests,
        IntegrationTests,
        NetworkTests,
        PerformanceTests,
        ConfigurationValidationTests,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=== Test Summary ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")

    return success

async def run_integration_test():
    """Run integration test with actual service startup"""
    print("\n=== Integration Test: Service Coordination ===")

    # Test port allocation
    allocator = DuckBotPortAllocator()
    allocations = allocator.get_port_allocations()

    print("Port allocations:")
    for service, port in sorted(allocations.items()):
        service_info = allocator.SERVICE_PORTS.get(service)
        if service_info:
            print(f"  {service_info.description:25} : {port:>5} ({service_info.protocol})")

    # Test service URL generation
    print("\nService URLs:")
    test_services = ["websocket_mcp", "websocket_chat", "webui", "mcp_server"]
    for service in test_services:
        url = allocator.get_service_url(service)
        if url:
            print(f"  {service:15} : {url}")

    # Test WebSocket server initialization
    print("\nTesting WebSocket server initialization...")
    try:
        server = DuckBotWebSocketServer()
        print(f"✅ WebSocket server initialized")
        print(f"   MCP port: {server.mcp_port}")
        print(f"   Chat port: {server.chat_port}")
        print(f"   Startup errors: {len(server.startup_errors)}")

        if server.startup_errors:
            print("   Errors:")
            for error in server.startup_errors:
                print(f"     - {error}")

    except Exception as e:
        print(f"❌ WebSocket server initialization failed: {e}")

    # Test health monitor initialization
    print("\nTesting health monitor initialization...")
    try:
        monitor = WebSocketHealthMonitor()
        summary = monitor.get_health_summary()
        print(f"✅ Health monitor initialized")
        print(f"   Services monitored: {summary['total_services']}")
        print(f"   Current health: {summary['health_percentage']:.1f}%")
    except Exception as e:
        print(f"❌ Health monitor initialization failed: {e}")

    print("\n✅ Integration test completed")

async def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(description='DuckBot WebSocket Configuration Test Suite')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration test only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.all or not (args.unit or args.integration):
        # Run comprehensive test suite
        success = await run_comprehensive_test()

    if args.integration or args.all:
        # Run integration test
        await run_integration_test()

    if not args.unit and not args.integration and not args.all:
        print("No test specified. Use --unit, --integration, or --all")

if __name__ == "__main__":
    asyncio.run(main())
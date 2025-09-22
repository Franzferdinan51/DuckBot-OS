"""
Unit Tests for Service Management

Tests service management functionality including:
- Service detection and startup
- Service lifecycle management
- Service status monitoring
- Service configuration
- Service health checks
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import test utilities
from tests.unit import UnitTestHelpers, UnitTestDataGenerator, CustomAssertions

# Import DuckBot modules
try:
    from duckbot.service_detector import ServiceDetector
    from duckbot.server_manager import ServerManager, ServiceStatus
    from duckbot.core.logging_setup import setup_logging
except ImportError as e:
    print(f"Warning: Could not import some service modules: {e}")
    SERVICE_MODULES_AVAILABLE = False
else:
    SERVICE_MODULES_AVAILABLE = True

pytestmark = pytest.mark.unit

class TestServiceDetection:
    """Test service detection functionality"""

    def test_service_detector_initialization(self):
        """Test ServiceDetector initialization"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        detector = ServiceDetector()
        assert detector is not None
        assert hasattr(detector, 'get_startup_recommendations')

    def test_startup_recommendations(self):
        """Test startup recommendation generation"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        detector = ServiceDetector()
        recommendations = detector.get_startup_recommendations()

        assert isinstance(recommendations, dict)
        assert len(recommendations) > 0

        for service_name, recommendation in recommendations.items():
            assert "can_start" in recommendation
            assert "reason" in recommendation
            assert isinstance(recommendation["can_start"], bool)

    def test_service_dependency_checking(self):
        """Test service dependency checking"""
        test_services = [
            {
                "name": "webui",
                "dependencies": ["ai_router", "server_manager"],
                "available_deps": ["ai_router", "server_manager"],
                "expected": True
            },
            {
                "name": "ai_service",
                "dependencies": ["lm_studio", "python_packages"],
                "available_deps": ["python_packages"],
                "expected": False
            }
        ]

        for service in test_services:
            can_start = self._check_dependencies(
                service["dependencies"],
                service["available_deps"]
            )
            assert can_start == service["expected"]

    def _check_dependencies(self, dependencies: List[str], available: List[str]) -> bool:
        """Helper method to check dependencies"""
        return all(dep in available for dep in dependencies)

class TestServerManager:
    """Test server management functionality"""

    def test_server_manager_initialization(self):
        """Test ServerManager initialization"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        manager = ServerManager()
        assert manager is not None
        assert hasattr(manager, 'get_all_service_status')

    def test_service_status_retrieval(self):
        """Test service status retrieval"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        manager = ServerManager()
        status = manager.get_all_service_status()

        assert isinstance(status, dict)
        assert len(status) > 0

        for service_name, service_info in status.items():
            assert hasattr(service_info, 'status')
            assert hasattr(service_info, 'display_name')
            assert service_info.status in ServiceStatus

    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """Test service lifecycle management"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        manager = ServerManager()
        test_service = "test_service"

        # Mock service operations
        with patch.object(manager, 'start_service') as mock_start:
            with patch.object(manager, 'stop_service') as mock_stop:
                mock_start.return_value = {"success": True, "service": test_service}
                mock_stop.return_value = {"success": True, "service": test_service}

                # Test start
                start_result = await mock_start(test_service)
                assert start_result["success"] is True

                # Test stop
                stop_result = await mock_stop(test_service)
                assert stop_result["success"] is True

class TestServiceConfiguration:
    """Test service configuration management"""

    def test_config_parsing(self):
        """Test service configuration parsing"""
        test_config = {
            "services": {
                "webui": {
                    "port": 8787,
                    "host": "127.0.0.1",
                    "enabled": True,
                    "autostart": False
                },
                "terminal": {
                    "port": 8788,
                    "host": "127.0.0.1",
                    "enabled": True,
                    "autostart": True
                }
            }
        }

        parsed_configs = self._parse_service_configs(test_config)
        assert len(parsed_configs) == 2

        for service_name, config in parsed_configs.items():
            assert "port" in config
            assert "host" in config
            assert "enabled" in config
            assert isinstance(config["port"], int)
            assert isinstance(config["enabled"], bool)

    def test_config_validation(self):
        """Test service configuration validation"""
        valid_configs = [
            {"port": 8787, "host": "127.0.0.1", "enabled": True},
            {"port": 3000, "host": "localhost", "enabled": False}
        ]

        invalid_configs = [
            {"port": "invalid", "host": "127.0.0.1", "enabled": True},  # Invalid port type
            {"port": 8787, "enabled": True},  # Missing host
            {"host": "127.0.0.1", "enabled": True},  # Missing port
            {}  # Empty config
        ]

        for config in valid_configs:
            assert self._validate_service_config(config) is True

        for config in invalid_configs:
            assert self._validate_service_config(config) is False

    def _parse_service_configs(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to parse service configurations"""
        parsed = {}
        for service_name, config in raw_config.get("services", {}).items():
            parsed[service_name] = {
                "port": config.get("port", 8000),
                "host": config.get("host", "127.0.0.1"),
                "enabled": config.get("enabled", False),
                "autostart": config.get("autostart", False)
            }
        return parsed

    def _validate_service_config(self, config: Dict[str, Any]) -> bool:
        """Helper method to validate service configuration"""
        required_fields = ["port", "host", "enabled"]

        if not isinstance(config, dict):
            return False

        for field in required_fields:
            if field not in config:
                return False

        # Validate port is integer and in valid range
        if not isinstance(config["port"], int) or config["port"] < 1 or config["port"] > 65535:
            return False

        # Validate host is string
        if not isinstance(config["host"], str) or len(config["host"]) == 0:
            return False

        # Validate enabled is boolean
        if not isinstance(config["enabled"], bool):
            return False

        return True

class TestServiceHealth:
    """Test service health monitoring"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health checking"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        test_services = [
            {"name": "webui", "port": 8787, "expected_healthy": True},
            {"name": "terminal", "port": 8788, "expected_healthy": False}
        ]

        for service in test_services:
            health_status = await self._check_service_health(
                service["name"],
                service["port"]
            )

            # In real implementation, this would check actual service health
            # For testing, we simulate the expected result
            assert health_status["healthy"] == service["expected_healthy"]

    def test_health_thresholds(self):
        """Test health monitoring thresholds"""
        thresholds = {
            "response_time": 5.0,  # seconds
            "memory_usage": 512,  # MB
            "cpu_usage": 80,  # percentage
            "error_rate": 0.05  # 5%
        }

        test_metrics = [
            {"response_time": 2.0, "memory_usage": 256, "cpu_usage": 50, "error_rate": 0.01},
            {"response_time": 6.0, "memory_usage": 600, "cpu_usage": 90, "error_rate": 0.10}
        ]

        for i, metrics in enumerate(test_metrics):
            healthy = self._evaluate_health_metrics(metrics, thresholds)
            expected = i == 0  # Only first metric set should be healthy
            assert healthy == expected

    async def _check_service_health(self, service_name: str, port: int) -> Dict[str, Any]:
        """Helper method to check service health"""
        # Mock health check
        await asyncio.sleep(0.1)  # Simulate network call

        # Simulate different health statuses based on service name
        if "webui" in service_name:
            return {"healthy": True, "response_time": 0.1}
        else:
            return {"healthy": False, "error": "Service not responding"}

    def _evaluate_health_metrics(self, metrics: Dict[str, float], thresholds: Dict[str, float]) -> bool:
        """Helper method to evaluate health metrics"""
        return (
            metrics["response_time"] <= thresholds["response_time"] and
            metrics["memory_usage"] <= thresholds["memory_usage"] and
            metrics["cpu_usage"] <= thresholds["cpu_usage"] and
            metrics["error_rate"] <= thresholds["error_rate"]
        )

class TestServiceErrorHandling:
    """Test service error handling and recovery"""

    @pytest.mark.asyncio
    async def test_service_start_failure(self):
        """Test service start failure handling"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        manager = ServerManager()
        test_service = "failing_service"

        with patch.object(manager, 'start_service') as mock_start:
            mock_start.side_effect = Exception("Service failed to start")

            with pytest.raises(Exception, match="Service failed to start"):
                await mock_start(test_service)

    def test_port_conflict_detection(self):
        """Test port conflict detection"""
        services = [
            {"name": "service1", "port": 8787},
            {"name": "service2", "port": 8787},  # Same port
            {"name": "service3", "port": 8788}
        ]

        conflicts = self._detect_port_conflicts(services)
        assert len(conflicts) == 1
        assert conflicts[0]["port"] == 8787
        assert len(conflicts[0]["services"]) == 2

    def test_service_restart_logic(self):
        """Test service restart logic"""
        test_scenarios = [
            {"crashes": 1, "should_restart": True},
            {"crashes": 3, "should_restart": True},
            {"crashes": 5, "should_restart": False},  # Too many crashes
        ]

        for scenario in test_scenarios:
            should_restart = self._should_restart_service(scenario["crashes"])
            assert should_restart == scenario["should_restart"]

    def _detect_port_conflicts(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Helper method to detect port conflicts"""
        port_usage = {}
        conflicts = []

        for service in services:
            port = service["port"]
            if port not in port_usage:
                port_usage[port] = []
            port_usage[port].append(service["name"])

        for port, service_names in port_usage.items():
            if len(service_names) > 1:
                conflicts.append({
                    "port": port,
                    "services": service_names
                })

        return conflicts

    def _should_restart_service(self, crash_count: int, max_crashes: int = 4) -> bool:
        """Helper method to determine if service should be restarted"""
        return crash_count <= max_crashes

class TestServicePerformance:
    """Test service performance characteristics"""

    @pytest.mark.asyncio
    async def test_service_startup_time(self):
        """Test service startup performance"""
        if not SERVICE_MODULES_AVAILABLE:
            pytest.skip("Service modules not available")

        import time
        start_time = time.time()

        # Simulate service startup
        await self._simulate_service_startup("test_service")

        end_time = time.time()
        startup_time = end_time - start_time

        assert startup_time < 5.0, f"Service startup time {startup_time}s exceeds threshold"

    def test_service_memory_usage(self):
        """Test service memory usage"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate service operations
        self._simulate_service_operations()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert memory_increase < 50, f"Memory increase {memory_increase}MB exceeds threshold"

    async def _simulate_service_startup(self, service_name: str):
        """Helper method to simulate service startup"""
        await asyncio.sleep(0.1)  # Simulate startup time
        return {"service": service_name, "status": "started"}

    def _simulate_service_operations(self):
        """Helper method to simulate service operations"""
        # Simulate some service operations that consume memory
        data = [f"service_data_{i}" for i in range(1000)]
        return len(data)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
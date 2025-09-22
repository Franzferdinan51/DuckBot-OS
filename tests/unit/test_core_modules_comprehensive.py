#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for DuckBot v4.2 Core Modules
Tests all core functionality with proper mocking and isolation
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, Mock
import json
import tempfile
import shutil
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import TestUtils

# Import core modules
try:
    from duckbot.core.ai_provider_manager import UnifiedAIProviderManager, UnifiedModelSpec
    from duckbot.core.service_manager import ServiceManager
    from duckbot.core.dynamic_model_manager import DynamicModelManager, ModelSpec
    from duckbot.core.hardware_detector import HardwareDetector
    from duckbot.core.cost_management import CostManager
    from duckbot.core.rate_limit import RateLimiter
    from duckbot.core.logging_setup import setup_logging
    from duckbot.core.utilities import consolidate_utilities
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False


class TestAIProviderManager:
    """Test suite for AI Provider Manager"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_provider_initialization(self, test_config):
        """Test AI provider manager initialization"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        with patch('duckbot.core.ai_provider_manager.DynamicModelManager'):
            manager = UnifiedAIProviderManager()
            assert manager is not None
            assert hasattr(manager, 'providers')
            assert hasattr(manager, 'active_models')

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_routing(self, test_config, mock_ai_provider):
        """Test intelligent model routing based on resource availability"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        with patch('duckbot.core.ai_provider_manager.DynamicModelManager'):
            manager = UnifiedAIProviderManager()
            manager.providers['test'] = mock_ai_provider

            # Test model selection
            model = await manager.select_optimal_model(
                prompt="Test prompt",
                complexity="medium",
                available_memory=4096
            )

            assert model is not None
            assert isinstance(model, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_provider_health_check(self, test_config, mock_ai_provider):
        """Test provider health monitoring"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        with patch('duckbot.core.ai_provider_manager.DynamicModelManager'):
            manager = UnifiedAIProviderManager()
            manager.providers['test'] = mock_ai_provider

            health_status = await manager.check_provider_health('test')
            assert health_status is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cost_tracking(self, test_config):
        """Test API cost tracking functionality"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        with patch('duckbot.core.ai_provider_manager.DynamicModelManager'):
            manager = UnifiedAIProviderManager()

            # Track a request
            manager.track_request_cost(
                provider="openai",
                model="gpt-3.5-turbo",
                tokens_used=1000,
                cost=0.002
            )

            assert manager.total_costs > 0
            assert len(manager.cost_history) > 0


class TestServiceManager:
    """Test suite for Service Manager"""

    @pytest.mark.unit
    def test_service_registration(self, test_config):
        """Test service registration functionality"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = ServiceManager()

        # Register a mock service
        service_info = manager.register_service(
            name="test_service",
            service_type="api",
            endpoint="http://localhost:8080",
            health_check_url="http://localhost:8080/health"
        )

        assert service_info['name'] == "test_service"
        assert service_info['status'] == "registered"
        assert "test_service" in manager.services

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, test_config, mock_http_client):
        """Test service health monitoring"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = ServiceManager()
        manager.register_service("test_service", "api", "http://localhost:8080")

        with patch('aiohttp.ClientSession', return_value=mock_http_client):
            health_status = await manager.check_service_health("test_service")
            assert health_status['status'] == 'healthy'

    @pytest.mark.unit
    def test_service_dependency_resolution(self, test_config):
        """Test service dependency resolution"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = ServiceManager()

        # Register services with dependencies
        manager.register_service("database", "storage", "http://localhost:5432")
        manager.register_service("api", "api", "http://localhost:8080", dependencies=["database"])

        dependencies = manager.resolve_dependencies("api")
        assert "database" in dependencies

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_lifecycle_management(self, test_config):
        """Test service start/stop lifecycle"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = ServiceManager()
        service_name = "test_service"

        # Start service
        start_result = await manager.start_service(service_name)
        assert start_result['status'] in ['starting', 'running']

        # Stop service
        stop_result = await manager.stop_service(service_name)
        assert stop_result['status'] == 'stopped'


class TestDynamicModelManager:
    """Test suite for Dynamic Model Manager"""

    @pytest.mark.unit
    def test_model_registration(self, test_config):
        """Test model registration functionality"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = DynamicModelManager()

        model_spec = ModelSpec(
            name="test_model",
            provider="openai",
            model_id="gpt-3.5-turbo",
            memory_required=2048,
            gpu_required=False,
            max_tokens=4096,
            cost_per_1k_tokens=0.002
        )

        manager.register_model(model_spec)
        assert "test_model" in manager.available_models
        assert manager.available_models["test_model"].name == "test_model"

    @pytest.mark.unit
    def test_model_selection_by_resources(self, test_config):
        """Test model selection based on available resources"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = DynamicModelManager()

        # Register models with different resource requirements
        light_model = ModelSpec("light", "openai", "gpt-3.5-turbo", 1024, False, 2048, 0.001)
        heavy_model = ModelSpec("heavy", "openai", "gpt-4", 8192, True, 8192, 0.03)

        manager.register_model(light_model)
        manager.register_model(heavy_model)

        # Test with limited resources
        selected = manager.select_model_by_resources(available_memory=2048, has_gpu=False)
        assert selected.name == "light"

        # Test with ample resources
        selected = manager.select_model_by_resources(available_memory=16384, has_gpu=True)
        assert selected.name == "heavy"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_loading_unloading(self, test_config):
        """Test dynamic model loading and unloading"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = DynamicModelManager()
        model_spec = ModelSpec("test_model", "openai", "gpt-3.5-turbo", 1024, False, 2048, 0.001)
        manager.register_model(model_spec)

        # Load model
        load_result = await manager.load_model("test_model")
        assert load_result['success'] is True
        assert "test_model" in manager.loaded_models

        # Unload model
        unload_result = await manager.unload_model("test_model")
        assert unload_result['success'] is True
        assert "test_model" not in manager.loaded_models

    @pytest.mark.unit
    def test_memory_management(self, test_config):
        """Test memory management for loaded models"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        manager = DynamicModelManager()
        manager.max_memory_usage = 4096  # 4GB limit

        # Register models
        model1 = ModelSpec("model1", "openai", "gpt-3.5-turbo", 2048, False, 2048, 0.001)
        model2 = ModelSpec("model2", "openai", "gpt-4", 4096, True, 8192, 0.03)

        manager.register_model(model1)
        manager.register_model(model2)

        # Test memory constraint enforcement
        can_load = manager.can_load_model("model2")
        assert can_load is False  # Exceeds memory limit

        can_load = manager.can_load_model("model1")
        assert can_load is True


class TestHardwareDetector:
    """Test suite for Hardware Detector"""

    @pytest.mark.unit
    def test_system_info_detection(self, test_config):
        """Test system information detection"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        detector = HardwareDetector()
        system_info = detector.get_system_info()

        assert isinstance(system_info, dict)
        assert 'cpu' in system_info
        assert 'memory' in system_info
        assert 'gpu' in system_info
        assert 'disk' in system_info

    @pytest.mark.unit
    def test_gpu_detection(self, test_config):
        """Test GPU detection and capabilities"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        detector = HardwareDetector()
        gpu_info = detector.get_gpu_info()

        assert isinstance(gpu_info, list)
        for gpu in gpu_info:
            assert 'name' in gpu
            assert 'memory_total' in gpu
            assert 'compute_capability' in gpu

    @pytest.mark.unit
    def test_resource_monitoring(self, test_config):
        """Test real-time resource monitoring"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        detector = HardwareDetector()
        metrics = detector.get_current_metrics()

        assert isinstance(metrics, dict)
        assert 'cpu_usage_percent' in metrics
        assert 'memory_usage_percent' in metrics
        assert 'gpu_usage_percent' in metrics
        assert 0 <= metrics['cpu_usage_percent'] <= 100

    @pytest.mark.unit
    def test_hardware_recommendations(self, test_config):
        """Test hardware optimization recommendations"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        detector = HardwareDetector()
        recommendations = detector.get_hardware_recommendations()

        assert isinstance(recommendations, dict)
        assert 'optimal_models' in recommendations
        assert 'memory_management' in recommendations
        assert 'performance_tips' in recommendations


class TestCostManager:
    """Test suite for Cost Manager"""

    @pytest.mark.unit
    def test_cost_tracking(self, test_config):
        """Test API cost tracking"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        cost_manager = CostManager()

        # Track different API calls
        cost_manager.track_cost("openai", "gpt-3.5-turbo", 1000, 0.002)
        cost_manager.track_cost("anthropic", "claude-3-sonnet", 2000, 0.015)

        assert cost_manager.get_total_cost() > 0
        assert len(cost_manager.get_cost_history()) == 2

    @pytest.mark.unit
    def test_cost_prediction(self, test_config):
        """Test cost prediction functionality"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        cost_manager = CostManager()

        # Add some historical data
        cost_manager.track_cost("openai", "gpt-3.5-turbo", 1000, 0.002)
        cost_manager.track_cost("openai", "gpt-3.5-turbo", 1500, 0.003)

        # Predict future costs
        prediction = cost_manager.predict_daily_cost(daily_requests=100)
        assert prediction > 0
        assert isinstance(prediction, float)

    @pytest.mark.unit
    def test_budget_management(self, test_config):
        """Test budget management and alerts"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        cost_manager = CostManager(daily_budget=10.0)

        # Track costs within budget
        cost_manager.track_cost("openai", "gpt-3.5-turbo", 5000, 0.01)
        assert cost_manager.is_within_budget() is True

        # Track costs exceeding budget
        cost_manager.track_cost("openai", "gpt-4", 10000, 0.30)
        assert cost_manager.is_within_budget() is False

        alerts = cost_manager.get_budget_alerts()
        assert len(alerts) > 0
        assert "exceeded" in alerts[0].lower()


class TestRateLimiter:
    """Test suite for Rate Limiter"""

    @pytest.mark.unit
    def test_rate_limiting(self, test_config):
        """Test API rate limiting functionality"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        limiter = RateLimiter(max_requests=5, time_window=60)

        # Test within limits
        for i in range(5):
            assert limiter.can_make_request("test_user") is True
            limiter.record_request("test_user")

        # Test exceeding limits
        assert limiter.can_make_request("test_user") is False

    @pytest.mark.unit
    def test_sliding_window(self, test_config):
        """Test sliding window rate limiting"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        limiter = RateLimiter(max_requests=3, time_window=60)

        # Make requests
        for i in range(3):
            limiter.record_request("test_user")

        # Should be blocked
        assert limiter.can_make_request("test_user") is False

        # Wait for window to slide (simulate time passing)
        import time
        time.sleep(0.1)  # Small delay for testing

        # Should still be blocked within window
        assert limiter.can_make_request("test_user") is False

    @pytest.mark.unit
    def test_user_isolation(self, test_config):
        """Test that rate limits are isolated per user"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        limiter = RateLimiter(max_requests=2, time_window=60)

        # User 1 makes requests
        limiter.record_request("user1")
        limiter.record_request("user1")
        assert limiter.can_make_request("user1") is False

        # User 2 should still be able to make requests
        assert limiter.can_make_request("user2") is True


class TestLoggingSetup:
    """Test suite for Logging Setup"""

    @pytest.mark.unit
    def test_logging_configuration(self, test_config):
        """Test logging configuration and setup"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        logger = setup_logging(
            level="INFO",
            format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            log_file=test_config.get("log_file", None)
        )

        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')

    @pytest.mark.unit
    def test_log_rotation(self, test_config, temp_dir):
        """Test log file rotation"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        log_file = Path(temp_dir) / "test.log"
        logger = setup_logging(
            level="INFO",
            log_file=str(log_file),
            max_file_size=1024,  # 1KB for testing
            backup_count=3
        )

        # Log enough data to trigger rotation
        for i in range(100):
            logger.info(f"Test log message {i}" * 10)  # Make messages longer

        # Check if rotation files were created
        log_files = list(Path(temp_dir).glob("test.log*"))
        assert len(log_files) > 0


class TestUtilities:
    """Test suite for Core Utilities"""

    @pytest.mark.unit
    def test_configuration_loading(self, test_config, temp_dir):
        """Test configuration file loading"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        # Create test configuration
        config_data = {
            "test_key": "test_value",
            "nested": {
                "key": "value"
            }
        }

        config_file = Path(temp_dir) / "test_config.json"
        config_file.write_text(json.dumps(config_data))

        # Test loading
        loaded_config = consolidate_utilities.load_config(str(config_file))
        assert loaded_config == config_data

    @pytest.mark.unit
    def test_path_operations(self, test_config, temp_dir):
        """Test file system path operations"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        test_path = Path(temp_dir) / "test_file.txt"
        test_content = "Test content"

        # Test file writing and reading
        consolidate_utilities.write_file(str(test_path), test_content)
        assert test_path.exists()

        read_content = consolidate_utilities.read_file(str(test_path))
        assert read_content == test_content

    @pytest.mark.unit
    def test_error_handling(self, test_config):
        """Test centralized error handling"""
        if not CORE_MODULES_AVAILABLE:
            pytest.skip("Core modules not available")

        # Test error logging
        try:
            raise ValueError("Test error for logging")
        except Exception as e:
            error_info = consolidate_utilities.handle_error(e, context="test_context")
            assert error_info['error'] == str(e)
            assert error_info['context'] == "test_context"
            assert 'timestamp' in error_info


# Parameterized tests for multiple scenarios
@pytest.mark.unit
@pytest.mark.parametrize("provider,model,expected_memory", [
    ("openai", "gpt-3.5-turbo", 2048),
    ("anthropic", "claude-3-sonnet", 4096),
    ("local", "llama2-7b", 8192),
])
def test_model_memory_requirements(provider, model, expected_memory):
    """Test model memory requirements across different providers"""
    if not CORE_MODULES_AVAILABLE:
        pytest.skip("Core modules not available")

    model_spec = ModelSpec(
        name=f"test_{provider}_{model}",
        provider=provider,
        model_id=model,
        memory_required=expected_memory,
        gpu_required=False,
        max_tokens=4096,
        cost_per_1k_tokens=0.001
    )

    assert model_spec.memory_required == expected_memory
    assert model_spec.provider == provider


# Performance benchmarks for critical functions
@pytest.mark.unit
@pytest.mark.performance
def test_ai_provider_selection_performance(test_config):
    """Test performance of AI provider selection"""
    if not CORE_MODULES_AVAILABLE:
        pytest.skip("Core modules not available")

    manager = UnifiedAIProviderManager()

    def benchmark_selection():
        return manager.select_optimal_model(
            prompt="Test prompt for benchmarking",
            complexity="medium",
            available_memory=4096
        )

    result, execution_time = TestUtils.measure_execution_time(benchmark_selection)
    assert execution_time < 0.1  # Should complete within 100ms


# Edge case testing
@pytest.mark.unit
def test_error_recovery_mechanisms(test_config):
    """Test error recovery and fallback mechanisms"""
    if not CORE_MODULES_AVAILABLE:
        pytest.skip("Core modules not available")

    manager = ServiceManager()

    # Test service failure recovery
    with patch.object(manager, 'check_service_health', return_value={'status': 'unhealthy'}):
        recovery_action = manager.handle_service_failure("test_service")
        assert recovery_action['action'] in ['restart', 'fallback', 'degrade']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=duckbot.core", "--cov-report=html"])
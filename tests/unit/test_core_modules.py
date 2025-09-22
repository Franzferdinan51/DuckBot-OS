#!/usr/bin/env python3
"""
Unit Tests for DuckBot Core Modules
Comprehensive unit testing for all core functionality
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import json
import time
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import core modules
from duckbot.core.ai_provider_manager import AIProviderManager
from duckbot.core.service_manager import ServiceManager
from duckbot.core.hardware_detector import HardwareDetector
from duckbot.core.cost_management import CostManager
from duckbot.core.logging_setup import setup_logging
from duckbot.core.rate_limit import RateLimiter
from duckbot.core.utilities import (
    validate_config,
    sanitize_input,
    format_timestamp,
    calculate_hash
)

class TestAIProviderManager:
    """Unit tests for AI Provider Manager."""

    @pytest.fixture
    def provider_manager(self):
        """Create AI Provider Manager instance."""
        return AIProviderManager()

    @pytest.mark.unit
    def test_provider_manager_initialization(self, provider_manager):
        """Test provider manager initialization."""
        assert provider_manager is not None
        assert hasattr(provider_manager, 'providers')
        assert hasattr(provider_manager, 'active_provider')

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_provider(self, provider_manager, mock_ai_provider):
        """Test registering a new AI provider."""
        await provider_manager.register_provider("test_provider", mock_ai_provider)
        assert "test_provider" in provider_manager.providers
        assert provider_manager.providers["test_provider"] == mock_ai_provider

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response(self, provider_manager, mock_ai_provider, sample_ai_request):
        """Test generating AI response."""
        await provider_manager.register_provider("openai", mock_ai_provider)
        response = await provider_manager.generate_response(sample_ai_request)
        assert response == "Test response"
        mock_ai_provider.generate_response.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_provider_health_check(self, provider_manager, mock_ai_provider):
        """Test provider health check functionality."""
        await provider_manager.register_provider("test_provider", mock_ai_provider)
        health_status = await provider_manager.check_provider_health("test_provider")
        assert health_status is True
        mock_ai_provider.health_check.assert_called_once()

    @pytest.mark.unit
    def test_provider_switching(self, provider_manager):
        """Test switching between providers."""
        provider_manager.active_provider = "openai"
        provider_manager.switch_provider("anthropic")
        assert provider_manager.active_provider == "anthropic"

class TestServiceManager:
    """Unit tests for Service Manager."""

    @pytest.fixture
    def service_manager(self):
        """Create Service Manager instance."""
        return ServiceManager()

    @pytest.mark.unit
    def test_service_manager_initialization(self, service_manager):
        """Test service manager initialization."""
        assert service_manager is not None
        assert hasattr(service_manager, 'services')
        assert hasattr(service_manager, 'service_status')

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_service(self, service_manager):
        """Test registering a new service."""
        mock_service = MagicMock()
        mock_service.start = AsyncMock()
        mock_service.stop = AsyncMock()
        mock_service.health_check = AsyncMock(return_value=True)

        await service_manager.register_service("test_service", mock_service)
        assert "test_service" in service_manager.services
        assert service_manager.services["test_service"] == mock_service

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_service(self, service_manager):
        """Test starting a service."""
        mock_service = MagicMock()
        mock_service.start = AsyncMock()
        await service_manager.register_service("test_service", mock_service)

        await service_manager.start_service("test_service")
        mock_service.start.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_service(self, service_manager):
        """Test stopping a service."""
        mock_service = MagicMock()
        mock_service.stop = AsyncMock()
        await service_manager.register_service("test_service", mock_service)

        await service_manager.stop_service("test_service")
        mock_service.stop.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, service_manager):
        """Test service health monitoring."""
        mock_service = MagicMock()
        mock_service.health_check = AsyncMock(return_value=True)
        await service_manager.register_service("test_service", mock_service)

        health_status = await service_manager.check_service_health("test_service")
        assert health_status is True
        mock_service.health_check.assert_called_once()

class TestHardwareDetector:
    """Unit tests for Hardware Detector."""

    @pytest.fixture
    def hardware_detector(self):
        """Create Hardware Detector instance."""
        return HardwareDetector()

    @pytest.mark.unit
    def test_hardware_detector_initialization(self, hardware_detector):
        """Test hardware detector initialization."""
        assert hardware_detector is not None
        assert hasattr(hardware_detector, 'system_info')
        assert hasattr(hardware_detector, 'gpu_info')

    @pytest.mark.unit
    def test_detect_cpu_info(self, hardware_detector):
        """Test CPU information detection."""
        cpu_info = hardware_detector.detect_cpu()
        assert 'cores' in cpu_info
        assert 'usage_percent' in cpu_info
        assert isinstance(cpu_info['cores'], int)
        assert isinstance(cpu_info['usage_percent'], (int, float))

    @pytest.mark.unit
    def test_detect_memory_info(self, hardware_detector):
        """Test memory information detection."""
        memory_info = hardware_detector.detect_memory()
        assert 'total_gb' in memory_info
        assert 'available_gb' in memory_info
        assert 'usage_percent' in memory_info
        assert memory_info['total_gb'] > 0
        assert 0 <= memory_info['usage_percent'] <= 100

    @pytest.mark.unit
    def test_detect_gpu_info(self, hardware_detector):
        """Test GPU information detection."""
        gpu_info = hardware_detector.detect_gpu()
        assert isinstance(gpu_info, list)
        if gpu_info:  # If GPU is available
            for gpu in gpu_info:
                assert 'name' in gpu
                assert 'memory_gb' in gpu
                assert 'usage_percent' in gpu

    @pytest.mark.unit
    def test_system_requirements_check(self, hardware_detector):
        """Test system requirements validation."""
        requirements = {
            'min_cpu_cores': 2,
            'min_memory_gb': 4,
            'min_disk_gb': 10
        }
        meets_requirements = hardware_detector.check_system_requirements(requirements)
        assert isinstance(meets_requirements, bool)

class TestCostManager:
    """Unit tests for Cost Manager."""

    @pytest.fixture
    def cost_manager(self):
        """Create Cost Manager instance."""
        return CostManager()

    @pytest.mark.unit
    def test_cost_manager_initialization(self, cost_manager):
        """Test cost manager initialization."""
        assert cost_manager is not None
        assert hasattr(cost_manager, 'usage_data')
        assert hasattr(cost_manager, 'cost_limits')

    @pytest.mark.unit
    def test_track_api_usage(self, cost_manager):
        """Test API usage tracking."""
        cost_manager.track_usage(
            provider="openai",
            model="gpt-3.5-turbo",
            tokens_in=100,
            tokens_out=50,
            cost=0.002
        )
        assert "openai" in cost_manager.usage_data
        assert cost_manager.usage_data["openai"]["total_tokens"] == 150
        assert cost_manager.usage_data["openai"]["total_cost"] == 0.002

    @pytest.mark.unit
    def test_cost_limit_check(self, cost_manager):
        """Test cost limit validation."""
        cost_manager.set_cost_limit("openai", 10.0)
        cost_manager.track_usage("openai", "gpt-3.5-turbo", 1000, 500, 5.0)

        within_limit = cost_manager.check_cost_limit("openai")
        assert within_limit is True

    @pytest.mark.unit
    def test_cost_report_generation(self, cost_manager):
        """Test cost report generation."""
        cost_manager.track_usage("openai", "gpt-3.5-turbo", 1000, 500, 0.01)
        cost_manager.track_usage("anthropic", "claude-3-sonnet", 2000, 1000, 0.02)

        report = cost_manager.generate_cost_report()
        assert "openai" in report
        assert "anthropic" in report
        assert "total_cost" in report
        assert report["total_cost"] == 0.03

class TestLoggingSetup:
    """Unit tests for Logging Setup."""

    @pytest.mark.unit
    def test_logging_configuration(self):
        """Test logging configuration."""
        logger = setup_logging(level="INFO")
        assert logger is not None
        assert logger.level == 20  # INFO level

    @pytest.mark.unit
    def test_log_file_creation(self, temp_dir):
        """Test log file creation."""
        log_file = Path(temp_dir) / "test.log"
        logger = setup_logging(log_file=str(log_file))
        logger.info("Test message")

        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Test message" in log_content

class TestRateLimiter:
    """Unit tests for Rate Limiter."""

    @pytest.fixture
    def rate_limiter(self):
        """Create Rate Limiter instance."""
        return RateLimiter(max_requests=10, time_window=60)

    @pytest.mark.unit
    def test_rate_limiter_initialization(self, rate_limiter):
        """Test rate limiter initialization."""
        assert rate_limiter is not None
        assert rate_limiter.max_requests == 10
        assert rate_limiter.time_window == 60

    @pytest.mark.unit
    def test_allow_request_within_limit(self, rate_limiter):
        """Test request allowance within limits."""
        for i in range(10):
            allowed = rate_limiter.allow_request("test_user")
            assert allowed is True

    @pytest.mark.unit
    def test_deny_request_over_limit(self, rate_limiter):
        """Test request denial over limits."""
        # Use up all requests
        for i in range(10):
            rate_limiter.allow_request("test_user")

        # Next request should be denied
        allowed = rate_limiter.allow_request("test_user")
        assert allowed is False

    @pytest.mark.unit
    def test_rate_limit_reset(self, rate_limiter):
        """Test rate limit reset after time window."""
        # Use up all requests
        for i in range(10):
            rate_limiter.allow_request("test_user")

        # Mock time passage
        with patch('time.time', return_value=time.time() + 61):
            allowed = rate_limiter.allow_request("test_user")
            assert allowed is True

class TestUtilities:
    """Unit tests for utility functions."""

    @pytest.mark.unit
    def test_validate_config_valid(self, sample_config_data):
        """Test configuration validation with valid data."""
        result = validate_config(sample_config_data)
        assert result is True

    @pytest.mark.unit
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid data."""
        invalid_config = {"missing_required_field": "value"}
        result = validate_config(invalid_config)
        assert result is False

    @pytest.mark.unit
    def test_sanitize_input(self):
        """Test input sanitization."""
        malicious_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(malicious_input)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized

    @pytest.mark.unit
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp = 1704067200  # 2024-01-01 00:00:00 UTC
        formatted = format_timestamp(timestamp)
        assert isinstance(formatted, str)
        assert "2024" in formatted

    @pytest.mark.unit
    def test_calculate_hash(self):
        """Test hash calculation."""
        data = "test_string"
        hash_value = calculate_hash(data)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 produces 64 character hex string

class TestErrorHandling:
    """Unit tests for error handling."""

    @pytest.mark.unit
    def test_ai_provider_error_handling(self):
        """Test AI provider error handling."""
        manager = AIProviderManager()

        # Test handling of non-existent provider
        with pytest.raises(ValueError):
            asyncio.run(manager.switch_provider("non_existent_provider"))

    @pytest.mark.unit
    def test_service_manager_error_handling(self):
        """Test service manager error handling."""
        manager = ServiceManager()

        # Test handling of non-existent service
        with pytest.raises(KeyError):
            asyncio.run(manager.start_service("non_existent_service"))

    @pytest.mark.unit
    def test_rate_limiter_error_handling(self):
        """Test rate limiter error handling."""
        limiter = RateLimiter(max_requests=10, time_window=60)

        # Test handling of invalid parameters
        with pytest.raises(ValueError):
            RateLimiter(max_requests=0, time_window=60)

        with pytest.raises(ValueError):
            RateLimiter(max_requests=10, time_window=0)

# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests for core modules."""

    @pytest.mark.unit
    @pytest.mark.performance
    def test_ai_response_time_benchmark(self, provider_manager, mock_ai_provider, sample_ai_request):
        """Test AI response time performance."""
        async def benchmark():
            await provider_manager.register_provider("openai", mock_ai_provider)
            start_time = time.time()
            await provider_manager.generate_response(sample_ai_request)
            return time.time() - start_time

        execution_time = asyncio.run(benchmark())
        assert execution_time < 1.0  # Should complete within 1 second

    @pytest.mark.unit
    @pytest.mark.performance
    def test_hardware_detection_performance(self, hardware_detector):
        """Test hardware detection performance."""
        start_time = time.time()
        hardware_detector.detect_all()
        execution_time = time.time() - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.unit
    @pytest.mark.performance
    def test_cost_tracking_performance(self, cost_manager):
        """Test cost tracking performance."""
        start_time = time.time()
        for i in range(1000):
            cost_manager.track_usage("openai", "gpt-3.5-turbo", 100, 50, 0.001)
        execution_time = time.time() - start_time
        assert execution_time < 1.0  # Should complete within 1 second for 1000 operations

# Edge case testing
class TestEdgeCases:
    """Edge case testing for core modules."""

    @pytest.mark.unit
    def test_empty_config_validation(self):
        """Test validation with empty configuration."""
        result = validate_config({})
        assert result is False

    @pytest.mark.unit
    def test_large_input_sanitization(self):
        """Test sanitization of very large input."""
        large_input = "A" * 1000000  # 1MB of data
        sanitized = sanitize_input(large_input)
        assert len(sanitized) == len(large_input)

    @pytest.mark.unit
    def test_unicode_input_handling(self):
        """Test handling of Unicode input."""
        unicode_input = "测试文本 𝄞 𝄢 𝄡 🦆"
        sanitized = sanitize_input(unicode_input)
        assert isinstance(sanitized, str)

    @pytest.mark.unit
    def test_concurrent_rate_limiting(self):
        """Test rate limiting under concurrent access."""
        limiter = RateLimiter(max_requests=5, time_window=60)

        async def make_requests():
            results = []
            for i in range(10):
                results.append(limiter.allow_request("concurrent_user"))
            return results

        # Run multiple concurrent requests
        tasks = [make_requests() for _ in range(3)]
        results = asyncio.run(asyncio.gather(*tasks))

        # Flatten results
        all_results = [item for sublist in results for item in sublist]

        # Some requests should be denied due to rate limiting
        assert False in all_results
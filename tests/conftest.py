#!/usr/bin/env python3
"""
DuckBot v4.2 Comprehensive Testing Framework
Main test configuration and fixtures for all testing types
"""

import pytest
import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, Optional
from unittest.mock import MagicMock, AsyncMock
import json
import sqlite3
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "database_url": "sqlite:///:memory:",
    "api_base_url": "http://localhost:8787",
    "test_timeout": 30,
    "max_retries": 3,
    "mock_external_services": True,
    "coverage_threshold": 0.80,
    "performance_thresholds": {
        "api_response_time": 2.0,
        "memory_usage_mb": 512,
        "cpu_usage_percent": 80
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return TEST_CONFIG.copy()

@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing."""
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value="Test response")
    mock_provider.get_model_info = MagicMock(return_value={
        "name": "test-model",
        "context_length": 4096,
        "supports_streaming": True
    })
    mock_provider.health_check = AsyncMock(return_value=True)
    return mock_provider

@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "ai_providers": {
            "openai": {
                "api_key": "test_key",
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1"
            },
            "anthropic": {
                "api_key": "test_key",
                "model": "claude-3-sonnet-20240229"
            }
        },
        "system_settings": {
            "max_concurrent_requests": 5,
            "timeout": 30,
            "retry_attempts": 3
        },
        "features": {
            "enable_voice": True,
            "enable_video": False,
            "enable_desktop_automation": True
        }
    }

@pytest.fixture
def sample_ai_request():
    """Sample AI request for testing."""
    return {
        "prompt": "Test prompt for AI processing",
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }

@pytest.fixture
def sample_user_message():
    """Sample user message for testing."""
    return {
        "content": "Hello, I need help with testing",
        "timestamp": "2024-01-01T12:00:00Z",
        "user_id": "test_user_123",
        "session_id": "test_session_456"
    }

@pytest.fixture
def sample_system_metrics():
    """Sample system metrics for testing."""
    return {
        "cpu_usage": 45.2,
        "memory_usage": 2048,
        "disk_usage": 75.5,
        "network_usage": 125.3,
        "gpu_usage": 30.0,
        "temperature": 65.0
    }

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    mock_ws = MagicMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=json.dumps({"type": "response", "data": "test"}))
    mock_ws.close = AsyncMock()
    return mock_ws

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"status": "ok"}))
    mock_client.post = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"result": "success"}))
    mock_client.put = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"updated": True}))
    mock_client.delete = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"deleted": True}))
    return mock_client

@pytest.fixture
def security_test_data():
    """Security testing data fixtures."""
    return {
        "malicious_input": "<script>alert('xss')</script>",
        "sql_injection": "SELECT * FROM users WHERE id = '1' OR '1'='1'",
        "command_injection": "rm -rf /; cat /etc/passwd",
        "large_payload": "A" * 10000,
        "unicode_test": "测试文本 𝄞 𝄢 𝄡 🦆",
        "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    }

@pytest.fixture
def performance_test_config():
    """Performance testing configuration."""
    return {
        "concurrent_users": [1, 10, 50, 100],
        "request_duration": 60,
        "ramp_up_period": 30,
        "think_time": 1,
        "max_response_time": 5.0,
        "success_rate_threshold": 0.95
    }

@pytest.fixture
def integration_test_services():
    """Integration testing services configuration."""
    return {
        "discord_bot": {"port": 8788, "token": "test_token"},
        "webui": {"port": 8787, "host": "localhost"},
        "ai_service": {"port": 8789, "endpoints": ["/chat", "/models", "/health"]},
        "database": {"url": "sqlite:///:memory:", "tables": ["users", "sessions", "logs"]},
        "cache": {"type": "memory", "ttl": 3600}
    }

# Test utilities
class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def create_test_files(directory: Path, files: Dict[str, str]) -> None:
        """Create test files with given content."""
        directory.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            (directory / filename).write_text(content)

    @staticmethod
    def assert_response_structure(response: Dict[str, Any], required_fields: list) -> None:
        """Assert response has required structure."""
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> tuple:
        """Measure execution time of a function."""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    @staticmethod
    async def measure_async_execution_time(func, *args, **kwargs) -> tuple:
        """Measure execution time of an async function."""
        import time
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "mocked: marks tests that use mocking"
    )

# Test hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add markers based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add slow marker for tests that might take longer
        if "performance" in str(item.fspath) or "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.slow)

        # Add mocked marker for tests using mocking
        if "mock" in item.name or "Mock" in str(item.fspath):
            item.add_marker(pytest.mark.mocked)
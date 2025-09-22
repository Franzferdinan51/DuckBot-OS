"""
Unit Tests for DuckBot v4.2

This package contains comprehensive unit tests for all DuckBot components.
Unit tests focus on individual components in isolation with mocked dependencies.

Test Categories:
- Core AI components
- Service management
- WebUI components
- Integration modules
- Database operations
- Configuration management
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Unit test configuration
UNIT_TEST_CONFIG = {
    "mock_external_services": True,
    "use_test_database": True,
    "timeout": 10,
    "max_retries": 3
}

# Test utilities
class UnitTestHelpers:
    """Helper utilities for unit tests"""

    @staticmethod
    def create_mock_service(name: str, port: int = 8000) -> Mock:
        """Create a mock service with standard interface"""
        mock_service = Mock()
        mock_service.name = name
        mock_service.port = port
        mock_service.status = Mock()
        mock_service.status.value = "stopped"
        mock_service.start = Mock()
        mock_service.stop = Mock()
        mock_service.restart = Mock()
        mock_service.get_status = Mock(return_value="stopped")
        return mock_service

    @staticmethod
    def create_mock_ai_model(name: str, capabilities: List[str] = None) -> Mock:
        """Create a mock AI model"""
        mock_model = Mock()
        mock_model.name = name
        mock_model.capabilities = capabilities or ["text", "code", "analysis"]
        mock_model.generate = Mock(return_value="Mock AI response")
        mock_model.is_available = Mock(return_value=True)
        return mock_model

    @staticmethod
    def create_mock_response(status_code: int = 200, data: Dict = None) -> Mock:
        """Create a mock HTTP response"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json = Mock(return_value=data or {})
        mock_response.text = Mock(return_value=str(data or {}))
        mock_response.content = Mock(return_value=b'{"result": "success"}')
        return mock_response

    @staticmethod
    def create_test_task(task_type: str = "reasoning") -> Dict[str, Any]:
        """Create a test task dictionary"""
        return {
            "id": f"test_task_{task_type}",
            "kind": task_type,
            "prompt": f"Test {task_type} task",
            "expected_output": "Test response",
            "priority": "normal",
            "timeout": 30
        }

# Test data generators
class UnitTestDataGenerator:
    """Generate test data for unit tests"""

    @staticmethod
    def generate_test_scenarios() -> List[Dict[str, Any]]:
        """Generate test scenarios for unit tests"""
        return [
            {
                "name": "Happy Path",
                "input": {"valid": True},
                "expected": {"success": True},
                "mock_behavior": "return_success"
            },
            {
                "name": "Error Path",
                "input": {"valid": False},
                "expected": {"error": "Invalid input"},
                "mock_behavior": "raise_exception"
            },
            {
                "name": "Edge Case",
                "input": {"edge": True},
                "expected": {"handled": True},
                "mock_behavior": "return_edge_case"
            }
        ]

    @staticmethod
    def generate_api_test_data() -> List[Dict[str, Any]]:
        """Generate API test data"""
        return [
            {
                "endpoint": "/api/health",
                "method": "GET",
                "status_code": 200,
                "response": {"status": "healthy"}
            },
            {
                "endpoint": "/api/models",
                "method": "GET",
                "status_code": 200,
                "response": {"models": ["test_model"]}
            },
            {
                "endpoint": "/api/tasks",
                "method": "POST",
                "status_code": 201,
                "response": {"task_id": "test_task_123"}
            }
        ]

    @staticmethod
    def generate_error_test_data() -> List[Dict[str, Any]]:
        """Generate error test data"""
        return [
            {
                "error_type": "ValueError",
                "error_message": "Invalid value",
                "expected_exception": ValueError
            },
            {
                "error_type": "ConnectionError",
                "error_message": "Connection failed",
                "expected_exception": ConnectionError
            },
            {
                "error_type": "TimeoutError",
                "error_message": "Request timeout",
                "expected_exception": TimeoutError
            }
        ]

# Custom assertions
class CustomAssertions:
    """Custom assertion methods for unit tests"""

    @staticmethod
    def assert_service_response(response, expected_status: int, expected_keys: List[str] = None):
        """Assert service response meets expectations"""
        assert response.status_code == expected_status
        if expected_keys:
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Expected key '{key}' not found in response"

    @staticmethod
    def assert_task_result(result, expected_keys: List[str] = None):
        """Assert task result contains expected keys"""
        assert isinstance(result, dict)
        if expected_keys:
            for key in expected_keys:
                assert key in result, f"Expected key '{key}' not found in task result"

    @staticmethod
    def assert_performance_metrics(metrics, max_time: float, max_memory: float):
        """Assert performance metrics are within acceptable limits"""
        assert metrics["execution_time"] <= max_time, f"Execution time {metrics['execution_time']} exceeds {max_time}s"
        assert metrics["memory_used"] <= max_memory, f"Memory used {metrics['memory_used']} exceeds {max_memory}MB"

    @staticmethod
    def assert_error_handling(func, expected_exception):
        """Assert that function raises expected exception"""
        with pytest.raises(expected_exception):
            func()

# Async test utilities
class AsyncTestHelpers:
    """Helper utilities for async unit tests"""

    @staticmethod
    async def create_async_mock_response(data: Dict = None, status_code: int = 200) -> Mock:
        """Create a mock async response"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json = AsyncMock(return_value=data or {})
        mock_response.text = AsyncMock(return_value=str(data or {}))
        return mock_response

    @staticmethod
    async def test_async_function(func, *args, **kwargs) -> Dict[str, Any]:
        """Test an async function and return results"""
        try:
            result = await func(*args, **kwargs)
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @staticmethod
    def create_async_mock(name: str, return_value: Any = None) -> Mock:
        """Create a mock async function"""
        mock = AsyncMock()
        mock.__name__ = name
        if return_value is not None:
            mock.return_value = return_value
        return mock

# Test fixtures
@pytest.fixture
def mock_service():
    """Fixture providing a mock service"""
    return UnitTestHelpers.create_mock_service("test_service", 8001)

@pytest.fixture
def mock_ai_model():
    """Fixture providing a mock AI model"""
    return UnitTestHelpers.create_mock_ai_model("test_model", ["text", "code"])

@pytest.fixture
def mock_http_response():
    """Fixture providing a mock HTTP response"""
    return UnitTestHelpers.create_mock_response()

@pytest.fixture
def test_helpers():
    """Fixture providing test helpers"""
    return UnitTestHelpers()

@pytest.fixture
def data_generator():
    """Fixture providing test data generator"""
    return UnitTestDataGenerator()

@pytest.fixture
def custom_assertions():
    """Fixture providing custom assertions"""
    return CustomAssertions()

@pytest.fixture
def async_helpers():
    """Fixture providing async test helpers"""
    return AsyncTestHelpers()

# Export utilities
__all__ = [
    "UnitTestHelpers",
    "UnitTestDataGenerator",
    "CustomAssertions",
    "AsyncTestHelpers",
    "UNIT_TEST_CONFIG"
]
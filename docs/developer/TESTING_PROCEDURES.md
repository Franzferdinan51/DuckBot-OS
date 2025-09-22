# DuckBot v4.2 Testing Procedures

## Table of Contents
- [Testing Philosophy](#testing-philosophy)
- [Test Environment Setup](#test-environment-setup)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [Load Testing](#load-testing)
- [Test Automation](#test-automation)
- [Test Reporting](#test-reporting)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting Tests](#troubleshooting-tests)

## Testing Philosophy

### Core Principles

1. **Test-Driven Development (TDD)**: Write tests before code
2. **Comprehensive Coverage**: Aim for >90% code coverage
3. **Realistic Scenarios**: Test with real-world data and conditions
4. **Automated Testing**: Automate all possible test scenarios
5. **Continuous Integration**: Run tests on every commit
6. **Fast Feedback**: Provide quick test results
7. **Maintainable Tests**: Keep tests clean and maintainable

### Testing Pyramid

```
                    E2E Tests (5%)
                   /               \
              Integration Tests (25%)
             /                       \
        Unit Tests (70%)
       /                           \
    Fast & Focused                   Slow & Comprehensive
```

## Test Environment Setup

### 1. Local Development Environment

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # Linux/macOS
# or
test_env\Scripts\activate  # Windows

# Install test dependencies
pip install -r docs/requirements-test.txt

# Install DuckBot in development mode
pip install -e .

# Verify installation
python -c "import duckbot; print('DuckBot installed successfully')"
```

### 2. Test Configuration

```yaml
# tests/test_config.yaml
test_environment:
  database_url: "sqlite:///test.db"
  redis_url: "redis://localhost:6379/0"
  api_base_url: "http://localhost:8790"
  webui_url: "http://localhost:8787"

test_users:
  admin:
    username: "admin"
    password: "admin123"
    role: "admin"

  user:
    username: "testuser"
    password: "test123"
    role: "user"

test_data:
  sample_prompts:
    - "Hello, how are you?"
    - "Write a Python function"
    - "Explain quantum computing"

  sample_responses:
    - "I'm doing well, thank you!"
    - "Here's a Python function..."
    - "Quantum computing is..."
```

### 3. Test Fixtures

```python
# tests/fixtures.py
import pytest
import asyncio
from duckbot.core.ai_provider_manager import AIProviderManager
from duckbot.core.service_manager import ServiceManager

@pytest.fixture
async def ai_manager():
    """AI provider manager test fixture"""
    manager = AIProviderManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()

@pytest.fixture
async def service_manager():
    """Service manager test fixture"""
    manager = ServiceManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()

@pytest.fixture
def sample_request_data():
    """Sample request data for testing"""
    return {
        "prompt": "Test prompt",
        "task_type": "test",
        "model": "test-model",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }

@pytest.fixture
def sample_response_data():
    """Sample response data for testing"""
    return {
        "response": "Test response",
        "model": "test-model",
        "tokens_used": 25,
        "cost": 0.001
    }
```

## Unit Testing

### 1. Core Components Testing

```python
# tests/unit/test_core_modules.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from duckbot.core.ai_provider_manager import AIProviderManager

class TestAIProviderManager:
    """Test AI provider manager functionality"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test AI provider manager initialization"""
        manager = AIProviderManager()
        await manager.initialize()

        assert manager.providers == {}
        assert manager.router is not None
        assert manager.cache is not None

    @pytest.mark.asyncio
    async def test_add_provider(self, ai_manager):
        """Test adding AI provider"""
        mock_provider = AsyncMock()
        await ai_manager.add_provider("test_provider", mock_provider)

        assert "test_provider" in ai_manager.providers
        assert ai_manager.providers["test_provider"] == mock_provider

    @pytest.mark.asyncio
    async def test_route_request_success(self, ai_manager, sample_request_data):
        """Test successful request routing"""
        # Setup mock response
        mock_response = "Mock AI response"
        ai_manager.router = AsyncMock()
        ai_manager.router.route_request.return_value = mock_response

        # Execute test
        result = await ai_manager.route_request(
            prompt=sample_request_data["prompt"],
            task_type=sample_request_data["task_type"]
        )

        # Verify results
        assert result == mock_response
        ai_manager.router.route_request.assert_called_once_with(
            sample_request_data["prompt"],
            sample_request_data["task_type"]
        )

    @pytest.mark.asyncio
    async def test_route_request_with_cache(self, ai_manager, sample_request_data):
        """Test request routing with cache hit"""
        # Setup cache
        cached_response = "Cached response"
        ai_manager.cache = AsyncMock()
        ai_manager.cache.get.return_value = cached_response

        # Execute test
        result = await ai_manager.route_request(
            prompt=sample_request_data["prompt"],
            task_type=sample_request_data["task_type"]
        )

        # Verify cache was used
        assert result == cached_response
        ai_manager.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_request_failure(self, ai_manager, sample_request_data):
        """Test request routing failure"""
        # Setup mock to raise exception
        ai_manager.router = AsyncMock()
        ai_manager.router.route_request.side_effect = Exception("Route failed")

        # Execute test and verify exception
        with pytest.raises(Exception, match="Route failed"):
            await ai_manager.route_request(
                prompt=sample_request_data["prompt"],
                task_type=sample_request_data["task_type"]
            )
```

### 2. Service Testing

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from duckbot.services.webui_service import WebUIService

class TestWebUIService:
    """Test WebUI service functionality"""

    @pytest.mark.asyncio
    async def test_service_start(self):
        """Test WebUI service start"""
        service = WebUIService()
        config = {"host": "127.0.0.1", "port": 8787}

        # Mock server creation
        service._create_app = AsyncMock()
        service._setup_auth = AsyncMock()
        service._setup_routes = AsyncMock()

        await service.start(config)

        # Verify service setup
        service._create_app.assert_called_once()
        service._setup_auth.assert_called_once()
        service._setup_routes.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_stop(self):
        """Test WebUI service stop"""
        service = WebUIService()
        service.server = AsyncMock()

        await service.stop()

        # Verify server stop
        service.server.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test WebUI health check"""
        service = WebUIService()
        service.app = AsyncMock()
        service.app.state = {"healthy": True}

        health = await service.get_health_status()

        assert health["status"] == "healthy"
        assert health["service"] == "webui"
```

### 3. Integration Testing

```python
# tests/integration/test_api_endpoints.py
import pytest
import aiohttp
from duckbot.enhanced_webui import EnhancedWebUI

class TestAPIEndpoints:
    """Test API endpoint integration"""

    @pytest.fixture
    async def webui_app(self):
        """Create test WebUI application"""
        webui = EnhancedWebUI()
        app = await webui.create_app()
        yield app
        await webui.stop()

    @pytest.mark.asyncio
    async def test_health_endpoint(self, webui_app):
        """Test health check endpoint"""
        async with aiohttp.test_client.TestClient(webui_app) as client:
            response = await client.get("/health")
            assert response.status == 200

            data = await response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_chat_endpoint(self, webui_app):
        """Test chat endpoint"""
        async with aiohttp.test_client.TestClient(webui_app) as client:
            response = await client.post(
                "/api/v1/chat",
                json={
                    "message": "Hello, test",
                    "model": "test-model",
                    "stream": False
                }
            )
            assert response.status == 200

            data = await response.json()
            assert "response" in data
            assert "model" in data
            assert "tokens_used" in data

    @pytest.mark.asyncio
    async def test_rate_limiting(self, webui_app):
        """Test rate limiting endpoint"""
        async with aiohttp.test_client.TestClient(webui_app) as client:
            # Send multiple requests quickly
            responses = []
            for _ in range(15):  # Exceed rate limit
                response = await client.get("/api/v1/status")
                responses.append(response)

            # Check if rate limited
            rate_limited = any(r.status == 429 for r in responses)
            assert rate_limited, "Rate limiting not working"
```

### 4. Agent Testing

```python
# tests/integration/test_agents.py
import pytest
from duckbot.agents.intelligent_agents import IntelligentAgents

class TestIntelligentAgents:
    """Test intelligent agent system"""

    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """Test agent creation"""
        agents = IntelligentAgents()
        await agents.initialize()

        agent_id = await agents.create_agent(
            agent_type="code_agent",
            config={"model": "test-model", "max_tasks": 5}
        )

        assert agent_id is not None
        assert len(agents.agents) == 1

    @pytest.mark.asyncio
    async def test_task_assignment(self):
        """Test task assignment to agents"""
        agents = IntelligentAgents()
        await agents.initialize()

        # Create agent
        agent_id = await agents.create_agent(
            agent_type="research_agent",
            config={"model": "test-model"}
        )

        # Assign task
        task = {
            "type": "research",
            "topic": "AI trends",
            "deadline": "2024-01-01"
        }

        result = await agents.assign_task(agent_id, task)

        assert result["status"] == "assigned"
        assert result["agent_id"] == agent_id

    @pytest.mark.asyncio
    async def test_agent_coordination(self):
        """Test multi-agent coordination"""
        agents = IntelligentAgents()
        await agents.initialize()

        # Create multiple agents
        agent_ids = []
        for agent_type in ["research_agent", "code_agent", "creative_agent"]:
            agent_id = await agents.create_agent(
                agent_type=agent_type,
                config={"model": "test-model"}
            )
            agent_ids.append(agent_id)

        # Coordinate task
        result = await agents.coordinate_agents(
            task="Create comprehensive AI report",
            agent_ids=agent_ids
        )

        assert result["status"] == "completed"
        assert len(result["agent_results"]) == 3
```

## End-to-End Testing

### 1. Complete System Testing

```python
# tests/e2e/test_complete_system.py
import pytest
import asyncio
import aiohttp
from duckbot.start_ecosystem import start_ecosystem

class TestCompleteSystem:
    """Test complete DuckBot system"""

    @pytest.mark.asyncio
    async def test_full_system_startup(self):
        """Test complete system startup"""
        # Start ecosystem
        ecosystem = await start_ecosystem()

        # Verify services are running
        services = await ecosystem.get_service_status()
        assert "webui" in services
        assert services["webui"]["status"] == "running"

        # Test API access
        async with aiohttp.test_client.TestClient(ecosystem.api_app) as client:
            response = await client.get("/health")
            assert response.status == 200

        # Cleanup
        await ecosystem.stop()

    @pytest.mark.asyncio
    async def test_user_workflow(self):
        """Test complete user workflow"""
        # Start system
        ecosystem = await start_ecosystem()

        # Test WebUI access
        async with aiohttp.test_client.TestClient(ecosystem.webui_app) as client:
            # Get token
            token_response = await client.post("/api/v1/auth/token")
            assert token_response.status == 200
            token_data = await token_response.json()
            token = token_data["token"]

            # Test chat
            chat_response = await client.post(
                "/api/v1/chat",
                json={
                    "message": "Hello, how are you?",
                    "model": "test-model"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert chat_response.status == 200

            # Test agent coordination
            agent_response = await client.post(
                "/api/v1/agents/coordinate",
                json={
                    "task": "Research AI trends",
                    "agents": ["research_agent", "creative_agent"]
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert agent_response.status == 200

        # Cleanup
        await ecosystem.stop()
```

### 2. Browser Testing

```python
# tests/e2e/test_browser_integration.py
import pytest
import asyncio
from playwright.async_api import async_playwright

class TestBrowserIntegration:
    """Test browser integration with Playwright"""

    @pytest.mark.asyncio
    async def test_webui_browser_access(self):
        """Test WebUI access through browser"""
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to WebUI
            await page.goto("http://localhost:8787")

            # Wait for page to load
            await page.wait_for_selector(".dashboard")

            # Check title
            title = await page.title()
            assert "DuckBot" in title

            # Test chat functionality
            await page.fill("#chat-input", "Hello, test")
            await page.click("#send-button")

            # Wait for response
            await page.wait_for_selector(".chat-response")
            response = await page.text_content(".chat-response")
            assert response is not None

            # Close browser
            await browser.close()
```

## Performance Testing

### 1. Load Testing

```python
# tests/performance/test_load.py
import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

class TestLoadTesting:
    """Test system under load"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        async def make_request(session, request_id):
            start_time = time.time()
            try:
                async with session.post(
                    "http://localhost:8787/api/v1/chat",
                    json={
                        "message": f"Test message {request_id}",
                        "model": "test-model"
                    }
                ) as response:
                    result = await response.json()
                    return {
                        "request_id": request_id,
                        "status": "success",
                        "response_time": time.time() - start_time
                    }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "status": "error",
                    "error": str(e),
                    "response_time": time.time() - start_time
                }

        # Create session
        async with aiohttp.ClientSession() as session:
            # Send 100 concurrent requests
            tasks = [make_request(session, i) for i in range(100)]
            results = await asyncio.gather(*tasks)

        # Analyze results
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        # Verify results
        assert len(successful) >= 95, f"Too many failures: {len(failed)}/100"

        # Check response times
        response_times = [r["response_time"] for r in successful]
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time}s"

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate load
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(50):
                task = session.post(
                    "http://localhost:8787/api/v1/chat",
                    json={"message": f"Load test {i}", "model": "test-model"}
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"
```

### 2. Stress Testing

```python
# tests/performance/test_stress.py
import pytest
import asyncio
import aiohttp
import time

class TestStressTesting:
    """Test system under stress"""

    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Test system under sustained load"""
        async def sustained_load_test(duration_seconds=60):
            start_time = time.time()
            request_count = 0
            error_count = 0

            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < duration_seconds:
                    try:
                        async with session.post(
                            "http://localhost:8787/api/v1/chat",
                            json={"message": f"Stress test {request_count}", "model": "test-model"}
                        ) as response:
                            if response.status != 200:
                                error_count += 1
                            request_count += 1
                    except Exception:
                        error_count += 1
                        request_count += 1

                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.1)

            return {
                "duration": duration_seconds,
                "requests": request_count,
                "errors": error_count,
                "requests_per_second": request_count / duration_seconds,
                "error_rate": error_count / request_count if request_count > 0 else 0
            }

        # Run sustained load test
        results = await sustained_load_test(60)

        # Verify results
        assert results["requests_per_second"] > 5, f"Throughput too low: {results['requests_per_second']} req/s"
        assert results["error_rate"] < 0.05, f"Error rate too high: {results['error_rate']*100:.1f}%"

    @pytest.mark.asyncio
    async def test_circuit_breaker_stress(self):
        """Test circuit breaker under stress"""
        async with aiohttp.ClientSession() as session:
            # Send requests to trigger circuit breaker
            responses = []
            for i in range(20):
                try:
                    async with session.post(
                        "http://localhost:8787/api/v1/chat",
                        json={"message": f"Circuit breaker test {i}", "model": "failing-model"}
                    ) as response:
                        responses.append(response.status)
                except Exception:
                    responses.append(500)

            # Check if circuit breaker activated
            circuit_breaker_activated = responses.count(503) > 0
            assert circuit_breaker_activated, "Circuit breaker not activated"
```

## Security Testing

### 1. Authentication Testing

```python
# tests/security/test_authentication.py
import pytest
import aiohttp
import jwt

class TestAuthentication:
    """Test authentication security"""

    @pytest.mark.asyncio
    async def test_token_validation(self):
        """Test JWT token validation"""
        # Test valid token
        valid_token = jwt.encode(
            {"user_id": "test_user", "exp": time.time() + 3600},
            "test_secret",
            algorithm="HS256"
        )

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "http://localhost:8787/api/v1/protected",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            assert response.status == 200

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test invalid token rejection"""
        invalid_token = "invalid.token.here"

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "http://localhost:8787/api/v1/protected",
                headers={"Authorization": f"Bearer {invalid_token}"}
            )
            assert response.status == 401

    @pytest.mark.asyncio
    async def test_expired_token(self):
        """Test expired token rejection"""
        expired_token = jwt.encode(
            {"user_id": "test_user", "exp": time.time() - 3600},
            "test_secret",
            algorithm="HS256"
        )

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "http://localhost:8787/api/v1/protected",
                headers={"Authorization": f"Bearer {expired_token}"}
            )
            assert response.status == 401
```

### 2. Input Validation Testing

```python
# tests/security/test_input_validation.py
import pytest
import aiohttp

class TestInputValidation:
    """Test input validation security"""

    @pytest.mark.asyncio
    async def test_sql_injection(self):
        """Test SQL injection prevention"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "'; WAITFOR DELAY '0:0:5'--"
        ]

        async with aiohttp.ClientSession() as session:
            for malicious_input in malicious_inputs:
                response = await session.post(
                    "http://localhost:8787/api/v1/chat",
                    json={"message": malicious_input, "model": "test-model"}
                )
                # Should handle gracefully, not crash
                assert response.status in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_xss_prevention(self):
        """Test XSS prevention"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>"
        ]

        async with aiohttp.ClientSession() as session:
            for xss_payload in xss_payloads:
                response = await session.post(
                    "http://localhost:8787/api/v1/chat",
                    json={"message": xss_payload, "model": "test-model"}
                )
                # Should handle gracefully, not execute script
                assert response.status in [200, 400, 422]

                # Check response doesn't contain script
                if response.status == 200:
                    data = await response.json()
                    assert "<script>" not in data["response"]
```

## Test Automation

### 1. CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r docs/requirements-test.txt
        pip install -e .

    - name: Run linting
      run: |
        ruff check duckbot/
        black --check duckbot/
        isort --check-only duckbot/

    - name: Run type checking
      run: |
        mypy duckbot/

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=duckbot --cov-report=xml

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v

    - name: Run performance tests
      run: |
        pytest tests/performance/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 2. Test Runner Script

```python
# scripts/run_tests.py
#!/usr/bin/env python3
"""
Comprehensive test runner for DuckBot
"""

import argparse
import asyncio
import pytest
import subprocess
import sys
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.test_results = {}

    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Running comprehensive test suite...")

        # Run unit tests
        print("\n📝 Running unit tests...")
        unit_result = await self.run_unit_tests()
        self.test_results["unit"] = unit_result

        # Run integration tests
        print("\n🔗 Running integration tests...")
        integration_result = await self.run_integration_tests()
        self.test_results["integration"] = integration_result

        # Run performance tests
        print("\n⚡ Running performance tests...")
        performance_result = await self.run_performance_tests()
        self.test_results["performance"] = performance_result

        # Run security tests
        print("\n🔒 Running security tests...")
        security_result = await self.run_security_tests()
        self.test_results["security"] = security_result

        # Generate report
        await self.generate_report()

    async def run_unit_tests(self):
        """Run unit tests with coverage"""
        try:
            result = subprocess.run([
                "pytest", "tests/unit/",
                "-v", "--cov=duckbot", "--cov-report=term-missing",
                "--cov-report=html", "--cov-fail-under=90"
            ], capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "coverage": self._extract_coverage(result.stdout)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_integration_tests(self):
        """Run integration tests"""
        try:
            result = subprocess.run([
                "pytest", "tests/integration/", "-v"
            ], capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "output": result.stdout
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_performance_tests(self):
        """Run performance tests"""
        try:
            result = subprocess.run([
                "pytest", "tests/performance/", "-v"
            ], capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "output": result.stdout
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_security_tests(self):
        """Run security tests"""
        try:
            result = subprocess.run([
                "pytest", "tests/security/", "-v"
            ], capture_output=True, text=True)

            return {
                "success": result.returncode == 0,
                "output": result.stdout
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_coverage(self, output):
        """Extract coverage percentage from output"""
        for line in output.split('\n'):
            if 'TOTAL' in line and '%' in line:
                coverage = line.split()[-1].replace('%', '')
                return float(coverage)
        return 0.0

    async def generate_report(self):
        """Generate test report"""
        print("\n📊 Test Results Summary:")
        print("=" * 50)

        total_tests = 0
        passed_tests = 0

        for test_type, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{test_type.upper()}: {status}")

            if result["success"]:
                passed_tests += 1
            total_tests += 1

        print("=" * 50)
        print(f"Overall: {passed_tests}/{total_tests} test suites passed")

        if "unit" in self.test_results and "coverage" in self.test_results["unit"]:
            coverage = self.test_results["unit"]["coverage"]
            print(f"Coverage: {coverage:.1f}%")

        # Generate HTML report
        await self._generate_html_report()

    async def _generate_html_report(self):
        """Generate HTML test report"""
        report_path = Path("test_report.html")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                .summary {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>DuckBot Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Generated: {datetime.datetime.now().isoformat()}</p>
                <ul>
        """

        for test_type, result in self.test_results.items():
            status_class = "pass" if result["success"] else "fail"
            status_text = "PASS" if result["success"] else "FAIL"
            html_content += f'<li class="{status_class}">{test_type}: {status_text}</li>'

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """

        report_path.write_text(html_content)
        print(f"\n📄 HTML report generated: {report_path}")

async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="DuckBot Test Runner")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--security-only", action="store_true", help="Run only security tests")

    args = parser.parse_args()
    runner = TestRunner()

    if args.unit_only:
        await runner.run_unit_tests()
    elif args.integration_only:
        await runner.run_integration_tests()
    elif args.performance_only:
        await runner.run_performance_tests()
    elif args.security_only:
        await runner.run_security_tests()
    else:
        await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
```

## Test Reporting

### 1. Test Coverage Report

```python
# scripts/coverage_report.py
#!/usr/bin/env python3
"""
Generate comprehensive test coverage report
"""

import coverage
import json
from pathlib import Path

class CoverageReporter:
    def __init__(self):
        self.cov = coverage.Coverage()

    def generate_report(self):
        """Generate coverage report"""
        # Start coverage
        self.cov.start()

        # Run tests
        import pytest
        pytest.main(["tests/", "--cov=duckbot", "--cov-report=html"])

        # Stop coverage
        self.cov.stop()

        # Generate reports
        self.cov.save()
        self.cov.html_report(directory="coverage_html")
        self.cov.xml_report(outfile="coverage.xml")

        # Generate summary
        self._generate_summary()

    def _generate_summary(self):
        """Generate coverage summary"""
        total_coverage = self.cov.report()
        print(f"\n📊 Coverage Summary:")
        print(f"Total Coverage: {total_coverage:.1f}%")

        # Generate JSON report
        report = {
            "total_coverage": total_coverage,
            "generated_at": datetime.datetime.now().isoformat(),
            "files": self._get_file_coverage()
        }

        with open("coverage_summary.json", "w") as f:
            json.dump(report, f, indent=2)

    def _get_file_coverage(self):
        """Get coverage per file"""
        file_coverage = {}
        for filename in self.cov.get_data().measured_files():
            if "duckbot" in filename:
                file_coverage[filename] = {
                    "line_coverage": self.cov.analysis2(filename)[1],
                    "total_lines": self.cov.analysis2(filename)[2]
                }
        return file_coverage
```

## Troubleshooting Tests

### 1. Common Test Issues

```python
# tests/troubleshooting/test_helpers.py
import pytest
import asyncio
import logging

class TestHelpers:
    """Helper functions for test troubleshooting"""

    @staticmethod
    def setup_test_logging():
        """Setup logging for test debugging"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    @staticmethod
    async def wait_for_service(url, timeout=30):
        """Wait for service to be available"""
        import aiohttp
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return True
            except:
                pass
            await asyncio.sleep(1)

        return False

    @staticmethod
    def capture_test_output(test_func):
        """Capture test output for debugging"""
        import io
        from contextlib import redirect_stdout, redirect_stderr

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            result = test_func()

        return {
            "result": result,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue()
        }
```

### 2. Test Debugging

```python
# tests/debug/test_debug_mode.py
import pytest
import pdb
import traceback

class TestDebugMode:
    """Debug mode for troubleshooting tests"""

    @pytest.mark.debug
    def test_with_debugger(self):
        """Test with interactive debugger"""
        # Set breakpoint
        pdb.set_trace()

        # Test code
        result = 2 + 2
        assert result == 4

    @pytest.mark.slow
    def test_with_detailed_logging(self, caplog):
        """Test with detailed logging"""
        import logging

        # Enable detailed logging
        logger = logging.getLogger("duckbot")
        logger.setLevel(logging.DEBUG)

        # Capture logs
        with caplog.at_level(logging.DEBUG):
            # Test code
            from duckbot.core.ai_provider_manager import AIProviderManager
            manager = AIProviderManager()

        # Check logs
        debug_logs = [record for record in caplog.records if record.levelno == logging.DEBUG]
        print(f"Debug logs: {len(debug_logs)} entries")
        for log in debug_logs:
            print(f"  {log.message}")

    @pytest.mark.exception_trace
    def test_with_exception_trace(self):
        """Test with full exception trace"""
        try:
            # Code that might fail
            from duckbot.core.nonexistent_module import NonExistentClass
        except Exception as e:
            # Print full exception trace
            print("Full exception trace:")
            traceback.print_exc()
            raise
```

This comprehensive testing documentation covers all aspects of testing DuckBot v4.2, from unit tests to end-to-end testing, performance testing, security testing, and test automation. The testing procedures ensure high-quality, reliable software that meets the project's standards for performance, security, and functionality.
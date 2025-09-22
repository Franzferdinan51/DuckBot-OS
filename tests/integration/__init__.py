"""
Integration Tests for DuckBot v4.2

This package contains comprehensive integration tests that verify
how different components work together. Integration tests focus on:

- Cross-service communication
- End-to-end workflows
- API contract validation
- Database integration
- External service integration
- System behavior under realistic conditions

Integration tests use real components but may mock external dependencies.
"""

import pytest
import asyncio
import aiohttp
import httpx
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List, Optional
import sys
import os
import tempfile
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Integration test configuration
INTEGRATION_TEST_CONFIG = {
    "base_url": "http://localhost:8787",
    "api_timeout": 30,
    "database_url": "sqlite:///test_integration.db",
    "enable_real_services": False,  # Set to True to test with real services
    "test_data_dir": "test_integration_data",
    "cleanup_after_tests": True
}

# Integration test utilities
class IntegrationTestHelpers:
    """Helper utilities for integration tests"""

    @staticmethod
    async def start_test_service(service_name: str, port: int, config: Dict = None) -> Dict[str, Any]:
        """Start a test service for integration testing"""
        import uvicorn
        from fastapi import FastAPI
        import threading
        import time

        app = FastAPI(title=f"Test {service_name}")

        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": service_name}

        @app.get("/config")
        async def get_config():
            return config or {"service": service_name, "port": port}

        # Start service in background thread
        def run_service():
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

        service_thread = threading.Thread(target=run_service, daemon=True)
        service_thread.start()
        time.sleep(1)  # Give service time to start

        return {
            "name": service_name,
            "port": port,
            "url": f"http://127.0.0.1:{port}",
            "thread": service_thread
        }

    @staticmethod
    async def make_api_request(
        method: str,
        url: str,
        headers: Dict = None,
        data: Dict = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """Make HTTP request and return structured response"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "headers": dict(response.headers),
                    "success": response.status_code < 400
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "data": None,
                    "headers": {},
                    "success": False,
                    "error": str(e)
                }

    @staticmethod
    def create_test_database(db_url: str) -> Any:
        """Create test database with sample data"""
        from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime
        from sqlalchemy.orm import sessionmaker
        from datetime import datetime

        engine = create_engine(db_url)
        metadata = MetaData()

        # Create test tables
        services_table = Table(
            'services', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)),
            Column('port', Integer),
            Column('status', String(20)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )

        tasks_table = Table(
            'tasks', metadata,
            Column('id', Integer, primary_key=True),
            Column('task_id', String(100)),
            Column('type', String(50)),
            Column('status', String(20)),
            Column('result', String(500)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )

        metadata.create_all(engine)

        # Insert test data
        Session = sessionmaker(bind=engine)
        session = Session()

        # Insert test services
        test_services = [
            {"name": "webui", "port": 8787, "status": "running"},
            {"name": "terminal", "port": 8788, "status": "stopped"},
            {"name": "monitoring", "port": 8789, "status": "running"}
        ]

        for service_data in test_services:
            session.execute(services_table.insert().values(**service_data))

        # Insert test tasks
        test_tasks = [
            {"task_id": "task_001", "type": "analysis", "status": "completed", "result": "Analysis complete"},
            {"task_id": "task_002", "type": "code", "status": "pending", "result": None},
            {"task_id": "task_003", "type": "reasoning", "status": "running", "result": "In progress"}
        ]

        for task_data in test_tasks:
            session.execute(tasks_table.insert().values(**task_data))

        session.commit()
        session.close()

        return engine

    @staticmethod
    async def test_service_communication(service1_url: str, service2_url: str) -> Dict[str, Any]:
        """Test communication between two services"""
        # Test service1 can reach service2
        health_check = await IntegrationTestHelpers.make_api_request(
            "GET", f"{service2_url}/health"
        )

        # Test data exchange
        test_data = {"test_message": "Hello from service1", "timestamp": "2024-01-01T00:00:00Z"}
        response = await IntegrationTestHelpers.make_api_request(
            "POST", f"{service2_url}/receive", data=test_data
        )

        return {
            "service1_to_service2": {
                "health_check": health_check["success"],
                "data_exchange": response["success"]
            }
        }

# Test workflow executor
class WorkflowExecutor:
    """Execute complex test workflows across multiple services"""

    def __init__(self):
        self.services = {}
        self.workflow_results = []

    async def start_services(self, service_configs: List[Dict]) -> Dict[str, Any]:
        """Start multiple services for workflow testing"""
        started_services = {}

        for config in service_configs:
            service = await IntegrationTestHelpers.start_test_service(
                config["name"],
                config["port"],
                config.get("config")
            )
            started_services[config["name"]] = service

        self.services = started_services
        return started_services

    async def execute_workflow(self, workflow_steps: List[Dict]) -> Dict[str, Any]:
        """Execute a workflow with multiple steps"""
        workflow_result = {
            "workflow_name": workflow_steps[0].get("workflow_name", "unnamed"),
            "steps": [],
            "success": True,
            "total_duration": 0
        }

        import time
        start_time = time.time()

        for step in workflow_steps:
            step_result = await self._execute_workflow_step(step)
            workflow_result["steps"].append(step_result)

            if not step_result["success"]:
                workflow_result["success"] = False
                break

        workflow_result["total_duration"] = time.time() - start_time
        self.workflow_results.append(workflow_result)

        return workflow_result

    async def _execute_workflow_step(self, step: Dict) -> Dict[str, Any]:
        """Execute a single workflow step"""
        import time
        step_start = time.time()

        try:
            if step["type"] == "api_call":
                result = await IntegrationTestHelpers.make_api_request(
                    step["method"],
                    step["url"],
                    step.get("headers"),
                    step.get("data")
                )
            elif step["type"] == "service_communication":
                service1 = self.services.get(step["service1"])
                service2 = self.services.get(step["service2"])
                result = await IntegrationTestHelpers.test_service_communication(
                    service1["url"], service2["url"]
                )
            else:
                raise ValueError(f"Unknown step type: {step['type']}")

            return {
                "step_name": step.get("name", "unnamed"),
                "type": step["type"],
                "success": True,
                "result": result,
                "duration": time.time() - step_start
            }
        except Exception as e:
            return {
                "step_name": step.get("name", "unnamed"),
                "type": step["type"],
                "success": False,
                "error": str(e),
                "duration": time.time() - step_start
            }

# Integration test data generators
class IntegrationTestDataGenerator:
    """Generate realistic test data for integration tests"""

    @staticmethod
    def generate_workflow_definitions() -> List[Dict[str, Any]]:
        """Generate workflow definitions for testing"""
        return [
            {
                "name": "User Request Processing",
                "description": "Process user request through AI pipeline",
                "steps": [
                    {
                        "name": "Receive Request",
                        "type": "api_call",
                        "method": "POST",
                        "url": "http://localhost:8787/api/request",
                        "data": {"prompt": "Test request", "type": "analysis"}
                    },
                    {
                        "name": "Route to AI",
                        "type": "service_communication",
                        "service1": "webui",
                        "service2": "ai_service"
                    },
                    {
                        "name": "Process Response",
                        "type": "api_call",
                        "method": "GET",
                        "url": "http://localhost:8787/api/result/test_task_id"
                    }
                ]
            },
            {
                "name": "Service Health Monitoring",
                "description": "Monitor health of all services",
                "steps": [
                    {
                        "name": "Check WebUI Health",
                        "type": "api_call",
                        "method": "GET",
                        "url": "http://localhost:8787/health"
                    },
                    {
                        "name": "Check AI Service Health",
                        "type": "api_call",
                        "method": "GET",
                        "url": "http://localhost:8790/health"
                    },
                    {
                        "name": "Aggregate Health Status",
                        "type": "api_call",
                        "method": "POST",
                        "url": "http://localhost:8789/api/health/aggregate",
                        "data": {"services": ["webui", "ai_service"]}
                    }
                ]
            }
        ]

    @staticmethod
    def generate_service_configs() -> List[Dict[str, Any]]:
        """Generate service configurations for integration testing"""
        return [
            {
                "name": "webui",
                "port": 8787,
                "config": {
                    "enable_ai": True,
                    "enable_auth": False,
                    "max_connections": 100
                }
            },
            {
                "name": "ai_service",
                "port": 8790,
                "config": {
                    "model": "test_model",
                    "max_tokens": 1000,
                    "timeout": 30
                }
            },
            {
                "name": "monitoring",
                "port": 8789,
                "config": {
                    "check_interval": 5,
                    "alert_threshold": 0.8
                }
            }
        ]

    @staticmethod
    def generate_api_test_scenarios() -> List[Dict[str, Any]]:
        """Generate API test scenarios"""
        return [
            {
                "name": "Authentication Flow",
                "endpoints": [
                    {
                        "method": "POST",
                        "url": "/api/auth/login",
                        "data": {"username": "test", "password": "test123"},
                        "expected_status": 200
                    },
                    {
                        "method": "GET",
                        "url": "/api/user/profile",
                        "headers": {"Authorization": "Bearer test_token"},
                        "expected_status": 200
                    },
                    {
                        "method": "POST",
                        "url": "/api/auth/logout",
                        "expected_status": 200
                    }
                ]
            },
            {
                "name": "Task Management",
                "endpoints": [
                    {
                        "method": "POST",
                        "url": "/api/tasks",
                        "data": {"type": "analysis", "prompt": "Test task"},
                        "expected_status": 201
                    },
                    {
                        "method": "GET",
                        "url": "/api/tasks",
                        "expected_status": 200
                    },
                    {
                        "method": "GET",
                        "url": "/api/tasks/test_task_id",
                        "expected_status": 200
                    }
                ]
            }
        ]

# Performance monitoring for integration tests
class IntegrationPerformanceMonitor:
    """Monitor performance during integration tests"""

    def __init__(self):
        self.metrics = []

    def record_metric(self, name: str, value: float, unit: str = "seconds"):
        """Record a performance metric"""
        self.metrics.append({
            "name": name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now()
        })

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {"total_metrics": 0}

        # Group by metric name
        grouped = {}
        for metric in self.metrics:
            name = metric["name"]
            if name not in grouped:
                grouped[name] = []
            grouped[name].append(metric["value"])

        # Calculate statistics
        summary = {"total_metrics": len(self.metrics)}
        for name, values in grouped.items():
            summary[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "unit": next((m["unit"] for m in self.metrics if m["name"] == name), "unknown")
            }

        return summary

# Integration test fixtures
@pytest.fixture(scope="session")
def integration_config():
    """Provide integration test configuration"""
    return INTEGRATION_TEST_CONFIG

@pytest.fixture(scope="session")
def test_helpers():
    """Provide integration test helpers"""
    return IntegrationTestHelpers()

@pytest.fixture(scope="session")
def workflow_executor():
    """Provide workflow executor"""
    return WorkflowExecutor()

@pytest.fixture(scope="session")
def data_generator():
    """Provide integration test data generator"""
    return IntegrationTestDataGenerator()

@pytest.fixture(scope="session")
def performance_monitor():
    """Provide performance monitor"""
    return IntegrationPerformanceMonitor()

@pytest.fixture
def test_database():
    """Provide test database"""
    # Create temporary database
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    db_url = f"sqlite:///{db_path}"
    engine = IntegrationTestHelpers.create_test_database(db_url)

    yield engine

    # Cleanup
    os.unlink(db_path)

# Export utilities
__all__ = [
    "IntegrationTestHelpers",
    "WorkflowExecutor",
    "IntegrationTestDataGenerator",
    "IntegrationPerformanceMonitor",
    "INTEGRATION_TEST_CONFIG"
]
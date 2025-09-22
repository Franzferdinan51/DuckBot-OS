"""
Integration Tests for Service Integration

Tests integration between different services:
- WebUI and AI services
- Service communication
- API endpoint integration
- Data flow between services
- Service orchestration
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import test utilities
from tests.integration import (
    IntegrationTestHelpers,
    WorkflowExecutor,
    IntegrationTestDataGenerator,
    IntegrationPerformanceMonitor,
    INTEGRATION_TEST_CONFIG
)

pytestmark = pytest.mark.integration

class TestWebUIAIIntegration:
    """Test integration between WebUI and AI services"""

    @pytest.mark.asyncio
    async def test_webui_ai_communication(self, test_helpers, data_generator):
        """Test WebUI can communicate with AI services"""
        # Start mock services
        webui_service = await test_helpers.start_test_service("webui", 8787)
        ai_service = await test_helpers.start_test_service("ai", 8790)

        # Test WebUI can reach AI service
        health_check = await test_helpers.make_api_request(
            "GET", f"{ai_service['url']}/health"
        )

        assert health_check["success"], f"AI service health check failed: {health_check.get('error')}"

        # Test AI task processing
        task_data = {
            "task_id": "integration_test_001",
            "type": "analysis",
            "prompt": "Analyze this integration test",
            "parameters": {"complexity": "medium"}
        }

        ai_response = await test_helpers.make_api_request(
            "POST", f"{ai_service['url']}/process", data=task_data
        )

        assert ai_response["success"], f"AI processing failed: {ai_response.get('error')}"
        assert "result" in ai_response["data"]

    @pytest.mark.asyncio
    async def test_api_contract_validation(self, test_helpers):
        """Test API contracts between services"""
        # Test WebUI API endpoints
        webui_endpoints = [
            {
                "method": "GET",
                "url": "/health",
                "expected_status": 200,
                "expected_fields": ["status", "service"]
            },
            {
                "method": "GET",
                "/servers/status",
                "expected_status": 200,
                "expected_fields": ["services", "timestamp"]
            },
            {
                "method": "POST",
                "url": "/api/tasks",
                "expected_status": 201,
                "expected_fields": ["task_id", "status"]
            }
        ]

        for endpoint in webui_endpoints:
            # Mock WebUI service
            webui_service = await test_helpers.start_test_service("webui", 8787)

            response = await test_helpers.make_api_request(
                endpoint["method"],
                f"{webui_service['url']}{endpoint['url']}",
                data=endpoint.get("data")
            )

            assert response["status_code"] == endpoint["expected_status"]
            assert response["success"]

            if "expected_fields" in endpoint:
                for field in endpoint["expected_fields"]:
                    assert field in response["data"], f"Expected field {field} not found in response"

class TestServiceOrchestration:
    """Test service orchestration and coordination"""

    @pytest.mark.asyncio
    async def test_service_startup_sequence(self, workflow_executor, data_generator):
        """Test proper service startup sequence"""
        service_configs = data_generator.generate_service_configs()

        # Start services
        started_services = await workflow_executor.start_services(service_configs)
        assert len(started_services) == 3

        # Verify all services are running
        for service_name, service_info in started_services.items():
            health_check = await IntegrationTestHelpers.make_api_request(
                "GET", f"{service_info['url']}/health"
            )
            assert health_check["success"], f"Service {service_name} not healthy"

    @pytest.mark.asyncio
    async def test_workflow_execution(self, workflow_executor, data_generator):
        """Test complete workflow execution across services"""
        # Define test workflow
        workflow_steps = [
            {
                "name": "Initialize Services",
                "type": "service_communication",
                "service1": "webui",
                "service2": "monitoring",
                "workflow_name": "Service Initialization"
            },
            {
                "name": "Process User Request",
                "type": "api_call",
                "method": "POST",
                "url": "http://localhost:8787/api/request",
                "data": {"prompt": "Test integration request", "type": "analysis"}
            },
            {
                "name": "Verify Results",
                "type": "api_call",
                "method": "GET",
                "url": "http://localhost:8787/api/result/test_task_id"
            }
        ]

        # Execute workflow
        result = await workflow_executor.execute_workflow(workflow_steps)

        assert result["success"], f"Workflow failed: {result}"
        assert len(result["steps"]) == 3
        assert result["total_duration"] < 10.0  # Should complete within 10 seconds

class TestDataFlowIntegration:
    """Test data flow between services"""

    @pytest.mark.asyncio
    async def test_data_propagation(self, test_helpers, test_database):
        """Test data propagation between services"""
        # Create test services
        data_service = await test_helpers.start_test_service("data", 8791)
        processing_service = await test_helpers.start_test_service("processing", 8792)

        # Test data input
        test_data = {
            "id": "integration_test_001",
            "type": "user_request",
            "content": "Test data for integration",
            "metadata": {"source": "webui", "priority": "normal"}
        }

        # Send data to data service
        data_response = await test_helpers.make_api_request(
            "POST", f"{data_service['url']}/data", data=test_data
        )
        assert data_response["success"]

        # Simulate data processing
        processed_data = {
            "original_id": test_data["id"],
            "processed_content": "Processed: " + test_data["content"],
            "processing_time": 0.5,
            "status": "completed"
        }

        # Send to processing service
        processing_response = await test_helpers.make_api_request(
            "POST", f"{processing_service['url']}/process", data=processed_data
        )
        assert processing_response["success"]

        # Verify data integrity
        assert processing_response["data"]["original_id"] == test_data["id"]
        assert "processed_content" in processing_response["data"]

    @pytest.mark.asyncio
    async def test_database_integration(self, test_database):
        """Test database integration across services"""
        from sqlalchemy import text
        from sqlalchemy.orm import sessionmaker

        # Test database operations
        Session = sessionmaker(bind=test_database)
        session = Session()

        # Query test data
        result = session.execute(text("SELECT * FROM services WHERE status = 'running'"))
        running_services = result.fetchall()

        assert len(running_services) >= 1, "Should have at least one running service"

        # Test task status updates
        session.execute(
            text("UPDATE tasks SET status = 'completed' WHERE task_id = 'task_002'")
        )
        session.commit()

        # Verify update
        result = session.execute(
            text("SELECT status FROM tasks WHERE task_id = 'task_002'")
        )
        task_status = result.fetchone()
        assert task_status[0] == "completed"

        session.close()

class TestErrorHandlingIntegration:
    """Test error handling across services"""

    @pytest.mark.asyncio
    async def test_service_failure_propagation(self, test_helpers):
        """Test service failure propagation and handling"""
        # Create services where one will fail
        healthy_service = await test_helpers.start_test_service("healthy", 8793)
        failing_service = await test_helpers.start_test_service("failing", 8794)

        # Test failure detection
        health_check = await test_helpers.make_api_request(
            "GET", f"{failing_service['url']}/health"
        )
        assert health_check["success"]  # Service should be healthy initially

        # Simulate service failure (would be more complex in real scenario)
        # For testing, we'll check that the monitoring service can detect failures

        # Test fallback mechanisms
        fallback_response = await test_helpers.make_api_request(
            "POST", f"{healthy_service['url']}/fallback",
            data={"failed_service": "failing", "action": "restart"}
        )
        assert fallback_response["success"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self, test_helpers):
        """Test circuit breaker pattern for service resilience"""
        # Create service with circuit breaker
        protected_service = await test_helpers.start_test_service("protected", 8795)

        # Test circuit breaker activation
        test_requests = [
            {"should_succeed": True},
            {"should_succeed": False},  # This will fail
            {"should_succeed": False},  # This will also fail
            {"should_succeed": True}   # This should be blocked by circuit breaker
        ]

        circuit_breaker_tripped = False
        for i, request in enumerate(test_requests):
            response = await test_helpers.make_api_request(
                "POST", f"{protected_service['url']}/test_circuit",
                data=request
            )

            if i >= 2 and not response["success"]:
                # Circuit breaker should be tripped
                circuit_breaker_tripped = True
                assert "circuit_breaker" in response.get("error", "").lower()

        assert circuit_breaker_tripped, "Circuit breaker should have been tripped"

class TestPerformanceIntegration:
    """Test performance characteristics of integrated services"""

    @pytest.mark.asyncio
    async def test_end_to_end_performance(self, workflow_executor, performance_monitor, data_generator):
        """Test end-to-end performance of service integration"""
        # Execute performance test workflow
        workflow_steps = [
            {
                "name": "Service Health Check",
                "type": "api_call",
                "method": "GET",
                "url": "http://localhost:8787/health"
            },
            {
                "name": "Task Submission",
                "type": "api_call",
                "method": "POST",
                "url": "http://localhost:8787/api/tasks",
                "data": {"type": "performance_test", "prompt": "Performance test task"}
            },
            {
                "name": "Task Processing",
                "type": "api_call",
                "method": "GET",
                "url": "http://localhost:8787/api/tasks/performance_task_id"
            },
            {
                "name": "Result Retrieval",
                "type": "api_call",
                "method": "GET",
                "url": "http://localhost:8787/api/results/performance_task_id"
            }
        ]

        result = await workflow_executor.execute_workflow(workflow_steps)

        # Record performance metrics
        performance_monitor.record_metric(
            "end_to_end_workflow",
            result["total_duration"],
            "seconds"
        )

        # Record individual step performance
        for step in result["steps"]:
            performance_monitor.record_metric(
                f"step_{step['step_name']}",
                step["duration"],
                "seconds"
            )

        # Assert performance thresholds
        assert result["total_duration"] < 5.0, f"Workflow took {result['total_duration']}s, expected < 5s"
        assert result["success"], f"Workflow failed: {result}"

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, test_helpers, performance_monitor):
        """Test concurrent request handling across services"""
        # Create test service
        test_service = await test_helpers.start_test_service("concurrent", 8796)

        # Make concurrent requests
        import concurrent.futures

        async def make_request(request_id: int):
            start_time = asyncio.get_event_loop().time()
            response = await test_helpers.make_api_request(
                "POST", f"{test_service['url']}/concurrent_test",
                data={"request_id": request_id, "delay": 0.1}
            )
            duration = asyncio.get_event_loop().time() - start_time

            performance_monitor.record_metric(
                f"concurrent_request_{request_id}",
                duration,
                "seconds"
            )

            return response

        # Execute concurrent requests
        num_requests = 10
        tasks = [make_request(i) for i in range(num_requests)]
        responses = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        successful_requests = sum(1 for r in responses if r["success"])
        assert successful_requests == num_requests, f"Only {successful_requests}/{num_requests} requests succeeded"

        # Check performance summary
        summary = performance_monitor.get_summary()
        assert summary["total_metrics"] >= num_requests

class TestSecurityIntegration:
    """Test security integration across services"""

    @pytest.mark.asyncio
    async def test_authentication_flow(self, test_helpers):
        """Test authentication flow between services"""
        # Create auth service and protected service
        auth_service = await test_helpers.start_test_service("auth", 8797)
        protected_service = await test_helpers.start_test_service("protected", 8798)

        # Test login
        login_data = {"username": "test_user", "password": "test_password"}
        login_response = await test_helpers.make_api_request(
            "POST", f"{auth_service['url']}/login", data=login_data
        )

        assert login_response["success"], f"Login failed: {login_response.get('error')}"
        assert "token" in login_response["data"]

        # Test protected resource access
        token = login_response["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        protected_response = await test_helpers.make_api_request(
            "GET", f"{protected_service['url']}/protected", headers=headers
        )

        assert protected_response["success"], f"Protected access failed: {protected_response.get('error')}"

    @pytest.mark.asyncio
    async def test_authorization_enforcement(self, test_helpers):
        """Test authorization enforcement across services"""
        # Create service with authorization
        auth_service = await test_helpers.start_test_service("authz", 8799)

        # Test different permission levels
        test_cases = [
            {
                "user": "admin",
                "resource": "/admin/settings",
                "should_succeed": True
            },
            {
                "user": "user",
                "resource": "/admin/settings",
                "should_succeed": False
            },
            {
                "user": "user",
                "resource": "/user/profile",
                "should_succeed": True
            }
        ]

        for case in test_cases:
            response = await test_helpers.make_api_request(
                "POST", f"{auth_service['url']}/authorize",
                data={"user": case["user"], "resource": case["resource"]}
            )

            assert response["success"] == case["should_succeed"], \
                f"Authorization test failed for {case['user']} accessing {case['resource']}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
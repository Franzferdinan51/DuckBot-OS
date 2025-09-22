"""
End-to-End System Tests for DuckBot v4.2

Tests complete system behavior including:
- Full deployment and startup
- User workflow execution
- Performance under load
- Disaster recovery scenarios
- Security validation
- System resilience
"""

import pytest
import asyncio
import httpx
import json
from typing import Dict, Any, List
import time
from datetime import datetime, timedelta

# Import system test utilities
from tests.system import (
    SystemDeployment,
    SystemTestScenarios,
    SystemPerformanceMonitor,
    LoadTester,
    SYSTEM_TEST_CONFIG
)

pytestmark = pytest.mark.system

class TestSystemDeployment:
    """Test complete system deployment"""

    @pytest.mark.asyncio
    async def test_full_deployment(self, system_deployment, performance_monitor):
        """Test complete system deployment and startup"""
        assert system_deployment.is_deployed, "System should be deployed successfully"

        # Verify all services are running
        for service_name in ["webui", "terminal", "monitoring"]:
            is_healthy = await system_deployment._check_service_health(service_name)
            assert is_healthy, f"Service {service_name} should be healthy"

        # Check deployment time
        assert hasattr(system_deployment, 'deployment_start_time')
        deployment_time = (datetime.now() - system_deployment.deployment_start_time).total_seconds()
        assert deployment_time < SYSTEM_TEST_CONFIG["deployment_timeout"], \
            f"Deployment took {deployment_time}s, expected < {SYSTEM_TEST_CONFIG['deployment_timeout']}s"

    @pytest.mark.asyncio
    async def test_service_integration(self, system_deployment):
        """Test integration between all deployed services"""
        # Test WebUI service
        async with httpx.AsyncClient(timeout=10) as client:
            webui_response = await client.get("http://localhost:8787/health")
            assert webui_response.status_code == 200
            assert "status" in webui_response.json()

        # Test monitoring service
        async with httpx.AsyncClient(timeout=10) as client:
            monitoring_response = await client.get("http://localhost:8789/health")
            assert monitoring_response.status_code == 200

        # Test API endpoints
        api_endpoints = [
            ("GET", "http://localhost:8787/api/servers/status"),
            ("GET", "http://localhost:8787/api/models/available"),
            ("GET", "http://localhost:8787/api/system/info")
        ]

        for method, url in api_endpoints:
            async with httpx.AsyncClient(timeout=10) as client:
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url)

                assert response.status_code < 500, f"API endpoint {url} failed with status {response.status_code}"

class TestUserWorkflows:
    """Test complete user workflows"""

    @pytest.mark.asyncio
    async def test_new_user_onboarding(self, system_deployment, performance_monitor):
        """Test complete new user onboarding workflow"""
        performance_monitor.start_monitoring()

        workflow_steps = [
            {
                "name": "access_webui",
                "action": self._access_webui,
                "expected_success": True
            },
            {
                "name": "configure_settings",
                "action": self._configure_settings,
                "expected_success": True
            },
            {
                "name": "start_ai_interaction",
                "action": self._start_ai_interaction,
                "expected_success": True
            },
            {
                "name": "submit_first_task",
                "action": self._submit_first_task,
                "expected_success": True
            }
        ]

        results = []
        for step in workflow_steps:
            print(f"[WORKFLOW] Executing step: {step['name']}")
            performance_monitor.capture_metrics(step['name'])

            try:
                result = await step['action']()
                success = result.get("success", False)
            except Exception as e:
                result = {"error": str(e)}
                success = False

            results.append({
                "step": step['name'],
                "success": success,
                "expected": step['expected_success'],
                "result": result
            })

            assert success == step['expected_success'], \
                f"Step {step['name']} failed: expected {step['expected_success']}, got {success}"

        # Verify workflow completion
        successful_steps = sum(1 for r in results if r['success'])
        assert successful_steps == len(workflow_steps), \
            f"Only {successful_steps}/{len(workflow_steps)} workflow steps succeeded"

        # Check performance metrics
        perf_summary = performance_monitor.get_performance_summary()
        assert len(perf_summary["threshold_violations"]) == 0, \
            f"Performance threshold violations: {perf_summary['threshold_violations']}"

    @pytest.mark.asyncio
    async def test_ai_task_processing_workflow(self, system_deployment):
        """Test complete AI task processing workflow"""
        task_id = f"system_test_task_{int(time.time())}"

        # Create task
        task_data = {
            "task_id": task_id,
            "type": "analysis",
            "prompt": "Analyze the system performance and provide optimization recommendations",
            "parameters": {
                "complexity": "high",
                "require_code": True,
                "timeout": 60
            }
        }

        # Submit task
        async with httpx.AsyncClient(timeout=10) as client:
            submit_response = await client.post(
                "http://localhost:8787/api/tasks",
                json=task_data
            )
            assert submit_response.status_code == 201
            assert task_id in submit_response.json().get("task_id", "")

        # Monitor task progress
        max_wait_time = 120  # 2 minutes
        start_time = time.time()
        task_completed = False

        while time.time() - start_time < max_wait_time:
            async with httpx.AsyncClient(timeout=10) as client:
                status_response = await client.get(f"http://localhost:8787/api/tasks/{task_id}")
                if status_response.status_code == 200:
                    task_info = status_response.json()
                    if task_info.get("status") == "completed":
                        task_completed = True
                        break
                    elif task_info.get("status") == "failed":
                        pytest.fail(f"Task {task_id} failed: {task_info.get('error')}")

            await asyncio.sleep(5)

        assert task_completed, f"Task {task_id} did not complete within {max_wait_time} seconds"

        # Retrieve results
        async with httpx.AsyncClient(timeout=10) as client:
            result_response = await client.get(f"http://localhost:8787/api/results/{task_id}")
            assert result_response.status_code == 200
            result_data = result_response.json()

            assert "analysis" in result_data
            assert "recommendations" in result_data
            assert len(result_data["recommendations"]) > 0

    async def _access_webui(self) -> Dict[str, Any]:
        """Access WebUI interface"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("http://localhost:8787/")
                return {"success": response.status_code == 200, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _configure_settings(self) -> Dict[str, Any]:
        """Configure system settings"""
        try:
            settings_data = {
                "ai": {
                    "local_only": True,
                    "confidence_threshold": 0.75
                },
                "ui": {
                    "theme": "dark",
                    "auto_save": True
                }
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    "http://localhost:8787/api/settings",
                    json=settings_data
                )
                return {"success": response.status_code == 200, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _start_ai_interaction(self) -> Dict[str, Any]:
        """Start AI interaction"""
        try:
            interaction_data = {
                "type": "chat",
                "message": "Hello, I'm testing the system",
                "model": "local"
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    "http://localhost:8787/api/chat",
                    json=interaction_data
                )
                return {"success": response.status_code == 200, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _submit_first_task(self) -> Dict[str, Any]:
        """Submit first task"""
        try:
            task_data = {
                "type": "analysis",
                "prompt": "Analyze system status",
                "priority": "normal"
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    "http://localhost:8787/api/tasks",
                    json=task_data
                )
                return {"success": response.status_code == 201, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

class TestPerformanceAndScalability:
    """Test system performance and scalability"""

    @pytest.mark.asyncio
    async def test_baseline_performance(self, system_deployment, performance_monitor):
        """Test baseline system performance"""
        performance_monitor.start_monitoring()

        # Measure response times for key operations
        operations = [
            ("health_check", "GET", "http://localhost:8787/health"),
            ("server_status", "GET", "http://localhost:8787/api/servers/status"),
            ("model_info", "GET", "http://localhost:8787/api/models/available"),
            ("task_creation", "POST", "http://localhost:8787/api/tasks", {"type": "status", "prompt": "test"})
        ]

        response_times = []
        for op_name, method, url, *data in operations:
            performance_monitor.capture_metrics(f"performance_{op_name}")

            start_time = time.time()
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    if method == "GET":
                        response = await client.get(url)
                    else:
                        response = await client.post(url, json=data[0] if data else None)

                    response_time = time.time() - start_time
                    response_times.append(response_time)

                    assert response.status_code < 500, f"Operation {op_name} failed"
                    assert response_time < SYSTEM_TEST_CONFIG["performance_thresholds"]["response_time"], \
                        f"Operation {op_name} took {response_time:.2f}s, expected < {SYSTEM_TEST_CONFIG['performance_thresholds']['response_time']}s"

            except Exception as e:
                pytest.fail(f"Operation {op_name} failed with exception: {str(e)}")

        # Verify average response time
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.2f}s exceeds threshold"

        # Check performance summary
        perf_summary = performance_monitor.get_performance_summary()
        assert perf_summary["averages"]["cpu_percent"] < 50, "CPU usage too high during baseline test"
        assert perf_summary["averages"]["memory_percent"] < 70, "Memory usage too high during baseline test"

    @pytest.mark.asyncio
    async def test_load_handling(self, system_deployment, load_tester, performance_monitor):
        """Test system behavior under load"""
        performance_monitor.start_monitoring()

        # Run load test
        load_test_params = {
            "concurrent_users": 50,
            "duration": 60,  # 1 minute
            "requests_per_second": 100
        }

        print(f"[LOAD TEST] Starting load test with parameters: {load_test_params}")
        performance_monitor.capture_metrics("load_test_start")

        load_result = await load_tester.run_load_test(**load_test_params)

        print(f"[LOAD TEST] Results: {load_result}")
        performance_monitor.capture_metrics("load_test_end")

        # Verify load test results
        assert load_result["successful_requests"] > 0, "No successful requests during load test"
        assert load_result["failed_requests"] / load_result["total_requests"] < 0.05, \
            f"Error rate too high: {load_result['failed_requests']/load_result['total_requests']*100:.1f}%"

        assert load_result["average_response_time"] < SYSTEM_TEST_CONFIG["performance_thresholds"]["response_time"], \
            f"Average response time too high: {load_result['average_response_time']:.2f}s"

        # Check system stability under load
        perf_summary = performance_monitor.get_performance_summary()
        assert perf_summary["averages"]["cpu_percent"] < SYSTEM_TEST_CONFIG["performance_thresholds"]["cpu_limit"], \
            f"CPU usage too high under load: {perf_summary['averages']['cpu_percent']:.1f}%"

        assert perf_summary["averages"]["memory_percent"] < SYSTEM_TEST_CONFIG["performance_thresholds"]["memory_limit"], \
            f"Memory usage too high under load: {perf_summary['averages']['memory_percent']:.1f}%"

class TestDisasterRecovery:
    """Test disaster recovery scenarios"""

    @pytest.mark.asyncio
    async def test_service_crash_recovery(self, system_deployment):
        """Test system recovery when a service crashes"""
        # Verify initial system state
        initial_health = await self._check_all_services_health()
        assert all(initial_health.values()), "Not all services initially healthy"

        # Simulate service crash (find and kill a process)
        crashed_service = None
        for service_name, process in system_deployment.processes.items():
            if process.poll() is None:  # Process is running
                process.terminate()
                crashed_service = service_name
                break

        assert crashed_service, "No running service found to crash"

        print(f"[DISASTER] Simulated crash of service: {crashed_service}")

        # Wait for detection and recovery
        await asyncio.sleep(30)

        # Check if service was automatically restarted
        recovery_successful = False
        for attempt in range(3):  # Check for 3 minutes
            health_status = await self._check_all_services_health()
            if all(health_status.values()):
                recovery_successful = True
                break
            await asyncio.sleep(60)

        assert recovery_successful, f"System did not recover from {crashed_service} crash"

    @pytest.mark.asyncio
    async def test_high_load_recovery(self, system_deployment, load_tester):
        """Test system recovery after high load"""
        # Generate high load
        print(f"[DISASTER] Generating high load...")
        load_result = await load_tester.run_load_test(
            concurrent_users=200,
            duration=120,  # 2 minutes
            requests_per_second=500
        )

        print(f"[DISASTER] Load test completed: {load_result}")

        # Verify system is still functional after load
        await asyncio.sleep(30)  # Allow cooldown period

        # Test basic functionality
        recovery_tests = [
            ("webui_health", "http://localhost:8787/health"),
            ("api_functionality", "http://localhost:8787/api/servers/status"),
            ("task_creation", "http://localhost:8787/api/tasks")
        ]

        for test_name, url in recovery_tests:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    if test_name == "task_creation":
                        response = await client.post(url, json={"type": "status", "prompt": "recovery_test"})
                    else:
                        response = await client.get(url)

                    assert response.status_code < 500, f"Recovery test {test_name} failed"
            except Exception as e:
                pytest.fail(f"Recovery test {test_name} failed with exception: {str(e)}")

    async def _check_all_services_health(self) -> Dict[str, bool]:
        """Check health of all services"""
        services = ["webui", "terminal", "monitoring"]
        health_status = {}

        for service in services:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    port = {"webui": 8787, "terminal": 8788, "monitoring": 8789}[service]
                    response = await client.get(f"http://localhost:{port}/health")
                    health_status[service] = response.status_code == 200
            except Exception:
                health_status[service] = False

        return health_status

class TestSecurityValidation:
    """Test system security aspects"""

    @pytest.mark.asyncio
    async def test_access_control(self, system_deployment):
        """Test access control mechanisms"""
        # Test protected endpoints without authentication
        protected_endpoints = [
            "http://localhost:8787/api/admin/settings",
            "http://localhost:8787/api/users/list",
            "http://localhost:8787/api/system/config"
        ]

        for endpoint in protected_endpoints:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(endpoint)
                assert response.status_code == 401 or response.status_code == 403, \
                    f"Protected endpoint {endpoint} should require authentication"

    @pytest.mark.asyncio
    async def test_input_validation(self, system_deployment):
        """Test input validation and security"""
        # Test malicious input
        malicious_inputs = [
            {"prompt": "<script>alert('xss')</script>"},
            {"prompt": "'; DROP TABLE users; --"},
            {"prompt": "../../../../etc/passwd"},
            {"prompt": '{"__proto__": {"malicious": true}}'}
        ]

        for malicious_input in malicious_inputs:
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    response = await client.post(
                        "http://localhost:8787/api/tasks",
                        json=malicious_input,
                        timeout=10
                    )

                    # Should either reject the input or sanitize it safely
                    assert response.status_code != 500, \
                        f"Malicious input caused server error: {malicious_input}"

                    if response.status_code == 400:
                        # Good: Input was rejected
                        continue
                    elif response.status_code == 201:
                        # Check that response doesn't contain malicious content
                        response_text = response.text
                        assert "<script>" not in response_text, "XSS script not sanitized"
                        assert "DROP TABLE" not in response_text, "SQL injection not sanitized"
                    else:
                        # Other status codes might be acceptable depending on security policy
                        pass

                except Exception as e:
                    # Network errors or timeouts are acceptable for security testing
                    assert "timeout" in str(e).lower() or "connection" in str(e).lower(), \
                        f"Unexpected error with malicious input: {str(e)}"

class TestSystemResilience:
    """Test overall system resilience"""

    @pytest.mark.asyncio
    async def test_long_running_stability(self, system_deployment, performance_monitor):
        """Test system stability over extended period"""
        performance_monitor.start_monitoring()

        # Run system for extended period with periodic checks
        test_duration = 600  # 10 minutes
        check_interval = 60  # Check every minute
        checks_passed = 0
        total_checks = test_duration // check_interval

        print(f"[STABILITY] Starting long-running stability test ({test_duration}s)")

        start_time = time.time()
        while time.time() - start_time < test_duration:
            # Perform health check
            health_status = await self._check_all_services_health()

            # Perform basic functionality test
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get("http://localhost:8787/health")
                    functionality_ok = response.status_code == 200
                except Exception:
                    functionality_ok = False

                if all(health_status.values()) and functionality_ok:
                    checks_passed += 1

                performance_monitor.capture_metrics(f"stability_check_{checks_passed}")

                await asyncio.sleep(check_interval)

        # Verify stability
        stability_rate = checks_passed / total_checks
        assert stability_rate >= 0.95, \
            f"System stability too low: {stability_rate*100:.1f}% ({checks_passed}/{total_checks} checks passed)"

        # Check performance degradation
        perf_summary = performance_monitor.get_performance_summary()
        memory_growth = perf_summary["peaks"]["memory_percent"] - perf_summary["averages"]["memory_percent"]
        assert memory_growth < 20, f"Memory growth too high: {memory_growth:.1f}%"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
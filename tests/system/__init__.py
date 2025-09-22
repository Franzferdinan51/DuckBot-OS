"""
System Tests for DuckBot v4.2

This package contains comprehensive system tests that verify
the entire DuckBot system in production-like environments.
System tests focus on:

- Full system deployment testing
- End-to-end user workflows
- Production environment simulation
- Disaster recovery testing
- Performance and scalability testing
- Security penetration testing
- System reliability and resilience

System tests use real deployments and actual external dependencies.
"""

import pytest
import asyncio
import aiohttp
import httpx
import subprocess
import tempfile
import shutil
import psutil
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import sys
import os
from datetime import datetime, timedelta
import threading
import queue

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# System test configuration
SYSTEM_TEST_CONFIG = {
    "deployment_timeout": 300,  # 5 minutes for deployment
    "test_timeout": 600,  # 10 minutes for tests
    "production_mode": True,
    "external_services": {
        "enable_real_ai": False,  # Use real AI services
        "enable_real_database": True,
        "enable_real_messaging": False
    },
    "performance_thresholds": {
        "startup_time": 180,  # 3 minutes
        "response_time": 5.0,  # 5 seconds
        "memory_limit": 2048,  # 2GB
        "cpu_limit": 80,  # 80%
        "concurrent_users": 100
    },
    "disaster_scenarios": [
        "service_crash",
        "network_partition",
        "database_failure",
        "high_load",
        "resource_exhaustion"
    ]
}

# System deployment manager
class SystemDeployment:
    """Manage complete system deployment for testing"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or SYSTEM_TEST_CONFIG
        self.deployment_dir = None
        self.processes = {}
        self.services = {}
        self.is_deployed = False

    async def deploy_system(self) -> Dict[str, Any]:
        """Deploy complete DuckBot system for testing"""
        print("[DEPLOYMENT] Starting system deployment...")

        # Create deployment directory
        self.deployment_dir = Path(tempfile.mkdtemp(prefix="duckbot_system_test_"))
        print(f"[DEPLOYMENT] Deployment directory: {self.deployment_dir}")

        try:
            # Copy project files
            await self._copy_project_files()

            # Configure environment
            await self._configure_environment()

            # Start core services
            await self._start_core_services()

            # Verify deployment
            deployment_result = await self._verify_deployment()

            self.is_deployed = deployment_result["success"]
            return deployment_result

        except Exception as e:
            print(f"[DEPLOYMENT ERROR] {str(e)}")
            await self.cleanup()
            return {"success": False, "error": str(e)}

    async def _copy_project_files(self):
        """Copy project files to deployment directory"""
        project_root = Path(__file__).parent.parent.parent

        # Copy essential files
        essential_files = [
            "duckbot",
            "start_ecosystem.py",
            "ai_ecosystem_manager.py",
            "requirements.txt",
            "config"
        ]

        for item in essential_files:
            source = project_root / item
            if source.exists():
                dest = self.deployment_dir / item
                if source.is_dir():
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)

    async def _configure_environment(self):
        """Configure test environment"""
        env_file = self.deployment_dir / ".env"

        env_config = {
            "PYTHONPATH": str(self.deployment_dir),
            "DUCKBOT_TEST_MODE": "true",
            "DUCKBOT_LOG_LEVEL": "INFO",
            "DUCKBOT_WEBUI_PORT": "8787",
            "DUCKBOT_TERMINAL_PORT": "8788",
            "DUCKBOT_MONITORING_PORT": "8789",
            "DUCKBOT_LOCAL_ONLY": "true",
            "DUCKBOT_ENABLE_TESTS": "true"
        }

        with open(env_file, 'w') as f:
            for key, value in env_config.items():
                f.write(f"{key}={value}\n")

    async def _start_core_services(self):
        """Start core DuckBot services"""
        print("[DEPLOYMENT] Starting core services...")

        # Start ecosystem manager
        ecosystem_script = self.deployment_dir / "start_ecosystem.py"
        if ecosystem_script.exists():
            process = await self._start_process(
                [sys.executable, str(ecosystem_script)],
                cwd=str(self.deployment_dir),
                name="ecosystem_manager"
            )
            self.processes["ecosystem"] = process

        # Wait for services to start
        await asyncio.sleep(10)

        # Start individual services if ecosystem manager fails
        if not await self._check_service_health("ecosystem"):
            await self._start_fallback_services()

    async def _start_fallback_services(self):
        """Start services individually if ecosystem manager fails"""
        services = [
            ("webui", "python -m duckbot.webui"),
            ("terminal", "python -m duckbot.charm_terminal_ui"),
            ("monitoring", "python ai_ecosystem_manager.py")
        ]

        for service_name, command in services:
            process = await self._start_process(
                command.split(),
                cwd=str(self.deployment_dir),
                name=service_name
            )
            self.processes[service_name] = process

    async def _start_process(self, command: List[str], cwd: str, name: str) -> subprocess.Popen:
        """Start a subprocess and return process object"""
        env = os.environ.copy()
        env["PYTHONPATH"] = cwd

        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self._monitor_process,
            args=(process, name),
            daemon=True
        )
        monitor_thread.start()

        return process

    def _monitor_process(self, process: subprocess.Popen, name: str):
        """Monitor process output and health"""
        try:
            while process.poll() is None:
                # Check resource usage
                try:
                    ps_process = psutil.Process(process.pid)
                    memory_info = ps_process.memory_info()
                    cpu_percent = ps_process.cpu_percent()

                    if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
                        print(f"[WARNING] {name} memory usage high: {memory_info.rss / 1024 / 1024:.1f}MB")

                    if cpu_percent > 90:
                        print(f"[WARNING] {name} CPU usage high: {cpu_percent:.1f}%")

                except psutil.NoSuchProcess:
                    break

                time.sleep(5)

        except Exception as e:
            print(f"[MONITOR ERROR] {name}: {str(e)}")

    async def _check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            if service_name == "ecosystem":
                # Check if ecosystem manager is running
                return service_name in self.processes and self.processes[service_name].poll() is None
            else:
                # Check HTTP health endpoint
                port = self._get_service_port(service_name)
                if port:
                    async with httpx.AsyncClient(timeout=5) as client:
                        response = await client.get(f"http://localhost:{port}/health")
                        return response.status_code == 200
                return False
        except Exception:
            return False

    def _get_service_port(self, service_name: str) -> Optional[int]:
        """Get service port"""
        port_map = {
            "webui": 8787,
            "terminal": 8788,
            "monitoring": 8789
        }
        return port_map.get(service_name)

    async def _verify_deployment(self) -> Dict[str, Any]:
        """Verify that system deployment was successful"""
        print("[DEPLOYMENT] Verifying deployment...")

        results = {
            "success": True,
            "services": {},
            "errors": []
        }

        # Check each service
        services_to_check = ["webui", "terminal", "monitoring"]
        for service in services_to_check:
            is_healthy = await self._check_service_health(service)
            results["services"][service] = {
                "healthy": is_healthy,
                "port": self._get_service_port(service)
            }

            if not is_healthy:
                results["success"] = False
                results["errors"].append(f"Service {service} is not healthy")

        # Check system resources
        system_resources = self._get_system_resources()
        results["system_resources"] = system_resources

        return results

    def _get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids())
        }

    async def cleanup(self):
        """Clean up deployment"""
        print("[CLEANUP] Cleaning up deployment...")

        # Stop all processes
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                print(f"[CLEANUP ERROR] Failed to stop {name}: {str(e)}")

        # Remove deployment directory
        if self.deployment_dir and self.deployment_dir.exists():
            try:
                shutil.rmtree(self.deployment_dir)
            except Exception as e:
                print(f"[CLEANUP ERROR] Failed to remove deployment directory: {str(e)}")

        self.is_deployed = False

# System test scenarios
class SystemTestScenarios:
    """Define system test scenarios"""

    @staticmethod
    def get_user_workflows() -> List[Dict[str, Any]]:
        """Get user workflow test scenarios"""
        return [
            {
                "name": "New User Setup",
                "description": "Complete user onboarding workflow",
                "steps": [
                    {"action": "open_webui", "expected": "interface_loads"},
                    {"action": "configure_settings", "expected": "settings_saved"},
                    {"action": "start_ai_chat", "expected": "chat_ready"},
                    {"action": "submit_task", "expected": "task_accepted"}
                ]
            },
            {
                "name": "AI Task Processing",
                "description": "Complete AI task processing workflow",
                "steps": [
                    {"action": "create_analysis_task", "expected": "task_created"},
                    {"action": "monitor_progress", "expected": "progress_updates"},
                    {"action": "receive_results", "expected": "results_delivered"},
                    {"action": "save_results", "expected": "results_saved"}
                ]
            },
            {
                "name": "Multi-Service Coordination",
                "description": "Coordinate multiple services for complex task",
                "steps": [
                    {"action": "start_webui", "expected": "webui_running"},
                    {"action": "start_terminal", "expected": "terminal_running"},
                    {"action": "initiate_cross_service_task", "expected": "task_coordination_success"},
                    {"action": "verify_results", "expected": "all_services_completed"}
                ]
            }
        ]

    @staticmethod
    def get_disaster_scenarios() -> List[Dict[str, Any]]:
        """Get disaster recovery test scenarios"""
        return [
            {
                "name": "Service Crash Recovery",
                "description": "Test system recovery when a service crashes",
                "actions": [
                    {"action": "kill_service", "service": "webui"},
                    {"action": "wait_for_detection", "timeout": 30},
                    {"action": "verify_auto_restart", "expected": "service_restarted"},
                    {"action": "verify_functionality", "expected": "full_operation"}
                ]
            },
            {
                "name": "Network Partition",
                "description": "Test behavior during network partition",
                "actions": [
                    {"action": "simulate_network_partition", "services": ["webui", "ai"]},
                    {"action": "wait_for_timeout", "timeout": 60},
                    {"action": "verify_fallback_behavior", "expected": "degraded_mode"},
                    {"action": "restore_network", "expected": "recovery_complete"}
                ]
            },
            {
                "name": "High Load Stress Test",
                "description": "Test system under high load conditions",
                "actions": [
                    {"action": "generate_high_load", "requests_per_second": 100, "duration": 300},
                    {"action": "monitor_performance", "metrics": ["response_time", "error_rate"]},
                    {"action": "verify_stability", "expected": "no_crashes"},
                    {"action": "measure_recovery", "expected": "quick_recovery"}
                ]
            }
        ]

# Performance monitoring for system tests
class SystemPerformanceMonitor:
    """Monitor system performance during tests"""

    def __init__(self):
        self.metrics = []
        self.baseline_metrics = {}
        self.start_time = None

    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = datetime.now()
        self._capture_baseline()

    def _capture_baseline(self):
        """Capture baseline performance metrics"""
        self.baseline_metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "process_count": len(psutil.pids())
        }

    def capture_metrics(self, test_name: str):
        """Capture current performance metrics"""
        if not self.start_time:
            self.start_monitoring()

        current_metrics = {
            "test_name": test_name,
            "timestamp": datetime.now(),
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "process_count": len(psutil.pids())
        }

        # Calculate deltas from baseline
        for key in ["cpu_percent", "memory_percent", "disk_percent"]:
            if key in self.baseline_metrics:
                current_metrics[f"{key}_delta"] = current_metrics[key] - self.baseline_metrics[key]

        self.metrics.append(current_metrics)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {"status": "no_data"}

        summary = {
            "total_duration": self.metrics[-1]["elapsed_time"],
            "metrics_count": len(self.metrics),
            "averages": {},
            "peaks": {},
            "threshold_violations": []
        }

        # Calculate averages and peaks
        numeric_fields = ["cpu_percent", "memory_percent", "disk_percent"]
        for field in numeric_fields:
            values = [m[field] for m in self.metrics]
            summary["averages"][field] = sum(values) / len(values)
            summary["peaks"][field] = max(values)

            # Check against thresholds
            threshold = SYSTEM_TEST_CONFIG["performance_thresholds"].get(f"{field.split('_')[0]}_limit")
            if threshold:
                if summary["peaks"][field] > threshold:
                    summary["threshold_violations"].append({
                        "metric": field,
                        "peak": summary["peaks"][field],
                        "threshold": threshold
                    })

        return summary

# Load testing utilities
class LoadTester:
    """Generate load for system testing"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = queue.Queue()

    async def run_load_test(self, concurrent_users: int, duration: int, requests_per_second: int):
        """Run load test with specified parameters"""
        print(f"[LOAD TEST] Starting: {concurrent_users} users, {duration}s duration, {requests_per_second} req/s")

        # Create user tasks
        user_tasks = []
        for user_id in range(concurrent_users):
            task = self._simulate_user(user_id, duration, requests_per_second // concurrent_users)
            user_tasks.append(task)

        # Run all users concurrently
        start_time = datetime.now()
        await asyncio.gather(*user_tasks)
        end_time = datetime.now()

        # Collect results
        results = []
        while not self.results.empty():
            results.append(self.results.get())

        return {
            "total_requests": len(results),
            "duration": (end_time - start_time).total_seconds(),
            "successful_requests": sum(1 for r in results if r["success"]),
            "failed_requests": sum(1 for r in results if not r["success"]),
            "average_response_time": sum(r["response_time"] for r in results) / len(results) if results else 0,
            "requests_per_second": len(results) / (end_time - start_time).total_seconds() if results else 0
        }

    async def _simulate_user(self, user_id: int, duration: int, requests_per_second: int):
        """Simulate a single user making requests"""
        end_time = datetime.now() + timedelta(seconds=duration)
        request_interval = 1.0 / requests_per_second if requests_per_second > 0 else 1.0

        while datetime.now() < end_time:
            start_time = datetime.now()

            # Make request
            result = await self._make_request(user_id)
            self.results.put(result)

            # Calculate sleep time to maintain request rate
            request_duration = (datetime.now() - start_time).total_seconds()
            sleep_time = max(0, request_interval - request_duration)

            await asyncio.sleep(sleep_time)

    async def _make_request(self, user_id: int) -> Dict[str, Any]:
        """Make a single request"""
        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")

            return {
                "user_id": user_id,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "user_id": user_id,
                "success": False,
                "error": str(e),
                "response_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now()
            }

# System test fixtures
@pytest.fixture(scope="session")
def system_deployment():
    """Fixture providing system deployment"""
    deployment = SystemDeployment()

    # Deploy system
    result = asyncio.run(deployment.deploy_system())
    if not result["success"]:
        pytest.fail(f"System deployment failed: {result.get('error')}")

    yield deployment

    # Cleanup
    asyncio.run(deployment.cleanup())

@pytest.fixture(scope="session")
def performance_monitor():
    """Fixture providing performance monitor"""
    return SystemPerformanceMonitor()

@pytest.fixture(scope="session")
def load_tester():
    """Fixture providing load tester"""
    return LoadTester("http://localhost:8787")

@pytest.fixture(scope="session")
def test_scenarios():
    """Fixture providing test scenarios"""
    return SystemTestScenarios()

# Export utilities
__all__ = [
    "SystemDeployment",
    "SystemTestScenarios",
    "SystemPerformanceMonitor",
    "LoadTester",
    "SYSTEM_TEST_CONFIG"
]
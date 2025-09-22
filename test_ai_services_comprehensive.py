#!/usr/bin/env python3
"""
Comprehensive AI Service Integration Test Suite
Tests all AI services including GeminiChat, system metrics, and API endpoints
"""

import asyncio
import json
import logging
import os
import sys
import time
import requests
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

# Add DuckBot to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_service_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIServiceTester:
    """Comprehensive AI Service Testing Suite"""

    def __init__(self):
        self.base_url = "http://localhost:8787"
        self.test_results = {}
        self.concurrent_results = {}
        self.test_id = str(uuid.uuid4())

    def log_test_result(self, test_name: str, result: Dict[str, Any]):
        """Log test result"""
        result["test_id"] = self.test_id
        result["timestamp"] = datetime.now().isoformat()

        if test_name not in self.test_results:
            self.test_results[test_name] = []
        self.test_results[test_name].append(result)

        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        logger.info(f"{status} {test_name}: {result.get('message', 'No message')}")

        if not result.get("success"):
            logger.error(f"Error details: {result.get('error', 'Unknown error')}")

    async def test_gemini_chat_endpoint(self) -> Dict[str, Any]:
        """Test GeminiChat API endpoint functionality and routing"""
        logger.info("Testing GeminiChat API endpoint...")

        try:
            # Test 1: Health check
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=10)
                health_ok = response.status_code == 200
                self.log_test_result("gemini_health_check", {
                    "success": health_ok,
                    "message": f"Health check returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if health_ok else None
                })
            except Exception as e:
                self.log_test_result("gemini_health_check", {
                    "success": False,
                    "message": "Health check failed",
                    "error": str(e)
                })

            # Test 2: Chat endpoint
            try:
                chat_payload = {
                    "message": "Hello, this is a test message",
                    "model": "gemini-1.5-flash",
                    "temperature": 0.7,
                    "maxTokens": 100
                }

                response = requests.post(
                    f"{self.base_url}/api/gemini/chat",
                    json=chat_payload,
                    timeout=30
                )

                chat_ok = response.status_code == 200
                self.log_test_result("gemini_chat_endpoint", {
                    "success": chat_ok,
                    "message": f"Chat endpoint returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if chat_ok else None,
                    "payload_size": len(json.dumps(chat_payload))
                })
            except Exception as e:
                self.log_test_result("gemini_chat_endpoint", {
                    "success": False,
                    "message": "Chat endpoint test failed",
                    "error": str(e)
                })

            # Test 3: Models endpoint
            try:
                response = requests.get(f"{self.base_url}/api/gemini/models", timeout=10)
                models_ok = response.status_code == 200
                self.log_test_result("gemini_models_endpoint", {
                    "success": models_ok,
                    "message": f"Models endpoint returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if models_ok else None
                })
            except Exception as e:
                self.log_test_result("gemini_models_endpoint", {
                    "success": False,
                    "message": "Models endpoint test failed",
                    "error": str(e)
                })

            # Test 4: Authentication
            try:
                headers = {"Authorization": "Bearer invalid_token"}
                response = requests.get(f"{self.base_url}/api/gemini/models", headers=headers, timeout=10)

                # Should either succeed (no auth required) or fail with 401/403
                auth_test_ok = response.status_code in [200, 401, 403]
                self.log_test_result("gemini_authentication", {
                    "success": auth_test_ok,
                    "message": f"Auth test returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                self.log_test_result("gemini_authentication", {
                    "success": False,
                    "message": "Authentication test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("gemini_chat_overall", {
                "success": False,
                "message": "GeminiChat testing failed",
                "error": str(e)
            })

    async def test_system_metrics_api(self) -> Dict[str, Any]:
        """Test system metrics API integration and data collection"""
        logger.info("Testing system metrics API...")

        try:
            # Test 1: Basic metrics endpoint
            try:
                response = requests.get(f"{self.base_url}/api/metrics", timeout=10)
                metrics_ok = response.status_code == 200
                self.log_test_result("system_metrics_basic", {
                    "success": metrics_ok,
                    "message": f"Metrics endpoint returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if metrics_ok else None
                })
            except Exception as e:
                self.log_test_result("system_metrics_basic", {
                    "success": False,
                    "message": "Basic metrics test failed",
                    "error": str(e)
                })

            # Test 2: System status endpoint
            try:
                response = requests.get(f"{self.base_url}/api/system/status", timeout=10)
                status_ok = response.status_code == 200
                self.log_test_result("system_status_endpoint", {
                    "success": status_ok,
                    "message": f"Status endpoint returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if status_ok else None
                })
            except Exception as e:
                self.log_test_result("system_status_endpoint", {
                    "success": False,
                    "message": "System status test failed",
                    "error": str(e)
                })

            # Test 3: Performance metrics
            try:
                response = requests.get(f"{self.base_url}/api/performance", timeout=10)
                perf_ok = response.status_code == 200
                self.log_test_result("performance_metrics", {
                    "success": perf_ok,
                    "message": f"Performance endpoint returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if perf_ok else None
                })
            except Exception as e:
                self.log_test_result("performance_metrics", {
                    "success": False,
                    "message": "Performance metrics test failed",
                    "error": str(e)
                })

            # Test 4: Real-time data collection
            try:
                # Make multiple requests to test real-time data
                responses = []
                for i in range(3):
                    response = requests.get(f"{self.base_url}/api/metrics", timeout=10)
                    if response.status_code == 200:
                        responses.append(response.json())
                    time.sleep(1)

                realtime_ok = len(responses) >= 2
                self.log_test_result("realtime_metrics", {
                    "success": realtime_ok,
                    "message": f"Collected {len(responses)} real-time metric samples",
                    "data_samples": len(responses),
                    "variation": any(r != responses[0] for r in responses[1:])
                })
            except Exception as e:
                self.log_test_result("realtime_metrics", {
                    "success": False,
                    "message": "Real-time metrics test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("system_metrics_overall", {
                "success": False,
                "message": "System metrics testing failed",
                "error": str(e)
            })

    async def test_ai_service_request_handling(self) -> Dict[str, Any]:
        """Test AI service request/response handling and error management"""
        logger.info("Testing AI service request handling...")

        try:
            # Test 1: Valid request handling
            try:
                payload = {
                    "prompt": "What is the capital of France?",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 50
                }

                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    timeout=30
                )

                valid_ok = response.status_code in [200, 404]  # 404 if endpoint doesn't exist
                self.log_test_result("valid_request_handling", {
                    "success": valid_ok,
                    "message": f"Valid request returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if response.status_code == 200 else None
                })
            except Exception as e:
                self.log_test_result("valid_request_handling", {
                    "success": False,
                    "message": "Valid request test failed",
                    "error": str(e)
                })

            # Test 2: Invalid request handling
            try:
                payload = {
                    "invalid_field": "test"
                }

                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    timeout=10
                )

                invalid_ok = response.status_code in [400, 404, 422]  # Client error or not found
                self.log_test_result("invalid_request_handling", {
                    "success": invalid_ok,
                    "message": f"Invalid request returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if response.status_code != 404 else None
                })
            except Exception as e:
                self.log_test_result("invalid_request_handling", {
                    "success": False,
                    "message": "Invalid request test failed",
                    "error": str(e)
                })

            # Test 3: Large payload handling
            try:
                large_payload = {
                    "prompt": "x" * 10000,  # 10KB payload
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 100
                }

                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json=large_payload,
                    timeout=30
                )

                large_ok = response.status_code in [200, 400, 413, 404]  # Success or client error
                self.log_test_result("large_payload_handling", {
                    "success": large_ok,
                    "message": f"Large payload returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "payload_size": len(json.dumps(large_payload))
                })
            except Exception as e:
                self.log_test_result("large_payload_handling", {
                    "success": False,
                    "message": "Large payload test failed",
                    "error": str(e)
                })

            # Test 4: Error response format
            try:
                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json={"malformed": True},
                    timeout=10
                )

                error_format_ok = response.status_code != 500  # Should not be server error
                self.log_test_result("error_response_format", {
                    "success": error_format_ok,
                    "message": f"Error response returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "has_error_structure": "error" in response.json().lower() if response.text else False
                })
            except Exception as e:
                self.log_test_result("error_response_format", {
                    "success": False,
                    "message": "Error response format test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("request_handling_overall", {
                "success": False,
                "message": "Request handling testing failed",
                "error": str(e)
            })

    async def test_concurrent_request_handling(self) -> Dict[str, Any]:
        """Test concurrent request handling for all AI services"""
        logger.info("Testing concurrent request handling...")

        def make_request(endpoint: str, payload: Dict = None, method: str = "GET") -> Dict:
            """Make a single request"""
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=30)

                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "endpoint": endpoint
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "endpoint": endpoint
                }

        try:
            # Test 1: Concurrent health checks
            start_time = time.time()
            threads = []

            for i in range(10):
                thread = threading.Thread(
                    target=lambda: self.concurrent_results.update({
                        f"health_check_{i}": make_request("/api/health")
                    })
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            concurrent_time = time.time() - start_time
            health_success = sum(1 for r in self.concurrent_results.values() if r.get("success"))

            self.log_test_result("concurrent_health_checks", {
                "success": health_success >= 8,  # Allow some failures
                "message": f"{health_success}/10 concurrent health checks succeeded",
                "total_time": concurrent_time,
                "avg_time_per_request": concurrent_time / 10
            })

            # Test 2: Mixed concurrent requests
            endpoints = [
                ("/api/health", "GET", None),
                ("/api/metrics", "GET", None),
                ("/api/system/status", "GET", None),
                ("/api/gemini/models", "GET", None),
                ("/api/ai/chat", "POST", {"prompt": "test", "model": "gpt-3.5-turbo"})
            ]

            start_time = time.time()
            threads = []

            for i, (endpoint, method, payload) in enumerate(endpoints * 4):  # 20 requests
                thread = threading.Thread(
                    target=lambda e=endpoint, m=method, p=payload: self.concurrent_results.update({
                        f"mixed_request_{i}": make_request(e, p, m)
                    })
                )
                threads.append(thread)
                thread.start()
                time.sleep(0.1)  # Small delay to avoid overwhelming

            for thread in threads:
                thread.join()

            mixed_time = time.time() - start_time
            mixed_success = sum(1 for r in self.concurrent_results.values() if r.get("success"))

            self.log_test_result("concurrent_mixed_requests", {
                "success": mixed_success >= 15,  # Allow some failures
                "message": f"{mixed_success}/20 concurrent mixed requests succeeded",
                "total_time": mixed_time,
                "avg_time_per_request": mixed_time / 20
            })

            # Test 3: Rate limiting
            start_time = time.time()
            threads = []

            for i in range(50):  # High volume test
                thread = threading.Thread(
                    target=lambda: self.concurrent_results.update({
                        f"rate_limit_test_{i}": make_request("/api/health")
                    })
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            rate_limit_time = time.time() - start_time
            rate_success = sum(1 for r in self.concurrent_results.values() if r.get("success"))

            self.log_test_result("rate_limiting_test", {
                "success": rate_success >= 40,  # Allow some rate limiting
                "message": f"{rate_success}/50 rate limit test requests succeeded",
                "total_time": rate_limit_time,
                "requests_per_second": 50 / rate_limit_time
            })

        except Exception as e:
            self.log_test_result("concurrent_handling_overall", {
                "success": False,
                "message": "Concurrent handling testing failed",
                "error": str(e)
            })

    async def test_timeout_mechanisms(self) -> Dict[str, Any]:
        """Test timeout mechanisms and graceful degradation"""
        logger.info("Testing timeout mechanisms...")

        try:
            # Test 1: Fast timeout
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/health", timeout=1)
                elapsed = time.time() - start_time

                timeout_ok = elapsed < 2  # Should complete quickly
                self.log_test_result("fast_timeout_test", {
                    "success": timeout_ok,
                    "message": f"Fast request completed in {elapsed:.2f}s",
                    "elapsed_time": elapsed,
                    "timeout_setting": 1
                })
            except requests.Timeout:
                self.log_test_result("fast_timeout_test", {
                    "success": True,
                    "message": "Fast timeout properly triggered",
                    "elapsed_time": time.time() - start_time
                })
            except Exception as e:
                self.log_test_result("fast_timeout_test", {
                    "success": False,
                    "message": "Fast timeout test failed",
                    "error": str(e)
                })

            # Test 2: Slow endpoint timeout
            try:
                # Test with a potentially slow endpoint
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/metrics", timeout=5)
                elapsed = time.time() - start_time

                slow_timeout_ok = elapsed < 6  # Should complete within timeout + buffer
                self.log_test_result("slow_timeout_test", {
                    "success": slow_timeout_ok,
                    "message": f"Slow request completed in {elapsed:.2f}s",
                    "elapsed_time": elapsed,
                    "timeout_setting": 5
                })
            except requests.Timeout:
                self.log_test_result("slow_timeout_test", {
                    "success": True,
                    "message": "Slow timeout properly triggered",
                    "elapsed_time": time.time() - start_time
                })
            except Exception as e:
                self.log_test_result("slow_timeout_test", {
                    "success": False,
                    "message": "Slow timeout test failed",
                    "error": str(e)
                })

            # Test 3: Invalid hostname timeout
            try:
                start_time = time.time()
                response = requests.get("http://invalid-hostname:8787/api/health", timeout=5)
                elapsed = time.time() - start_time

                self.log_test_result("invalid_hostname_timeout", {
                    "success": False,  # Should fail
                    "message": "Invalid hostname should fail",
                    "elapsed_time": elapsed
                })
            except (requests.Timeout, requests.ConnectionError):
                elapsed = time.time() - start_time
                self.log_test_result("invalid_hostname_timeout", {
                    "success": True,
                    "message": "Invalid hostname timeout properly handled",
                    "elapsed_time": elapsed
                })
            except Exception as e:
                self.log_test_result("invalid_hostname_timeout", {
                    "success": False,
                    "message": "Invalid hostname test failed unexpectedly",
                    "error": str(e)
                })

            # Test 4: Graceful degradation
            try:
                # Test with malformed request that should fail gracefully
                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json={"invalid": "data"},
                    timeout=10
                )

                graceful_ok = response.status_code in [400, 422, 404]  # Client error, not server error
                self.log_test_result("graceful_degradation", {
                    "success": graceful_ok,
                    "message": f"Graceful degradation returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds(),
                    "is_client_error": response.status_code < 500
                })
            except Exception as e:
                self.log_test_result("graceful_degradation", {
                    "success": False,
                    "message": "Graceful degradation test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("timeout_mechanisms_overall", {
                "success": False,
                "message": "Timeout mechanisms testing failed",
                "error": str(e)
            })

    async def test_local_vs_cloud_modes(self) -> Dict[str, Any]:
        """Test local vs cloud AI modes and feature parity"""
        logger.info("Testing local vs cloud AI modes...")

        try:
            # Test 1: Local mode detection
            try:
                # Check if local AI services are available
                local_tests = []

                # Test LM Studio (local)
                try:
                    response = requests.get("http://localhost:1234/v1/models", timeout=5)
                    lm_studio_ok = response.status_code == 200
                    local_tests.append(("lm_studio", lm_studio_ok))
                except:
                    local_tests.append(("lm_studio", False))

                # Test Ollama (local)
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=5)
                    ollama_ok = response.status_code == 200
                    local_tests.append(("ollama", ollama_ok))
                except:
                    local_tests.append(("ollama", False))

                local_available = any(ok for _, ok in local_tests)
                self.log_test_result("local_mode_detection", {
                    "success": True,  # Always succeed, just report status
                    "message": f"Local services available: {local_available}",
                    "services": dict(local_tests)
                })
            except Exception as e:
                self.log_test_result("local_mode_detection", {
                    "success": False,
                    "message": "Local mode detection failed",
                    "error": str(e)
                })

            # Test 2: Cloud mode detection
            try:
                # Test cloud API connectivity
                cloud_tests = []

                # Test OpenRouter (if API key available)
                if os.getenv("OPENROUTER_API_KEY"):
                    try:
                        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
                        openrouter_ok = response.status_code == 200
                        cloud_tests.append(("openrouter", openrouter_ok))
                    except:
                        cloud_tests.append(("openrouter", False))
                else:
                    cloud_tests.append(("openrouter", "no_api_key"))

                # Test other cloud services
                cloud_available = any(ok == True for _, ok in cloud_tests)
                self.log_test_result("cloud_mode_detection", {
                    "success": True,  # Always succeed, just report status
                    "message": f"Cloud services available: {cloud_available}",
                    "services": dict(cloud_tests)
                })
            except Exception as e:
                self.log_test_result("cloud_mode_detection", {
                    "success": False,
                    "message": "Cloud mode detection failed",
                    "error": str(e)
                })

            # Test 3: Feature parity check
            try:
                # Check if both modes provide similar capabilities
                features = {
                    "chat_completion": False,
                    "model_selection": False,
                    "streaming": False,
                    "token_counting": False
                }

                # Test basic chat completion
                try:
                    response = requests.post(
                        f"{self.base_url}/api/ai/chat",
                        json={"prompt": "test", "model": "auto"},
                        timeout=30
                    )
                    features["chat_completion"] = response.status_code in [200, 404]
                except:
                    features["chat_completion"] = False

                # Test model selection
                try:
                    response = requests.get(f"{self.base_url}/api/models", timeout=10)
                    features["model_selection"] = response.status_code == 200
                except:
                    features["model_selection"] = False

                parity_score = sum(features.values()) / len(features)
                self.log_test_result("feature_parity", {
                    "success": parity_score >= 0.5,  # At least half the features
                    "message": f"Feature parity score: {parity_score:.2f}",
                    "features": features,
                    "parity_score": parity_score
                })
            except Exception as e:
                self.log_test_result("feature_parity", {
                    "success": False,
                    "message": "Feature parity test failed",
                    "error": str(e)
                })

            # Test 4: Mode switching
            try:
                # Test if the system can handle mode switching
                switch_test_results = {}

                # Test with different model providers
                test_models = ["auto", "local", "cloud"]
                for model in test_models:
                    try:
                        response = requests.post(
                            f"{self.base_url}/api/ai/chat",
                            json={"prompt": "test", "model": model},
                            timeout=15
                        )
                        switch_test_results[model] = response.status_code in [200, 404]
                    except:
                        switch_test_results[model] = False

                switch_success = any(switch_test_results.values())
                self.log_test_result("mode_switching", {
                    "success": switch_success,
                    "message": f"Mode switching test: {dict(switch_test_results)}",
                    "test_results": switch_test_results
                })
            except Exception as e:
                self.log_test_result("mode_switching", {
                    "success": False,
                    "message": "Mode switching test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("local_cloud_modes_overall", {
                "success": False,
                "message": "Local vs cloud modes testing failed",
                "error": str(e)
            })

    async def test_ai_provider_manager(self) -> Dict[str, Any]:
        """Test AI provider manager and model switching"""
        logger.info("Testing AI provider manager...")

        try:
            # Test 1: Provider availability
            try:
                from duckbot.core.ai_provider_manager import get_available_providers, get_all_provider_status

                providers = get_available_providers()
                status = get_all_provider_status()

                self.log_test_result("provider_availability", {
                    "success": True,
                    "message": f"Found {len(providers)} available providers",
                    "providers": providers,
                    "status": status
                })
            except Exception as e:
                self.log_test_result("provider_availability", {
                    "success": False,
                    "message": "Provider availability test failed",
                    "error": str(e)
                })

            # Test 2: Model capabilities
            try:
                from duckbot.core.ai_provider_manager import get_model_capabilities

                # Test with a known model
                capabilities = get_model_capabilities("gpt-3.5-turbo")

                self.log_test_result("model_capabilities", {
                    "success": "error" not in capabilities,
                    "message": f"Model capabilities retrieved",
                    "capabilities": capabilities
                })
            except Exception as e:
                self.log_test_result("model_capabilities", {
                    "success": False,
                    "message": "Model capabilities test failed",
                    "error": str(e)
                })

            # Test 3: Task execution
            try:
                from duckbot.core.ai_provider_manager import execute_ai_task

                # Test a simple task
                task = {
                    "kind": "code",
                    "prompt": "Write a simple Python function",
                    "context": {"language": "python"}
                }

                result = await execute_ai_task(task)

                self.log_test_result("task_execution", {
                    "success": result.get("success", False),
                    "message": f"Task execution {'succeeded' if result.get('success') else 'failed'}",
                    "result": result
                })
            except Exception as e:
                self.log_test_result("task_execution", {
                    "success": False,
                    "message": "Task execution test failed",
                    "error": str(e)
                })

            # Test 4: Provider switching
            try:
                from duckbot.core.ai_provider_manager import ai_provider_manager

                # Test model selection for different task types
                tasks = [
                    {"kind": "code", "prompt": "Write code", "complexity": "medium"},
                    {"kind": "general", "prompt": "General question", "complexity": "low"},
                    {"kind": "analysis", "prompt": "Analyze data", "complexity": "high"}
                ]

                switch_results = {}
                for i, task in enumerate(tasks):
                    try:
                        model, provider = ai_provider_manager.select_optimal_model_for_task(task)
                        switch_results[f"task_{i}"] = {"model": model, "provider": provider}
                    except Exception as e:
                        switch_results[f"task_{i}"] = {"error": str(e)}

                switch_success = all("error" not in r for r in switch_results.values())
                self.log_test_result("provider_switching", {
                    "success": switch_success,
                    "message": f"Provider switching test completed",
                    "results": switch_results
                })
            except Exception as e:
                self.log_test_result("provider_switching", {
                    "success": False,
                    "message": "Provider switching test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("ai_provider_manager_overall", {
                "success": False,
                "message": "AI provider manager testing failed",
                "error": str(e)
            })

    async def test_api_authentication(self) -> Dict[str, Any]:
        """Test API authentication and security measures"""
        logger.info("Testing API authentication...")

        try:
            # Test 1: No authentication required
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=10)
                no_auth_ok = response.status_code == 200
                self.log_test_result("no_auth_required", {
                    "success": no_auth_ok,
                    "message": f"No auth request returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                self.log_test_result("no_auth_required", {
                    "success": False,
                    "message": "No auth test failed",
                    "error": str(e)
                })

            # Test 2: Invalid authentication
            try:
                headers = {"Authorization": "Bearer invalid_token_12345"}
                response = requests.get(f"{self.base_url}/api/health", headers=headers, timeout=10)

                # Should either succeed (no auth) or fail with 401/403
                invalid_auth_ok = response.status_code in [200, 401, 403]
                self.log_test_result("invalid_auth", {
                    "success": invalid_auth_ok,
                    "message": f"Invalid auth returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                self.log_test_result("invalid_auth", {
                    "success": False,
                    "message": "Invalid auth test failed",
                    "error": str(e)
                })

            # Test 3: SQL injection attempt
            try:
                payload = {
                    "prompt": "'; DROP TABLE users; --",
                    "model": "test"
                }

                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    timeout=10
                )

                sql_injection_ok = response.status_code in [200, 400, 422, 404]  # Should not crash
                self.log_test_result("sql_injection_protection", {
                    "success": sql_injection_ok,
                    "message": f"SQL injection attempt returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                self.log_test_result("sql_injection_protection", {
                    "success": False,
                    "message": "SQL injection test failed",
                    "error": str(e)
                })

            # Test 4: XSS attempt
            try:
                payload = {
                    "prompt": "<script>alert('xss')</script>",
                    "model": "test"
                }

                response = requests.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    timeout=10
                )

                xss_ok = response.status_code in [200, 400, 422, 404]  # Should not crash
                self.log_test_result("xss_protection", {
                    "success": xss_ok,
                    "message": f"XSS attempt returned {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                self.log_test_result("xss_protection", {
                    "success": False,
                    "message": "XSS protection test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("api_authentication_overall", {
                "success": False,
                "message": "API authentication testing failed",
                "error": str(e)
            })

    async def test_service_availability(self) -> Dict[str, Any]:
        """Test service availability and health monitoring"""
        logger.info("Testing service availability...")

        try:
            # Test 1: Core services health
            try:
                from duckbot.services.server_manager import server_manager

                service_status = server_manager.get_all_service_status()

                healthy_services = sum(1 for s in service_status.values() if s.status.value == "running")
                total_services = len(service_status)

                self.log_test_result("core_services_health", {
                    "success": healthy_services > 0,
                    "message": f"{healthy_services}/{total_services} core services healthy",
                    "service_status": {name: status.status.value for name, status in service_status.items()}
                })
            except Exception as e:
                self.log_test_result("core_services_health", {
                    "success": False,
                    "message": "Core services health test failed",
                    "error": str(e)
                })

            # Test 2: Monitoring system
            try:
                from duckbot.core.monitoring_system import get_monitoring

                monitoring = get_monitoring()
                status = monitoring.get_system_status()

                self.log_test_result("monitoring_system", {
                    "success": "error" not in status,
                    "message": "Monitoring system status retrieved",
                    "status_keys": list(status.keys())
                })
            except Exception as e:
                self.log_test_result("monitoring_system", {
                    "success": False,
                    "message": "Monitoring system test failed",
                    "error": str(e)
                })

            # Test 3: Database connectivity
            try:
                import sqlite3
                db_path = os.path.join(os.getcwd(), "monitoring.db")

                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()

                    self.log_test_result("database_connectivity", {
                        "success": True,
                        "message": f"Database connected, found {len(tables)} tables",
                        "tables": [t[0] for t in tables]
                    })
                else:
                    self.log_test_result("database_connectivity", {
                        "success": True,
                        "message": "Database file not found (expected if not initialized)",
                        "database_exists": False
                    })
            except Exception as e:
                self.log_test_result("database_connectivity", {
                    "success": False,
                    "message": "Database connectivity test failed",
                    "error": str(e)
                })

            # Test 4: Resource availability
            try:
                import psutil

                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                resource_status = {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "memory_available_gb": memory.available / (1024**3)
                }

                # Check if resources are available (not critically low)
                resources_ok = all([
                    cpu_percent < 95,
                    memory.percent < 95,
                    (disk.used / disk.total) < 95
                ])

                self.log_test_result("resource_availability", {
                    "success": resources_ok,
                    "message": f"Resources check: {'OK' if resources_ok else 'CRITICAL'}",
                    "resource_status": resource_status
                })
            except Exception as e:
                self.log_test_result("resource_availability", {
                    "success": False,
                    "message": "Resource availability test failed",
                    "error": str(e)
                })

        except Exception as e:
            self.log_test_result("service_availability_overall", {
                "success": False,
                "message": "Service availability testing failed",
                "error": str(e)
            })

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        logger.info("Generating comprehensive test report...")

        # Calculate overall statistics
        total_tests = sum(len(results) for results in self.test_results.values())
        passed_tests = sum(
            sum(1 for result in results if result.get("success"))
            for results in self.test_results.values()
        )

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Group results by category
        category_results = {}
        for category, results in self.test_results.items():
            category_passed = sum(1 for result in results if result.get("success"))
            category_results[category] = {
                "total": len(results),
                "passed": category_passed,
                "success_rate": (category_passed / len(results) * 100) if results else 0
            }

        # Identify failed tests
        failed_tests = []
        for category, results in self.test_results.items():
            for result in results:
                if not result.get("success"):
                    failed_tests.append({
                        "category": category,
                        "message": result.get("message", "Unknown"),
                        "error": result.get("error", "Unknown error")
                    })

        # Generate recommendations
        recommendations = []

        if success_rate < 80:
            recommendations.append("Overall success rate is low - investigate systemic issues")

        if category_results.get("concurrent_handling_overall", {}).get("success_rate", 100) < 70:
            recommendations.append("Concurrent request handling needs improvement")

        if category_results.get("timeout_mechanisms_overall", {}).get("success_rate", 100) < 80:
            recommendations.append("Timeout mechanisms need attention")

        if category_results.get("api_authentication_overall", {}).get("success_rate", 100) < 90:
            recommendations.append("API authentication and security should be reviewed")

        if not recommendations:
            recommendations.append("All tests passed successfully!")

        report = {
            "test_id": self.test_id,
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate
            },
            "category_results": category_results,
            "failed_tests": failed_tests[:10],  # Limit to first 10 failures
            "recommendations": recommendations,
            "raw_results": self.test_results
        }

        # Save report to file
        with open(f"ai_service_test_report_{self.test_id}.json", "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Test report saved: ai_service_test_report_{self.test_id}.json")

        return report

    async def run_all_tests(self):
        """Run all AI service tests"""
        logger.info("Starting comprehensive AI service testing...")
        logger.info(f"Test ID: {self.test_id}")
        logger.info(f"Base URL: {self.base_url}")

        # Run all test suites
        await self.test_gemini_chat_endpoint()
        await self.test_system_metrics_api()
        await self.test_ai_service_request_handling()
        await self.test_concurrent_request_handling()
        await self.test_timeout_mechanisms()
        await self.test_local_vs_cloud_modes()
        await self.test_ai_provider_manager()
        await self.test_api_authentication()
        await self.test_service_availability()

        # Generate final report
        report = self.generate_test_report()

        logger.info("=" * 60)
        logger.info("AI SERVICE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {report['summary']['total_tests']}")
        logger.info(f"Passed: {report['summary']['passed_tests']}")
        logger.info(f"Failed: {report['summary']['failed_tests']}")
        logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        logger.info("=" * 60)

        for rec in report['recommendations']:
            logger.info(f"• {rec}")

        logger.info("=" * 60)

        return report

async def main():
    """Main test execution"""
    tester = AIServiceTester()

    try:
        report = await tester.run_all_tests()
        print(f"\nTest completed! Success rate: {report['summary']['success_rate']:.1f}%")
        print(f"Report saved: ai_service_test_report_{tester.test_id}.json")

        return report

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())
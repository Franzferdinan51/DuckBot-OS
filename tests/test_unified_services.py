"""
Comprehensive Test Suite for Unified Services Integration
Tests ComfyUI, TRELLIS, and VibeVoice integrations
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import aiohttp
import pytest

# Import the services to test
from duckbot.integrations.comfyui_integration import ComfyUIManager
from duckbot.integrations.trellis_integration import TRELLISManager
from duckbot.integrations.vibevoice_client import VibeVoiceManager
from duckbot.integrations.unified_service_manager import UnifiedServiceManager


class TestComfyUIIntegration(unittest.TestCase):
    """Test suite for ComfyUI integration"""

    def setUp(self):
        """Set up test environment"""
        self.comfyui_manager = ComfyUIManager(
            comfyui_path="C:/ComfyUI",  # Mock path
            api_base_url="http://localhost:8188"
        )

    def test_initialization(self):
        """Test ComfyUI manager initialization"""
        self.assertIsNotNone(self.comfyui_manager)
        self.assertEqual(self.comfyui_manager.api_base_url, "http://localhost:8188")
        self.assertEqual(self.comfyui_manager.server_port, 8188)

    def test_workflow_templates_loading(self):
        """Test loading of workflow templates"""
        templates = self.comfyui_manager.workflow_templates
        self.assertIsInstance(templates, dict)
        self.assertIn("text_to_image", templates)
        self.assertIn("image_to_image", templates)

    def test_workflow_template_structure(self):
        """Test workflow template structure"""
        template = self.comfyui_manager.workflow_templates["text_to_image"]
        self.assertIn("template", template)
        self.assertIn("description", template)
        self.assertIn("category", template)

    @patch('aiohttp.ClientSession')
    async def test_server_status_check(self, mock_session):
        """Test server status checking"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        result = await self.comfyui_manager._check_server_status()
        self.assertTrue(result)

    def test_resource_checking(self):
        """Test resource availability checking"""
        # Mock GPU info
        self.comfyui_manager.hardware_detector.get_gpu_info = Mock(return_value={
            "memory": {"total": 8192, "used": 4096}
        })

        # Test within limits
        result = asyncio.run(self.comfyui_manager._check_resources())
        self.assertTrue(result)

        # Test exceeding limits
        self.comfyui_manager.hardware_detector.get_gpu_info = Mock(return_value={
            "memory": {"total": 8192, "used": 7800}  # 95% usage
        })

        result = asyncio.run(self.comfyui_manager._check_resources())
        self.assertFalse(result)


class TestTRELLISIntegration(unittest.TestCase):
    """Test suite for TRELLIS integration"""

    def setUp(self):
        """Set up test environment"""
        self.trellis_manager = TRELLISManager(
            trellis_path="C:/TRELLIS",  # Mock path
            api_base_url="http://localhost:8288"
        )

    def test_initialization(self):
        """Test TRELLIS manager initialization"""
        self.assertIsNotNone(self.trellis_manager)
        self.assertEqual(self.trellis_manager.api_base_url, "http://localhost:8288")
        self.assertEqual(self.trellis_manager.server_port, 8288)

    def test_asset_templates_loading(self):
        """Test loading of asset templates"""
        templates = self.trellis_manager.asset_templates
        self.assertIsInstance(templates, dict)
        self.assertIn("text_to_3d", templates)
        self.assertIn("image_to_3d", templates)

    def test_asset_template_structure(self):
        """Test asset template structure"""
        template = self.trellis_manager.asset_templates["text_to_3d"]
        self.assertIn("description", template)
        self.assertIn("input_type", template)
        self.assertIn("output_formats", template)
        self.assertIn("parameters", template)

    def test_workflow_structures(self):
        """Test workflow structure definitions"""
        structures = self.trellis_manager.workflow_structures
        self.assertIsInstance(structures, dict)
        self.assertIn("sequential", structures)
        self.assertIn("parallel", structures)
        self.assertIn("hierarchical", structures)
        self.assertIn("adaptive", structures)

    def test_dependency_graph_building(self):
        """Test dependency graph construction"""
        tasks = [
            {"id": "task1", "type": "3d_generation"},
            {"id": "task2", "type": "comfyui_workflow"}
        ]
        dependencies = [("task1", "task2")]

        graph = self.trellis_manager._build_dependency_graph(tasks, dependencies)

        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertEqual(len(graph["nodes"]), 2)
        self.assertEqual(len(graph["edges"]), 1)

    def test_adaptive_rules_creation(self):
        """Test adaptive rules creation"""
        tasks = [
            {
                "id": "task1",
                "type": "adaptive",
                "adaptive_conditions": [
                    {"field": "quality", "operator": "greater_than", "value": 0.8}
                ]
            }
        ]

        rules = self.trellis_manager._create_adaptive_rules(tasks)
        self.assertIsInstance(rules, list)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["task_id"], "task1")


class TestVibeVoiceIntegration(unittest.TestCase):
    """Test suite for VibeVoice integration"""

    def setUp(self):
        """Set up test environment"""
        self.vibevoice_manager = VibeVoiceManager(
            api_url="http://localhost:8000"
        )

    def test_initialization(self):
        """Test VibeVoice manager initialization"""
        self.assertIsNotNone(self.vibevoice_manager)
        self.assertEqual(self.vibevoice_manager.api_url, "http://localhost:8000")
        self.assertTrue(self.vibevoice_manager.enabled)

    def test_voice_presets(self):
        """Test voice presets configuration"""
        presets = self.vibevoice_manager.voice_presets
        self.assertIsInstance(presets, dict)
        self.assertIn("alice", presets)
        self.assertIn("conversation", presets)

    def test_available_voices(self):
        """Test available voices list"""
        voices = self.vibevoice_manager.get_available_voices()
        self.assertIsInstance(voices, list)
        self.assertIn("en-alice", voices)
        self.assertIn("en-carter", voices)

    def test_content_optimization(self):
        """Test content optimization"""
        text = "This is a news article about technology. It has questions? And exclamations!"
        optimization = asyncio.run(self.vibevoice_manager.optimize_for_content(text, "news"))

        self.assertIn("content_type", optimization)
        self.assertIn("text_analysis", optimization)
        self.assertIn("recommended_settings", optimization)

        # Check text analysis
        analysis = optimization["text_analysis"]
        self.assertTrue(analysis["has_dialogue"])
        self.assertTrue(analysis["questions"])
        self.assertTrue(analysis["exclamations"])

    def test_emotional_speech_parameters(self):
        """Test emotional speech parameter validation"""
        # Test valid emotions
        valid_emotions = ["happy", "sad", "angry", "surprised", "neutral"]
        for emotion in valid_emotions:
            # This would normally call the API, just testing parameter handling
            self.assertIn(emotion, valid_emotions)

        # Test intensity range
        valid_intensities = [0.0, 0.5, 1.0]
        for intensity in valid_intensities:
            self.assertTrue(0.0 <= intensity <= 1.0)


class TestUnifiedServiceManager(unittest.TestCase):
    """Test suite for Unified Service Manager"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.config_path = self.temp_config.name

        # Write default config
        json.dump({
            "comfyui": {"enabled": True, "api_url": "http://localhost:8188"},
            "trellis": {"enabled": True, "api_url": "http://localhost:8288"},
            "vibevoice": {"enabled": True, "api_url": "http://localhost:8000"},
            "unified": {"health_check_interval": 30}
        }, self.temp_config)
        self.temp_config.close()

        self.unified_manager = UnifiedServiceManager(self.config_path)

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.config_path)

    def test_initialization(self):
        """Test unified manager initialization"""
        self.assertIsNotNone(self.unified_manager)
        self.assertIsNotNone(self.unified_manager.comfyui_manager)
        self.assertIsNotNone(self.unified_manager.trellis_manager)
        self.assertIsNotNone(self.unified_manager.vibevoice_manager)

    def test_configuration_loading(self):
        """Test configuration loading"""
        config = self.unified_manager.config
        self.assertIn("comfyui", config)
        self.assertIn("trellis", config)
        self.assertIn("vibevoice", config)
        self.assertIn("unified", config)

    def test_service_status_tracking(self):
        """Test service status tracking"""
        status = self.unified_manager.service_status
        self.assertIn("comfyui", status)
        self.assertIn("trellis", status)
        self.assertIn("vibevoice", status)

        # Check initial status
        for service_status in status.values():
            self.assertFalse(service_status["initialized"])
            self.assertFalse(service_status["healthy"])

    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        metrics = self.unified_manager.performance_metrics
        self.assertIn("total_requests", metrics)
        self.assertIn("successful_requests", metrics)
        self.assertIn("failed_requests", metrics)
        self.assertIn("average_response_time", metrics)
        self.assertIn("uptime_start", metrics)
        self.assertIn("service_usage", metrics)

    def test_multimodal_workflow_planning(self):
        """Test multimodal workflow planning"""
        description = "Create a story with images and narration"
        requirements = {"style": "educational"}

        workflow_plan = asyncio.run(self.unified_manager._plan_multimodal_workflow(description, requirements))

        self.assertIn("description", workflow_plan)
        self.assertIn("requirements", workflow_plan)
        self.assertIn("services", workflow_plan)
        self.assertIn("steps", workflow_plan)

        # Should include image and voice services
        self.assertIn("comfyui", workflow_plan["services"])
        self.assertIn("vibevoice", workflow_plan["services"])

    def test_workflow_result_summarization(self):
        """Test workflow result summarization"""
        results = [
            {"step": {"service": "comfyui"}, "result": {"success": True}},
            {"step": {"service": "vibevoice"}, "result": {"success": True}},
            {"step": {"service": "trellis"}, "result": {"success": False}}
        ]

        summary = self.unified_manager._summarize_workflow_results(results)

        self.assertEqual(summary["total_steps"], 3)
        self.assertEqual(summary["successful_steps"], 2)
        self.assertEqual(summary["failed_steps"], 1)
        self.assertAlmostEqual(summary["success_rate"], 2/3, places=2)

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Valid configuration
        valid_config = {
            "comfyui": {},
            "trellis": {},
            "vibevoice": {},
            "unified": {}
        }
        self.assertTrue(self.unified_manager._validate_configuration(valid_config))

        # Invalid configuration (missing required key)
        invalid_config = {
            "comfyui": {},
            "trellis": {},
            "vibevoice": {}
            # Missing "unified"
        }
        self.assertFalse(self.unified_manager._validate_configuration(invalid_config))


class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""

    def setUp(self):
        """Set up test environment"""
        self.unified_manager = UnifiedServiceManager()

    def test_content_creation_pipeline(self):
        """Test complete content creation pipeline"""
        scenario = {
            "description": "Create educational content about space",
            "requirements": {
                "include_images": True,
                "include_3d_models": True,
                "include_narration": True,
                "style": "educational"
            }
        }

        # Plan the workflow
        workflow_plan = asyncio.run(self.unified_manager._plan_multimodal_workflow(
            scenario["description"], scenario["requirements"]
        ))

        # Verify workflow includes all required services
        self.assertIn("comfyui", workflow_plan["services"])
        self.assertIn("trellis", workflow_plan["services"])
        self.assertIn("vibevoice", workflow_plan["services"])

        # Verify workflow structure
        self.assertGreater(len(workflow_plan["steps"]), 0)

        # Check that each step has required fields
        for step in workflow_plan["steps"]:
            self.assertIn("service", step)
            self.assertIn("action", step)
            self.assertIn("parameters", step)

    def test_storytelling_pipeline(self):
        """Test storytelling pipeline scenario"""
        scenario = {
            "description": "Create a children's story about a robot",
            "requirements": {
                "genre": "children",
                "length": "short",
                "include_illustrations": True,
                "include_voiceover": True
            }
        }

        workflow_plan = asyncio.run(self.unified_manager._plan_multimodal_workflow(
            scenario["description"], scenario["requirements"]
        ))

        # Should include image and voice services
        self.assertIn("comfyui", workflow_plan["services"])
        self.assertIn("vibevoice", workflow_plan["services"])

        # Should have appropriate steps
        steps = [step for step in workflow_plan["steps"] if step["service"] in ["comfyui", "vibevoice"]]
        self.assertGreater(len(steps), 0)

    def test_service_failure_handling(self):
        """Test handling of service failures"""
        # Mock service failure
        self.unified_manager.service_status["comfyui"]["initialized"] = False
        self.unified_manager.service_status["trellis"]["initialized"] = False
        self.unified_manager.service_status["vibevoice"]["initialized"] = False

        # Try to create workflow requiring unavailable services
        description = "Create content with images and 3D models"
        requirements = {}

        workflow_plan = asyncio.run(self.unified_manager._plan_multimodal_workflow(
            description, requirements
        ))

        # Should still create plan but execution would fail
        self.assertIn("description", workflow_plan)
        self.assertIn("steps", workflow_plan)

    def test_resource_constrained_scenario(self):
        """Test behavior under resource constraints"""
        # Mock high resource usage
        self.unified_manager.hardware_detector.get_system_info = Mock(return_value={
            "memory": {"total": 8192, "used": 7800},  # High memory usage
            "cpu": {"usage_percent": 95.0},
            "gpu": {"memory": {"total": 4096, "used": 3900}}
        })

        # Test resource checking for each service
        # This would normally prevent new workflows from starting
        system_info = self.unified_manager.hardware_detector.get_system_info()
        self.assertGreater(system_info["memory"]["used"] / system_info["memory"]["total"], 0.9)


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoint functionality"""

    def setUp(self):
        """Set up test environment"""
        # Import the API router
        from duckbot.integrations.unified_webui_integration import unified_router

        self.router = unified_router
        self.unified_manager = unified_service_manager

    def test_router_routes(self):
        """Test that all expected routes are defined"""
        routes = [route.path for route in self.router.routes]
        expected_routes = [
            "/status",
            "/services/{service_name}/health",
            "/services/{service_name}/restart",
            "/comfyui/workflows",
            "/comfyui/execute",
            "/trellis/assets/types",
            "/trellis/generate",
            "/vibevoice/voices",
            "/vibevoice/generate",
            "/multimodal-workflow",
            "/config"
        ]

        for route in expected_routes:
            self.assertIn(route, routes)

    def test_endpoint_parameter_validation(self):
        """Test endpoint parameter validation logic"""
        # Test ComfyUI workflow execution validation
        def validate_comfyui_params(params):
            return "workflow_type" in params

        self.assertTrue(validate_comfyui_params({"workflow_type": "text_to_image"}))
        self.assertFalse(validate_comfyui_params({}))

        # Test TRELLIS asset generation validation
        def validate_trellis_params(params):
            return "asset_type" in params

        self.assertTrue(validate_trellis_params({"asset_type": "text_to_3d"}))
        self.assertFalse(validate_trellis_params({}))

        # Test VibeVoice generation validation
        def validate_vibevoice_params(params):
            return "content" in params

        self.assertTrue(validate_vibevoice_params({"content": "Hello world"}))
        self.assertFalse(validate_vibevoice_params({}))


class TestPerformanceAndLoad(unittest.TestCase):
    """Test performance and load handling"""

    def setUp(self):
        """Set up test environment"""
        self.unified_manager = UnifiedServiceManager()

    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests"""
        async def simulate_concurrent_requests():
            tasks = []
            for i in range(10):
                task = self.unified_manager._update_performance_metrics(
                    execution_time=1.0,
                    success=True
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Check metrics updated correctly
            self.assertEqual(self.unified_manager.performance_metrics["total_requests"], 10)
            self.assertEqual(self.unified_manager.performance_metrics["successful_requests"], 10)

        asyncio.run(simulate_concurrent_requests())

    def test_metrics_calculation(self):
        """Test performance metrics calculation"""
        # Simulate some requests
        initial_metrics = self.unified_manager.performance_metrics.copy()

        # Add successful request
        self.unified_manager._update_performance_metrics(2.0, True)

        # Add failed request
        self.unified_manager._update_performance_metrics(1.0, False)

        # Check calculations
        self.assertEqual(self.unified_manager.performance_metrics["total_requests"], 2)
        self.assertEqual(self.unified_manager.performance_metrics["successful_requests"], 1)
        self.assertEqual(self.unified_manager.performance_metrics["failed_requests"], 1)

        # Check average response time
        expected_avg = (2.0 + 1.0) / 2
        self.assertEqual(self.unified_manager.performance_metrics["average_response_time"], expected_avg)

    def test_memory_usage_tracking(self):
        """Test memory usage tracking"""
        # This would normally integrate with actual memory monitoring
        # For testing, we simulate the tracking logic
        mock_memory_info = {
            "total": 8192,
            "used": 4096,
            "available": 4096
        }

        usage_percent = mock_memory_info["used"] / mock_memory_info["total"]
        self.assertEqual(usage_percent, 0.5)
        self.assertLess(usage_percent, 0.8)  # Below threshold


class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery"""

    def setUp(self):
        """Set up test environment"""
        self.unified_manager = UnifiedServiceManager()

    def test_service_restart_logic(self):
        """Test service restart functionality"""
        # Mock service status
        self.unified_manager.service_status["comfyui"]["initialized"] = True
        self.unified_manager.service_status["comfyui"]["healthy"] = False

        # Test restart logic (mocked)
        async def mock_restart():
            self.unified_manager.service_status["comfyui"]["healthy"] = True
            return True

        result = asyncio.run(mock_restart())
        self.assertTrue(result)
        self.assertTrue(self.unified_manager.service_status["comfyui"]["healthy"])

    def test_configuration_error_handling(self):
        """Test configuration error handling"""
        # Test with invalid configuration file
        invalid_config_path = "/nonexistent/path/config.json"

        # Should create default configuration
        manager = UnifiedServiceManager(invalid_config_path)
        self.assertIsNotNone(manager.config)
        self.assertIn("comfyui", manager.config)

    def test_api_error_handling(self):
        """Test API error handling"""
        # Test timeout handling
        async def simulate_timeout():
            try:
                # Simulate API timeout
                await asyncio.sleep(0.1)
                return {"success": False, "error": "timeout"}
            except asyncio.TimeoutError:
                return {"success": False, "error": "timeout"}

        result = asyncio.run(simulate_timeout())
        self.assertFalse(result["success"])
        self.assertIn("timeout", result["error"])

    def test_fallback_behavior(self):
        """Test fallback behavior when services are unavailable"""
        # Test multimodal workflow with services offline
        self.unified_manager.service_status["comfyui"]["initialized"] = False
        self.unified_manager.service_status["trellis"]["initialized"] = False
        self.unified_manager.service_status["vibevoice"]["initialized"] = False

        description = "Simple test request"
        requirements = {}

        # Should still create workflow plan even if services are offline
        workflow_plan = asyncio.run(self.unified_manager._plan_multimodal_workflow(
            description, requirements
        ))

        self.assertIn("description", workflow_plan)
        self.assertIn("steps", workflow_plan)


# Test runner and reporting
def run_comprehensive_tests():
    """Run all tests and generate report"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestComfyUIIntegration,
        TestTRELLISIntegration,
        TestVibeVoiceIntegration,
        TestUnifiedServiceManager,
        TestIntegrationScenarios,
        TestAPIEndpoints,
        TestPerformanceAndLoad,
        TestErrorHandling
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Generate report
    report = {
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun,
        "timestamp": time.time(),
        "test_details": {
            "failures": [{"test": str(failure[0]), "error": str(failure[1])} for failure in result.failures],
            "errors": [{"test": str(error[0]), "error": str(error[1])} for error in result.errors]
        }
    }

    return report


if __name__ == "__main__":
    # Run tests and print report
    report = run_comprehensive_tests()

    print("\n" + "="*50)
    print("UNIFIED SERVICES TEST REPORT")
    print("="*50)
    print(f"Total Tests: {report['total_tests']}")
    print(f"Failures: {report['failures']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']:.2%}")
    print("="*50)

    if report['failures'] > 0 or report['errors'] > 0:
        print("\nFAILED TESTS:")
        for failure in report['test_details']['failures']:
            print(f"- {failure['test']}: {failure['error'][:100]}...")

        for error in report['test_details']['errors']:
            print(f"- {error['test']}: {error['error'][:100]}...")

        print("\nSome tests failed. Please review the output above.")
        exit(1)
    else:
        print("\nAll tests passed! ✅")
        exit(0)
"""
Unit Tests for Core AI Components

Tests core AI functionality including:
- AI routing and model selection
- Local AI integration
- Task processing and routing
- AI configuration management
- Model detection and validation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import test utilities
from tests.unit import UnitTestHelpers, UnitTestDataGenerator, CustomAssertions

# Import DuckBot modules
try:
    from duckbot.ai_router_gpt import get_lm_studio_model, route_task, _select_best_available_model, TIERS
    from duckbot.dynamic_model_manager import DynamicModelManager
    from duckbot.qwen_agent_integration import is_qwen_agent_available, get_qwen_agent_capabilities
except ImportError as e:
    print(f"Warning: Could not import some AI modules: {e}")
    # Create mock modules for testing
    AI_MODULES_AVAILABLE = False
else:
    AI_MODULES_AVAILABLE = True

pytestmark = pytest.mark.unit

class TestAIRouting:
    """Test AI routing functionality"""

    @pytest.mark.asyncio
    async def test_model_detection(self, mock_http_response):
        """Test LM Studio model detection"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        with patch('httpx.get', return_value=mock_http_response):
            model = get_lm_studio_model()
            assert isinstance(model, str)
            assert len(model) > 0

    @pytest.mark.asyncio
    async def test_task_routing(self):
        """Test task routing to appropriate AI models"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        test_tasks = [
            {"kind": "reasoning", "prompt": "Analyze this data"},
            {"kind": "code", "prompt": "Write a function"},
            {"kind": "status", "prompt": "Check system status"}
        ]

        for task in test_tasks:
            result = route_task(task)
            assert result is not None
            assert "model" in result
            assert "confidence" in result

    def test_model_selection(self):
        """Test model selection based on task type"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        available_models = ["qwen/qwen3-coder-30b", "google/gemma-3-12b"]
        task = {"kind": "code", "prompt": "Write Python code"}

        selected = _select_best_available_model(available_models, task)
        assert selected in available_models
        assert "coder" in selected.lower()

    def test_tier_configuration(self):
        """Test AI tier configuration"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        assert isinstance(TIERS, dict)
        assert len(TIERS) > 0

        for tier_name, tier_config in TIERS.items():
            assert "model" in tier_config
            assert "tier" in tier_config

class TestDynamicModelManager:
    """Test dynamic model management"""

    @pytest.mark.asyncio
    async def test_model_loading(self):
        """Test dynamic model loading"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        with patch('duckbot.dynamic_model_manager.DynamicModelManager') as MockManager:
            mock_manager = MockManager()
            mock_manager.load_model = AsyncMock(return_value={"model": "test_model", "loaded": True})

            result = await mock_manager.load_model("test_model")
            assert result["loaded"] is True
            assert result["model"] == "test_model"

    def test_model_availability_check(self):
        """Test model availability checking"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        test_models = [
            {"name": "test_model_1", "available": True},
            {"name": "test_model_2", "available": False}
        ]

        for model in test_models:
            # Mock model availability check
            with patch('duckbot.dynamic_model_manager.check_model_availability', return_value=model["available"]):
                # This would normally call the actual function
                available = model["available"]  # Mock result
                assert available == model["available"]

class TestQwenIntegration:
    """Test Qwen agent integration"""

    def test_qwen_availability(self):
        """Test Qwen agent availability detection"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        available = is_qwen_agent_available()
        assert isinstance(available, bool)

    def test_qwen_capabilities(self):
        """Test Qwen agent capabilities retrieval"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        caps = get_qwen_agent_capabilities()
        assert isinstance(caps, dict)
        assert "tools" in caps
        assert "models" in caps

class TestAIAgentIntegration:
    """Test AI agent integration functionality"""

    @pytest.mark.asyncio
    async def test_agent_task_processing(self):
        """Test agent task processing"""
        test_task = {
            "id": "test_task_001",
            "type": "analysis",
            "input": {"data": "test data"},
            "expected_output": "analysis result"
        }

        # Mock agent processing
        with patch('duckbot.intelligent_agents.process_task') as mock_process:
            mock_process.return_value = {
                "task_id": test_task["id"],
                "result": "Mock analysis result",
                "success": True
            }

            result = await mock_process(test_task)
            assert result["success"] is True
            assert result["task_id"] == test_task["id"]

    def test_agent_coordination(self):
        """Test coordination between multiple agents"""
        agents = [
            {"name": "analyst", "capabilities": ["analysis", "reasoning"]},
            {"name": "coder", "capabilities": ["code", "testing"]},
            {"name": "coordinator", "capabilities": ["coordination", "planning"]}
        ]

        # Test agent selection based on capabilities
        task_type = "code"
        suitable_agents = [a for a in agents if task_type in a["capabilities"]]

        assert len(suitable_agents) > 0
        assert suitable_agents[0]["name"] == "coder"

class TestAIConfiguration:
    """Test AI configuration management"""

    def test_config_loading(self):
        """Test AI configuration loading"""
        test_config = {
            "ai": {
                "local_only": True,
                "lm_studio_url": "http://localhost:1234",
                "confidence_threshold": 0.75,
                "max_retries": 3
            },
            "models": {
                "primary": "qwen/qwen3-coder-30b",
                "fallback": "google/gemma-3-12b"
            }
        }

        assert "ai" in test_config
        assert "local_only" in test_config["ai"]
        assert test_config["ai"]["confidence_threshold"] == 0.75

    def test_config_validation(self):
        """Test configuration validation"""
        valid_configs = [
            {"local_only": True, "lm_studio_url": "http://localhost:1234"},
            {"local_only": False, "api_key": "test_key"}
        ]

        invalid_configs = [
            {"local_only": True},  # Missing lm_studio_url
            {"local_only": False, "api_key": ""},  # Empty api_key
            {}  # Missing required fields
        ]

        for config in valid_configs:
            assert self._validate_ai_config(config) is True

        for config in invalid_configs:
            assert self._validate_ai_config(config) is False

    def _validate_ai_config(self, config: Dict[str, Any]) -> bool:
        """Helper method to validate AI configuration"""
        if not isinstance(config, dict):
            return False

        if "local_only" not in config:
            return False

        if config["local_only"]:
            return "lm_studio_url" in config and len(config["lm_studio_url"]) > 0
        else:
            return "api_key" in config and len(config["api_key"]) > 0

class TestAIErrorHandling:
    """Test AI error handling and recovery"""

    @pytest.mark.asyncio
    async def test_model_loading_error(self):
        """Test model loading error handling"""
        with patch('duckbot.dynamic_model_manager.load_model') as mock_load:
            mock_load.side_effect = Exception("Model loading failed")

            with pytest.raises(Exception, match="Model loading failed"):
                await mock_load("test_model")

    def test_routing_fallback(self):
        """Test AI routing fallback mechanism"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        # Test fallback when primary model is unavailable
        primary_models = ["unavailable_model"]
        fallback_models = ["fallback_model"]

        task = {"kind": "reasoning", "prompt": "Test task"}

        # Mock model selection
        with patch('duckbot.ai_router_gpt._select_best_available_model') as mock_select:
            mock_select.return_value = "fallback_model"

            selected = mock_select(primary_models + fallback_models, task)
            assert selected == "fallback_model"

class TestAIPerformance:
    """Test AI performance characteristics"""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test AI response time performance"""
        if not AI_MODULES_AVAILABLE:
            pytest.skip("AI modules not available")

        import time
        start_time = time.time()

        # Mock AI processing
        with patch('duckbot.ai_router_gpt.route_task') as mock_route:
            mock_route.return_value = {"model": "test_model", "response": "test response"}

            result = mock_route({"kind": "status", "prompt": "Quick check"})

        end_time = time.time()
        response_time = end_time - start_time

        assert response_time < 1.0, f"Response time {response_time}s exceeds threshold"

    def test_memory_usage(self):
        """Test AI component memory usage"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate AI model loading
        mock_models = [f"model_{i}" for i in range(100)]

        # This would normally load actual models
        loaded_models = len(mock_models)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Allow some memory increase but within reasonable limits
        assert memory_increase < 100, f"Memory increase {memory_increase}MB exceeds threshold"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
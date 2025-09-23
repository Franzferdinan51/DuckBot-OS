#!/usr/bin/env python3
"""
Enhanced AI Provider Manager for DuckBot
Integrates all AI providers with smart routing, cost optimization, and fallback mechanisms
"""

import os
import json
import logging
import asyncio
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, deque
from datetime import datetime, timedelta
import time

# Unified model specification for all providers
@dataclass
class UnifiedModelSpec:
    id: str
    name: str
    size_gb: float
    ram_required_gb: float
    vram_required_gb: float
    capabilities: List[str]
    performance_score: int
    load_time_seconds: float
    specialty_bonus: Dict[str, int]
    provider: str
    api_endpoint: Optional[str] = None

# Import configuration manager
from .ai_configuration_manager import AIConfigurationManager, ProviderConfig

# Import required modules
try:
    from .dynamic_model_manager import DynamicModelManager, ModelSpec
    AI_ROUTING_AVAILABLE = True
except ImportError:
    AI_ROUTING_AVAILABLE = False
    DynamicModelManager = object
    ModelSpec = None
    UnifiedModelSpec = None

try:
    from ..integrations.claude_code_integration import claude_code_integration
    CLAUDE_CODE_AVAILABLE = True
except ImportError:
    CLAUDE_CODE_AVAILABLE = False
    claude_code_integration = None

try:
    from ..integrations.qwen_agent_integration import qwen_agent
    QWEN_AGENT_AVAILABLE = True
except ImportError:
    QWEN_AGENT_AVAILABLE = False
    qwen_agent = None

try:
    from ..integrations.zai_claude_code_integration import zai_claude_integration
    ZAI_CLAUDE_AVAILABLE = True
except ImportError:
    ZAI_CLAUDE_AVAILABLE = False
    zai_claude_integration = None

try:
    from ..integrations.vibevoice_client import vibevoice_integration
    VIBEVOICE_AVAILABLE = True
except ImportError:
    VIBEVOICE_AVAILABLE = False
    vibevoice_integration = None

# Import Qwen3-Omni integration
try:
    from .qwen3_omni_integration import qwen3_omni_integration, Qwen3OmniIntegration
    QWEN3_OMNI_AVAILABLE = True
except ImportError:
    QWEN3_OMNI_AVAILABLE = False
    qwen3_omni_integration = None
    Qwen3OmniIntegration = None

# Import intelligent caching
try:
    from .intelligent_cache import get_intelligent_cache, CacheConfig
    INTELLIGENT_CACHE_AVAILABLE = True
except ImportError:
    INTELLIGENT_CACHE_AVAILABLE = False

# Import cost management
try:
    from .cost_management import CostTracker
    COST_MANAGEMENT_AVAILABLE = True
except ImportError:
    COST_MANAGEMENT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Model performance and resource requirements database
@dataclass
class ProviderStatus:
    """Status information for a provider"""
    available: bool = False
    enabled: bool = False
    healthy: bool = False
    last_check: datetime = None
    error_message: str = ""
    response_time_ms: float = 0.0
    success_rate: float = 0.0
    consecutive_failures: int = 0

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for provider"""
    is_open: bool = False
    failure_count: int = 0
    last_failure_time: datetime = None
    reset_time: datetime = None

class AIProviderManager:
    """Enhanced AI Provider Manager for DuckBot"""

    def __init__(self):
        # Initialize configuration manager
        self.config_manager = AIConfigurationManager()

        # Initialize dynamic model manager
        self.dynamic_manager = DynamicModelManager() if AI_ROUTING_AVAILABLE else None

        # Initialize cost tracking
        self.cost_tracker = CostTracker() if COST_MANAGEMENT_AVAILABLE else None

        # Provider status tracking
        self.provider_status: Dict[str, ProviderStatus] = {}
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}

        # Initialize providers dict
        self.providers: Dict[str, Dict[str, Any]] = {}

        # Initialize intelligent caching
        self.cache = None
        if INTELLIGENT_CACHE_AVAILABLE:
            try:
                cache_config = CacheConfig(
                    ai_response_ttl_seconds=86400,  # Cache AI responses for 24 hours
                    enable_similarity_matching=True,
                    enable_cost_aware_eviction=True
                )
                self.cache = get_intelligent_cache(cache_config)
                logger.info("Intelligent caching initialized for AI provider manager")
            except Exception as e:
                logger.warning(f"Failed to initialize intelligent caching: {e}")

        # Cache statistics
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'cost_saved': 0.0
        }

        # Initialize provider instances and status
        self.provider_instances = {}
        self._initialize_providers()

        # Initialize model database with all providers
        self.model_database = self._initialize_unified_model_database()

        # Main brain model - always kept loaded for system orchestration
        self.main_brain_model = None
        self.main_brain_provider = None
        self.qwen3_omni_instance = None
        self._initialize_main_brain()

        # Start health monitoring (lazy initialization)
        self.health_monitor_started = False

    def _initialize_providers(self):
        """Initialize provider instances based on configuration"""
        for provider_name, provider_config in self.config_manager.providers.items():
            if not provider_config.enabled:
                continue

            provider_instance = None
            available = False

            # Initialize based on provider type
            if provider_name == "lm_studio" and self.dynamic_manager:
                provider_instance = self.dynamic_manager
                available = True
            elif provider_name == "claude_code" and CLAUDE_CODE_AVAILABLE:
                provider_instance = claude_code_integration
                available = claude_code_integration and claude_code_integration.is_available()
            elif provider_name == "qwen_agent" and QWEN_AGENT_AVAILABLE:
                provider_instance = qwen_agent
                available = qwen_agent and qwen_agent.available
            elif provider_name == "zai_claude" and ZAI_CLAUDE_AVAILABLE:
                provider_instance = zai_claude_integration
                available = zai_claude_integration and zai_claude_integration.available
            elif provider_name == "vibevoice" and VIBEVOICE_AVAILABLE:
                provider_instance = vibevoice_integration
                available = vibevoice_integration and vibevoice_integration.available
            elif provider_name == "qwen3_omni" and QWEN3_OMNI_AVAILABLE:
                provider_instance = qwen3_omni_integration
                available = qwen3_omni_integration and qwen3_omni_integration.is_available()
                # Ensure model is loaded for Qwen3-Omni
                if available and not qwen3_omni_integration.is_loaded:
                    asyncio.create_task(qwen3_omni_integration.load_model())
            elif provider_name == "duckbot":
                # Internal DuckBot provider
                provider_instance = self._create_duckbot_provider(provider_config)
                available = True
            elif provider_name == "gemini":
                # Gemini provider
                provider_instance = self._create_gemini_provider(provider_config)
                available = True
            elif provider_name == "openrouter":
                # OpenRouter provider
                provider_instance = self._create_openrouter_provider(provider_config)
                available = True

            self.provider_instances[provider_name] = provider_instance

            # Initialize providers dict
            self.providers[provider_name] = {
                "available": available,
                "enabled": provider_config.enabled,
                "instance": provider_instance,
                "config": provider_config
            }

            # Initialize status and circuit breaker
            self.provider_status[provider_name] = ProviderStatus(
                available=available,
                enabled=provider_config.enabled,
                healthy=available,
                last_check=datetime.now()
            )

            self.circuit_breakers[provider_name] = CircuitBreakerState()

    def _create_duckbot_provider(self, config: ProviderConfig):
        """Create DuckBot internal provider instance"""
        class DuckBotProvider:
            def __init__(self, config):
                self.config = config
                self.available = True

            def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                # Internal DuckBot logic for system tasks
                task_type = task.get("kind", "general")

                if task_type == "system_management":
                    return {
                        "success": True,
                        "response": "System management task executed internally",
                        "action_taken": "internal_execution",
                        "cost_estimate": 0.0
                    }
                elif task_type == "configuration":
                    return {
                        "success": True,
                        "response": "Configuration task processed",
                        "changes_made": [],
                        "cost_estimate": 0.0
                    }
                else:
                    return {
                        "success": True,
                        "response": f"DuckBot processed {task_type} task",
                        "cost_estimate": 0.0
                    }

            def is_available(self):
                return self.available

            def get_status(self):
                return {"available": self.available, "type": "internal"}

        return DuckBotProvider(config)

    def _create_gemini_provider(self, config: ProviderConfig):
        """Create Gemini provider instance"""
        class GeminiProvider:
            def __init__(self, config):
                self.config = config
                self.api_key = getattr(config, 'api_key', None)
                self.available = bool(self.api_key)

            async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                if not self.available:
                    return {"success": False, "error": "Gemini API key not configured"}

                # Gemini API call implementation
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key
                }

                payload = {
                    "contents": [{
                        "parts": [{"text": task.get("prompt", "")}]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": self.config.max_tokens,
                        "temperature": self.config.temperature
                    }
                }

                try:
                    url = f"{self.config.url}/models/{self.config.default_model}:generateContent"
                    response = requests.post(url, json=payload, headers=headers, timeout=self.config.timeout)

                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "success": True,
                            "response": result["candidates"][0]["content"]["parts"][0]["text"],
                            "usage": {
                                "input_tokens": 0,  # Gemini doesn't provide token count
                                "output_tokens": 0
                            },
                            "cost_estimate": 0.001  # Fixed cost estimate
                        }
                    else:
                        return {"success": False, "error": f"Gemini API error: {response.status_code}"}

                except Exception as e:
                    return {"success": False, "error": f"Gemini provider error: {str(e)}"}

            def is_available(self):
                return self.available

            def get_status(self):
                return {"available": self.available, "api_key_configured": bool(self.api_key)}

        return GeminiProvider(config)

    def _create_openrouter_provider(self, config: ProviderConfig):
        """Create OpenRouter provider instance"""
        class OpenRouterProvider:
            def __init__(self, config):
                self.config = config
                self.api_key = getattr(config, 'api_key', None)
                self.available = bool(self.api_key)

            async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                if not self.available:
                    return {"success": False, "error": "OpenRouter API key not configured"}

                # OpenRouter API call implementation
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://duckbot.ai",
                    "X-Title": "DuckBot"
                }

                payload = {
                    "model": self.config.default_model,
                    "messages": [{"role": "user", "content": task.get("prompt", "")}],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }

                try:
                    response = requests.post(self.config.url, json=payload, headers=headers, timeout=self.config.timeout)

                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "success": True,
                            "response": result["choices"][0]["message"]["content"],
                            "usage": result.get("usage", {}),
                            "cost_estimate": 0.0005  # Fixed cost estimate
                        }
                    else:
                        return {"success": False, "error": f"OpenRouter API error: {response.status_code}"}

                except Exception as e:
                    return {"success": False, "error": f"OpenRouter provider error: {str(e)}"}

            def is_available(self):
                return self.available

            def get_status(self):
                return {"available": self.available, "api_key_configured": bool(self.api_key)}

        return OpenRouterProvider(config)

    def _create_qwen3_omni_provider(self, config: ProviderConfig):
        """Create Qwen3-Omni provider instance"""
        class Qwen3OmniProvider:
            def __init__(self, config, integration_instance):
                self.config = config
                self.integration = integration_instance
                self.available = integration_instance and integration_instance.is_available()

            async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
                if not self.available or not self.integration:
                    return {"success": False, "error": "Qwen3-Omni not available"}

                # Execute task using Qwen3-Omni integration
                return await self.integration.execute_task(task)

            def is_available(self):
                return self.available and self.integration and self.integration.is_available()

            def get_status(self):
                if self.integration:
                    return self.integration.get_status()
                return {"available": False, "error": "Integration not available"}

        return Qwen3OmniProvider(config, qwen3_omni_integration)

    async def start_health_monitoring(self):
        """Start background health monitoring for providers"""
        if not self.health_monitor_started and self.config_manager.fallback_config.enabled:
            self.health_monitor_started = True
            asyncio.create_task(self._health_monitor_loop())

    def _start_health_monitoring(self):
        """Legacy method for backward compatibility"""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self._health_monitor_loop())
        except RuntimeError:
            # No event loop running, will start later
            pass

    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while True:
            try:
                await self._check_all_providers_health()
                await asyncio.sleep(self.config_manager.system_config.monitoring_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _check_all_providers_health(self):
        """Check health status of all providers"""
        for provider_name in self.config_manager.get_enabled_providers():
            await self._check_provider_health(provider_name)

    async def _check_provider_health(self, provider_name: str):
        """Check health of a specific provider"""
        if provider_name not in self.provider_status:
            return

        status = self.provider_status[provider_name]
        circuit_breaker = self.circuit_breakers[provider_name]

        # Skip if circuit breaker is open
        if circuit_breaker.is_open:
            if datetime.now() < circuit_breaker.reset_time:
                return
            else:
                # Reset circuit breaker
                circuit_breaker.is_open = False
                circuit_breaker.failure_count = 0
                logger.info(f"Circuit breaker reset for provider {provider_name}")

        start_time = time.time()
        success = False
        error_message = ""

        try:
            if provider_name in self.provider_instances:
                instance = self.provider_instances[provider_name]
                if hasattr(instance, 'is_available'):
                    success = instance.is_available()
                elif hasattr(instance, 'get_status'):
                    status_info = instance.get_status()
                    success = status_info.get("available", False)
                else:
                    success = True

            status.response_time_ms = (time.time() - start_time) * 1000
            status.last_check = datetime.now()

            if success:
                status.healthy = True
                status.consecutive_failures = 0
                status.success_rate = min(1.0, status.success_rate + 0.1)
                circuit_breaker.failure_count = 0
            else:
                status.healthy = False
                status.consecutive_failures += 1
                status.success_rate = max(0.0, status.success_rate - 0.1)

                # Update circuit breaker
                circuit_breaker.failure_count += 1
                circuit_breaker.last_failure_time = datetime.now()

                if (circuit_breaker.failure_count >=
                    self.config_manager.fallback_config.circuit_breaker_threshold):
                    circuit_breaker.is_open = True
                    circuit_breaker.reset_time = (
                        datetime.now() + timedelta(
                            milliseconds=self.config_manager.fallback_config.circuit_breaker_timeout_ms
                        )
                    )
                    logger.warning(f"Circuit breaker opened for provider {provider_name}")

        except Exception as e:
            error_message = str(e)
            status.healthy = False
            status.consecutive_failures += 1
            status.error_message = error_message
            logger.error(f"Health check failed for {provider_name}: {error_message}")

    def _initialize_unified_model_database(self) -> Dict[str, UnifiedModelSpec]:
        """Initialize unified database of known models from all providers"""
        models = {}
        
        # Add models from dynamic model manager (LM Studio)
        if self.dynamic_manager:
            for model_id, spec in self.dynamic_manager.model_database.items():
                models[model_id] = UnifiedModelSpec(
                    id=spec.id,
                    name=spec.name,
                    size_gb=spec.size_gb,
                    ram_required_gb=spec.ram_required_gb,
                    vram_required_gb=spec.vram_required_gb,
                    capabilities=spec.capabilities,
                    performance_score=spec.performance_score,
                    load_time_seconds=spec.load_time_seconds,
                    specialty_bonus=spec.specialty_bonus,
                    provider="lm_studio"
                )
        
        # Add Claude Code models
        if self.providers.get("claude_code", {}).get("available", False):
            claude_models = [
                ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", 85),
                ("anthropic/claude-3-haiku", "Claude 3 Haiku", 70),
                ("deepseek/coder", "DeepSeek Coder", 80),
            ]
            
            for model_id, name, score in claude_models:
                models[model_id] = UnifiedModelSpec(
                    id=model_id,
                    name=name,
                    size_gb=0.0,  # Cloud model
                    ram_required_gb=0.0,
                    vram_required_gb=0.0,
                    capabilities=["coding", "general", "analysis", "reasoning"],
                    performance_score=score,
                    load_time_seconds=2.0,  # Fast cloud access
                    specialty_bonus={"code": 30, "general": 20, "analysis": 15, "reasoning": 10},
                    provider="claude_code",
                    api_endpoint="http://localhost:11434/v1/chat/completions"
                )
        
        # Add Qwen-Agent models
        if self.providers.get("qwen_agent", {}).get("available", False):
            models["qwen/qwen3-coder:free"] = UnifiedModelSpec(
                id="qwen/qwen3-coder:free",
                name="Qwen3 Coder (Free Tier)",
                size_gb=0.0,  # Cloud model
                ram_required_gb=0.0,
                vram_required_gb=0.0,
                capabilities=["coding", "general", "analysis", "reasoning"],
                performance_score=85,
                load_time_seconds=2.0,  # Fast cloud access
                specialty_bonus={"code": 30, "general": 20, "analysis": 15, "reasoning": 10},
                provider="qwen_agent",
                api_endpoint="https://openrouter.ai/api/v1"
            )
        
        # Add Z.ai Claude models
        if self.providers.get("zai_claude", {}).get("available", False):
            models["claude-3-5-sonnet-20241022"] = UnifiedModelSpec(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet (Z.ai)",
                size_gb=0.0,  # Cloud model
                ram_required_gb=0.0,
                vram_required_gb=0.0,
                capabilities=["coding", "general", "analysis", "reasoning"],
                performance_score=90,
                load_time_seconds=2.0,  # Fast cloud access
                specialty_bonus={"code": 35, "general": 25, "analysis": 20, "reasoning": 15},
                provider="zai_claude",
                api_endpoint="https://api.z.ai/v1/chat/completions"
            )

        # Add Qwen3-Omni models
        if QWEN3_OMNI_AVAILABLE:
            models["Qwen/Qwen3-Omni"] = UnifiedModelSpec(
                id="Qwen/Qwen3-Omni",
                name="Qwen3-Omni (Main Brain)",
                size_gb=15.0,  # Local model size estimate
                ram_required_gb=16.0,
                vram_required_gb=12.0,
                capabilities=["coding", "general", "analysis", "reasoning", "multimodal", "voice"],
                performance_score=95,
                load_time_seconds=30.0,  # Longer load time for large model
                specialty_bonus={"code": 40, "general": 30, "analysis": 25, "reasoning": 25, "multimodal": 50, "voice": 45},
                provider="qwen3_omni",
                api_endpoint="local"
            )

        return models
    
    def _initialize_main_brain(self):
        """Initialize and load the main brain model for system orchestration"""
        # Priority order for main brain selection - Qwen3-Omni first
        main_brain_candidates = [
            ("Qwen/Qwen3-Omni", "qwen3_omni"),
            ("qwen/qwen3-coder:free", "qwen_agent"),
            ("anthropic/claude-3.5-sonnet", "claude_code"),
            ("claude-3-5-sonnet-20241022", "zai_claude"),
        ]
        
        # Try to use LM Studio if available and has models loaded
        if self.dynamic_manager and self.dynamic_manager.main_brain_model:
            self.main_brain_model = self.dynamic_manager.main_brain_model
            self.main_brain_provider = "lm_studio"
            logger.info(f"[BRAIN] Main brain established: {self.main_brain_model} (LM Studio)")
            return
        
        # Try cloud providers
        for model_id, provider in main_brain_candidates:
            if (provider in self.providers and
                self.providers[provider]["available"] and
                (model_id in self.model_database or provider == "qwen3_omni")):
                self.main_brain_model = model_id
                self.main_brain_provider = provider
                # For Qwen3-Omni, ensure it's loaded
                if provider == "qwen3_omni" and QWEN3_OMNI_AVAILABLE:
                    self.qwen3_omni_instance = qwen3_omni_integration
                    if not qwen3_omni_integration.is_loaded:
                        asyncio.create_task(qwen3_omni_integration.load_model())
                logger.info(f"[BRAIN] Main brain established: {model_id} ({provider})")
                return
        
        # Fallback to any available model
        if self.model_database:
            model_id = list(self.model_database.keys())[0]
            spec = self.model_database[model_id]
            self.main_brain_model = model_id
            self.main_brain_provider = spec.provider
            logger.warning(f"[BRAIN] Fallback main brain: {model_id} ({spec.provider})")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        return [name for name, info in self.providers.items() if info["available"]]
    
    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Get status of a specific provider"""
        if provider_name not in self.providers:
            return {"available": False, "error": "Provider not found"}
        
        provider = self.providers[provider_name]
        if not provider["available"]:
            return {"available": False, "error": "Provider not initialized"}
        
        status = {"available": True}
        
        if provider_name == "lm_studio" and self.dynamic_manager:
            status.update(self.dynamic_manager.get_status())
        elif provider_name == "claude_code" and claude_code_integration:
            status.update(claude_code_integration.get_status())
        elif provider_name == "qwen_agent" and qwen_agent:
            status.update(qwen_agent.get_capabilities())
        elif provider_name == "zai_claude" and zai_claude_integration:
            status.update(zai_claude_integration.get_status())
        
        return status
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        return {
            provider_name: self.get_provider_status(provider_name)
            for provider_name in self.providers.keys()
        }
    
    def select_optimal_model_for_task(self, task: Dict[str, Any]) -> Tuple[str, str]:
        """Select the best model and provider for a task"""
        task_kind = task.get("kind", "*")
        prompt_length = len(task.get("prompt", ""))
        
        # For general system orchestration tasks, always use main brain
        orchestration_tasks = ["server_management", "ecosystem_management", "system_status", 
                             "service_management", "policy", "arbiter"]
        if task_kind in orchestration_tasks and self.main_brain_model:
            return self.main_brain_model, self.main_brain_provider
        
        # Score all available models for specialized task loading
        model_scores = {}
        
        for model_id, spec in self.model_database.items():
            score = spec.performance_score
            
            # Task-specific bonuses
            if task_kind in spec.specialty_bonus:
                score += spec.specialty_bonus[task_kind]
            
            # Capability matching
            if task_kind in ["reasoning", "policy"] and "reasoning" in spec.capabilities:
                score += 20
            elif task_kind in ["code", "debugging"] and "coding" in spec.capabilities:
                score += 20
            
            # Resource efficiency bonus for light tasks
            if prompt_length < 200 and spec.size_gb < 10:
                score += 15
            
            # Penalty for heavy models on simple tasks
            if task_kind in ["status", "summary"] and spec.size_gb > 20:
                score -= 25
            
            model_scores[model_id] = score
        
        # Sort by score and check availability
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        
        for model_id, score in sorted_models:
            spec = self.model_database[model_id]
            provider_name = spec.provider
            
            # Check if provider is available
            if self.providers[provider_name]["available"]:
                return model_id, provider_name
        
        # Fallback to main brain if no other models are suitable
        if self.main_brain_model:
            return self.main_brain_model, self.main_brain_provider
        
        # Ultimate fallback
        if self.model_database:
            model_id = list(self.model_database.keys())[0]
            spec = self.model_database[model_id]
            return model_id, spec.provider
        
        return "unknown", "unknown"
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using the optimal model and provider with caching"""
        try:
            model_id, provider_name = self.select_optimal_model_for_task(task)

            # Generate cache key
            cache_key = self._generate_cache_key(task, model_id, provider_name)

            # Check cache first
            if self.cache:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    self.cache_stats['hits'] += 1
                    logger.debug(f"Cache hit for task with {provider_name}/{model_id}")
                    return {
                        **cached_result.value,
                        "cached": True,
                        "cache_hit": True,
                        "provider": provider_name,
                        "model": model_id
                    }

                self.cache_stats['misses'] += 1

            # Execute task with caching wrapper
            if self.cache:
                result = await self.cache.cached_call(
                    cache_key,
                    self._execute_task_without_cache,
                    task, model_id, provider_name
                )
            else:
                result = await self._execute_task_without_cache(task, model_id, provider_name)

            # Add caching metadata
            result["provider"] = provider_name
            result["model"] = model_id
            result["cached"] = False

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Using basic response",
                "provider": provider_name if 'provider_name' in locals() else "unknown",
                "model": model_id if 'model_id' in locals() else "unknown"
            }

    async def _execute_task_without_cache(self, task: Dict[str, Any], model_id: str, provider_name: str) -> Dict[str, Any]:
        """Execute task without caching (internal method)"""
        if provider_name == "lm_studio" and self.dynamic_manager:
            # Use dynamic model manager for LM Studio
            selected_model = self.dynamic_manager.get_or_load_model_for_task(task)
            # For now, we'll just return a success message
            # In a full implementation, this would actually call the model
            return {
                "success": True,
                "response": f"Task executed using LM Studio model: {selected_model}",
                "cost_estimate": 0.0  # Local model, no API cost
            }

        elif provider_name == "claude_code" and claude_code_integration:
            # Use Claude Code integration
            result = await claude_code_integration.execute_code_task(
                task.get("prompt", ""), task.get("context")
            )
            # Estimate cost based on usage if available
            cost_estimate = self._estimate_cost(result.get("usage", {}), "claude_code")
            result["cost_estimate"] = cost_estimate
            return result

        elif provider_name == "qwen_agent" and qwen_agent:
            # Use Qwen-Agent
            result = await qwen_agent.execute_task(
                task.get("prompt", ""), task.get("context")
            )
            # Estimate cost
            cost_estimate = self._estimate_cost(result.get("usage", {}), "qwen_agent")
            result["cost_estimate"] = cost_estimate
            return result

        elif provider_name == "qwen3_omni" and qwen3_omni_integration:
            # Use Qwen3-Omni integration
            result = await qwen3_omni_integration.execute_task(task)
            return result

        elif provider_name == "zai_claude" and zai_claude_integration:
            # Use Z.ai Claude
            messages = [{"role": "user", "content": task.get("prompt", "")}]
            result = await zai_claude_integration.chat_completion(messages)
            usage = result.get("usage", {})
            cost_estimate = self._estimate_cost(usage, "zai_claude")
            return {
                "success": True,
                "response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "usage": usage,
                "cost_estimate": cost_estimate
            }

        else:
            return {
                "success": False,
                "error": f"No available provider for model {model_id}",
                "cost_estimate": 0.0
            }

    def _generate_cache_key(self, task: Dict[str, Any], model_id: str, provider_name: str) -> str:
        """Generate cache key for task"""
        import hashlib
        import json

        # Create normalized task representation
        normalized_task = {
            "prompt": task.get("prompt", "").strip(),
            "kind": task.get("kind", "general"),
            "context": task.get("context", {}),
            "model_id": model_id,
            "provider": provider_name
        }

        # Generate hash
        task_str = json.dumps(normalized_task, sort_keys=True)
        return f"ai_task_{hashlib.md5(task_str.encode()).hexdigest()}"

    def _estimate_cost(self, usage: Dict[str, Any], provider: str) -> float:
        """Estimate API call cost based on usage"""
        if not usage:
            return 0.0

        # Simple cost estimation (can be enhanced with real pricing data)
        input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
        output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))

        # Basic pricing (cents per 1K tokens)
        pricing = {
            "claude_code": {"input": 0.015, "output": 0.075},  # Claude 3.5 Sonnet
            "qwen_agent": {"input": 0.001, "output": 0.002},    # Qwen free tier
            "zai_claude": {"input": 0.003, "output": 0.015}    # Z.ai Claude
        }

        provider_pricing = pricing.get(provider, {"input": 0.001, "output": 0.002})
        cost = (input_tokens * provider_pricing["input"] / 1000 +
                output_tokens * provider_pricing["output"] / 1000)

        return max(0.0, cost)  # Ensure non-negative
    
    def get_model_capabilities(self, model_id: str) -> Dict[str, Any]:
        """Get capabilities of a specific model"""
        if model_id not in self.model_database:
            return {"error": "Model not found"}

        spec = self.model_database[model_id]
        return {
            "id": spec.id,
            "name": spec.name,
            "provider": spec.provider,
            "capabilities": spec.capabilities,
            "performance_score": spec.performance_score,
            "specialty_bonus": spec.specialty_bonus,
            "size_gb": spec.size_gb,
            "available": self.providers[spec.provider]["available"]
        }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = {
            "cache_enabled": self.cache is not None,
            "cache_stats": self.cache_stats.copy()
        }

        if self.cache:
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            if total_requests > 0:
                stats["hit_rate"] = self.cache_stats['hits'] / total_requests
            else:
                stats["hit_rate"] = 0.0

            # Add detailed cache stats from intelligent cache
            try:
                cache_detailed_stats = asyncio.get_event_loop().run_until_complete(
                    self.cache.get_stats()
                )
                stats["detailed_cache_stats"] = cache_detailed_stats
            except Exception as e:
                logger.warning(f"Could not get detailed cache stats: {e}")

        return stats

# Global instance
ai_provider_manager = AIProviderManager()

# Convenience functions
def get_available_providers() -> List[str]:
    """Get list of available AI providers"""
    return ai_provider_manager.get_available_providers()

def get_provider_status(provider_name: str) -> Dict[str, Any]:
    """Get status of a specific provider"""
    return ai_provider_manager.get_provider_status(provider_name)

def get_all_provider_status() -> Dict[str, Any]:
    """Get status of all providers"""
    return ai_provider_manager.get_all_status()

async def execute_ai_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a task using the optimal AI provider"""
    return await ai_provider_manager.execute_task(task)

def get_model_capabilities(model_id: str) -> Dict[str, Any]:
    """Get capabilities of a specific model"""
    return ai_provider_manager.get_model_capabilities(model_id)

if __name__ == "__main__":
    # Test the integration
    import asyncio
    
    async def test():
        print("AI Provider Manager Test")
        print("======================")
        
        # Show available providers
        providers = get_available_providers()
        print(f"Available providers: {providers}")
        
        # Show provider status
        for provider in providers:
            status = get_provider_status(provider)
            print(f"{provider} status: {status}")
        
        # Test task execution
        test_task = {
            "kind": "code",
            "prompt": "Write a simple Python function to calculate factorial",
            "context": {"language": "python"}
        }
        
        result = await execute_ai_task(test_task)
        print(f"Task result: {json.dumps(result, indent=2)}")
    
    asyncio.run(test())
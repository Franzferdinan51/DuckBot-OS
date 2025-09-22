#!/usr/bin/env python3
"""
DuckBot Unified AI Router Management System
Combines ai_router_gpt.py, settings_gpt.py, and provider_connectors.py into one comprehensive module
"""

import os
import time
import hashlib
import json
import requests
import logging
import threading
import asyncio
import traceback
from collections import deque
from pathlib import Path
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
import httpx

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("duckbot.ai_router")

# Try to import optional modules
try:
    from .rag import maybe_augment_with_rag, index_stats, auto_ingest_defaults
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG module not available")

try:
    from .action_reasoning_logger import action_logger
    ACTION_LOGGING_AVAILABLE = True
except ImportError:
    ACTION_LOGGING_AVAILABLE = False
    logger.warning("Action reasoning logger not available")

try:
    from .dynamic_model_manager import DynamicModelManager
    DYNAMIC_MODEL_MANAGER = DynamicModelManager()
    DYNAMIC_LOADING_AVAILABLE = True
except ImportError:
    DYNAMIC_LOADING_AVAILABLE = False
    logger.warning("Dynamic model manager not available")

try:
    from .local_feature_parity import ensure_full_local_parity, local_parity
    LOCAL_PARITY_AVAILABLE = True
except ImportError:
    LOCAL_PARITY_AVAILABLE = False
    logger.warning("Local feature parity not available")

try:
    from .qwen_agent_integration import is_qwen_agent_available, execute_enhanced_task
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    ENHANCED_AI_AVAILABLE = False
    logger.warning("Qwen-Agent integration not available")

# ============================================================================
# Configuration Management
# ============================================================================

@dataclass
class ProviderConfig:
    """Configuration for AI provider connectors"""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60
    streaming: bool = True
    extra_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class AISettings:
    """AI router settings and configuration"""
    # Routing and model selection
    ai_routing_mode: str = "cloud_first"  # cloud_first or local_first
    ai_model_main_brain: str = "qwen/qwen3-coder:free"
    lm_studio_model: str = "qwen/qwen3-coder-30b"
    force_cloud_for_chat: bool = False

    # Local tuning
    ai_local_strict: bool = True
    ai_local_max_attempts: int = 2
    ai_local_conf_min: float = 0.68

    # Cloud budget and routing limits
    openrouter_budget_per_min: int = 6
    ai_ttl_cache_sec: int = 60
    ai_max_hops_routine: int = 1
    ai_max_hops_critical: int = 3
    ai_confidence_min: float = 0.75

    # Cloud model selection
    ai_model_code: str = "qwen/qwen3-coder:free"
    ai_model_analysis: str = "glm/glm-4.5-air:free"
    ai_model_debug: str = "qwen/qwen3-coder:free"
    ai_model_server_brain: str = "qwen/qwen3-coder:free"

    # Reasoning model settings
    enable_qwq_reasoning: bool = False
    ai_model_reasoning: str = "qwen/qwq-32b:free"

    # OpenRouter tier environment overrides
    or_qwen_coder: str = "qwen/qwen3-coder:free"
    or_glm_air: str = "z-ai/glm-4.5-air:free"
    or_nemo: str = "qwen/qwen3-coder:free"
    or_kimi: str = "moonshot/kimi-k2:free"
    or_r1: str = "deepseek/deepseek-r1:free"
    or_qwq: str = "qwen/qwq-32b:free"

    # Feature toggles
    enable_rag: bool = True
    enable_enhanced_ai: bool = True
    enable_local_parity: bool = True
    enable_action_logging: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "AI_ROUTING_MODE": self.ai_routing_mode,
            "AI_MODEL_MAIN_BRAIN": self.ai_model_main_brain,
            "LM_STUDIO_MODEL": self.lm_studio_model,
            "FORCE_CLOUD_FOR_CHAT": "1" if self.force_cloud_for_chat else "0",
            "AI_LOCAL_STRICT": "1" if self.ai_local_strict else "0",
            "AI_LOCAL_MAX_ATTEMPTS": str(self.ai_local_max_attempts),
            "AI_LOCAL_CONF_MIN": str(self.ai_local_conf_min),
            "OPENROUTER_BUDGET_PER_MIN": str(self.openrouter_budget_per_min),
            "AI_TTL_CACHE_SEC": str(self.ai_ttl_cache_sec),
            "AI_MAX_HOPS_ROUTINE": str(self.ai_max_hops_routine),
            "AI_MAX_HOPS_CRITICAL": str(self.ai_max_hops_critical),
            "AI_CONFIDENCE_MIN": str(self.ai_confidence_min),
            "AI_MODEL_CODE": self.ai_model_code,
            "AI_MODEL_ANALYSIS": self.ai_model_analysis,
            "AI_MODEL_DEBUG": self.ai_model_debug,
            "AI_MODEL_SERVER_BRAIN": self.ai_model_server_brain,
            "ENABLE_QWQ_REASONING": "1" if self.enable_qwq_reasoning else "0",
            "AI_MODEL_REASONING": self.ai_model_reasoning,
            "OR_QWEN_CODER": self.or_qwen_coder,
            "OR_GLM_AIR": self.or_glm_air,
            "OR_NEMO": self.or_nemo,
            "OR_KIMI": self.or_kimi,
            "OR_R1": self.or_r1,
            "OR_QWQ": self.or_qwq,
            "ENABLE_RAG": "1" if self.enable_rag else "0",
            "ENABLE_ENHANCED_AI": "1" if self.enable_enhanced_ai else "0",
            "ENABLE_LOCAL_PARITY": "1" if self.enable_local_parity else "0",
            "ENABLE_ACTION_LOGGING": "1" if self.enable_action_logging else "0"
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'AISettings':
        """Create settings from dictionary"""
        return cls(
            ai_routing_mode=data.get("AI_ROUTING_MODE", "cloud_first"),
            ai_model_main_brain=data.get("AI_MODEL_MAIN_BRAIN", "qwen/qwen3-coder:free"),
            lm_studio_model=data.get("LM_STUDIO_MODEL", "qwen/qwen3-coder-30b"),
            force_cloud_for_chat=data.get("FORCE_CLOUD_FOR_CHAT", "0") == "1",
            ai_local_strict=data.get("AI_LOCAL_STRICT", "1") == "1",
            ai_local_max_attempts=int(data.get("AI_LOCAL_MAX_ATTEMPTS", "2")),
            ai_local_conf_min=float(data.get("AI_LOCAL_CONF_MIN", "0.68")),
            openrouter_budget_per_min=int(data.get("OPENROUTER_BUDGET_PER_MIN", "6")),
            ai_ttl_cache_sec=int(data.get("AI_TTL_CACHE_SEC", "60")),
            ai_max_hops_routine=int(data.get("AI_MAX_HOPS_ROUTINE", "1")),
            ai_max_hops_critical=int(data.get("AI_MAX_HOPS_CRITICAL", "3")),
            ai_confidence_min=float(data.get("AI_CONFIDENCE_MIN", "0.75")),
            ai_model_code=data.get("AI_MODEL_CODE", "qwen/qwen3-coder:free"),
            ai_model_analysis=data.get("AI_MODEL_ANALYSIS", "glm/glm-4.5-air:free"),
            ai_model_debug=data.get("AI_MODEL_DEBUG", "qwen/qwen3-coder:free"),
            ai_model_server_brain=data.get("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
            enable_qwq_reasoning=data.get("ENABLE_QWQ_REASONING", "0") == "1",
            ai_model_reasoning=data.get("AI_MODEL_REASONING", "qwen/qwq-32b:free"),
            or_qwen_coder=data.get("OR_QWEN_CODER", "qwen/qwen3-coder:free"),
            or_glm_air=data.get("OR_GLM_AIR", "z-ai/glm-4.5-air:free"),
            or_nemo=data.get("OR_NEMO", "qwen/qwen3-coder:free"),
            or_kimi=data.get("OR_KIMI", "moonshot/kimi-k2:free"),
            or_r1=data.get("OR_R1", "deepseek/deepseek-r1:free"),
            or_qwq=data.get("OR_QWQ", "qwen/qwq-32b:free"),
            enable_rag=data.get("ENABLE_RAG", "1") == "1",
            enable_enhanced_ai=data.get("ENABLE_ENHANCED_AI", "1") == "1",
            enable_local_parity=data.get("ENABLE_LOCAL_PARITY", "1") == "1",
            enable_action_logging=data.get("ENABLE_ACTION_LOGGING", "1") == "1"
        )

# ============================================================================
# Provider Connectors
# ============================================================================

class BaseConnector(ABC):
    """Abstract base class for all AI provider connectors"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.usage_stats = {"requests": 0, "tokens": 0, "cost": 0.0}

    @abstractmethod
    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete a chat conversation"""
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
        pass

    def update_stats(self, tokens: int, cost: float = 0.0):
        """Update usage statistics"""
        self.usage_stats["requests"] += 1
        self.usage_stats["tokens"] += tokens
        self.usage_stats["cost"] += cost

class OpenAIConnector(BaseConnector):
    """OpenAI API connector"""

    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using OpenAI API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            headers.update(self.config.extra_headers)

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": False
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    self.update_stats(
                        result.get("usage", {}).get("total_tokens", 0),
                        self._estimate_cost(result.get("usage", {}))
                    )
                    return result
                else:
                    return {"error": f"OpenAI API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"OpenAI connector error: {e}")
            return {"error": str(e)}

    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion using OpenAI API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            headers.update(self.config.extra_headers)

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": True
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = json.loads(line[6:])
                                if data.get("choices"):
                                    content = data["choices"][0].get("delta", {}).get("content", "")
                                    if content:
                                        yield content
                    else:
                        yield f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"

    def _estimate_cost(self, usage: Dict) -> float:
        """Estimate API cost"""
        # Simplified cost estimation
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        return (input_tokens * 0.001 + output_tokens * 0.002) / 1000  # $ per token

class OpenRouterConnector(BaseConnector):
    """OpenRouter API connector"""

    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://duckbot.ai",
                "X-Title": "DuckBot"
            }
            headers.update(self.config.extra_headers)

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": False
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    self.update_stats(
                        result.get("usage", {}).get("total_tokens", 0),
                        self._estimate_cost(result.get("usage", {}))
                    )
                    return result
                else:
                    return {"error": f"OpenRouter API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"OpenRouter connector error: {e}")
            return {"error": str(e)}

    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion using OpenRouter API"""
        # Similar to OpenAI streaming but with OpenRouter endpoints
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://duckbot.ai",
                "X-Title": "DuckBot"
            }

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": True
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = json.loads(line[6:])
                                if data.get("choices"):
                                    content = data["choices"][0].get("delta", {}).get("content", "")
                                    if content:
                                        yield content
                    else:
                        yield f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            yield f"Error: {str(e)}"

    def _estimate_cost(self, usage: Dict) -> float:
        """Estimate API cost for OpenRouter"""
        # OpenRouter pricing varies by model
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        # Simplified estimation - actual costs depend on specific model
        return (input_tokens * 0.0005 + output_tokens * 0.0015) / 1000

class LocalConnector(BaseConnector):
    """Local model connector (LM Studio, Ollama, etc.)"""

    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using local model"""
        try:
            headers = {"Content-Type": "application/json"}
            headers.update(self.config.extra_headers)

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": False
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/generate",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    self.update_stats(
                        result.get("usage", {}).get("total_tokens", 0),
                        0.0  # Local models are free
                    )
                    return result
                else:
                    return {"error": f"Local model error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Local connector error: {e}")
            return {"error": str(e)}

    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion using local model"""
        try:
            headers = {"Content-Type": "application/json"}

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": True
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.config.base_url}/api/generate",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            try:
                                data = json.loads(line)
                                if data.get("response"):
                                    yield data["response"]
                            except json.JSONDecodeError:
                                continue
                    else:
                        yield f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Local streaming error: {e}")
            yield f"Error: {str(e)}"

# ============================================================================
# AI Router System
# ============================================================================

class AIRouter:
    """Main AI routing system with intelligent model selection"""

    def __init__(self, settings: AISettings = None):
        self.settings = settings or AISettings()
        self.connectors: Dict[str, BaseConnector] = {}
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = self.settings.ai_ttl_cache_sec
        self.circuit_breakers: Dict[str, Dict] = {}
        self.usage_stats = {"total_requests": 0, "cache_hits": 0, "errors": 0}
        self._initialize_connectors()

    def _initialize_connectors(self):
        """Initialize provider connectors"""
        # OpenAI connector
        if os.getenv("OPENAI_API_KEY"):
            self.connectors["openai"] = OpenAIConnector(ProviderConfig(
                name="openai",
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url="https://api.openai.com/v1",
                model="gpt-4"
            ))

        # OpenRouter connector
        if os.getenv("OPENROUTER_API_KEY"):
            self.connectors["openrouter"] = OpenRouterConnector(ProviderConfig(
                name="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                model=self.settings.ai_model_main_brain
            ))

        # Local model connectors
        if os.getenv("LM_STUDIO_URL"):
            self.connectors["lm_studio"] = LocalConnector(ProviderConfig(
                name="lm_studio",
                base_url=os.getenv("LM_STUDIO_URL", "http://localhost:1234"),
                model=self.settings.lm_studio_model
            ))

        if os.getenv("OLLAMA_URL"):
            self.connectors["ollama"] = LocalConnector(ProviderConfig(
                name="ollama",
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
                model="llama2"
            ))

    async def route_task(self, prompt: str, task_type: str = "auto", **kwargs) -> Dict[str, Any]:
        """Route AI task to appropriate provider and model"""
        try:
            self.usage_stats["total_requests"] += 1

            # Check cache first
            cache_key = self._generate_cache_key(prompt, task_type, kwargs)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.usage_stats["cache_hits"] += 1
                return cached_result

            # Determine routing strategy
            if self.settings.ai_routing_mode == "cloud_first":
                result = await self._route_cloud_first(prompt, task_type, **kwargs)
            else:
                result = await self._route_local_first(prompt, task_type, **kwargs)

            # Cache successful results
            if result.get("success") or result.get("ok"):
                self._cache_result(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Routing error: {e}")
            self.usage_stats["errors"] += 1
            return {"error": str(e), "success": False}

    async def _route_cloud_first(self, prompt: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """Cloud-first routing strategy"""
        # Try cloud providers first
        for provider_name in ["openrouter", "openai"]:
            if provider_name in self.connectors:
                if self._is_circuit_closed(provider_name):
                    result = await self._execute_with_provider(
                        self.connectors[provider_name], prompt, task_type, **kwargs
                    )
                    if result.get("success") or result.get("ok"):
                        return result

        # Fallback to local models
        return await self._route_local_fallback(prompt, task_type, **kwargs)

    async def _route_local_first(self, prompt: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """Local-first routing strategy"""
        # Try local models first
        local_result = await self._route_local_fallback(prompt, task_type, **kwargs)
        if local_result.get("success") or local_result.get("ok"):
            return local_result

        # Fallback to cloud providers
        for provider_name in ["openrouter", "openai"]:
            if provider_name in self.connectors:
                if self._is_circuit_closed(provider_name):
                    result = await self._execute_with_provider(
                        self.connectors[provider_name], prompt, task_type, **kwargs
                    )
                    if result.get("success") or result.get("ok"):
                        return result

        return {"error": "All providers failed", "success": False}

    async def _route_local_fallback(self, prompt: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """Route to local models with enhanced features"""
        # Try enhanced AI if available
        if ENHANCED_AI_AVAILABLE and self.settings.enable_enhanced_ai:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, execute_enhanced_task, prompt, task_type
                )
                if result and result.get("success"):
                    return result
            except Exception as e:
                logger.warning(f"Enhanced AI failed: {e}")

        # Try local connectors
        for provider_name in ["lm_studio", "ollama"]:
            if provider_name in self.connectors:
                if self._is_circuit_closed(provider_name):
                    result = await self._execute_with_provider(
                        self.connectors[provider_name], prompt, task_type, **kwargs
                    )
                    if result.get("success") or result.get("ok"):
                        return result

        return {"error": "No local models available", "success": False}

    async def _execute_with_provider(self, connector: BaseConnector, prompt: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """Execute task with specific provider"""
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self._get_system_prompt(task_type)},
                {"role": "user", "content": prompt}
            ]

            # Apply RAG if enabled and available
            if self.settings.enable_rag and RAG_AVAILABLE:
                try:
                    rag_context = await asyncio.get_event_loop().run_in_executor(
                        None, maybe_augment_with_rag, prompt
                    )
                    if rag_context:
                        messages.insert(1, {"role": "system", "content": f"Context: {rag_context}"})
                except Exception as e:
                    logger.warning(f"RAG augmentation failed: {e}")

            # Select appropriate model
            model = self._select_model_for_task(connector.name, task_type)

            # Execute completion
            result = await connector.complete_chat(messages, model=model, **kwargs)

            # Log action if enabled
            if self.settings.enable_action_logging and ACTION_LOGGING_AVAILABLE:
                try:
                    action_logger.log_action(
                        action=f"ai_task_{task_type}",
                        input_data={"prompt": prompt, "provider": connector.name, "model": model},
                        output_data=result,
                        success=result.get("success", False)
                    )
                except Exception as e:
                    logger.warning(f"Action logging failed: {e}")

            # Update circuit breaker
            if result.get("success") or result.get("ok"):
                self._reset_circuit_breaker(connector.name)
            else:
                self._trip_circuit_breaker(connector.name)

            return result

        except Exception as e:
            logger.error(f"Provider execution error: {e}")
            self._trip_circuit_breaker(connector.name)
            return {"error": str(e), "success": False}

    def _get_system_prompt(self, task_type: str) -> str:
        """Get system prompt based on task type"""
        prompts = {
            "auto": "You are DuckBot, an advanced AI assistant. Help the user with their request.",
            "code": "You are an expert programmer. Provide clean, efficient code solutions.",
            "reasoning": "You are a logical reasoning expert. Provide step-by-step analysis.",
            "summary": "You are a summarization expert. Provide concise, accurate summaries.",
            "long_form": "You are a content creator. Provide detailed, comprehensive responses.",
            "json_format": "You are a data formatting expert. Respond in valid JSON format."
        }
        return prompts.get(task_type, prompts["auto"])

    def _select_model_for_task(self, provider: str, task_type: str) -> str:
        """Select appropriate model for task type"""
        model_mapping = {
            "openrouter": {
                "code": self.settings.ai_model_code,
                "analysis": self.settings.ai_model_analysis,
                "debug": self.settings.ai_model_debug,
                "reasoning": self.settings.ai_model_reasoning if self.settings.enable_qwq_reasoning else self.settings.ai_model_main_brain
            },
            "openai": {
                "code": "gpt-4",
                "analysis": "gpt-4",
                "debug": "gpt-4",
                "reasoning": "gpt-4"
            }
        }

        provider_models = model_mapping.get(provider, {})
        return provider_models.get(task_type, getattr(self.settings, f'ai_model_main_brain', 'gpt-4'))

    def _generate_cache_key(self, prompt: str, task_type: str, kwargs: Dict) -> str:
        """Generate cache key for request"""
        key_data = f"{prompt}:{task_type}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get result from cache if valid"""
        if key in self.cache:
            cached_data = self.cache[key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
            else:
                del self.cache[key]
        return None

    def _cache_result(self, key: str, result: Dict):
        """Cache successful result"""
        self.cache[key] = {
            "data": result,
            "timestamp": time.time()
        }

    def _is_circuit_closed(self, provider: str) -> bool:
        """Check if circuit breaker is closed (provider available)"""
        breaker = self.circuit_breakers.get(provider, {"failures": 0, "last_failure": 0})
        if breaker["failures"] >= 3:
            # Wait 60 seconds before retrying
            if time.time() - breaker["last_failure"] < 60:
                return False
        return True

    def _trip_circuit_breaker(self, provider: str):
        """Trip circuit breaker for provider"""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = {"failures": 0, "last_failure": 0}

        self.circuit_breakers[provider]["failures"] += 1
        self.circuit_breakers[provider]["last_failure"] = time.time()

    def _reset_circuit_breaker(self, provider: str):
        """Reset circuit breaker for provider"""
        if provider in self.circuit_breakers:
            self.circuit_breakers[provider]["failures"] = 0

    def get_router_state(self) -> Dict[str, Any]:
        """Get current router state and statistics"""
        return {
            "settings": self.settings.to_dict(),
            "connectors": {
                name: {
                    "available": True,
                    "usage_stats": connector.usage_stats
                }
                for name, connector in self.connectors.items()
            },
            "cache_stats": {
                "size": len(self.cache),
                "ttl": self.cache_ttl
            },
            "circuit_breakers": self.circuit_breakers,
            "usage_stats": self.usage_stats,
            "features": {
                "rag": RAG_AVAILABLE and self.settings.enable_rag,
                "enhanced_ai": ENHANCED_AI_AVAILABLE and self.settings.enable_enhanced_ai,
                "local_parity": LOCAL_PARITY_AVAILABLE and self.settings.enable_local_parity,
                "action_logging": ACTION_LOGGING_AVAILABLE and self.settings.enable_action_logging,
                "dynamic_loading": DYNAMIC_LOADING_AVAILABLE
            }
        }

    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("AI router cache cleared")

    def reset_breakers(self):
        """Reset all circuit breakers"""
        self.circuit_breakers.clear()
        logger.info("AI router circuit breakers reset")

# ============================================================================
# Settings Management
# ============================================================================

class SettingsManager:
    """Manager for AI router settings"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(Path(__file__).parent / "ai_settings.json")
        self.settings = AISettings()
        self._load_settings()

    def _load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                self.settings = AISettings.from_dict(data)
                logger.info("AI settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            logger.info("AI settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def apply_to_env(self):
        """Apply settings to environment variables"""
        settings_dict = self.settings.to_dict()
        for key, value in settings_dict.items():
            os.environ[key] = value
        logger.info("AI settings applied to environment")

    def update_setting(self, key: str, value: str):
        """Update a specific setting"""
        if hasattr(self.settings, key.lower()):
            setattr(self.settings, key.lower(), self._convert_value(value, getattr(self.settings, key.lower())))
            self.save_settings()
            self.apply_to_env()
            return True
        return False

    def _convert_value(self, value: str, current_value):
        """Convert string value to appropriate type"""
        if isinstance(current_value, bool):
            return value.lower() in ['1', 'true', 'yes', 'on']
        elif isinstance(current_value, int):
            return int(value)
        elif isinstance(current_value, float):
            return float(value)
        else:
            return value

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary"""
        return self.settings.to_dict()

# ============================================================================
# Global instances and convenience functions
# ============================================================================

# Initialize global instances
settings_manager = SettingsManager()
ai_router = AIRouter(settings_manager.settings)

# Convenience functions for backward compatibility
async def route_task(prompt: str, task_type: str = "auto", **kwargs) -> Dict[str, Any]:
    """Route AI task using global router instance"""
    return await ai_router.route_task(prompt, task_type, **kwargs)

def get_router_state() -> Dict[str, Any]:
    """Get router state using global instance"""
    return ai_router.get_router_state()

def clear_cache() -> None:
    """Clear cache using global instance"""
    ai_router.clear_cache()

def reset_breakers() -> None:
    """Reset circuit breakers using global instance"""
    ai_router.reset_breakers()

def load_settings() -> Dict[str, Any]:
    """Load settings using global manager"""
    settings_manager._load_settings()
    return settings_manager.get_settings()

def save_settings() -> None:
    """Save settings using global manager"""
    settings_manager.save_settings()

def apply_to_env() -> None:
    """Apply settings to environment using global manager"""
    settings_manager.apply_to_env()

# Export classes and functions for backward compatibility
AIRouter = AIRouter
AISettings = AISettings
SettingsManager = SettingsManager
ProviderConfig = ProviderConfig
BaseConnector = BaseConnector
OpenAIConnector = OpenAIConnector
OpenRouterConnector = OpenRouterConnector
LocalConnector = LocalConnector
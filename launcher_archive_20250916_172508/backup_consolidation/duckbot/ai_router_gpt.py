#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot AI Router System
Intelligent model selection and routing across multiple providers
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    QWEN = "qwen"

@dataclass
class ModelConfig:
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7

class AIRouter:
    """
    Intelligent AI model router that selects the best model for each task
    """

    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.usage_stats = {}
        self.cost_tracker = {}
        self.load_models_config()

    def load_models_config(self):
        """Load model configurations from environment and config files"""
        # Load OpenAI config
        if os.getenv("OPENAI_API_KEY"):
            self.models["gpt-4"] = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=4000
            )
            self.models["gpt-3.5-turbo"] = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=4000
            )

        # Load Anthropic config
        if os.getenv("ANTHROPIC_API_KEY"):
            self.models["claude-3"] = ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                max_tokens=4000
            )

        # Load local model config
        if os.getenv("LOCAL_MODEL_URL"):
            self.models["local"] = ModelConfig(
                provider=ModelProvider.LOCAL,
                model_name="local-llm",
                base_url=os.getenv("LOCAL_MODEL_URL"),
                max_tokens=4000
            )

        # Load Qwen config
        if os.getenv("QWEN_API_KEY"):
            self.models["qwen"] = ModelConfig(
                provider=ModelProvider.QWEN,
                model_name="qwen-turbo",
                api_key=os.getenv("QWEN_API_KEY"),
                base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"),
                max_tokens=4000
            )

    def select_model(self, task_type: str = "general", complexity: str = "medium") -> str:
        """
        Select the best model for the given task
        """
        # Simple selection logic - can be enhanced
        available_models = list(self.models.keys())

        if not available_models:
            logger.warning("No models available")
            return None

        # Priority-based selection
        if complexity == "high" and "gpt-4" in available_models:
            return "gpt-4"
        elif complexity == "medium" and "claude-3" in available_models:
            return "claude-3"
        elif "gpt-3.5-turbo" in available_models:
            return "gpt-3.5-turbo"
        elif "local" in available_models:
            return "local"
        elif "qwen" in available_models:
            return "qwen"
        else:
            return available_models[0]

    async def route_request(self, prompt: str, task_type: str = "general", complexity: str = "medium") -> Dict[str, Any]:
        """
        Route a request to the appropriate model
        """
        model_name = self.select_model(task_type, complexity)
        if not model_name:
            return {"error": "No models available"}

        model_config = self.models[model_name]

        try:
            if model_config.provider == ModelProvider.OPENAI:
                return await self._call_openai(model_config, prompt)
            elif model_config.provider == ModelProvider.ANTHROPIC:
                return await self._call_anthropic(model_config, prompt)
            elif model_config.provider == ModelProvider.LOCAL:
                return await self._call_local(model_config, prompt)
            elif model_config.provider == ModelProvider.QWEN:
                return await self._call_qwen(model_config, prompt)
            else:
                return {"error": f"Unsupported provider: {model_config.provider}"}
        except Exception as e:
            logger.error(f"Error calling {model_name}: {e}")
            return {"error": str(e)}

    async def _call_openai(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=config.api_key)

            response = client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )

            return {
                "response": response.choices[0].message.content,
                "model": config.model_name,
                "provider": "openai",
                "usage": response.usage.model_dump() if hasattr(response, 'usage') else {}
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"error": str(e)}

    async def _call_anthropic(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.api_key)

            response = client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "response": response.content[0].text,
                "model": config.model_name,
                "provider": "anthropic",
                "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
            }
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return {"error": str(e)}

    async def _call_local(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """Call local model API"""
        try:
            response = requests.post(
                config.base_url,
                json={
                    "prompt": prompt,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature
                },
                timeout=60
            )
            response.raise_for_status()

            return {
                "response": response.json().get("response", ""),
                "model": config.model_name,
                "provider": "local",
                "usage": response.json().get("usage", {})
            }
        except Exception as e:
            logger.error(f"Local model error: {e}")
            return {"error": str(e)}

    async def _call_qwen(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """Call Qwen API"""
        try:
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": config.model_name,
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature
                }
            }

            response = requests.post(
                config.base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return {
                "response": result.get("output", {}).get("text", ""),
                "model": config.model_name,
                "provider": "qwen",
                "usage": result.get("usage", {})
            }
        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            return {"error": str(e)}

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return [
            {
                "name": name,
                "provider": config.provider.value,
                "model_name": config.model_name,
                "max_tokens": config.max_tokens
            }
            for name, config in self.models.items()
        ]

# Export functions for MCP server integration
def route_task(prompt: str, task_type: str = "general", complexity: str = "medium") -> Dict[str, Any]:
    """Route a task to the appropriate AI model (async wrapper)"""
    router = AIRouter()
    return asyncio.run(router.route_request(prompt, task_type, complexity))

async def route_task_async(prompt: str, task_type: str = "general", complexity: str = "medium") -> Dict[str, Any]:
    """Route a task to the appropriate AI model (async version)"""
    router = AIRouter()
    return await router.route_request(prompt, task_type, complexity)

def get_available_providers() -> List[str]:
    """Get list of available AI providers"""
    router = AIRouter()
    return list(set(model['provider'] for model in router.get_available_models()))

def get_ollama_model(model_name: str = "llama2") -> Dict[str, Any]:
    """Get information about a specific Ollama model"""
    router = AIRouter()
    for model in router.get_available_models():
        if model['provider'] == 'ollama' and model_name in model['name'].lower():
            return model
    return {"error": f"Model {model_name} not found in Ollama"}

async def main():
    """Main function for running the AI router"""
    router = AIRouter()

    # Example usage
    print("Available models:", router.get_available_models())

    # Test with a simple prompt
    result = await router.route_request("Hello, how are you?")
    print("Test result:", result)

if __name__ == "__main__":
    asyncio.run(main())
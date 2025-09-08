"""
DuckBot Enhanced Provider Connectors
SmythOS-inspired pluggable connector system for seamless provider switching
"""

import os
import json
import requests
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

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
    extra_headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.extra_headers is None:
            self.extra_headers = {}

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
        """Stream a chat conversation"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate connector configuration and connection"""
        pass
    
    def update_stats(self, tokens_used: int, cost: float = 0.0):
        """Update usage statistics"""
        self.usage_stats["requests"] += 1
        self.usage_stats["tokens"] += tokens_used
        self.usage_stats["cost"] += cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.usage_stats.copy()


class OpenRouterConnector(BaseConnector):
    """OpenRouter API connector with free models support"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = "https://openrouter.ai/api/v1"
        
        # Free models available without API key
        self.free_models = [
            "microsoft/phi-3-mini-128k-instruct:free",
            "google/gemma-7b-it:free",
            "meta-llama/llama-3-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "nousresearch/nous-capybara-7b:free",
            "openchat/openchat-7b:free"
        ]
    
    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using OpenRouter API"""
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://duckbot-ai.local/",
            "X-Title": "DuckBot AI Enhanced",
            **self.config.extra_headers
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = {
            "model": kwargs.get("model", self.config.model or self.free_models[0]),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Update stats
            usage = result.get("usage", {})
            self.update_stats(usage.get("total_tokens", 0))
            
            return {
                "success": True,
                "content": result["choices"][0]["message"]["content"],
                "model": result.get("model", payload["model"]),
                "usage": usage,
                "provider": "openrouter"
            }
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "openrouter"
            }
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat using OpenRouter API"""
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://duckbot-ai.local/",
            "X-Title": "DuckBot AI Enhanced",
            **self.config.extra_headers
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = {
            "model": kwargs.get("model", self.config.model or self.free_models[0]),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{self.config.base_url}/chat/completions", headers=headers, json=payload, timeout=self.config.timeout) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line and line.startswith("data: "):
                            data = line[6:].decode("utf-8")
                            if data == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                        
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            yield f"Error: {e}"
    
    def get_available_models(self) -> List[str]:
        """Get available models from OpenRouter"""
        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            response = requests.get(
                f"{self.config.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                return [model["id"] for model in models.get("data", [])]
            else:
                return self.free_models
                
        except Exception:
            return self.free_models
    
    def validate_connection(self) -> bool:
        """Validate OpenRouter connection"""
        try:
            models = self.get_available_models()
            return len(models) > 0
        except:
            return False


class LMStudioConnector(BaseConnector):
    """Local LM Studio connector for privacy-first AI"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = "http://localhost:1234/v1"
    
    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using LM Studio local API"""
        payload = {
            "model": kwargs.get("model", self.config.model or "local-model"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    json=payload,
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Update stats (no cost for local)
            usage = result.get("usage", {})
            self.update_stats(usage.get("total_tokens", 0), 0.0)
            
            return {
                "success": True,
                "content": result["choices"][0]["message"]["content"],
                "model": result.get("model", "local"),
                "usage": usage,
                "provider": "lm_studio",
                "cost": 0.0
            }
            
        except Exception as e:
            logger.error(f"LM Studio error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "lm_studio"
            }
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat using LM Studio"""
        payload = {
            "model": kwargs.get("model", self.config.model or "local-model"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{self.config.base_url}/chat/completions", json=payload, timeout=self.config.timeout) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line and line.startswith("data: "):
                            data = line[6:].decode("utf-8")
                            if data == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                        
        except Exception as e:
            logger.error(f"LM Studio streaming error: {e}")
            yield f"Error: {e}"
    
    def get_available_models(self) -> List[str]:
        """Get available models from LM Studio"""
        try:
            response = requests.get(f"{self.config.base_url}/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                return [model["id"] for model in models.get("data", [])]
            return ["local-model"]
        except:
            return ["local-model"]
    
    def validate_connection(self) -> bool:
        """Validate LM Studio connection"""
        try:
            response = requests.get(f"{self.config.base_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False


class AnthropicConnector(BaseConnector):
    """Anthropic Claude API connector"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = "https://api.anthropic.com/v1"
        if not config.model:
            config.model = "claude-3-haiku-20240307"
    
    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using Anthropic API"""
        if not self.config.api_key:
            return {
                "success": False,
                "error": "Anthropic API key required",
                "provider": "anthropic"
            }
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            **self.config.extra_headers
        }
        
        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        payload = {
            "model": kwargs.get("model", self.config.model),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "messages": anthropic_messages
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Update stats
            usage = result.get("usage", {})
            self.update_stats(usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
            
            return {
                "success": True,
                "content": result["content"][0]["text"],
                "model": result.get("model", payload["model"]),
                "usage": usage,
                "provider": "anthropic"
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "anthropic"
            }
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat using Anthropic API"""
        # Note: Anthropic streaming implementation would go here
        # For now, fall back to non-streaming
        result = await self.complete_chat(messages, **kwargs)
        if result.get("success"):
            yield result["content"]
        else:
            yield f"Error: {result.get('error', 'Unknown error')}"
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022"
        ]
    
    def validate_connection(self) -> bool:
        """Validate Anthropic connection"""
        if not self.config.api_key:
            return False
        
        try:
            # Simple validation request
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01"
            }
            response = requests.post(
                f"{self.config.base_url}/messages",
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


class ClaudeCodeRouterConnector(BaseConnector):
    """Claude Code Router connector for code analysis"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.base_url:
            config.base_url = "http://localhost:8765"
    
    async def complete_chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Complete chat using Claude Code Router"""
        # This would integrate with our existing Claude Code Router
        try:
            # Import the Claude Code integration
            from duckbot.claude_code_integration import execute_claude_code_task
            
            # Convert messages to task format
            last_message = messages[-1]["content"] if messages else ""
            context = {
                "messages": messages,
                "task_type": kwargs.get("task_type", "code_analysis")
            }
            
            result = await execute_claude_code_task(last_message, context)
            
            if result.get("success"):
                return {
                    "success": True,
                    "content": result["response"],
                    "model": result.get("model", "claude-code-router"),
                    "provider": "claude_code_router"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Claude Code Router failed"),
                    "provider": "claude_code_router"
                }
                
        except Exception as e:
            logger.error(f"Claude Code Router error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "claude_code_router"
            }
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat using Claude Code Router"""
        result = await self.complete_chat(messages, **kwargs)
        if result.get("success"):
            yield result["content"]
        else:
            yield f"Error: {result.get('error', 'Unknown error')}"
    
    def get_available_models(self) -> List[str]:
        """Get available Claude Code Router models"""
        return ["claude-code-router", "anthropic/claude-3.5-sonnet"]
    
    def validate_connection(self) -> bool:
        """Validate Claude Code Router connection"""
        try:
            from duckbot.claude_code_integration import is_claude_code_available
            return is_claude_code_available()
        except:
            return False


class ConnectorManager:
    """Central manager for all AI provider connectors"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.connectors: Dict[str, BaseConnector] = {}
        self.active_connector = "openrouter"  # Default
        self.config_file = config_file or "provider_config.json"
        self.load_configuration()
    
    def load_configuration(self):
        """Load connector configurations from file"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)
                    
                self.active_connector = config_data.get("active_provider", "openrouter")
                
                for provider_name, provider_config in config_data.get("providers", {}).items():
                    self.register_connector(provider_name, provider_config)
                    
            except Exception as e:
                logger.error(f"Error loading connector config: {e}")
                self.create_default_configuration()
        else:
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default configuration file"""
        default_config = {
            "active_provider": "openrouter",
            "providers": {
                "openrouter": {
                    "name": "openrouter",
                    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                    "base_url": "https://openrouter.ai/api/v1",
                    "model": "microsoft/phi-3-mini-128k-instruct:free",
                    "extra_headers": {
                        "HTTP-Referer": "https://duckbot-ai.local/",
                        "X-Title": "DuckBot AI Enhanced"
                    }
                },
                "lm_studio": {
                    "name": "lm_studio",
                    "base_url": "http://localhost:1234/v1",
                    "model": "local-model"
                },
                "anthropic": {
                    "name": "anthropic",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "model": "claude-3-haiku-20240307"
                },
                "claude_code_router": {
                    "name": "claude_code_router",
                    "base_url": "http://localhost:8765"
                }
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default provider config: {self.config_file}")
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
        
        # Register default connectors
        for provider_name, provider_config in default_config["providers"].items():
            self.register_connector(provider_name, provider_config)
    
    def register_connector(self, name: str, config_dict: Dict[str, Any]):
        """Register a new connector"""
        config = ProviderConfig(**config_dict)
        
        connector_classes = {
            "openrouter": OpenRouterConnector,
            "lm_studio": LMStudioConnector,
            "anthropic": AnthropicConnector,
            "claude_code_router": ClaudeCodeRouterConnector
        }
        
        connector_class = connector_classes.get(name)
        if connector_class:
            self.connectors[name] = connector_class(config)
            logger.info(f"Registered {name} connector")
        else:
            logger.warning(f"Unknown connector type: {name}")
    
    def switch_provider(self, provider_name: str) -> bool:
        """Switch active provider"""
        if provider_name in self.connectors:
            if self.connectors[provider_name].validate_connection():
                self.active_connector = provider_name
                logger.info(f"Switched to provider: {provider_name}")
                return True
            else:
                logger.error(f"Provider {provider_name} connection validation failed")
                return False
        else:
            logger.error(f"Provider {provider_name} not found")
            return False
    
    def get_active_connector(self) -> BaseConnector:
        """Get the currently active connector"""
        return self.connectors.get(self.active_connector)
    
    def get_all_providers(self) -> List[str]:
        """Get list of all available providers"""
        return list(self.connectors.keys())
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for name, connector in self.connectors.items():
            status[name] = {
                "active": name == self.active_connector,
                "connected": connector.validate_connection(),
                "stats": connector.get_stats(),
                "models": connector.get_available_models()[:5]  # First 5 models
            }
        return status
    
    async def complete_chat(self, messages: List[Dict], provider: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Complete chat using specified or active provider"""
        connector_name = provider or self.active_connector
        connector = self.connectors.get(connector_name)
        
        if not connector:
            return {
                "success": False,
                "error": f"Provider {connector_name} not available"
            }
        
        return await connector.complete_chat(messages, **kwargs)
    
    async def stream_chat(self, messages: List[Dict], provider: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat using specified or active provider"""
        connector_name = provider or self.active_connector
        connector = self.connectors.get(connector_name)
        
        if not connector:
            yield f"Error: Provider {connector_name} not available"
            return
        
        async for chunk in connector.stream_chat(messages, **kwargs):
            yield chunk


# Global connector manager instance
connector_manager = ConnectorManager()


# Convenience functions for easy integration
async def complete_chat(messages: List[Dict], provider: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Complete chat using connector manager"""
    return await connector_manager.complete_chat(messages, provider, **kwargs)

async def stream_chat(messages: List[Dict], provider: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
    """Stream chat using connector manager"""
    async for chunk in connector_manager.stream_chat(messages, provider, **kwargs):
        yield chunk

def switch_provider(provider_name: str) -> bool:
    """Switch active AI provider"""
    return connector_manager.switch_provider(provider_name)

def get_provider_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all providers"""
    return connector_manager.get_provider_status()

def get_available_providers() -> List[str]:
    """Get list of available providers"""
    return connector_manager.get_all_providers()
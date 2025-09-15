#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Claude Providers Integration
Consolidates all Claude Code related integrations into a single module
Includes native Claude Code, Claude Code Router, and Z.ai Claude integration
"""

import os
import subprocess
import asyncio
import logging
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClaudeProviderConfig:
    """Configuration for Claude providers"""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    enabled: bool = True
    max_tokens: int = 4000
    temperature: float = 0.7

class ClaudeCodeIntegration:
    """Native Claude Code integration"""

    def __init__(self):
        self.available = False
        self.claude_code_path = None
        self.version = None

    async def initialize(self) -> bool:
        """Initialize Claude Code integration"""
        try:
            # Check if Claude Code is installed
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.available = True
                self.version = result.stdout.strip().split()[-1]
                logger.info(f"Claude Code detected: version {self.version}")
            else:
                logger.info("Claude Code not found in PATH")

            return self.available

        except Exception as e:
            logger.error(f"Failed to check Claude Code: {e}")
            return False

    async def execute_command(self, command: str, working_dir: str = None) -> Dict[str, Any]:
        """Execute a command using Claude Code"""
        if not self.available:
            return {"error": "Claude Code not available"}

        try:
            cmd = ["claude", command]
            if working_dir:
                cmd.extend(["--directory", working_dir])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

class ClaudeCodeRouterIntegration:
    """Claude Code Router MCP integration"""

    def __init__(self):
        self.available = False
        self.router_process = None
        self.port = 8765  # Default port
        self.base_url = f"http://localhost:{self.port}"

    async def initialize(self) -> bool:
        """Initialize Claude Code Router"""
        try:
            # Check if router is already running
            if await self._check_router_running():
                self.available = True
                return True

            # Try to start router
            self.router_process = subprocess.Popen(
                ["python", "-m", "claude_code_router", "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait a moment for startup
            await asyncio.sleep(2)

            if await self._check_router_running():
                self.available = True
                logger.info(f"Claude Code Router started on port {self.port}")
                return True
            else:
                logger.error("Failed to start Claude Code Router")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize Claude Code Router: {e}")
            return False

    async def _check_router_running(self) -> bool:
        """Check if router is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    async def route_task(self, prompt: str, task_type: str = "general") -> Dict[str, Any]:
        """Route task through Claude Code Router"""
        if not self.available:
            return {"error": "Claude Code Router not available"}

        try:
            response = requests.post(
                f"{self.base_url}/route",
                json={
                    "prompt": prompt,
                    "task_type": task_type
                },
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Router error: {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    async def cleanup(self):
        """Cleanup router process"""
        if self.router_process:
            self.router_process.terminate()
            await asyncio.sleep(1)
            if self.router_process.poll() is None:
                self.router_process.kill()

class ZAIClaudeIntegration:
    """Z.ai Claude Code integration"""

    def __init__(self, config: ClaudeProviderConfig = None):
        self.config = config or ClaudeProviderConfig(
            name="zai",
            api_key=os.getenv("ZAI_API_KEY", ""),
            base_url="https://api.z.ai/v1",
            model="claude-3-5-sonnet-20241022"
        )
        self.available = bool(self.config.api_key)

    async def chat_completion(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Send chat completion request to Z.ai Claude"""
        if not self.available:
            return {"error": "Z.ai API key not configured"}

        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature)
            }

            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }

        except Exception as e:
            return {"error": str(e)}

class UnifiedClaudeProviders:
    """Unified interface for all Claude providers"""

    def __init__(self):
        self.native_claude = ClaudeCodeIntegration()
        self.router = ClaudeCodeRouterIntegration()
        self.zai = ZAIClaudeIntegration()
        self.providers = {
            "native": self.native_claude,
            "router": self.router,
            "zai": self.zai
        }

    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all Claude providers"""
        results = {}

        # Initialize all providers concurrently
        tasks = [
            self.native_claude.initialize(),
            self.router.initialize(),
        ]

        # Zai initializes without async call
        results["native"] = self.native_claude.available
        results["router"] = self.router.available
        results["zai"] = self.zai.available

        await asyncio.gather(*tasks, return_exceptions=True)
        results["native"] = self.native_claude.available
        results["router"] = self.router.available

        logger.info(f"Claude providers initialized: {results}")
        return results

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [name for name, provider in self.providers.items() if provider.available]

    async def execute_with_best_provider(
        self,
        prompt: str,
        task_type: str = "general",
        preferred_provider: str = None
    ) -> Dict[str, Any]:
        """Execute task with the best available provider"""

        # Use preferred provider if specified and available
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if provider.available:
                if preferred_provider == "native":
                    return await self.native_claude.execute_command(prompt)
                elif preferred_provider == "router":
                    return await self.router.route_task(prompt, task_type)
                elif preferred_provider == "zai":
                    messages = [{"role": "user", "content": prompt}]
                    return await self.zai.chat_completion(messages)

        # Try providers in order of preference
        for provider_name in ["router", "native", "zai"]:
            provider = self.providers[provider_name]
            if provider.available:
                try:
                    if provider_name == "native":
                        result = await self.native_claude.execute_command(prompt)
                        if result.get("success"):
                            result["provider"] = "native"
                            return result
                    elif provider_name == "router":
                        result = await self.router.route_task(prompt, task_type)
                        if "error" not in result:
                            result["provider"] = "router"
                            return result
                    elif provider_name == "zai":
                        messages = [{"role": "user", "content": prompt}]
                        result = await self.zai.chat_completion(messages)
                        if "error" not in result:
                            result["provider"] = "zai"
                            return result
                except Exception as e:
                    logger.error(f"Provider {provider_name} failed: {e}")
                    continue

        return {"error": "No Claude provider available"}

    async def cleanup(self):
        """Cleanup all providers"""
        await self.router.cleanup()

# Global instance
_claude_providers = None

def get_claude_providers() -> UnifiedClaudeProviders:
    """Get or create the global Claude providers instance"""
    global _claude_providers
    if _claude_providers is None:
        _claude_providers = UnifiedClaudeProviders()
    return _claude_providers

async def initialize_claude_providers() -> Dict[str, bool]:
    """Initialize all Claude providers"""
    return await get_claude_providers().initialize_all()

async def execute_claude_task(
    prompt: str,
    task_type: str = "general",
    preferred_provider: str = None
) -> Dict[str, Any]:
    """Execute a task using Claude providers"""
    return await get_claude_providers().execute_with_best_provider(
        prompt, task_type, preferred_provider
    )

# Legacy compatibility functions
async def init_claude_code_integration() -> bool:
    """Legacy function for backward compatibility"""
    results = await initialize_claude_providers()
    return any(results.values())

# Test functions
async def test_claude_providers():
    """Test all Claude providers"""
    providers = get_claude_providers()
    await providers.initialize_all()

    print("Available Claude providers:")
    for name in providers.get_available_providers():
        print(f"  - {name}")

    # Test a simple command
    test_prompt = "What is 2+2?"
    result = await providers.execute_with_best_provider(test_prompt)
    print(f"\nTest result: {result}")

if __name__ == "__main__":
    asyncio.run(test_claude_providers())
#!/usr/bin/env python3
"""
Z.ai Claude Code Integration for DuckBot
Provides Claude Code functionality using Z.ai API
"""

import os
import json
import logging
import requests
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ZAIClaudeCodeIntegration:
    """Z.ai Claude Code integration for DuckBot"""

    def __init__(self):
        self.api_key = os.getenv("ZAI_API_KEY", "")
        self.base_url = "https://api.z.ai/v1"
        self.model = "claude-3-5-sonnet-20241022"
        self.available = bool(self.api_key)

    async def chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Send chat completion request to Z.ai Claude"""
        if not self.available:
            return {"error": "Z.ai API key not configured"}

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.7)
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Z.ai API error: {response.status_code} - {response.text}")
                return {"error": f"API request failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Z.ai integration error: {e}")
            return {"error": str(e)}

    async def code_analysis(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code using Claude"""
        messages = [
            {
                "role": "system",
                "content": f"You are Claude Code, an expert programming assistant. Analyze the following {language} code and provide insights, suggestions, and improvements."
            },
            {
                "role": "user",
                "content": f"```{language}\n{code}\n```"
            }
        ]

        return await self.chat_completion(messages)

    async def generate_code(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """Generate code using Claude"""
        messages = [
            {
                "role": "system",
                "content": f"You are Claude Code, an expert programmer. Generate {language} code based on the following requirements."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        return await self.chat_completion(messages)

    async def debug_issue(self, code: str, error_message: str, language: str = "python") -> Dict[str, Any]:
        """Debug code issues using Claude"""
        messages = [
            {
                "role": "system",
                "content": f"You are Claude Code, an expert debugger. Help debug this {language} code."
            },
            {
                "role": "user",
                "content": f"Code:\n```{language}\n{code}\n```\n\nError: {error_message}"
            }
        ]

        return await self.chat_completion(messages)

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "available": self.available,
            "provider": "Z.ai",
            "model": self.model,
            "api_key_configured": bool(self.api_key),
            "features": [
                "code_analysis",
                "code_generation",
                "debugging",
                "chat_completion"
            ]
        }

# Global instance
zai_claude_integration = ZAIClaudeCodeIntegration()

# FastAPI integration functions
async def setup_zai_routes(app):
    """Setup Z.ai Claude Code routes"""

    @app.get("/api/zai/status")
    async def get_zai_status():
        return zai_claude_integration.get_status()

    @app.post("/api/zai/chat")
    async def zai_chat(request: dict):
        result = await zai_claude_integration.chat_completion(
            messages=request.get("messages", []),
            max_tokens=request.get("max_tokens", 4000),
            temperature=request.get("temperature", 0.7)
        )
        return result

    @app.post("/api/zai/analyze")
    async def zai_analyze(request: dict):
        result = await zai_claude_integration.code_analysis(
            code=request.get("code", ""),
            language=request.get("language", "python")
        )
        return result

    @app.post("/api/zai/generate")
    async def zai_generate(request: dict):
        result = await zai_claude_integration.generate_code(
            prompt=request.get("prompt", ""),
            language=request.get("language", "python")
        )
        return result

    @app.post("/api/zai/debug")
    async def zai_debug(request: dict):
        result = await zai_claude_integration.debug_issue(
            code=request.get("code", ""),
            error_message=request.get("error", ""),
            language=request.get("language", "python")
        )
        return result

# Integration with existing DuckBot systems
def integrate_with_ai_router():
    """Integrate Z.ai Claude with DuckBot's AI router"""
    try:
        from duckbot.ai_router_gpt import get_available_providers

        # Add Z.ai as a provider if not already present
        providers = get_available_providers()
        if "zai" not in providers:
            providers.append("zai")

        logger.info("Z.ai Claude Code integrated with AI router")
        return True
    except ImportError:
        logger.warning("Could not integrate with AI router - module not found")
        return False

# Initialize integration
def initialize_zai_integration():
    """Initialize Z.ai Claude Code integration"""
    logger.info("Initializing Z.ai Claude Code integration...")

    # Check if API key is configured
    if not zai_claude_integration.available:
        logger.warning("Z.ai API key not configured - set ZAI_API_KEY environment variable")
        return False

    # Integrate with existing systems
    integrate_with_ai_router()

    logger.info("Z.ai Claude Code integration initialized successfully")
    return True

if __name__ == "__main__":
    # Test the integration
    import asyncio

    async def test():
        status = zai_claude_integration.get_status()
        print(f"Z.ai Status: {status}")

        if status["available"]:
            # Test code analysis
            code = '''
def hello_world():
    print("Hello, World!")
            '''

            result = await zai_claude_integration.code_analysis(code)
            print("Analysis result:", json.dumps(result, indent=2))

    asyncio.run(test())
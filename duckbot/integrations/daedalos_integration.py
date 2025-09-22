#!/usr/bin/env python3
"""
DaedalOS Integration for DuckBot
Provides DuckBot AI capabilities to the DaedalOS web-based operating system
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from duckbot.ai_router_gpt import AIRouter
    from duckbot.core.dynamic_model_manager import DynamicModelManager
    from duckbot.integrations.bytebot_integration import ByteBotIntegration
    from duckbot.integrations.archon_integration import ArchonIntegration
    from duckbot.ui.discord_bot import DiscordBot
except ImportError as e:
    print(f"Warning: Some DuckBot modules not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DaedalOSIntegration:
    """Integrates DuckBot AI capabilities with DaedalOS"""

    def __init__(self):
        self.ai_router = None
        self.model_manager = None
        self.bytebot = None
        self.archon = None
        self.discord_bot = None
        self.running = False

    async def initialize(self):
        """Initialize all DuckBot components"""
        try:
            # Initialize AI Router
            try:
                self.ai_router = AIRouter()
                logger.info("AI Router initialized")
            except Exception as e:
                logger.warning(f"AI Router initialization failed: {e}")

            # Initialize Model Manager
            try:
                self.model_manager = DynamicModelManager()
                logger.info("Dynamic Model Manager initialized")
            except Exception as e:
                logger.warning(f"Model Manager initialization failed: {e}")

            # Initialize ByteBot
            try:
                self.bytebot = ByteBotIntegration()
                await self.bytebot.start_service()
                logger.info("ByteBot integration initialized")
            except Exception as e:
                logger.warning(f"ByteBot initialization failed: {e}")

            # Initialize Archon
            try:
                self.archon = ArchonIntegration()
                await self.archon.start_service()
                logger.info("Archon integration initialized")
            except Exception as e:
                logger.warning(f"Archon initialization failed: {e}")

            # Initialize Discord Bot
            try:
                self.discord_bot = DiscordBot()
                await self.discord_bot.start_service()
                logger.info("Discord Bot integration initialized")
            except Exception as e:
                logger.warning(f"Discord Bot initialization failed: {e}")

            self.running = True
            logger.info("DaedalOS Integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize DaedalOS integration: {e}")

    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a command from DaedalOS"""
        if not self.running:
            await self.initialize()

        result = {
            "success": False,
            "response": "",
            "actions": [],
            "error": None
        }

        try:
            # Route command through AI Router
            if self.ai_router:
                ai_result = await self.ai_router.route_task_async(command)
                result["response"] = ai_result.get("response", "")
                result["success"] = ai_result.get("success", False)

                # Add suggested actions
                if ai_result.get("actions"):
                    result["actions"].extend(ai_result["actions"])

            # Handle specific DaedalOS actions
            if "open_app" in command.lower():
                result["actions"].append({
                    "type": "open_application",
                    "app": self._extract_app_name(command)
                })

            elif "file" in command.lower():
                result["actions"].extend([
                    {"type": "file_operation", "operation": "list"},
                    {"type": "show_file_explorer"}
                ])

            elif "desktop" in command.lower():
                result["actions"].extend([
                    {"type": "desktop_operation", "operation": "show"},
                    {"type": "window_management", "action": "organize"}
                ])

            # Add ByteBot automation if available
            if self.bytebot and ("automate" in command.lower() or "control" in command.lower()):
                automation_result = await self.bytebot.process_command(command)
                if automation_result.get("success"):
                    result["actions"].append({
                        "type": "automation",
                        "description": automation_result.get("description", "")
                    })

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error processing command: {e}")

        return result

    def _extract_app_name(self, command: str) -> str:
        """Extract application name from command"""
        apps = ["browser", "terminal", "editor", "file_manager", "settings", "calculator"]
        for app in apps:
            if app in command.lower():
                return app
        return "unknown"

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status for DaedalOS"""
        status = {
            "duckbot_running": self.running,
            "services": {},
            "ai_models": [],
            "system_resources": {}
        }

        try:
            # Get AI Router status
            if self.ai_router:
                status["services"]["ai_router"] = "active"
                status["ai_models"] = self.ai_router.get_available_models()

            # Get Model Manager status
            if self.model_manager:
                status["services"]["model_manager"] = "active"
                status["system_resources"] = self.model_manager.get_system_info()

            # Get ByteBot status
            if self.bytebot:
                status["services"]["bytebot"] = "active"

            # Get Archon status
            if self.archon:
                status["services"]["archon"] = "active"

            # Get Discord Bot status
            if self.discord_bot:
                status["services"]["discord_bot"] = "active"

        except Exception as e:
            logger.error(f"Error getting system status: {e}")

        return status

    async def run_daedalos_server(self, host: str = "127.0.0.1", port: int = 8081):
        """Run the DaedalOS integration server"""
        try:
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            import uvicorn

            app = FastAPI(title="DuckBot DaedalOS Integration")

            @app.get("/")
            async def root():
                return {"message": "DuckBot DaedalOS Integration Server"}

            @app.post("/command")
            async def handle_command(request: Dict[str, Any]):
                command = request.get("command", "")
                context = request.get("context", {})

                if not command:
                    raise HTTPException(status_code=400, detail="No command provided")

                result = await self.process_command(command, context)
                return JSONResponse(result)

            @app.get("/status")
            async def get_status():
                return await self.get_system_status()

            @app.get("/health")
            async def health_check():
                return {"status": "healthy" if self.running else "initializing"}

            logger.info(f"Starting DaedalOS integration server on {host}:{port}")
            await uvicorn.run(app, host=host, port=port)

        except ImportError:
            logger.error("FastAPI not available. Install with: pip install fastapi uvicorn")
        except Exception as e:
            logger.error(f"Error running DaedalOS server: {e}")

async def main():
    """Main entry point for DaedalOS integration"""
    integration = DaedalOSIntegration()

    print("Starting DuckBot DaedalOS Integration...")
    print("This provides AI capabilities to the DaedalOS web-based operating system")
    print()

    # Initialize integration
    await integration.initialize()

    # Start server
    await integration.run_daedalos_server()

if __name__ == "__main__":
    asyncio.run(main())
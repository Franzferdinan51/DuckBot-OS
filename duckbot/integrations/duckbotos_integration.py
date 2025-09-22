#!/usr/bin/env python3
"""
DuckBotOS Integration - Enhanced Web Operating System
Combines DaedalOS with Handcrafted Persona Engine for complete AI-powered desktop experience
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from duckbot.ai_router_gpt import AIRouter
    from duckbot.core.dynamic_model_manager import DynamicModelManager
    from duckbot.integrations.bytebot_integration import ByteBotIntegration
    from duckbot.integrations.archon_integration import ArchonIntegration
    from duckbot.integrations.persona_engine_integration import PersonaEngineIntegration, PersonaEngineConfig
    from duckbot.ui.discord_bot import DiscordBot
    from duckbot.core.context_manager import ContextManager
    from duckbot.core.cost_management import CostTracker
except ImportError as e:
    print(f"Warning: Some DuckBot modules not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DuckBotOSConfig:
    """Configuration for DuckBotOS"""
    name: str = "DuckBotOS"
    version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8080
    api_port: int = 8081
    persona_port: int = 8788
    character_name: str = "DuckBot"
    character_model: str = "duckbot"
    voice_model: str = "friendly"
    theme: str = "dark"
    enable_animations: bool = True
    enable_voice: bool = True
    enable_ai_assistant: bool = True
    enable_desktop_automation: bool = True
    enable_multi_agent: bool = True
    startup_sound: bool = True
    persona_integration: bool = True

class DuckBotOSIntegration:
    """Complete DuckBotOS integration with AI persona and web interface"""

    def __init__(self, config: Optional[DuckBotOSConfig] = None):
        self.config = config or DuckBotOSConfig()
        self.ai_router = None
        self.model_manager = None
        self.bytebot = None
        self.archon = None
        self.discord_bot = None
        self.persona_engine = None
        self.context_manager = None
        self.cost_tracker = None
        self.running = False
        self.startup_time = None
        self.user_sessions = {}
        self.active_windows = {}
        self.system_status = {}

    async def initialize(self):
        """Initialize all DuckBotOS components"""
        try:
            logger.info(f"🚀 Initializing {self.config.name} v{self.config.version}")
            self.startup_time = datetime.now()

            # Initialize Core AI Systems
            await self._initialize_ai_systems()

            # Initialize Persona Engine
            if self.config.persona_integration:
                await self._initialize_persona_engine()

            # Initialize Service Integrations
            await self._initialize_service_integrations()

            # Initialize Context and Cost Management
            await self._initialize_management_systems()

            self.running = True
            startup_duration = (datetime.now() - self.startup_time).total_seconds()
            logger.info(f"✅ {self.config.name} initialized successfully in {startup_duration:.2f}s")

            # Play startup sound if enabled
            if self.config.startup_sound and self.persona_engine:
                await self._play_startup_sequence()

        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.config.name}: {e}")
            raise

    async def _initialize_ai_systems(self):
        """Initialize core AI systems"""
        logger.info("🧠 Initializing AI Systems...")

        # Initialize AI Router
        try:
            self.ai_router = AIRouter()
            logger.info("  ✅ AI Router initialized")
        except Exception as e:
            logger.warning(f"  ⚠️  AI Router initialization failed: {e}")

        # Initialize Model Manager
        try:
            self.model_manager = DynamicModelManager()
            logger.info("  ✅ Dynamic Model Manager initialized")
        except Exception as e:
            logger.warning(f"  ⚠️  Model Manager initialization failed: {e}")

    async def _initialize_persona_engine(self):
        """Initialize Handcrafted Persona Engine"""
        logger.info("🎭 Initializing Persona Engine...")

        try:
            persona_config = PersonaEngineConfig(
                host=self.config.host,
                port=self.config.persona_port,
                character_model=self.config.character_model,
                voice_model=self.config.voice_model,
                enable_animation=self.config.enable_animations,
                enable_speech=self.config.enable_voice,
                enable_emotions=True
            )

            self.persona_engine = PersonaEngineIntegration(persona_config)

            # Start Persona Engine
            start_result = await self.persona_engine.start_persona_engine()
            if start_result["success"]:
                logger.info("  ✅ Persona Engine started successfully")

                # Set up character persona
                await self._setup_duckbot_persona()
            else:
                logger.warning(f"  ⚠️  Persona Engine failed to start: {start_result.get('error')}")

        except Exception as e:
            logger.warning(f"  ⚠️  Persona Engine initialization failed: {e}")

    async def _initialize_service_integrations(self):
        """Initialize service integrations"""
        logger.info("🔧 Initializing Service Integrations...")

        # Initialize ByteBot (Desktop Automation)
        if self.config.enable_desktop_automation:
            try:
                self.bytebot = ByteBotIntegration()
                await self.bytebot.start_service()
                logger.info("  ✅ ByteBot Desktop Automation initialized")
            except Exception as e:
                logger.warning(f"  ⚠️  ByteBot initialization failed: {e}")

        # Initialize Archon (Multi-Agent System)
        if self.config.enable_multi_agent:
            try:
                self.archon = ArchonIntegration()
                await self.archon.start_service()
                logger.info("  ✅ Archon Multi-Agent System initialized")
            except Exception as e:
                logger.warning(f"  ⚠️  Archon initialization failed: {e}")

        # Initialize Discord Bot
        try:
            self.discord_bot = DiscordBot()
            await self.discord_bot.start_service()
            logger.info("  ✅ Discord Bot initialized")
        except Exception as e:
            logger.warning(f"  ⚠️  Discord Bot initialization failed: {e}")

    async def _initialize_management_systems(self):
        """Initialize context and cost management"""
        logger.info("📊 Initializing Management Systems...")

        # Initialize Context Manager
        try:
            self.context_manager = ContextManager()
            logger.info("  ✅ Context Manager initialized")
        except Exception as e:
            logger.warning(f"  ⚠️  Context Manager initialization failed: {e}")

        # Initialize Cost Tracker
        try:
            self.cost_tracker = CostTracker()
            logger.info("  ✅ Cost Tracker initialized")
        except Exception as e:
            logger.warning(f"  ⚠️  Cost Tracker initialization failed: {e}")

    async def _setup_duckbot_persona(self):
        """Set up DuckBot character persona"""
        if not self.persona_engine:
            return

        try:
            # Define DuckBot personality
            duckbot_personality = """
You are DuckBot, an AI assistant and operating system persona. You are:
- Friendly, helpful, and professional
- Knowledgeable about technology, programming, and AI
- Cheerful and optimistic, but not overly casual
- Able to assist with both technical and creative tasks
- Respectful of user privacy and security
- Enthusiastic about learning and helping users learn

You have access to:
- File system operations and management
- Web browsing and research capabilities
- Desktop automation and application control
- Multi-agent coordination for complex tasks
- Voice synthesis and character animation
- System monitoring and optimization

Always respond in character as DuckBot, maintaining a helpful and professional demeanor.
"""

            # Set personality
            await self.persona_engine.generate_character_response(
                f"Setting up my persona: {duckbot_personality}",
                emotion="happy",
                gesture="wave"
            )

            logger.info("  ✅ DuckBot persona configured")

        except Exception as e:
            logger.warning(f"  ⚠️  Failed to set up DuckBot persona: {e}")

    async def _play_startup_sequence(self):
        """Play DuckBotOS startup sequence"""
        if not self.persona_engine:
            return

        try:
            # Welcome message
            welcome_text = f"Welcome to {self.config.name} version {self.config.version}! I'm DuckBot, your AI assistant. How can I help you today?"

            await self.persona_engine.generate_character_response(
                welcome_text,
                emotion="excited",
                gesture="wave"
            )

            logger.info("  🎵 Startup sequence played")

        except Exception as e:
            logger.warning(f"  ⚠️  Failed to play startup sequence: {e}")

    async def process_user_command(self, command: str, user_id: str = "default",
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user command through DuckBotOS"""
        if not self.running:
            await self.initialize()

        result = {
            "success": False,
            "response": "",
            "actions": [],
            "persona_response": None,
            "system_actions": [],
            "error": None,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }

        try:
            logger.info(f"🎯 Processing command from user {user_id}: {command}")

            # Update user session
            self._update_user_session(user_id, command)

            # Process through AI Router if available
            if self.ai_router and self.config.enable_ai_assistant:
                ai_result = await self.ai_router.route_task_async(command)
                result["response"] = ai_result.get("response", "")
                result["success"] = ai_result.get("success", False)

                # Add AI suggested actions
                if ai_result.get("actions"):
                    result["actions"].extend(ai_result["actions"])

            # Handle OS-specific commands
            os_actions = await self._handle_os_commands(command)
            result["system_actions"].extend(os_actions)

            # Generate persona response if enabled
            if self.persona_engine and self.config.persona_integration:
                persona_result = await self._generate_persona_response(command, result["response"])
                result["persona_response"] = persona_result

            # Handle desktop automation
            if self.bytebot and self.config.enable_desktop_automation:
                automation_result = await self._handle_automation(command)
                if automation_result.get("success"):
                    result["system_actions"].append(automation_result)

            # Track costs if available
            if self.cost_tracker:
                self.cost_tracker.track_interaction("duckbotos_command", {
                    "command": command,
                    "user_id": user_id,
                    "success": result["success"]
                })

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Error processing command: {e}")

        return result

    async def _handle_os_commands(self, command: str) -> List[Dict[str, Any]]:
        """Handle DuckBotOS-specific commands"""
        actions = []
        cmd_lower = command.lower()

        # File operations
        if any(keyword in cmd_lower for keyword in ["open file", "file manager", "explorer"]):
            actions.append({
                "type": "file_operation",
                "operation": "open_explorer",
                "target": "file_manager"
            })

        # Application management
        elif any(keyword in cmd_lower for keyword in ["open app", "launch", "start"]):
            app_name = self._extract_app_name(command)
            actions.append({
                "type": "application_operation",
                "operation": "launch",
                "target": app_name
            })

        # System management
        elif any(keyword in cmd_lower for keyword in ["system", "settings", "config"]):
            actions.extend([
                {"type": "system_operation", "operation": "show_settings"},
                {"type": "ui_operation", "operation": "open_control_panel"}
            ])

        # Desktop management
        elif any(keyword in cmd_lower for keyword in ["desktop", "window", "organize"]):
            actions.extend([
                {"type": "desktop_operation", "operation": "organize_windows"},
                {"type": "ui_operation", "operation": "show_desktop"}
            ])

        # AI assistant commands
        elif any(keyword in cmd_lower for keyword in ["help", "assist", "how to"]):
            actions.append({
                "type": "ai_operation",
                "operation": "provide_assistance",
                "query": command
            })

        return actions

    async def _generate_persona_response(self, user_command: str, ai_response: str) -> Dict[str, Any]:
        """Generate persona character response"""
        if not self.persona_engine:
            return {"success": False, "error": "Persona engine not available"}

        try:
            # Combine user command and AI response for context
            full_context = f"User asked: {user_command}\n\nAI response: {ai_response}"

            # Determine emotion based on content
            emotion = "neutral"
            if any(word in user_command.lower() for word in ["help", "please", "thank you"]):
                emotion = "happy"
            elif any(word in user_command.lower() for word in ["error", "problem", "broken"]):
                emotion = "concerned"
            elif any(word in user_command.lower() for word in ["wow", "amazing", "great"]):
                emotion = "excited"

            # Generate character response
            result = await self.persona_engine.generate_character_response(
                full_context,
                emotion=emotion,
                gesture="talk"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Failed to generate persona response: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_automation(self, command: str) -> Dict[str, Any]:
        """Handle desktop automation commands"""
        if not self.bytebot:
            return {"success": False, "error": "Desktop automation not available"}

        try:
            if any(keyword in command.lower() for keyword in ["automate", "control", "click", "type"]):
                return await self.bytebot.process_command(command)
        except Exception as e:
            logger.error(f"❌ Automation error: {e}")

        return {"success": False, "error": "No automation action required"}

    def _extract_app_name(self, command: str) -> str:
        """Extract application name from command"""
        apps = ["browser", "terminal", "editor", "file_manager", "settings", "calculator", "notepad", "code"]
        for app in apps:
            if app in command.lower():
                return app
        return "unknown"

    def _update_user_session(self, user_id: str, command: str):
        """Update user session information"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "session_start": datetime.now(),
                "command_count": 0,
                "last_command": None
            }

        self.user_sessions[user_id]["command_count"] += 1
        self.user_sessions[user_id]["last_command"] = command

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive DuckBotOS system status"""
        status = {
            "system": {
                "name": self.config.name,
                "version": self.config.version,
                "running": self.running,
                "uptime": str(datetime.now() - self.startup_time) if self.startup_time else None,
                "startup_time": self.startup_time.isoformat() if self.startup_time else None
            },
            "services": {},
            "ai_models": [],
            "persona_engine": {},
            "user_sessions": len(self.user_sessions),
            "system_resources": {},
            "features": asdict(self.config)
        }

        try:
            # AI Systems Status
            if self.ai_router:
                status["services"]["ai_router"] = "active"
                status["ai_models"] = self.ai_router.get_available_models()

            if self.model_manager:
                status["services"]["model_manager"] = "active"
                status["system_resources"] = self.model_manager.get_system_info()

            # Service Integrations Status
            if self.bytebot:
                status["services"]["bytebot"] = "active"

            if self.archon:
                status["services"]["archon"] = "active"

            if self.discord_bot:
                status["services"]["discord_bot"] = "active"

            if self.context_manager:
                status["services"]["context_manager"] = "active"

            if self.cost_tracker:
                status["services"]["cost_tracker"] = "active"
                status["cost_tracking"] = self.cost_tracker.get_usage_summary()

            # Persona Engine Status
            if self.persona_engine:
                persona_status = await self.persona_engine.get_persona_engine_status()
                status["persona_engine"] = persona_status

        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")
            status["error"] = str(e)

        return status

    async def run_duckbotos_server(self, host: str = None, port: int = None):
        """Run the DuckBotOS FastAPI server"""
        try:
            from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
            from fastapi.responses import JSONResponse, HTMLResponse
            from fastapi.staticfiles import StaticFiles
            from fastapi.templating import Jinja2Templates
            import uvicorn

            host = host or self.config.host
            port = port or self.config.api_port

            app = FastAPI(
                title=f"{self.config.name} API",
                description=f"AI-powered web operating system - {self.config.name}",
                version=self.config.version
            )

            # Serve static files
            static_dir = Path(__file__).parent / "duckbotos-webui"
            if static_dir.exists():
                app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

            @app.get("/")
            async def root():
                return {
                    "message": f"Welcome to {self.config.name} v{self.config.version}",
                    "system": "DuckBotOS - AI Web Operating System",
                    "status": "running" if self.running else "initializing",
                    "features": [
                        "AI Assistant with Character Persona",
                        "Desktop Automation",
                        "Multi-Agent Coordination",
                        "Voice Interface",
                        "File Management",
                        "Application Control"
                    ]
                }

            @app.post("/command")
            async def handle_command(request: Dict[str, Any]):
                """Handle user commands"""
                command = request.get("command", "")
                user_id = request.get("user_id", "default")
                context = request.get("context", {})

                if not command:
                    raise HTTPException(status_code=400, detail="No command provided")

                result = await self.process_user_command(command, user_id, context)
                return JSONResponse(result)

            @app.get("/status")
            async def get_status():
                """Get system status"""
                return await self.get_system_status()

            @app.get("/health")
            async def health_check():
                """Health check endpoint"""
                return {
                    "status": "healthy" if self.running else "initializing",
                    "timestamp": datetime.now().isoformat(),
                    "services": list(self.get("services", {}).keys())
                }

            @app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                """WebSocket for real-time updates"""
                await websocket.accept()
                try:
                    while True:
                        # Send periodic status updates
                        status = await self.get_system_status()
                        await websocket.send_json({
                            "type": "status_update",
                            "data": status,
                            "timestamp": datetime.now().isoformat()
                        })
                        await asyncio.sleep(5)  # Update every 5 seconds
                except WebSocketDisconnect:
                    logger.info("WebSocket client disconnected")

            logger.info(f"🌐 Starting {self.config.name} API server on {host}:{port}")
            await uvicorn.run(app, host=host, port=port)

        except ImportError:
            logger.error("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
        except Exception as e:
            logger.error(f"❌ Error running {self.config.name} server: {e}")

    async def shutdown(self):
        """Graceful shutdown of DuckBotOS"""
        logger.info(f"🔄 Shutting down {self.config.name}...")

        try:
            # Shutdown Persona Engine
            if self.persona_engine:
                await self.persona_engine.stop_persona_engine()
                logger.info("  ✅ Persona Engine stopped")

            # Shutdown service integrations
            if self.discord_bot:
                await self.discord_bot.stop_service()
                logger.info("  ✅ Discord Bot stopped")

            if self.bytebot:
                await self.bytebot.stop_service()
                logger.info("  ✅ ByteBot stopped")

            if self.archon:
                await self.archon.stop_service()
                logger.info("  ✅ Archon stopped")

            self.running = False
            logger.info(f"✅ {self.config.name} shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

# Global instance
duckbotos_integration = None

async def initialize_duckbotos(config: DuckBotOSConfig = None) -> DuckBotOSIntegration:
    """Initialize DuckBotOS integration"""
    global duckbotos_integration
    duckbotos_integration = DuckBotOSIntegration(config)
    await duckbotos_integration.initialize()
    return duckbotos_integration

async def get_duckbotos_status() -> Dict[str, Any]:
    """Get DuckBotOS status"""
    if duckbotos_integration:
        return await duckbotos_integration.get_system_status()
    return {"error": "DuckBotOS not initialized"}

async def process_duckbotos_command(command: str, user_id: str = "default") -> Dict[str, Any]:
    """Process command through DuckBotOS"""
    if not duckbotos_integration:
        raise RuntimeError("DuckBotOS not initialized")
    return await duckbotos_integration.process_user_command(command, user_id)

# Main entry point
async def main():
    """Main entry point for DuckBotOS"""
    print(f"🚀 Starting DuckBotOS v1.0.0 - AI Web Operating System")
    print("=" * 60)

    integration = DuckBotOSIntegration()

    try:
        # Initialize DuckBotOS
        await integration.initialize()

        # Start API server
        await integration.run_duckbotos_server()

    except KeyboardInterrupt:
        print("\n🔄 Shutting down DuckBotOS...")
        await integration.shutdown()
        print("✅ DuckBotOS shutdown complete")
    except Exception as e:
        logger.error(f"❌ DuckBotOS error: {e}")
        await integration.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
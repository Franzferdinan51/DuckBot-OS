#!/usr/bin/env python3
"""
DuckBot Unified WebUI Management System
Combines webui.py, enhanced_webui.py, webui_enhanced.py, and web_dashboard.py into one comprehensive module
"""

import os
import asyncio
import time
import json
import re
import sys
import logging
import threading
import secrets
import tempfile
import uuid
import base64
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, is_dataclass, field

# FastAPI and related imports
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# Flask for cost dashboard
from flask import Flask, render_template, jsonify, request
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
APP_TITLE = "DuckBot Unified WebUI Manager"
VERSION = "4.2"
MAX_CHAT_HISTORY = 100

# Improve Windows console Unicode handling
if os.name == 'nt':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Try to import optional integrations
try:
    from .service_detector import ServiceDetector
    SERVICE_DETECTOR_AVAILABLE = True
except ImportError:
    SERVICE_DETECTOR_AVAILABLE = False
    logger.warning("ServiceDetector not available")

try:
    from .ai_router_gpt import route_task, get_router_state, clear_cache, reset_breakers
    AI_ROUTER_AVAILABLE = True
except ImportError:
    AI_ROUTER_AVAILABLE = False
    logger.warning("AI Router not available")
    # Fallback functions
    def route_task(*args, **kwargs):
        return {"ok": True, "note": "ai-router unavailable"}
    def get_router_state():
        return {}
    def clear_cache():
        return True
    def reset_breakers():
        return True

try:
    from .cost_management import CostTracker, CostVisualizer
    COST_MANAGEMENT_AVAILABLE = True
except ImportError:
    COST_MANAGEMENT_AVAILABLE = False
    logger.warning("Cost management not available")

try:
    from .server_manager import server_manager
    SERVER_MANAGER_AVAILABLE = True
except ImportError:
    SERVER_MANAGER_AVAILABLE = False
    logger.warning("Server manager not available")

try:
    from ..integrations.mining_manager import MiningManager, MiningSoftware
    MINING_MANAGER_AVAILABLE = True
except ImportError:
    MINING_MANAGER_AVAILABLE = False
    logger.warning("Mining manager not available")
    MiningManager = None
    MiningSoftware = None

try:
    from ..integrations.browser_use_integration import (
        BrowserUseIntegration, 
        initialize_browser_use, 
        is_browser_use_available,
        get_browser_use_status
    )
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger.warning("Browser-Use integration not available")
    BrowserUseIntegration = None
    initialize_browser_use = None
    is_browser_use_available = lambda: False
    get_browser_use_status = lambda: {}

try:
    from ..integrations.web_ui_integration import (
        WebUIIntegration,
        initialize_webui,
        is_webui_available,
        get_webui_integration_status
    )
    WEB_UI_AVAILABLE = True
except ImportError:
    WEB_UI_AVAILABLE = False
    logger.warning("Web-UI integration not available")
    WebUIIntegration = None
    initialize_webui = None
    is_webui_available = lambda: False
    get_webui_integration_status = lambda: {}

try:
    from ..integrations.persona_engine_integration import (
        PersonaEngineIntegration,
        initialize_persona_engine,
        is_persona_engine_available,
        get_persona_engine_integration_status
    )
    PERSONA_ENGINE_AVAILABLE = True
except ImportError:
    PERSONA_ENGINE_AVAILABLE = False
    logger.warning("Persona Engine integration not available")
    PersonaEngineIntegration = None
    initialize_persona_engine = None
    is_persona_engine_available = lambda: False
    get_persona_engine_integration_status = lambda: {}

try:
    from .observability import router as observability_router
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    logger.warning("Observability not available")

try:
    from .rag import index_stats as rag_index_stats, ingest_paths as rag_ingest_paths, clear_index as rag_clear_index
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG not available")

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ChatMessage:
    """Chat message data structure"""
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    model: Optional[str] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None

@dataclass
class SystemStatus:
    """System status information"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime: str
    active_connections: int
    total_requests: int
    services_running: int

@dataclass
class WebUIConfig:
    """WebUI configuration"""
    host: str = "127.0.0.1"
    port: int = 8787
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    static_dir: str = "static"
    templates_dir: str = "templates"
    enable_websocket: bool = True
    enable_cost_dashboard: bool = True
    session_secret: str = field(default_factory=lambda: secrets.token_urlsafe(32))

# ============================================================================
# Core FastAPI WebUI
# ============================================================================

class DuckBotWebUI:
    """Main FastAPI-based web interface"""

    def __init__(self, config: WebUIConfig = None):
        self.config = config or WebUIConfig()
        self.app = self._create_app()
        self.chat_history: List[ChatMessage] = []
        self.websocket_connections: List[WebSocket] = []
        self.system_stats_thread: Optional[threading.Thread] = None
        self.system_stats_running = False
        self.cost_tracker = None
        self.cost_visualizer = None
        self.flask_app = None

        # Initialize components
        self._initialize_components()

    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title=APP_TITLE,
            version=VERSION,
            description="DuckBot Unified Web Interface"
        )

        # Add middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        app.add_middleware(
            SessionMiddleware,
            secret_key=self.config.session_secret
        )

        # Add routes
        self._add_routes(app)

        # Add event handlers
        @app.on_event("startup")
        async def startup_event():
            await self._on_startup()

        @app.on_event("shutdown")
        async def shutdown_event():
            await self._on_shutdown()

        return app

    def _add_routes(self, app: FastAPI):
        """Add all routes to the FastAPI app"""

        @app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Main dashboard page"""
            return templates.TemplateResponse("dashboard.html", {"request": request})

        @app.get("/mining", response_class=HTMLResponse)
        async def mining_dashboard(request: Request):
            """Mining dashboard page"""
            return templates.TemplateResponse("mining_dashboard.html", {"request": request})

        @app.get("/settings", response_class=HTMLResponse)
        async def chat_page(request: Request):
            """Chat interface page"""
            return await self._render_chat_page(request)

        @app.get("/cost", response_class=HTMLResponse)
        async def cost_dashboard_page(request: Request):
            """Cost dashboard page"""
            return await self._render_cost_dashboard(request)

        @app.get("/integrations", response_class=HTMLResponse)
        async def integrations_page(request: Request):
            """Integrations management page"""
            return await self._render_integrations_page(request)

        @app.get("/api/status")
        async def get_system_status():
            """Get current system status"""
            return await self._get_system_status()

        @app.get("/api/chat/history")
        async def get_chat_history():
            """Get chat history"""
            return {
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "model": msg.model,
                        "tokens": msg.tokens,
                        "cost": msg.cost
                    }
                    for msg in self.chat_history[-MAX_CHAT_HISTORY:]
                ]
            }

        @app.post("/api/chat")
        async def send_message(request: Request):
            """Send a chat message"""
            data = await request.json()
            message = data.get("message", "")
            model = data.get("model", "default")

            if not message:
                raise HTTPException(status_code=400, detail="Message is required")

            # Add user message to history
            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                role="user",
                content=message,
                timestamp=datetime.now(),
                model=model
            )
            self.chat_history.append(user_msg)

            # Get AI response
            try:
                if AI_ROUTER_AVAILABLE:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: route_task(message, model=model)
                    )
                else:
                    response = {"response": f"I received: {message}", "model": "fallback"}

                # Add assistant message to history
                assistant_msg = ChatMessage(
                    id=str(uuid.uuid4()),
                    role="assistant",
                    content=response.get("response", "No response"),
                    timestamp=datetime.now(),
                    model=response.get("model", model),
                    tokens=response.get("tokens_used"),
                    cost=response.get("cost")
                )
                self.chat_history.append(assistant_msg)

                return {
                    "success": True,
                    "response": response.get("response"),
                    "model": response.get("model", model),
                    "tokens": response.get("tokens_used"),
                    "cost": response.get("cost")
                }

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                return {"success": False, "error": str(e)}

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle WebSocket messages
                    await self._handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)

        @app.get("/api/cost/summary")
        async def get_cost_summary(days: int = Query(30, ge=1, le=365)):
            """Get cost summary"""
            if not COST_MANAGEMENT_AVAILABLE or not self.cost_tracker:
                return {"error": "Cost management not available"}

            try:
                summary = self.cost_tracker.get_usage_summary(days)
                predictions = self.cost_tracker.get_cost_predictions()

                return {
                    "success": True,
                    "data": {
                        "total_cost": summary.total_cost,
                        "total_tokens": summary.total_tokens,
                        "total_requests": summary.total_requests,
                        "by_model": dict(summary.by_model),
                        "by_provider": dict(summary.by_provider),
                        "predictions": predictions,
                        "period_days": days
                    }
                }
            except Exception as e:
                logger.error(f"Error getting cost summary: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/cost/chart")
        async def get_cost_chart(days: int = Query(30, ge=1, le=365)):
            """Generate cost chart"""
            if not COST_MANAGEMENT_AVAILABLE or not self.cost_visualizer:
                return {"error": "Cost visualization not available"}

            try:
                # Generate chart
                chart_path = self.cost_visualizer.create_cost_dashboard(days)

                if not chart_path or not os.path.exists(chart_path):
                    return {"error": "No cost data available"}

                # Read and encode image
                with open(chart_path, 'rb') as f:
                    image_data = f.read()
                    encoded = base64.b64encode(image_data).decode()

                return {
                    "success": True,
                    "image": encoded,
                    "format": "png"
                }

            except Exception as e:
                logger.error(f"Error generating cost chart: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/integrations/status")
        async def get_integrations_status():
            """Get status of all integrations"""
            status = {
                "ai_router": AI_ROUTER_AVAILABLE,
                "cost_management": COST_MANAGEMENT_AVAILABLE,
                "server_manager": SERVER_MANAGER_AVAILABLE,
                "observability": OBSERVABILITY_AVAILABLE,
                "rag": RAG_AVAILABLE,
                "service_detector": SERVICE_DETECTOR_AVAILABLE,
                "mining": MINING_MANAGER_AVAILABLE,
                "browser_use": BROWSER_USE_AVAILABLE,
                "web_ui": WEB_UI_AVAILABLE,
                "persona_engine": PERSONA_ENGINE_AVAILABLE
            }

            if SERVICE_DETECTOR_AVAILABLE:
                detector = ServiceDetector()
                detected_services = detector.detect_all_services()
                status["services"] = detected_services

            # Add detailed status for each integration if available
            if BROWSER_USE_AVAILABLE and self.browser_use_integration:
                try:
                    status["browser_use_details"] = self.browser_use_integration.get_status()
                except Exception as e:
                    logger.error(f"Error getting Browser-Use status: {e}")

            if WEB_UI_AVAILABLE and self.webui_integration:
                try:
                    status["web_ui_details"] = self.webui_integration.get_status()
                except Exception as e:
                    logger.error(f"Error getting Web-UI status: {e}")

            if PERSONA_ENGINE_AVAILABLE and self.persona_engine_integration:
                try:
                    status["persona_engine_details"] = self.persona_engine_integration.get_status()
                except Exception as e:
                    logger.error(f"Error getting Persona Engine status: {e}")

            return status

        @app.post("/api/mining/start")
        async def start_mining():
            """Start cryptocurrency mining"""
            if not MINING_MANAGER_AVAILABLE or not self.mining_manager:
                return {"success": False, "error": "Mining manager not available"}

            try:
                # Get mining configuration from settings
                # For now, use default settings
                success = await self.mining_manager.start_mining()
                return {"success": success, "error": None if success else "Failed to start mining"}
            except Exception as e:
                logger.error(f"Error starting mining: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/mining/stop")
        async def stop_mining():
            """Stop cryptocurrency mining"""
            if not MINING_MANAGER_AVAILABLE or not self.mining_manager:
                return {"success": False, "error": "Mining manager not available"}

            try:
                success = await self.mining_manager.stop_mining()
                return {"success": success, "error": None if success else "Failed to stop mining"}
            except Exception as e:
                logger.error(f"Error stopping mining: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/mining/status")
        async def get_mining_status():
            """Get cryptocurrency mining status"""
            if not MINING_MANAGER_AVAILABLE or not self.mining_manager:
                return {"success": False, "error": "Mining manager not available"}

            try:
                status = await self.mining_manager.get_mining_status()
                return {"success": True, "data": status}
            except Exception as e:
                logger.error(f"Error getting mining status: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/mining/optimize")
        async def optimize_mining():
            """Optimize cryptocurrency mining settings"""
            if not MINING_MANAGER_AVAILABLE or not self.mining_manager:
                return {"success": False, "error": "Mining manager not available"}

            try:
                recommendations = await self.mining_manager.optimize_mining()
                return {"success": True, "data": recommendations}
            except Exception as e:
                logger.error(f"Error optimizing mining: {e}")
                return {"success": False, "error": str(e)}

        # Browser-Use Integration API endpoints
        @app.post("/api/browser-use/navigate")
        async def navigate_to_url(request: dict):
            """Navigate to a specific URL using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                url = request.get("url")
                if not url:
                    return {"success": False, "error": "URL is required"}

                result = await self.browser_use_integration.navigate_to_url(url)
                return result
            except Exception as e:
                logger.error(f"Error navigating to URL: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/search")
        async def search_web(request: dict):
            """Search the web using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                query = request.get("query")
                search_engine = request.get("search_engine", "google")
                
                if not query:
                    return {"success": False, "error": "Query is required"}

                result = await self.browser_use_integration.search_web(query, search_engine)
                return result
            except Exception as e:
                logger.error(f"Error searching web: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/extract-text")
        async def extract_text_content(request: dict):
            """Extract text content from current page using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                selector = request.get("selector")
                
                result = await self.browser_use_integration.extract_text_content(selector)
                return result
            except Exception as e:
                logger.error(f"Error extracting text content: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/screenshot")
        async def take_screenshot(request: dict):
            """Take screenshot of current page using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                filename = request.get("filename")
                
                result = await self.browser_use_integration.take_screenshot(filename)
                return result
            except Exception as e:
                logger.error(f"Error taking screenshot: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/click")
        async def click_element(request: dict):
            """Click element using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                selector = request.get("selector")
                if not selector:
                    return {"success": False, "error": "Selector is required"}

                result = await self.browser_use_integration.click_element(selector)
                return result
            except Exception as e:
                logger.error(f"Error clicking element: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/type")
        async def type_text(request: dict):
            """Type text into element using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                selector = request.get("selector")
                text = request.get("text")
                
                if not selector or not text:
                    return {"success": False, "error": "Selector and text are required"}

                result = await self.browser_use_integration.type_text(selector, text)
                return result
            except Exception as e:
                logger.error(f"Error typing text: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/agent-task")
        async def execute_agent_task(request: dict):
            """Execute task using Browser-Use agent"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                task = request.get("task")
                if not task:
                    return {"success": False, "error": "Task is required"}

                result = await self.browser_use_integration.execute_agent_task(task)
                return result
            except Exception as e:
                logger.error(f"Error executing agent task: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/browser-use/close")
        async def close_browser():
            """Close browser using Browser-Use"""
            if not BROWSER_USE_AVAILABLE or not self.browser_use_integration:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                result = await self.browser_use_integration.close_browser()
                return result
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/browser-use/status")
        async def get_browser_use_status():
            """Get Browser-Use integration status"""
            if not BROWSER_USE_AVAILABLE:
                return {"success": False, "error": "Browser-Use integration not available"}

            try:
                status = self.browser_use_integration.get_status()
                return {"success": True, "data": status}
            except Exception as e:
                logger.error(f"Error getting Browser-Use status: {e}")
                return {"success": False, "error": str(e)}

        # Web-UI Integration API endpoints
        @app.post("/api/webui/start")
        async def start_webui():
            """Start Web-UI server"""
            if not WEB_UI_AVAILABLE or not self.webui_integration:
                return {"success": False, "error": "Web-UI integration not available"}

            try:
                result = await self.webui_integration.start_webui()
                return result
            except Exception as e:
                logger.error(f"Error starting Web-UI: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/webui/stop")
        async def stop_webui():
            """Stop Web-UI server"""
            if not WEB_UI_AVAILABLE or not self.webui_integration:
                return {"success": False, "error": "Web-UI integration not available"}

            try:
                result = await self.webui_integration.stop_webui()
                return result
            except Exception as e:
                logger.error(f"Error stopping Web-UI: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/webui/status")
        async def get_webui_status():
            """Get Web-UI server status"""
            if not WEB_UI_AVAILABLE or not self.webui_integration:
                return {"success": False, "error": "Web-UI integration not available"}

            try:
                result = await self.webui_integration.get_webui_status()
                return result
            except Exception as e:
                logger.error(f"Error getting Web-UI status: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/webui/task")
        async def execute_webui_task(request: dict):
            """Execute task via Web-UI"""
            if not WEB_UI_AVAILABLE or not self.webui_integration:
                return {"success": False, "error": "Web-UI integration not available"}

            try:
                task = request.get("task")
                parameters = request.get("parameters", {})
                
                if not task:
                    return {"success": False, "error": "Task is required"}

                result = await self.webui_integration.execute_webui_task(task, parameters)
                return result
            except Exception as e:
                logger.error(f"Error executing Web-UI task: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/webui/interface")
        async def get_webui_interface():
            """Get Web-UI interface information"""
            if not WEB_UI_AVAILABLE or not self.webui_integration:
                return {"success": False, "error": "Web-UI integration not available"}

            try:
                result = await self.webui_integration.get_webui_interface()
                return result
            except Exception as e:
                logger.error(f"Error getting Web-UI interface: {e}")
                return {"success": False, "error": str(e)}

        # Persona Engine Integration API endpoints
        @app.post("/api/persona-engine/start")
        async def start_persona_engine():
            """Start Persona Engine server"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                result = await self.persona_engine_integration.start_persona_engine()
                return result
            except Exception as e:
                logger.error(f"Error starting Persona Engine: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/persona-engine/stop")
        async def stop_persona_engine():
            """Stop Persona Engine server"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                result = await self.persona_engine_integration.stop_persona_engine()
                return result
            except Exception as e:
                logger.error(f"Error stopping Persona Engine: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/persona-engine/status")
        async def get_persona_engine_status():
            """Get Persona Engine server status"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                result = await self.persona_engine_integration.get_persona_engine_status()
                return result
            except Exception as e:
                logger.error(f"Error getting Persona Engine status: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/persona-engine/generate-response")
        async def generate_character_response(request: dict):
            """Generate character response with animation and voice"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                text = request.get("text")
                emotion = request.get("emotion")
                gesture = request.get("gesture")
                
                if not text:
                    return {"success": False, "error": "Text is required"}

                result = await self.persona_engine_integration.generate_character_response(text, emotion, gesture)
                return result
            except Exception as e:
                logger.error(f"Error generating character response: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/persona-engine/animate")
        async def animate_character(request: dict):
            """Animate character with specific animation"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                animation = request.get("animation")
                duration = request.get("duration")
                
                if not animation:
                    return {"success": False, "error": "Animation is required"}

                result = await self.persona_engine_integration.animate_character(animation, duration)
                return result
            except Exception as e:
                logger.error(f"Error animating character: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/persona-engine/speak")
        async def synthesize_speech(request: dict):
            """Synthesize speech for character"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                text = request.get("text")
                voice = request.get("voice")
                speed = request.get("speed")
                
                if not text:
                    return {"success": False, "error": "Text is required"}

                result = await self.persona_engine_integration.synthesize_speech(text, voice, speed)
                return result
            except Exception as e:
                logger.error(f"Error synthesizing speech: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/persona-engine/emote")
        async def express_emotion(request: dict):
            """Express emotion on character"""
            if not PERSONA_ENGINE_AVAILABLE or not self.persona_engine_integration:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                emotion = request.get("emotion")
                intensity = request.get("intensity")
                
                if not emotion:
                    return {"success": False, "error": "Emotion is required"}

                result = await self.persona_engine_integration.express_emotion(emotion, intensity)
                return result
            except Exception as e:
                logger.error(f"Error expressing emotion: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/persona-engine/capabilities")
        async def get_persona_engine_capabilities():
            """Get Persona Engine capabilities"""
            if not PERSONA_ENGINE_AVAILABLE:
                return {"success": False, "error": "Persona Engine integration not available"}

            try:
                status = self.persona_engine_integration.get_status()
                return {"success": True, "data": status}
            except Exception as e:
                logger.error(f"Error getting Persona Engine capabilities: {e}")
                return {"success": False, "error": str(e)}

        @app.post("/api/mining/switch")
        async def switch_miner(request: Request):
            """Switch between different mining software"""
            if not MINING_MANAGER_AVAILABLE or not self.mining_manager:
                return {"success": False, "error": "Mining manager not available"}

            try:
                data = await request.json()
                software = data.get("software", "multipoolminer")
                
                # Convert string to enum
                software_enum = MiningSoftware.MULTIPOOLMINER if software.lower() == "multipoolminer" else MiningSoftware.NPLUSMINER
                
                success = await self.mining_manager.switch_miner(software_enum)
                return {"success": success, "error": None if success else "Failed to switch miner"}
            except Exception as e:
                logger.error(f"Error switching miner: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/mining/profitability")
        async def get_profitability_data():
            """Get current mining profitability data"""
            if not MINING_MANAGER_AVAILABLE or not self.mining_manager:
                return {"success": False, "error": "Mining manager not available"}

            try:
                profitability_data = await self.mining_manager.get_profitability_data()
                return {"success": True, "data": profitability_data}
            except Exception as e:
                logger.error(f"Error getting profitability data: {e}")
                return {"success": False, "error": str(e)}

    def _initialize_components(self):
        """Initialize optional components"""
        # Initialize cost management if available
        if COST_MANAGEMENT_AVAILABLE:
            try:
                self.cost_tracker = CostTracker()
                self.cost_visualizer = CostVisualizer(self.cost_tracker)
                logger.info("[OK] Cost management initialized")
            except Exception as e:
                logger.error(f"[FAIL] Cost management initialization failed: {e}")
                self.cost_tracker = None
                self.cost_visualizer = None

        # Initialize server manager if available
        if SERVER_MANAGER_AVAILABLE:
            try:
                self.server_manager = server_manager
                logger.info("[OK] Server manager initialized")
            except Exception as e:
                logger.error(f"[FAIL] Server manager initialization failed: {e}")
                self.server_manager = None

        # Initialize mining manager if available
        if MINING_MANAGER_AVAILABLE:
            try:
                self.mining_manager = MiningManager(cost_tracker=self.cost_tracker)
                logger.info("[OK] Mining manager initialized")
            except Exception as e:
                logger.error(f"[FAIL] Mining manager initialization failed: {e}")
                self.mining_manager = None

        # Initialize browser-use integration if available
        if BROWSER_USE_AVAILABLE:
            try:
                asyncio.run(initialize_browser_use())
                self.browser_use_integration = BrowserUseIntegration()
                logger.info("[OK] Browser-Use integration initialized")
            except Exception as e:
                logger.error(f"[FAIL] Browser-Use integration initialization failed: {e}")
                self.browser_use_integration = None

        # Initialize web-ui integration if available
        if WEB_UI_AVAILABLE:
            try:
                asyncio.run(initialize_webui())
                self.webui_integration = WebUIIntegration()
                logger.info("[OK] Web-UI integration initialized")
            except Exception as e:
                logger.error(f"[FAIL] Web-UI integration initialization failed: {e}")
                self.webui_integration = None

        # Initialize persona engine integration if available
        if PERSONA_ENGINE_AVAILABLE:
            try:
                asyncio.run(initialize_persona_engine())
                self.persona_engine_integration = PersonaEngineIntegration()
                logger.info("[OK] Persona Engine integration initialized")
            except Exception as e:
                logger.error(f"[FAIL] Persona Engine integration initialization failed: {e}")
                self.persona_engine_integration = None

        # Initialize observability if available
        if OBSERVABILITY_AVAILABLE:
            try:
                logger.info("[OK] Observability initialized")
            except Exception as e:
                logger.error(f"[FAIL] Observability initialization failed: {e}")

        # Initialize RAG if available
        if RAG_AVAILABLE:
            try:
                logger.info("[OK] RAG initialized")
            except Exception as e:
                logger.error(f"[FAIL] RAG initialization failed: {e}")

        # Initialize Flask app for cost dashboard if enabled
        if self.config.enable_cost_dashboard:
            self.flask_app = self._create_flask_app()

    def _create_flask_app(self) -> Flask:
        """Create Flask app for cost dashboard"""
        app = Flask(__name__)
        app.secret_key = self.config.session_secret

        @app.route('/')
        def dashboard():
            """Redirect to cost dashboard"""
            return render_template('cost_dashboard.html')

        @app.route('/cost')
        def cost_dashboard():
            """Cost dashboard page"""
            return render_template('cost_dashboard.html')

        @app.route('/api/cost_summary')
        def api_cost_summary():
            """Get cost summary data"""
            days = request.args.get('days', 30, type=int)

            try:
                if self.cost_tracker:
                    summary = self.cost_tracker.get_usage_summary(days)
                    predictions = self.cost_tracker.get_cost_predictions()

                    return jsonify({
                        'success': True,
                        'data': {
                            'total_cost': summary.total_cost,
                            'total_tokens': summary.total_tokens,
                            'total_requests': summary.total_requests,
                            'by_model': dict(summary.by_model),
                            'by_provider': dict(summary.by_provider),
                            'predictions': predictions,
                            'period_days': days
                        }
                    })
                else:
                    return jsonify({'success': False, 'error': 'Cost tracker not available'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @app.route('/api/cost_chart')
        def api_cost_chart():
            """Generate cost chart"""
            days = request.args.get('days', 30, type=int)

            try:
                if self.cost_visualizer:
                    chart_path = self.cost_visualizer.create_cost_dashboard(days)

                    if chart_path and os.path.exists(chart_path):
                        with open(chart_path, 'rb') as f:
                            image_data = f.read()
                            encoded = base64.b64encode(image_data).decode()

                        return jsonify({
                            'success': True,
                            'image': encoded,
                            'format': 'png'
                        })

                return jsonify({'success': False, 'error': 'Chart generation failed'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        return app

    async def _on_startup(self):
        """Handle application startup"""
        logger.info(f"Starting {APP_TITLE} v{VERSION}")
        self.system_stats_running = True
        self.system_stats_thread = threading.Thread(target=self._system_stats_loop, daemon=True)
        self.system_stats_thread.start()

    async def _on_shutdown(self):
        """Handle application shutdown"""
        logger.info("Shutting down WebUI")
        self.system_stats_running = False
        if self.system_stats_thread:
            self.system_stats_thread.join(timeout=5)

    def _system_stats_loop(self):
        """Background loop for collecting system statistics"""
        while self.system_stats_running:
            try:
                # Collect system stats and broadcast via WebSocket
                stats = self._collect_system_stats()
                asyncio.run(self._broadcast_system_stats(stats))
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error in system stats loop: {e}")
                time.sleep(10)  # Wait longer on error

    def _collect_system_stats(self) -> Dict[str, Any]:
        """Collect system statistics"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            uptime = time.time() - psutil.boot_time()

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "uptime": str(timedelta(seconds=int(uptime))),
                "timestamp": datetime.now().isoformat()
            }
        except ImportError:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "uptime": "N/A",
                "timestamp": datetime.now().isoformat()
            }

    async def _broadcast_system_stats(self, stats: Dict[str, Any]):
        """Broadcast system stats to all WebSocket connections"""
        if self.websocket_connections:
            message = json.dumps({"type": "system_stats", "data": stats})
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(message)
                except:
                    disconnected.append(websocket)

            # Remove disconnected clients
            for websocket in disconnected:
                self.websocket_connections.remove(websocket)

    async def _handle_websocket_message(self, websocket: WebSocket, data: str):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            logger.warning(f"Invalid WebSocket message: {data}")

    async def _render_dashboard(self, request: Request) -> str:
        """Render main dashboard"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 8px; }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 20px; text-decoration: none; color: #0066cc; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🦆 DuckBot Dashboard</h1>
                <div class="nav">
                    <a href="/">Dashboard</a>
                    <a href="/chat">Chat</a>
                    <a href="/cost">Cost Dashboard</a>
                    <a href="/integrations">Integrations</a>
                </div>
                <div class="card">
                    <h2>System Status</h2>
                    <div id="system-status">Loading...</div>
                </div>
                <div class="card">
                    <h2>Quick Actions</h2>
                    <button onclick="location.href='/chat'">Start Chat</button>
                    <button onclick="location.href='/cost'">View Costs</button>
                    <button onclick="location.href='/integrations'">Manage Integrations</button>
                </div>
            </div>
            <script>
                // Connect to WebSocket for real-time updates
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'system_stats') {
                        updateSystemStatus(data.data);
                    }
                };

                function updateSystemStatus(stats) {
                    document.getElementById('system-status').innerHTML = `
                        <p>CPU: ${stats.cpu_percent.toFixed(1)}%</p>
                        <p>Memory: ${stats.memory_percent.toFixed(1)}%</p>
                        <p>Disk: ${stats.disk_percent.toFixed(1)}%</p>
                        <p>Uptime: ${stats.uptime}</p>
                    `;
                }

                // Initial status fetch
                fetch('/api/status').then(response => response.json()).then(data => {
                    updateSystemStatus(data);
                });
            </script>
        </body>
        </html>
        """

    async def _render_chat_page(self, request: Request) -> str:
        """Render chat interface page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot Chat</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chat-container { max-width: 800px; margin: 0 auto; }
                .messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
                .input-container { display: flex; gap: 10px; }
                .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
                .user { background: #e3f2fd; text-align: right; }
                .assistant { background: #f5f5f5; }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <h1>🦆 DuckBot Chat</h1>
                <div class="messages" id="messages"></div>
                <div class="input-container">
                    <input type="text" id="message-input" placeholder="Type your message..." style="flex: 1;">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            <script>
                async function sendMessage() {
                    const input = document.getElementById('message-input');
                    const message = input.value.trim();
                    if (!message) return;

                    input.value = '';

                    // Add user message to UI
                    addMessage('user', message);

                    try {
                        const response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message })
                        });

                        const data = await response.json();
                        if (data.success) {
                            addMessage('assistant', data.response);
                        } else {
                            addMessage('assistant', 'Error: ' + data.error);
                        }
                    } catch (error) {
                        addMessage('assistant', 'Error: ' + error.message);
                    }
                }

                function addMessage(role, content) {
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${role}`;
                    messageDiv.textContent = content;
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                // Load chat history
                fetch('/api/chat/history').then(response => response.json()).then(data => {
                    data.messages.forEach(msg => {
                        addMessage(msg.role, msg.content);
                    });
                });

                // Enter key to send
                document.getElementById('message-input').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
            </script>
        </body>
        </html>
        """

    async def _render_cost_dashboard(self, request: Request) -> str:
        """Render cost dashboard page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot Cost Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💰 Cost Dashboard</h1>
                <div class="card">
                    <h2>Cost Summary</h2>
                    <div id="cost-summary">Loading...</div>
                </div>
                <div class="card">
                    <h2>Cost Chart</h2>
                    <img id="cost-chart" alt="Cost Chart" style="max-width: 100%;">
                </div>
            </div>
            <script>
                async function loadCostData() {
                    try {
                        const response = await fetch('/api/cost/summary');
                        const data = await response.json();

                        if (data.success) {
                            const summary = data.data;
                            document.getElementById('cost-summary').innerHTML = `
                                <p><strong>Total Cost:</strong> $${summary.total_cost.toFixed(4)}</p>
                                <p><strong>Total Tokens:</strong> ${summary.total_tokens.toLocaleString()}</p>
                                <p><strong>Total Requests:</strong> ${summary.total_requests.toLocaleString()}</p>
                                <p><strong>Projected Monthly:</strong> $${summary.predictions.projected_30d.toFixed(4)}</p>
                            `;
                        }

                        // Load chart
                        const chartResponse = await fetch('/api/cost/chart');
                        const chartData = await chartResponse.json();

                        if (chartData.success) {
                            document.getElementById('cost-chart').src =
                                'data:image/png;base64,' + chartData.image;
                        }
                    } catch (error) {
                        console.error('Error loading cost data:', error);
                    }
                }

                loadCostData();
            </script>
        </body>
        </html>
        """

    async def _render_integrations_page(self, request: Request) -> str:
        """Render integrations management page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Integrations Management</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .integration { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .available { background: #d4edda; }
                .unavailable { background: #f8d7da; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔗 Integrations Management</h1>
                <div id="integrations-status">Loading...</div>
            </div>
            <script>
                async function loadIntegrationsStatus() {
                    try {
                        const response = await fetch('/api/integrations/status');
                        const data = await response.json();

                        let html = '';
                        for (const [name, available] of Object.entries(data)) {
                            if (name !== 'services') {
                                html += `
                                    <div class="integration ${available ? 'available' : 'unavailable'}">
                                        <h3>${name}</h3>
                                        <p>Status: ${available ? '✅ Available' : '❌ Unavailable'}</p>
                                    </div>
                                `;
                            }
                        }

                        if (data.services) {
                            html += '<h2>Detected Services</h2>';
                            for (const [service, info] of Object.entries(data.services)) {
                                html += `
                                    <div class="integration ${info.running ? 'available' : 'unavailable'}">
                                        <h3>${service}</h3>
                                        <p>Status: ${info.running ? '✅ Running' : '❌ Not Running'}</p>
                                        <p>Port: ${info.port || 'N/A'}</p>
                                    </div>
                                `;
                            }
                        }

                        document.getElementById('integrations-status').innerHTML = html;
                    } catch (error) {
                        console.error('Error loading integrations:', error);
                    }
                }

                loadIntegrationsStatus();
            </script>
        </body>
        </html>
        """

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "timestamp": datetime.now().isoformat(),
                "webui_version": VERSION,
                "active_websockets": len(self.websocket_connections)
            }
        except ImportError:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "timestamp": datetime.now().isoformat(),
                "webui_version": VERSION,
                "active_websockets": len(self.websocket_connections)
            }

    def run(self, host: str = None, port: int = None):
        """Run the web UI"""
        host = host or self.config.host
        port = port or self.config.port

        logger.info(f"Starting DuckBot WebUI on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

# ============================================================================
# Convenience functions for backward compatibility
# ============================================================================

def create_webui(config: WebUIConfig = None) -> DuckBotWebUI:
    """Create a DuckBot WebUI instance"""
    return DuckBotWebUI(config)

def run_webui(host: str = "127.0.0.1", port: int = 8787):
    """Run the web UI with default settings"""
    webui = DuckBotWebUI()
    webui.run(host, port)

# For backward compatibility with original modules
DuckBotWebUI = DuckBotWebUI
WebUIConfig = WebUIConfig
ChatMessage = ChatMessage
SystemStatus = SystemStatus
#!/usr/bin/env python3
"""
[DUCKBOT] DuckBot v3.1.0 Enhanced Professional WebUI
Next-generation web interface with advanced monitoring, real-time updates, and modern UI/UX
"""

import os
import asyncio
import time
import json
import re
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import threading
import tempfile
import secrets
import psutil
import uuid

# Import DuckBot components
from .service_detector import ServiceDetector
from .settings_gpt import load_settings, save_settings, apply_to_env
from .ai_router_gpt import route_task, get_router_state, clear_cache, reset_breakers, refresh_lm_studio_model
from .observability import router as observability_router
from .rate_limit import rate_limited
from .rag import index_stats as rag_index_stats, ingest_paths as rag_ingest_paths, clear_index as rag_clear_index
from .server_manager import server_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
APP_TITLE = "[DUCKBOT] DuckBot v3.1.0 Enhanced WebUI"
VERSION = "3.1.0"
MAX_CHAT_HISTORY = 100
WEBSOCKET_PING_INTERVAL = 30

# Enhanced Unicode handling for Windows
if os.name == 'nt':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except Exception:
        pass

# Data Models
@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime: str
    active_connections: int
    total_requests: int
    error_count: int

@dataclass
class ServiceStatus:
    """Enhanced service status information"""
    name: str
    display_name: str
    status: str
    port: Optional[int]
    url: Optional[str]
    pid: Optional[int]
    uptime: Optional[str]
    health_score: int  # 0-100
    last_error: Optional[str]
    response_time: Optional[float]

@dataclass
class ChatMessage:
    """Chat message structure"""
    id: str
    timestamp: datetime
    role: str  # user, assistant, system
    content: str
    metadata: Dict[str, Any]

# Global State Management
class WebUIState:
    """Enhanced global state management"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.active_connections = set()
        self.chat_history: List[ChatMessage] = []
        self.system_metrics_cache = {}
        self.cache_expiry = {}
        self._lock = asyncio.Lock()
        
        # Add initial system message
        self.add_chat_message(ChatMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            role="system",
            content="[DUCKBOT] DuckBot Enhanced WebUI v3.1.0 ready! Advanced monitoring, real-time updates, and professional interface active.",
            metadata={"system": True, "version": VERSION}
        ))
    
    def add_chat_message(self, message: ChatMessage):
        """Add message to chat history with limits"""
        self.chat_history.append(message)
        if len(self.chat_history) > MAX_CHAT_HISTORY:
            self.chat_history.pop(0)
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get cached system metrics"""
        cache_key = "system_metrics"
        now = time.time()
        
        if (cache_key in self.cache_expiry and 
            now < self.cache_expiry[cache_key] and 
            cache_key in self.system_metrics_cache):
            return self.system_metrics_cache[cache_key]
        
        # Update metrics
        try:
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(interval=0.1),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                uptime=str(datetime.now() - self.start_time).split('.')[0],
                active_connections=len(self.active_connections),
                total_requests=self.request_count,
                error_count=self.error_count
            )
            
            self.system_metrics_cache[cache_key] = metrics
            self.cache_expiry[cache_key] = now + 5  # Cache for 5 seconds
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(0, 0, 0, "unknown", 0, self.request_count, self.error_count)

# Global state instance
webui_state = WebUIState()

# Connection Manager for WebSockets
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = client_info or {}
        webui_state.active_connections.add(websocket)
        logger.info(f"WebSocket connection established. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        webui_state.active_connections.discard(websocket)
        logger.info(f"WebSocket connection closed. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

# Global connection manager
connection_manager = ConnectionManager()

# Security and Authentication
security = HTTPBearer()
SECRET_KEY = secrets.token_urlsafe(32)

def generate_access_token() -> str:
    """Generate secure access token"""
    return secrets.token_urlsafe(32)

# Generate token for this session
ACCESS_TOKEN = generate_access_token()

async def require_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Require valid token for API access"""
    if credentials.credentials != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

async def require_token_query(token: str = Query(...)):
    """Require valid token via query parameter"""
    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

# Enhanced AI Task Processing
def infer_task_type(message: str) -> str:
    """Enhanced AI task type inference"""
    m = message.lower().strip()
    
    # Priority scoring system
    patterns = {
        "code": [r"code", r"function", r"debug", r"programming", r"python", r"javascript"],
        "json_format": [r"json", r"format", r"structure", r"parse"],
        "summary": [r"summarize", r"summary", r"tldr", r"brief"],
        "reasoning": [r"analyze", r"reason", r"explain", r"why", r"how"],
        "long_form": [r"explain in detail", r"comprehensive", r"thorough"],
        "status": [r"status", r"health", r"check", r"ping"]
    }
    
    scores = {}
    for task_type, pattern_list in patterns.items():
        score = sum(len(re.findall(pattern, m)) for pattern in pattern_list)
        if score > 0:
            scores[task_type] = score
    
    return max(scores.items(), key=lambda x: x[1])[0] if scores else "status"

# Enhanced Service Management
async def get_enhanced_services() -> Dict[str, ServiceStatus]:
    """Get enhanced service status information"""
    try:
        services = {}
        
        # Enhanced service definitions
        service_configs = {
            'webui': {
                'name': 'DuckBot WebUI', 
                'port': 8787, 
                'url': 'http://localhost:8787',
                'health_endpoint': '/api/health'
            },
            'comfyui': {
                'name': 'ComfyUI Image Generator', 
                'port': 8188, 
                'url': 'http://localhost:8188',
                'health_endpoint': '/'
            },
            'lm_studio': {
                'name': 'LM Studio Server', 
                'port': 1234, 
                'url': 'http://localhost:1234',
                'health_endpoint': '/v1/models'
            },
            'jupyter': {
                'name': 'Jupyter Notebook Server', 
                'port': 8889, 
                'url': 'http://localhost:8889',
                'health_endpoint': '/api/status'
            },
            'n8n': {
                'name': 'n8n Workflow Automation', 
                'port': 5678, 
                'url': 'http://localhost:5678',
                'health_endpoint': '/healthz'
            },
            'open_notebook': {
                'name': 'Open Notebook AI Interface', 
                'port': 8502, 
                'url': 'http://localhost:8502',
                'health_endpoint': '/'
            },
            'discord_bot': {
                'name': 'DuckBot Discord Bot', 
                'port': None, 
                'url': None,
                'health_endpoint': None
            }
        }
        
        import requests
        import psutil
        
        for service_id, config in service_configs.items():
            status = ServiceStatus(
                name=service_id,
                display_name=config['name'],
                status='not_running',
                port=config['port'],
                url=config['url'],
                pid=None,
                uptime=None,
                health_score=0,
                last_error=None,
                response_time=None
            )
            
            # Check if port is in use
            if config['port']:
                port_in_use = False
                service_pid = None
                
                for conn in psutil.net_connections():
                    if (hasattr(conn, 'laddr') and conn.laddr and 
                        conn.laddr.port == config['port'] and 
                        conn.status == psutil.CONN_LISTEN):
                        port_in_use = True
                        service_pid = conn.pid
                        break
                
                if port_in_use:
                    status.status = 'running'
                    status.pid = service_pid
                    status.health_score = 50  # Base score for running
                    
                    # Health check with response time
                    if config.get('health_endpoint'):
                        try:
                            start_time = time.time()
                            response = requests.get(
                                f"{config['url']}{config['health_endpoint']}", 
                                timeout=5
                            )
                            response_time = (time.time() - start_time) * 1000  # ms
                            
                            status.response_time = round(response_time, 2)
                            
                            if response.status_code < 400:
                                status.status = 'healthy'
                                status.health_score = min(100, 70 + (30 if response_time < 1000 else 10))
                            else:
                                status.status = 'unhealthy'
                                status.health_score = 30
                                status.last_error = f"HTTP {response.status_code}"
                                
                        except requests.exceptions.RequestException as e:
                            status.status = 'running_unhealthy'
                            status.health_score = 25
                            status.last_error = str(e)[:100]
                    
                    # Get process uptime if PID available
                    if service_pid:
                        try:
                            proc = psutil.Process(service_pid)
                            create_time = datetime.fromtimestamp(proc.create_time())
                            uptime_delta = datetime.now() - create_time
                            status.uptime = str(uptime_delta).split('.')[0]
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            
            # Special handling for Discord bot (no port)
            elif service_id == 'discord_bot':
                # Check for discord bot process
                discord_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if (proc.info['cmdline'] and 
                            any('discord' in str(arg).lower() or 'duckbot' in str(arg).lower() 
                                for arg in proc.info['cmdline'])):
                            discord_processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if discord_processes:
                    status.status = 'healthy'
                    status.health_score = 85
                    status.pid = discord_processes[0].pid
                    try:
                        create_time = datetime.fromtimestamp(discord_processes[0].create_time())
                        uptime_delta = datetime.now() - create_time
                        status.uptime = str(uptime_delta).split('.')[0]
                    except:
                        pass
            
            services[service_id] = status
        
        return services
        
    except Exception as e:
        logger.error(f"Error getting enhanced services: {e}")
        return {}

# Background Tasks
async def background_monitor():
    """Background monitoring and broadcasting"""
    while True:
        try:
            # Get current metrics and services
            metrics = webui_state.get_system_metrics()
            services = await get_enhanced_services()
            
            # Broadcast updates to connected clients
            update_data = {
                "type": "system_update",
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics),
                "services": {k: asdict(v) for k, v in services.items()}
            }
            
            await connection_manager.broadcast(update_data)
            
            # Wait before next update
            await asyncio.sleep(10)  # Update every 10 seconds
            
        except Exception as e:
            logger.error(f"Background monitor error: {e}")
            await asyncio.sleep(30)  # Longer delay on error

# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan management"""
    # Startup
    logger.info("[START] Starting DuckBot Enhanced WebUI v3.1.0...")
    
    # Start background monitoring
    background_task = asyncio.create_task(background_monitor())
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("[STOP] Shutting down DuckBot Enhanced WebUI...")
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

# FastAPI Application Setup
app = FastAPI(
    title=APP_TITLE,
    version=VERSION,
    description="Enhanced professional web interface for DuckBot AI ecosystem management",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=3600  # 1 hour
)

# Static files and templates
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Request middleware for tracking
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Track requests and errors"""
    webui_state.request_count += 1
    start_time = time.time()
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        webui_state.error_count += 1
        logger.error(f"Request error: {e}")
        raise
    finally:
        # Log slow requests
        duration = time.time() - start_time
        if duration > 5:  # 5 seconds
            logger.warning(f"Slow request: {request.url} took {duration:.2f}s")

# API Routes

@app.get("/")
async def root():
    """Redirect to dashboard with token"""
    return RedirectResponse(url=f"/dashboard?token={ACCESS_TOKEN}")

@app.get("/token")
async def get_token():
    """Get access token for API calls"""
    return {"token": ACCESS_TOKEN}

@app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint"""
    metrics = webui_state.get_system_metrics()
    services = await get_enhanced_services()
    
    healthy_services = sum(1 for s in services.values() if s.health_score > 70)
    total_services = len(services)
    
    return {
        "status": "healthy" if healthy_services >= total_services * 0.7 else "degraded",
        "version": VERSION,
        "uptime": metrics.uptime,
        "services": {
            "total": total_services,
            "healthy": healthy_services,
            "unhealthy": total_services - healthy_services
        },
        "system": {
            "cpu": metrics.cpu_percent,
            "memory": metrics.memory_percent,
            "disk": metrics.disk_percent
        },
        "requests": {
            "total": metrics.total_requests,
            "errors": metrics.error_count,
            "active_connections": metrics.active_connections
        }
    }

@app.get("/api/services/enhanced")
async def get_services_enhanced(_auth: bool = Depends(require_token)):
    """Get enhanced service information"""
    services = await get_enhanced_services()
    return {"services": {k: asdict(v) for k, v in services.items()}}

@app.get("/api/metrics")
async def get_metrics(_auth: bool = Depends(require_token)):
    """Get system metrics"""
    metrics = webui_state.get_system_metrics()
    return asdict(metrics)

@app.get("/dashboard")
async def dashboard(request: Request, token: str = Query(...)):
    """Enhanced dashboard with real-time monitoring"""
    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get current state
    metrics = webui_state.get_system_metrics()
    services = await get_enhanced_services()
    router_state = get_router_state()
    
    # Enhanced context
    context = {
        "request": request,
        "token": ACCESS_TOKEN,
        "version": VERSION,
        "metrics": asdict(metrics),
        "services": {k: asdict(v) for k, v in services.items()},
        "router_state": router_state,
        "chat_history": [asdict(msg) for msg in webui_state.chat_history[-20:]],  # Last 20 messages
        "websocket_url": f"ws://localhost:8787/ws?token={ACCESS_TOKEN}"
    }
    
    return templates.TemplateResponse("dashboard_enhanced.html", context)

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time updates"""
    if token != ACCESS_TOKEN:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    await connection_manager.connect(websocket, {"connected_at": datetime.now()})
    
    try:
        # Send initial data
        initial_data = {
            "type": "connection_established",
            "message": "Real-time updates connected",
            "server_time": datetime.now().isoformat()
        }
        await connection_manager.send_personal_message(initial_data, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for message with timeout for ping
                message = await asyncio.wait_for(
                    websocket.receive_json(), 
                    timeout=WEBSOCKET_PING_INTERVAL
                )
                
                # Handle different message types
                if message.get("type") == "ping":
                    await connection_manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.now().isoformat()},
                        websocket
                    )
                elif message.get("type") == "request_update":
                    # Send current state
                    metrics = webui_state.get_system_metrics()
                    services = await get_enhanced_services()
                    
                    update_data = {
                        "type": "system_update",
                        "timestamp": datetime.now().isoformat(),
                        "metrics": asdict(metrics),
                        "services": {k: asdict(v) for k, v in services.items()}
                    }
                    
                    await connection_manager.send_personal_message(update_data, websocket)
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await connection_manager.send_personal_message(
                    {"type": "ping", "timestamp": datetime.now().isoformat()},
                    websocket
                )
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

# Enhanced Chat API
@app.post("/api/chat/enhanced")
async def enhanced_chat(
    request: Request,
    message: str = Form(...),
    task_type: str = Form(default="auto"),
    priority: str = Form(default="medium"),
    context: str = Form(default=""),
    _auth: bool = Depends(require_token)
):
    """Enhanced chat endpoint with better processing"""
    try:
        # Infer task type if auto
        if task_type == "auto":
            task_type = infer_task_type(message)
        
        # Create enhanced task
        task = {
            "prompt": message,
            "kind": task_type,
            "risk": priority.lower() if priority.lower() in ["low", "medium", "high"] else "medium",
            "context": context,
            "user_id": request.client.host,
            "timestamp": datetime.now().isoformat(),
            "session_id": request.session.get("session_id", str(uuid.uuid4()))
        }
        
        # Store user message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            role="user",
            content=message,
            metadata={"task_type": task_type, "priority": priority}
        )
        webui_state.add_chat_message(user_msg)
        
        # Process with AI
        start_time = time.time()
        ai_response = route_task(task, bucket_type="chat")
        response_time = time.time() - start_time
        
        # Store AI response
        ai_msg = ChatMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            role="assistant",
            content=ai_response,
            metadata={
                "task_type": task_type, 
                "priority": priority, 
                "response_time": response_time,
                "model_used": task.get("model", "unknown")
            }
        )
        webui_state.add_chat_message(ai_msg)
        
        # Broadcast update to WebSocket connections
        chat_update = {
            "type": "chat_update",
            "messages": [asdict(user_msg), asdict(ai_msg)]
        }
        await connection_manager.broadcast(chat_update)
        
        return {
            "success": True,
            "response": ai_response,
            "metadata": {
                "task_type": task_type,
                "response_time": round(response_time, 3),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        webui_state.error_count += 1
        logger.error(f"Enhanced chat error: {e}")
        
        error_msg = ChatMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            role="system",
            content=f"[ERROR] Error processing request: {str(e)}",
            metadata={"error": True, "error_type": type(e).__name__}
        )
        webui_state.add_chat_message(error_msg)
        
        return {"success": False, "error": str(e)}

# Service Management APIs
@app.post("/api/services/{service_id}/action/{action}")
async def service_action(
    service_id: str, 
    action: str, 
    _auth: bool = Depends(require_token)
):
    """Enhanced service management actions"""
    try:
        valid_actions = ["start", "stop", "restart", "status"]
        if action not in valid_actions:
            raise HTTPException(400, f"Invalid action. Must be one of: {valid_actions}")
        
        # Use server manager for actions
        if action == "start":
            success, message = server_manager.start_service(service_id)
        elif action == "stop":
            success, message = server_manager.stop_service(service_id)
        elif action == "restart":
            success, message = server_manager.restart_service(service_id)
        elif action == "status":
            status_info = server_manager.get_service_status(service_id)
            return {
                "success": True,
                "service": service_id,
                "status": asdict(status_info) if hasattr(status_info, '__dict__') else str(status_info)
            }
        
        # Broadcast service update
        if success:
            services = await get_enhanced_services()
            update_data = {
                "type": "service_update",
                "service_id": service_id,
                "action": action,
                "status": asdict(services.get(service_id)) if service_id in services else None
            }
            await connection_manager.broadcast(update_data)
        
        return {
            "success": success,
            "message": message,
            "service": service_id,
            "action": action
        }
        
    except Exception as e:
        logger.error(f"Service action error: {e}")
        return {"success": False, "error": str(e)}

# Action & Reasoning Logs (Enhanced)
@app.get("/action-logs")
async def action_logs_page(request: Request, token: str = Query(...)):
    """Serve the Action Logs page; token via query for browser navigation."""
    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return templates.TemplateResponse(
        "action_logs.html",
        {"request": request, "action_logging_available": True},
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.get("/api/action-logs")
async def api_action_logs(
    hours: int = Query(24, ge=1, le=168),
    action_type: str | None = Query(None),
    component: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    _auth: bool = Depends(require_token),
):
    try:
        from .action_reasoning_logger import action_logger as _action_logger
        logs = _action_logger.get_recent_actions(
            hours=hours, action_type=action_type, component=component, limit=limit
        )
        # Ensure timestamps are ISO-formatted for consistent parsing
        for entry in logs:
            ts = entry.get("timestamp")
            if isinstance(ts, str) and "T" not in ts:
                entry["timestamp"] = ts.replace(" ", "T")
        return JSONResponse({
            "ok": True,
            "logs": logs,
            "count": len(logs),
            "filters": {
                "hours": hours,
                "action_type": action_type,
                "component": component,
                "limit": limit,
            },
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Failed to retrieve logs: {e}"})

@app.get("/api/action-logs/summary")
async def api_action_logs_summary(
    hours: int = Query(24, ge=1, le=168), _auth: bool = Depends(require_token)
):
    try:
        from .action_reasoning_logger import action_logger as _action_logger
        summary = _action_logger.get_action_summary(hours=hours)
        return JSONResponse({"ok": True, "summary": summary})
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Failed to generate summary: {e}"})

if __name__ == "__main__":
    import uvicorn
    print(f"[DUCKBOT] Starting DuckBot Enhanced WebUI v{VERSION}")
    print(f"[EMOJI] Access Token: {ACCESS_TOKEN}")
    print(f"[CLOUD] Dashboard: http://localhost:8787/dashboard?token={ACCESS_TOKEN}")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8787,
        log_level="info",
        access_log=True
    )

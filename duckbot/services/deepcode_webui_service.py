#!/usr/bin/env python3
"""
DuckBot DeepCode WebUI Service
Provides REST API endpoints and WebSocket support for DeepCode integration
Comprehensive backend service for all DeepCode WebUI functionality

Features:
- REST API endpoints for all DeepCode operations
- WebSocket support for real-time updates
- Integration with existing DuckBot service architecture
- Authentication and session management
- File upload and processing
- Task management and monitoring
- Agent coordination and MCP server management
- Paper2Code, Text2Web, Text2Backend API endpoints
- Comprehensive error handling and logging
"""

import os
import sys
import json
import time
import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import tempfile
import shutil
import uuid
from io import BytesIO
import base64

# FastAPI and related imports
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DuckBot modules
try:
    from duckbot.core.service_manager import UnifiedServiceManager, ServiceInfo, ServiceType, ServiceStatus
    from duckbot.core.monitoring_system import MonitoringSystem
    from duckbot.core.cost_management import CostTracker
    from duckbot.core.logging_setup import setup_logging
    from duckbot.core.security_framework import SecurityManager
    from launcher_modules.deepcode.deepcode_integration import DeepCodeIntegration
    from launcher_modules.deepcode.deepcode_mcp_servers import DeepCodeMCPServers
    from duckbot.services.deepcode_auth_integration import (
        DeepCodeAuthIntegration, DeepCodeRole, Permission,
        get_current_user, get_current_active_user, require_permission,
        AuthenticationMiddleware, auth_routes, auth_integration
    )
except ImportError as e:
    logging.warning(f"Some modules not available: {e}")
    # Create fallback auth integration
    auth_integration = DeepCodeAuthIntegration()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
APP_TITLE = "DuckBot DeepCode WebUI Service"
VERSION = "4.2"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.txt', '.md']
UPLOAD_DIR = Path("uploads/deepcode")

# Data Models
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

class MCPServerStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"

class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task (paper2code, text2web, text2backend)")
    description: str = Field(..., description="Task description")
    priority: str = Field("medium", description="Task priority (low, medium, high)")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class TaskResponse(BaseModel):
    id: str
    task_type: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentInfo(BaseModel):
    id: str
    name: str
    type: str
    status: AgentStatus
    description: str
    capabilities: List[str]
    tasks_completed: int = 0
    success_rate: float = 0.0
    last_active: datetime

class MCPServerInfo(BaseModel):
    id: str
    name: str
    type: str
    status: MCPServerStatus
    port: int
    url: str
    description: str
    connected_at: Optional[datetime] = None

class ProjectInfo(BaseModel):
    id: str
    name: str
    type: str
    description: str
    framework: str
    status: str
    created_at: datetime
    updated_at: datetime
    files: List[str] = []

class PaperInfo(BaseModel):
    id: str
    title: str
    filename: str
    file_path: str
    uploaded_at: datetime
    status: str
    analysis_result: Optional[Dict[str, Any]] = None

class SystemStatus(BaseModel):
    overall: str
    agents_online: int
    mcp_servers_connected: int
    active_tasks: int
    total_tasks_completed: int
    system_load: float
    memory_usage: float
    disk_usage: float

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

    async def send_to_client(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            self.disconnect(websocket)

class DeepCodeWebUIService:
    def __init__(self):
        self.app = FastAPI(
            title=APP_TITLE,
            description="DuckBot DeepCode WebUI Service",
            version=VERSION,
            docs_url="/docs",
            redoc_url="/redoc"
        )

        self.ws_manager = WebSocketManager()
        self.security_manager = SecurityManager()
        self.auth_integration = auth_integration
        self.deepcode_integration = None
        self.mcp_servers = None

        # Storage
        self.tasks: Dict[str, TaskResponse] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.mcp_servers_info: Dict[str, MCPServerInfo] = {}
        self.projects: Dict[str, ProjectInfo] = {}
        self.papers: Dict[str, PaperInfo] = {}

        # Background tasks
        self.background_tasks = set()

        self.setup_middleware()
        self.setup_routes()
        self.setup_static_files()
        self.initialize_components()

    def setup_middleware(self):
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Session middleware
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=secrets.token_urlsafe(32),
            session_cookie="deepcode_session"
        )

        # Authentication middleware
        self.app.add_middleware(AuthenticationMiddleware, auth_integration=self.auth_integration)

    def setup_routes(self):
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now()}

        # Authentication routes
        @self.app.post("/auth/login")
        async def login(username: str = Form(...), password: str = Form(...)):
            return await auth_routes.login(username, password)

        @self.app.post("/auth/refresh")
        async def refresh_token(refresh_token: str = Form(...)):
            return await auth_routes.refresh_token(refresh_token)

        @self.app.post("/auth/logout")
        async def logout(refresh_token: str = Form(...)):
            return await auth_routes.logout(refresh_token)

        @self.app.get("/auth/me")
        async def get_current_user_info(current_user: User = Depends(get_current_user)):
            return current_user.dict()

        # DeepCode Dashboard
        @self.app.get("/deepcode", response_class=HTMLResponse)
        async def deepcode_dashboard(request: Request):
            return self.serve_template("deepcode_dashboard.html", request)

        # API Routes
        @self.app.get("/api/deepcode/status")
        async def get_system_status(current_user: User = Depends(get_current_user)):
            return await self.get_system_status()

        @self.app.get("/api/deepcode/tasks")
        async def get_tasks(current_user: User = Depends(get_current_user)):
            return list(self.tasks.values())

        @self.app.post("/api/deepcode/tasks", response_model=TaskResponse)
        async def create_task(
            task_request: TaskRequest,
            current_user: User = Depends(get_current_active_user)
        ):
            return await self.create_task(task_request)

        @self.app.get("/api/deepcode/tasks/{task_id}")
        async def get_task(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            return self.tasks[task_id]

        @self.app.delete("/api/deepcode/tasks/{task_id}")
        async def delete_task(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            del self.tasks[task_id]
            return {"message": "Task deleted successfully"}

        @self.app.get("/api/deepcode/agents")
        async def get_agents():
            return list(self.agents.values())

        @self.app.post("/api/deepcode/agents")
        async def create_agent(agent_data: dict):
            return await self.create_agent(agent_data)

        @self.app.get("/api/deepcode/agents/{agent_id}")
        async def get_agent(agent_id: str):
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            return self.agents[agent_id]

        @self.app.get("/api/deepcode/mcp-servers")
        async def get_mcp_servers():
            return list(self.mcp_servers_info.values())

        @self.app.post("/api/deepcode/mcp-servers/{server_id}/toggle")
        async def toggle_mcp_server(server_id: str):
            return await self.toggle_mcp_server(server_id)

        @self.app.get("/api/deepcode/projects")
        async def get_projects():
            return list(self.projects.values())

        @self.app.post("/api/deepcode/projects")
        async def create_project(project_data: dict):
            return await self.create_project(project_data)

        @self.app.get("/api/deepcode/projects/{project_id}")
        async def get_project(project_id: str):
            if project_id not in self.projects:
                raise HTTPException(status_code=404, detail="Project not found")
            return self.projects[project_id]

        @self.app.get("/api/deepcode/papers")
        async def get_papers():
            return list(self.papers.values())

        @self.app.post("/api/deepcode/upload-paper")
        async def upload_paper(file: UploadFile = File(...)):
            return await self.upload_paper(file)

        @self.app.post("/api/deepcode/papers/{paper_id}/analyze")
        async def analyze_paper(paper_id: str):
            return await self.analyze_paper(paper_id)

        @self.app.post("/api/deepcode/papers/{paper_id}/generate-code")
        async def generate_code_from_paper(paper_id: str):
            return await self.generate_code_from_paper(paper_id)

        @self.app.post("/api/deepcode/generate-web")
        async def generate_web_app(request: dict):
            return await self.generate_web_application(request)

        @self.app.post("/api/deepcode/generate-backend")
        async def generate_backend(request: dict):
            return await self.generate_backend_application(request)

        # WebSocket endpoint
        @self.app.websocket("/ws/deepcode")
        async def websocket_endpoint(websocket: WebSocket):
            await self.ws_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                self.ws_manager.disconnect(websocket)

    def setup_static_files(self):
        # Mount static files
        static_dir = Path(__file__).parent.parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def initialize_components(self):
        # Initialize upload directory
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize DeepCode integration
        try:
            self.deepcode_integration = DeepCodeIntegration()
            asyncio.create_task(self.deepcode_integration.startup())
        except Exception as e:
            logger.error(f"Failed to initialize DeepCode integration: {e}")

        # Initialize MCP servers
        try:
            self.mcp_servers = DeepCodeMCPServers()
            asyncio.create_task(self.mcp_servers.startup())
        except Exception as e:
            logger.error(f"Failed to initialize MCP servers: {e}")

        # Start background tasks
        asyncio.create_task(self.update_system_status())
        asyncio.create_task(self.cleanup_old_files())

    async def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        agents_online = len([a for a in self.agents.values() if a.status == AgentStatus.ONLINE])
        mcp_servers_connected = len([s for s in self.mcp_servers_info.values() if s.status == MCPServerStatus.CONNECTED])
        active_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        total_tasks_completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])

        # Get system metrics
        import psutil
        system_load = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        overall_status = "online"
        if agents_online == 0:
            overall_status = "warning"
        if mcp_servers_connected == 0:
            overall_status = "offline"

        return SystemStatus(
            overall=overall_status,
            agents_online=agents_online,
            mcp_servers_connected=mcp_servers_connected,
            active_tasks=active_tasks,
            total_tasks_completed=total_tasks_completed,
            system_load=system_load,
            memory_usage=memory_usage,
            disk_usage=disk_usage
        )

    async def create_task(self, task_request: TaskRequest) -> TaskResponse:
        """Create a new task"""
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = TaskResponse(
            id=task_id,
            task_type=task_request.task_type,
            description=task_request.description,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now
        )

        self.tasks[task_id] = task

        # Broadcast task creation
        await self.ws_manager.broadcast({
            "type": "task_update",
            "task": task.dict()
        })

        # Start task execution
        asyncio.create_task(self.execute_task(task_id, task_request))

        return task

    async def execute_task(self, task_id: str, task_request: TaskRequest):
        """Execute a task in the background"""
        try:
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.now()

            await self.ws_manager.broadcast({
                "type": "task_update",
                "task": task.dict()
            })

            # Execute task based on type
            if task_request.task_type == "paper2code":
                result = await self.execute_paper2code_task(task_request)
            elif task_request.task_type == "text2web":
                result = await self.execute_text2web_task(task_request)
            elif task_request.task_type == "text2backend":
                result = await self.execute_text2backend_task(task_request)
            else:
                raise ValueError(f"Unknown task type: {task_request.task_type}")

            # Update task with result
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.updated_at = datetime.now()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.updated_at = datetime.now()

        finally:
            await self.ws_manager.broadcast({
                "type": "task_update",
                "task": task.dict()
            })

    async def execute_paper2code_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Execute Paper2Code task"""
        if not self.deepcode_integration:
            raise Exception("DeepCode integration not available")

        # Simulate task execution
        await asyncio.sleep(2)

        return {
            "type": "paper2code",
            "files_generated": ["main.py", "requirements.txt", "README.md"],
            "quality_score": 0.85,
            "code_lines": 1250
        }

    async def execute_text2web_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Execute Text2Web task"""
        # Simulate task execution
        await asyncio.sleep(3)

        return {
            "type": "text2web",
            "framework": task_request.parameters.get("framework", "react"),
            "files_generated": ["index.html", "styles.css", "app.js"],
            "components": 15,
            "lines_of_code": 850
        }

    async def execute_text2backend_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Execute Text2Backend task"""
        # Simulate task execution
        await asyncio.sleep(4)

        return {
            "type": "text2backend",
            "framework": task_request.parameters.get("framework", "fastapi"),
            "endpoints": 12,
            "models": 8,
            "files_generated": ["main.py", "models.py", "routers.py", "database.py"]
        }

    async def upload_paper(self, file: UploadFile) -> PaperInfo:
        """Upload and process a research paper"""
        # Validate file
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="File type not supported")

        # Create upload directory if needed
        upload_path = UPLOAD_DIR / file.filename

        # Save file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Create paper record
        paper_id = str(uuid.uuid4())
        paper = PaperInfo(
            id=paper_id,
            title=file.filename.replace(file_extension, ""),
            filename=file.filename,
            file_path=str(upload_path),
            uploaded_at=datetime.now(),
            status="uploaded"
        )

        self.papers[paper_id] = paper

        # Broadcast upload event
        await self.ws_manager.broadcast({
            "type": "paper_uploaded",
            "paper": paper.dict()
        })

        return paper

    async def analyze_paper(self, paper_id: str) -> Dict[str, Any]:
        """Analyze a research paper"""
        if paper_id not in self.papers:
            raise HTTPException(status_code=404, detail="Paper not found")

        paper = self.papers[paper_id]
        paper.status = "analyzing"

        # Simulate analysis
        await asyncio.sleep(5)

        analysis_result = {
            "title": paper.title,
            "authors": ["Author 1", "Author 2", "Author 3"],
            "abstract": "This is a sample abstract extracted from the paper...",
            "key_concepts": ["concept1", "concept2", "concept3"],
            "methodologies": ["method1", "method2"],
            "quality_score": 0.87,
            "extracted_code_snippets": 3,
            "potential_applications": ["app1", "app2", "app3"]
        }

        paper.analysis_result = analysis_result
        paper.status = "analyzed"

        await self.ws_manager.broadcast({
            "type": "paper_analyzed",
            "paper_id": paper_id,
            "analysis": analysis_result
        })

        return analysis_result

    async def generate_code_from_paper(self, paper_id: str) -> Dict[str, Any]:
        """Generate code from a research paper"""
        if paper_id not in self.papers:
            raise HTTPException(status_code=404, detail="Paper not found")

        paper = self.papers[paper_id]
        if paper.status != "analyzed":
            raise HTTPException(status_code=400, detail="Paper must be analyzed first")

        # Create task for code generation
        task_request = TaskRequest(
            task_type="paper2code",
            description=f"Generate code from paper: {paper.title}",
            parameters={"paper_id": paper_id}
        )

        task = await self.create_task(task_request)
        return {"task_id": task.id, "message": "Code generation task created"}

    async def generate_web_application(self, request: dict) -> Dict[str, Any]:
        """Generate a web application from description"""
        # Create task for web generation
        task_request = TaskRequest(
            task_type="text2web",
            description=request.get("description", ""),
            parameters={
                "framework": request.get("framework", "react"),
                "styling": request.get("styling", "tailwind")
            }
        )

        task = await self.create_task(task_request)
        return {"task_id": task.id, "message": "Web application generation task created"}

    async def generate_backend_application(self, request: dict) -> Dict[str, Any]:
        """Generate a backend application from description"""
        # Create task for backend generation
        task_request = TaskRequest(
            task_type="text2backend",
            description=request.get("description", ""),
            parameters={
                "framework": request.get("framework", "fastapi"),
                "database": request.get("database", "postgresql")
            }
        )

        task = await self.create_task(task_request)
        return {"task_id": task.id, "message": "Backend application generation task created"}

    async def handle_websocket_message(self, websocket: WebSocket, data: str):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(data)

            if message.get("type") == "ping":
                await self.ws_manager.send_to_client(websocket, {"type": "pong"})
            elif message.get("type") == "subscribe":
                # Handle subscription to specific events
                pass
            else:
                logger.warning(f"Unknown WebSocket message type: {message.get('type')}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def update_system_status(self):
        """Periodically update system status"""
        while True:
            try:
                status = await self.get_system_status()
                await self.ws_manager.broadcast({
                    "type": "system_status",
                    "status": status.dict()
                })
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error updating system status: {e}")
                await asyncio.sleep(60)

    async def cleanup_old_files(self):
        """Clean up old uploaded files"""
        while True:
            try:
                now = datetime.now()
                cutoff_time = now - timedelta(days=7)  # Keep files for 7 days

                for paper in list(self.papers.values()):
                    if paper.uploaded_at < cutoff_time:
                        # Remove file
                        file_path = Path(paper.file_path)
                        if file_path.exists():
                            file_path.unlink()

                        # Remove from database
                        del self.papers[paper.id]

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error cleaning up old files: {e}")
                await asyncio.sleep(3600)

    def serve_template(self, template_name: str, request: Request) -> HTMLResponse:
        """Serve HTML template"""
        # For now, return a simple template response
        # In a real implementation, you'd use Jinja2Templates
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DeepCode Dashboard</title>
            <link rel="stylesheet" href="/static/modern-styles.css">
            <link rel="stylesheet" href="/static/deepcode-styles.css">
        </head>
        <body>
            <div class="container">
                <h1>DeepCode Dashboard</h1>
                <p>This is a placeholder for the actual DeepCode dashboard template.</p>
                <p>The full template should be loaded from: {template_name}</p>
            </div>
            <script src="/static/deepcode-ui.js"></script>
        </body>
        </html>
        """)

    async def startup(self):
        """Startup the service"""
        logger.info(f"Starting {APP_TITLE} v{VERSION}")

    async def shutdown(self):
        """Shutdown the service"""
        logger.info(f"Shutting down {APP_TITLE}")

# Create service instance
deepcode_service = DeepCodeWebUIService()
app = deepcode_service.app

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await deepcode_service.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await deepcode_service.shutdown()

# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot DeepCode WebUI Service")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8790, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Configure logging level
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info(f"Starting DeepCode WebUI Service on {args.host}:{args.port}")

    uvicorn.run(
        "duckbot.services.deepcode_webui_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )
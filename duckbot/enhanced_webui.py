#!/usr/bin/env python3
"""
Enhanced WebUI for DuckBot with integrated features from ByteBot, Archon, and ChromiumOS
Modern, responsive web interface with real-time updates, multi-agent coordination, and desktop integration
"""

import os
import asyncio
import time
import json
import logging
import threading
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import base64

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """System status information"""
    timestamp: datetime
    wsl_available: bool
    wsl_distros: List[str]
    ai_providers: List[str]
    active_services: List[str]
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_active: bool
    
@dataclass 
class AgentState:
    """Multi-agent state management"""
    agent_id: str
    name: str
    status: str  # active, idle, busy, error
    current_task: Optional[str]
    capabilities: List[str]
    performance_metrics: Dict[str, Any]
    last_activity: datetime

@dataclass
class TaskExecution:
    """Task execution tracking"""
    task_id: str
    description: str
    assigned_agent: str
    status: str  # queued, running, completed, failed
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    progress: float
    logs: List[str]
    artifacts: List[Dict]

class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_data: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_data[client_id] = {
            'connected_at': datetime.now(),
            'subscriptions': set()
        }
        logger.info(f"WebSocket connection established: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_data:
            del self.connection_data[client_id]
        logger.info(f"WebSocket connection closed: {client_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, subscription_type: str = None):
        """Broadcast message to all connected clients or subscribers"""
        disconnect_list = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                # Check subscription filter
                if subscription_type:
                    client_subs = self.connection_data.get(client_id, {}).get('subscriptions', set())
                    if subscription_type not in client_subs:
                        continue
                
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnect_list.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnect_list:
            self.disconnect(client_id)

class EnhancedWebUI:
    """Enhanced WebUI with multi-agent orchestration and desktop integration"""
    
    def __init__(self):
        self.app = FastAPI(title="DuckBot Enhanced WebUI", version="3.1.0+")
        self.connection_manager = ConnectionManager()
        self.system_status = None
        self.agents: Dict[str, AgentState] = {}
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.knowledge_base = {}
        self.security_token = secrets.token_urlsafe(32)
        
        # Initialize integrations
        self.wsl_integration = None
        self.bytebot_integration = None
        self.ai_router = None
        
        self.setup_middleware()
        self.setup_routes()
        self.setup_background_tasks()
    
    def setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure as needed
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup all API routes"""
        
        # Static files and templates
        static_path = Path(__file__).parent / "static"
        templates_path = Path(__file__).parent / "templates"
        
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        if templates_path.exists():
            self.templates = Jinja2Templates(directory=str(templates_path))
        
        # Main routes
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return await self.render_dashboard(request)
        
        @self.app.get("/dashboard", response_class=HTMLResponse) 
        async def dashboard(request: Request):
            return await self.render_dashboard(request)
        
        # API routes
        @self.app.get("/api/status")
        async def api_status():
            return await self.get_system_status()
        
        @self.app.get("/api/agents")
        async def api_agents():
            return {"agents": [asdict(agent) for agent in self.agents.values()]}
        
        @self.app.get("/api/tasks")
        async def api_tasks():
            return {"tasks": [asdict(task) for task in self.active_tasks.values()]}
        
        @self.app.post("/api/tasks/create")
        async def api_create_task(task_data: dict):
            return await self.create_task(task_data)
        
        @self.app.post("/api/agents/{agent_id}/assign")
        async def api_assign_task(agent_id: str, task_data: dict):
            return await self.assign_task_to_agent(agent_id, task_data)
        
        # WSL Integration routes
        @self.app.get("/api/wsl/status")
        async def api_wsl_status():
            return await self.get_wsl_status()
        
        @self.app.post("/api/wsl/execute")
        async def api_wsl_execute(command_data: dict):
            return await self.execute_wsl_command(command_data)
        
        # ByteBot Integration routes
        @self.app.get("/api/desktop/screenshot")
        async def api_screenshot():
            return await self.get_desktop_screenshot()
        
        @self.app.post("/api/desktop/task")
        async def api_desktop_task(task_data: dict):
            return await self.execute_desktop_task(task_data)
        
        # Knowledge Base routes (Archon-inspired)
        @self.app.get("/api/knowledge")
        async def api_knowledge():
            return {"knowledge_base": self.knowledge_base}
        
        @self.app.post("/api/knowledge/ingest")
        async def api_knowledge_ingest(data: dict):
            return await self.ingest_knowledge(data)
        
        @self.app.post("/api/knowledge/search")
        async def api_knowledge_search(query: dict):
            return await self.search_knowledge(query["query"])
        
        # WebSocket endpoint
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self.connection_manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self.handle_websocket_message(client_id, message)
            except WebSocketDisconnect:
                self.connection_manager.disconnect(client_id)
    
    def setup_background_tasks(self):
        """Setup background monitoring tasks"""
        
        async def system_monitor():
            """Background system monitoring"""
            while True:
                try:
                    self.system_status = await self.collect_system_status()
                    
                    # Broadcast system updates
                    await self.connection_manager.broadcast({
                        "type": "system_status",
                        "data": asdict(self.system_status)
                    }, "system_status")
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    logger.error(f"System monitor error: {e}")
                    await asyncio.sleep(10)
        
        async def agent_monitor():
            """Background agent monitoring"""
            while True:
                try:
                    # Update agent states
                    await self.update_agent_states()
                    
                    # Broadcast agent updates
                    await self.connection_manager.broadcast({
                        "type": "agents_update", 
                        "data": [asdict(agent) for agent in self.agents.values()]
                    }, "agents")
                    
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Agent monitor error: {e}")
                    await asyncio.sleep(5)
        
        # Start background tasks
        asyncio.create_task(system_monitor())
        asyncio.create_task(agent_monitor())
    
    async def initialize_integrations(self):
        """Initialize all system integrations"""
        try:
            # WSL Integration
            from .wsl_integration import wsl_integration
            self.wsl_integration = wsl_integration
            await wsl_integration.initialize()
            
            # ByteBot Integration
            from .bytebot_integration import ByteBotIntegration
            self.bytebot_integration = ByteBotIntegration()
            
            # AI Router
            from .ai_router_gpt import route_task
            self.ai_router = route_task
            
            # Initialize default agents
            await self.initialize_default_agents()
            
            logger.info("All integrations initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize integrations: {e}")
    
    async def initialize_default_agents(self):
        """Initialize default AI agents"""
        default_agents = [
            {
                "agent_id": "main_brain",
                "name": "Main Brain",
                "capabilities": ["general", "reasoning", "coordination"],
                "status": "active"
            },
            {
                "agent_id": "code_specialist", 
                "name": "Code Specialist",
                "capabilities": ["coding", "debugging", "review"],
                "status": "idle"
            },
            {
                "agent_id": "system_admin",
                "name": "System Admin",
                "capabilities": ["system", "wsl", "docker", "monitoring"],
                "status": "idle"
            },
            {
                "agent_id": "desktop_controller",
                "name": "Desktop Controller", 
                "capabilities": ["desktop", "automation", "ui_interaction"],
                "status": "idle"
            }
        ]
        
        for agent_data in default_agents:
            agent = AgentState(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                status=agent_data["status"],
                current_task=None,
                capabilities=agent_data["capabilities"],
                performance_metrics={},
                last_activity=datetime.now()
            )
            self.agents[agent.agent_id] = agent
    
    async def render_dashboard(self, request: Request) -> HTMLResponse:
        """Render the main dashboard"""
        
        dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckBot Enhanced WebUI v3.1.0+</title>
    <style>
        :root {
            --primary-color: #00d4aa;
            --secondary-color: #0066cc;
            --accent-color: #ff6b35;
            --bg-dark: #1a1a2e;
            --bg-light: #16213e;
            --text-primary: #ffffff;
            --text-secondary: #a0a9c0;
            --border-color: #2a3441;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            display: grid;
            grid-template-areas: 
                "header header header"
                "sidebar main-content status-panel"
                "sidebar main-content status-panel";
            grid-template-columns: 250px 1fr 300px;
            grid-template-rows: 60px 1fr;
            height: 100vh;
        }
        
        .header {
            grid-area: header;
            background: var(--bg-light);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .header-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: var(--primary-color);
            color: white;
        }
        
        .btn-secondary {
            background: var(--secondary-color);
            color: white;
        }
        
        .btn:hover {
            opacity: 0.8;
            transform: translateY(-1px);
        }
        
        .sidebar {
            grid-area: sidebar;
            background: var(--bg-light);
            border-right: 1px solid var(--border-color);
            padding: 20px;
        }
        
        .nav-menu {
            list-style: none;
        }
        
        .nav-menu li {
            margin-bottom: 10px;
        }
        
        .nav-menu a {
            display: block;
            padding: 10px 15px;
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        
        .nav-menu a:hover,
        .nav-menu a.active {
            background: var(--primary-color);
            color: white;
        }
        
        .main-content {
            grid-area: main-content;
            padding: 20px;
            overflow-y: auto;
        }
        
        .status-panel {
            grid-area: status-panel;
            background: var(--bg-light);
            border-left: 1px solid var(--border-color);
            padding: 20px;
            overflow-y: auto;
        }
        
        .card {
            background: var(--bg-light);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .card-header {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 15px;
            color: var(--primary-color);
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background: #00ff00; }
        .status-offline { background: #ff0000; }
        .status-busy { background: #ffaa00; }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: var(--bg-dark);
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .agent-list {
            list-style: none;
        }
        
        .agent-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .agent-info {
            display: flex;
            flex-direction: column;
        }
        
        .agent-name {
            font-weight: bold;
        }
        
        .agent-task {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .terminal {
            background: #000;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            padding: 15px;
            border-radius: 4px;
            height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        
        .chat-container {
            height: 400px;
            display: flex;
            flex-direction: column;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px 4px 0 0;
        }
        
        .chat-input {
            display: flex;
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 4px 4px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: none;
            background: var(--bg-dark);
            color: var(--text-primary);
        }
        
        .chat-input button {
            padding: 10px 20px;
            border: none;
            background: var(--primary-color);
            color: white;
            cursor: pointer;
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: var(--border-color);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--primary-color);
            transition: width 0.3s ease;
        }
        
        @media (max-width: 1024px) {
            .container {
                grid-template-areas:
                    "header header"
                    "main-content status-panel";
                grid-template-columns: 1fr 300px;
                grid-template-rows: 60px 1fr;
            }
            
            .sidebar {
                display: none;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-areas:
                    "header"
                    "main-content";
                grid-template-columns: 1fr;
            }
            
            .status-panel {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">🦆 DuckBot v3.1.0+ Enhanced WebUI</div>
            <div class="header-actions">
                <button class="btn btn-secondary" onclick="toggleTerminal()">Terminal</button>
                <button class="btn btn-primary" onclick="startChat()">AI Chat</button>
                <button class="btn btn-secondary" onclick="showSettings()">Settings</button>
            </div>
        </header>
        
        <aside class="sidebar">
            <nav>
                <ul class="nav-menu">
                    <li><a href="#dashboard" class="active">🏠 Dashboard</a></li>
                    <li><a href="#agents">🤖 AI Agents</a></li>
                    <li><a href="#tasks">📋 Tasks</a></li>
                    <li><a href="#wsl">🐧 WSL Integration</a></li>
                    <li><a href="#desktop">🖥️ Desktop Control</a></li>
                    <li><a href="#knowledge">📚 Knowledge Base</a></li>
                    <li><a href="#monitoring">📊 Monitoring</a></li>
                    <li><a href="#logs">📝 Logs</a></li>
                </ul>
            </nav>
        </aside>
        
        <main class="main-content">
            <div class="card">
                <div class="card-header">System Overview</div>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="cpu-usage">0%</div>
                        <div class="metric-label">CPU Usage</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="memory-usage">0%</div>
                        <div class="metric-label">Memory</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="active-agents">0</div>
                        <div class="metric-label">Active Agents</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="running-tasks">0</div>
                        <div class="metric-label">Running Tasks</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">AI Chat Interface</div>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-messages">
                        <div style="color: var(--text-secondary);">AI Chat ready. Start a conversation...</div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chat-input" placeholder="Type your message...">
                        <button onclick="sendChatMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">Terminal Output</div>
                <div class="terminal" id="terminal-output">
DuckBot Enhanced WebUI v3.1.0+ Terminal
=====================================
System initialized successfully.
All integrations loaded.
Ready for commands...

$ 
                </div>
            </div>
        </main>
        
        <aside class="status-panel">
            <div class="card">
                <div class="card-header">System Status</div>
                <div>
                    <div><span class="status-indicator status-online"></span>AI Router: Online</div>
                    <div><span class="status-indicator status-online"></span>WSL: <span id="wsl-status">Checking...</span></div>
                    <div><span class="status-indicator status-online"></span>ByteBot: <span id="bytebot-status">Checking...</span></div>
                    <div><span class="status-indicator status-online"></span>WebUI: Online</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">Active Agents</div>
                <ul class="agent-list" id="agent-list">
                    <li class="agent-item">
                        <div class="agent-info">
                            <div class="agent-name">Main Brain</div>
                            <div class="agent-task">Coordinating tasks...</div>
                        </div>
                        <span class="status-indicator status-online"></span>
                    </li>
                </ul>
            </div>
            
            <div class="card">
                <div class="card-header">Recent Tasks</div>
                <div id="recent-tasks">
                    <div style="color: var(--text-secondary);">No recent tasks</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">Quick Actions</div>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <button class="btn btn-primary" onclick="createNewTask()">New Task</button>
                    <button class="btn btn-secondary" onclick="takeScreenshot()">Screenshot</button>
                    <button class="btn btn-secondary" onclick="runSystemCheck()">System Check</button>
                </div>
            </div>
        </aside>
    </div>
    
    <script>
        // WebSocket connection for real-time updates
        const clientId = 'web-ui-' + Math.random().toString(36).substr(2, 9);
        let ws;
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws/${clientId}`);
            
            ws.onopen = function(event) {
                console.log('WebSocket connected');
                // Subscribe to updates
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    subscriptions: ['system_status', 'agents', 'tasks']
                }));
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };
            
            ws.onclose = function(event) {
                console.log('WebSocket closed, reconnecting in 5 seconds...');
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function handleWebSocketMessage(message) {
            switch(message.type) {
                case 'system_status':
                    updateSystemStatus(message.data);
                    break;
                case 'agents_update':
                    updateAgents(message.data);
                    break;
                case 'task_update':
                    updateTasks(message.data);
                    break;
                case 'chat_response':
                    addChatMessage(message.data.content, 'assistant');
                    break;
                case 'terminal_output':
                    addTerminalOutput(message.data.output);
                    break;
            }
        }
        
        function updateSystemStatus(data) {
            document.getElementById('cpu-usage').textContent = data.cpu_usage.toFixed(1) + '%';
            document.getElementById('memory-usage').textContent = data.memory_usage.toFixed(1) + '%';
            document.getElementById('wsl-status').textContent = data.wsl_available ? 'Available' : 'Not Available';
            document.getElementById('bytebot-status').textContent = 'Ready';
        }
        
        function updateAgents(agents) {
            const agentList = document.getElementById('agent-list');
            agentList.innerHTML = '';
            
            document.getElementById('active-agents').textContent = agents.filter(a => a.status === 'active').length;
            
            agents.forEach(agent => {
                const li = document.createElement('li');
                li.className = 'agent-item';
                
                const statusClass = agent.status === 'active' ? 'status-online' : 
                                  agent.status === 'busy' ? 'status-busy' : 'status-offline';
                
                li.innerHTML = `
                    <div class="agent-info">
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-task">${agent.current_task || 'Idle'}</div>
                    </div>
                    <span class="status-indicator ${statusClass}"></span>
                `;
                
                agentList.appendChild(li);
            });
        }
        
        function updateTasks(tasks) {
            const runningTasks = tasks.filter(t => t.status === 'running').length;
            document.getElementById('running-tasks').textContent = runningTasks;
        }
        
        function sendChatMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (message) {
                addChatMessage(message, 'user');
                input.value = '';
                
                // Send to backend
                fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
            }
        }
        
        function addChatMessage(content, role) {
            const messages = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.style.marginBottom = '10px';
            div.style.color = role === 'user' ? 'var(--primary-color)' : 'var(--text-primary)';
            div.innerHTML = `<strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> ${content}`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function addTerminalOutput(output) {
            const terminal = document.getElementById('terminal-output');
            terminal.textContent += output + '\\n';
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        function createNewTask() {
            const description = prompt('Enter task description:');
            if (description) {
                fetch('/api/tasks/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: description })
                });
            }
        }
        
        function takeScreenshot() {
            fetch('/api/desktop/screenshot')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addTerminalOutput('Screenshot taken successfully');
                    }
                });
        }
        
        function runSystemCheck() {
            addTerminalOutput('Running system check...');
            fetch('/api/system/check')
                .then(response => response.json())
                .then(data => {
                    addTerminalOutput('System check completed');
                });
        }
        
        // Chat input enter key
        document.getElementById('chat-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
        
        // Initialize WebSocket connection
        connectWebSocket();
        
        // Initial data load
        fetch('/api/status').then(r => r.json()).then(updateSystemStatus);
        fetch('/api/agents').then(r => r.json()).then(data => updateAgents(data.agents));
    </script>
</body>
</html>
        '''
        
        return HTMLResponse(content=dashboard_html)
    
    async def get_system_status(self) -> Dict:
        """Get current system status"""
        try:
            import psutil
            
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check integrations
            wsl_available = bool(self.wsl_integration and self.wsl_integration.wsl_available)
            wsl_distros = list(self.wsl_integration.available_distros.keys()) if self.wsl_integration else []
            
            status = SystemStatus(
                timestamp=datetime.now(),
                wsl_available=wsl_available,
                wsl_distros=wsl_distros,
                ai_providers=["local", "cloud"],
                active_services=["webui", "ai_router"],
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_active=True
            )
            
            return asdict(status)
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}
    
    async def start_server(self, host: str = "127.0.0.1", port: int = 8787):
        """Start the enhanced WebUI server"""
        await self.initialize_integrations()
        
        print(f"Starting DuckBot Enhanced WebUI v3.1.0+")
        print(f"Server: http://{host}:{port}")
        print(f"Features: Multi-agent, WSL integration, Desktop control, Real-time updates")
        print(f"Security Token: {self.security_token}")
        print("-" * 60)
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()

# Global instance
enhanced_webui = EnhancedWebUI()

async def start_enhanced_webui(host: str = "127.0.0.1", port: int = 8787):
    """Start the enhanced WebUI"""
    await enhanced_webui.start_server(host, port)

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DuckBot Enhanced WebUI')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8787, help='Port to bind to')
    
    args = parser.parse_args()
    
    asyncio.run(start_enhanced_webui(args.host, args.port))

if __name__ == "__main__":
    main()
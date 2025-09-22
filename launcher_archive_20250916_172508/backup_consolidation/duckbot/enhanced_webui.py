#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Enhanced WebUI
Modern web interface with real-time updates and comprehensive integration
"""

import os
import sys
import json
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Import existing webui manager
try:
    from duckbot.services.webui_manager import WebUIManager, APP_TITLE, VERSION
except ImportError:
    # Fallback if import fails
    class WebUIManager:
        def __init__(self):
            self.title = "DuckBot Enhanced WebUI"
            self.version = "4.2"

        async def startup(self):
            pass

        async def shutdown(self):
            pass

    APP_TITLE = "DuckBot Enhanced WebUI"
    VERSION = "4.2"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title=APP_TITLE,
    description="DuckBot Enhanced WebUI with Real-time Updates",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="duckbot_session"
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Global state
webui_manager = None
startup_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    global webui_manager
    logger.info("Starting Enhanced WebUI...")
    webui_manager = WebUIManager()
    await webui_manager.startup()
    logger.info("Enhanced WebUI started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    global webui_manager
    logger.info("Shutting down Enhanced WebUI...")
    if webui_manager:
        await webui_manager.shutdown()
    logger.info("Enhanced WebUI shutdown complete")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Main dashboard page"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{APP_TITLE}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #e0e0e0;
            }}
            .status-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .status-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }}
            .status-card h3 {{
                margin: 0 0 10px 0;
                color: #333;
            }}
            .status-card p {{
                margin: 5px 0;
                color: #666;
            }}
            .online {{
                border-left-color: #28a745;
            }}
            .offline {{
                border-left-color: #dc3545;
            }}
            .websocket-status {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
                background: #e9ecef;
            }}
            .websocket-connected {{
                background: #d4edda;
                color: #155724;
            }}
            .websocket-disconnected {{
                background: #f8d7da;
                color: #721c24;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{APP_TITLE}</h1>
                <p>Version {VERSION} - Enhanced Web Interface</p>
                <p>Server started at: {startup_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div id="websocket-status" class="websocket-status websocket-disconnected">
                WebSocket: Disconnected
            </div>

            <div class="status-grid">
                <div class="status-card online">
                    <h3>Web Server</h3>
                    <p>Status: <span style="color: #28a745;">● Online</span></p>
                    <p>Port: {getattr(webui_manager, 'port', 8787)}</p>
                    <p>Uptime: <span id="uptime">0s</span></p>
                </div>

                <div class="status-card">
                    <h3>AI Router</h3>
                    <p>Status: <span id="ai-router-status">Checking...</span></p>
                    <p>Models: <span id="ai-models-count">0</span></p>
                    <p>Last check: <span id="ai-last-check">Never</span></p>
                </div>

                <div class="status-card">
                    <h3>System Resources</h3>
                    <p>CPU: <span id="cpu-usage">0%</span></p>
                    <p>Memory: <span id="memory-usage">0%</span></p>
                    <p>Disk: <span id="disk-usage">0%</span></p>
                </div>

                <div class="status-card">
                    <h3>Active Services</h3>
                    <p>Running: <span id="running-services">0</span></p>
                    <p>Total: <span id="total-services">0</span></p>
                    <p>Last update: <span id="services-last-update">Never</span></p>
                </div>
            </div>

            <div>
                <h2>Real-time System Log</h2>
                <div id="log-container" style="background: #f8f9fa; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px;">
                    <div>System started. Waiting for real-time updates...</div>
                </div>
            </div>

            <div>
                <h2>Multi-Agent Chat Interface</h2>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <input type="text" id="chat-input" placeholder="Ask the multi-agent system..."
                               style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        <select id="agent-type" style="padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                            <option value="general">General</option>
                            <option value="market_analysis">Market Analysis</option>
                            <option value="workflow_optimization">Workflow Optimization</option>
                            <option value="user_interaction">User Interaction</option>
                            <option value="system_analysis">System Analysis</option>
                        </select>
                        <label style="display: flex; align-items: center; gap: 5px;">
                            <input type="checkbox" id="use-multi-agent" checked>
                            <span>Use Multi-Agent</span>
                        </label>
                        <button id="send-button" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            Send
                        </button>
                    </div>

                    <div id="chat-messages" style="height: 400px; overflow-y: auto; background: white; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px;">
                        <div style="text-align: center; color: #666; font-style: italic;">
                            Chat with DuckBot's multi-agent system. Messages will be processed by specialized AI agents working together.
                        </div>
                    </div>

                    <div id="agent-status" style="display: flex; gap: 20px; font-size: 12px; color: #666;">
                        <span>Agents Active: <span id="agents-active">0</span></span>
                        <span>Approach: <span id="chat-approach">-</span></span>
                        <span>Confidence: <span id="chat-confidence">-</span></span>
                        <span>Last Response: <span id="last-response">-</span></span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // WebSocket connection
            const ws = new WebSocket(`ws://${{window.location.host}}/ws`);
            const wsStatus = document.getElementById('websocket-status');
            const logContainer = document.getElementById('log-container');

            ws.onopen = function() {{
                wsStatus.textContent = 'WebSocket: Connected';
                wsStatus.className = 'websocket-status websocket-connected';
                logMessage('WebSocket connected', 'info');
            }};

            ws.onclose = function() {{
                wsStatus.textContent = 'WebSocket: Disconnected';
                wsStatus.className = 'websocket-status websocket-disconnected';
                logMessage('WebSocket disconnected', 'error');
            }};

            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            }};

            ws.onerror = function(error) {{
                wsStatus.textContent = 'WebSocket: Error';
                wsStatus.className = 'websocket-status websocket-disconnected';
                logMessage('WebSocket error: ' + error, 'error');
            }};

            function handleWebSocketMessage(data) {{
                if (data.type === 'log') {{
                    logMessage(data.message, data.level);
                }} else if (data.type === 'status_update') {{
                    updateStatus(data);
                }} else if (data.type === 'system_metrics') {{
                    updateSystemMetrics(data);
                }}
            }}

            function logMessage(message, level = 'info') {{
                const timestamp = new Date().toLocaleTimeString();
                const logEntry = document.createElement('div');
                logEntry.innerHTML = `<span style="color: #666;">[${{timestamp}}]</span> <span style="color: ${{getColorForLevel(level)}};">[${{level.toUpperCase()}}]</span> ${{message}}`;
                logContainer.appendChild(logEntry);
                logContainer.scrollTop = logContainer.scrollHeight;
            }}

            function getColorForLevel(level) {{
                switch(level) {{
                    case 'error': return '#dc3545';
                    case 'warning': return '#ffc107';
                    case 'info': return '#007bff';
                    case 'debug': return '#6c757d';
                    default: return '#28a745';
                }}
            }}

            function updateStatus(data) {{
                if (data.ai_router) {{
                    document.getElementById('ai-router-status').textContent = data.ai_router.status || 'Unknown';
                    document.getElementById('ai-models-count').textContent = data.ai_router.models || 0;
                    document.getElementById('ai-last-check').textContent = data.ai_router.last_check || 'Never';
                }}
                if (data.services) {{
                    document.getElementById('running-services').textContent = data.services.running || 0;
                    document.getElementById('total-services').textContent = data.services.total || 0;
                    document.getElementById('services-last-update').textContent = data.services.last_update || 'Never';
                }}
            }}

            function updateSystemMetrics(data) {{
                if (data.cpu !== undefined) {{
                    document.getElementById('cpu-usage').textContent = data.cpu + '%';
                }}
                if (data.memory !== undefined) {{
                    document.getElementById('memory-usage').textContent = data.memory + '%';
                }}
                if (data.disk !== undefined) {{
                    document.getElementById('disk-usage').textContent = data.disk + '%';
                }}
            }}

            // Update uptime
            const startTime = new Date('{startup_time.isoformat()}');
            setInterval(() => {{
                const now = new Date();
                const uptime = Math.floor((now - startTime) / 1000);
                const hours = Math.floor(uptime / 3600);
                const minutes = Math.floor((uptime % 3600) / 60);
                const seconds = uptime % 60;
                document.getElementById('uptime').textContent = `${{hours}}h ${{minutes}}m ${{seconds}}s`;
            }}, 1000);

            // Chat functionality
            const chatInput = document.getElementById('chat-input');
            const chatSend = document.getElementById('chat-send');
            const chatMessages = document.getElementById('chat-messages');
            const chatStatus = document.getElementById('chat-status');
            const multiAgentToggle = document.getElementById('multi-agent-toggle');
            const agentTypeSelect = document.getElementById('agent-type-select');
            const activeAgentsDisplay = document.getElementById('active-agents');
            const approachTypeDisplay = document.getElementById('approach-type');
            const confidenceLevelDisplay = document.getElementById('confidence-level');

            // Chat WebSocket connection
            let chatWs;
            function connectChatWebSocket() {{
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${{protocol}}//${{window.location.host}}/ws/chat`;

                chatWs = new WebSocket(wsUrl);

                chatWs.onopen = function() {{
                    chatStatus.textContent = 'Chat: Connected';
                    chatStatus.className = 'status-indicator status-connected';
                    logMessage('Chat WebSocket connected', 'info');
                }};

                chatWs.onclose = function() {{
                    chatStatus.textContent = 'Chat: Disconnected';
                    chatStatus.className = 'status-indicator status-disconnected';
                    logMessage('Chat WebSocket disconnected', 'warning');
                    // Attempt to reconnect after 5 seconds
                    setTimeout(connectChatWebSocket, 5000);
                }};

                chatWs.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    handleChatMessage(data);
                }};

                chatWs.onerror = function(error) {{
                    chatStatus.textContent = 'Chat: Error';
                    chatStatus.className = 'status-indicator status-error';
                    logMessage('Chat WebSocket error: ' + error, 'error');
                }};
            }}

            function handleChatMessage(data) {{
                if (data.response) {{
                    addChatMessage('assistant', data.response);

                    // Update multi-agent info if available
                    if (data.agents_used !== undefined) {{
                        activeAgentsDisplay.textContent = data.agents_used;
                    }}
                    if (data.approach) {{
                        approachTypeDisplay.textContent = data.approach;
                    }}
                    if (data.confidence !== undefined) {{
                        confidenceLevelDisplay.textContent = (data.confidence * 100).toFixed(1) + '%';
                        confidenceLevelDisplay.className = 'confidence-level ' +
                            (data.confidence > 0.7 ? 'high' : data.confidence > 0.4 ? 'medium' : 'low');
                    }}

                    logMessage(`Chat response: ${{data.agents_used || 1}} agent(s), approach: ${{data.approach || 'unknown'}}`, 'info');
                }} else if (data.error) {{
                    addChatMessage('assistant', `Error: ${{data.error}}`);
                    logMessage('Chat error: ' + data.error, 'error');
                }}
            }}

            function addChatMessage(role, message) {{
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${{role}}`;

                const timestamp = new Date().toLocaleTimeString();
                const header = document.createElement('div');
                header.className = 'chat-header';
                header.textContent = `${{role === 'user' ? 'You' : 'Assistant'}} - ${{timestamp}}`;

                const content = document.createElement('div');
                content.className = 'chat-content';
                content.textContent = message;

                messageDiv.appendChild(header);
                messageDiv.appendChild(content);
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }}

            function sendMessage() {{
                const message = chatInput.value.trim();
                if (!message) return;

                // Add user message to chat
                addChatMessage('user', message);

                // Clear input
                chatInput.value = '';

                // Send via WebSocket
                if (chatWs && chatWs.readyState === WebSocket.OPEN) {{
                    const chatData = {{
                        message: message,
                        use_multi_agent: multiAgentToggle.checked,
                        agent_type: agentTypeSelect.value
                    }};
                    chatWs.send(JSON.stringify(chatData));
                    logMessage(`Sent message: ${{message}} (multi-agent: ${{multiAgentToggle.checked}}, type: ${{agentTypeSelect.value}})`, 'info');
                }} else {{
                    addChatMessage('assistant', 'Error: Chat connection not available');
                    logMessage('Cannot send message - WebSocket not connected', 'error');
                }}
            }}

            // Event listeners
            chatSend.addEventListener('click', sendMessage);
            chatInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});

            multiAgentToggle.addEventListener('change', function() {{
                logMessage(`Multi-agent mode: ${{this.checked ? 'Enabled' : 'Disabled'}}`, 'info');
            }});

            agentTypeSelect.addEventListener('change', function() {{
                logMessage(`Agent type changed to: ${{this.value}}`, 'info');
            }});

            // Initialize chat connection
            connectChatWebSocket();
        </script>
    </body>
    </html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)

            # Check AI Router status
            try:
                from duckbot.ai_router_gpt import AIRouter
                router = AIRouter()
                models = router.get_available_models()

                await manager.broadcast({
                    "type": "status_update",
                    "ai_router": {
                        "status": "Online" if models else "Offline",
                        "models": len(models),
                        "last_check": datetime.now().strftime("%H:%M:%S")
                    }
                })
            except Exception as e:
                logger.error(f"Error checking AI Router: {e}")

            # Get system metrics
            try:
                import psutil
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent

                await manager.broadcast({
                    "type": "system_metrics",
                    "cpu": round(cpu_percent, 1),
                    "memory": round(memory_percent, 1),
                    "disk": round(disk_percent, 1)
                })
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")

            # Send log message
            await manager.broadcast({
                "type": "log",
                "message": "System health check completed",
                "level": "info"
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/status")
async def get_status():
    """Get current system status"""
    try:
        # AI Router status
        try:
            from duckbot.ai_router_gpt import AIRouter
            router = AIRouter()
            models = router.get_available_models()
            ai_status = {
                "status": "Online" if models else "Offline",
                "models": len(models),
                "available_models": models
            }
        except Exception as e:
            ai_status = {"status": "Error", "error": str(e)}

        # System metrics
        try:
            import psutil
            metrics = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime_seconds": (datetime.now() - startup_time).total_seconds()
            }
        except Exception as e:
            metrics = {"error": str(e)}

        return {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "ai_router": ai_status,
            "system_metrics": metrics,
            "webui_version": VERSION
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Chat functionality with multi-agent integration
@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Chat endpoint with multi-agent support"""
    try:
        data = await request.json()
        message = data.get("message", "")
        use_multi_agent = data.get("use_multi_agent", True)
        agent_type = data.get("agent_type", "general")

        if not message:
            return {"error": "No message provided"}

        # Use multi-agent system if requested
        if use_multi_agent:
            try:
                from multi_agent_activator import get_multi_agent_system
                multi_agent_system = await get_multi_agent_system()

                # Route message through multi-agent system
                result = await multi_agent_system.process_request(
                    "user_interaction",
                    {"query": message, "type": agent_type},
                    {"session_id": request.session.get("session_id", "default")}
                )

                response = {
                    "response": result.get("best_result", {}).get("reasoning", "Multi-agent analysis completed"),
                    "agents_used": len(result.get("results", {})),
                    "approach": result.get("approach", "unknown"),
                    "confidence": result.get("best_result", {}).get("confidence", 0),
                    "multi_agent": True
                }
            except Exception as e:
                logger.warning(f"Multi-agent system failed, falling back to single agent: {e}")
                # Fallback to single agent
                response = await _single_agent_response(message, agent_type)
        else:
            # Single agent response
            response = await _single_agent_response(message, agent_type)

        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "chat_message",
            "message": message,
            "response": response["response"],
            "timestamp": datetime.now().isoformat()
        })

        return response

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {"error": str(e)}

async def _single_agent_response(message: str, agent_type: str) -> dict:
    """Fallback single agent response"""
    try:
        from duckbot.ai_router_gpt import route_task_async

        # Route through AI router
        result = await route_task_async(message, agent_type)

        return {
            "response": result.get("response", "AI response processed"),
            "agents_used": 1,
            "approach": "single_agent",
            "confidence": result.get("confidence", 0.5),
            "multi_agent": False
        }
    except Exception as e:
        logger.warning(f"Single agent response failed: {e}")
        return {
            "response": f"I received your message: '{message}'. I'm experiencing some technical difficulties, but I'm here to help!",
            "agents_used": 1,
            "approach": "fallback",
            "confidence": 0.3,
            "multi_agent": False
        }

@app.get("/api/chat/history")
async def get_chat_history():
    """Get chat history"""
    # This would typically connect to a database
    # For now, return empty history
    return {"history": [], "total": 0}

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process message
            response = await chat_endpoint_websocket(message_data)

            # Send response back
            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def chat_endpoint_websocket(data: dict) -> dict:
    """Chat endpoint for WebSocket (similar to HTTP but simplified)"""
    message = data.get("message", "")
    use_multi_agent = data.get("use_multi_agent", True)
    agent_type = data.get("agent_type", "general")

    if not message:
        return {"error": "No message provided"}

    try:
        if use_multi_agent:
            from multi_agent_activator import get_multi_agent_system
            multi_agent_system = await get_multi_agent_system()

            result = await multi_agent_system.process_request(
                "user_interaction",
                {"query": message, "type": agent_type},
                {"session_id": f"ws_{datetime.now().timestamp()}"}
            )

            return {
                "response": result.get("best_result", {}).get("reasoning", "Multi-agent analysis completed"),
                "agents_used": len(result.get("results", {})),
                "approach": result.get("approach", "unknown"),
                "multi_agent": True
            }
        else:
            from duckbot.ai_router_gpt import route_task_async
            result = await route_task_async(message, agent_type)

            return {
                "response": result.get("response", "AI response processed"),
                "agents_used": 1,
                "approach": "single_agent",
                "multi_agent": False
            }
    except Exception as e:
        logger.error(f"WebSocket chat error: {e}")
        return {
            "response": f"I received your message but encountered an error: {str(e)}",
            "agents_used": 0,
            "approach": "error",
            "multi_agent": False
        }

def main():
    """Main function to run the Enhanced WebUI"""
    parser = argparse.ArgumentParser(description="DuckBot Enhanced WebUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Store port in webui manager if available
    if webui_manager:
        webui_manager.port = args.port

    logger.info(f"Starting Enhanced WebUI on {args.host}:{args.port}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    main()
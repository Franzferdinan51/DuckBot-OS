#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Web Launcher
Modern web-based startup interface with real-time monitoring
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import uvicorn
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False
    print("Warning: FastAPI not available. Web launcher will be limited.")

# Import from our AI startup interface
try:
    from duckbot.ai_startup_interface import AIStartupInterface, APIKeys, StartupMode
    STARTUP_AVAILABLE = True
except ImportError:
    STARTUP_AVAILABLE = False
    print("Warning: AI startup interface not available")

logger = logging.getLogger(__name__)

class WebLauncher:
    """Web-based launcher with real-time monitoring"""

    def __init__(self):
        self.app = FastAPI(title="DuckBot Web Launcher", version="1.0.0")
        self.startup_interface = AIStartupInterface() if STARTUP_AVAILABLE else None
        self.running_processes = {}
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard"""
            return self._generate_dashboard_html()

        @self.app.get("/api/modes")
        async def get_modes():
            """Get all available startup modes"""
            if not self.startup_interface:
                return {"error": "Startup interface not available"}

            modes = []
            for mode in self.startup_interface.startup_modes:
                requirements = self.startup_interface.check_api_requirements(mode)
                modes.append({
                    "id": mode.id,
                    "name": mode.name,
                    "description": mode.description,
                    "category": mode.category,
                    "ai_powered": mode.ai_powered,
                    "port": mode.port,
                    "requirements": requirements,
                    "can_launch": all(requirements.values())
                })
            return {"modes": modes}

        @self.app.get("/api/status")
        async def get_status():
            """Get system status"""
            if not self.startup_interface:
                return {"error": "Startup interface not available"}

            return {
                "api_keys": {
                    "gemini": bool(self.startup_interface.api_keys.gemini_api_key),
                    "openrouter": bool(self.startup_interface.api_keys.openrouter_api_key),
                    "zai": bool(self.startup_interface.api_keys.zai_api_key)
                },
                "running_processes": len(self.running_processes),
                "system_info": {
                    "python": sys.version.split()[0],
                    "platform": sys.platform
                }
            }

        @self.app.post("/api/launch/{mode_id}")
        async def launch_mode(mode_id: str):
            """Launch a specific mode"""
            if not self.startup_interface:
                raise HTTPException(status_code=500, detail="Startup interface not available")

            mode = self.startup_interface.get_mode_by_id(mode_id)
            if not mode:
                raise HTTPException(status_code=404, detail="Mode not found")

            requirements = self.startup_interface.check_api_requirements(mode)
            if not all(requirements.values()):
                raise HTTPException(status_code=400, detail="Missing required API keys")

            # Launch the mode
            try:
                # This would be enhanced with actual process management
                process_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.running_processes[process_id] = {
                    "mode": mode.name,
                    "started_at": datetime.now().isoformat(),
                    "status": "running"
                }

                # For now, simulate launch
                # In production, this would actually launch the process
                return {
                    "success": True,
                    "process_id": process_id,
                    "message": f"Launched {mode.name}"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/setup-api-keys")
        async def setup_api_keys(request: Request):
            """Setup API keys"""
            if not self.startup_interface:
                raise HTTPException(status_code=500, detail="Startup interface not available")

            try:
                data = await request.json()

                if "gemini" in data:
                    self.startup_interface.api_keys.gemini_api_key = data["gemini"]
                if "openrouter" in data:
                    self.startup_interface.api_keys.openrouter_api_key = data["openrouter"]
                if "zai" in data:
                    self.startup_interface.api_keys.zai_api_key = data["zai"]
                if "zai_coding_plan" in data:
                    self.startup_interface.api_keys.zai_coding_plan = data["zai_coding_plan"]

                self.startup_interface._save_config()
                return {"success": True, "message": "API keys updated"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _generate_dashboard_html(self) -> str:
        """Generate dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckBot Web Launcher</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <style>
        .mode-card {
            transition: all 0.3s ease;
        }
        .mode-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-ready { background-color: #10b981; }
        .status-locked { background-color: #f59e0b; }
        .status-running { background-color: #3b82f6; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-4">
                    <div class="flex items-center">
                        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                            <i data-lucide="bot" class="w-5 h-5 text-white"></i>
                        </div>
                        <div>
                            <h1 class="text-2xl font-bold text-gray-900">DuckBot Web Launcher</h1>
                            <p class="text-sm text-gray-500">AI-Powered Startup Interface</p>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button onclick="showApiSetup()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                            <i data-lucide="settings" class="w-4 h-4 inline mr-2"></i>
                            Setup API Keys
                        </button>
                        <button onclick="refreshStatus()" class="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors">
                            <i data-lucide="refresh-cw" class="w-4 h-4 inline mr-2"></i>
                            Refresh
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Status Bar -->
        <div class="bg-white border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-6">
                        <div class="flex items-center">
                            <span class="status-indicator status-ready"></span>
                            <span class="text-sm text-gray-600">System Ready</span>
                        </div>
                        <div class="flex items-center">
                            <span id="api-status-gemini" class="status-indicator status-locked"></span>
                            <span class="text-sm text-gray-600">Gemini</span>
                        </div>
                        <div class="flex items-center">
                            <span id="api-status-openrouter" class="status-indicator status-locked"></span>
                            <span class="text-sm text-gray-600">OpenRouter</span>
                        </div>
                        <div class="flex items-center">
                            <span id="api-status-zai" class="status-indicator status-locked"></span>
                            <span class="text-sm text-gray-600">Z.ai</span>
                        </div>
                    </div>
                    <div class="text-sm text-gray-500">
                        <span id="running-processes">0</span> processes running
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- AI Recommendations -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
                <div class="flex items-center mb-4">
                    <i data-lucide="sparkles" class="w-6 h-6 text-blue-600 mr-3"></i>
                    <h2 class="text-xl font-semibold text-blue-900">AI Recommendations</h2>
                </div>
                <div id="recommendations" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <!-- Recommendations will be loaded here -->
                </div>
            </div>

            <!-- Startup Modes -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="modes-container">
                <!-- Modes will be loaded here -->
            </div>
        </main>
    </div>

    <!-- API Setup Modal -->
    <div id="api-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
        <div class="flex items-center justify-center min-h-screen p-4">
            <div class="bg-white rounded-lg max-w-md w-full p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">API Key Setup</h3>
                    <button onclick="closeApiSetup()" class="text-gray-400 hover:text-gray-600">
                        <i data-lucide="x" class="w-5 h-5"></i>
                    </button>
                </div>
                <form id="api-form" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Gemini API Key</label>
                        <input type="password" id="gemini-key" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter Gemini API Key">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">OpenRouter API Key</label>
                        <input type="password" id="openrouter-key" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter OpenRouter API Key">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Z.ai API Key</label>
                        <input type="password" id="zai-key" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter Z.ai API Key">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Z.ai Coding Plan (Optional)</label>
                        <input type="text" id="zai-plan" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter Coding Plan ID">
                    </div>
                    <div class="flex space-x-3">
                        <button type="submit" class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
                            Save Keys
                        </button>
                        <button type="button" onclick="closeApiSetup()" class="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Initialize Lucide icons
        lucide.createIcons();

        // Load modes and status
        async function loadModes() {
            try {
                const response = await fetch('/api/modes');
                const data = await response.json();

                const container = document.getElementById('modes-container');
                container.innerHTML = '';

                // Group by category
                const categories = {};
                data.modes.forEach(mode => {
                    if (!categories[mode.category]) {
                        categories[mode.category] = [];
                    }
                    categories[mode.category].push(mode);
                });

                // Render modes
                Object.entries(categories).forEach(([category, modes]) => {
                    const categoryDiv = document.createElement('div');
                    categoryDiv.className = 'col-span-full mb-6';
                    categoryDiv.innerHTML = `
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">${category}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            ${modes.map(mode => createModeCard(mode)).join('')}
                        </div>
                    `;
                    container.appendChild(categoryDiv);
                });
            } catch (error) {
                console.error('Error loading modes:', error);
            }
        }

        function createModeCard(mode) {
            const canLaunch = mode.can_launch;
            const statusClass = canLaunch ? 'status-ready' : 'status-locked';
            const buttonClass = canLaunch ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed';
            const buttonText = canLaunch ? 'Launch' : 'Setup API Keys';

            return `
                <div class="mode-card bg-white rounded-lg shadow-sm border p-6">
                    <div class="flex items-center justify-between mb-3">
                        <span class="status-indicator ${statusClass}"></span>
                        ${mode.ai_powered ? '<i data-lucide="bot" class="w-4 h-4 text-blue-600"></i>' : ''}
                    </div>
                    <h4 class="font-semibold text-gray-900 mb-2">${mode.name}</h4>
                    <p class="text-sm text-gray-600 mb-4">${mode.description}</p>
                    ${mode.port ? `<p class="text-xs text-gray-500 mb-3">Port: ${mode.port}</p>` : ''}
                    <button onclick="launchMode('${mode.id}')" class="w-full ${buttonClass} text-white py-2 px-4 rounded-md transition-colors">
                        ${buttonText}
                    </button>
                </div>
            `;
        }

        async function launchMode(modeId) {
            try {
                const response = await fetch(`/api/launch/${modeId}`, { method: 'POST' });
                const data = await response.json();

                if (data.success) {
                    alert(`Successfully launched: ${data.message}`);
                    refreshStatus();
                } else {
                    alert(`Error: ${data.message}`);
                }
            } catch (error) {
                alert('Error launching mode');
            }
        }

        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                // Update API status indicators
                if (data.api_keys) {
                    document.getElementById('api-status-gemini').className =
                        `status-indicator ${data.api_keys.gemini ? 'status-ready' : 'status-locked'}`;
                    document.getElementById('api-status-openrouter').className =
                        `status-indicator ${data.api_keys.openrouter ? 'status-ready' : 'status-locked'}`;
                    document.getElementById('api-status-zai').className =
                        `status-indicator ${data.api_keys.zai ? 'status-ready' : 'status-locked'}`;
                }

                // Update running processes
                document.getElementById('running-processes').textContent = data.running_processes;
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }

        function showApiSetup() {
            document.getElementById('api-modal').classList.remove('hidden');
        }

        function closeApiSetup() {
            document.getElementById('api-modal').classList.add('hidden');
        }

        // API form submission
        document.getElementById('api-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                gemini: document.getElementById('gemini-key').value,
                openrouter: document.getElementById('openrouter-key').value,
                zai: document.getElementById('zai-key').value,
                zai_coding_plan: document.getElementById('zai-plan').value
            };

            try {
                const response = await fetch('/api/setup-api-keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                if (response.ok) {
                    alert('API keys saved successfully!');
                    closeApiSetup();
                    refreshStatus();
                    loadModes();
                } else {
                    alert('Error saving API keys');
                }
            } catch (error) {
                alert('Error saving API keys');
            }
        });

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadModes();
            refreshStatus();

            // Refresh status every 30 seconds
            setInterval(refreshStatus, 30000);
        });
    </script>
</body>
</html>
        """

def start_web_launcher(host: str = "127.0.0.1", port: int = 8080):
    """Start the web launcher"""
    if not WEB_AVAILABLE:
        print("❌ FastAPI not available. Please install: pip install fastapi uvicorn")
        return

    launcher = WebLauncher()
    print(f"🌐 Starting DuckBot Web Launcher on http://{host}:{port}")
    uvicorn.run(launcher.app, host=host, port=port)

if __name__ == "__main__":
    start_web_launcher()
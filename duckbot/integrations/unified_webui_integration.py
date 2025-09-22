"""
Unified WebUI Integration for ComfyUI, TRELLIS, and VibeVoice
Provides web interface for managing all three services
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .unified_service_manager import unified_service_manager

logger = logging.getLogger(__name__)

# Create router for unified services
unified_router = APIRouter(prefix="/api/unified", tags=["unified-services"])

# Static files for unified services
UNIFIED_STATIC_DIR = Path(__file__).parent.parent.parent / "static" / "unified"
UNIFIED_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "unified"

# Ensure directories exist
UNIFIED_STATIC_DIR.mkdir(parents=True, exist_ok=True)
UNIFIED_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

@unified_router.get("/status")
async def get_unified_status():
    """Get unified status of all services"""
    try:
        return await unified_service_manager.get_unified_status()
    except Exception as e:
        logger.error(f"Error getting unified status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.get("/services/{service_name}/health")
async def get_service_health(service_name: str):
    """Get health information for a specific service"""
    try:
        return await unified_service_manager.get_service_health(service_name)
    except Exception as e:
        logger.error(f"Error getting service health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/services/{service_name}/restart")
async def restart_service(service_name: str):
    """Restart a specific service"""
    try:
        success = await unified_service_manager.restart_service(service_name)
        return {"success": success, "service": service_name}
    except Exception as e:
        logger.error(f"Error restarting service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ComfyUI Endpoints
@unified_router.get("/comfyui/workflows")
async def get_comfyui_workflows():
    """Get available ComfyUI workflows"""
    try:
        return await unified_service_manager.comfyui_manager.get_available_workflows()
    except Exception as e:
        logger.error(f"Error getting ComfyUI workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/comfyui/execute")
async def execute_comfyui_workflow(request: Dict[str, Any]):
    """Execute ComfyUI workflow"""
    try:
        workflow_type = request.get("workflow_type")
        parameters = request.get("parameters", {})
        output_dir = request.get("output_dir")

        if not workflow_type:
            raise HTTPException(status_code=400, detail="workflow_type is required")

        result = await unified_service_manager.execute_comfyui_workflow(
            workflow_type, parameters, output_dir
        )
        return result
    except Exception as e:
        logger.error(f"Error executing ComfyUI workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.get("/comfyui/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get status of a specific ComfyUI workflow"""
    try:
        status = await unified_service_manager.comfyui_manager.get_workflow_status(workflow_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TRELLIS Endpoints
@unified_router.get("/trellis/assets/types")
async def get_trellis_asset_types():
    """Get available TRELLIS asset types"""
    try:
        return await unified_service_manager.trellis_manager.get_available_asset_types()
    except Exception as e:
        logger.error(f"Error getting TRELLIS asset types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/trellis/generate")
async def generate_3d_asset(request: Dict[str, Any]):
    """Generate 3D asset using TRELLIS"""
    try:
        asset_type = request.get("asset_type")
        parameters = request.get("parameters", {})
        output_format = request.get("output_format", "gaussians")
        output_dir = request.get("output_dir")

        if not asset_type:
            raise HTTPException(status_code=400, detail="asset_type is required")

        result = await unified_service_manager.generate_3d_asset(
            asset_type, parameters, output_format, output_dir
        )
        return result
    except Exception as e:
        logger.error(f"Error generating 3D asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.get("/trellis/workflows/structures")
async def get_workflow_structures():
    """Get available TRELLIS workflow structures"""
    try:
        return await unified_service_manager.trellis_manager.get_workflow_structures()
    except Exception as e:
        logger.error(f"Error getting workflow structures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/trellis/workflows/create")
async def create_trellis_workflow(request: Dict[str, Any]):
    """Create TRELLIS workflow structure"""
    try:
        structure_type = request.get("structure_type")
        tasks = request.get("tasks", [])
        dependencies = request.get("dependencies", [])

        if not structure_type or not tasks:
            raise HTTPException(status_code=400, detail="structure_type and tasks are required")

        result = await unified_service_manager.create_trellis_workflow(
            structure_type, tasks, dependencies
        )
        return result
    except Exception as e:
        logger.error(f"Error creating TRELLIS workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.get("/trellis/workflows/{workflow_id}/status")
async def get_trellis_workflow_status(workflow_id: str):
    """Get status of a specific TRELLIS workflow"""
    try:
        status = await unified_service_manager.trellis_manager.get_workflow_status(workflow_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting TRELLIS workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# VibeVoice Endpoints
@unified_router.get("/vibevoice/voices")
async def get_vibevoice_voices():
    """Get available VibeVoice voices"""
    try:
        return {"voices": unified_service_manager.vibevoice_manager.get_available_voices()}
    except Exception as e:
        logger.error(f"Error getting VibeVoice voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/vibevoice/generate")
async def generate_voice_content(request: Dict[str, Any]):
    """Generate voice content using VibeVoice"""
    try:
        content = request.get("content")
        speakers = request.get("speakers")
        style = request.get("style", "conversational")

        if not content:
            raise HTTPException(status_code=400, detail="content is required")

        result = await unified_service_manager.generate_voice_content(
            content, speakers, style
        )
        return result
    except Exception as e:
        logger.error(f"Error generating voice content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/vibevoice/conversation")
async def generate_voice_conversation(request: Dict[str, Any]):
    """Generate multi-speaker conversation"""
    try:
        script = request.get("script", [])
        style = request.get("style", "conversational")
        output_dir = request.get("output_dir")

        if not script:
            raise HTTPException(status_code=400, detail="script is required")

        result = await unified_service_manager.generate_voice_conversation(
            script, style, output_dir
        )
        return result
    except Exception as e:
        logger.error(f"Error generating voice conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/vibevoice/emotion")
async def generate_emotional_speech(request: Dict[str, Any]):
    """Generate emotional speech"""
    try:
        text = request.get("text")
        emotion = request.get("emotion", "neutral")
        speaker = request.get("speaker", "en-alice")
        intensity = request.get("intensity", 0.5)
        output_dir = request.get("output_dir")

        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        result = await unified_service_manager.vibevoice_manager.generate_with_emotion(
            text, emotion, speaker, intensity, output_dir
        )
        return {"success": result is not None, "audio_path": result}
    except Exception as e:
        logger.error(f"Error generating emotional speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/vibevoice/podcast")
async def generate_podcast_episode(request: Dict[str, Any]):
    """Generate podcast episode"""
    try:
        content = request.get("content", {})
        output_dir = request.get("output_dir")

        result = await unified_service_manager.vibevoice_manager.generate_podcast_episode(
            content, output_dir
        )
        return result
    except Exception as e:
        logger.error(f"Error generating podcast episode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cross-Service Integration Endpoints
@unified_router.post("/multimodal-workflow")
async def create_multimodal_workflow(request: Dict[str, Any]):
    """Create cross-service multimodal workflow"""
    try:
        description = request.get("description")
        requirements = request.get("requirements", {})

        if not description:
            raise HTTPException(status_code=400, detail="description is required")

        result = await unified_service_manager.create_multimodal_workflow(
            description, requirements
        )
        return result
    except Exception as e:
        logger.error(f"Error creating multimodal workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.get("/config")
async def get_configuration():
    """Get current configuration"""
    try:
        config = unified_service_manager.config
        # Remove sensitive information
        safe_config = {
            k: {k2: v2 for k2, v2 in v.items() if k2 not in ["path"]}
            for k, v in config.items()
        }
        return safe_config
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.put("/config")
async def update_configuration(request: Dict[str, Any]):
    """Update configuration"""
    try:
        success = await unified_service_manager.update_configuration(request)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File Upload Endpoints
@unified_router.post("/comfyui/upload-image")
async def upload_comfyui_image(file: UploadFile = File(...)):
    """Upload image for ComfyUI processing"""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create upload directory
        upload_dir = UNIFIED_STATIC_DIR / "uploads" / "comfyui"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {"success": True, "file_path": str(file_path)}
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@unified_router.post("/trellis/upload-mesh")
async def upload_trellis_mesh(file: UploadFile = File(...)):
    """Upload mesh for TRELLIS processing"""
    try:
        allowed_extensions = [".obj", ".ply", ".stl", ".glb", ".gltf"]
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File must be one of: {allowed_extensions}")

        # Create upload directory
        upload_dir = UNIFIED_STATIC_DIR / "uploads" / "trellis"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {"success": True, "file_path": str(file_path)}
    except Exception as e:
        logger.error(f"Error uploading mesh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# HTML Templates
def create_unified_dashboard_html():
    """Create HTML for unified services dashboard"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckBot Unified Services Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #7c3aed;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #e2e8f0;
            --border-color: #334155;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 10px;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: var(--card-bg);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .card-title {
            font-size: 1.3rem;
            font-weight: 600;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-online { background-color: var(--success-color); }
        .status-offline { background-color: var(--error-color); }
        .status-warning { background-color: var(--warning-color); }

        .btn {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }

        .btn:hover {
            background: #1d4ed8;
        }

        .btn-secondary {
            background: var(--secondary-color);
        }

        .btn-secondary:hover {
            background: #6d28d9;
        }

        .btn-success {
            background: var(--success-color);
        }

        .btn-danger {
            background: var(--error-color);
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }

        input, select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 5px;
            background: var(--bg-color);
            color: var(--text-color);
            font-size: 0.9rem;
        }

        textarea {
            resize: vertical;
            min-height: 100px;
        }

        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
        }

        .tab.active {
            border-bottom-color: var(--primary-color);
            color: var(--primary-color);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }

        .stat-item {
            background: var(--bg-color);
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary-color);
        }

        .stat-label {
            font-size: 0.8rem;
            opacity: 0.8;
        }

        .loading {
            text-align: center;
            padding: 20px;
        }

        .spinner {
            border: 3px solid var(--border-color);
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
        }

        .alert-success { background: rgba(16, 185, 129, 0.2); border-left: 4px solid var(--success-color); }
        .alert-error { background: rgba(239, 68, 68, 0.2); border-left: 4px solid var(--error-color); }
        .alert-warning { background: rgba(245, 158, 11, 0.2); border-left: 4px solid var(--warning-color); }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
        }

        .modal-content {
            background: var(--card-bg);
            margin: 5% auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 600px;
        }

        .close {
            color: var(--text-color);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: var(--error-color);
        }

        .workflow-steps {
            margin: 15px 0;
        }

        .workflow-step {
            background: var(--bg-color);
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 3px solid var(--primary-color);
        }

        .chart-container {
            position: relative;
            height: 200px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 DuckBot Unified Services</h1>
            <p class="subtitle">ComfyUI • TRELLIS • VibeVoice Integration</p>
        </header>

        <!-- Service Status Cards -->
        <div class="dashboard-grid">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">🎨 ComfyUI</h3>
                    <span class="status-indicator status-offline" id="comfyui-status"></span>
                </div>
                <p>AI-powered image generation and creative workflows</p>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="comfyui-workflows">0</div>
                        <div class="stat-label">Workflows</div>
                    </div>
                </div>
                <button class="btn" onclick="showComfyUIPanel()">Manage</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">🎯 TRELLIS</h3>
                    <span class="status-indicator status-offline" id="trellis-status"></span>
                </div>
                <p>3D asset generation and structured AI workflows</p>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="trellis-assets">0</div>
                        <div class="stat-label">Asset Types</div>
                    </div>
                </div>
                <button class="btn btn-secondary" onclick="showTrellISPanel()">Manage</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">🎤 VibeVoice</h3>
                    <span class="status-indicator status-offline" id="vibevoice-status"></span>
                </div>
                <p>Multi-speaker text-to-speech with emotional intelligence</p>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="vibevoice-voices">0</div>
                        <div class="stat-label">Voices</div>
                    </div>
                </div>
                <button class="btn btn-success" onclick="showVibeVoicePanel()">Manage</button>
            </div>
        </div>

        <!-- Performance Overview -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">📊 Performance Overview</h3>
                <button class="btn" onclick="refreshStatus()">Refresh</button>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="total-requests">0</div>
                    <div class="stat-label">Total Requests</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="success-rate">0%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="avg-response">0s</div>
                    <div class="stat-label">Avg Response</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="uptime">0h</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="usage-chart"></canvas>
            </div>
        </div>

        <!-- Multimodal Workflow -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">🔗 Multimodal Workflow</h3>
            </div>
            <p>Create workflows that combine multiple services</p>
            <div class="form-group">
                <label for="workflow-description">Workflow Description:</label>
                <textarea id="workflow-description" placeholder="Describe what you want to create (e.g., 'A story about a robot with images, 3D models, and narration')"></textarea>
            </div>
            <button class="btn btn-secondary" onclick="createMultimodalWorkflow()">Create Workflow</button>
            <div id="workflow-results"></div>
        </div>
    </div>

    <!-- Modals -->
    <div id="comfyui-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('comfyui-modal')">&times;</span>
            <h2>ComfyUI Management</h2>
            <div class="tabs">
                <div class="tab active" onclick="showTab('comfyui', 'workflows')">Workflows</div>
                <div class="tab" onclick="showTab('comfyui', 'execute')">Execute</div>
                <div class="tab" onclick="showTab('comfyui', 'status')">Status</div>
            </div>
            <div id="comfyui-workflows" class="tab-content active">
                <div id="comfyui-workflows-list"></div>
            </div>
            <div id="comfyui-execute" class="tab-content">
                <!-- ComfyUI execution form -->
            </div>
            <div id="comfyui-status" class="tab-content">
                <div id="comfyui-status-details"></div>
            </div>
        </div>
    </div>

    <div id="trellis-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('trellis-modal')">&times;</span>
            <h2>TRELLIS Management</h2>
            <div class="tabs">
                <div class="tab active" onclick="showTab('trellis', 'assets')">3D Assets</div>
                <div class="tab" onclick="showTab('trellis', 'workflows')">Workflows</div>
                <div class="tab" onclick="showTab('trellis', 'status')">Status</div>
            </div>
            <div id="trellis-assets" class="tab-content active">
                <div id="trellis-assets-list"></div>
            </div>
            <div id="trellis-workflows" class="tab-content">
                <div id="trellis-workflows-list"></div>
            </div>
            <div id="trellis-status" class="tab-content">
                <div id="trellis-status-details"></div>
            </div>
        </div>
    </div>

    <div id="vibevoice-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('vibevoice-modal')">&times;</span>
            <h2>VibeVoice Management</h2>
            <div class="tabs">
                <div class="tab active" onclick="showTab('vibevoice', 'generate')">Generate</div>
                <div class="tab" onclick="showTab('vibevoice', 'conversation')">Conversation</div>
                <div class="tab" onclick="showTab('vibevoice', 'podcast')">Podcast</div>
                <div class="tab" onclick="showTab('vibevoice', 'status')">Status</div>
            </div>
            <div id="vibevoice-generate" class="tab-content active">
                <!-- VibeVoice generation form -->
            </div>
            <div id="vibevoice-conversation" class="tab-content">
                <!-- Conversation generation form -->
            </div>
            <div id="vibevoice-podcast" class="tab-content">
                <!-- Podcast generation form -->
            </div>
            <div id="vibevoice-status" class="tab-content">
                <div id="vibevoice-status-details"></div>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let statusData = null;
        let usageChart = null;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeDashboard();
            startStatusUpdates();
        });

        async function initializeDashboard() {
            await refreshStatus();
            initializeChart();
        }

        async function refreshStatus() {
            try {
                const response = await fetch('/api/unified/status');
                statusData = await response.json();
                updateDashboard();
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }

        function updateDashboard() {
            if (!statusData) return;

            // Update service status
            updateServiceStatus('comfyui', statusData.services.comfyui);
            updateServiceStatus('trellis', statusData.services.trellis);
            updateServiceStatus('vibevoice', statusData.services.vibevoice);

            // Update performance metrics
            const perf = statusData.performance;
            document.getElementById('total-requests').textContent = perf.total_requests;
            document.getElementById('success-rate').textContent =
                perf.total_requests > 0 ? Math.round((perf.successful_requests / perf.total_requests) * 100) + '%' : '0%';
            document.getElementById('avg-response').textContent = Math.round(perf.average_response_time) + 's';

            const uptime = new Date() - new Date(perf.uptime_start);
            document.getElementById('uptime').textContent = Math.round(uptime / 3600000) + 'h';

            // Update chart
            updateChart();
        }

        function updateServiceStatus(service, data) {
            const statusIndicator = document.getElementById(service + '-status');
            const isHealthy = data.healthy && data.initialized;

            statusIndicator.className = 'status-indicator ' + (isHealthy ? 'status-online' : 'status-offline');

            // Update specific stats
            if (service === 'comfyui') {
                document.getElementById('comfyui-workflows').textContent = data.available_workflows?.length || 0;
            } else if (service === 'trellis') {
                document.getElementById('trellis-assets').textContent = data.available_asset_types?.length || 0;
            } else if (service === 'vibevoice') {
                document.getElementById('vibevoice-voices').textContent = data.available_voices?.length || 0;
            }
        }

        function initializeChart() {
            const ctx = document.getElementById('usage-chart').getContext('2d');
            usageChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['ComfyUI', 'TRELLIS', 'VibeVoice'],
                    datasets: [{
                        label: 'Service Usage',
                        data: [0, 0, 0],
                        backgroundColor: ['#2563eb', '#7c3aed', '#10b981']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#e2e8f0'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#e2e8f0'
                            },
                            grid: {
                                color: '#334155'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#e2e8f0'
                            },
                            grid: {
                                color: '#334155'
                            }
                        }
                    }
                }
            });
        }

        function updateChart() {
            if (!usageChart || !statusData) return;

            const usage = statusData.performance.service_usage;
            usageChart.data.datasets[0].data = [
                usage.comfyui,
                usage.trellis,
                usage.vibevoice
            ];
            usageChart.update();
        }

        function startStatusUpdates() {
            setInterval(refreshStatus, 30000); // Update every 30 seconds
        }

        // Modal functions
        function showComfyUIPanel() {
            document.getElementById('comfyui-modal').style.display = 'block';
            loadComfyUIWorkflows();
        }

        function showTrellISPanel() {
            document.getElementById('trellis-modal').style.display = 'block';
            loadTrellISAssets();
        }

        function showVibeVoicePanel() {
            document.getElementById('vibevoice-modal').style.display = 'block';
            loadVibeVoiceVoices();
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        function showTab(service, tabName) {
            // Remove active class from all tabs and content
            const tabs = document.querySelectorAll(`#${service}-modal .tab`);
            const contents = document.querySelectorAll(`#${service}-modal .tab-content`);

            tabs.forEach(tab => tab.classList.remove('active'));
            contents.forEach(content => content.classList.remove('active'));

            // Add active class to selected tab and content
            event.target.classList.add('active');
            document.getElementById(`${service}-${tabName}`).classList.add('active');
        }

        // Service-specific functions
        async function loadComfyUIWorkflows() {
            try {
                const response = await fetch('/api/unified/comfyui/workflows');
                const workflows = await response.json();

                const listHtml = workflows.map(w => `
                    <div class="workflow-step">
                        <h4>${w.name}</h4>
                        <p>${w.description}</p>
                        <button class="btn" onclick="executeComfyUIWorkflow('${w.name}')">Execute</button>
                    </div>
                `).join('');

                document.getElementById('comfyui-workflows-list').innerHTML = listHtml;
            } catch (error) {
                console.error('Error loading ComfyUI workflows:', error);
            }
        }

        async function loadTrellISAssets() {
            try {
                const response = await fetch('/api/unified/trellis/assets/types');
                const assets = await response.json();

                const listHtml = assets.map(a => `
                    <div class="workflow-step">
                        <h4>${a.name}</h4>
                        <p>${a.description}</p>
                        <p><strong>Input:</strong> ${a.input_type}</p>
                        <p><strong>Output:</strong> ${a.output_formats.join(', ')}</p>
                        <button class="btn btn-secondary" onclick="generate3DAsset('${a.name}')">Generate</button>
                    </div>
                `).join('');

                document.getElementById('trellis-assets-list').innerHTML = listHtml;
            } catch (error) {
                console.error('Error loading TRELLIS assets:', error);
            }
        }

        async function loadVibeVoiceVoices() {
            try {
                const response = await fetch('/api/unified/vibevoice/voices');
                const data = await response.json();

                const voicesHtml = data.voices.map(v => `
                    <div class="workflow-step">
                        <h4>${v}</h4>
                        <button class="btn btn-success" onclick="generateVoice('${v}')">Test Voice</button>
                    </div>
                `).join('');

                document.getElementById('vibevoice-voices-list') = voicesHtml;
            } catch (error) {
                console.error('Error loading VibeVoice voices:', error);
            }
        }

        async function createMultimodalWorkflow() {
            const description = document.getElementById('workflow-description').value;
            if (!description) {
                alert('Please enter a workflow description');
                return;
            }

            try {
                const response = await fetch('/api/unified/multimodal-workflow', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        description: description,
                        requirements: {}
                    })
                });

                const result = await response.json();

                if (result.success) {
                    displayWorkflowResults(result);
                } else {
                    alert('Error creating workflow: ' + result.error);
                }
            } catch (error) {
                console.error('Error creating multimodal workflow:', error);
                alert('Error creating workflow');
            }
        }

        function displayWorkflowResults(result) {
            const resultsDiv = document.getElementById('workflow-results');
            const summary = result.execution_summary;

            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4>Workflow Created Successfully!</h4>
                    <p><strong>Services Used:</strong> ${summary.services_used.join(', ')}</p>
                    <p><strong>Total Steps:</strong> ${summary.total_steps}</p>
                    <p><strong>Success Rate:</strong> ${Math.round(summary.success_rate * 100)}%</p>
                </div>
                <div class="workflow-steps">
                    ${result.results.map((step, i) => `
                        <div class="workflow-step">
                            <h5>Step ${i + 1}: ${step.step.service}</h5>
                            <p><strong>Action:</strong> ${step.step.action}</p>
                            <p><strong>Status:</strong> ${step.result.success ? '✅ Success' : '❌ Failed'}</p>
                            ${step.result.error ? `<p><strong>Error:</strong> ${step.result.error}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Close modals when clicking outside
        window.onclick = function(event) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
    """

# Create the dashboard HTML file
dashboard_html_path = UNIFIED_STATIC_DIR / "dashboard.html"
with open(dashboard_html_path, 'w', encoding='utf-8') as f:
    f.write(create_unified_dashboard_html())

@unified_router.get("/dashboard", response_class=HTMLResponse)
async def unified_dashboard():
    """Serve the unified services dashboard"""
    return create_unified_dashboard_html()

# Function to integrate with existing WebUI
def integrate_with_webui(app):
    """Integrate unified services with existing FastAPI app"""
    # Include the unified router
    app.include_router(unified_router)

    # Mount static files
    app.mount("/unified-static", StaticFiles(directory=str(UNIFIED_STATIC_DIR)), name="unified-static")

    logger.info("Unified services integrated with WebUI")

# Export for use in other modules
__all__ = ["unified_router", "integrate_with_webui"]
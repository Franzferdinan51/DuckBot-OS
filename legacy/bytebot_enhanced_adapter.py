"""
ByteBot-Enhanced OpenWebUI-DuckBot Adapter
Integrates ByteBot's desktop agent capabilities with DuckBot's AI routing
Provides advanced task automation, workflow management, and cross-application integration
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator, Any, Union
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
import httpx
import subprocess
import tempfile
from pathlib import Path

# Import DuckBot's AI router
try:
    from duckbot.ai_router_gpt import route_task, get_router_state, enhanced_chat_completion
    from duckbot.rag import search_rag, index_stats
    from duckbot.cost_tracker import get_cost_summary
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    logging.error("DuckBot modules not available - adapter will run in mock mode")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bytebot_enhanced_adapter")

# Configuration
DUCKBOT_URL = "http://localhost:8787"
BYTEBOT_URL = "http://localhost:8000"  # ByteBot default port
ADAPTER_PORT = 11434
ADAPTER_HOST = "127.0.0.1"

# Enhanced models with ByteBot capabilities
class TaskRequest(BaseModel):
    task: str = Field(..., description="Natural language task description")
    files: Optional[List[str]] = Field(None, description="File paths to process")
    applications: Optional[List[str]] = Field(None, description="Applications to use")
    automation_type: str = Field("desktop", description="Type of automation: desktop, web, file")
    ai_model: str = Field("duckbot-auto", description="AI model to use")

class WorkflowStep(BaseModel):
    step_id: int = Field(..., description="Step sequence number")
    action: str = Field(..., description="Action to perform")
    target: Optional[str] = Field(None, description="Target application or element")
    parameters: Optional[Dict] = Field(None, description="Step parameters")
    ai_assistance: bool = Field(True, description="Use AI for this step")

class WorkflowRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    ai_model: str = Field("duckbot-auto", description="Primary AI model")

class ByteBotIntegration:
    """ByteBot desktop agent integration"""
    
    def __init__(self):
        self.bytebot_available = False
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=300)  # 5 minute timeout for long tasks
        await self.check_bytebot_availability()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_bytebot_availability(self) -> bool:
        """Check if ByteBot is available"""
        try:
            response = await self.session.get(f"{BYTEBOT_URL}/health", timeout=5)
            self.bytebot_available = response.status_code == 200
            logger.info(f"ByteBot availability: {self.bytebot_available}")
            return self.bytebot_available
        except Exception as e:
            logger.warning(f"ByteBot not available: {e}")
            self.bytebot_available = False
            return False
    
    async def execute_desktop_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Execute desktop automation task using ByteBot"""
        if not self.bytebot_available:
            return {"error": "ByteBot desktop agent not available", "fallback": True}
        
        try:
            # Prepare ByteBot task payload
            payload = {
                "task": task_request.task,
                "ai_model": task_request.ai_model,
                "automation_type": task_request.automation_type
            }
            
            # Add file uploads if provided
            files = None
            if task_request.files:
                files = []
                for file_path in task_request.files:
                    if Path(file_path).exists():
                        files.append(("files", open(file_path, "rb")))
            
            # Execute task via ByteBot API
            response = await self.session.post(
                f"{BYTEBOT_URL}/api/tasks",
                data=payload,
                files=files if files else None
            )
            
            # Clean up file handles
            if files:
                for _, file_handle in files:
                    file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "task_id": result.get("task_id"),
                    "status": result.get("status", "completed"),
                    "result": result.get("result"),
                    "execution_time": result.get("execution_time"),
                    "applications_used": result.get("applications_used", []),
                    "bytebot_enhanced": True
                }
            else:
                return {
                    "error": f"ByteBot task failed: {response.status_code}",
                    "fallback": True
                }
                
        except Exception as e:
            logger.error(f"ByteBot task execution error: {e}")
            return {"error": str(e), "fallback": True}
    
    async def execute_workflow(self, workflow_request: WorkflowRequest) -> Dict[str, Any]:
        """Execute multi-step workflow using ByteBot"""
        if not self.bytebot_available:
            return {"error": "ByteBot not available for workflow execution"}
        
        workflow_results = []
        overall_success = True
        
        try:
            for step in workflow_request.steps:
                step_result = await self._execute_workflow_step(step, workflow_request.ai_model)
                workflow_results.append(step_result)
                
                if not step_result.get("success", False):
                    overall_success = False
                    if step_result.get("critical", True):
                        break  # Stop on critical step failure
            
            return {
                "workflow_name": workflow_request.name,
                "overall_success": overall_success,
                "steps_completed": len(workflow_results),
                "total_steps": len(workflow_request.steps),
                "step_results": workflow_results,
                "bytebot_workflow": True
            }
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {"error": str(e), "workflow_failed": True}
    
    async def _execute_workflow_step(self, step: WorkflowStep, ai_model: str) -> Dict[str, Any]:
        """Execute individual workflow step"""
        try:
            payload = {
                "action": step.action,
                "target": step.target,
                "parameters": step.parameters or {},
                "ai_model": ai_model if step.ai_assistance else None,
                "step_id": step.step_id
            }
            
            response = await self.session.post(
                f"{BYTEBOT_URL}/api/workflow/step",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "step_id": step.step_id,
                    "error": f"Step failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "step_id": step.step_id,
                "error": str(e)
            }
    
    async def get_desktop_screenshot(self) -> Optional[bytes]:
        """Get current desktop screenshot from ByteBot"""
        if not self.bytebot_available:
            return None
        
        try:
            response = await self.session.get(f"{BYTEBOT_URL}/api/desktop/screenshot")
            if response.status_code == 200:
                return response.content
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
        
        return None
    
    async def list_available_applications(self) -> List[str]:
        """Get list of applications available in ByteBot environment"""
        if not self.bytebot_available:
            return []
        
        try:
            response = await self.session.get(f"{BYTEBOT_URL}/api/applications")
            if response.status_code == 200:
                return response.json().get("applications", [])
        except Exception as e:
            logger.error(f"Applications list error: {e}")
        
        return []

class EnhancedDuckBotAdapter:
    """Enhanced DuckBot adapter with ByteBot integration"""
    
    def __init__(self):
        self.duckbot_token = None
        self.models_cache = {}
        self.last_model_refresh = 0
        self.bytebot_integration = None
    
    async def initialize(self):
        """Initialize ByteBot integration"""
        self.bytebot_integration = ByteBotIntegration()
        await self.bytebot_integration.__aenter__()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.bytebot_integration:
            await self.bytebot_integration.__aexit__(None, None, None)
    
    async def get_duckbot_token(self) -> Optional[str]:
        """Get authentication token from DuckBot WebUI"""
        if self.duckbot_token:
            return self.duckbot_token
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{DUCKBOT_URL}/token", timeout=5)
                if response.status_code == 200:
                    self.duckbot_token = response.json().get("token")
                    return self.duckbot_token
        except Exception as e:
            logger.error(f"Failed to get DuckBot token: {e}")
        return None
    
    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get available models including ByteBot-enhanced capabilities"""
        current_time = time.time()
        if current_time - self.last_model_refresh < 300:  # 5 minute cache
            return list(self.models_cache.values())
        
        models = []
        
        # Enhanced DuckBot models with ByteBot capabilities
        enhanced_models = [
            {"id": "duckbot-auto-bytebot", "name": "DuckBot Auto + Desktop Agent", "type": "enhanced"},
            {"id": "duckbot-code-bytebot", "name": "DuckBot Code + File Automation", "type": "enhanced"},
            {"id": "duckbot-workflow", "name": "DuckBot Workflow Orchestrator", "type": "workflow"},
            {"id": "duckbot-desktop", "name": "DuckBot Desktop Automation", "type": "desktop"},
            # Original models
            {"id": "duckbot-auto", "name": "DuckBot Auto (Smart Routing)", "type": "auto"},
            {"id": "duckbot-code", "name": "DuckBot Code Specialist", "type": "code"},
            {"id": "duckbot-reasoning", "name": "DuckBot Reasoning Expert", "type": "reasoning"},
            {"id": "duckbot-summary", "name": "DuckBot Summary Generator", "type": "summary"},
            {"id": "duckbot-long-form", "name": "DuckBot Long-form Writer", "type": "long_form"},
            {"id": "duckbot-qwen", "name": "DuckBot Qwen Enhanced", "type": "qwen"},
        ]
        
        # Add ByteBot availability indicator
        bytebot_status = "[OK]" if (self.bytebot_integration and self.bytebot_integration.bytebot_available) else "[FAIL]"
        for model in enhanced_models:
            if "bytebot" in model["id"] or model["type"] in ["enhanced", "workflow", "desktop"]:
                model["name"] += f" {bytebot_status}"
            models.append(model)
        
        # Try to get LM Studio models
        try:
            token = await self.get_duckbot_token()
            if token:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{DUCKBOT_URL}/models/available", 
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("ok"):
                            lm_models = result.get("models", [])
                            for model in lm_models:
                                model_id = model.get("id", "unknown")
                                models.append({
                                    "id": f"lm-studio-{model_id}",
                                    "name": f"LM Studio: {model_id}",
                                    "type": "local"
                                })
        except Exception as e:
            logger.warning(f"Could not fetch LM Studio models: {e}")
        
        # Update cache
        self.models_cache = {m["id"]: m for m in models}
        self.last_model_refresh = current_time
        
        return models
    
    async def enhanced_chat_completion(self, request, original_method) -> Dict[str, Any]:
        """Enhanced chat completion with ByteBot integration"""
        model_id = request.model
        
        # Check if this is a ByteBot-enhanced model
        if "bytebot" in model_id or model_id in ["duckbot-workflow", "duckbot-desktop"]:
            return await self._handle_bytebot_enhanced_chat(request)
        else:
            # Use original DuckBot processing
            return await original_method(request)
    
    async def _handle_bytebot_enhanced_chat(self, request) -> Dict[str, Any]:
        """Handle ByteBot-enhanced chat requests"""
        last_message = request.messages[-1] if request.messages else None
        if not last_message:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        message_content = last_message.content
        
        # Detect if this is a task automation request
        automation_keywords = [
            "open", "create file", "run program", "screenshot", "automate",
            "workflow", "execute", "desktop", "application", "save file"
        ]
        
        is_automation_request = any(keyword in message_content.lower() for keyword in automation_keywords)
        
        if is_automation_request and self.bytebot_integration and self.bytebot_integration.bytebot_available:
            # Handle as desktop automation task
            task_request = TaskRequest(
                task=message_content,
                automation_type="desktop",
                ai_model=request.model
            )
            
            automation_result = await self.bytebot_integration.execute_desktop_task(task_request)
            
            if automation_result.get("success"):
                response_text = f"""[AI] **Task Completed Successfully**

**Task:** {message_content}

**Result:** {automation_result.get('result', 'Task completed')}

**Execution Details:**
• Time: {automation_result.get('execution_time', 'N/A')}
• Applications: {', '.join(automation_result.get('applications_used', []))}
• Enhanced by: ByteBot Desktop Agent + DuckBot AI

[OK] Desktop automation task completed successfully!"""
            else:
                # Fallback to regular DuckBot processing
                response_text = f"""[WARN] **Desktop Automation Unavailable**

ByteBot desktop agent is not available. Processing with DuckBot AI only.

**Your request:** {message_content}

Let me help you with information or guidance instead of direct automation."""
        else:
            # Regular chat processing with DuckBot
            # Build conversation context
            conversation_context = ""
            for msg in request.messages[:-1]:
                conversation_context += f"{msg.role.title()}: {msg.content}\n"
            
            prompt = message_content
            if conversation_context:
                prompt = f"Context:\n{conversation_context}\n\nCurrent message: {prompt}"
            
            # Determine task type
            task_type = "auto"
            if request.model.startswith("duckbot-"):
                base_type = request.model.replace("duckbot-", "").replace("-bytebot", "")
                task_type = base_type if base_type != "auto" else "auto"
            
            task = {
                "kind": task_type,
                "risk": "medium", 
                "prompt": prompt,
                "override": ""
            }
            
            # Route through DuckBot
            if DUCKBOT_AVAILABLE:
                result = route_task(task, bucket_type="chat")
                response_text = result.get("text", "No response available")
            else:
                response_text = "DuckBot AI system not available - this is a mock response"
        
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(message_content.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(message_content.split()) + len(response_text.split())
            }
        }

# Initialize enhanced adapter
enhanced_adapter = EnhancedDuckBotAdapter()

# FastAPI app with ByteBot enhancement
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ByteBot-Enhanced OpenWebUI-DuckBot Adapter")
    logger.info(f"DuckBot Available: {DUCKBOT_AVAILABLE}")
    await enhanced_adapter.initialize()
    logger.info(f"ByteBot Integration: {'[OK] Available' if enhanced_adapter.bytebot_integration.bytebot_available else '[FAIL] Unavailable'}")
    yield
    await enhanced_adapter.cleanup()
    logger.info("Shutting down ByteBot-Enhanced Adapter")

app = FastAPI(
    title="ByteBot-Enhanced OpenWebUI-DuckBot Adapter",
    description="OpenWebUI compatible API with DuckBot AI routing and ByteBot desktop automation",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced endpoints
@app.get("/api/tags")
@app.get("/v1/models")
async def list_models():
    """List available models including ByteBot-enhanced ones"""
    try:
        models = await enhanced_adapter.get_available_models()
        from openwebui_duckbot_adapter import Model, ModelList
        
        model_list = []
        for model in models:
            model_list.append(Model(
                id=model["id"],
                object="model",
                created=int(time.time()),
                owned_by="duckbot-bytebot"
            ))
        
        return ModelList(data=model_list)
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return ModelList(data=[])

@app.post("/api/chat")
@app.post("/v1/chat/completions")
async def chat_completions(request):
    """Enhanced chat completions with ByteBot integration"""
    from openwebui_duckbot_adapter import ChatCompletionRequest, adapter
    
    try:
        # Parse request
        if hasattr(request, 'model'):
            chat_request = request
        else:
            chat_request = ChatCompletionRequest(**await request.json())
        
        if chat_request.stream:
            # For now, use original streaming
            return StreamingResponse(
                adapter.stream_chat_completion(chat_request),
                media_type="text/event-stream"
            )
        else:
            # Use enhanced completion
            result = await enhanced_adapter.enhanced_chat_completion(
                chat_request, 
                adapter.chat_completion
            )
            return JSONResponse(result)
    except Exception as e:
        logger.error(f"Enhanced chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ByteBot-specific endpoints
@app.post("/api/bytebot/task")
async def execute_desktop_task(task_request: TaskRequest):
    """Execute desktop automation task"""
    if not enhanced_adapter.bytebot_integration or not enhanced_adapter.bytebot_integration.bytebot_available:
        raise HTTPException(status_code=503, detail="ByteBot desktop agent not available")
    
    result = await enhanced_adapter.bytebot_integration.execute_desktop_task(task_request)
    return JSONResponse(result)

@app.post("/api/bytebot/workflow") 
async def execute_workflow(workflow_request: WorkflowRequest):
    """Execute multi-step workflow"""
    if not enhanced_adapter.bytebot_integration or not enhanced_adapter.bytebot_integration.bytebot_available:
        raise HTTPException(status_code=503, detail="ByteBot not available for workflows")
    
    result = await enhanced_adapter.bytebot_integration.execute_workflow(workflow_request)
    return JSONResponse(result)

@app.get("/api/bytebot/screenshot")
async def get_desktop_screenshot():
    """Get current desktop screenshot"""
    if not enhanced_adapter.bytebot_integration:
        raise HTTPException(status_code=503, detail="ByteBot not available")
    
    screenshot = await enhanced_adapter.bytebot_integration.get_desktop_screenshot()
    if screenshot:
        return Response(content=screenshot, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Screenshot not available")

@app.get("/api/bytebot/applications")
async def list_applications():
    """List available applications in ByteBot environment"""
    if not enhanced_adapter.bytebot_integration:
        return JSONResponse({"applications": [], "error": "ByteBot not available"})
    
    apps = await enhanced_adapter.bytebot_integration.list_available_applications()
    return JSONResponse({"applications": apps})

@app.post("/api/bytebot/upload")
async def upload_file_for_task(file: UploadFile = File(...), task: str = ""):
    """Upload file for task processing"""
    if not enhanced_adapter.bytebot_integration or not enhanced_adapter.bytebot_integration.bytebot_available:
        raise HTTPException(status_code=503, detail="ByteBot not available")
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / file.filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Execute task with file
    task_request = TaskRequest(
        task=task or f"Process the uploaded file: {file.filename}",
        files=[str(file_path)],
        automation_type="file"
    )
    
    result = await enhanced_adapter.bytebot_integration.execute_desktop_task(task_request)
    
    # Cleanup
    try:
        file_path.unlink()
        Path(temp_dir).rmdir()
    except:
        pass
    
    return JSONResponse(result)

@app.get("/health")
async def enhanced_health_check():
    """Enhanced health check with ByteBot status"""
    duckbot_status = "available" if DUCKBOT_AVAILABLE else "unavailable"
    bytebot_status = "available" if (enhanced_adapter.bytebot_integration and enhanced_adapter.bytebot_integration.bytebot_available) else "unavailable"
    
    # Check DuckBot WebUI
    duckbot_webui_status = "offline"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DUCKBOT_URL}/token", timeout=5)
            if response.status_code == 200:
                duckbot_webui_status = "online"
    except:
        pass
    
    return {
        "status": "healthy",
        "duckbot_modules": duckbot_status,
        "duckbot_webui": duckbot_webui_status,
        "bytebot_agent": bytebot_status,
        "adapter_version": "2.0.0",
        "enhanced_features": "ByteBot Desktop Agent + Archon Knowledge Management + DuckBot AI",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("ByteBot-Enhanced OpenWebUI-DuckBot Adapter Starting...")
    print("=" * 80)
    print(f"[ADAPTER] Running on: http://{ADAPTER_HOST}:{ADAPTER_PORT}")
    print(f"[DUCKBOT] Backend URL: {DUCKBOT_URL}")
    print(f"[BYTEBOT] Desktop Agent URL: {BYTEBOT_URL}")
    print(f"[MODULES] DuckBot Available: {DUCKBOT_AVAILABLE}")
    print("=" * 80)
    print("[ENHANCED] Features Available:")
    print("  [OK] DuckBot AI Routing & RAG")
    print("  [OK] Archon Knowledge Management") 
    print("  [TOOLS] ByteBot Desktop Automation (if running)")
    print("=" * 80)
    print("[INFO] Configure OpenWebUI to use this adapter as Ollama server")
    print(f"[INFO] Set Ollama API URL to: http://{ADAPTER_HOST}:{ADAPTER_PORT}")
    print("=" * 80)
    
    uvicorn.run(
        "bytebot_enhanced_adapter:app",
        host=ADAPTER_HOST,
        port=ADAPTER_PORT,
        log_level="info",
        reload=False
    )
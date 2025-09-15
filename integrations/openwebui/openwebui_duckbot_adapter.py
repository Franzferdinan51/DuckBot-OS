"OpenWebUI-DuckBot API Adapter
Provides OpenWebUI-compatible API endpoints that use DuckBot's AI routing system as backend
Includes advanced features inspired by Archon for enhanced functionality
"

import os
import json
import asyncio
import logging
import time
import sqlite3
from typing import Dict, List, Optional, AsyncGenerator, Any
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
import httpx
import shutil

# Import DuckBot's AI router
try:
    from duckbot.ai_router_gpt import route_task, get_router_state, enhanced_chat_completion, pause_agent, resume_agent
    from duckbot.rag import search_rag, index_stats, add_document, add_website
    from duckbot.cost_tracker import get_cost_summary
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    logging.error("DuckBot modules not available - adapter will run in mock mode")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openwebui_adapter")

# Configuration
DUCKBOT_URL = "http://localhost:8787"
ADAPTER_PORT = 11434  # Ollama default port for compatibility
ADAPTER_HOST = "127.0.0.1"
DB_PATH = "ecosystem_state.db"
KNOWLEDGE_BASE_DIR = "knowledge_base"

# Create knowledge base directory if it doesn't exist
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
os.makedirs(os.path.join(KNOWLEDGE_BASE_DIR, "files"), exist_ok=True)

# Database connection
def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

# Pydantic models for Task Management
class Project(BaseModel):
    id: int
    name: str
    created_at: datetime

class Task(BaseModel):
    id: int
    project_id: int
    title: str
    status: str
    created_at: datetime

class ProjectCreate(BaseModel):
    name: str

class TaskCreate(BaseModel):
    project_id: int
    title: str

class TaskUpdate(BaseModel):
    status: str

class WebsiteCrawlRequest(BaseModel):
    url: str

# OpenWebUI compatible models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional message sender name")

class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, description="Nucleus sampling parameter")
    max_tokens: Optional[int] = Field(2048, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Stream the response")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")

class Model(BaseModel):
    id: str = Field(..., description="Model identifier")
    object: str = Field(default="model", description="Object type")
    created: int = Field(default_factory=lambda: int(time.time()), description="Creation timestamp")
    owned_by: str = Field(default="duckbot", description="Owner of the model")

class ModelList(BaseModel):
    object: str = Field(default="list", description="Object type")
    data: List[Model] = Field(..., description="List of available models")

class DuckBotAdapter:
    """Main adapter class that bridges OpenWebUI and DuckBot"""
    
    def __init__(self):
        self.duckbot_token = None
        self.models_cache = {}
        self.last_model_refresh = 0
        
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
        """Get available models from DuckBot with caching"""
        current_time = time.time()
        if current_time - self.last_model_refresh < 300:  # 5 minute cache
            return list(self.models_cache.values())
        
        models = []
        
        # DuckBot built-in models
        duckbot_models = [
            {"id": "duckbot-auto", "name": "DuckBot Auto (Smart Routing)", "type": "auto"},
            {"id": "duckbot-code", "name": "DuckBot Code Specialist", "type": "code"},
            {"id": "duckbot-reasoning", "name": "DuckBot Reasoning Expert", "type": "reasoning"},
            {"id": "duckbot-summary", "name": "DuckBot Summary Generator", "type": "summary"},
            {"id": "duckbot-long-form", "name": "DuckBot Long-form Writer", "type": "long_form"},
            {"id": "duckbot-qwen", "name": "DuckBot Qwen Enhanced", "type": "qwen"},
        ]
        
        for model in duckbot_models:
            models.append(model)
        
        # Try to get LM Studio models if available
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
    
    async def chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Handle chat completion using DuckBot's AI router"""
        try:
            # Convert OpenWebUI format to DuckBot format
            last_message = request.messages[-1] if request.messages else None
            if not last_message:
                raise HTTPException(status_code=400, detail="No messages provided")
            
            # Determine task type from model
            task_type = "auto"
            if request.model.startswith("duckbot-"):
                task_type = request.model.replace("duckbot-", "")
                if task_type == "auto":
                    task_type = "auto"
            elif request.model.startswith("lm-studio-"):
                task_type = "local"
            
            # Build conversation context
            conversation_context = ""
            for msg in request.messages[:-1]:  # All but the last message
                conversation_context += f"{msg.role.title()}: {msg.content}\n"
            
            # Prepare DuckBot task
            prompt = last_message.content
            if conversation_context:
                prompt = f"Context:\n{conversation_context}\n\nCurrent message: {prompt}"
            
            task = {
                "kind": task_type,
                "risk": "medium",
                "prompt": prompt,
                "override": ""
            }
            
            # Route through DuckBot
            if DUCKBOT_AVAILABLE:
                result = route_task(task, bucket_type="chat")
            else:
                # Mock response for testing
                result = {
                    "text": "DuckBot AI system not available - this is a mock response",
                    "model_used": "mock",
                    "confidence": 0.5,
                    "cached": False
                }
            
            # Convert back to OpenWebUI format
            response_text = result.get("text", "No response available")
            model_used = result.get("model_used", request.model)
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_used,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(prompt.split()) + len(response_text.split())
                }
            }
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stream_chat_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """Handle streaming chat completion"""
        try:
            if not DUCKBOT_AVAILABLE:
                yield f"data: {json.dumps({'error': {'message': 'DuckBot not available', 'type': 'adapter_error'}})}\n\n"
                return

            # Use the enhanced_chat_completion with streaming
            async for chunk in enhanced_chat_completion(request.messages, stream=True):
                if chunk["type"] == "error":
                    error_chunk = {"error": {"message": chunk["data"], "type": "model_error"}}
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    break
                
                if chunk["type"] == "thought":
                    thought_chunk = {"thought": chunk["data"]}
                    yield f"event: thought\ndata: {json.dumps(thought_chunk)}\n\n"
                    continue

                response_chunk = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": chunk["data"]},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(response_chunk)}\n\n"

            # Final chunk
            final_chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "adapter_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

# Initialize adapter
adapter = DuckBotAdapter()

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OpenWebUI-DuckBot Adapter")
    logger.info(f"DuckBot Available: {DUCKBOT_AVAILABLE}")
    yield
    logger.info("Shutting down OpenWebUI-DuckBot Adapter")

app = FastAPI(
    title="OpenWebUI-DuckBot Adapter",
    description="OpenWebUI compatible API using DuckBot's AI routing system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for OpenWebUI compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/tags")
@app.get("/v1/models")
async def list_models():
    """List available models in OpenWebUI/Ollama format"""
    try:
        models = await adapter.get_available_models()
        model_list = []
        
        for model in models:
            model_list.append(Model(
                id=model["id"],
                object="model",
                created=int(time.time()),
                owned_by="duckbot"
            ))
        
        return ModelList(data=model_list)
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return ModelList(data=[])

@app.post("/api/chat")
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Handle chat completions"""
    try:
        if request.stream:
            return StreamingResponse(
                adapter.stream_chat_completion(request),
                media_type="text/event-stream"
            )
        else:
            result = await adapter.chat_completion(request)
            return JSONResponse(result)
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/show/{model_name}")
async def show_model(model_name: str):
    """Show model information"""
    models = await adapter.get_available_models()
    model = next((m for m in models if m["id"] == model_name), None)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "modelfile": f"# {model['name']}\n# DuckBot AI Model\n",
        "parameters": {},
        "template": "{{ .Prompt }}",
        "details": {
            "parent_model": "",
            "format": "duckbot",
            "family": "duckbot",
            "families": ["duckbot"],
            "parameter_size": "unknown",
            "quantization_level": "unknown"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    duckbot_status = "available" if DUCKBOT_AVAILABLE else "unavailable"
    
    # Try to ping DuckBot WebUI
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
        "adapter_version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/version")
async def version():
    """Version information"""
    return {
        "version": "1.0.0",
        "adapter": "OpenWebUI-DuckBot",
        "duckbot_available": DUCKBOT_AVAILABLE
    }

# Task Management API
@app.get("/api/projects", response_model=List[Project])
async def get_projects(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, name, created_at FROM projects ORDER BY created_at DESC")
    projects = cursor.fetchall()
    return projects

@app.post("/api/projects", response_model=Project)
async def create_project(project: ProjectCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("INSERT INTO projects (name) VALUES (?)", (project.name,))
    db.commit()
    project_id = cursor.lastrowid
    cursor.execute("SELECT id, name, created_at FROM projects WHERE id = ?", (project_id,))
    new_project = cursor.fetchone()
    return new_project

@app.get("/api/projects/{project_id}/tasks", response_model=List[Task])
async def get_tasks(project_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, project_id, title, status, created_at FROM tasks WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    tasks = cursor.fetchall()
    return tasks

@app.post("/api/tasks", response_model=Task)
async def create_task(task: TaskCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("INSERT INTO tasks (project_id, title) VALUES (?, ?)", (task.project_id, task.title))
    db.commit()
    task_id = cursor.lastrowid
    cursor.execute("SELECT id, project_id, title, status, created_at FROM tasks WHERE id = ?", (task_id,))
    new_task = cursor.fetchone()
    return new_task

@app.put("/api/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: TaskUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (task.status, task_id))
    db.commit()
    cursor.execute("SELECT id, project_id, title, status, created_at FROM tasks WHERE id = ?", (task_id,))
    updated_task = cursor.fetchone()
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

# Knowledge Base API
@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(KNOWLEDGE_BASE_DIR, "files", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Add the document to the RAG index
    if DUCKBOT_AVAILABLE:
        try:
            add_document(file_path)
        except Exception as e:
            logger.error(f"Error adding document to RAG: {e}")
            raise HTTPException(status_code=500, detail="Error adding document to RAG")

    return {"filename": file.filename, "status": "uploaded"}

@app.get("/api/files")
async def get_files():
    files = []
    for filename in os.listdir(os.path.join(KNOWLEDGE_BASE_DIR, "files")):
        files.append({"name": filename})
    return files

@app.post("/api/rag/crawl")
async def crawl_website(request: WebsiteCrawlRequest):
    if DUCKBOT_AVAILABLE:
        try:
            add_website(request.url)
        except Exception as e:
            logger.error(f"Error crawling website: {e}")
            raise HTTPException(status_code=500, detail="Error crawling website")
    return {"url": request.url, "status": "crawling_started"}

# Agent Control API
@app.post("/api/agent/pause")
async def pause_agent_endpoint():
    if DUCKBOT_AVAILABLE:
        pause_agent()
        return {"status": "paused"}
    else:
        raise HTTPException(status_code=503, detail="DuckBot not available")

@app.post("/api/agent/resume")
async def resume_agent_endpoint():
    if DUCKBOT_AVAILABLE:
        resume_agent()
        return {"status": "resumed"}
    else:
        raise HTTPException(status_code=503, detail="DuckBot not available")

# Advanced features inspired by Archon

@app.post("/api/duckbot/rag/search")
async def rag_search(query: str, top_k: int = 5):
    """RAG search using DuckBot's knowledge base"""
    try:
        token = await adapter.get_duckbot_token()
        if not token:
            raise HTTPException(status_code=503, detail="DuckBot not available")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DUCKBOT_URL}/rag/search",
                headers={"Authorization": f"Bearer {token}"},
                data={"q": query, "top_k": top_k},
                timeout=20
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="RAG search failed")
                
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/duckbot/status")
async def duckbot_status():
    """Get comprehensive DuckBot system status"""
    try:
        token = await adapter.get_duckbot_token()
        if not token:
            raise HTTPException(status_code=503, detail="DuckBot not available")
        
        status_data = {}
        
        # Get AI status
        async with httpx.AsyncClient() as client:
            ai_response = await client.get(
                f"{DUCKBOT_URL}/api/system-status",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if ai_response.status_code == 200:
                status_data["ai_system"] = ai_response.json()
            
            # Get services status
            services_response = await client.get(
                f"{DUCKBOT_URL}/api/services",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if services_response.status_code == 200:
                status_data["services"] = services_response.json()
        
        return status_data
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/duckbot/analyze")
async def analyze_code(code: str):
    """Code analysis using DuckBot's Qwen system"""
    try:
        token = await adapter.get_duckbot_token()
        if not token:
            raise HTTPException(status_code=503, detail="DuckBot not available")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DUCKBOT_URL}/qwen/analyze",
                headers={"Authorization": f"Bearer {token}"},
                data={"code_prompt": code},
                timeout=45
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Code analysis failed")
                
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("OpenWebUI-DuckBot Adapter Starting...")
    print("=" * 70)
    print(f"[ADAPTER] Running on: http://{ADAPTER_HOST}:{ADAPTER_PORT}")
    print(f"[DUCKBOT] Backend URL: {DUCKBOT_URL}")
    print(f"[MODULES] DuckBot Available: {DUCKBOT_AVAILABLE}")
    print("=" * 70)
    print("[INFO] Configure OpenWebUI to use this adapter as Ollama server")
    print(f"[INFO] Set Ollama API URL to: http://{ADAPTER_HOST}:{ADAPTER_PORT}")
    print("=" * 70)
    
    uvicorn.run(
        "openwebui_duckbot_adapter:app",
        host=ADAPTER_HOST,
        port=ADAPTER_PORT,
        log_level="info",
        reload=False
    )

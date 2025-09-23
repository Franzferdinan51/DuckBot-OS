#!/usr/bin/env python3
"""
Qwen3-Omni Web Server - OpenAI-compatible API
Provides HTTP API for Qwen3-Omni brain integration
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime

import sys
import os
sys.path.append(os.getcwd())

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from duckbot.core.qwen3_omni_integration import qwen3_omni_integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Qwen3-Omni API", version="1.0.0")

# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "qwen3-omni"
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    load_time: Optional[float] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        status = qwen3_omni_integration.get_status()
        return HealthResponse(
            status="healthy" if status["available"] else "loading",
            model_loaded=status["available"],
            device=status.get("device", "unknown"),
            load_time=status.get("load_time")
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            model_loaded=False,
            device="unknown"
        )

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint"""

    # Check if model is loaded
    status = qwen3_omni_integration.get_status()
    if not status["available"]:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        # Convert messages to Qwen3-Omni format
        conversation = []
        for msg in request.messages:
            if msg.role == "system":
                conversation.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                conversation.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                conversation.append({"role": "assistant", "content": msg.content})

        # Generate response
        if request.stream:
            return StreamingResponse(
                stream_chat_completion(conversation, request.model),
                media_type="text/plain"
            )
        else:
            # Non-streaming response
            start_time = time.time()
            # Convert conversation to a single prompt string
            prompt = ""
            for msg in conversation:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    prompt += f"Assistant: {msg['content']}\n"

            # Generate response using the correct method
            response = await qwen3_omni_integration.generate_text(prompt)
            response_text = response.text

            response_time = time.time() - start_time

            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex}",
                created=int(time.time()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": len(str(conversation)),
                    "completion_tokens": len(response_text),
                    "total_tokens": len(str(conversation)) + len(response_text)
                }
            )

    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def stream_chat_completion(conversation: List[Dict], model: str) -> AsyncGenerator[str, None]:
    """Stream chat completion response"""
    try:
        # For streaming, we'll simulate chunks by generating the full response
        # and then yielding it in chunks
        # Convert conversation to a single prompt string
        prompt = ""
        for msg in conversation:
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n"
            elif msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n"

        # Generate response using the correct method
        response = await qwen3_omni_integration.generate_text(prompt)
        response_text = response.text

        # Split response into chunks for streaming
        words = response_text.split()
        current_chunk = ""

        for word in words:
            current_chunk += word + " "
            if len(current_chunk) > 20:  # Send chunks of roughly 20 characters
                chunk_data = {
                    "id": f"chatcmpl-{uuid.uuid4().hex}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": current_chunk},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                current_chunk = ""

        # Send remaining chunk
        if current_chunk:
            chunk_data = {
                "id": f"chatcmpl-{uuid.uuid4().hex}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": current_chunk},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"

        # Send final chunk
        final_chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Qwen3-Omni API Server",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "POST /v1/chat/completions - OpenAI-compatible chat completion",
            "GET / - This info page"
        ]
    }

if __name__ == "__main__":
    # Start the server
    logger.info("Starting Qwen3-Omni API server...")
    logger.info("Server will be available at: http://localhost:5000")

    # Check if model is loaded
    status = qwen3_omni_integration.get_status()
    if not status["available"]:
        logger.warning("Model is not loaded yet. The brain should be started first.")

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
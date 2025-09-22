"""
RealtimeVoiceChat - Real-time voice conversation system with AI integration
Supports multiple AI providers: LM Studio, OpenRouter, Gemini, DuckBot
"""
import asyncio
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import time
import wave
import numpy as np
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import aiohttp
import aiofiles

# Import AI providers
import openai
import google.generativeai as genai
from ..core.ai_router_gpt import AI_ROUTER_GPT
from ..integrations.vibevoice_client import vibevoice_integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RealtimeVoiceChat", version="1.0.0")

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_data[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "ai_provider": "lm_studio",
            "voice_profile": "en-alice",
            "conversation_history": [],
            "is_listening": False,
            "current_task": None
        }
        logger.info(f"Client connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]
        logger.info(f"Client disconnected: {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.session_data.get(session_id)

    def update_session_data(self, session_id: str, data: Dict[str, Any]):
        if session_id in self.session_data:
            self.session_data[session_id].update(data)

manager = ConnectionManager()

# AI Provider configurations
AI_PROVIDERS = {
    "lm_studio": {
        "api_url": "http://localhost:1234",
        "model": "local",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "openrouter": {
        "api_url": "https://openrouter.ai/api/v1",
        "model": "anthropic/claude-3.5-sonnet",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "gemini": {
        "api_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-pro",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "duckbot": {
        "api_url": "local",
        "model": "duckbot",
        "max_tokens": 2000,
        "temperature": 0.7
    }
}

# Voice profiles
VOICE_PROFILES = {
    "en-alice": {"name": "Alice", "gender": "female", "pitch": 0.0, "speed": 1.0},
    "en-carter": {"name": "Carter", "gender": "male", "pitch": -2.0, "speed": 1.0},
    "en-david": {"name": "David", "gender": "male", "pitch": 1.0, "speed": 0.9},
    "en-emily": {"name": "Emily", "gender": "female", "pitch": 1.5, "speed": 1.1}
}

class ChatMessage(BaseModel):
    """Message model for chat"""
    session_id: str
    text: str
    voice_profile: str = "en-alice"
    ai_provider: str = "lm_studio"

class AudioChunk(BaseModel):
    """Audio chunk model"""
    session_id: str
    audio_data: str  # base64 encoded
    sample_rate: int = 16000
    channels: int = 1

class VoiceSettings(BaseModel):
    """Voice settings model"""
    session_id: str
    voice_profile: str
    ai_provider: str
    settings: Dict[str, Any]

class AIProvider:
    """Base class for AI providers"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def generate_response(self, text: str, conversation_history: List[Dict[str, str]]) -> str:
        raise NotImplementedError

class LMStudioProvider(AIProvider):
    """LM Studio AI provider"""
    async def generate_response(self, text: str, conversation_history: List[Dict[str, str]]) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare conversation context
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant engaged in voice conversation. Keep responses concise and natural for speech."}
                ]

                # Add conversation history
                for msg in conversation_history[-5:]:  # Last 5 messages
                    messages.append({"role": msg["role"], "content": msg["content"]})

                messages.append({"role": "user", "content": text})

                async with session.post(
                    f"{self.config['api_url']}/v1/chat/completions",
                    json={
                        "model": self.config["model"],
                        "messages": messages,
                        "max_tokens": self.config["max_tokens"],
                        "temperature": self.config["temperature"],
                        "stream": False
                    },
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"LM Studio error: {response.status} - {error_text}")
                        return "I'm having trouble connecting to my local AI service."

        except Exception as e:
            logger.error(f"LM Studio provider error: {e}")
            return "I'm experiencing technical difficulties with my local AI service."

class OpenRouterProvider(AIProvider):
    """OpenRouter AI provider"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def generate_response(self, text: str, conversation_history: List[Dict[str, str]]) -> str:
        try:
            # Prepare conversation context
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant engaged in voice conversation. Keep responses concise and natural for speech."}
            ]

            # Add conversation history
            for msg in conversation_history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            messages.append({"role": "user", "content": text})

            response = await self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"]
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenRouter provider error: {e}")
            return "I'm having trouble connecting to my AI service."

class GeminiProvider(AIProvider):
    """Google Gemini AI provider"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_response(self, text: str, conversation_history: List[Dict[str, str]]) -> str:
        try:
            # Build conversation context
            context = "You are a helpful AI assistant engaged in voice conversation. Keep responses concise and natural for speech.\n\n"

            for msg in conversation_history[-5:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                context += f"{role}: {msg['content']}\n"

            context += f"User: {text}\nAssistant:"

            response = await asyncio.to_thread(self.model.generate_content, context)
            return response.text

        except Exception as e:
            logger.error(f"Gemini provider error: {e}")
            return "I'm experiencing technical difficulties with my AI service."

class DuckBotProvider(AIProvider):
    """DuckBot AI provider"""
    async def generate_response(self, text: str, conversation_history: List[Dict[str, str]]) -> str:
        try:
            # Use existing DuckBot AI router
            response = await AI_ROUTER_GPT.generate_response(
                text,
                context=conversation_history,
                mode="voice_chat"
            )
            return response

        except Exception as e:
            logger.error(f"DuckBot provider error: {e}")
            return "I'm having trouble with my internal systems."

def get_ai_provider(provider_name: str) -> AIProvider:
    """Get AI provider instance"""
    if provider_name == "lm_studio":
        return LMStudioProvider(AI_PROVIDERS["lm_studio"])
    elif provider_name == "openrouter":
        return OpenRouterProvider(AI_PROVIDERS["openrouter"])
    elif provider_name == "gemini":
        return GeminiProvider(AI_PROVIDERS["gemini"])
    elif provider_name == "duckbot":
        return DuckBotProvider(AI_PROVIDERS["duckbot"])
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")

async def process_voice_message(session_id: str, text: str, voice_profile: str, ai_provider: str):
    """Process voice message and generate response"""
    try:
        session_data = manager.get_session_data(session_id)
        if not session_data:
            return

        # Send processing status
        await manager.send_message(session_id, {
            "type": "processing",
            "message": "Processing your message..."
        })

        # Get AI provider
        provider = get_ai_provider(ai_provider)

        # Generate AI response
        conversation_history = session_data.get("conversation_history", [])
        response_text = await provider.generate_response(text, conversation_history)

        # Update conversation history
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": response_text})
        manager.update_session_data(session_id, {"conversation_history": conversation_history})

        # Send text response
        await manager.send_message(session_id, {
            "type": "text_response",
            "text": response_text,
            "voice_profile": voice_profile
        })

        # Generate voice response using VibeVoice
        if vibevoice_integration.available:
            await manager.send_message(session_id, {
                "type": "generating_voice",
                "message": "Generating voice response..."
            })

            voice_result = await vibevoice_integration.generate_speech(
                text=response_text,
                speakers=[voice_profile]
            )

            if voice_result.get("success"):
                audio_path = voice_result.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    # Read audio file and send as base64
                    async with aiofiles.open(audio_path, 'rb') as f:
                        audio_data = await f.read()

                    await manager.send_message(session_id, {
                        "type": "voice_response",
                        "audio_data": audio_data.hex(),  # Send as hex for simplicity
                        "format": "wav"
                    })

                    # Clean up audio file
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                else:
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": "Voice generation failed"
                    })
            else:
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": "Voice generation unavailable"
                })
        else:
            await manager.send_message(session_id, {
                "type": "error",
                "message": "VibeVoice not available"
            })

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "message": f"Error processing message: {str(e)}"
        })

@app.get("/")
async def get_web_interface():
    """Web interface for RealtimeVoiceChat"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RealtimeVoiceChat</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .chat-log { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 20px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background-color: #e3f2fd; }
            .assistant { background-color: #f3e5f5; }
            .controls { display: flex; gap: 10px; margin-bottom: 20px; }
            button { padding: 10px; background-color: #2196f3; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:disabled { background-color: #ccc; }
            select, input { padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            .status { padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>RealtimeVoiceChat</h1>

            <div class="controls">
                <select id="voiceProfile">
                    <option value="en-alice">Alice (Female)</option>
                    <option value="en-carter">Carter (Male)</option>
                    <option value="en-david">David (Male)</option>
                    <option value="en-emily">Emily (Female)</option>
                </select>

                <select id="aiProvider">
                    <option value="lm_studio">LM Studio</option>
                    <option value="openrouter">OpenRouter</option>
                    <option value="gemini">Gemini</option>
                    <option value="duckbot">DuckBot</option>
                </select>

                <button id="connectBtn">Connect</button>
                <button id="disconnectBtn" disabled>Disconnect</button>
            </div>

            <div id="status" class="status">Not connected</div>

            <div id="chatLog" class="chat-log"></div>

            <div class="controls">
                <input type="text" id="messageInput" placeholder="Type your message..." disabled>
                <button id="sendBtn" disabled>Send</button>
                <button id="listenBtn" disabled>🎤 Listen</button>
            </div>
        </div>

        <script>
            let ws = null;
            let sessionId = null;
            let isListening = false;

            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');
            const sendBtn = document.getElementById('sendBtn');
            const listenBtn = document.getElementById('listenBtn');
            const messageInput = document.getElementById('messageInput');
            const chatLog = document.getElementById('chatLog');
            const status = document.getElementById('status');
            const voiceProfile = document.getElementById('voiceProfile');
            const aiProvider = document.getElementById('aiProvider');

            function addMessage(role, content) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;
                messageDiv.innerHTML = `<strong>${role}:</strong> ${content}`;
                chatLog.appendChild(messageDiv);
                chatLog.scrollTop = chatLog.scrollHeight;
            }

            function updateStatus(message, type = 'info') {
                status.textContent = message;
                status.className = `status ${type}`;
            }

            connectBtn.addEventListener('click', async () => {
                try {
                    // Generate session ID
                    sessionId = 'session_' + Date.now();

                    // Connect WebSocket
                    ws = new WebSocket(`ws://localhost:8001/ws/${sessionId}`);

                    ws.onopen = () => {
                        updateStatus('Connected', 'success');
                        connectBtn.disabled = true;
                        disconnectBtn.disabled = false;
                        sendBtn.disabled = false;
                        listenBtn.disabled = false;
                        messageInput.disabled = false;

                        // Initialize settings
                        ws.send(JSON.stringify({
                            type: 'initialize',
                            voice_profile: voiceProfile.value,
                            ai_provider: aiProvider.value
                        }));
                    };

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);

                        switch(data.type) {
                            case 'text_response':
                                addMessage('Assistant', data.text);
                                break;
                            case 'voice_response':
                                // Play audio response
                                const audioData = new Uint8Array(data.audio_data.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
                                const audioBlob = new Blob([audioData], { type: 'audio/wav' });
                                const audio = new Audio(URL.createObjectURL(audioBlob));
                                audio.play();
                                break;
                            case 'status':
                                updateStatus(data.message);
                                break;
                            case 'error':
                                updateStatus(data.message, 'error');
                                break;
                        }
                    };

                    ws.onclose = () => {
                        updateStatus('Disconnected', 'error');
                        connectBtn.disabled = false;
                        disconnectBtn.disabled = true;
                        sendBtn.disabled = true;
                        listenBtn.disabled = true;
                        messageInput.disabled = true;
                    };

                    ws.onerror = (error) => {
                        updateStatus('Connection error', 'error');
                        console.error('WebSocket error:', error);
                    };

                } catch (error) {
                    updateStatus('Connection failed: ' + error.message, 'error');
                }
            });

            disconnectBtn.addEventListener('click', () => {
                if (ws) {
                    ws.close();
                }
            });

            sendBtn.addEventListener('click', () => {
                const message = messageInput.value.trim();
                if (message && ws) {
                    addMessage('User', message);
                    ws.send(JSON.stringify({
                        type: 'chat',
                        text: message,
                        voice_profile: voiceProfile.value,
                        ai_provider: aiProvider.value
                    }));
                    messageInput.value = '';
                }
            });

            listenBtn.addEventListener('click', () => {
                if (!isListening) {
                    // Start listening (implementation would use Web Audio API)
                    isListening = true;
                    listenBtn.textContent = '🔴 Stop Listening';
                    updateStatus('Listening...', 'info');

                    // Placeholder for speech recognition
                    setTimeout(() => {
                        isListening = false;
                        listenBtn.textContent = '🎤 Listen';
                        updateStatus('Listening stopped', 'info');
                    }, 5000);
                } else {
                    isListening = false;
                    listenBtn.textContent = '🎤 Listen';
                    updateStatus('Listening stopped', 'info');
                }
            });

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendBtn.click();
                }
            });
        </script>
    </body>
    </html>
    """)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "initialize":
                # Initialize session settings
                manager.update_session_data(session_id, {
                    "voice_profile": message.get("voice_profile", "en-alice"),
                    "ai_provider": message.get("ai_provider", "lm_studio")
                })

                await manager.send_message(session_id, {
                    "type": "status",
                    "message": "Session initialized successfully"
                })

            elif message["type"] == "chat":
                # Process chat message
                text = message.get("text", "")
                voice_profile = message.get("voice_profile", "en-alice")
                ai_provider = message.get("ai_provider", "lm_studio")

                # Update session settings
                manager.update_session_data(session_id, {
                    "voice_profile": voice_profile,
                    "ai_provider": ai_provider
                })

                # Process message in background
                asyncio.create_task(
                    process_voice_message(session_id, text, voice_profile, ai_provider)
                )

            elif message["type"] == "settings_update":
                # Update session settings
                manager.update_session_data(session_id, {
                    "voice_profile": message.get("voice_profile", "en-alice"),
                    "ai_provider": message.get("ai_provider", "lm_studio")
                })

                await manager.send_message(session_id, {
                    "type": "status",
                    "message": "Settings updated"
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)

@app.post("/chat")
async def chat_message(message: ChatMessage):
    """REST API endpoint for chat"""
    try:
        # Create session if not exists
        if message.session_id not in manager.session_data:
            manager.session_data[message.session_id] = {
                "connected_at": datetime.now().isoformat(),
                "ai_provider": message.ai_provider,
                "voice_profile": message.voice_profile,
                "conversation_history": []
            }

        # Process message
        asyncio.create_task(
            process_voice_message(
                message.session_id,
                message.text,
                message.voice_profile,
                message.ai_provider
            )
        )

        return {"status": "processing", "session_id": message.session_id}

    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-settings")
async def update_voice_settings(settings: VoiceSettings):
    """Update voice settings"""
    try:
        manager.update_session_data(settings.session_id, {
            "voice_profile": settings.voice_profile,
            "ai_provider": settings.ai_provider
        })

        return {"status": "updated", "session_id": settings.session_id}

    except Exception as e:
        logger.error(f"Voice settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
async def get_providers():
    """Get available AI providers"""
    return {
        "providers": list(AI_PROVIDERS.keys()),
        "voice_profiles": list(VOICE_PROFILES.keys()),
        "default_provider": "lm_studio",
        "default_voice": "en-alice"
    }

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    session_data = manager.get_session_data(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "connected": session_id in manager.active_connections,
        "data": session_data
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RealtimeVoiceChat",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "active_sessions": len(manager.active_connections),
        "available_providers": len(AI_PROVIDERS),
        "vibevoice_available": vibevoice_integration.available
    }

if __name__ == "__main__":
    print("Starting RealtimeVoiceChat server...")
    print("Available AI providers:", list(AI_PROVIDERS.keys()))
    print("Available voice profiles:", list(VOICE_PROFILES.keys()))
    print("Web interface: http://localhost:8001")
    print("WebSocket endpoint: ws://localhost:8001/ws/{session_id}")

    uvicorn.run(app, host="0.0.0.0", port=8001)
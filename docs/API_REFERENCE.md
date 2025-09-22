# DuckBot v4.2 API Reference

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [REST API Endpoints](#rest-api-endpoints)
- [WebSocket API](#websocket-api)
- [GraphQL API](#graphql-api)
- [Python SDK Reference](#python-sdk-reference)
- [Module APIs](#module-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Code Examples](#code-examples)

## Overview

DuckBot v4.2 provides comprehensive REST APIs, WebSocket interfaces, and GraphQL endpoints for integrating with external applications and services. All APIs use JSON for request/response formatting and follow RESTful principles.

### Base URL
- **Local Development**: `http://localhost:8787/api`
- **Production**: `https://your-domain.com/api`

### API Versioning
All API endpoints include version information:
- Current version: `v1`
- Endpoint format: `/api/v1/{resource}`

### Response Format
```json
{
  "success": true,
  "data": {},
  "message": "Success message",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Authentication

### API Key Authentication
```bash
# Include API key in header
curl -X GET "http://localhost:8787/api/v1/status" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json"
```

### JWT Authentication (WebUI)
```bash
# Login to get JWT token
curl -X POST "http://localhost:8787/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Use JWT token
curl -X GET "http://localhost:8787/api/v1/user/profile" \
  -H "Authorization: Bearer your_jwt_token"
```

### WebSocket Authentication
```javascript
// Connect with authentication
const ws = new WebSocket('ws://localhost:8787/ws/v1/chat?token=your_token');
```

## REST API Endpoints

### 1. System Management

#### Get System Status
```http
GET /api/v1/system/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "running",
    "uptime": 86400,
    "version": "4.2.0",
    "mode": "local_only",
    "services": {
      "webui": "running",
      "monitoring": "running",
      "api": "running"
    },
    "resources": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_usage": 23.4,
      "gpu_usage": null
    }
  }
}
```

### 2. AI Model Management

#### List Available Models
```http
GET /api/v1/models/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "phi-3-mini",
        "name": "Phi-3 Mini",
        "size_gb": 2.2,
        "loaded": true,
        "specialty": "general",
        "performance_score": 75
      },
      {
        "id": "qwen3-30b",
        "name": "Qwen3 30B",
        "size_gb": 18.5,
        "loaded": false,
        "specialty": "coding",
        "performance_score": 95
      }
    ]
  }
}
```

#### Load Model
```http
POST /api/v1/models/load
```

**Request:**
```json
{
  "model_id": "qwen3-30b",
  "priority": "high"
}
```

### 3. Multi-Agent Framework

#### Deploy Agent
```http
POST /api/v1/agents/deploy
```

**Request:**
```json
{
  "agent_type": "market_analyzer",
  "task": "Analyze cryptocurrency trends",
  "context": {
    "timeframe": "7d",
    "coins": ["BTC", "ETH"]
  },
  "priority": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "agent_12345",
    "status": "deploying",
    "estimated_time": 30,
    "task_id": "task_67890"
  }
}
```

#### List Active Agents
```http
GET /api/v1/agents/active
```

### 4. Memory & Learning System

#### Store Memory
```http
POST /api/v1/memory/store
```

**Request:**
```json
{
  "problem": "file_permission_error",
  "solution": "chmod +x script.py",
  "confidence": 0.95,
  "tags": ["permissions", "linux", "fix"],
  "context": {
    "environment": "ubuntu",
    "user_id": "user_123"
  }
}
```

#### Search Memory
```http
GET /api/v1/memory/search?query=permission%20denied
```

### 5. Desktop Automation

#### Execute Task
```http
POST /api/v1/automation/execute
```

**Request:**
```json
{
  "task": "Open Notepad and type Hello World",
  "timeout": 300,
  "safe_mode": true,
  "return_screenshot": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "result": "Task completed successfully",
    "execution_time": 5.2,
    "screenshot": "base64_encoded_image",
    "artifacts": {
      "files_created": ["output.txt"]
    }
  }
}
```

### 6. Cross-Platform Operations

#### Execute WSL Command
```http
POST /api/v1/platforms/wsl/execute
```

**Request:**
```json
{
  "command": "ls -la /home",
  "distribution": "Ubuntu-20.04",
  "timeout": 30
}
```

#### List Docker Containers
```http
GET /api/v1/platforms/docker/containers
```

#### Get System Status
```http
GET /api/v1/system/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "running",
    "uptime": 86400,
    "version": "4.2.0",
    "mode": "local_only",
    "services": {
      "webui": "running",
      "monitoring": "running",
      "api": "running"
    },
    "resources": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_usage": 23.4,
      "gpu_usage": null
    }
  }
}
```

#### Get System Configuration
```http
GET /api/v1/system/config
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ai_provider": "lm_studio",
    "lm_studio_url": "http://localhost:1234/v1",
    "max_tokens": 512,
    "temperature": 0.2,
    "features": {
      "comfyui": true,
      "trellis": true,
      "vibevoice": true,
      "mining": false
    }
  }
}
```

#### Update System Configuration
```http
PUT /api/v1/system/config
Content-Type: application/json

{
  "ai_provider": "lm_studio",
  "max_tokens": 1024,
  "temperature": 0.3,
  "features": {
    "comfyui": true,
    "trellis": false,
    "vibevoice": true,
    "mining": false
  }
}
```

### 2. AI Chat and Models

#### Chat with AI
```http
POST /api/v1/chat/completions
Content-Type: application/json

{
  "model": "qwen3-coder",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "chat_123456789",
    "model": "qwen3-coder",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 25,
      "completion_tokens": 18,
      "total_tokens": 43
    }
  }
}
```

#### Stream Chat Response
```http
POST /api/v1/chat/completions
Content-Type: application/json

{
  "model": "qwen3-coder",
  "messages": [
    {"role": "user", "content": "Tell me a story"}
  ],
  "stream": true
}
```

**Streaming Response:**
```
data: {"id": "chat_123", "choices": [{"delta": {"content": "Once"}}]}
data: {"id": "chat_123", "choices": [{"delta": {"content": " upon"}}]}
data: {"id": "chat_123", "choices": [{"delta": {"content": " a"}}]}
data: {"id": "chat_123", "choices": [{"delta": {"content": " time..."}}]}
data: [DONE]
```

#### Get Available Models
```http
GET /api/v1/models
```

**Response:**
```json
{
  "success": true,
  "data": {
    "object": "list",
    "data": [
      {
        "id": "qwen3-coder",
        "name": "Qwen3 Coder 30B",
        "size_gb": 18.5,
        "specialty": "coding",
        "loaded": true,
        "memory_usage_mb": 18500
      },
      {
        "id": "nemotron-49b",
        "name": "Nemotron Super 49B",
        "size_gb": 28.7,
        "specialty": "reasoning",
        "loaded": false,
        "memory_usage_mb": 0
      }
    ]
  }
}
```

#### Load Model
```http
POST /api/v1/models/load
Content-Type: application/json

{
  "model_id": "nemotron-49b",
  "force_reload": false
}
```

#### Unload Model
```http
POST /api/v1/models/unload
Content-Type: application/json

{
  "model_id": "nemotron-49b"
}
```

### 3. ComfyUI Integration

#### Generate Image
```http
POST /api/v1/comfyui/generate
Content-Type: application/json

{
  "prompt": "A beautiful landscape painting",
  "width": 512,
  "height": 512,
  "steps": 20,
  "cfg_scale": 7.0,
  "seed": -1,
  "sampler": "euler"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "img_123456789",
    "prompt": "A beautiful landscape painting",
    "images": [
      {
        "filename": "generated_001.png",
        "url": "/api/v1/files/images/generated_001.png",
        "width": 512,
        "height": 512
      }
    ],
    "metadata": {
      "steps": 20,
      "cfg_scale": 7.0,
      "seed": 123456789,
      "generation_time_ms": 15432
    }
  }
}
```

#### Get ComfyUI Workflows
```http
GET /api/v1/comfyui/workflows
```

**Response:**
```json
{
  "success": true,
  "data": {
    "workflows": [
      {
        "id": "txt2img",
        "name": "Text to Image",
        "description": "Generate images from text prompts",
        "parameters": ["prompt", "width", "height", "steps", "cfg_scale"]
      },
      {
        "id": "img2img",
        "name": "Image to Image",
        "description": "Transform existing images",
        "parameters": ["image", "prompt", "denoising_strength"]
      }
    ]
  }
}
```

### 4. TRELLIS Integration

#### Generate 3D Model
```http
POST /api/v1/trellis/generate
Content-Type: application/json

{
  "description": "A modern chair with wooden legs",
  "detail_level": "high",
  "style": "realistic",
  "format": "glb"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "model_123456789",
    "description": "A modern chair with wooden legs",
    "files": [
      {
        "filename": "chair_model.glb",
        "url": "/api/v1/files/models/chair_model.glb",
        "format": "glb",
        "size_bytes": 2547890
      }
    ],
    "metadata": {
      "detail_level": "high",
      "generation_time_ms": 45678,
      "triangle_count": 15432
    }
  }
}
```

#### Get 3D Model Status
```http
GET /api/v1/trellis/models/{model_id}/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "model_123456789",
    "status": "completed",
    "progress": 100,
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:31:00Z",
    "error": null
  }
}
```

### 5. VibeVoice TTS Integration

#### Generate Speech
```http
POST /api/v1/vibevoice/generate
Content-Type: application/json

{
  "text": "Hello, this is a test message from DuckBot",
  "voice": "default",
  "emotion": "neutral",
  "speed": 1.0,
  "format": "mp3"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "audio_123456789",
    "text": "Hello, this is a test message from DuckBot",
    "audio_file": {
      "filename": "speech_001.mp3",
      "url": "/api/v1/files/audio/speech_001.mp3",
      "duration_ms": 2456,
      "size_bytes": 45678
    },
    "metadata": {
      "voice": "default",
      "emotion": "neutral",
      "speed": 1.0,
      "generation_time_ms": 1234
    }
  }
}
```

#### Get Available Voices
```http
GET /api/v1/vibevoice/voices
```

**Response:**
```json
{
  "success": true,
  "data": {
    "voices": [
      {
        "id": "default",
        "name": "Default Voice",
        "language": "en-US",
        "gender": "neutral",
        "age": "adult",
        "emotions_supported": ["neutral", "happy", "sad", "angry"]
      },
      {
        "id": "female_1",
        "name": "Female Voice 1",
        "language": "en-US",
        "gender": "female",
        "age": "adult",
        "emotions_supported": ["neutral", "happy", "sad", "angry", "surprised"]
      }
    ]
  }
}
```

### 6. File Management

#### Upload File
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: [file data]
type: "image" | "audio" | "document" | "model"
description: "File description"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "file_123456789",
    "filename": "uploaded_file.png",
    "size_bytes": 123456,
    "type": "image",
    "url": "/api/v1/files/uploaded_file.png",
    "uploaded_at": "2024-01-15T10:30:00Z"
  }
}
```

#### List Files
```http
GET /api/v1/files?type=image&limit=50&offset=0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": "file_123456789",
        "filename": "image_001.png",
        "type": "image",
        "size_bytes": 123456,
        "url": "/api/v1/files/image_001.png",
        "uploaded_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 25,
    "limit": 50,
    "offset": 0
  }
}
```

#### Delete File
```http
DELETE /api/v1/files/{file_id}
```

### 7. Memory and Learning

#### Store Memory
```http
POST /api/v1/memory/store
Content-Type: application/json

{
  "key": "user_preferences",
  "value": {
    "theme": "dark",
    "language": "en",
    "preferred_model": "qwen3-coder"
  },
  "ttl_seconds": 86400
}
```

#### Retrieve Memory
```http
GET /api/v1/memory/{key}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "user_preferences",
    "value": {
      "theme": "dark",
      "language": "en",
      "preferred_model": "qwen3-coder"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-16T10:30:00Z",
    "ttl_seconds": 86400
  }
}
```

#### Search Memories
```http
GET /api/v1/memory/search?q=preferences&limit=10
```

### 8. Desktop Automation

#### Take Screenshot
```http
POST /api/v1/automation/screenshot
```

**Response:**
```json
{
  "success": true,
  "data": {
    "screenshot_url": "/api/v1/files/screenshots/screen_001.png",
    "timestamp": "2024-01-15T10:30:00Z",
    "width": 1920,
    "height": 1080
  }
}
```

#### Execute Automation
```http
POST /api/v1/automation/execute
Content-Type: application/json

{
  "actions": [
    {"type": "open", "target": "notepad.exe"},
    {"type": "type", "text": "Hello, World!"},
    {"type": "wait", "duration_ms": 1000},
    {"type": "click", "target": "close_button"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_123456789",
    "status": "completed",
    "actions_executed": 4,
    "execution_time_ms": 3456,
    "results": [
      {"action": "open", "success": true},
      {"action": "type", "success": true},
      {"action": "wait", "success": true},
      {"action": "click", "success": true}
    ]
  }
}
```

### 9. Multi-Agent Framework

#### Create Agent Team
```http
POST /api/v1/agents/team
Content-Type: application/json

{
  "name": "Content Creation Team",
  "agents": ["research", "creative", "code"],
  "task": "Create a blog post about AI advancements"
}
```

#### Get Agent Status
```http
GET /api/v1/agents/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "research_agent",
        "name": "Research Agent",
        "status": "idle",
        "tasks_completed": 45,
        "current_task": null
      },
      {
        "id": "creative_agent",
        "name": "Creative Agent",
        "status": "working",
        "current_task": "Create blog content",
        "progress": 75
      }
    ]
  }
}
```

### 10. Mining Integration

#### Start Mining
```http
POST /api/v1/mining/start
Content-Type: application/json

{
  "algorithm": "ethash",
  "pool_url": "stratum+tcp://pool.example.com:3333",
  "wallet": "your_wallet_address",
  "worker_name": "duckbot_miner",
  "intensity": 8
}
```

#### Get Mining Statistics
```http
GET /api/v1/mining/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "mining",
    "algorithm": "ethash",
    "hash_rate": {
      "current": 45.6,
      "average": 43.2,
      "unit": "MH/s"
    },
    "shares": {
      "accepted": 1234,
      "rejected": 12,
      "stale": 5
    },
    "temperature": {
      "gpu": 72,
      "ambient": 25
    },
    "uptime": 86400,
    "estimated_daily_earnings": 0.0234
  }
}
```

## WebSocket API

### 1. Chat WebSocket

#### Connect to Chat
```javascript
const ws = new WebSocket('ws://localhost:8787/ws/v1/chat?token=your_token');

ws.onopen = () => {
  console.log('Connected to chat');

  // Send message
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Hello, DuckBot!',
    model: 'qwen3-coder',
    stream: true
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onclose = () => {
  console.log('Disconnected from chat');
};
```

#### Message Format
```json
{
  "type": "chat",
  "message": "Your message here",
  "model": "qwen3-coder",
  "stream": true,
  "max_tokens": 512,
  "temperature": 0.7
}
```

### 2. System Events WebSocket

#### Connect to System Events
```javascript
const ws = new WebSocket('ws://localhost:8787/ws/v1/system/events?token=your_token');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('System event:', data);
};
```

#### Event Types
```json
{
  "type": "system_event",
  "event": "model_loaded",
  "data": {
    "model_id": "qwen3-coder",
    "memory_usage_mb": 18500
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. File Upload WebSocket

#### Upload File via WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8787/ws/v1/files/upload?token=your_token');

ws.onopen = () => {
  // Start file upload
  ws.send(JSON.stringify({
    type: 'upload_start',
    filename: 'example.jpg',
    size_bytes: 123456,
    type: 'image'
  }));

  // Send file data in chunks
  // ...
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Upload progress:', data.progress);
};
```

## GraphQL API

### 1. GraphQL Endpoint

#### Query Examples
```graphql
# Get system status
query GetSystemStatus {
  systemStatus {
    status
    uptime
    version
    mode
    resources {
      cpuUsage
      memoryUsage
      diskUsage
    }
  }
}

# Get models
query GetModels {
  models {
    id
    name
    sizeGb
    specialty
    loaded
    memoryUsageMb
  }
}

# Get chat history
query GetChatHistory($limit: Int!) {
  chatHistory(limit: $limit) {
    id
    model
    messages {
      role
      content
    }
    createdAt
  }
}
```

#### Mutation Examples
```graphql
# Store memory
mutation StoreMemory($key: String!, $value: Json!, $ttlSeconds: Int) {
  storeMemory(key: $key, value: $value, ttlSeconds: $ttlSeconds) {
    key
    value
    createdAt
    expiresAt
  }
}

# Load model
mutation LoadModel($modelId: String!, $forceReload: Boolean) {
  loadModel(modelId: $modelId, forceReload: $forceReload) {
    id
    name
    loaded
    memoryUsageMb
  }
}
```

### 2. GraphQL Schema

```graphql
type SystemStatus {
  status: String!
  uptime: Int!
  version: String!
  mode: String!
  services: Json!
  resources: SystemResources!
}

type SystemResources {
  cpuUsage: Float!
  memoryUsage: Float!
  diskUsage: Float!
  gpuUsage: Float
}

type Model {
  id: String!
  name: String!
  sizeGb: Float!
  specialty: String!
  loaded: Boolean!
  memoryUsageMb: Int!
}

type ChatMessage {
  role: String!
  content: String!
}

type ChatHistory {
  id: String!
  model: String!
  messages: [ChatMessage!]!
  createdAt: String!
}

type Memory {
  key: String!
  value: Json!
  createdAt: String!
  expiresAt: String
  ttlSeconds: Int
}

type Query {
  systemStatus: SystemStatus!
  models: [Model!]!
  chatHistory(limit: Int): [ChatHistory!]!
  memory(key: String!): Memory
  searchMemories(query: String!, limit: Int): [Memory!]!
}

type Mutation {
  storeMemory(key: String!, value: Json!, ttlSeconds: Int): Memory!
  loadModel(modelId: String!, forceReload: Boolean): Model!
  unloadModel(modelId: String!): Boolean!
  startMining(input: MiningInput!): MiningStatus!
  stopMining: Boolean!
}

input MiningInput {
  algorithm: String!
  poolUrl: String!
  wallet: String!
  workerName: String!
  intensity: Int!
}

type MiningStatus {
  status: String!
  algorithm: String!
  hashRate: Float!
  shares: Json!
  temperature: Float!
  uptime: Int!
}
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Model 'qwen3-coder' not found",
    "details": "Available models: nemotron-49b, gemma-12b",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication failed |
| `FORBIDDEN` | 403 | Permission denied |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `MODEL_NOT_FOUND` | 404 | Model not found |
| `MODEL_LOADING_FAILED` | 500 | Failed to load model |
| `RESOURCE_EXHAUSTED` | 429 | System resources exhausted |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `RATE_LIMITED` | 429 | Too many requests |

### Error Handling Best Practices
```javascript
// JavaScript example
async function callDuckBotAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`http://localhost:8787/api/v1${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error.message);
    }

    return data.data;
  } catch (error) {
    console.error('API call failed:', error.message);

    // Handle specific errors
    if (error.message.includes('MODEL_NOT_FOUND')) {
      // Handle model not found
    } else if (error.message.includes('RATE_LIMITED')) {
      // Handle rate limiting
    }

    throw error;
  }
}
```

## Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642249200
```

### Rate Limit Rules
- **Authenticated requests**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour
- **WebSocket connections**: 100 messages per minute
- **File uploads**: 10 uploads per minute
- **Model operations**: 5 operations per minute

### Handling Rate Limits
```javascript
// Check rate limits
function checkRateLimits(response) {
  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining'));
  const reset = parseInt(response.headers.get('X-RateLimit-Reset'));

  if (remaining < 10) {
    const resetTime = new Date(reset * 1000);
    console.warn(`Rate limit almost exceeded. Resets at ${resetTime}`);
  }

  return remaining;
}

// Exponential backoff
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.message.includes('RATE_LIMITED') && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
}
```

## Python SDK Reference

### Installation
```bash
pip install duckbot-sdk
```

### Basic Usage
```python
from duckbot import DuckBotClient
import asyncio

async def main():
    # Initialize client
    client = DuckBotClient(
        api_key="your_api_key",
        base_url="http://localhost:8787"
    )

    # Get system status
    status = await client.get_system_status()
    print(f"System status: {status['data']['status']}")

    # Load a model
    await client.load_model("qwen3-30b")

    # Deploy an agent
    agent = await client.deploy_agent(
        agent_type="market_analyzer",
        task="Analyze market trends"
    )

    # Execute automation task
    result = await client.execute_automation_task(
        "Open Chrome and navigate to GitHub"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Module APIs

#### Dynamic Model Manager
```python
from duckbot.core.dynamic_model_manager import DynamicModelManager

manager = DynamicModelManager()

# Load optimal model
model_id = await manager.load_optimal_model(
    task_type="coding",
    complexity="high"
)

# Get recommendations
recommendations = manager.get_model_recommendations(
    available_ram=8,
    task_requirements=["reasoning", "coding"]
)
```

#### Intelligent Agents
```python
from duckbot.agents.intelligent_agents import IntelligentAgents

agents = IntelligentAgents()

# Deploy single agent
agent = await agents.deploy_agent(
    agent_type="market_analyzer",
    task="Analyze cryptocurrency trends",
    context={"timeframe": "7d", "coins": ["BTC", "ETH"]}
)

# Coordinate multiple agents
result = await agents.coordinate_agents([
    ("market_analyzer", "Analyze market"),
    ("cost_optimizer", "Optimize resources"),
    ("workflow_optimizer", "Improve process")
])
```

#### Memory System
```python
from duckbot.integrations.memento_integration import MementoIntegration

memento = MementoIntegration()

# Store solution
memento.store_solution(
    problem="file_permission_error",
    solution="chmod +x script.py",
    confidence=0.95,
    tags=["permissions", "linux", "fix"]
)

# Search similar solutions
solutions = memento.find_similar_solutions("permission denied")
```

#### Desktop Automation
```python
from duckbot.integrations.bytebot_integration import ByteBotIntegration

bytebot = ByteBotIntegration()

# Execute task
result = await bytebot.execute_task(
    "Open Notepad and type 'Hello World'"
)

# Start interactive mode
await bytebot.start_interactive_mode()
```

#### Cross-Platform Integration
```python
from duckbot.platforms.wsl_integration import WSLIntegration

wsl = WSLIntegration()

# Execute Linux command
result = await wsl.execute_command("ls -la /home")

# Manage Docker containers
containers = await wsl.list_containers()
await wsl.start_container("nginx")
```

## Code Examples

### Python Examples

#### Basic Chat
```python
import requests
import json

API_BASE = "http://localhost:8787/api/v1"
API_KEY = "your_api_key_here"

def chat_with_duckbot(message, model="qwen3-coder"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "max_tokens": 512,
        "temperature": 0.7
    }

    response = requests.post(f"{API_BASE}/chat/completions",
                          headers=headers,
                          json=data)

    if response.status_code == 200:
        result = response.json()
        return result["data"]["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API call failed: {response.text}")

# Usage
response = chat_with_duckbot("Hello, how are you?")
print(response)
```

#### Generate Image with ComfyUI
```python
def generate_image(prompt, width=512, height=512):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 20,
        "cfg_scale": 7.0
    }

    response = requests.post(f"{API_BASE}/comfyui/generate",
                          headers=headers,
                          json=data)

    if response.status_code == 200:
        result = response.json()
        return result["data"]["images"][0]["url"]
    else:
        raise Exception(f"Image generation failed: {response.text}")

# Usage
image_url = generate_image("A beautiful sunset over mountains")
print(f"Generated image: {image_url}")
```

#### WebSocket Chat Client
```python
import asyncio
import websockets
import json

async def websocket_chat():
    uri = "ws://localhost:8787/ws/v1/chat"

    async with websockets.connect(uri) as websocket:
        # Send authentication
        await websocket.send(json.dumps({
            "type": "auth",
            "token": API_KEY
        }))

        # Send message
        await websocket.send(json.dumps({
            "type": "chat",
            "message": "Hello via WebSocket!",
            "model": "qwen3-coder",
            "stream": True
        }))

        # Receive response
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "chat_response":
                print(f"DuckBot: {data['content']}")
            elif data["type"] == "chat_complete":
                print("Chat completed")
                break

# Run WebSocket client
asyncio.run(websocket_chat())
```

### JavaScript Examples

#### REST API Client
```javascript
class DuckBotClient {
    constructor(apiKey, baseUrl = 'http://localhost:8787/api/v1') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async chat(message, model = 'qwen3-coder') {
        const data = {
            model,
            messages: [{ role: 'user', content: message }],
            max_tokens: 512,
            temperature: 0.7
        };

        const response = await this.request('/chat/completions', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        return response.data.choices[0].message.content;
    }

    async generateImage(prompt, options = {}) {
        const data = {
            prompt,
            width: options.width || 512,
            height: options.height || 512,
            steps: options.steps || 20,
            cfg_scale: options.cfgScale || 7.0
        };

        const response = await this.request('/comfyui/generate', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        return response.data.images[0].url;
    }
}

// Usage
const client = new DuckBotClient('your_api_key_here');

client.chat('Hello, how are you?')
    .then(response => console.log(response))
    .catch(error => console.error('Error:', error));

client.generateImage('A beautiful sunset')
    .then(imageUrl => console.log('Generated image:', imageUrl))
    .catch(error => console.error('Error:', error));
```

#### WebSocket Client
```javascript
class DuckBotWebSocket {
    constructor(apiKey, url = 'ws://localhost:8787/ws/v1/chat') {
        this.apiKey = apiKey;
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        this.ws = new WebSocket(`${url}?token=${this.apiKey}`);

        this.ws.onopen = () => {
            console.log('Connected to DuckBot WebSocket');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    sendMessage(message, model = 'qwen3-coder') {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'chat',
                message,
                model,
                stream: true
            }));
        } else {
            console.error('WebSocket not connected');
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'chat_response':
                console.log('DuckBot:', data.content);
                break;
            case 'chat_complete':
                console.log('Chat completed');
                break;
            case 'system_event':
                console.log('System event:', data.event);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000;
            console.log(`Reconnecting in ${delay}ms...`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
}

// Usage
const wsClient = new DuckBotWebSocket('your_api_key_here');
wsClient.connect();

wsClient.sendMessage('Hello via WebSocket!');
```

### Node.js Examples

#### File Upload
```javascript
const fs = require('fs');
const FormData = require('form-data');
const fetch = require('node-fetch');

async function uploadFile(filePath, fileType = 'image') {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('type', fileType);
    form.append('description', 'Uploaded file via API');

    const response = await fetch('http://localhost:8787/api/v1/files/upload', {
        method: 'POST',
        headers: {
            ...form.getHeaders(),
            'Authorization': `Bearer ${API_KEY}`
        },
        body: form
    });

    return await response.json();
}

// Usage
uploadFile('./example.jpg', 'image')
    .then(result => console.log('Upload result:', result))
    .catch(error => console.error('Upload error:', error));
```

#### Streaming Chat
```javascript
async function streamingChat(message, model = 'qwen3-coder') {
    const response = await fetch('http://localhost:8787/api/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model,
            messages: [{ role: 'user', content: message }],
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                    console.log('Stream completed');
                    return;
                }
                try {
                    const parsed = JSON.parse(data);
                    console.log('Received:', parsed.choices[0].delta.content);
                } catch (e) {
                    // Ignore parse errors
                }
            }
        }
    }
}

// Usage
streamingChat('Tell me a story about AI')
    .then(() => console.log('Chat completed'))
    .catch(error => console.error('Error:', error));
```

### cURL Examples

#### Basic Chat
```bash
curl -X POST "http://localhost:8787/api/v1/chat/completions" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-coder",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

#### Generate Image
```bash
curl -X POST "http://localhost:8787/api/v1/comfyui/generate" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful landscape painting",
    "width": 512,
    "height": 512,
    "steps": 20,
    "cfg_scale": 7.0
  }'
```

#### Upload File
```bash
curl -X POST "http://localhost:8787/api/v1/files/upload" \
  -H "Authorization: Bearer your_api_key_here" \
  -F "file=@example.jpg" \
  -F "type=image" \
  -F "description=Test image upload"
```

This comprehensive API reference provides detailed documentation for all DuckBot v4.2 APIs, including REST endpoints, WebSocket interfaces, GraphQL queries, and practical code examples in multiple programming languages.
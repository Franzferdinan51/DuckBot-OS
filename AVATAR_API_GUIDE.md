# DuckBot REST API for Avatar Integration

## 🎯 Quick Start for Avatar Integration

DuckBot provides multiple REST API endpoints that are perfect for connecting to avatar systems, chatbots, or any external application that needs to communicate with the AI.

### 🔗 Base URLs
- **Enhanced Mode**: `http://localhost:8787` or `http://YOUR_TAILSCALE_IP:8787`
- **OpenWebUI**: `http://localhost:8080` or `http://YOUR_TAILSCALE_IP:8080`

### 🔐 Authentication
All API endpoints require a token. Get your token from:
```
GET http://localhost:8787/token
```

Include the token in your requests:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

---

## 🎭 Primary Chat API for Avatars

### `/chat` - Main Chat Endpoint
**Perfect for avatar integration** - This is your main endpoint for conversational AI.

**Request:**
```http
POST http://localhost:8787/chat
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer YOUR_TOKEN

message=Hello! How are you today?&kind=*&risk=low
```

**JSON Response:**
```json
{
  "success": true,
  "response": "Hello! I'm doing great, thank you for asking. How can I help you today?",
  "model": "microsoft/phi-3-mini-128k-instruct:free",
  "timestamp": 1693847238.123,
  "cached": false,
  "risk": "low"
}
```

**Parameters:**
- `message` (required): The user's message to the AI
- `kind` (optional): Task type (`*`, `code`, `json_format`, `policy`, `long_form`, `arbiter`)
- `risk` (optional): Risk level (`low`, `medium`, `high`)

---

## 🎪 Alternative Chat APIs

### `/api/task` - Direct Task API
**For more control over AI tasks**

**Request:**
```http
POST http://localhost:8787/api/task
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer YOUR_TOKEN

prompt=Tell me a joke&kind=chat&risk=low
```

**JSON Response:**
```json
{
  "success": true,
  "result": {
    "text": "Why don't scientists trust atoms? Because they make up everything!",
    "model_used": "microsoft/phi-3-mini-128k-instruct:free",
    "cached": false
  },
  "task_id": "task_1693847238"
}
```

---

## 🎵 Voice Integration (VibeVoice TTS)

### Voice Generation for Avatar Speech
If you have VibeVoice TTS running (port 8000), you can generate speech for your avatar:

**Request:**
```http
POST http://localhost:8000/generate
Content-Type: application/json

{
  "text": "Hello! I'm your AI assistant avatar.",
  "voice": "en-alice",
  "format": "wav"
}
```

---

## 🔄 Provider Management

### Switch AI Models
**For different avatar personalities or capabilities**

**Request:**
```http
POST http://localhost:8787/api/services/start
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer YOUR_TOKEN

# Switch to different providers via Discord commands:
message=/switch openrouter&kind=*&risk=low
```

**Available Providers:**
- `/switch openrouter` - Cloud AI models (free tier available)
- `/switch local` - Local LM Studio models (private)
- `/switch claude` - Anthropic Claude models
- `/switch code` - Claude Code Router (for coding tasks)

---

## 📊 System Status APIs

### Real-time System Status
**Monitor your avatar's AI backend health**

```http
GET http://localhost:8787/api/system-status
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "ok": true,
  "status": {
    "bucket_tokens": 28,
    "active_model": "microsoft/phi-3-mini-128k-instruct:free",
    "cache_hits": 15,
    "total_requests": 42,
    "uptime": "2h 34m",
    "memory_usage": "67%"
  }
}
```

---

## 🎨 Enhanced Features APIs

### Context Analysis
**Give your avatar memory and context awareness**

```http
GET http://localhost:8787/api/action-logs?hours=24
Authorization: Bearer YOUR_TOKEN
```

### Cost Tracking
**Monitor API usage for your avatar**

```http
GET http://localhost:8787/api/cost_summary?days=7
Authorization: Bearer YOUR_TOKEN
```

---

## 🤖 Avatar Integration Examples

### Simple Avatar Chat Client (Python)
```python
import requests
import json

class DuckBotAvatarClient:
    def __init__(self, base_url="http://localhost:8787", token=None):
        self.base_url = base_url
        self.token = token or self.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def get_token(self):
        response = requests.get(f"{self.base_url}/token")
        return response.json()["token"]
    
    def chat(self, message, personality="friendly"):
        data = {
            "message": message,
            "kind": "*",
            "risk": "low"
        }
        response = requests.post(
            f"{self.base_url}/chat",
            data=data,
            headers=self.headers
        )
        return response.json()
    
    def get_status(self):
        response = requests.get(
            f"{self.base_url}/api/system-status",
            headers=self.headers
        )
        return response.json()

# Usage
avatar = DuckBotAvatarClient()
result = avatar.chat("Hello! What's your name?")
print(f"Avatar says: {result['response']}")
```

### JavaScript/Web Avatar
```javascript
class DuckBotAvatar {
    constructor(baseUrl = 'http://localhost:8787') {
        this.baseUrl = baseUrl;
        this.token = null;
        this.init();
    }
    
    async init() {
        const response = await fetch(`${this.baseUrl}/token`);
        const data = await response.json();
        this.token = data.token;
    }
    
    async chat(message) {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('kind', '*');
        formData.append('risk', 'low');
        
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        return await response.json();
    }
}

// Usage
const avatar = new DuckBotAvatar();
avatar.chat("Tell me a joke").then(result => {
    console.log("Avatar response:", result.response);
    // Send to TTS or display in avatar
});
```

---

## 🚀 Avatar Deployment Options

### Option 1: Enhanced Mode (Recommended)
Start with Option 1 in the launcher for full API access:
- All REST endpoints available
- OpenWebUI integration
- Provider switching
- Enhanced features

### Option 2: OpenWebUI Only
Use OpenWebUI as a direct chat interface:
- Modern ChatGPT-like interface
- Direct web integration
- Easy to embed in web pages

### Option 3: Headless API Mode
Use Option 6 (AI-Headless) for pure API access:
- No web interface overhead
- Pure REST API server
- Perfect for avatar backends

---

## 🔧 Configuration for Avatars

### Enable Remote Access
All services are already configured for remote access via Tailscale:
- WebUI: `0.0.0.0:8787`
- OpenWebUI: `0.0.0.0:8080`
- VibeVoice: `0.0.0.0:8000`

### Rate Limits
- Chat API: 10 requests/second, burst 15
- Task API: 5 requests/second, burst 10
- Other APIs: Various limits per endpoint

### Security
- Token-based authentication required
- Rate limiting prevents abuse
- CORS headers can be configured for web avatars

---

## 💡 Avatar Use Cases

1. **Virtual Assistant Avatar**: Use `/chat` endpoint for natural conversations
2. **Gaming NPC**: Use `/api/task` for specific game interactions
3. **Educational Tutor**: Use different `kind` parameters for various learning modes
4. **Customer Support Bot**: Combine with context APIs for persistent memory
5. **Voice Assistant**: Integrate with VibeVoice for speech synthesis
6. **Web Chatbot**: Use OpenWebUI or direct API integration
7. **Mobile App Avatar**: REST APIs work with any mobile development framework

---

## 🛠️ Advanced Features

### Multi-Provider Avatar Personalities
- **OpenRouter**: Cloud-based, general conversation
- **Local Models**: Privacy-focused, customizable
- **Claude Code**: Technical assistance
- **Qwen Code**: Programming help

### Context-Aware Avatars
- Use `/api/action-logs` to give your avatar memory
- Build conversation history
- Personalized responses based on user patterns

### Cost-Aware Avatars
- Monitor usage with `/api/cost_summary`
- Switch to free models when needed
- Budget-conscious avatar behavior

---

Your DuckBot system is now ready for avatar integration! The REST APIs provide everything you need to create intelligent, conversational avatars with full AI capabilities.
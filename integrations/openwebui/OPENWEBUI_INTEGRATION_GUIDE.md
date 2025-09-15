# OpenWebUI-DuckBot Integration Guide

Complete integration that allows OpenWebUI to use DuckBot's powerful AI routing system instead of external providers, with advanced features inspired by Archon.

## 🚀 Features

### Core Integration
- **Direct AI Routing**: OpenWebUI uses DuckBot's intelligent AI routing system
- **Model Compatibility**: Full Ollama API compatibility for seamless integration
- **Streaming Support**: Real-time streaming responses
- **Multi-Model Support**: Access all DuckBot AI models through OpenWebUI

### Advanced Features (Archon-Inspired)
- **Smart Search**: Advanced RAG with multiple search strategies
- **Knowledge Management**: Document processing and indexing
- **Code Analysis**: Qwen-enhanced code analysis through OpenWebUI
- **Voice Synthesis**: VibeVoice TTS integration
- **Cost Analytics**: Real-time usage and cost tracking

### Available Models
- `duckbot-auto` - Smart AI routing with automatic model selection
- `duckbot-code` - Code specialist for programming tasks
- `duckbot-reasoning` - Advanced reasoning and problem-solving
- `duckbot-summary` - Efficient summarization and extraction
- `duckbot-long-form` - Long-form content creation
- `duckbot-qwen` - Qwen-enhanced AI with advanced capabilities
- Plus any LM Studio models automatically detected

## 📋 Prerequisites

1. **DuckBot System** - Running and accessible at `http://localhost:8787`
2. **OpenWebUI** - Installed and running
3. **Python 3.8+** - With pip for dependency installation

## 🔧 Installation & Setup

### Step 1: Start DuckBot
First, ensure DuckBot is running:
```bash
# Start DuckBot WebUI
START_ENHANCED_DUCKBOT.bat
# OR
python -m duckbot.webui
```

### Step 2: Launch the Integration Adapter
```bash
# Easy one-click setup
START_OPENWEBUI_DUCKBOT_ADAPTER.bat
```

The adapter will:
- ✅ Check DuckBot availability 
- ✅ Install required dependencies
- ✅ Start the OpenWebUI-compatible API server
- ✅ Display configuration instructions

### Step 3: Configure OpenWebUI

1. **Open OpenWebUI** in your browser
2. **Go to Settings** → Connections/Integrations
3. **Set Ollama API URL** to: `http://127.0.0.1:11434`
4. **Save** and **refresh** the models list
5. **Select** any DuckBot model from the dropdown

## 🎯 Usage Examples

### Basic Chat
Simply select a DuckBot model in OpenWebUI and start chatting. The conversation will be routed through DuckBot's intelligent AI system.

### Code Analysis
1. Select `duckbot-code` or `duckbot-qwen` model
2. Paste your code and ask for analysis
3. Get enhanced code insights powered by DuckBot's Qwen system

### Smart Search & RAG
1. Select `duckbot-auto` model  
2. Ask questions that benefit from knowledge base search
3. DuckBot's RAG system will automatically enhance responses

### Long-form Content
1. Select `duckbot-long-form` model
2. Request detailed explanations or content creation
3. Get comprehensive, well-structured responses

## 🏗️ Architecture

```
OpenWebUI → Adapter (Port 11434) → DuckBot WebUI (Port 8787) → AI Router
                                                                    ↓
                                                              [Local Models]
                                                              [Cloud APIs]
                                                              [RAG System]
                                                              [Qwen Analysis]
```

### Key Components

1. **openwebui_duckbot_adapter.py** - Main adapter providing Ollama-compatible API
2. **openwebui_integration_config.py** - Advanced configuration and knowledge management
3. **START_OPENWEBUI_DUCKBOT_ADAPTER.bat** - Easy startup script

## 🔍 Advanced Features

### Knowledge Management API
The adapter exposes additional endpoints for advanced functionality:

```python
# RAG Search
POST /api/duckbot/rag/search
{
  "query": "your search query",
  "top_k": 5
}

# System Status  
GET /api/duckbot/status

# Code Analysis
POST /api/duckbot/analyze
{
  "code": "your code here"
}

# Health Check
GET /health
```

### Configuration

Run the configuration setup:
```bash
python openwebui_integration_config.py
```

This generates:
- `openwebui_duckbot_config.yaml` - Main configuration file
- `openwebui_model_config.json` - Model definitions  
- `start_integration.sh` - Linux/Mac startup script
- `docker-compose.yml` - Docker deployment configuration

## 🐳 Docker Deployment

For containerized deployment:

```bash
# Generate Docker configuration
python openwebui_integration_config.py

# Deploy with Docker Compose
docker-compose up -d
```

## 🛠️ Troubleshooting

### Adapter Won't Start
- ✅ Check if DuckBot WebUI is running at `localhost:8787`
- ✅ Ensure Python 3.8+ is installed
- ✅ Verify port 11434 is available
- ✅ Check firewall settings

### OpenWebUI Can't Connect
- ✅ Confirm Ollama API URL is set to `http://127.0.0.1:11434`
- ✅ Check adapter is running (green status in terminal)
- ✅ Test adapter endpoint: `http://localhost:11434/health`
- ✅ Refresh models list in OpenWebUI

### Models Not Appearing
- ✅ Wait 30 seconds after starting adapter
- ✅ Refresh OpenWebUI models list
- ✅ Check adapter logs for model discovery issues
- ✅ Ensure LM Studio is running if using local models

### Poor Response Quality
- ✅ Try different DuckBot models (duckbot-reasoning, duckbot-qwen)
- ✅ Check DuckBot system status via WebUI
- ✅ Ensure adequate system resources
- ✅ Verify model configurations in DuckBot

## 📊 Monitoring & Analytics

### Health Monitoring
Check adapter health:
```bash
curl http://localhost:11434/health
```

### DuckBot System Status  
Monitor DuckBot through the adapter:
```bash
curl http://localhost:11434/api/duckbot/status
```

### Cost Analytics
If using cloud models, monitor costs through DuckBot's WebUI at `http://localhost:8787`

## 🔒 Security Notes

- **Localhost Only**: Adapter runs on localhost by default for security
- **Token Authentication**: DuckBot WebUI uses secure token authentication  
- **No External Dependencies**: All processing stays local when using local models
- **Network Isolation**: Can run completely offline with local-only DuckBot setup

## 📈 Performance Optimization

### For Best Performance:
1. **Use Local Models**: Configure DuckBot for local-only mode to avoid API latencies
2. **Enable Caching**: DuckBot's built-in caching reduces response times
3. **Resource Monitoring**: Monitor system resources via DuckBot WebUI
4. **Model Selection**: Choose appropriate models for each task type

### Scaling Options:
- **Multi-Instance**: Run multiple adapter instances on different ports
- **Load Balancing**: Use nginx/haproxy to balance across adapters
- **Containerization**: Deploy with Docker for easier scaling

## 🤝 Integration Benefits

### Why Use This Integration?

1. **Privacy**: Keep all AI processing local with DuckBot's local-only mode
2. **Cost Control**: Avoid external API costs with local models
3. **Customization**: Full control over AI routing and model selection  
4. **Advanced Features**: Access DuckBot's RAG, Qwen, and VibeVoice capabilities
5. **Unified Interface**: Use familiar OpenWebUI interface with powerful DuckBot backend

### Compared to Standard OpenWebUI:
- ✅ **More AI Models**: Access to DuckBot's intelligent routing
- ✅ **Better RAG**: Advanced knowledge base integration
- ✅ **Code Analysis**: Qwen-enhanced code understanding  
- ✅ **Voice Synthesis**: Built-in TTS capabilities
- ✅ **Cost Analytics**: Real-time usage monitoring
- ✅ **Privacy Options**: Complete local processing available

## 🎉 Success! 

You now have OpenWebUI fully integrated with DuckBot's powerful AI ecosystem. Enjoy intelligent AI routing, advanced RAG capabilities, and complete control over your AI interactions!

---

**Need Help?** Check the adapter logs, DuckBot WebUI status, or verify all services are running correctly.
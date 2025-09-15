# 🦆 DuckBot v3.0.6 - Quick Start Guide

Get DuckBot running in **3 minutes** with the enhanced production control center and Qwen AI system initialization.

## 🚀 Ultra-Fast Setup

1. **Extract and Launch**
   ```bash
   # Extract DuckBot-v3.0.6-FINAL-TESTED-[timestamp].zip
   # Double-click SETUP_AND_START.bat
   ```

2. **Configure OpenRouter (IMPORTANT)**
   ```bash
   # Edit .env file and add:
   OPENROUTER_API_KEY=your_key_from_openrouter.ai
   # This enables Qwen Code tools and AI system initialization
   ```

3. **Choose Your Experience**
   ```
   1. [WEBUI] Professional AI Dashboard - RECOMMENDED!
      Real-time monitoring + AI task execution
      Token-secured + Professional interface
   ```

3. **Auto-Setup Process**
   The enhanced launcher automatically:
   - ✅ **Python Check**: Validates installation automatically
   - ✅ **Dependencies**: Auto-installs FastAPI, uvicorn, and requirements  
   - ✅ **Token Security**: Generates secure access token
   - ✅ **Browser Launch**: Opens dashboard automatically

## 🔐 First Access

After startup, you'll see:
```
🔐 DuckBot WebUI Token: abc123xyz...
🌐 WebUI URL: http://localhost:8787/?token=abc123xyz...
📱 Tailscale-friendly: Works best with localhost:8787 (not IP addresses)
```

**Copy the full URL** and paste it into your browser.

## 🎯 Core Features

### AI-Enhanced Task Execution
- **Dynamic Model Detection**: Auto-detects LM Studio models with 60s caching
- **Local-First Routing**: LM Studio → OpenRouter free tier escalation
- **Smart Caching**: 60-80% cost reduction via intelligent response caching  
- **Circuit Breakers**: Auto-disable failing models, prevent cascade failures
- **Multi-Tier Models**: Local → Qwen → GLM → DeepSeek → Kimi → R1 chains

### Professional WebUI Dashboard
- **Real-time Monitoring**: Live system status, cache stats, circuit breakers
- **Task Runner**: Execute AI tasks with confidence scoring and retry options
- **Progress Visualization**: Live progress bars and telemetry charts
- **One-Click Actions**: JSON export, cache management, breaker resets
- **Token Security**: Secure localhost-only access with auto-generated tokens

### Advanced Diagnostics (NEW!)
- **Qwen Integration**: Advanced code analysis and system diagnostics
- **Performance Analysis**: Bottleneck detection and optimization recommendations
- **Server Management**: Process monitoring, health checks, port management
- **System Validation**: Comprehensive testing and dependency checking

## 🛠️ Configuration

### AI Providers
Set your OpenRouter API key:
```bash
set OPENROUTER_API_KEY=your_key_here
```

**Free Models Available** (no API key needed):
- `qwen/qwen3-coder:free` - Code tasks
- `glm/glm-4.5-air:free` - General tasks  
- `deepseek/deepseek-r1:free` - Reasoning tasks

### Model Selection Strategy
```
Task Type → Model Priority Chain
status     → local → glm
summary    → local → glm → kimi  
code       → local → qwen → glm
reasoning  → local → r1 → nemo
```

## 🔧 Advanced Usage

### Environment Variables
```bash
# Core Settings
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BUDGET_PER_MIN=6
AI_CONFIDENCE_MIN=0.75
AI_LOCAL_CONF_MIN=0.68

# WebUI Security
DUCKBOT_WEBUI_HOST=127.0.0.1  # localhost only
DUCKBOT_WEBUI_PORT=8787

# Cache & Performance  
AI_TTL_CACHE_SEC=60
AI_MAX_HOPS_ROUTINE=1
AI_MAX_HOPS_CRITICAL=3
```

### Command Line Options
```bash
# Standard AI-enhanced startup
python start_ai_ecosystem.py

# WebUI only
python -m duckbot.webui

# Interactive chat
python chat_with_ai.py

# Settings configuration
python setup_ai_provider.py
```

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
**Solution**: Dependencies missing
```bash
pip install -r requirements.txt
```

### WebUI Access Denied
**Solution**: Token required
- Check terminal output for the full URL with token
- Use: `http://localhost:8787/?token=YOUR_TOKEN`

### Models Timing Out
**Solution**: Circuit breakers activated
- Click "🔄 Reset Breakers" in WebUI
- Or restart: `SETUP_AND_START.bat` → Option 2

### Cache Issues
**Solution**: Clear corrupted cache
- Click "🗑️ Clear Cache" in WebUI  
- Manual: Delete `duckbot/ai_cache/` folder

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI WebUI │────│  AI Router (GPT) │────│  Model Providers│
│  (localhost:8787)│    │  Local-First     │    │  LM Studio      │
└─────────────────┘    │  Circuit Breakers│    │  OpenRouter     │
                       │  Token Bucket    │    │  (Free Tier)    │
                       └──────────────────┘    └─────────────────┘
                                │                        
                       ┌──────────────────┐              
                       │   Cache Manager  │              
                       │   SQLite Storage │              
                       │   60-80% Savings │              
                       └──────────────────┘              
```

## 🔒 Security Features

- ✅ **Shared Token Authentication** - Secure WebUI access
- ✅ **Localhost Binding** - Network isolation by default
- ✅ **Log Sanitization** - Never prints API keys or secrets
- ✅ **Atomic File Writes** - Prevents corruption during updates
- ✅ **Graceful Shutdown** - Clean background worker termination

## 🏃‍♂️ Ready to Go!

1. Run `SETUP_AND_START.bat` → Option 2
2. Copy the token URL from terminal
3. Open in browser and start using the professional AI manager

**Need Help?** The WebUI has built-in tooltips and the system logs errors clearly.

---
*Generated by DuckBot v3.0.4 - AI-Managed Crypto Ecosystem*
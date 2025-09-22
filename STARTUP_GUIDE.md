# DuckBot v4.2 Startup Guide

## 🚀 Complete Startup Documentation

This guide provides comprehensive information about all startup options and features available in DuckBot v4.2, including the new VibeVoice and RealtimeVoiceChat functionality.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Main Launcher](#main-launcher)
3. [Individual Service Starters](#individual-service-starters)
4. [All-in-One Services](#all-in-one-services)
5. [Voice & Communication Services](#voice--communication-services)
6. [Troubleshooting](#troubleshooting)
7. [Configuration](#configuration)

## 🚀 Quick Start

### For Immediate Use:
1. **Complete Experience**: Run `launcher\CONSOLIDATED_DUCKBOT_LAUNCHER.bat` and select option 1
2. **All Services**: Run `START_ALL_SERVICES.bat` for everything at once
3. **Web Interface Only**: Run `START_WEBUI.bat` for just the dashboard

### Access Points:
- **WebUI Dashboard**: http://localhost:8787
- **System Monitor**: http://localhost:8789
- **VibeVoice TTS**: http://localhost:8000
- **Voice Chat**: http://localhost:8001

## 🎛️ Main Launcher

**File**: `launcher\CONSOLIDATED_DUCKBOT_LAUNCHER.bat`

The main launcher provides access to all DuckBot features through an intuitive menu system.

### Primary Launch Modes:

#### 1. 🌟 [ULTIMATE] Complete Ecosystem
**Recommended for full experience**
- Launches all core DuckBot services
- Includes WebUI, AI management, monitoring
- **Access**: http://localhost:8787

#### 2. 🌐 [WEBUI] Enhanced Web Interface Only
- Modern web dashboard with real-time updates
- **Access**: http://localhost:8787

#### 3. 🤖 [HEADLESS] AI Management Only
- Pure AI management without WebUI overhead
- Optimized for server deployment

#### 4. 🏠 [LOCAL-ONLY] Complete Privacy Mode
- Complete offline operation with LM Studio
- Zero external API calls
- Requires LM Studio running locally

#### 5. ⚡ [QUICK-START] Ultra-Fast Unified Mode
- One-click startup with optimizations
- Skips configuration menus

### Specialized Modes:

#### 6. 🧪 [TEST] Comprehensive System Testing
- All features validation
- Performance benchmarks
- AI routing and model detection

#### 7. 📊 [MONITORING] System Monitoring Dashboard
- Real-time system metrics
- Performance tracking
- **Access**: http://localhost:8789

#### 8. 💬 [CHAT] Interactive AI Assistant
- Direct chat with DuckBot AI Assistant
- Ask questions and get help

### Voice & Communication Modes:

#### 9. 🔊 [VIBEVOICE] VibeVoice TTS Server
- Advanced text-to-speech with multiple voices
- Edge TTS, pyttsx3, and Coqui TTS support
- **Access**: http://localhost:8000
- **API**: http://localhost:8000/tts

#### 10. 🗣️ [VOICECHAT] Realtime Voice Chat
- Real-time voice conversation with AI
- WebSocket-based live communication
- **Access**: http://localhost:8001
- **WebSocket**: ws://localhost:8001/ws/{session_id}

### System Management:

#### A. 🎛️ [ALL-SERVICES] Start All Services
- Complete ecosystem with all features
- VibeVoice + RealtimeVoiceChat + Discord + WebUI + MCP
- **All ports**: 8787, 8789, 8000, 8001

#### I. 📦 [INSTALL] Auto-Install Missing Components
- Install all required dependencies
- Python packages and system tools

#### U. 🔧 [UPDATE] Update All Components
- Update DuckBot and all integrations
- Dependency updates and configuration migration

#### D. 🩺 [DOCTOR] System Doctor & Dependency Fixer
- Comprehensive health diagnostics
- Automatic dependency installation
- Performance analysis and repair

#### S. 🔍 [STATUS] Quick System Status
- Integration health checks
- Service status and port availability
- Process monitoring

#### K. 🛑 [KILL] Kill All DuckBot Processes
- Stop all running services
- Clean shutdown and process cleanup

#### C. ⚙️ [CONFIG] DuckBot Settings and Configuration
- Configure AI providers and integrations
- System settings and network options

#### H. ❓ [HELP] Help and Documentation
- Integration guides and troubleshooting
- Feature documentation

## 🎯 Individual Service Starters

### Web Interface Services

#### START_WEBUI.bat
- **Purpose**: Launch Enhanced WebUI only
- **Port**: 8787
- **Access**: http://localhost:8787
- **Features**: Real-time monitoring, multi-agent dashboard

#### START_MONITORING.bat
- **Purpose**: Launch System Monitoring Dashboard
- **Port**: 8789
- **Access**: http://localhost:8789
- **Features**: System metrics, performance tracking

### AI Services

#### START_HEADLESS.bat
- **Purpose**: Launch AI management without UI
- **Features**: Service orchestration, AI coordination

#### START_CHAT.bat
- **Purpose**: Launch Interactive AI Assistant
- **Features**: Direct chat, help and control

### Voice Services

#### START_VIBEVOICE_SERVER.bat
- **Purpose**: Launch VibeVoice TTS Server
- **Port**: 8000
- **Access**: http://localhost:8000
- **Features**: Advanced TTS, multiple voice engines
- **Dependencies**: edge-tts, pyttsx3, fastapi, uvicorn

#### start_realtime_voicechat_enhanced.bat
- **Purpose**: Launch Realtime Voice Chat Server
- **Port**: 8001
- **Access**: http://localhost:8001
- **Features**: Real-time voice conversation, WebSocket communication
- **Dependencies**: fastapi, uvicorn, websockets, aiohttp

### Communication Services

#### START_DISCORD_BOT.bat
- **Purpose**: Launch Enhanced Discord Bot
- **Features**: Entertainment commands, games, AI integration
- **Requirements**: Discord bot token in .env file

#### START_KILL.bat
- **Purpose**: Stop all DuckBot processes
- **Features**: Clean shutdown, process cleanup

## 🎛️ All-in-One Services

### START_ALL_SERVICES.bat
**Complete ecosystem launcher with all features**

#### Services Started:
1. **Enhanced WebUI Dashboard** (Port 8787)
2. **AI Ecosystem Manager** (Background service)
3. **VibeVoice TTS Server** (Port 8000)
4. **Realtime Voice Chat Server** (Port 8001)
5. **MCP Server** (Background service)
6. **Enhanced Discord Bot** (Background service)
7. **System Monitoring Dashboard** (Port 8789)
8. **Archon Multi-Agent System** (Background service)
9. **ByteBot Desktop Automation** (Background service)

#### Features:
- Automatic port conflict resolution
- Comprehensive dependency checking
- Service health monitoring
- Detailed logging (logs/ directory)
- Graceful error handling
- Success/failure reporting

#### Usage:
```bash
# Normal startup with wait
START_ALL_SERVICES.bat

# Non-blocking startup
START_ALL_SERVICES.bat --no-wait
```

## 🎙️ Voice & Communication Services

### VibeVoice TTS Server

#### Capabilities:
- **Multiple TTS Engines**:
  - Microsoft Edge TTS (online, high quality)
  - pyttsx3 (offline, basic)
  - Coqui TTS (offline, neural voices)
- **REST API**: Complete programmatic access
- **Web Interface**: Browser-based testing
- **Multiple Languages**: Support for various languages and accents

#### API Endpoints:
- `GET /health` - Service health check
- `POST /tts` - Text-to-speech conversion
- `GET /voices` - Available voice list
- `GET /docs` - API documentation

#### Example Usage:
```bash
# Check service health
curl http://localhost:8000/health

# Convert text to speech
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from DuckBot!", "voice": "en-US-AriaNeural"}'

# List available voices
curl http://localhost:8000/voices
```

### Realtime Voice Chat

#### Capabilities:
- **Real-time Communication**: WebSocket-based live chat
- **Multiple AI Providers**: OpenAI, Anthropic, Google, local models
- **Voice Activity Detection**: Automatic speech detection
- **Noise Cancellation**: Background noise reduction
- **Session Management**: Persistent conversation history
- **Cross-browser**: Works in all modern browsers

#### Features:
- **Web Interface**: Browser-based voice chat
- **WebSocket API**: Programmatic access
- **Session Management**: Multiple concurrent sessions
- **AI Integration**: Natural conversation with AI
- **Audio Processing**: High-quality voice processing

#### API Endpoints:
- `GET /health` - Service health check
- `GET /docs` - API documentation
- `WebSocket /ws/{session_id}` - Real-time voice chat

#### Browser Usage:
1. Open http://localhost:8001
2. Click "Start Voice Chat"
3. Allow microphone access
4. Speak naturally and AI will respond

### Enhanced Discord Bot

#### Entertainment Features:
- **Games**: Trivia, word games, number guessing
- **Music**: Voice channel music playback (YouTube, Spotify)
- **Fun Commands**: Jokes, quotes, facts, meme generator
- **Utilities**: Translation, calculator, weather

#### AI Features:
- **Natural Language**: Context-aware conversations
- **Multiple Providers**: Support for various AI services
- **Voice Integration**: Voice channel capabilities
- **Custom Commands**: User-defined command creation

#### Control Commands:
- `!help` - Show all available commands
- `!ai` - Chat with AI assistant
- `!play` - Play music in voice channels
- `!trivia` - Start trivia game
- `!joke` - Get random joke
- `!weather` - Get weather information
- `!translate` - Translate text

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Port Conflicts
**Problem**: Service fails to start due to port already in use
**Solution**:
1. Use START_KILL.bat to free all ports
2. Or manually kill processes: `taskkill //F //PID <process_id>`

#### Python Not Found
**Problem**: "Python not found" error
**Solution**:
1. Install Python 3.8+ from https://www.python.org/downloads/
2. Ensure "Add Python to PATH" is checked during installation
3. Restart command prompt after installation

#### Missing Dependencies
**Problem**: Import errors or missing modules
**Solution**:
1. Run launcher option I (INSTALL) to auto-install dependencies
2. Or manually install: `pip install -r requirements.txt`

#### Discord Bot Not Starting
**Problem**: Discord bot fails to start
**Solution**:
1. Verify DISCORD_TOKEN is set in .env file
2. Check bot permissions in Discord Developer Portal
3. Ensure bot intents are enabled

#### Voice Services Not Working
**Problem**: VibeVoice or VoiceChat not accessible
**Solution**:
1. Check if ports 8000/8001 are open and not blocked
2. Verify microphone permissions for VoiceChat
3. Check firewall settings

#### Service Verification
**Check service status**:
```bash
# Check if ports are listening
netstat -ano | findstr :8787
netstat -ano | findstr :8000
netstat -ano | findstr :8001
netstat -ano | findstr :8789

# Check running processes
tasklist | findstr python
```

### Log Files
All services write logs to the `logs/` directory:
- `logs/unified_webui.log` - WebUI service
- `logs/vibevoice.log` - VibeVoice TTS
- `logs/voicechat.log` - Voice Chat
- `logs/discord.log` - Discord bot
- `logs/system_monitor.log` - Monitoring dashboard
- `logs/ai_ecosystem.log` - AI ecosystem manager

## ⚙️ Configuration

### Environment Variables (.env file)
```bash
# AI Provider Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
DISCORD_TOKEN=your_discord_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# System Configuration
DUCKBOT_WEBUI_HOST=127.0.0.1
DUCKBOT_WEBUI_PORT=8787
AI_CONFIDENCE_MIN=0.75
AI_LOCAL_CONF_MIN=0.68

# Local Mode Configuration
AI_LOCAL_ONLY_MODE=false
ENABLE_LM_STUDIO_ONLY=false
LM_STUDIO_URL=http://localhost:1234/v1

# Feature Toggles
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
```

### AI Configuration (ai_config.json)
Configure AI providers, routing rules, and model settings.

### Ecosystem Configuration (ecosystem_config.yaml)
Configure service management, ports, and integration settings.

## 📚 Advanced Usage

### Custom Startup Sequences
Create custom startup scripts by combining individual service starters:

```bash
@echo off
REM Custom startup example
START "WebUI" START_WEBUI.bat
timeout /t 3
START "VibeVoice" START_VIBEVOICE_SERVER.bat
timeout /t 2
START "VoiceChat" start_realtime_voicechat_enhanced.bat
```

### Service Dependencies
Some services depend on others:
- **WebUI** requires no dependencies
- **VibeVoice** requires audio libraries
- **VoiceChat** requires microphone access
- **Discord Bot** requires valid token and permissions

### Port Configuration
Default ports can be changed in configuration files:
- WebUI: 8787
- Monitoring: 8789
- VibeVoice: 8000
- VoiceChat: 8001

## 🎉 Getting Help

### Documentation
- **README.md**: Project overview and setup
- **CLAUDE.md**: Development guidelines
- **QWEN.md**: Qwen-specific documentation

### Support Commands
- Use launcher option H for help
- Use option S for system status
- Use option D for diagnostics

### Community
- Check project documentation for community links
- Review logs for detailed error information
- Use the diagnostic tools for system analysis

---

**DuckBot v4.2** - Enterprise-Grade AI-Managed Ecosystem
*Complete feature set with voice and communication capabilities*
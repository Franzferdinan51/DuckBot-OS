# DuckBot v4.2 - Consolidated Documentation

## Project Overview
**DuckBot v4.2** is an enterprise-grade AI-managed ecosystem featuring **revolutionary local-first architecture** and **complete cloud feature parity**. Choose between powerful cloud AI or complete privacy with local models - both modes offer identical intelligence and capabilities with comprehensive integration architecture including **Charm Ecosystem**, **Memento Memory System**, **ByteBot Desktop Automation**, **Archon Multi-Agent Framework**, **Advanced AI Router**, **VibeVoice TTS**, **LiveKit WebRTC**, and **Discord Bot Integration**.

**Key Differentiators**:
- **Local-First Revolution**: Complete privacy mode with full feature parity
- **Dynamic Model Management**: Intelligent loading/unloading based on tasks and system resources
- **Main Brain + Specialists**: Persistent orchestration model + auto-loading task-specific models
- **Resource Intelligence**: Smart GPU/CPU/RAM management with background cleanup
- **Zero Cost Local**: $0 API costs with comprehensive local analytics
- **Complete Privacy**: All processing stays on your machine in local-only mode

## Core Technologies
- **Python 3.9+** (FastAPI, asyncio, Discord.py)
- **ComfyUI** (Image/video generation)
- **LM Studio** (Local AI models)
- **OpenRouter** (AI API integration)
- **n8n** (Workflow automation)
- **LiveKit WebRTC** (Real-time communication)
- **VibeVoice TTS** (Text-to-speech)
- **Charm Ecosystem** (Terminal UI tools)
- **Claude Code Router** (Code routing and execution)
- **Qwen-Agent** (Advanced AI agent framework)
- **Browser-Use** (Web automation)
- **Web-UI** (Enhanced web interface)
- **Persona Engine** (Character animation and voice)
- **MCP Server** (Model Context Protocol integration)
- **Docker Integration** (Container management)
- **WSL Integration** (Linux on Windows)

## Architecture

### AI Provider Architecture

**🏠 LOCAL-ONLY MODE** (Privacy-First):
```
Architecture: Main Brain + Dynamic Specialists
Main Brain    → Qwen3 Coder 30B (always loaded, protected)
Task Routing  → Dynamic loading based on task type:
  code        → Qwen3 Coder (specialized)
  reasoning   → Nemotron/DeepSeek R1 (loads if needed)
  status      → Gemma 12B (efficient)
  general     → Main brain (avoids loading overhead)

Resource Management:
  - Max 3 models: Main brain + 2 specialists
  - Auto-cleanup after 15min idle
  - Smart GPU/CPU/RAM monitoring
```

**🌐 CLOUD + LOCAL MODE** (Hybrid Power):
```
Task Type → Model Priority Chain
status     → local → glm-4.5-air → qwen
code       → local → qwen/qwen3-coder:free → glm
reasoning  → local → r1 → nemotron
```

**Rate Limiting**:
- Cloud: Separate buckets for chat (30/min) and background (30/min) operations
- Local: Resource-based (CPU/RAM threshold monitoring)

### System Components
The system is organized into several key components:

1. **Core Services** (`duckbot/core/`) - Fundamental system components including dynamic model management, hardware detection, and context management
2. **AI Services** (`duckbot/ai/`) - AI routing and model management
3. **Agents** (`duckbot/agents/`) - Multi-agent framework with specialized capabilities
4. **Integrations** (`duckbot/integrations/`) - Third-party service integrations (VibeVoice, LiveKit, MCP, etc.)
5. **Platforms** (`duckbot/platforms/`) - Cross-platform support and privacy modes
6. **Services** (`duckbot/services/`) - Server management and web UI components
7. **Tools** (`duckbot/tools/`) - Utility functions and helper scripts

## Key Entry Points

### Main Launcher
- `START_ENHANCED_DUCKBOT.bat` - Primary Windows interface with multiple startup modes
- `start_ecosystem.py` - Python-based service orchestration
- `ai_ecosystem_manager.py` - AI-enhanced ecosystem monitoring

### Web Interface
- `duckbot/services/webui_manager.py` - Unified web dashboard (port 8787)
- React-based UI in `duckbot/react-webui/`

### Discord Bot
- `ai_ecosystem_manager.py` - Main Discord bot implementation

## Building and Running

### Quick Start (Production Ready)
```bash
# 🏠 LOCAL-ONLY MODE - Privacy First (Windows)
START_LOCAL_ONLY.bat                    # One-click local privacy mode

# 🌐 FULL LAUNCHER - All Options (Windows)
START_ENHANCED_DUCKBOT.bat

# Options:
# L. 🏠 LOCAL-ONLY Complete Unified Setup (NEW!)
# 1. 🌟 AI-Enhanced WebUI Dashboard (Cloud + Local)
# 2. 🖥️ WebUI Dashboard Only (Manual Control)
# 3. 🤖 AI-Enhanced Headless (Server Mode)
# Q. ⚡ Ultra-Fast Start (One-click with optimizations)
```

### Direct Python Commands
```bash
# 🏠 LOCAL-ONLY MODE
python start_local_ecosystem.py         # NEW: Complete local privacy mode
python model_status.py                  # NEW: Dynamic model manager status
CHECK_MODEL_STATUS.bat                  # NEW: Model usage analytics

# Core ecosystem management
python start_ecosystem.py               # Enterprise service orchestration
python ai_ecosystem_manager.py          # AI-enhanced management
python start_ai_ecosystem.py            # AI startup with monitoring

# WebUI and interfaces
python -m duckbot.webui                 # Professional dashboard (works offline)
python chat_with_ai.py                  # Interactive AI chat
python start_cost_dashboard.py          # Cost analytics dashboard

# Service testing
python -c "from duckbot.integrations.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"
```

### Manual Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Go tools (required for Charm ecosystem)
winget install GoLang.Go
go install github.com/charmbracelet/gum@latest
go install github.com/charmbracelet/glow@latest
go install github.com/charmbracelet/mods@latest
go install github.com/charmbracelet/skate@latest
go install github.com/charmbracelet/crush@latest
go install github.com/charmbracelet/charm@latest
go install github.com/charmbracelet/freeze@latest
go install github.com/charmbracelet/vhs@latest

# Install Node.js dependencies for React WebUI
cd duckbot/react-webui
npm install

# Install Claude Code Router
npm install -g @musistudio/claude-code-router

# Install Qwen-Agent
pip install qwen-agent

# Install Browser-Use
pip install browser-use

# Launch complete system
python start_ai_ecosystem.py
```

### Development Setup
```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# Edit .env with your API keys

# Launch enhanced system
python start_ai_ecosystem.py
```

## System Requirements

### Minimum Requirements
- Windows 10/11 (WSL2 for enhanced features)
- Python 3.8+ (3.10+ recommended)
- 4GB RAM minimum (8GB+ recommended)
- 2GB free disk space
- Go 1.20+ (auto-installed by setup script)

### Recommended for Full Experience
- 16GB RAM for optimal multi-agent performance
- NVIDIA GPU for AI acceleration (optional)
- Node.js 16+ for React WebUI components
- WSL2 for Linux integration
- Git for development features

## Key Features

### AI Memory System (Memento)
Persistent conversation memory that learns from interactions and improves responses over time.

### Desktop Automation (ByteBot)
Natural language control of Windows applications with screenshot analysis and UI interaction.

### Multi-Agent Framework (Archon)
Deploy specialized AI agents for different tasks with coordination and knowledge sharing.

### Terminal Ecosystem (Charm)
Beautiful terminal interfaces using Charm tools (Gum, Glow, Mods, Skate, Crush, Freeze, VHS).

### Spec-Driven Development
Create specifications that automatically generate code and documentation.

### Advanced AI Router
Intelligent model selection across providers with cost optimization and fallback chains.

### VibeVoice TTS
Multi-speaker voice generation with Microsoft's open-source text-to-speech system.

### LiveKit WebRTC
Real-time video conferencing and audio broadcasting with Discord integration.

### Claude Code Router Integration
Advanced code routing and execution with Claude Code Router for OpenRouter free models.

### Qwen-Agent Integration
Sophisticated AI agent framework with tool use and workflow management.

### Browser-Use Integration
Web automation and browsing capabilities through the browser-use integration.

### Web-UI Integration
Enhanced web interface with advanced features and integrations.

### Persona Engine Integration
Character animation and voice synthesis through the persona engine integration.

### Cryptocurrency Mining Integration
Comprehensive cryptocurrency mining management with support for MultiPoolMiner and NPlusMiner:
- Start/stop mining operations through web interface, Electron desktop app, or Discord commands
- Real-time mining statistics and performance monitoring
- AI-powered mining optimization recommendations
- Support for multiple mining algorithms and coins
- Profitability analysis and pool recommendations

### Docker MCP Gateway Integration
Container management and service orchestration through Docker MCP Gateway:
- Docker container management for MCP servers
- Service discovery and orchestration
- Health monitoring and auto-recovery

### WSL Integration
Native Linux commands and development environment on Windows:
- Full bash/shell integration within DuckBot
- Linux development tools and package management
- Cross-platform workflow support

## Configuration Files

### Environment Configuration (.env)

**🏠 LOCAL-ONLY MODE** (.env.local - auto-generated):
```bash
# Local-only configuration (automatically set)
AI_LOCAL_ONLY_MODE=true
DISABLE_OPENROUTER=true
ENABLE_LM_STUDIO_ONLY=true
ENABLE_DYNAMIC_LOADING=true           # NEW: Dynamic model loading
LM_STUDIO_URL=http://localhost:1234

# Local resource optimization
AI_CONFIDENCE_MIN=0.65                # Lower for local models
AI_LOCAL_CONF_MIN=0.60
MAX_MEMORY_THRESHOLD=85.0
DUCKBOT_WEBUI_HOST=127.0.0.1
DUCKBOT_WEBUI_PORT=8787

# Feature toggles (all work offline)
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
```

**🌐 CLOUD + LOCAL MODE** (.env):
```bash
# Required for cloud features
DISCORD_TOKEN=your_discord_token
OPENROUTER_API_KEY=your_openrouter_key  # Optional with local fallback

# AI Router Configuration
AI_CONFIDENCE_MIN=0.75
AI_LOCAL_CONF_MIN=0.68
OPENROUTER_BUDGET_PER_MIN=6
AI_TTL_CACHE_SEC=60

# WebUI Security
DUCKBOT_WEBUI_HOST=127.0.0.1
DUCKBOT_WEBUI_PORT=8787

# Feature Toggles
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
MAX_MEMORY_THRESHOLD=85.0
```

### Main Configuration
- `ecosystem_config.yaml` - Service ports and basic settings
- `ai_config.json` - AI provider and model settings
- `enhanced_config.json` - Enhanced feature configuration
- `hardware_config.json` - Hardware detection and optimization settings

### Environment Variables
- `.env` - API keys and sensitive configuration
- `.env.example` - Template for environment setup

## Development Patterns

### Service Architecture
All major integrations follow consistent patterns:
- `start_service()` method for background operation
- `start_interactive_mode()` for direct interaction
- Comprehensive error handling and graceful degradation
- Async/await patterns for proper concurrency

### Error Handling
- Unified logging system in `duckbot/core/logging_setup.py`
- Health monitoring via `duckbot/services/monitoring_dashboard.py`
- Automatic service recovery and fallback mechanisms
- Detailed error reporting with context preservation

### Cross-Platform Support
- Windows path handling with proper escaping
- WSL integration with automatic detection
- Platform-specific feature fallbacks
- Unicode support throughout

## Testing and Validation

### Test Structure
- Individual integration testing scripts
- System-wide validation tools
- Performance and health monitoring
- Comprehensive feature testing

### Running Tests
```bash
# Complete system validation
python tests/test_all_features.py

# Service health checks
python doctor_check_services.py

# Import validation
python doctor_check_imports.py

# Generate diagnostic report
python doctor_generate_report.py

# Component Development
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787
python ai_ecosystem_manager.py --host 127.0.0.1 --port 8789
python -m duckbot.charm_terminal_ui
python -m duckbot.monitoring_dashboard

# Code quality and linting
ruff check duckbot/
mypy duckbot/
black duckbot/
```

## File Structure
```
DuckBot-Consolidated-v4.2/
├── README.md                       # Main project documentation
├── START_LOCAL_ONLY.bat            # NEW: One-click local privacy mode
├── start_local_ecosystem.py        # NEW: Local-only startup script
├── model_status.py                 # NEW: Dynamic model analytics
├── test_local_feature_parity.py    # NEW: Local-cloud parity testing
├── CHECK_MODEL_STATUS.bat          # NEW: Model usage monitoring
├── TEST_LOCAL_PARITY.bat           # NEW: Feature parity validation
├── START_ENHANCED_DUCKBOT.bat      # Main Windows launcher
├── start_ecosystem.py              # Service orchestration
├── ai_ecosystem_manager.py         # AI-enhanced ecosystem monitoring
├── requirements.txt                # Python dependencies
├── ecosystem_config.yaml           # Ecosystem configuration
├── ai_config.json                  # AI provider settings
├── enhanced_config.json            # Enhanced features config
├── hardware_config.json            # Hardware detection
├── duckbot/                       # Core modules
│   ├── __init__.py                # Package initialization
│   ├── dynamic_model_manager.py    # NEW: Intelligent model loading/unloading
│   ├── local_feature_parity.py     # NEW: Complete cloud feature equivalence
│   ├── enhanced_webui.py           # Modern web interface
│   ├── ai_router_gpt.py            # Enhanced with local-only mode
│   ├── core/                      # Fundamental components
│   │   ├── __init__.py
│   │   ├── dynamic_model_manager.py
│   │   ├── hardware_detector.py
│   │   ├── logging_setup.py
│   │   ├── context_manager.py
│   │   ├── cost_management.py
│   │   ├── rate_limit.py
│   │   ├── rag.py
│   │   └── settings_menu.py
│   ├── ai/                        # AI routing and management
│   │   └── __init__.py
│   ├── agents/                    # Multi-agent framework
│   │   ├── __init__.py
│   │   ├── intelligent_agents.py
│   │   ├── learning_system.py
│   │   ├── metagpt_archon_integration.py
│   │   ├── mining_commands.py
│   │   ├── qwen_diagnostics.py
│   │   ├── vibevoice_commands.py
│   │   └── visual_workflow_designer.py
│   ├── integrations/              # Third-party integrations
│   │   ├── __init__.py
│   │   ├── archon_integration.py
│   │   ├── browser_use_integration.py
│   │   ├── bytebot_integration.py
│   │   ├── claude_code_integration.py
│   │   ├── docker_mcp_gateway.py
│   │   ├── livekit_integration.py
│   │   ├── memento_integration.py
│   │   ├── mining_manager.py
│   │   ├── persona_engine_integration.py
│   │   ├── qwen_agent_integration.py
│   │   ├── vibevoice_client.py
│   │   └── web_ui_integration.py
│   ├── platforms/                 # Cross-platform support
│   ├── services/                  # Server and UI management
│   │   ├── __init__.py
│   │   ├── webui_manager.py
│   │   ├── monitoring_dashboard.py
│   │   ├── server_manager.py
│   │   ├── ai_router_manager.py
│   │   └── integration_manager.py
│   ├── tools/                     # Utility functions
│   └── react-webui/               # Web interface
├── launcher/                      # Startup scripts and launchers
├── core_ai/                       # Core AI and routing modules
├── integrations/                  # Integration modules
├── config/                        # Configuration files
├── utils/                         # Utility and helper scripts
├── docs/                          # Documentation files
├── tests/                         # Test files
├── diagnostics/                   # Diagnostic tools
├── DuckBot-DE/                    # DuckBot Desktop Environment
├── logs/                          # System logs
└── data/                          # Data files
```

## Common Issues

### 🏠 LOCAL-ONLY MODE Issues
- **LM Studio Not Detected**: Ensure LM Studio is running with local server enabled (localhost:1234)
- **No Models Loaded**: Load at least one chat model in LM Studio before starting DuckBot
- **Main Brain Failed**: Check GPU/RAM availability, try smaller models first
- **Model Loading Failed**: Monitor system resources via `CHECK_MODEL_STATUS.bat`
- **Resource Exhaustion**: Dynamic manager will auto-cleanup, or manually restart

### 🌐 CLOUD + LOCAL MODE Issues
- **API Key Errors**: Check `.env` file for correct OpenRouter API key format
- **Rate Limiting**: Monitor cost dashboard, consider local-only mode for heavy usage
- **Model Fallback Issues**: Verify local models are loaded as fallback option

### 🔧 GENERAL TROUBLESHOOTING
- **ModuleNotFoundError**: Run dependency installation via launcher
- **WebUI Access Denied**: Check token URL in terminal output, ensure localhost binding
- **Unicode Errors**: Fixed in v4.2+ with proper UTF-8 encoding
- **Service Conflicts**: Use emergency kill options to reset all processes

### Dependency Management
Use the launcher's "Install Components" option or run:
```bash
pip install -r requirements.txt
```

### Port Conflicts
Common ports: 8787 (WebUI), 8788 (Terminal), 8789 (Monitoring), 8790 (MCP Server), 1234 (LM Studio)
Use system status option to check availability.

### 🧪 Diagnostic Tools
- **TEST_LOCAL_PARITY.bat**: Verify all features work in both modes
- **CHECK_MODEL_STATUS.bat**: Monitor dynamic model manager and resource usage
- **python model_status.py**: Detailed model usage analytics and system resources
- **Professional WebUI dashboard**: Real-time monitoring (works offline in local mode)
- **python test_every_feature.py**: Comprehensive system validation

### Unicode Handling
All scripts enforce UTF-8 encoding. Ensure terminal supports Unicode for proper display.

## Feature Status

### Claude Code Router
✅ Available and properly configured
- Installed via npm: `npm install -g @musistudio/claude-code-router`
- API key configured for OpenRouter integration
- Free models accessible: Phi-3, Gemma, LLaMA-3, Mistral, Zephyr

### Qwen-Agent
✅ Available and properly configured
- Installed via pip: `pip install qwen-agent`
- Integrated with OpenRouter for free models
- Advanced tool use and workflow management capabilities

### Browser-Use Integration
✅ Available and properly configured
- Web automation and browsing capabilities
- Screenshot analysis and UI interaction
- Multi-tab browsing support

### Web-UI Integration
✅ Available and properly configured
- Enhanced web interface with advanced features
- React-based UI with modern design
- Real-time updates and WebSocket support

### Persona Engine Integration
✅ Available and properly configured
- Character animation and voice synthesis
- Emotion expression and gesture control
- Multi-character support

### Cryptocurrency Mining Integration
✅ Available and properly configured
- MultiPoolMiner and NPlusMiner support
- Web interface controls for mining operations
- Real-time mining statistics and monitoring
- AI-powered mining optimization
- Profitability analysis and recommendations

### Docker MCP Gateway
✅ Available and properly configured
- Docker container management for MCP servers
- Service discovery and orchestration
- Health monitoring and auto-recovery

### WSL Integration
✅ Available and properly configured
- Linux command execution on Windows
- Cross-platform workflow support
- Package management and development tools

## Local Model Inventory
| Model | Size | Specialty | Best For |
|-------|------|-----------|----------|
| Nvidia Llama 3.3 Nemotron Super 49B | 49B | Reasoning | Complex tasks |
| Qwen3 Coder 30B | 30B | Coding | Programming |
| Qwen3 30B A3B | 30B | General | Balanced reasoning |
| Qwen2.5 Coder 32B | 32B | Coding | Debugging |
| QwQ 32B | 32B | Q&A | Answers |
| GPT-OSS 120B | 120B | General | Long prompts |
| GPT-OSS 20B | 20B | General | Efficiency |
| Gemma-3 12B | 12B | Instructions | Short tasks |
| Devstral Small | Small | Development | Mistral model |

## Important Notes

### 🏠 LOCAL-ONLY MODE
- **LM Studio Required**: Essential for local-only mode operation (localhost:1234)
- **Model Loading**: Main brain established on startup, specialists loaded dynamically
- **Complete Privacy**: Zero external API calls, all processing on your hardware
- **Resource Management**: Smart GPU/CPU/RAM monitoring with automatic cleanup
- **Feature Parity**: ALL cloud features work locally (RAG, caching, analytics, WebUI)
- **Zero Cost**: $0 API fees, comprehensive usage tracking instead of cost tracking

### 🌐 CLOUD + LOCAL MODE
- **OpenRouter API Key**: Optional but recommended for cloud model access
- **Local AI Preferred**: LM Studio used when available for cost optimization
- **Intelligent Fallbacks**: Cloud → Local or Local → Cloud based on availability
- **Hybrid Intelligence**: Best of both worlds with smart routing

### 🔧 GENERAL SYSTEM
- **Thread Safety Critical**: All cache operations use proper locking
- **Security First**: Never log API keys or sensitive information
- **Production Ready**: System designed for 24/7 operation with auto-recovery
- **Resource Monitoring**: Dynamic adjustment based on system capabilities

### Multi-Provider AI Support
The system integrates multiple AI providers (OpenAI, Anthropic, Qwen, local models) with intelligent routing based on task complexity, cost, and availability.

### Service Health Monitoring
Comprehensive monitoring system tracks service health, performance metrics, and automatic recovery across all integrations.

### Memory and Learning
Advanced memory system maintains context across sessions and learns from interactions to improve response quality over time.

### Enterprise Features
Production-ready with comprehensive error handling, logging, security features, and scalability considerations.

## Support & Documentation
- `CLAUDE.md` - Technical docs for Claude Code
- `QWEN.md` - This consolidated documentation
- Option 4 (Doctor Mode) - Diagnostics
- Option 7 (System Tests) - Validation

**AI Integration Note:** This project uses actual local models in `C:\Users\Duck1\.lmstudio\hub\models`. The main brain is `qwen/qwen3-coder:free` for server management. All models configurable via `.env` variables.
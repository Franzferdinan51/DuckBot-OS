# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

DuckBot v4.2 is an enterprise-grade AI-managed ecosystem featuring **revolutionary local-first architecture** and **complete cloud feature parity**. Choose between powerful cloud AI or complete privacy with local models - both modes offer identical intelligence and capabilities with comprehensive integration architecture including ByteBot desktop automation, multi-agent systems, terminal interfaces, and cross-platform support.

**Key Differentiators**:
- **Local-First Revolution**: Complete privacy mode with full feature parity
- **Dynamic Model Management**: Intelligent loading/unloading based on tasks and system resources
- **Main Brain + Specialists**: Persistent orchestration model + auto-loading task-specific models
- **Resource Intelligence**: Smart GPU/CPU/RAM management with background cleanup
- **Zero Cost Local**: $0 API costs with comprehensive local analytics
- **Complete Privacy**: All processing stays on your machine in local-only mode

## Architecture

### Core Entry Points

**Main Launcher** (`START_ENHANCED_DUCKBOT.bat`):
- Primary Windows interface with 15+ startup modes including new local-only mode
- Service orchestration and health monitoring
- Automatic dependency detection and installation
- Cross-platform compatibility checks

**Python Orchestration**:
- `start_ecosystem.py` - Service lifecycle management
- `ai_ecosystem_manager.py` - AI-enhanced ecosystem monitoring
- `start_ai_ecosystem.py` - AI service coordination
- `start_local_ecosystem.py` - **NEW**: Privacy-first local-only startup

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

### Key Integrations

**🤖 Multi-Agent Framework** (`duckbot/intelligent_agents.py`, `duckbot/archon_integration.py`):
- Deploy specialized AI agents for different tasks
- Agent coordination and knowledge sharing
- Real-time collaboration and task distribution

**🖥️ Desktop Automation** (`duckbot/bytebot_integration.py`):
- Natural language control of Windows applications
- Screenshot analysis and UI interaction
- Multi-step workflow automation

**🧠 AI Router System** (`duckbot/ai_router_gpt.py`, `duckbot/dynamic_model_manager.py`):
- Intelligent model selection across providers
- Cost optimization and performance balancing
- Fallback chains for reliability

**💾 Memory & Learning** (`duckbot/memento_integration.py`, `duckbot/learning_system.py`):
- Persistent conversation memory across sessions
- Case-based learning and pattern recognition
- Adaptive response improvement

**🌐 Cross-Platform Integration** (`duckbot/wsl_integration.py`):
- Windows Subsystem for Linux support
- Docker container management
- Development environment orchestration

**🎨 Terminal Ecosystem** (`duckbot/charm_terminal_ui.py`, `duckbot/charm_ecosystem.py`):
- Beautiful terminal interfaces using Charm tools
- Interactive menus and configuration
- Rich text rendering and forms

## Development Commands

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
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"
```

### Testing
```bash
# Comprehensive feature testing
python tests/test_all_features.py
python tests/test_enhanced_duckbot.py
python tests/test_every_feature.py

# Integration validation
python doctor_check_imports.py
python doctor_check_services.py
python doctor_generate_report.py

# Code quality and linting
ruff check duckbot/
mypy duckbot/
black duckbot/
```

### Component Development
```bash
# Enhanced WebUI development
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

# System monitoring
python ai_ecosystem_manager.py --host 127.0.0.1 --port 8789

# Individual component testing
python -m duckbot.charm_terminal_ui
python -m duckbot.monitoring_dashboard
```

## Configuration

### Environment Setup
- **Python**: 3.8+ required (3.11+ recommended)
- **Dependencies**: Managed via `requirements.txt`
- **Optional**: Node.js for Electron components, Go for Charm tools
- **Encoding**: UTF-8 enforced throughout

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

### Key Configuration Files
- `ecosystem_config.yaml` - Service management settings
- `enhanced_config.json` - Enhanced feature configuration
- `ai_config.json` - AI provider and model settings
- `hardware_config.json` - Hardware detection and optimization

## Development Patterns

### Service Architecture
All major integrations follow consistent patterns:
- `start_service()` method for background operation
- `start_interactive_mode()` for direct interaction
- Comprehensive error handling and graceful degradation
- Async/await patterns for proper concurrency

### Error Handling
- Unified logging system in `duckbot/logging_setup.py`
- Health monitoring via `duckbot/observability.py`
- Automatic service recovery and fallback mechanisms
- Detailed error reporting with context preservation

### Cross-Platform Support
- Windows path handling with proper escaping
- WSL integration with automatic detection
- Platform-specific feature fallbacks
- Unicode support throughout

## Testing and Validation

### Test Structure
- `tests/` directory contains comprehensive test suites
- Individual integration testing scripts
- System-wide validation tools
- Performance and health monitoring

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
```

## File Structure

```
DuckBot-Consolidated-v4.2/
├── START_LOCAL_ONLY.bat            # NEW: One-click local privacy mode
├── start_local_ecosystem.py        # NEW: Local-only startup script
├── model_status.py                 # NEW: Dynamic model analytics
├── test_local_feature_parity.py    # NEW: Local-cloud parity testing
├── CHECK_MODEL_STATUS.bat          # NEW: Model usage monitoring
├── TEST_LOCAL_PARITY.bat           # NEW: Feature parity validation
├── START_ENHANCED_DUCKBOT.bat      # Main Windows launcher
├── start_ecosystem.py              # Service orchestration
├── ai_ecosystem_manager.py         # AI-enhanced management
├── requirements.txt                # Python dependencies
├── duckbot/                        # Core modules
│   ├── dynamic_model_manager.py    # NEW: Intelligent model loading/unloading
│   ├── local_feature_parity.py     # NEW: Complete cloud feature equivalence
│   ├── enhanced_webui.py           # Modern web interface
│   ├── ai_router_gpt.py            # Enhanced with local-only mode
│   ├── bytebot_integration.py      # Desktop automation
│   ├── intelligent_agents.py       # Multi-agent framework
│   ├── memento_integration.py      # Memory/learning system
│   ├── charm_terminal_ui.py        # Terminal interface
│   ├── wsl_integration.py          # Linux subsystem
│   ├── server_manager.py           # Service orchestration
│   ├── cost_tracker.py             # Enhanced with local usage analytics
│   ├── qwen_diagnostics.py         # Advanced diagnostics
│   └── templates/                  # WebUI templates
├── tests/                          # Test suites
│   ├── test_all_features.py        # Comprehensive testing
│   ├── test_enhanced_duckbot.py    # Enhanced feature validation
│   └── README.md                   # Test documentation
├── tools/                          # External tool integrations
├── logs/                           # System logs
└── config/                         # Configuration files
```

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
- **Service Conflicts**: Use `EMERGENCY_KILL.bat` to reset all processes

### Dependency Management
Use the launcher's "Install Components" option or run:
```bash
python -m pip install -r requirements.txt
```

### Port Conflicts
Common ports: 8787 (WebUI), 8788 (Terminal), 8789 (Monitoring), 1234 (LM Studio)
Use system status option to check availability.

### 🧪 Diagnostic Tools
- **TEST_LOCAL_PARITY.bat**: Verify all features work in both modes
- **CHECK_MODEL_STATUS.bat**: Monitor dynamic model manager and resource usage
- **python model_status.py**: Detailed model usage analytics and system resources
- **Professional WebUI dashboard**: Real-time monitoring (works offline in local mode)
- **python test_every_feature.py**: Comprehensive system validation
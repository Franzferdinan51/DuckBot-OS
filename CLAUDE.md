# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DuckBot Enhanced v4.2 is a comprehensive AI-powered operating system featuring Qwen3-Omni as the main brain, desktop automation, multi-agent coordination, local AI capabilities, and cross-platform integration. The system supports both cloud-based AI services and complete local-only privacy modes with full feature parity. This is a consolidated architecture that has achieved 85% reduction in batch files, 90% in utilities, and 75% in core modules while maintaining all functionality.

## Key Architecture Update: Qwen3-Omni Integration

The system now features **Qwen3-Omni as the primary AI brain** with comprehensive multimodal capabilities:
- **Main Brain**: Qwen3-Omni-30B-A3B-Instruct with Flash Attention 2
- **FastAPI Server**: OpenAI-compatible API server on port 5000
- **Combined Service**: Brain and server run in single process for reliability
- **UI Integration**: React/TypeScript UI with proper endpoint configuration

## Architecture

### Core System Components

**Main Application Entry Points:**
- `launcher/CONSOLIDATED_DUCKBOT_LAUNCHER.bat` - Primary Windows launcher with 15+ startup modes
- `START_LOCAL_ONLY.bat` - One-click local privacy mode startup
- `start_ecosystem.py` - Service orchestration and management
- `ai_ecosystem_manager.py` - AI-enhanced ecosystem monitoring with intelligent decision-making

**AI Architecture:**
- **Local-Only Mode**: Main brain (Qwen3 Coder 30B) + dynamic specialist loading
- **Hybrid Mode**: Cloud + Local AI with intelligent routing and fallbacks
- **Multi-Provider Support**: OpenAI, Anthropic, Qwen, LM Studio, and local models
- **AI-Powered Management**: Intelligent ecosystem monitoring and automated decision-making

### Service Management Architecture

The system uses a unified service management architecture with 5 categories:

**Core Services** (`duckbot/core/service_manager.py`):
- **LM Studio Server**: Local AI model hosting (port 1234)
- **AI Provider Manager**: Unified integration across multiple AI providers
- **Service Manager**: Centralized service lifecycle management
- **Dynamic Model Manager**: Intelligent model loading/unloading based on system resources
- **Hardware Detector**: System resource monitoring and optimization
- **Cost Management**: Usage tracking and cost optimization

**Integration Services**:
- **Archon Integration**: Multi-agent framework coordination
- **ByteBot Integration**: Desktop automation and natural language control
- **MCP Server**: Model Context Protocol server
- **VibeVoice Client**: Text-to-speech integration
- **Browser-Use Integration**: AI-powered web automation

**Enhanced Services**:
- **Enhanced WebUI**: Professional web dashboard
- **Monitoring Dashboard**: Real-time system monitoring
- **Intelligent Agents**: AI agent coordination
- **Observability**: Comprehensive logging and metrics
- **Context Manager**: Persistent conversation memory

### AI-Powered Ecosystem Management

The `ai_ecosystem_manager.py` provides intelligent ecosystem monitoring:

**Core Features:**
- **Caching System**: SQLite-based caching for AI API calls with rate limiting
- **Multi-Provider Support**: Automatic fallback between AI providers
- **Intelligent Decision-Making**: AI analyzes system state and makes management decisions
- **Pattern Recognition**: Identifies error patterns and performance trends
- **Automated Recovery**: Self-healing capabilities for service failures

**Key Components:**
```python
class AIEcosystemManager:
    """AI-powered ecosystem management with intelligent decision-making"""

    async def analyze_and_decide(self, system_state: SystemState) -> Optional[AIDecision]:
        """Analyze system state and make management decisions"""
        context = {
            "current_time": system_state.timestamp.isoformat(),
            "services": {name: status.value for name, status in system_state.services_status.items()},
            "system_metrics": system_state.system_metrics,
            "recent_events": system_state.recent_events[-10:],
            "error_patterns": system_state.error_patterns,
            "performance_trends": system_state.performance_trends,
            "restart_counts": {k: v for k, v in self.restart_counts.items() if v > 0}
        }
```

### Key Integrations

**🤖 Multi-Agent Framework**:
- **Specialized AI Agents**: Different agents for various task types
- **Agent Coordination**: Knowledge sharing and collaborative problem-solving
- **Dynamic Deployment**: Automatic scaling based on workload
- **Cross-Agent Learning**: Shared knowledge base for continuous improvement

**🖥️ Desktop Automation**:
- **Natural Language Control**: Control Windows applications with plain English
- **UI-TARS Integration**: Advanced GUI automation capabilities
- **Screenshot Analysis**: Visual understanding and interaction
- **Application Integration**: Works with any Windows application

**💾 Memory & Learning**:
- **Persistent Memory**: SQLite-based conversation storage across sessions
- **Case-Based Learning**: Pattern recognition and adaptive responses
- **Knowledge Graph**: Interconnected understanding of concepts
- **Continuous Improvement**: Self-optimizing response quality

**🌐 Cross-Platform Integration**:
- **WSL Support**: Windows Subsystem for Linux integration
- **Docker Management**: Container orchestration and monitoring
- **Development Environment**: Automated setup and management
- **Platform Detection**: Automatic feature adaptation

## Development Commands

### Quick Start
```bash
# 🧠 QWEN3-OMNI MAIN BRAIN STARTUP
python start_qwen_brain_and_server.py   # Combined brain + server (port 5000)
python start_qwen_brain.py             # Brain only (voice assistant)
python qwen3_omni_server.py            # API server only

# 🏠 LOCAL-ONLY MODE - Privacy First
START_LOCAL_ONLY.bat                    # One-click local privacy mode
python start_local_ecosystem.py         # Local-only startup script

# 🌐 FULL LAUNCHER - All Options
START_ELECTRON_LAUNCHER.bat             # Main Windows launcher with Qwen3-Omni

# Direct Python commands
python start_ecosystem.py               # Enterprise service orchestration
python ai_ecosystem_manager.py          # AI-enhanced management
python chat_with_ai.py                  # Interactive AI chat
python -m duckbot.webui                 # Professional dashboard
```

### Testing and Diagnostics
```bash
# Qwen3-Omni specific testing
python test_qwen3_omni.py                # Qwen3-Omni integration test
python test_launcher_simple.bat           # Qwen3-Omni launcher test
TEST_MODEL_LOADING.bat                   # Model loading diagnostics
TEST_TRANSFORMERS.bat                    # Transformers library test

# Comprehensive testing
python tests/unified_test_suite.py      # Complete unified test suite
python tests/test_all_features.py        # Complete feature validation
python tests/test_enhanced_duckbot.py    # Enhanced feature testing
python tests/test_every_feature.py      # System-wide validation

# Diagnostic tools
python diagnostics/doctor_check_services.py    # Service health checks
python diagnostics/doctor_check_imports.py     # Import validation
python diagnostics/doctor_generate_report.py   # System diagnostic report

# Code quality
ruff check duckbot/                       # Linting
mypy duckbot/                            # Type checking
black duckbot/                           # Code formatting
```

### Component Development
```bash
# Qwen3-Omni UI Development
cd qwen3-omni-ui && npm run dev             # React UI dev server (port 5173)
cd qwen3-omni-ui && npm run build           # Production build

# Qwen3-Omni Server Development
python qwen3_omni_server.py                # API server only (port 5000)
python start_qwen_brain_and_server.py     # Combined brain + server

# WebUI development
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

# AI Ecosystem Management
python ai_ecosystem_manager.py --host 127.0.0.1 --port 8789

# Desktop automation testing
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"

# Service monitoring
python -c "from duckbot.core.service_manager import UnifiedServiceManager; manager = UnifiedServiceManager(); asyncio.run(manager.start_all_services())"
```

## Configuration

### Environment Setup
- **Python**: 3.8+ required (3.11+ recommended)
- **Dependencies**: `docs/requirements.txt` contains all Python dependencies
- **Optional**: Node.js for React components, Go for Charm tools

### Key Configuration Files
- `config/ai_config.json` - AI provider and model settings
- `config/ecosystem_config.yaml` - Service management
- `config/hardware_config.json` - Hardware detection and optimization
- `config/qwen3_omni_config.json` - Qwen3-Omni model configuration
- `.env` - Environment variables (API keys, feature toggles)

### Important Ports
- **5000**: Qwen3-Omni API server (main brain)
- **5173**: Qwen3-Omni UI development server
- **8787**: Enhanced WebUI
- **8788**: Terminal interface
- **8789**: AI ecosystem manager
- **1234**: LM Studio server (local fallback)

### Environment Variables
```bash
# AI Configuration
AI_CONFIDENCE_MIN=0.75
AI_LOCAL_CONF_MIN=0.68
OPENROUTER_API_KEY=your_key_here
DISCORD_TOKEN=your_discord_token

# Local-Only Mode
AI_LOCAL_ONLY_MODE=true
ENABLE_LM_STUDIO_ONLY=true
LM_STUDIO_URL=http://localhost:1234

# Feature Toggles
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
```

## Development Patterns

### Service Architecture
All major integrations follow consistent patterns:
- `start_service()` method for background operation
- `start_interactive_mode()` for direct interaction
- Comprehensive error handling and graceful degradation
- Async/await patterns for proper concurrency
- Health monitoring and automatic recovery

### AI-Powered Decision Making
The system uses AI for intelligent management:
- **System State Analysis**: Real-time monitoring of all services
- **Pattern Recognition**: Identifies recurring issues and trends
- **Automated Decisions**: AI makes management decisions based on system state
- **Self-Healing**: Automatic recovery from service failures
- **Resource Optimization**: Dynamic adjustment based on system capabilities

### Caching and Performance
- **SQLite Caching**: Persistent caching for AI API responses
- **Rate Limiting**: Intelligent API call management
- **Memory Management**: Automatic cleanup and resource optimization
- **Performance Monitoring**: Real-time performance metrics and trends

### Error Handling
- **Unified Logging**: Comprehensive logging system in `duckbot/core/logging_setup.py`
- **Health Monitoring**: Real-time service health checks
- **Automatic Recovery**: Self-healing capabilities for service failures
- **Detailed Reporting**: Context-preserving error reporting
- **Pattern Analysis**: Identifies recurring error patterns

### Cross-Platform Support
- **Windows Path Handling**: Proper path escaping and normalization
- **WSL Integration**: Automatic detection and configuration
- **Platform-Specific Features**: Adaptive functionality based on platform
- **Unicode Support**: Full UTF-8 encoding throughout

### Browser-Use Integration Development
**Key Patterns for browser-use integration:**
- Use `uv` instead of `pip` for dependency management
- Follow async patterns with proper typing (`str | None` instead of `Optional[str]`)
- Use Pydantic v2 models for all data structures
- Event-driven architecture with service/watchdog pattern
- CDP integration via `cdp-use` wrapper
- **Never create random example files** - test inline if needed

### Core Module Organization
The project uses a consolidated architecture with key modules in `duckbot/core/`:
- `ai_provider_manager.py` - Unified AI provider integration
- `agent_framework.py` - Multi-agent coordination framework
- `service_manager.py` - Service lifecycle management
- `dynamic_model_manager.py` - Intelligent model loading/unloading
- `hardware_detector.py` - System resource detection
- `cost_management.py` - Usage and cost tracking
- `utilities.py` - Consolidated utility functions

## File Structure

```
DuckBot-Consolidated-v4.2/
├── START_ELECTRON_LAUNCHER.bat         # Main Windows launcher
├── START_LOCAL_ONLY.bat               # Local-only privacy mode
├── start_ecosystem.py                 # Service orchestration
├── ai_ecosystem_manager.py            # AI-enhanced management

# Qwen3-Omni Integration (NEW)
├── qwen3_omni_server.py              # FastAPI server (port 5000)
├── start_qwen_brain.py               # Brain startup script
├── start_qwen_brain_and_server.py    # Combined brain + server
├── qwen3-omni-ui/                    # React/TypeScript UI
│   ├── src/                          # UI source code
│   ├── package.json                  # Node.js dependencies
│   └── test-api-connection.html      # Connectivity testing
├── config/qwen3_omni_config.json     # Qwen3-Omni configuration

# Model Management (NEW)
├── DOWNLOAD_MODEL.bat                 # Hugging Face model download
├── CHECK_MODEL_FILES.bat              # Model file verification
├── TEST_MODEL_LOADING.bat             # Model loading diagnostics
├── HF_LOGIN.bat                       # Hugging Face authentication
└── models/                           # Downloaded model files

├── requirements.txt                   # Python dependencies
├── duckbot/                          # Core application
│   ├── core/                          # 12 consolidated core modules
│   │   ├── ai_provider_manager.py    # Unified AI provider integration
│   │   ├── agent_framework.py        # Multi-agent framework
│   │   ├── service_manager.py        # Service management
│   │   ├── dynamic_model_manager.py  # Dynamic model loading
│   │   ├── hardware_detector.py      # Hardware detection
│   │   ├── logging_setup.py          # Unified logging
│   │   ├── cost_management.py        # Cost tracking
│   │   ├── utilities.py              # Consolidated utilities
│   │   └── qwen3_omni_integration.py # Qwen3-Omni brain integration
│   ├── integrations/                  # 15+ integration modules
│   │   ├── archon_integration.py     # Multi-agent framework
│   │   ├── bytebot_integration.py    # Desktop automation
│   │   ├── mcp_server.py             # Model Context Protocol
│   │   ├── vibevoice_client.py       # TTS integration
│   │   └── browser_use_integration.py # Web automation
│   ├── agents/                        # AI agent implementations
│   ├── platforms/                     # Cross-platform support
│   └── services/                      # Server and UI management
├── core_ai/                          # Core AI orchestration modules
├── launcher/                         # Consolidated startup scripts
├── config/                           # Configuration files
├── docs/                            # Documentation and requirements
├── tests/                           # Unified test suite
├── diagnostics/                     # System diagnostic tools
└── utils/                           # Utility modules
```

## Browser-Use Integration

The project includes the `browser-use` library for AI-powered web automation:

**Key Features:**
- **Async Architecture**: Built on async Python using LLMs + CDP (Chrome DevTools Protocol)
- **Event-Driven**: Coordinated watchdog services for reliable operation
- **Multi-LLM Support**: OpenAI, Anthropic, Google, Groq providers
- **MCP Server Mode**: Claude Desktop integration via Model Context Protocol
- **Smart Caching**: Intelligent caching for API responses and web data

**Development Patterns:**
- Use `uv` instead of `pip` for dependency management
- Follow async patterns with proper typing
- Use Pydantic v2 models for data structures
- Event-driven architecture with service/watchdog pattern
- CDP integration via `cdp-use` wrapper

## Important Notes

### System Requirements
- **Windows 10/11** (WSL2 for enhanced features)
- **Python 3.8+** (3.11+ recommended)
- **4GB RAM** minimum (8GB+ recommended for multi-agent features)
- **LM Studio** required for local-only mode operation

### Local-Only Mode
- **LM Studio Required**: Must be running with local server enabled (localhost:1234)
- **Complete Privacy**: Zero external API calls, all processing on local hardware
- **Feature Parity**: All cloud features work locally with $0 API costs
- **Resource Management**: Smart GPU/CPU/RAM monitoring with automatic cleanup
- **AI-Powered**: Full AI decision-making capabilities in local mode

### Development Best Practices
- **Thread Safety**: Critical for all cache operations and service management
- **Security**: Never log API keys or sensitive information
- **Production Ready**: System designed for 24/7 operation with auto-recovery
- **Resource Monitoring**: Dynamic adjustment based on system capabilities
- **AI Enhancement**: Leverage AI for intelligent system management

### Common Issues

#### Qwen3-Omni Specific Issues
- **Port 8000 Connection Errors**: UI trying to connect to old port - clear browser localStorage or use `qwen3-omni-ui/clear-settings.html`
- **Model Loading Failures**: Use `TEST_MODEL_LOADING.bat` for diagnostics, check GPU memory availability
- **API Method Not Found**: Server calling `generate_response` instead of `generate_text` - this has been fixed in latest version
- **Unicode Character Errors**: Fixed in startup scripts - ASCII characters used instead of Unicode
- **Service Communication Issues**: Use combined brain and server (`start_qwen_brain_and_server.py`) for reliability

#### General Issues
- **ModuleNotFoundError**: Run dependency installation via launcher or `python -m pip install -r docs/requirements.txt`
- **WebUI Access**: Check token URL in terminal output, ensure localhost binding
- **Port Conflicts**: Common ports 5000 (Qwen3-Omni), 5173 (UI dev), 8787 (WebUI), 8788 (Terminal), 8789 (Monitoring)
- **LM Studio Detection**: Ensure local server is running before starting local-only mode
- **Unicode Errors**: System enforces UTF-8 encoding throughout

### Testing Strategy
- Use `tests/unified_test_suite.py` for comprehensive testing
- Run specific test categories with `--category` flag
- Use diagnostic tools in `diagnostics/` directory for system health checks
- Test both local-only and hybrid modes for feature parity
- Validate AI decision-making capabilities through scenario testing

### AI Management Capabilities
- **Intelligent Monitoring**: AI continuously monitors system health and performance
- **Pattern Recognition**: Identifies trends and potential issues before they become critical
- **Automated Optimization**: AI makes decisions to optimize system performance
- **Self-Healing**: Automatic recovery from service failures and performance degradation
- **Resource Allocation**: Dynamic resource management based on current system state
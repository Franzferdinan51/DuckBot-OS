# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

DuckBot v3.1.0+ is an enterprise-grade AI-managed crypto ecosystem with **revolutionary integration architecture** featuring complete ByteBot desktop automation, Archon multi-agent systems, Charm terminal interfaces, ChromiumOS system features, and WSL cross-platform support.

**Key Differentiators**: 
- **Ultimate Integration Suite**: ByteBot + Archon + Charm + ChromiumOS + WSL all working together
- **Dynamic AI Routing**: Intelligent model selection and failover systems
- **Professional WebUI**: Real-time monitoring with WebSocket updates
- **Cross-Platform Support**: Windows, Linux, WSL, and macOS compatibility
- **Enterprise-Grade**: Production-ready with comprehensive error handling

## Core Architecture

### Main Components

- **Enhanced WebUI** (`duckbot/enhanced_webui.py`) - Professional real-time dashboard with all integrations
- **AI Router** (`duckbot/ai_router_gpt.py`) - Intelligent multi-model routing and management
- **Server Manager** (`duckbot/server_manager.py`) - Comprehensive service orchestration
- **Cost Tracker** (`duckbot/cost_tracker.py`) - Advanced usage analytics and monitoring

### Integration Architecture

**🚀 ByteBot Integration** (`duckbot/bytebot_integration.py`):
```
Features: Complete desktop automation and control
Capabilities:
  - Screenshot analysis and UI interaction
  - Multi-step task execution and workflows
  - Cross-application automation
  - Natural language task processing
```

**🧠 Archon Multi-Agent System** (`duckbot/archon_integration.py`):
```
Architecture: Advanced AI agent orchestration
Features:
  - Knowledge base management and search
  - Real-time agent collaboration
  - Microservices architecture with MCP protocol
  - Semantic search and RAG capabilities
```

**💻 Charm Terminal Interface** (`duckbot/charm_terminal_ui.py` + `duckbot/charm_ecosystem.py`):
```
Based on: Complete Charm ecosystem (bubbletea, lipgloss, wish, etc.)
Features:
  - Beautiful, color-coded terminal experiences
  - Interactive menus and configuration
  - Multi-model AI session management
  - Model-View-Update (MVU) architecture
```

**🌐 ChromiumOS Integration** (`duckbot/chromium_integration.py`):
```
Inspired by: ChromiumOS architecture and security model
Features:
  - Advanced system-level integration
  - Enhanced security and containerization
  - Cross-platform compatibility features
  - Resource monitoring and optimization
```

**🐧 WSL Integration** (`duckbot/wsl_integration.py`):
```
Platform: Windows Subsystem for Linux
Features:
  - Full WSL distribution management
  - Docker container integration
  - Cross-platform development environment
  - File operations and network configuration
```

### Service Orchestration

**Startup Scripts**:
- `START_ENHANCED_DUCKBOT.bat` - Main Windows launcher with 15+ startup modes
- `start_ecosystem.py` - Python-based service orchestration
- `ai_ecosystem_manager.py` - AI-enhanced ecosystem management with health monitoring

**Available Startup Modes**:
1. **Ultimate Complete Mode** - All integrations active simultaneously
2. **Electron Desktop Edition** - React-based native desktop app
3. **Enhanced WebUI** - Modern web interface with real-time updates
4. **Charm Terminal** - Beautiful command-line interface
5. **ByteBot Desktop Automation** - Task automation and control
6. **Archon Multi-Agent** - AI agent coordination
7. **WSL Integration** - Linux subsystem management
8. **Specialized modes** - Local privacy, hybrid cloud, monitoring, testing

## Development Commands

### Quick Start (Production Ready)
```bash
# Windows Ultimate Launcher
START_ENHANCED_DUCKBOT.bat

# Python Ecosystem Management
python start_ecosystem.py              # Service orchestration
python ai_ecosystem_manager.py         # AI-enhanced management

# Individual Integration Testing
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"
python -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_interactive_mode())"
python -c "from duckbot.wsl_integration import wsl_integration; import asyncio; asyncio.run(wsl_integration.start_interactive_mode())"
```

### Integration Development
```bash
# Enhanced WebUI Development
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

# React Electron UI Development  
cd duckbot/react-webui
npm install
npm run electron:dev

# Charm Terminal Development
python -m duckbot.charm_terminal_ui

# Testing All Integrations
python -c "
integrations = ['bytebot_integration', 'archon_integration', 'wsl_integration', 'chromium_integration']
for integration in integrations:
    try:
        module = __import__(f'duckbot.{integration}', fromlist=[integration])
        print(f'{integration}: Available')
    except Exception as e:
        print(f'{integration}: Error - {e}')
"
```

## Key Configuration Files

### Integration Configuration
- Each integration includes `start_service()` and `start_interactive_mode()` methods
- All integrations support async/await patterns for proper concurrency
- Comprehensive error handling and graceful degradation

### Environment Setup
- Python 3.8+ required for optimal compatibility
- Node.js required for React Electron UI components  
- Cross-platform file path handling using `pathlib.Path`
- UTF-8 encoding enforced for Unicode compatibility

## Architecture Patterns

### Async/Await Integration
- All integrations use proper asyncio patterns
- Background services with heartbeat monitoring
- Graceful shutdown handling with cleanup

### Error Handling Hierarchy
- Comprehensive try-catch blocks in all integration methods
- Graceful degradation when dependencies are unavailable
- Detailed logging with appropriate severity levels

### Cross-Platform Compatibility
- Path operations use `pathlib.Path` for cross-platform support
- Platform-specific feature detection and fallbacks
- Windows WSL integration with Linux environment detection

## Common Development Tasks

### Adding New Integrations
1. Create integration file in `duckbot/` directory
2. Implement `start_service()` and `start_interactive_mode()` methods
3. Add proper error handling and logging
4. Update startup script options
5. Add to ecosystem management files

### WebUI Development
- Templates in `duckbot/templates/`
- Static files in `duckbot/static/`
- Real-time updates via WebSocket connections
- React components in `duckbot/react-webui/src/`

### Integration Testing
- Individual integration testing methods available
- Comprehensive system validation via startup script option 'T'
- Cross-platform compatibility verification

## Production Deployment

### System Requirements
- **Python**: 3.8+ (3.11+ recommended for optimal performance)
- **Memory**: 8GB+ RAM for all integrations simultaneously
- **Storage**: 2GB+ free space for full installation
- **Platform**: Windows 10+, Linux, or macOS with compatibility mode

### Security Features
- All services bound to localhost by default for security
- Token-based authentication for web interfaces
- Comprehensive input validation and sanitization
- No API keys or secrets logged in any output

### Performance Optimization
- Async service architecture prevents blocking operations
- Intelligent resource monitoring and cleanup
- Configurable timeout values and retry mechanisms
- Background task management with proper lifecycle handling

## File Structure

```
DuckBotComplete/
├── START_ENHANCED_DUCKBOT.bat      # Main Windows launcher (15+ modes)
├── start_ecosystem.py              # Python service orchestration
├── ai_ecosystem_manager.py         # AI-enhanced ecosystem management
├── CLAUDE.md                       # This development documentation
├── README.md                       # User documentation
├── requirements.txt                # Python dependencies
├── duckbot/                        # Core DuckBot modules
│   ├── enhanced_webui.py           # Professional dashboard
│   ├── ai_router_gpt.py            # Intelligent AI routing
│   ├── bytebot_integration.py      # Desktop automation
│   ├── archon_integration.py       # Multi-agent system
│   ├── charm_terminal_ui.py        # Beautiful terminal UI
│   ├── charm_ecosystem.py          # Complete Charm framework
│   ├── wsl_integration.py          # Windows/Linux integration
│   ├── chromium_integration.py     # ChromiumOS features
│   ├── server_manager.py           # Service orchestration
│   ├── cost_tracker.py             # Usage analytics
│   └── react-webui/               # React Electron components
└── logs/                           # Comprehensive logging
```

## Troubleshooting

### Common Issues
- **Import Errors**: All integrations include fallback handling for missing dependencies
- **Async Event Loop Issues**: Fixed in v3.1.0+ with proper task management
- **Cross-Platform Paths**: All code uses `pathlib.Path` for compatibility
- **Unicode Handling**: UTF-8 encoding enforced throughout

### Integration-Specific Issues
- **ByteBot**: Requires PIL, cv2, numpy for full functionality (graceful fallback available)
- **Archon**: Includes sqlite3 database management with proper error handling
- **Charm**: Fallback UI available when full ecosystem unavailable
- **WSL**: Automatic detection with Windows-only functionality gracefully disabled on other platforms

### Diagnostic Tools
- Startup script option 'T' for comprehensive integration testing
- Startup script option 'S' for system status and diagnostics
- Individual integration interactive modes for debugging
- Detailed logging with configurable levels

## Important Notes

### Production Ready
- **All startup script options have been verified to work correctly**
- **Complete error handling and graceful degradation implemented**
- **Cross-platform compatibility ensured with proper fallbacks**
- **Performance optimized with async patterns and resource management**

### Integration Architecture
- Every integration supports both service and interactive modes
- All integrations include comprehensive help systems and command documentation
- Proper async/await patterns prevent blocking operations
- Unified error handling and logging across all components

### User Experience
- Beautiful terminal interfaces with rich text and interactivity
- Professional WebUI with real-time monitoring and updates
- Comprehensive documentation and help systems throughout
- Multiple startup modes for different use cases and skill levels
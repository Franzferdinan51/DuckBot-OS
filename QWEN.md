# DuckBot Enhanced v4.2 - Qwen3-Omni Integration

## Project Overview

DuckBot Enhanced v4.2 is an advanced AI-powered operating system with Qwen3-Omni serving as the central intelligence hub. This comprehensive system integrates multiple AI ecosystems, multimodal processing capabilities, and extensive service orchestration. The project features:

- **Qwen3-Omni as Main Brain**: Advanced multimodal AI model with Flash Attention 2 optimization
- **Native Voice Assistant**: Built-in voice capabilities without external dependencies
- **Multi-Agent AI Coordination**: Archon framework with specialized AI experts
- **Desktop Automation**: ByteBot integration for natural language control of Windows applications
- **Persistent Memory System**: SQLite-based conversation storage with case-based learning
- **Full UI Integration**: Modern React/TypeScript interface with real-time communication
- **Service Orchestration**: Comprehensive monitoring and management of multiple AI services

## Architecture

### Core Components

1. **Core AI (`/core_ai`)**: Contains the Qwen3-Omni brain integration, AI ecosystem management, and core chat functionality
2. **DuckBot Core (`/duckbot/core`)**: Main system architecture with AI decision making, RAG integration, security frameworks, and service management
3. **Qwen3-Omni UI (`/qwen3-omni-ui`)**: React/TypeScript frontend interface for real-time interaction
4. **Integrations (`/integrations`)**: Multi-agent framework, MCP server, browser-use, and OpenRouter plugins
5. **Launcher (`/launcher`)**: Comprehensive startup scripts and launchers for different configurations

### Key Technologies

- **Python 3.8+**: Primary backend language
- **React/TypeScript**: Modern UI framework
- **FastAPI**: Web framework for API services
- **Transformers**: Hugging Face AI model integration
- **Torch**: PyTorch for deep learning
- **WebSockets**: Real-time communication between services
- **SQLite**: Persistent memory and conversation storage

## Building and Running

### System Requirements
- **Windows 10/11** (WSL2 for enhanced features)
- **Python 3.8+** (3.11+ recommended)
- **8GB RAM minimum** (16GB+ recommended for Qwen3-Omni)
- **10GB free disk space** (for Qwen3-Omni model)
- **Node.js 16+** for Qwen3-Omni-UI

### Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r docs/requirements.txt
   cd qwen3-omni-ui
   npm install
   ```

2. **Launch the System**:
   ```bash
   # Main launcher with full Qwen3-Omni integration
   START_ELECTRON_LAUNCHER.bat
   
   # Alternative launchers available:
   START_LOCAL_ONLY.bat      # Local privacy mode
   START_HEADLESS.bat        # Headless operation
   START_ULTIMATE_DUCKBOT.bat # Enhanced features
   ```

3. **Access the Interface**:
   - Web UI: http://localhost:3000 (or port shown in console)
   - API Server: http://localhost:5000
   - Qwen3-Omni Brain: http://localhost:8000

### Main Startup Flow
The main startup process (via `START_ELECTRON_LAUNCHER.bat`) includes:
1. Dependency checking and installation
2. Starting Qwen3-Omni AI Brain Server (main brain)
3. Initializing core DuckBot services
4. Starting WebSocket and MCP servers
5. Launching Qwen3-Omni Web Server
6. Running the React-based UI

## Development Conventions

### Configuration Management
- AI configuration settings are stored in `ai_config.json`
- Service configurations are in `ecosystem_config.yaml`
- UI environment variables in `.env.local`

### Multi-Provider Support
- Primary: Qwen3-Omni via Hugging Face Transformers
- Fallback: LM Studio (port 1234), Ollama, OpenRouter
- Automatic provider switching based on availability

### Error Handling
- Comprehensive error handling system with logging
- Self-healing capabilities for service failures
- Predictive maintenance and monitoring

### Testing and Diagnostics
- Comprehensive test suite available in `/tests`
- Diagnostic tools in `/diagnostics`
- Health monitoring and performance analytics

## Key Features

### Advanced AI Capabilities
- **Qwen3-Omni Main Brain**: Multimodal text, voice, and visual processing
- **Flash Attention 2**: Optimized performance with reduced memory usage
- **Native Voice Assistant**: Built-in voice capabilities with wake word detection
- **Multi-Agent Coordination**: Archon framework with specialized experts

### Service Integration
- **Comprehensive Monitoring**: Health checks and performance tracking
- **WebSocket Communication**: Real-time service coordination
- **Memory & Learning**: Persistent conversations with adaptive responses
- **Desktop Automation**: Natural language control of applications

### Security and Reliability
- **Authentication System**: Secure access management
- **Rate Limiting**: Protection against abuse
- **Self-Healing**: Automatic recovery from service failures
- **Data Protection**: Secure handling of sensitive information

## File Structure

```
DuckBot-Consolidated-v4.2/
├── duckbot/                    # Main DuckBot application with nested structure
│   ├── agents/                 # AI agent implementations
│   ├── ai/                     # AI-specific modules
│   ├── core/                   # Core system architecture
│   ├── integrations/           # Platform integrations
│   └── services/               # Service implementations
├── core_ai/                    # Core AI and routing modules
├── launcher/                   # All startup scripts and launchers
├── qwen3-omni-ui/              # React/TypeScript UI components
├── integrations/               # All integration modules
├── config/                     # Configuration files
├── utils/                      # Utility and helper scripts
├── tests/                      # Test files
└── docs/                       # Documentation files
```

## Testing

Run the comprehensive test suite:
```bash
python tests/comprehensive_test_suite.py
```

Or run individual tests:
```bash
python tests/test_qwen3_omni_integration.py
python tests/test_voice_assistant.py
python tests/test_all_features.py
```

## Diagnostics

Run diagnostic tools:
```bash
python diagnostics/doctor_check_qwen3_omni.py
python diagnostics/doctor_check_services.py
python diagnostics/doctor_generate_report.py
```

## Additional Resources

- **Documentation**: Check the `docs/` directory for complete documentation
- **API References**: Available in the developer guides
- **UI Integration**: Qwen3-Omni-UI framework by franzferdinan51
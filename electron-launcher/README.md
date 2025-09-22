# DuckBot AI Launcher

A comprehensive AI-powered startup interface for DuckBot v4.2 with deep integration and real-time monitoring.

## Features

### 🤖 AI-Powered Interface
- **Deep DuckBot Integration**: Connects directly to DuckBot via MCP (Model Context Protocol)
- **Real-time Chat**: Communicate with DuckBot through the built-in chat interface
- **AI Recommendations**: Get intelligent suggestions based on system status and capabilities
- **Natural Language Control**: Start, stop, and monitor services using chat commands

### 🚀 Complete Startup Control
- **15+ Startup Modes**: Launch any DuckBot component individually
- **Real-time Monitoring**: Live system metrics and process status
- **Intelligent Process Management**: Start, stop, and monitor all services
- **One-click Operation**: Simple launch controls with detailed status information

### 📊 System Monitoring
- **Live Metrics**: CPU, Memory, Disk, and Network usage
- **Process Tracking**: Monitor all running DuckBot processes
- **Log Monitoring**: Real-time log file monitoring with filtering
- **Performance Analysis**: System resource utilization and optimization

### ⚙️ Advanced Features
- **API Key Management**: Configure Gemini, OpenRouter, and Z.ai API keys
- **Port Management**: Automatic port availability checking
- **Requirement Validation**: Ensure all prerequisites are met before launch
- **Error Handling**: Comprehensive error detection and recovery

### 🎯 Modern UI
- **Professional Design**: Clean, modern interface with dark theme
- **Responsive Layout**: Adapts to different screen sizes
- **Real-time Updates**: Live status updates and notifications
- **Keyboard Shortcuts**: Global shortcuts for quick access

## Installation

### Prerequisites
- Node.js 16+
- Python 3.8+
- DuckBot v4.2 installed

### Setup
```bash
# Navigate to the launcher directory
cd electron-launcher

# Install dependencies
npm install

# Start the launcher
npm start
```

## Usage

### Basic Operation
1. **Launch the Application**: Run `npm start` from the electron-launcher directory
2. **Configure API Keys**: Click the Settings button to add your API keys
3. **Launch Services**: Click on any mode card to start the corresponding service
4. **Monitor Status**: Use the Monitor tab to view real-time system metrics
5. **Chat with DuckBot**: Use the chat interface to communicate with DuckBot

### Keyboard Shortcuts
- **Ctrl+Shift+D**: Show/Hide launcher
- **Ctrl+Shift+C**: Focus chat input

### Chat Commands
- `"Launch ultimate mode"` - Start the complete Ultimate mode
- `"Stop bytebot"` - Stop the ByteBot service
- `"What's the system status?"` - Get current system status
- `"Recommend a mode"` - Get AI-powered recommendations
- `"Show running processes"` - List all active processes

## Configuration

### API Keys
The launcher supports three AI services:

1. **Gemini API Key** (Required for ByteBot, UI-TARS, Learning System)
   - Get from: https://makersuite.google.com/app/apikey

2. **OpenRouter API Key** (Required for AI-Enhanced modes, Archon)
   - Get from: https://openrouter.ai/keys

3. **Z.ai API Key** (Required for N8N Workflow Automation)
   - Get from: https://z.ai

### Settings
Settings are stored in the following locations:
- **Windows**: `%APPDATA%/duckbot-ai-launcher/config.json`
- **macOS**: `~/Library/Application Support/duckbot-ai-launcher/config.json`
- **Linux**: `~/.config/duckbot-ai-launcher/config.json`

## Architecture

### Components
- **Main Process**: Electron main process with system integration
- **Renderer Process**: React-based UI with real-time updates
- **MCP Connection**: WebSocket connection to DuckBot's Model Context Protocol
- **Chat Server**: WebSocket connection for DuckBot communication
- **Process Manager**: Handles all DuckBot process lifecycle
- **System Monitor**: Real-time system metrics collection

### Integration Points
- **DuckBot MCP**: Connects to `ws://localhost:8789` for system control
- **Chat Server**: Connects to `ws://localhost:8790` for AI communication
- **Process Control**: Direct Python process spawning with environment management
- **Log Monitoring**: Real-time log file watching and filtering

## Troubleshooting

### Common Issues

**Launcher won't start**
- Ensure Node.js 16+ is installed
- Check that all dependencies are installed with `npm install`
- Verify Python 3.8+ is available in system PATH

**Can't connect to DuckBot**
- Ensure DuckBot is running with MCP server enabled
- Check that ports 8789 (MCP) and 8790 (Chat) are available
- Verify DuckBot configuration allows external connections

**Services won't start**
- Check API keys are configured correctly
- Verify Python dependencies are installed
- Check port availability for the selected service
- Review log files for detailed error information

### Logs
- **Launcher Logs**: Check console for Electron process logs
- **Service Logs**: View individual service logs in the Logs tab
- **System Logs**: Windows Event Viewer for system-level issues

## Development

### Building for Production
```bash
# Build for Windows
npm run build:win

# Build for macOS
npm run build:mac

# Build for Linux
npm run build:linux
```

### Development Mode
```bash
# Start with DevTools open
npm run dev
```

## Security

### Data Protection
- API keys are stored encrypted using electron-store
- All local connections use WebSocket secure protocols
- No telemetry or analytics data is collected
- All settings are stored locally

### Network Security
- Only connects to localhost services by default
- Validates all incoming WebSocket connections
- Sanitizes all user inputs and chat messages

## Support

For issues and feature requests:
1. Check the troubleshooting section
2. Review DuckBot documentation
3. Check system requirements and dependencies
4. Verify configuration settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Built with ❤️ for DuckBot v4.2**
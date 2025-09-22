# DuckBot Electron App Startup Orchestrator

This guide explains the new unified startup system for the DuckBot Electron application that resolves the port conflicts, service coordination issues, and provides a robust startup sequence.

## Problems Solved

### 1. **MCP Server Port Conflict**
- **Issue**: MCP server was failing to start due to port conflicts and `errorHandler.logDebug is not a function` error
- **Solution**:
  - Created a proper service orchestrator that manages port allocation
  - Fixed the error handler missing method
  - Implemented smart port detection and fallback

### 2. **React Development Server Missing**
- **Issue**: Electron app expected React dev server on port 3000 but it wasn't starting
- **Solution**: Orchestrator automatically starts React dev server with proper configuration

### 3. **Service Coordination**
- **Issue**: Services were starting independently without proper coordination
- **Solution**: Orchestrator manages startup order and dependencies between services

### 4. **Configuration Management**
- **Issue**: Hard-coded port configurations causing conflicts
- **Solution**: Dynamic configuration generation and service discovery

## Architecture

### Service Orchestrator (`electron_startup_orchestrator.py`)
The central coordinator that manages:
- **Service startup sequence**: WebUI Backend → MCP Server → React Server
- **Port allocation**: Smart port detection to avoid conflicts
- **Health monitoring**: Continuous service health checks
- **Configuration generation**: Dynamic service config for Electron app

### Service Configuration Reader (`service-config-reader.js`)
- Reads dynamic configuration from orchestrator
- Provides port and URL information to Electron app
- Handles fallback to default configurations

### Enhanced Electron Main (`electron-main-orchestrated.js`)
- Updated to use orchestrated service configuration
- Proper error handling with fixed methods
- Integration with service status monitoring

### Service Status Component (`ServiceStatus.js`)
- React component for displaying service status
- Real-time health monitoring
- Service management capabilities

## Services

### 1. Enhanced WebUI Backend
- **Port**: 8787 (or fallback)
- **Purpose**: Core DuckBot backend services
- **Health Check**: `GET /health`

### 2. MCP Server
- **Port**: 8791+ (smart allocation)
- **Purpose**: Model Context Protocol server with WebSocket support
- **Health Check**: `GET /health`
- **Features**: Dynamic port allocation, fallback modes

### 3. React Development Server
- **Port**: 3000 (or fallback)
- **Purpose**: Frontend development server
- **Health Check**: HTTP response on root URL

## Usage

### Quick Start
```bash
# 1. Install dependencies (if not already installed)
cd duckbot/react-webui
npm install

# 2. Start the complete system
cd ../../
START_ELECTRON_APP.bat
```

### Manual Start
```bash
# 1. Start the service orchestrator
python electron_startup_orchestrator.py

# 2. In a new terminal, start Electron app
cd duckbot/react-webui
npm run electron:orchestrated
```

### Testing
```bash
# Run the startup test suite
python test_electron_startup.py
```

## Configuration

### Dynamic Configuration
Services are configured dynamically by the orchestrator. The configuration is saved to:
```
duckbot/react-webui/services_config.json
```

### Environment Variables
- `PYTHONPATH`: Points to project root
- `DUCKBOT_MCP_MODE`: Set to 'electron' for Electron integration
- `BROWSER`: Set to 'none' to prevent browser opening
- `PORT`: React server port (if needed)

### Port Allocation
The system uses smart port allocation:
1. Check if preferred port is available
2. If not, try next available port
3. Update configuration accordingly
4. Communicate ports to all services

## Service Communication

### IPC Communication
The Electron app communicates with services via:
- **Service Configuration**: Retrieved from `services_config.json`
- **Health Status**: Real-time status updates via IPC
- **Service Management**: Start/stop/restart capabilities

### WebSocket Support
The MCP server provides WebSocket support on:
- **Primary Port**: Configured MCP port (e.g., 8791)
- **WebSocket Endpoint**: Available for real-time communication

## Error Handling

### Service Failures
- **Automatic Restart**: Orchestrator monitors and restarts failed services
- **Health Checks**: Continuous monitoring with automatic recovery
- **Fallback Modes**: Services degrade gracefully when dependencies fail

### Port Conflicts
- **Smart Allocation**: Automatic detection of available ports
- **Configuration Updates**: All services notified of port changes
- **Graceful Degradation**: System continues with alternative ports

## Logging

### Orchestrator Logs
```
logs/electron_orchestrator.log
```

### MCP Server Logs
```
logs/mcp_server_startup.log
```

### Electron Error Logs
```
logs/electron-error.log
```

## Troubleshooting

### Common Issues

#### 1. "Port already in use" errors
- **Solution**: The orchestrator automatically detects and uses alternative ports
- **Check**: Look at `services_config.json` for actual ports used

#### 2. MCP server fails to start
- **Solution**: Check Python dependencies and MCP library availability
- **Log**: Check `logs/mcp_server_startup.log` for details

#### 3. React server not responding
- **Solution**: Ensure Node.js dependencies are installed
- **Command**: Run `npm install` in `duckbot/react-webui`

#### 4. Electron app fails to connect
- **Solution**: Wait for orchestrator to create `services_config.json`
- **Check**: Verify all services are running in orchestrator output

### Debug Mode
Enable debug logging:
```bash
# For orchestrator
python electron_startup_orchestrator.py
# Check logs for detailed information

# For Electron app
# Open DevTools (Ctrl+Shift+I) to see console output
```

### Health Checks
Manually check service health:
```bash
# WebUI Backend
curl http://localhost:8787/health

# MCP Server
curl http://localhost:8791/health  # Use actual port from config

# React Server
curl http://localhost:3000        # Use actual port from config
```

## Development

### Adding New Services
1. Add service to `electron_startup_orchestrator.py`
2. Update startup order if needed
3. Add health check endpoint
4. Update configuration reader
5. Add to service status component

### Modifying Startup Sequence
Edit the `startup_order` list in `electron_startup_orchestrator.py`:
```python
startup_order = ['webui_backend', 'mcp_server', 'react_server']
```

### Custom Port Configuration
Override default ports in the orchestrator:
```python
# In electron_startup_orchestrator.py
mcp_port = find_available_port(8791)
react_port = find_available_port(3000)
webui_port = find_available_port(8787)
```

## Benefits

### 1. **Reliability**
- Automatic service recovery
- Smart port allocation
- Health monitoring

### 2. **Flexibility**
- Dynamic configuration
- Service independence
- Graceful degradation

### 3. **Maintainability**
- Centralized orchestration
- Clear separation of concerns
- Comprehensive logging

### 4. **Developer Experience**
- Single command startup
- Real-time status monitoring
- Easy troubleshooting

## File Structure

```
DuckBot-Consolidated-v4.2/
├── electron_startup_orchestrator.py      # Main orchestrator
├── START_ELECTRON_APP.bat                  # Windows launcher
├── test_electron_startup.py                # Test suite
├── duckbot/
│   └── react-webui/
│       ├── electron-main-orchestrated.js   # Enhanced Electron main
│       ├── service-config-reader.js        # Configuration reader
│       ├── src/components/ServiceStatus.js # Status component
│       └── services_config.json            # Dynamic config (generated)
├── logs/                                   # Log files
└── ELECTRON_ORCHESTRATOR_GUIDE.md         # This guide
```

## Future Enhancements

### 1. **Service Dependencies**
- Automatic dependency resolution
- Service-specific health requirements
- Conditional startup based on dependencies

### 2. **Performance Monitoring**
- Resource usage tracking
- Performance metrics collection
- Automated scaling based on load

### 3. **Configuration Management**
- Persistent configuration storage
- Environment-specific configs
- Configuration validation

### 4. **Security Enhancements**
- Service authentication
- Encrypted communication
- Access control management

This comprehensive startup system provides a robust foundation for the DuckBot Electron application, addressing all the identified issues and providing a scalable architecture for future enhancements.
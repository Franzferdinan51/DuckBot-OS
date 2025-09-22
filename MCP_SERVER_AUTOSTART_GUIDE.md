# DuckBot MCP Server Auto-Start Guide

## Overview

The Electron launcher has been enhanced with automatic MCP server management capabilities. This ensures that the DuckBot MCP server is automatically started, monitored, and maintained by the Electron launcher without requiring manual intervention.

## Features

### 🔧 Automatic Server Management
- **Auto-start**: MCP server automatically starts when the Electron launcher launches
- **Health Monitoring**: Continuous health checks every 10 seconds
- **Auto-restart**: Server is automatically restarted if it becomes unhealthy
- **Graceful Shutdown**: Proper cleanup when the Electron app closes

### 📊 Real-time Status Monitoring
- **Process Tracking**: Monitors server process ID and resource usage
- **Health Checks**: Validates server responsiveness via HTTP endpoints
- **Status Notifications**: Real-time UI updates for server state changes
- **Error Handling**: Graceful degradation and error recovery

### 🔄 Connection Management
- **Server Readiness**: Waits for server to be ready before establishing connections
- **Connection Retry**: Automatic reconnection with exponential backoff
- **Fallback Handling**: Graceful handling of server unavailability

## Implementation Details

### Server Management Variables
```javascript
let mcpServerProcess = null;        // Child process reference
let mcpServerStarting = false;      // Prevents concurrent startup attempts
let mcpServerReady = false;         // Server readiness state
let mcpServerStartTime = null;       // Startup timestamp
let mcpServerPort = 8790;           // Server port
let mcpServerMaxStartupTime = 30000; // 30 second startup timeout
let mcpServerHealthCheckInterval = null; // Health check timer
```

### Key Functions

#### `startMCPServer()`
- Spawns the MCP server as a child process using `child_process.spawn`
- Monitors stdout/stderr for startup indicators
- Implements startup timeout handling
- Starts health monitoring once server is ready

#### `checkMCPServerHealth()`
- Performs HTTP GET requests to `/health` endpoint
- Validates server responsiveness and tool availability
- Returns server status metrics

#### `startMCPHealthChecks()`
- Sets up periodic health monitoring every 10 seconds
- Automatically restarts server if it becomes unhealthy
- Provides real-time status updates to the UI

#### `stopMCPServer()`
- Implements graceful shutdown with platform-specific handling
- Uses `taskkill` on Windows for proper process termination
- Cleans up resources and stops health monitoring

### IPC Handlers
The following IPC handlers are available for frontend control:
- `start-mcp-server`: Manually start the MCP server
- `stop-mcp-server`: Stop the running MCP server
- `restart-mcp-server`: Restart the MCP server
- `get-mcp-server-status`: Get current server status
- `check-mcp-server-health`: Perform immediate health check

## Integration Points

### Connection Initialization
The `initializeConnections()` function now:
1. Ensures MCP server is ready before attempting connections
2. Automatically starts the server if not running
3. Implements retry logic with backoff
4. Provides status feedback to the user

### Application Lifecycle
- **Startup**: Server starts automatically with AI assistant features
- **Runtime**: Continuous health monitoring and auto-recovery
- **Shutdown**: Graceful server termination on app exit

### Error Handling
- **Process Errors**: Automatic restart on unexpected process termination
- **Health Failures**: Auto-restart when server becomes unresponsive
- **Startup Timeouts**: Graceful handling of server startup delays
- **Connection Issues**: Retry logic with exponential backoff

## Configuration

### Default Settings
```javascript
{
    "mcpServerPort": 8790,
    "mcpServerMaxStartupTime": 30000,
    "healthCheckInterval": 10000,
    "autoRestart": true
}
```

### Customization
Settings can be modified in the Electron launcher code:
- Change `mcpServerPort` to use a different port
- Adjust `mcpServerMaxStartupTime` for slower systems
- Modify health check frequency as needed

## Testing

### Manual Testing
1. Run the Electron launcher: `electron-launcher\electron-launcher.exe`
2. Open developer console to see server startup logs
3. Verify MCP server is accessible at `http://127.0.0.1:8790/health`
4. Test server management via the UI controls

### Automated Testing
Use the provided test script:
```batch
TEST_MCP_AUTOSTART.bat
```

This script will:
1. Start the Electron launcher
2. Wait for initialization
3. Test MCP server connectivity
4. Report server status and metrics

## Troubleshooting

### Common Issues

**Server fails to start**
- Check Python installation and PATH
- Verify `start_mcp_server.py` exists
- Review launcher logs for error messages

**Health checks failing**
- Verify MCP server is actually running
- Check firewall settings for localhost connections
- Review server logs for startup errors

**Connection issues**
- Ensure correct port configuration
- Check for port conflicts with other applications
- Verify server health endpoint accessibility

### Debug Logging
Enable debug logging by setting log level to 'debug' in the Electron launcher:
```javascript
store.set('preferences.logLevel', 'debug');
```

### Log Files
- **Electron Launcher**: Console output and renderer logs
- **MCP Server**: `logs/mcp_server_startup.log`
- **System Events**: Windows Event Viewer for process management

## Benefits

### For Users
- **Seamless Experience**: No manual server management required
- **Reliable Operation**: Automatic recovery from failures
- **Real-time Feedback**: Live status updates in the UI
- **Resource Efficiency**: Server only runs when needed

### For Developers
- **Simplified Integration**: Automatic server lifecycle management
- **Robust Error Handling**: Comprehensive failure recovery
- **Extensible Architecture**: Easy to add new monitoring features
- **Cross-platform Support**: Works on Windows, macOS, and Linux

## Future Enhancements

### Planned Features
- **Configuration UI**: User-configurable server settings
- **Performance Monitoring**: Resource usage tracking and alerts
- **Multiple Server Support**: Management of multiple MCP instances
- **Remote Management**: Control server from external applications
- **Load Balancing**: Automatic load distribution across instances

### API Extensions
- **Metrics Endpoint**: Detailed performance and usage statistics
- **Configuration API**: Runtime server reconfiguration
- **Event Streaming**: Real-time event notifications
- **Health Diagnostics**: Comprehensive server health reports

## Conclusion

The MCP server auto-start functionality provides a robust, automated solution for managing the DuckBot MCP server lifecycle. This ensures reliable operation while maintaining the flexibility needed for development and production environments.

For questions or issues, please refer to the main DuckBot documentation or create an issue in the project repository.
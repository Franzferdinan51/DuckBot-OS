# DuckBot WebSocket Configuration Guide

## Overview

This guide documents the comprehensive WebSocket server configuration for DuckBot Electron app, including port allocation strategies, service coordination, and health monitoring.

## 🚀 Quick Start

### Basic WebSocket Server Startup
```bash
# Start the simple WebSocket server (MCP + Chat)
python simple_websocket_server.py

# Start with custom ports
python simple_websocket_server.py --mcp-port 8791 --chat-port 8792
```

### Start MCP Server
```bash
# Start dedicated MCP server
python start_mcp_server.py

# Start with custom port
python start_mcp_server.py --port 8794
```

### Health Monitoring
```bash
# Run health checks once
python websocket_health_monitor.py --once

# Start continuous monitoring
python websocket_health_monitor.py --monitor --interval 30

# Generate health report
python websocket_health_monitor.py --report health_report.json
```

### Service Coordination
```bash
# Start all services in proper order
python service_startup_coordinator.py
```

### Configuration Validation
```bash
# Validate WebSocket configuration
python validate_websocket_config_simple.py
```

## 📋 Port Allocation Strategy

### Core Services (8780-8789)
- **WebUI**: 8787 - Main DuckBot interface
- **Monitoring**: 8789 - AI ecosystem manager
- **AI Router**: 8790 - AI routing service

### WebSocket Services (8790-8799)
- **WebSocket MCP**: 8793 - WebSocket MCP server
- **WebSocket Chat**: 8794 - WebSocket chat server
- **WebSocket API**: 8795 - WebSocket API gateway
- **MCP WebSocket**: 8797 - MCP WebSocket endpoint

### MCP Services (8790-8799)
- **MCP Server**: 8796 - Dedicated MCP HTTP server

### Development Services (3000-3099)
- **React Dev**: 3000 - React development server
- **Hot Reload**: 3001 - Hot reload server

### Monitoring Services (8800-8809)
- **Health Monitor**: 8800 - Service health monitoring
- **Metrics**: 8801 - Performance metrics
- **Log Aggregator**: 8802 - Central logging

## 🔧 Configuration Files

### 1. Port Allocation (`config/port_allocation.py`)
Central port management with conflict detection and environment variable support.

**Key Features:**
- Automatic port allocation
- Conflict detection
- Environment variable overrides
- Service type categorization

**Environment Variables:**
```bash
export DUCKBOT_WEBSOCKET_MCP_PORT=8791
export DUCKBOT_WEBSOCKET_CHAT_PORT=8792
export DUCKBOT_MCP_SERVER_PORT=8794
export DUCKBOT_WEBUI_PORT=8787
export DUCKBOT_MONITORING_PORT=8789
export DUCKBOT_REACT_DEV_PORT=3000
```

### 2. WebSocket Server (`simple_websocket_server.py`)
Enhanced WebSocket server with health monitoring and error handling.

**Features:**
- Dual server (MCP + Chat)
- Port validation
- Health checks
- Error recovery
- Connection management

### 3. MCP Server (`start_mcp_server.py`)
Dedicated MCP server with proper port allocation.

**Features:**
- Port availability checking
- Retry logic
- Fallback mode
- Health endpoints

### 4. Health Monitor (`websocket_health_monitor.py`)
Comprehensive health monitoring for all WebSocket services.

**Features:**
- Real-time health checks
- Performance metrics
- Trend analysis
- Alert generation

### 5. Service Coordinator (`service_startup_coordinator.py`)
Coordinates startup and management of all services.

**Features:**
- Dependency management
- Ordered startup
- Health monitoring
- Graceful shutdown

## 🏗️ Service Architecture

### Service Dependencies
```
WebUI (8787) ────┐
                 ├─── WebSocket MCP (8793) ──── MCP Server (8796)
Monitoring (8789) ──┘
                 └─── WebSocket Chat (8794)
```

### Service Startup Order
1. **WebUI** (8787) - Core interface
2. **Monitoring** (8789) - System monitoring
3. **WebSocket MCP** (8793) - WebSocket MCP server
4. **MCP Server** (8796) - Dedicated MCP server
5. **React Dev** (3000) - Development server (optional)

## 📊 Health Monitoring

### Health Check Types
1. **WebSocket Connectivity** - Tests WebSocket connections
2. **HTTP Endpoints** - Checks HTTP service availability
3. **Port Availability** - Verifies ports are accessible
4. **Service Response** - Measures response times

### Health Metrics
- **Response Time** - Connection and response latency
- **Uptime** - Service availability duration
- **Connection Count** - Active connections
- **Error Rate** - Failed requests percentage

### Health Endpoints
```
WebSocket Health: ws://localhost:8793 (MCP), ws://localhost:8794 (Chat)
MCP Server Health: http://localhost:8796/health
WebUI Health: http://localhost:8787/health
Monitoring Health: http://localhost:8789/health
```

## 🔍 Troubleshooting

### Port Conflicts
**Symptoms:** Server fails to start with "address already in use" error

**Solutions:**
1. Check which process is using the port:
   ```bash
   netstat -ano | findstr ":8791"
   ```
2. Stop the conflicting process
3. Use environment variables to override ports:
   ```bash
   export DUCKBOT_WEBSOCKET_MCP_PORT=8795
   python simple_websocket_server.py
   ```

### Connection Issues
**Symptoms:** WebSocket connections fail or timeout

**Solutions:**
1. Verify server is running:
   ```bash
   python websocket_health_monitor.py --once
   ```
2. Check firewall settings
3. Verify port availability
4. Test with different ports

### Service Failures
**Symptoms:** Services start but become unhealthy

**Solutions:**
1. Check service logs:
   ```bash
   tail -f logs/mcp_server_startup.log
   ```
2. Run health diagnostics:
   ```bash
   python websocket_health_monitor.py --monitor
   ```
3. Restart affected services
4. Check system resources

## 🚀 Deployment

### Production Deployment
```bash
# 1. Validate configuration
python validate_websocket_config_simple.py

# 2. Start service coordinator
python service_startup_coordinator.py

# 3. Monitor health
python websocket_health_monitor.py --monitor --interval 60

# 4. Generate periodic reports
python websocket_health_monitor.py --report production_health.json
```

### Development Deployment
```bash
# Start development environment
python simple_websocket_server.py &
python start_mcp_server.py &
npm start &

# Monitor in development mode
python websocket_health_monitor.py --monitor --interval 10
```

## 📈 Performance Optimization

### WebSocket Configuration
- **Ping Interval**: 30 seconds
- **Ping Timeout**: 10 seconds
- **Max Queue**: 1024 connections
- **Compression**: Disabled for performance

### Health Monitoring
- **Check Interval**: 30-60 seconds (configurable)
- **Timeout**: 5 seconds per check
- **Retry Count**: 3 attempts
- **History Retention**: 100 snapshots

### Service Coordination
- **Startup Delay**: Configurable per service
- **Health Check Interval**: 30 seconds
- **Restart Policy**: Automatic restart on failure
- **Graceful Shutdown**: 10-second timeout

## 🛡️ Security Considerations

### Port Security
- All services bind to localhost by default
- Consider firewall rules for production
- Use different ports for development/production

### WebSocket Security
- Implement authentication in production
- Use WSS (WebSocket Secure) for external access
- Validate all incoming messages

### Monitoring Security
- Restrict health endpoint access
- Implement rate limiting
- Log all access attempts

## 📝 API Reference

### WebSocket Server API
**Connection URLs:**
- MCP WebSocket: `ws://localhost:8793`
- Chat WebSocket: `ws://localhost:8794`

**Message Format:**
```json
{
  "type": "ping|status|command|message",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {}
}
```

### Health Monitor API
**Endpoints:**
- Health summary: `GET /` (internal)
- Service status: `GET /status` (internal)
- Health report: `GET /report` (internal)

### Service Coordinator API
**Commands:**
- Start all services: `python service_startup_coordinator.py`
- Status check: Built-in health monitoring
- Graceful shutdown: SIGINT/SIGTERM handling

## 🔄 Configuration Updates

### Adding New Services
1. Update `config/port_allocation.py` with new service definition
2. Add service to `service_startup_coordinator.py` configuration
3. Update health monitoring if needed
4. Test with validation script

### Changing Ports
1. Use environment variables for temporary changes
2. Update configuration files for permanent changes
3. Test with validation script
4. Update documentation

### Monitoring Changes
1. Update health check intervals
2. Add new service monitoring
3. Update alert thresholds
4. Test with health monitor

## 📚 Additional Resources

### Related Files
- `config/port_allocation.py` - Port management
- `simple_websocket_server.py` - WebSocket server
- `start_mcp_server.py` - MCP server startup
- `websocket_health_monitor.py` - Health monitoring
- `service_startup_coordinator.py` - Service coordination
- `validate_websocket_config_simple.py` - Configuration validation

### Documentation
- [DuckBot Main Documentation](README.md)
- [Electron App Configuration](docs/electron-config.md)
- [Service Management](docs/service-management.md)

### Support
For issues and questions:
1. Check this guide
2. Run validation tests
3. Review health monitor output
4. Check service logs

---

## 📋 Configuration Checklist

- [ ] Port allocation configured without conflicts
- [ ] Environment variables set (if needed)
- [ ] Services start in correct order
- [ ] Health monitoring configured
- [ ] Error handling implemented
- [ ] Security measures in place
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] Validation tests passing

---

*This configuration ensures reliable WebSocket server operation with proper port allocation, health monitoring, and service coordination for the DuckBot Electron app.*
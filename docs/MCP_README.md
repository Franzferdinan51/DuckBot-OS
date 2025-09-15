# DuckBot MCP (Model Context Protocol) Integration

## Overview

DuckBot v3.1.0+ now includes full **Model Context Protocol (MCP)** integration, providing standardized tool access and AI workflow orchestration across all DuckBot components.

## What is MCP?

**Model Context Protocol (MCP)** is an open protocol that enables AI models to securely interact with external tools and data sources. DuckBot's MCP implementation provides:

- **Standardized Tool Interface**: Consistent API for all DuckBot integrations
- **Multi-Model Support**: Works with OpenAI, Anthropic, and local AI models
- **Real-time Coordination**: Live updates via WebSocket connections
- **Docker Containerization**: Portable deployment with isolation
- **WebUI Integration**: Built-in management dashboard
- **Docker MCP Gateway**: Enterprise-grade server management and orchestration

## Docker MCP Gateway Integration

DuckBot now includes **Docker MCP Gateway** integration for secure, container-based MCP server management. This provides:

### Key Features
- **Container Isolation**: Run MCP servers in isolated Docker containers
- **Centralized Management**: Single interface for managing multiple MCP servers
- **Dynamic Discovery**: Automatically discover and register new MCP servers
- **Health Monitoring**: Real-time health checks and auto-restart capabilities
- **Secrets Management**: Secure handling of API keys and sensitive data
- **OAuth Support**: Authentication and authorization for protected services
- **High Availability**: Load balancing and failover support

### Gateway Architecture
```
AI Client → DuckBot MCP Server → Docker MCP Gateway → MCP Servers (Docker Containers)
```

### Using Docker MCP Gateway

#### Prerequisites
- Docker Desktop with MCP Toolkit enabled
- Docker MCP Gateway plugin: `docker mcp install`

#### Launcher Options
Run `START_ENHANCED_DUCKBOT.bat` → Option **M** → Use gateway options:

- **9. GATEWAY-STATUS**: Check Docker MCP Gateway availability and status
- **10. GATEWAY-SERVERS**: List all servers managed by the gateway
- **11. GATEWAY-ADD**: Add new MCP server to the gateway
- **12. GATEWAY-REMOVE**: Remove MCP server from the gateway

#### WebUI Management
Access at `http://localhost:8787` → Docker MCP Gateway section:
- **Gateway Status**: Real-time gateway health and availability
- **Server Management**: Start, stop, add, and remove MCP servers
- **Tool Execution**: Execute tools across multiple servers
- **Configuration**: Modify gateway settings and security policies

#### API Endpoints
```http
GET  /api/docker/gateway/status
GET  /api/docker/gateway/catalogs
GET  /api/docker/gateway/servers
GET  /api/docker/gateway/tools
POST /api/docker/gateway/server/start
POST /api/docker/gateway/server/stop
POST /api/docker/gateway/execute
POST /api/docker/gateway/server/add
DELETE /api/docker/gateway/server/{name}
```

### Gateway Server Management

#### Adding a Server
```bash
# Via Docker CLI
docker mcp server add my-server --image my-mcp-image:latest --port 8001

# Via DuckBot Launcher
START_ENHANCED_DUCKBOT.bat → M → 11 → Enter server details
```

#### Managing Servers
```bash
# List servers
docker mcp server list

# Start server
docker mcp server start my-server

# Stop server
docker mcp server stop my-server

# Remove server
docker mcp server remove my-server
```

### Security Features
- **Container Isolation**: Each MCP server runs in its own container
- **Network Security**: Configurable firewall and access controls
- **Secrets Management**: Secure storage and rotation of API keys
- **Resource Limits**: CPU, memory, and storage constraints
- **Audit Logging**: Complete execution trail and access logs

### Configuration
Gateway configuration is stored in:
- **Docker Config**: `~/.docker/mcp/config.json`
- **DuckBot Config**: `duckbot/config/docker_mcp_gateway_config.json`

Key configuration options:
```json
{
  "docker_mcp_gateway": {
    "enabled": true,
    "auto_initialize": true,
    "fallback_mode": true,
    "server_management": {
      "auto_discovery": true,
      "health_check_interval": 30
    },
    "security": {
      "enable_secrets": true,
      "network_isolation": true
    }
  }
}
```

## Quick Start

### Using the Launcher

1. Run the main launcher:
   ```bash
   START_ENHANCED_DUCKBOT.bat
   ```

2. Select option **M** for MCP Options

3. Choose your preferred deployment:
   - **1. START-LOCAL**: Run MCP server locally
   - **2. START-DOCKER**: Run in Docker container
   - **7. COMPOSE**: Start full stack with Docker Compose

### Direct Command Line

#### Local Server
```bash
python -m duckbot.mcp_server
```

#### Docker Container
```bash
docker build -f Dockerfile.mcp -t duckbot-mcp .
docker run -d --name duckbot-mcp -p 8000:8000 duckbot-mcp
```

#### Docker Compose
```bash
docker-compose -f docker-compose.mcp.yml up -d
```

## Available MCP Tools

### System Tools
- **system_info**: Get system metrics (CPU, memory, disk)
- **list_files**: Browse directory contents
- **execute_command**: Run system commands safely

### Desktop Automation
- **screenshot**: Capture desktop screenshots
- **mouse_control**: Move and click mouse
- **keyboard_input**: Type text and press keys
- **window_control**: Manage application windows

### AI & Communication
- **ai_router**: Route tasks to optimal AI models
- **chat_completion**: Generate text responses
- **embedding**: Create text embeddings
- **image_analysis**: Analyze images with AI

### Memory & Learning
- **memory_store**: Save conversation context
- **memory_retrieve**: Access stored memories
- **knowledge_search**: Search knowledge base
- **learning_update**: Update learning models

### Terminal & CLI
- **terminal_execute**: Run shell commands
- **charm_tools**: Access Charm ecosystem tools
- **wsl_commands**: Execute WSL Linux commands
- **batch_processing**: Run multiple commands

### Integration Tools
- **web_scraping**: Extract web content
- **api_client**: Call external APIs
- **file_operations**: Read/write files
- **database_query**: Query SQL databases

### Docker MCP Gateway Tools
- **docker_gateway_status**: Get Docker MCP Gateway status and information
- **docker_list_catalogs**: List available MCP catalogs in Docker gateway
- **docker_list_servers**: List available MCP servers in Docker gateway
- **docker_list_tools**: List available tools from Docker MCP servers
- **docker_start_server**: Start a Docker MCP server
- **docker_stop_server**: Stop a Docker MCP server
- **docker_execute_tool**: Execute a tool on a Docker MCP server
- **docker_add_server**: Add a new Docker MCP server
- **docker_remove_server**: Remove a Docker MCP server

## WebUI Integration

The Enhanced WebUI includes full MCP management:

- **Real-time Status**: Live MCP server monitoring
- **Tool Explorer**: Browse and test available tools
- **Execution Logs**: View tool execution results
- **Docker Management**: Start/stop containers
- **Configuration Editor**: Modify MCP settings
- **Docker MCP Gateway**: Enterprise-grade server orchestration
- **Gateway Dashboard**: Monitor and manage multiple MCP servers
- **Server Health**: Real-time health checks and auto-restart
- **Security Management**: Configure access controls and secrets

Access at: `http://localhost:8787` → MCP Tools section → Docker MCP Gateway tab

## API Endpoints

### Server Status
```http
GET /api/mcp/status
```

### Available Tools
```http
GET /api/mcp/tools
```

### Execute Tool
```http
POST /api/mcp/execute
Content-Type: application/json

{
  "tool_name": "system_info",
  "arguments": {}
}
```

### Server Control
```http
POST /api/mcp/server/start
POST /api/mcp/server/stop
```

## Configuration

### File Configuration
Edit `duckbot/config/mcp_config.json`:

```json
{
  "mcp_server": {
    "host": "127.0.0.1",
    "port": 8000,
    "debug": false
  },
  "tools": {
    "timeout": 30,
    "max_concurrent": 5
  }
}
```

### Environment Variables
```bash
export DUCKBOT_MCP_HOST=127.0.0.1
export DUCKBOT_MCP_PORT=8000
export DUCKBOT_MCP_DEBUG=false
export DUCKBOT_MCP_DOCKER_ENABLED=true
```

## Docker Deployment

### Single Container
```bash
# Build image
docker build -f Dockerfile.mcp -t duckbot-mcp .

# Run container
docker run -d \
  --name duckbot-mcp \
  -p 8000:8000 \
  -v ./logs:/app/logs \
  duckbot-mcp
```

### Full Stack (MCP + WebUI)
```bash
docker-compose -f docker-compose.mcp.yml up -d
```

### Custom Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY duckbot/ ./duckbot/
EXPOSE 8000
CMD ["python", "-m", "duckbot.mcp_server"]
```

## Integration Examples

### Python Client
```python
import requests

# Get available tools
response = requests.get("http://localhost:8000/tools")
tools = response.json()["tools"]

# Execute a tool
result = requests.post("http://localhost:8000/execute", json={
    "tool_name": "system_info",
    "arguments": {}
})
print(result.json())
```

### WebSocket Updates
```javascript
const ws = new WebSocket("ws://localhost:8787/ws/mcp");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "mcp_status") {
        console.log("MCP Status:", data.data);
    }
};
```

### AI Model Integration
```python
# Using with AI router
from duckbot.ai_router_gpt import route_task_with_mcp

result = await route_task_with_mcp(
    "Take a screenshot and analyze it",
    use_mcp_tools=True
)
```

## Security Features

- **Localhost Binding**: Services bind to 127.0.0.1 by default
- **Tool Sandboxing**: Restricted execution environments
- **Rate Limiting**: Prevent abuse with configurable limits
- **Input Validation**: Sanitize all tool arguments
- **Audit Logging**: Complete execution trail

## Monitoring & Logging

### Log Files
- `logs/mcp_server.log`: Main server logs
- `logs/mcp_tools.log`: Tool execution logs
- `logs/mcp_errors.log`: Error tracking

### Metrics
- Tool execution count and duration
- Success/failure rates
- Resource utilization
- Connection statistics

### Health Checks
```bash
# Server health
curl http://localhost:8000/health

# Docker container health
docker ps --filter "name=duckbot-mcp"

# Process monitoring
ps aux | grep duckbot.mcp_server
```

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Docker Issues**
```bash
# Reset Docker state
docker system prune -a
docker stop duckbot-mcp
docker rm duckbot-mcp
```

**Permission Errors**
```bash
# Check file permissions
icacls logs /grant Everyone:F
```

**Missing Dependencies**
```bash
# Reinstall Python packages
pip install -r requirements.txt --force-reinstall
```

### Debug Mode
Enable debug logging in `mcp_config.json`:
```json
{
  "mcp_server": {
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

### Test Tools
Verify tool functionality:
```bash
python -c "
from duckbot.mcp_server import test_all_tools
test_all_tools()
"
```

## Development

### Adding New Tools

1. Create tool function in `duckbot/mcp_server.py`:
```python
async def tool_example(arguments: dict) -> dict:
    # Tool implementation
    return {"success": True, "result": data}
```

2. Register the tool:
```python
await self.register_tool("example", tool_example, "Example tool description")
```

3. Update documentation and tests

### Testing
```bash
# Run MCP tests
python -m pytest tests/test_mcp.py -v

# Test specific tool
python -c "from duckbot.mcp_server import test_tool; test_tool('system_info')"
```

## Support

### Documentation
- Main documentation: `CLAUDE.md`
- API reference: WebUI → Documentation section
- Tool catalog: WebUI → MCP Tools → List Available Tools

### Community
- Issues: GitHub repository issues
- Discussions: GitHub discussions
- Updates: Check `START_ENHANCED_DUCKBOT.bat` changelog

### Getting Help
1. Use launcher option **S** for system status
2. Check log files in `logs/` directory
3. Review WebUI MCP dashboard for real-time status
4. Run diagnostic: `python -m duckbot.mcp_server --diagnose`

---

**DuckBot MCP Integration** - Enterprise-grade AI tool orchestration with Model Context Protocol
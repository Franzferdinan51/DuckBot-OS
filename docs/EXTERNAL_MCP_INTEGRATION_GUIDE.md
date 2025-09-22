# External MCP Server Integration Guide for DuckBot v4.2

## Overview

DuckBot v4.2 now supports integration with external MCP (Model Context Protocol) servers, significantly expanding its capabilities through specialized servers for browser automation, system control, filesystem operations, web search, and development tools.

## High-Value MCP Servers Integrated

### 🎭 Browser Automation
- **Playwright MCP** (Microsoft Official)
  - Fast, lightweight browser automation using Playwright's accessibility tree
  - LLM-friendly, no vision models needed
  - Deterministic tool application
  - Tools: `browser_navigate`, `browser_click`, `browser_snapshot`, `browser_fill_form`

### 🖥️ System Control
- **MCPControl**
  - Windows OS automation server for mouse, keyboard, windows, and screen capture
  - Multiple automation providers: keysender, PowerShell, AutoHotkey
  - Tools: `mouse_move`, `mouse_click`, `keyboard_type`, `window_focus`, `screen_capture`

### 📁 Filesystem Operations
- **Standard Filesystem MCP**
  - Local filesystem read/write operations
  - Tools: `read_file`, `write_file`, `list_directory`, `search_files`

- **WSL Filesystem MCP**
  - Access WSL distributions from Windows
  - Optimized for faster file operations using native Linux commands
  - Tools: `wsl_read_file`, `wsl_write_file`, `wsl_list_directory`

### 🔍 Web Search
- **Exa Search MCP**
  - Free Google search integration
  - High-quality web search results
  - Tool: `web_search`

### 👨‍💻 Development Tools
- **Claude Code Tools**
  - Development utilities for agentic development
  - Wisdom extraction, infinite loops, auto-doc generation
  - Tools: `generate_docs`, `extract_wisdom`, `code_analysis`

### 🤖 Agent Orchestration
- **MCP Inception**
  - "Agent for your agent" - parallel and map-reduce task execution
  - Offload context windows and delegate tasks
  - Tools: `execute_mcp_client`, `execute_parallel_mcp_client`, `execute_map_reduce_mcp_client`

## Setup Instructions

### 1. Prerequisites
```bash
# Check system requirements
python scripts/setup_external_mcp_servers.py --check-prereqs

# Required software:
# - Node.js 18+
# - npm
# - Git
# - Python 3.8+
```

### 2. Setup External MCP Servers
```bash
# Run the setup script
python scripts/setup_external_mcp_servers.py

# This will:
# - Install all external MCP servers
# - Create necessary directories
# - Generate environment variable templates
# - Verify installations
```

### 3. Configure Environment Variables
```bash
# Copy the template
cp .env.example .env

# Edit .env and add your API keys
EXA_API_KEY=your_exa_api_key_here
# Add other API keys as needed
```

### 4. Start Enhanced MCP Manager
```bash
# Start the enhanced MCP manager
python duckbot/integrations/enhanced_mcp_manager.py

# Or use within DuckBot ecosystem
python start_ecosystem.py  # Will automatically start enhanced MCP manager
```

## Configuration

### Enhanced MCP Configuration
File: `config/enhanced_mcp_config.json`

Key sections:
- `external_mcp_servers`: Configuration for each external server
- `server_categories`: Group servers by category
- `integration_settings`: Auto-discovery, health monitoring, performance settings
- `security`: Access controls and rate limiting

### Example Server Configuration
```json
{
  "playwright": {
    "enabled": true,
    "name": "playwright",
    "description": "Microsoft Playwright MCP for browser automation",
    "command": "npx",
    "args": ["@playwright/mcp@latest"],
    "timeout": 60,
    "priority": "high",
    "category": "browser_automation",
    "auto_start": true,
    "health_check": true
  }
}
```

## Usage

### Access MCP Tools
```python
from duckbot.integrations.enhanced_mcp_manager import get_enhanced_mcp_manager

# Get manager instance
manager = get_enhanced_mcp_manager()

# Execute a tool
result = await manager.execute_tool("browser_navigate", {
    "url": "https://example.com"
})

# Get available tools
tools = manager.get_available_tools()
print(f"Available tools: {len(tools)}")
```

### Tool Categories
- **Browser Automation**: `browser_navigate`, `browser_click`, `browser_snapshot`
- **System Control**: `mouse_move`, `mouse_click`, `keyboard_type`
- **Filesystem**: `read_file`, `write_file`, `list_directory`
- **Web Search**: `web_search`
- **Development**: `generate_docs`, `extract_wisdom`
- **Agent Orchestration**: `execute_mcp_client`, `execute_parallel_mcp_client`

## Integration with DuckBot Features

### 1. Enhanced WebUI
The MCP servers integrate seamlessly with DuckBot's web interface:
- Access all MCP tools through the web dashboard
- Real-time server status monitoring
- Tool execution with progress tracking

### 2. AI Router Integration
MCP tools are automatically available to all AI providers:
- Local models (LM Studio) can access browser automation
- Cloud providers can control Windows applications
- All providers can search the web and access files

### 3. Service Manager Integration
External MCP servers are managed by DuckBot's service manager:
- Automatic startup and shutdown
- Health monitoring and auto-restart
- Resource management and scaling

## Security Considerations

### 1. Access Controls
- Filesystem access is restricted to allowed directories
- Rate limiting prevents abuse
- External server validation ensures only authorized servers are used

### 2. Environment Variables
- API keys are stored securely in environment variables
- No hardcoded credentials in configuration files

### 3. Network Security
- Servers run locally by default
- HTTPS required for remote access
- Allowed hosts configuration

## Performance Optimization

### 1. Caching
- Tool results are cached to improve performance
- Configurable cache TTL (Time To Live)
- Intelligent cache invalidation

### 2. Concurrency
- Multiple servers can run simultaneously
- Configurable concurrency limits
- Request queuing and prioritization

### 3. Resource Management
- Automatic cleanup of unused resources
- Memory monitoring and optimization
- CPU usage optimization

## Troubleshooting

### Common Issues

1. **Server fails to start**
   - Check Node.js installation: `node --version`
   - Verify npm installation: `npm --version`
   - Check logs: `logs/mcp_server.log`

2. **Tool execution fails**
   - Verify server is running: Check server status in logs
   - Check API keys: Ensure environment variables are set
   - Verify permissions: Check filesystem and network access

3. **Performance issues**
   - Check system resources: CPU, memory, disk space
   - Monitor cache performance: Check cache hit ratio
   - Optimize concurrency settings: Adjust max_concurrent_requests

### Debug Commands
```bash
# Check server status
python -c "from duckbot.integrations.enhanced_mcp_manager import get_enhanced_mcp_manager; import asyncio; print(asyncio.run(get_enhanced_mcp_manager().get_server_status()))"

# Test tool execution
python -c "from duckbot.integrations.enhanced_mcp_manager import get_enhanced_mcp_manager; import asyncio; print(asyncio.run(get_enhanced_mcp_manager().execute_tool('list_directory', {'path': '.'})))"

# View logs
tail -f logs/mcp_server.log
```

## Claude Desktop Integration

### 1. Configuration File
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "duckbot-enhanced": {
      "command": "python",
      "args": ["C:/Users/Ryan/Desktop/DuckBot-Consolidated-v4.2/duckbot/integrations/enhanced_mcp_manager.py"],
      "env": {}
    }
  }
}
```

### 2. Usage in Claude Desktop
Once configured, all MCP tools will be available in Claude Desktop:
- Browser automation tools
- System control tools
- Filesystem access
- Web search capabilities
- Development utilities

## Future Enhancements

### Planned Integrations
- **Database MCP Servers**: PostgreSQL, MongoDB, SQLite
- **Cloud Service MCP**: AWS, Azure, Google Cloud
- **Communication MCP**: Email, Slack, Discord
- **Development MCP**: GitHub, GitLab, Docker
- **AI/ML MCP**: Hugging Face, OpenAI, Anthropic

### Advanced Features
- **Server Chaining**: Use output from one server as input to another
- **Parallel Execution**: Run multiple servers simultaneously
- **Smart Routing**: Automatically select best server for task
- **Learning Integration**: Learn from tool usage patterns

## Contributing

### Adding New MCP Servers
1. Fork the DuckBot repository
2. Add server configuration to `config/enhanced_mcp_config.json`
3. Update setup script in `scripts/setup_external_mcp_servers.py`
4. Add tool definitions to `enhanced_mcp_manager.py`
5. Test integration thoroughly
6. Submit pull request

### Best Practices
- Use official MCP servers when available
- Implement proper error handling and fallbacks
- Add comprehensive logging and monitoring
- Follow DuckBot's coding standards
- Include documentation and examples

## Support

For issues and questions:
- Check logs in `logs/mcp_server.log`
- Run diagnostics: `python diagnostics/doctor_check_services.py`
- Review configuration: `config/enhanced_mcp_config.json`
- Test individual servers: Use the enhanced MCP manager CLI

---

This integration significantly expands DuckBot's capabilities, making it a comprehensive AI-powered operating system with access to specialized tools for every major computing task.
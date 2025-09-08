# DuckBot OpenWebUI Integration Tool

This tool allows you to execute commands on your DuckBot server directly from OpenWebUI, creating a powerful bridge between the two systems.

## Features

🤖 **AI Task Execution** - Run AI tasks with different types and priorities
⚙️ **Service Management** - Start, stop, and restart DuckBot services  
📊 **System Monitoring** - Get real-time status of your DuckBot ecosystem
💰 **Cost Tracking** - Monitor usage and cost summaries
🔍 **RAG Search** - Query your DuckBot knowledge base
🧠 **Model Management** - List and manage available AI models

## Quick Setup

### 1. Ensure DuckBot is Running
```bash
# Start DuckBot ecosystem
START_ECOSYSTEM.bat
# or
python start_ecosystem.py

# Verify WebUI is accessible at http://localhost:8787
```

### 2. Install in OpenWebUI

#### Method A: Direct Import (Recommended)
1. Copy the contents of `openwebui_duckbot_tool.py`
2. In OpenWebUI, go to **Admin Settings** → **Functions** 
3. Click **"+"** to add a new function
4. Paste the code and save

#### Method B: JSON Import
1. In OpenWebUI, go to **Admin Settings** → **Functions**
2. Click **"Import"** 
3. Upload `openwebui_duckbot_function.json`

### 3. Configure (Optional)
The tool auto-detects your DuckBot server configuration. If needed, update these values in the tool:
```python
self.base_url = "http://localhost:8787"  # Your DuckBot WebUI URL
self.timeout = 30  # Request timeout
```

## Usage Examples

### AI Task Execution
```javascript
// Ask DuckBot to analyze code
duckbot_command({
  command: "ai_task",
  prompt: "Explain this Python function: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
  task_type: "code",
  priority: "medium"
})

// Get a detailed explanation
duckbot_command({
  command: "ai_task", 
  prompt: "Explain quantum computing for a beginner",
  task_type: "long_form",
  priority: "high"
})
```

### System Management
```javascript
// Get complete system status
duckbot_command({
  command: "system_status"
})

// Start ComfyUI for image generation
duckbot_command({
  command: "manage_service",
  service_name: "comfyui",
  action: "start"
})

// Restart n8n workflow automation
duckbot_command({
  command: "manage_service", 
  service_name: "n8n",
  action: "restart"
})
```

### Knowledge & Analytics
```javascript
// Search your DuckBot knowledge base
duckbot_command({
  command: "rag_search",
  query: "how to configure AI models in DuckBot",
  top_k: 5
})

// Get cost summary for last 30 days
duckbot_command({
  command: "cost_summary",
  days: 30
})

// List available AI models
duckbot_command({
  command: "list_models"
})
```

## Available Commands

| Command | Description | Required Parameters |
|---------|-------------|-------------------|
| `ai_task` | Execute AI tasks | `prompt` |
| `system_status` | Get system status | None |
| `manage_service` | Control services | `service_name`, `action` |
| `cost_summary` | Usage analytics | None (`days` optional) |
| `rag_search` | Search knowledge base | `query` |
| `list_models` | Available AI models | None |

## Service Names

- `comfyui` - Image/video generation
- `n8n` - Workflow automation  
- `jupyter` - Data science notebooks
- `lm_studio` - Local AI models
- `webui` - DuckBot dashboard
- `open_notebook` - AI notebook interface

## Task Types

- `auto` - Auto-detect task type (default)
- `code` - Code analysis and generation
- `reasoning` - Complex reasoning tasks
- `summary` - Summarization tasks
- `long_form` - Detailed explanations
- `json_format` - Structured JSON responses
- `policy` - Policy and compliance queries
- `arbiter` - Comparison and decision tasks

## Priority Levels

- `low` - Background processing
- `medium` - Normal priority (default)
- `high` - High priority processing

## Troubleshooting

### Authentication Issues
- Ensure DuckBot WebUI is running at http://localhost:8787
- Check that the WebUI token is accessible (tool auto-detects this)
- Verify no firewall is blocking local connections

### Connection Problems
```bash
# Test DuckBot WebUI manually
curl http://localhost:8787/token

# Check if services are running
python -c "import requests; print(requests.get('http://localhost:8787/token').json())"
```

### Service Management Issues
- Use exact service names (case-sensitive)
- Ensure you have proper permissions to start/stop services
- Check DuckBot logs for detailed error messages

### Performance Issues
- Increase timeout if experiencing slow responses
- Check DuckBot system resources (CPU, memory, GPU)
- Monitor DuckBot logs for bottlenecks

## Advanced Configuration

### Custom DuckBot URL
If your DuckBot runs on a different port or host:
```python
self.base_url = "http://your-server:8787"
```

### Token Management
For production setups, you can hardcode the token:
```python
self.token = "your-webui-token-here"
```

### Request Timeout
For slower systems or complex tasks:
```python
self.timeout = 60  # 60 seconds
```

## Integration Examples

### Workflow Automation
Use with OpenWebUI's conversation flows to create automated DuckBot workflows:

1. **Status Check → Service Start → AI Task**
2. **RAG Search → Task Execution → Result Summary**
3. **Cost Monitor → Performance Analysis → Optimization**

### Multi-Agent Scenarios
Combine with other OpenWebUI tools for complex multi-agent workflows:
- DuckBot for AI reasoning
- Other tools for data processing
- DuckBot for final synthesis

## Support

For issues or questions:
1. Check DuckBot logs in the `logs/` directory
2. Verify all services are running with `python test_every_feature.py`
3. Use DuckBot's built-in diagnostics: `CHECK_MODEL_STATUS.bat`
4. Review the comprehensive DuckBot documentation in `CLAUDE.md`

## Version History

- **v1.0** - Initial release with full DuckBot API integration
  - AI task execution
  - Service management  
  - System monitoring
  - Cost tracking
  - RAG search
  - Model management
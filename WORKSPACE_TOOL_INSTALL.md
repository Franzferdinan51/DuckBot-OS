# DuckBot OpenWebUI Workspace Tool - Installation Guide

## 🚀 Quick Install

### Step 1: Ensure DuckBot is Running
```bash
# Start DuckBot ecosystem first
START_ECOSYSTEM.bat
# or
python start_ecosystem.py

# Verify WebUI is accessible
# Browser: http://localhost:8787
```

### Step 2: Install as Workspace Tool

1. **Open OpenWebUI** in your browser
2. **Navigate to Workspace**:
   - Click your profile/avatar (top right)
   - Select **"Workspace"** or **"Admin Panel"** 
   - Go to **"Tools"** or **"Functions"** section
3. **Add New Tool**:
   - Click **"+ Create New Function"** or **"Add Tool"**
   - **Copy and paste** the entire contents of `openwebui_workspace_tool.py`
   - Click **"Save"** or **"Create"**

### Step 3: Verify Installation

The tool should now appear in your workspace tools list. Test with:

```
@duckbot_system_status
```

## 🛠️ Available Functions

Once installed, you can use these functions in your OpenWebUI chats:

### 🤖 AI & Chat Functions
- `@duckbot_ai_chat("your message", "auto", "medium")` - Chat with DuckBot AI
- `@duckbot_qwen_analyze("your code")` - Analyze code with Qwen

### ⚙️ System Management
- `@duckbot_system_status()` - Get complete system status
- `@duckbot_manage_service("comfyui", "start")` - Control services
- `@duckbot_ecosystem_start()` - Start entire ecosystem
- `@duckbot_ecosystem_stop()` - Stop entire ecosystem

### 🧠 AI Models
- `@duckbot_list_models()` - Show available AI models

### 💰 Analytics & Monitoring
- `@duckbot_cost_summary(30)` - Get cost summary for 30 days
- `@duckbot_action_logs(24)` - View last 24 hours of logs

### 📚 Knowledge Base (RAG)
- `@duckbot_rag_search("your query", 5)` - Search knowledge base

### 🔧 Maintenance
- `@duckbot_cache_clear()` - Clear AI cache

## 📋 Usage Examples

### Basic AI Chat
```
@duckbot_ai_chat("Explain machine learning in simple terms", "long_form", "high")
```

### System Management
```
# Check what's running
@duckbot_system_status()

# Start image generation service
@duckbot_manage_service("comfyui", "start")

# Start everything
@duckbot_ecosystem_start()
```

### Knowledge Search
```
@duckbot_rag_search("how to configure AI models", 3)
```

### Code Analysis
```
@duckbot_qwen_analyze("def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)")
```

### Analytics
```
# Get cost summary for last week
@duckbot_cost_summary(7)

# Check recent activity
@duckbot_action_logs(12)
```

## 🎯 Function Parameters

### duckbot_ai_chat(message, task_type, priority)
- **message**: Your question/prompt (required)
- **task_type**: auto, code, reasoning, summary, long_form, json_format, policy, arbiter
- **priority**: low, medium, high

### duckbot_manage_service(service_name, action)
- **service_name**: comfyui, n8n, jupyter, lm_studio, webui, open_notebook
- **action**: start, stop, restart

### duckbot_cost_summary(days)
- **days**: Number of days to analyze (1-365)

### duckbot_rag_search(query, top_k)
- **query**: Search terms (required)
- **top_k**: Number of results (1-20)

### duckbot_action_logs(hours)
- **hours**: Hours of logs to retrieve (1-168)

## 🔧 Troubleshooting

### Tool Not Appearing
- **Refresh** the OpenWebUI page
- Check if there's an **"Enable"** toggle for the function
- Look under **"Tools"**, **"Functions"**, or **"Custom Functions"**
- Try **restarting OpenWebUI** after installation

### Connection Errors
```
❌ Error: DuckBot server not available at http://localhost:8787
```

**Solutions:**
1. Ensure DuckBot is running: `START_ECOSYSTEM.bat`
2. Test manually: Open http://localhost:8787 in browser
3. Check if port 8787 is blocked by firewall

### Authentication Errors
- The tool auto-detects DuckBot's token
- Ensure DuckBot WebUI is fully started
- Check DuckBot logs for startup errors

### Function Errors
```python
# If you get import/syntax errors, ensure you copied the COMPLETE file
# The file should start with:
"""
title: DuckBot Workspace Tool
author: open-webui
...
```

### Service Management Issues
- Use exact service names (lowercase)
- Common services: `comfyui`, `n8n`, `jupyter`, `lm_studio`
- Check DuckBot logs for detailed error messages

## 🚀 Advanced Usage

### Chained Operations
```
# First check status, then start services if needed
@duckbot_system_status()

# If ComfyUI is down, start it:
@duckbot_manage_service("comfyui", "start")

# Then use AI for image generation planning:
@duckbot_ai_chat("Create a prompt for a futuristic cityscape", "long_form")
```

### Automated Workflows
```
# Morning routine: Check system, clear cache, get analytics
@duckbot_system_status()
@duckbot_cache_clear()  
@duckbot_cost_summary(1)
@duckbot_action_logs(12)
```

## 🔄 Updates

To update the tool:
1. Download the latest `openwebui_workspace_tool.py`
2. In OpenWebUI workspace, **edit** the existing function
3. **Replace** the code with the new version
4. **Save** the changes

## 🆘 Getting Help

**If the workspace tool isn't working:**

1. **Verify DuckBot Status**: 
   - Open http://localhost:8787 in browser
   - Should show DuckBot WebUI dashboard

2. **Check OpenWebUI Version**: 
   - Workspace tools require OpenWebUI v0.1.0+
   - Some versions call them "Functions" instead of "Tools"

3. **Test Simple Function First**:
   ```
   @duckbot_system_status()
   ```

4. **Check Browser Console**: 
   - F12 → Console tab for JavaScript errors

5. **DuckBot Diagnostics**:
   ```bash
   python test_every_feature.py
   CHECK_MODEL_STATUS.bat
   ```

The workspace tool provides seamless integration between OpenWebUI and your DuckBot ecosystem! 🤖✨
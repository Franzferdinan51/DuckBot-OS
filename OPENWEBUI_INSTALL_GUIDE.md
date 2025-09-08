# OpenWebUI DuckBot Integration - Installation Guide

I've created **two versions** of the DuckBot tool for OpenWebUI to fix import issues:

## Option 1: Simple Tool (Recommended for beginners)
**File: `openwebui_duckbot_simple.py`**

### Features:
- ✅ Execute AI tasks on DuckBot
- ✅ Get system status  
- ✅ Start services (ComfyUI, n8n, Jupyter, etc.)
- ✅ Simple, lightweight, easy to import

### Functions Available:
1. `duckbot_ai_task(prompt, task_type)` - Ask DuckBot AI questions
2. `duckbot_status()` - Get system status
3. `duckbot_start_service(service_name)` - Start services

## Option 2: Full-Featured Tool
**File: `openwebui_duckbot_tool_fixed.py`**

### Features:
- ✅ All simple tool features PLUS:
- ✅ Service management (start/stop/restart)
- ✅ Cost tracking and analytics
- ✅ RAG knowledge base search
- ✅ Model management
- ✅ Advanced system monitoring

## Installation Steps

### Step 1: Start DuckBot
```bash
# Make sure DuckBot is running first
START_ECOSYSTEM.bat
# OR
python start_ecosystem.py
```

### Step 2: Import Tool into OpenWebUI

#### Method A: Copy & Paste (Easiest)
1. Open OpenWebUI in your browser
2. Go to **Admin Panel** → **Functions** (or **Tools**)
3. Click **"+ Add Function"** or **"Create New"**
4. Copy the **entire contents** of either:
   - `openwebui_duckbot_simple.py` (recommended first)
   - `openwebui_duckbot_tool_fixed.py` (full features)
5. Paste into the code editor
6. Click **Save**

#### Method B: File Upload (if supported)
1. In OpenWebUI Functions section
2. Look for **"Upload"** or **"Import"** button
3. Upload the `.py` file directly

### Step 3: Test the Integration

#### Simple Tool Test:
```javascript
// Ask DuckBot a question
duckbot_ai_task("What is artificial intelligence?", "long_form")

// Get system status
duckbot_status()

// Start ComfyUI for image generation
duckbot_start_service("comfyui")
```

#### Full Tool Test:
```javascript
// Execute AI task with full options
duckbot_command("ai_task", "Explain quantum computing", "", "", "long_form", "high")

// Get complete system status
duckbot_command("system_status")

// Search knowledge base
duckbot_command("rag_search", "", "", "", "", "", 7, "DuckBot configuration")
```

## Troubleshooting Import Issues

### Common Problems & Solutions:

#### 1. "Module not found" or "Import error"
- Make sure you copied the **complete file contents**
- Check that the tool file starts with the proper header:
  ```python
  """
  title: DuckBot Simple Command Tool
  author: DuckBot Team  
  version: 1.0.0
  ...
  ```

#### 2. "Syntax error" on import
- Verify you copied the entire file without truncation
- Make sure no extra characters were added during copy/paste
- Try the simple version first (`openwebui_duckbot_simple.py`)

#### 3. "Function not recognized"
- The tool must be imported as a **Function/Tool**, not a Model
- Look for "Functions", "Tools", or "Custom Functions" in OpenWebUI admin
- Not "Models" or "Agents"

#### 4. "Cannot connect to DuckBot"
- Ensure DuckBot WebUI is running at http://localhost:8787
- Test manually: Open http://localhost:8787 in browser
- Check DuckBot logs for errors

#### 5. OpenWebUI doesn't see the functions
- After importing, you may need to **restart OpenWebUI**
- Or **refresh** the functions list
- Check if there's an **"Enable"** toggle for the function

## Usage Examples

### Simple Version:
```javascript
// Basic AI conversation
duckbot_ai_task("How do I optimize Python code for performance?")

// Code analysis
duckbot_ai_task("Review this function: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)", "code")

// System check
duckbot_status()

// Start image generation
duckbot_start_service("comfyui")
```

### Full Version:
```javascript
// AI task with full control
duckbot_command("ai_task", "Write a Python script to analyze CSV files", "", "", "code", "high")

// Service management
duckbot_command("manage_service", "", "n8n", "restart")

// Cost analysis
duckbot_command("cost_summary", "", "", "", "", "", 30)

// Knowledge search
duckbot_command("rag_search", "", "", "", "", "", 7, "machine learning best practices", 5)
```

## Verification Steps

1. **Test Connection:**
   - Run `duckbot_status()` 
   - Should return system information, not an error

2. **Test AI Task:**
   - Run `duckbot_ai_task("Hello, can you hear me?")`
   - Should return AI response with model info

3. **Test Service:**
   - Run `duckbot_start_service("comfyui")`
   - Should return success/failure message

## Getting Help

If you still have import issues:

1. **Try the Simple version first** - it has fewer dependencies
2. **Check OpenWebUI documentation** for your specific version
3. **Verify OpenWebUI supports custom functions** (some versions call them "Tools")
4. **Test DuckBot directly** at http://localhost:8787 to ensure it's working

## Version Compatibility

- **OpenWebUI v0.1.x+**: Should work with both versions
- **DuckBot v3.0.6+**: Required for full functionality
- **Python 3.8+**: Required for the tools to run

The simple version has minimal dependencies and should work with most OpenWebUI setups!
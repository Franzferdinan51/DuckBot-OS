# DuckBot WebUI Structure Organization

## 📁 New Organized WebUI Structure

### 🌐 `/webui/` - Main WebUI Directory
All web interfaces are now organized under this central directory for easy access and maintenance.

---

## 🎯 Primary WebUI Components

### 1. **Main WebUI** (`/webui/main/`)
**Purpose**: Core DuckBot system management interface
- **Technology**: FastAPI + Jinja2 HTML templates
- **Access**: `python -m duckbot.webui` or through main startup modes
- **Features**:
  - `dashboard.html` - Main system overview dashboard
  - `dashboard_enhanced.html` - Enhanced real-time dashboard
  - `dashboard_modern.html` - Modern styled dashboard
  - `companion.html` - AI chat companion interface
  - `cost_dashboard.html` - Cost analysis and tracking
  - `mining_dashboard.html` - Cryptocurrency mining operations
  - `settings.html` - System configuration interface
  - `action_logs.html` - Action logging and monitoring

**Usage**: Primary interface for system management, monitoring, and configuration

### 2. **React Clippy Assistant** (`/webui/react-clippy/`)
**Purpose**: 3D AI desktop assistant with voice capabilities
- **Technology**: React 18 + Three.js + Electron
- **Access**: `cd webui/react-clippy && npm start` or through startup option
- **Features**:
  - 3D animated character with speech synthesis
  - Multi-AI provider support (DuckBot, LM Studio, OpenRouter)
  - Voice recognition and text-to-speech
  - Electron desktop application support
  - VibeVoice integration for enhanced TTS

**Usage**: Standalone desktop assistant, accessible via React development server or Electron app

### 3. **Browser Automation Interface** (`/webui/browser-automation/`)
**Purpose**: AI-powered web automation and scraping interface
- **Technology**: Gradio + browser-use library
- **Access**: `python -m duckbot.integrations.web_ui` or startup option 22
- **Features**:
  - Web automation and scraping capabilities
  - Multi-LLM provider support
  - Custom browser integration
  - AI-powered web task automation

**Usage**: Browser automation interface for web-based AI tasks

### 4. **OS Interface** (`/webui/os-interface/`)
**Purpose**: Desktop-like web operating system interface
- **Technology**: HTML/CSS/JavaScript + React components
- **Access**: Through DuckBotOS startup modes
- **Features**:
  - Desktop-like web interface
  - Application management
  - File system simulation
  - DuckBotOS integration

**Usage**: Alternative desktop-like interface for DuckBotOS operations

---

## 🔧 Secondary Components (Legacy)

### 5. **Legacy Clippy** (`/webui/react-clippy/legacy-version/`)
**Purpose**: Previous Clippy assistant implementation
- **Status**: Legacy, kept for compatibility
- **Usage**: Deprecated in favor of main React Clippy

### 6. **DuckBotOS GUI** (`/webui/os-interface/duckbot-os-gui/`)
**Purpose**: Google AI Studio generated interface
- **Status**: Experimental/Alternative
- **Usage**: Alternative GUI interface for DuckBotOS

---

## 🚀 Quick Access Guide

### Main WebUI Dashboard
```bash
# Method 1: Direct launch
python -m duckbot.webui

# Method 2: Via startup script (options 2, 3, 6)
START_ENHANCED_DUCKBOT.bat
# Choose Enhanced WebUI or DuckBotOS mode
```

### React Clippy Assistant
```bash
# Method 1: Development mode
cd webui/react-clippy
npm start

# Method 2: Electron app
cd webui/react-clippy
npm run electron

# Method 3: Via startup script (dedicated option coming soon)
```

### Browser Automation
```bash
# Method 1: Direct launch
python -c "from duckbot.integrations.web_ui.src.webui.interface import create_ui; create_ui().launch()"

# Method 2: Via startup script
START_ENHANCED_DUCKBOT.bat
# Choose option 22: Browser Automation
```

### Individual Components
```bash
# ByteBot Desktop Automation (Option 15)
START_ENHANCED_DUCKBOT.bat
# Choose option 15: ByteBot

# UI-TARS GUI Automation (Option 16)
START_ENHANCED_DUCKBOT.bat
# Choose option 16: UI-TARS

# Discord Bot with VibeVoice (Option 23)
START_ENHANCED_DUCKBOT.bat
# Choose option 23: Discord Bot
```

---

## 📋 Component Matrix

| Component | Purpose | Technology | Access Method | Status |
|-----------|---------|------------|---------------|---------|
| Main WebUI | System Management | FastAPI + HTML | `python -m duckbot.webui` | ✅ Active |
| React Clippy | 3D Assistant | React + Three.js | `npm start` in `/webui/react-clippy/` | ✅ Active |
| Browser Automation | Web Scraping | Gradio | Option 22 or direct launch | ✅ Active |
| OS Interface | Desktop-like UI | HTML + React | DuckBotOS modes | ✅ Active |
| Legacy Components | Compatibility | Various | Direct access | 🔄 Legacy |

---

## 🎯 About ByteBot Access

**ByteBot is available as option 15** in the startup script:

```
START_ENHANCED_DUCKBOT.bat

INDIVIDUAL COMPONENT LAUNCH:
15. [BYTEBOT] ByteBot Desktop Automation
    Complete computer control + Natural language processing
    UI automation + Task automation + Interactive mode
```

**Direct access methods:**
```bash
# Interactive mode
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"

# Service mode
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())"
```

---

## 🔄 Migration Notes

### Old Structure → New Structure
- `duckbot/templates/` → `webui/main/`
- `duckbot/react-webui/` → `webui/react-clippy/`
- `duckbot/integrations/web-ui/` → `webui/browser-automation/`
- `duckbot/integrations/duckbotos-webui/` → `webui/os-interface/`

### Import Updates Needed
Update any hardcoded paths in the following files:
- `duckbot/services/webui_manager.py`
- `duckbot/enhanced_webui.py`
- `START_ENHANCED_DUCKBOT.bat`
- Any files referencing old template paths

---

## 🛠️ Maintenance

### Adding New WebUI Components
1. Create appropriate subdirectory in `/webui/`
2. Update this documentation
3. Add startup script option if needed
4. Update import references

### Troubleshooting
- Check port conflicts (default ports: 8787, 8788, 8789)
- Verify Python dependencies for each component
- Check file permissions and path structure
- Review log files in `/logs/` directory
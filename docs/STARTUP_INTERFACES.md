# DuckBot Startup Interfaces

## 🚀 Overview

DuckBot v4.2 now offers **multiple modern startup interfaces** beyond the traditional batch script. Each interface provides unique advantages for different use cases and preferences.

## 🎯 Available Interfaces

### 1. 🤖 AI-Powered Terminal Interface
**File**: `duckbot/ai_startup_interface.py`

#### Features:
- **Interactive Command System**: Type commands like `launch`, `setup`, `recommend`
- **API Key Management**: Secure setup and management of API keys
- **AI Recommendations**: Intelligent mode suggestions based on available APIs
- **Real-time Status**: Live system monitoring and process tracking
- **Smart Search**: Find modes by name, description, or keywords

#### Usage:
```bash
python duckbot/ai_startup_interface.py
```

#### Commands:
- `help` - Show available commands
- `setup` - Configure API keys
- `list` - List all startup modes
- `recommend` - Get AI recommendations
- `launch <mode_id>` - Launch specific mode
- `status` - Show system status

#### Best For:
- Users who prefer terminal interfaces
- Developers and power users
- Remote server administration
- Automated deployments

---

### 2. 🌐 Web-Based Launcher Dashboard
**File**: `duckbot/web_launcher.py`

#### Features:
- **Modern Web Interface**: Clean, responsive design with Tailwind CSS
- **Real-time Monitoring**: Live status updates and process tracking
- **Drag-and-Drop**: Visual service management
- **API Configuration**: Web-based API key setup
- **Categorized Organization**: Modes organized by function
- **Mobile Friendly**: Access from any device

#### Usage:
```bash
# Install dependencies first
pip install fastapi uvicorn

# Start the web launcher
python duckbot/web_launcher.py

# Access at: http://localhost:8080
```

#### Best For:
- Visual learners and GUI enthusiasts
- Remote management via web browser
- Team collaboration environments
- Users new to command-line interfaces

---

### 3. 🎤 Voice-Controlled Launcher
**File**: `duckbot/voice_launcher.py`

#### Features:
- **Natural Language Control**: Launch services with voice commands
- **AI Voice Responses**: VibeVoice-powered audio feedback
- **Continuous Listening**: Always-ready voice activation
- **Smart Command Recognition**: Understands various phrasings
- **Hands-Free Operation**: Perfect for accessibility scenarios

#### Usage:
```bash
# Install dependencies first
pip install SpeechRecognition pyaudio

# Start voice launcher
python duckbot/voice_launcher.py
```

#### Voice Commands:
- "Launch AI Enhanced WebUI"
- "Start ByteBot"
- "What's the status?"
- "Show available modes"
- "What do you recommend?"
- "Stop listening"

#### Best For:
- Accessibility needs
- Hands-free operation
- Smart home integration
- Demonstrations and presentations

---

### 4. 🖥️ Desktop GUI Launcher
**File**: `duckbot/desktop_launcher.py`

#### Features:
- **Native GUI**: Tkinter-based desktop application
- **Categorized Tabs**: Organized interface by mode categories
- **Visual Status Indicators**: Color-coded readiness status
- **One-Click Launch**: Simple button-based operation
- **System Information**: Hardware and configuration details
- **Log Viewer**: Easy access to system logs

#### Usage:
```bash
python duckbot/desktop_launcher.py
```

#### Best For:
- Traditional desktop users
- Windows-centric workflows
- Users uncomfortable with command line
- Educational environments

---

### 5. ⚡ AI Interface Launcher (Recommended)
**File**: `START_AI_INTERFACE.bat`

#### Features:
- **Unified Access**: Single entry point to all interfaces
- **Quick Launch**: Fast access to popular modes
- **API Setup**: Integrated configuration management
- **Traditional Fallback**: Access to original batch script
- **System Testing**: API connectivity validation

#### Usage:
```bash
START_AI_INTERFACE.bat
```

#### Options:
1. **AI-Powered Terminal Interface** - Interactive command system
2. **Web-Based Launcher** - Modern web dashboard
3. **Voice-Controlled Launcher** - Hands-free operation
4. **Traditional Startup Script** - Original interface
5. **Quick Launch Menu** - Fast access to common modes
6. **API Key Configuration** - Setup all API keys

#### Best For:
- New users wanting to explore options
- System administrators
- Testing different interfaces
- Educational purposes

---

## 🔑 API Key Configuration

### Required APIs for Full Functionality:

#### 1. **Gemini API Key** (Google AI)
- **Purpose**: AI-powered features, code analysis, reasoning
- **Get Key**: https://makersuite.google.com/app/apikey
- **Required For**: ByteBot, UI-TARS, Learning System

#### 2. **OpenRouter API Key** (Cloud AI Models)
- **Purpose**: Access to cloud AI models (Claude, GPT, etc.)
- **Get Key**: https://openrouter.ai/keys
- **Required For**: AI-Enhanced modes, Archon Multi-Agent

#### 3. **Z.ai API Key** (Coding Assistance)
- **Purpose**: Advanced coding features and workflow automation
- **Get Key**: https://z.ai
- **Required For**: N8N Workflow Automation
- **Optional**: Z.ai Coding Plan for enhanced features

### Setup Methods:

#### Method 1: Web Interface Setup
1. Launch web launcher: `python duckbot/web_launcher.py`
2. Click "Setup API Keys"
3. Enter your keys in the web form
4. Save configuration

#### Method 2: Terminal Setup
1. Launch AI interface: `python duckbot/ai_startup_interface.py`
2. Type `setup` command
3. Enter keys when prompted
4. Configuration saved automatically

#### Method 3: Batch Script Setup
1. Run: `START_AI_INTERFACE.bat`
2. Choose option 6 for API setup
3. Follow on-screen prompts

#### Method 4: Manual Configuration
Create/edit `.env` file in project root:
```bash
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
ZAI_API_KEY=your_zai_key_here
ZAI_CODING_PLAN=your_coding_plan_id  # Optional
```

## 🎯 Mode Recommendations by Use Case

### **For Complete AI Experience**
- **Ultimate Complete AI System** - Requires Gemini + OpenRouter
- **AI-Enhanced WebUI Dashboard** - Requires OpenRouter

### **For Privacy-Focused Users**
- **Local-Only Privacy Mode** - No API keys required
- **AI Learning System** - Requires Gemini (local processing)

### **For Desktop Automation**
- **ByteBot Desktop Automation** - Requires Gemini
- **UI-TARS GUI Automation** - Requires Gemini

### **For Business Process Automation**
- **N8N Workflow Automation** - Requires Z.ai
- **Archon Multi-Agent System** - Requires OpenRouter

### **For Development**
- **Development Environment** - All APIs recommended
- **AI System Monitor** - No specific requirements

## 🛠️ Installation Requirements

### Common Dependencies:
```bash
# Core requirements
pip install fastapi uvicorn  # For web launcher
pip install speechRecognition pyaudio  # For voice launcher
pip install tkinter  # Usually included with Python

# Optional for enhanced features
pip install duckbot-tools  # If available
```

### Platform-Specific:

#### Windows:
- All interfaces work natively
- Voice control may require additional microphone setup
- Desktop launcher uses built-in tkinter

#### Linux/macOS:
- All interfaces supported
- May need additional packages for voice control:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-pyaudio portaudio19-dev

  # macOS
  brew install portaudio
  pip install pyaudio
  ```

## 🔄 Migration from Traditional Script

### For Current Users:
1. **Keep Using Traditional Script**: `START_ENHANCED_DUCKBOT.bat` still works
2. **Try New Interfaces**: Use `START_AI_INTERFACE.bat` to explore alternatives
3. **Gradual Migration**: Configure API keys once, use across all interfaces

### Configuration Migration:
- Existing `.env` files work with all new interfaces
- API keys are automatically detected and used
- No manual migration required

## 📊 Performance Comparison

| Interface | Resource Usage | Speed | Accessibility | Features |
|-----------|----------------|-------|---------------|----------|
| Traditional Batch | Very Low | Fastest | Moderate | Basic |
| AI Terminal | Low | Fast | High | Advanced |
| Web Launcher | Medium | Medium | Very High | Complete |
| Voice Launcher | Medium | Medium | Very High | Specialized |
| Desktop GUI | Low | Fast | High | Comprehensive |

## 🎉 Getting Started

### Quick Start (Recommended):
```bash
# 1. Launch the interface selector
START_AI_INTERFACE.bat

# 2. Choose option 6 to setup API keys
# 3. Select your preferred interface
# 4. Launch your desired mode
```

### Direct Launch:
```bash
# Terminal Interface
python duckbot/ai_startup_interface.py

# Web Interface
python duckbot/web_launcher.py

# Voice Interface
python duckbot/voice_launcher.py

# Desktop GUI
python duckbot/desktop_launcher.py
```

## 🆚 Feature Comparison

| Feature | Traditional | AI Terminal | Web | Voice | Desktop |
|---------|------------|-------------|-----|-------|---------|
| API Management | ❌ | ✅ | ✅ | ✅ | ✅ |
| AI Recommendations | ❌ | ✅ | ✅ | ✅ | ✅ |
| Real-time Monitoring | ⚡ | ✅ | ✅ | ⚡ | ✅ |
| Voice Control | ❌ | ❌ | ❌ | ✅ | ❌ |
| Mobile Access | ❌ | ✅ | ✅ | ❌ | ❌ |
| Visual Interface | ✅ | ❌ | ✅ | ❌ | ✅ |
| Scriptable | ✅ | ✅ | ⚡ | ❌ | ⚡ |
| Accessibility | ⚡ | ✅ | ✅ | ✅ | ✅ |

## 🚀 Conclusion

DuckBot now offers **multiple modern interfaces** to suit every user preference and use case. Whether you prefer traditional command-line, modern web interfaces, voice control, or desktop GUIs, there's an option for you.

**Recommended Path**:
1. Use `START_AI_INTERFACE.bat` to explore options
2. Setup API keys for full functionality
3. Choose your preferred interface
4. Launch DuckBot with AI-powered intelligence!

All interfaces maintain compatibility with the original batch script while adding powerful new features and improved user experiences.
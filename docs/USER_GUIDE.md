# DuckBot v4.2 Complete User Guide

## Table of Contents
- [Installation and Setup](#installation-and-setup)
- [Quick Start Guides](#quick-start-guides)
- [Core Features](#core-features)
- [Multi-Agent Framework](#multi-agent-framework)
- [Desktop Automation](#desktop-automation)
- [Memory and Learning System](#memory-and-learning-system)
- [AI Integration](#ai-integration)
- [Configuration Tutorials](#configuration-tutorials)
- [Troubleshooting and FAQ](#troubleshooting-and-faq)
- [Advanced Features](#advanced-features)

## Installation and Setup

### System Requirements

#### Minimum Requirements
- **Operating System**: Windows 10/11 (with WSL2 optional for enhanced features)
- **Python**: 3.8+ (3.10+ recommended)
- **RAM**: 4GB minimum (8GB+ recommended for optimal performance)
- **Storage**: 2GB free disk space
- **GPU**: Optional (NVIDIA recommended for AI acceleration)

#### Recommended Requirements
- **RAM**: 16GB+ for multi-agent features and large model support
- **GPU**: NVIDIA RTX 3060 or better with 8GB+ VRAM
- **Storage**: SSD with 10GB+ free space
- **Network**: Stable internet connection for cloud features

### Prerequisites Installation

#### 1. Python Environment Setup
```bash
# Download Python 3.10+ from https://python.org
# Ensure "Add to PATH" is checked during installation

# Verify installation
python --version
pip --version
```

#### 2. Git Installation
```bash
# Download Git from https://git-scm.com
# Verify installation
git --version
```

#### 3. Node.js Installation (for WebUI components)
```bash
# Download Node.js 16+ from https://nodejs.org
# Verify installation
node --version
npm --version
```

#### 4. Go Installation (for Charm ecosystem)
```bash
# Windows: winget install GoLang.Go
# Verify installation
go version
```

### DuckBot Installation

#### Method 1: Automated Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/your-username/DuckBot-Consolidated-v4.2.git
cd DuckBot-Consolidated-v4.2

# Run the automated installer
START_ENHANCED_DUCKBOT.bat
# Choose "Install Components" option
```

#### Method 2: Manual Installation
```bash
# Clone repository
git clone https://github.com/your-username/DuckBot-Consolidated-v4.2.git
cd DuckBot-Consolidated-v4.2

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Go tools
go install github.com/charmbracelet/gum@latest
go install github.com/charmbracelet/glow@latest
go install github.com/charmbracelet/mods@latest
go install github.com/charmbracelet/skate@latest
go install github.com/charmbracelet/crush@latest
go install github.com/charmbracelet/charm@latest
go install github.com/charmbracelet/freeze@latest
go install github.com/charmbracelet/vhs@latest

# Install Node.js dependencies
cd duckbot/react-webui
npm install
cd ../..

# Install additional tools
pip install qwen-agent browser-use
npm install -g @musistudio/claude-code-router
```

### LM Studio Setup (Required for Local-Only Mode)

#### 1. Download and Install LM Studio
- Visit https://lmstudio.ai
- Download the Windows version
- Install with default settings

#### 2. Configure Local Server
```bash
# Start LM Studio
# Go to settings (gear icon) → Server tab
# Enable "Local Server"
# Set Host: localhost
# Set Port: 1234
# Click "Apply & Restart"
```

#### 3. Download Models
```bash
# Recommended models for local-only mode:
- Qwen3 Coder 30B (main brain)
- NVIDIA Llama 3.3 Nemotron Super 49B (reasoning)
- Gemma-3 12B (instructions)
- Phi-3 Mini 3.8B (lightweight tasks)

# Search in LM Studio marketplace:
# qwen/qwen3-coder:free
# nvidia/llama-3.3-nemotron-super-49b
# google/gemma-3-12b-it
# microsoft/phi-3-mini-4k-instruct
```

### Environment Configuration

#### 1. Create Environment File
```bash
# Copy template
copy .env.example .env

# Edit .env with your configuration
notepad .env
```

#### 2. Local-Only Mode Configuration (.env)
```bash
# Local-only privacy mode
AI_LOCAL_ONLY_MODE=true
DISABLE_OPENROUTER=true
ENABLE_LM_STUDIO_ONLY=true
ENABLE_DYNAMIC_LOADING=true
LM_STUDIO_URL=http://localhost:1234

# Local resource optimization
AI_CONFIDENCE_MIN=0.65
AI_LOCAL_CONF_MIN=0.60
MAX_MEMORY_THRESHOLD=85.0
DUCKBOT_WEBUI_HOST=127.0.0.1
DUCKBOT_WEBUI_PORT=8787

# Feature toggles
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
ENABLE_MINING_FEATURES=true
ENABLE_COMFYUI_FEATURES=true
ENABLE_TRELLIS_FEATURES=true
```

#### 3. Cloud + Local Mode Configuration (.env)
```bash
# Discord bot (optional)
DISCORD_TOKEN=your_discord_token_here

# OpenRouter API (optional)
OPENROUTER_API_KEY=your_openrouter_key_here

# AI router configuration
AI_CONFIDENCE_MIN=0.75
AI_LOCAL_CONF_MIN=0.68
OPENROUTER_BUDGET_PER_MIN=6
AI_TTL_CACHE_SEC=60

# WebUI configuration
DUCKBOT_WEBUI_HOST=127.0.0.1
DUCKBOT_WEBUI_PORT=8787
DUCKBOT_WEBUI_TOKEN=your_webui_token_here

# Feature toggles
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
ENABLE_MINING_FEATURES=true
ENABLE_COMFYUI_FEATURES=true
ENABLE_TRELLIS_FEATURES=true
MAX_MEMORY_THRESHOLD=85.0
```

## Core Features

### AI Memory & Learning System (Memento)

The Memento integration provides DuckBot with persistent memory and learning capabilities, allowing it to remember solutions and improve over time.

#### Key Features
- **Persistent Memory**: AI remembers solutions and applies them automatically
- **Pattern Recognition**: Identifies recurring tasks for optimization
- **Context Preservation**: Maintains conversation context across sessions
- **Adaptive Learning**: Gets smarter with every interaction
- **Solution Caching**: Stores successful approaches for future reference

#### Configuration
```yaml
# config/memento_config.yaml
memory:
  enabled: true
  max_entries: 10000
  retention_days: 365
  auto_cleanup: true

learning:
  enabled: true
  learning_rate: 0.1
  confidence_threshold: 0.8
  pattern_detection: true
```

#### Usage Examples
```python
# Access memory system
from duckbot.integrations.memento_integration import MementoIntegration

memento = MementoIntegration()

# Store a solution
memento.store_solution(
    problem="file_permission_error",
    solution="chmod +x script.py",
    confidence=0.95,
    tags=["permissions", "linux", "fix"]
)

# Retrieve similar solutions
solutions = memento.find_similar_solutions("permission denied")
```

### Multi-Agent Framework (Archon)

DuckBot's multi-agent framework allows specialized AI agents to collaborate on complex tasks.

#### Agent Types
- **Market Analyzer**: Analyzes market trends and makes predictions
- **Discord Moderator**: Manages Discord communities with AI moderation
- **Workflow Optimizer**: Optimizes business processes and workflows
- **Code Analyzer**: Analyzes and improves code quality
- **Mining Manager**: Manages cryptocurrency mining operations
- **Cost Optimizer**: Optimizes resource usage and costs

#### Configuration
```yaml
# config/agents_config.yaml
agents:
  market_analyzer:
    enabled: true
    model: "qwen3-30b"
    priority: 1

  discord_moderator:
    enabled: true
    model: "llama3-8b"
    priority: 2

  mining_manager:
    enabled: true
    model: "phi-3-mini"
    priority: 3
```

#### Usage Examples
```python
# Deploy agents
from duckbot.agents.intelligent_agents import IntelligentAgents

agents = IntelligentAgents()

# Start market analysis
market_analysis = await agents.deploy_agent(
    agent_type="market_analyzer",
    task="Analyze cryptocurrency market trends",
    context={"timeframe": "7d", "coins": ["BTC", "ETH"]}
)

# Coordinate multiple agents
workflow_result = await agents.coordinate_agents([
    ("market_analyzer", "Analyze market"),
    ("cost_optimizer", "Optimize resources"),
    ("workflow_optimizer", "Improve process")
])
```

### Desktop Automation (ByteBot)

ByteBot integration provides advanced desktop automation capabilities using natural language commands.

#### Features
- **Natural Language Control**: Control applications with plain English
- **UI-TARS Integration**: Advanced GUI automation and interaction
- **Screenshot Analysis**: Understand and interact with visual interfaces
- **Task Automation**: Automate repetitive desktop tasks
- **Cross-Application**: Works across different Windows applications

#### Configuration
```yaml
# config/bytebot_config.yaml
automation:
  enabled: true
  confidence_threshold: 0.8
  max_execution_time: 300
  safe_mode: true

ui_automation:
  enabled: true
  screenshot_interval: 1.0
  interaction_timeout: 30
  element_detection: true
```

#### Usage Examples
```python
# Automate desktop tasks
from duckbot.integrations.bytebot_integration import ByteBotIntegration

bytebot = ByteBotIntegration()

# Open applications
result = await bytebot.execute_task("Open Notepad and type 'Hello World'")

# Automate workflows
workflow = await bytebot.execute_task("""
1. Open Chrome browser
2. Navigate to https://github.com
3. Search for 'DuckBot'
4. Take screenshot of results
""")

# Interactive mode
await bytebot.start_interactive_mode()
```

### Dynamic Model Management

Intelligent model loading and unloading based on system resources and task requirements.

#### Features
- **Resource-Aware Loading**: Loads models based on available RAM/VRAM
- **Task Optimization**: Selects best model for specific tasks
- **Hot Swapping**: Dynamically switches models without restart
- **Performance Monitoring**: Tracks model performance and resource usage
- **Intelligent Caching**: Keeps frequently used models loaded

#### Configuration
```yaml
# config/model_manager_config.yaml
model_manager:
  auto_optimize: true
  memory_threshold: 85
  vram_threshold: 90
  max_loaded_models: 3

models:
  phi-3-mini:
    size_gb: 2.2
    ram_required: 4
    vram_required: 2
    specialty: "general"
    performance_score: 75

  qwen3-30b:
    size_gb: 18.5
    ram_required: 16
    vram_required: 8
    specialty: "coding"
    performance_score: 95
```

#### Usage Examples
```python
# Dynamic model management
from duckbot.core.dynamic_model_manager import DynamicModelManager

model_manager = DynamicModelManager()

# Load optimal model for task
model_id = await model_manager.load_optimal_model(
    task_type="coding",
    complexity="high"
)

# Get model recommendations
recommendations = model_manager.get_model_recommendations(
    available_ram=8,
    task_requirements=["reasoning", "coding"]
)
```

### Cross-Platform Integration

Seamless integration with Windows Subsystem for Linux and other platforms.

#### Features
- **WSL Integration**: Run Linux commands and applications
- **Docker Management**: Container orchestration and management
- **Path Translation**: Automatic Windows/Linux path conversion
- **Service Management**: Cross-platform service control
- **Environment Sharing**: Share variables and configurations

#### Configuration
```yaml
# config/cross_platform_config.yaml
wsl:
  enabled: true
  distribution: "Ubuntu-20.04"
  auto_start: true

docker:
  enabled: true
  host: "npipe://./pipe/docker_engine"
  auto_connect: true
```

#### Usage Examples
```python
# Cross-platform operations
from duckbot.platforms.wsl_integration import WSLIntegration

wsl = WSLIntegration()

# Execute Linux commands
result = await wsl.execute_command("ls -la /home")

# Manage Docker containers
containers = await wsl.list_containers()
await wsl.start_container("nginx")
```

## Quick Start Guides

### 1. Local-Only Privacy Mode

#### One-Click Start
```bash
# Start DuckBot in complete privacy mode
START_LOCAL_ONLY.bat
```

#### Manual Start
```bash
# Start LM Studio first (ensure local server is running)
# Then start DuckBot
python start_local_ecosystem.py
```

#### Accessing the Interface
- **WebUI**: Open http://localhost:8787 in your browser
- **Terminal Interface**: Use the command-line interface in the terminal
- **API**: Available at http://localhost:8787/api

### 2. ComfyUI Integration

#### Start ComfyUI
```bash
# Method 1: Through DuckBot launcher
START_ENHANCED_DUCKBOT.bat
# Choose "Start ComfyUI" option

# Method 2: Direct start
python core_ai/start_comfyui.py
```

#### Access ComfyUI
- **Web Interface**: http://localhost:8185
- **API**: http://localhost:8185/prompt

#### Basic ComfyUI Usage
```python
# Example: Generate image with ComfyUI
from duckbot.integrations.comfyui_integration import ComfyUIIntegration

comfyui = ComfyUIIntegration()
result = comfyui.generate_image(
    prompt="A beautiful landscape",
    width=512,
    height=512,
    steps=20
)
```

### 3. TRELLIS Integration

#### Start TRELLIS
```bash
# Through DuckBot launcher
START_ENHANCED_DUCKBOT.bat
# Choose "Start TRELLIS" option

# Direct start
python duckbot.integrations.trellis_integration
```

#### TRELLIS Features
- **3D Model Generation**: Create 3D models from text descriptions
- **Scene Understanding**: Analyze and modify 3D scenes
- **Export Options**: Multiple format support (OBJ, GLTF, FBX)

#### Basic TRELLIS Usage
```python
# Example: Generate 3D model
from duckbot.integrations.trellis_integration import TRELLISIntegration

trellis = TRELLISIntegration()
model = trellis.generate_3d_model(
    description="A modern chair",
    detail_level="high"
)
```

### 4. VibeVoice TTS Integration

#### Start VibeVoice
```bash
# Through DuckBot launcher
START_ENHANCED_DUCKBOT.bat
# Choose "Start VibeVoice" option

# Direct start
python integrations/setup_vibevoice.py
```

#### VibeVoice Features
- **Multi-speaker Support**: Multiple voice options
- **Emotional TTS**: Voice with emotional context
- **Real-time Streaming**: Live voice generation
- **Custom Voice Training**: Train custom voice models

#### Basic VibeVoice Usage
```python
# Example: Generate speech
from duckbot.integrations.vibevoice_client import VibeVoiceClient

vibevoice = VibeVoiceClient()
audio = vibevoice.generate_speech(
    text="Hello, this is a test message",
    voice="default",
    emotion="neutral"
)
```

### 5. Full System Launch

#### Complete Ecosystem Start
```bash
# Method 1: Enhanced launcher (recommended)
START_ENHANCED_DUCKBOT.bat
# Choose option 1: "AI-Enhanced WebUI Dashboard"

# Method 2: Manual start
python start_ecosystem.py
```

#### System Verification
```bash
# Check all services
python diagnostics/doctor_check_services.py

# Check model status
python model_status.py

# Test all features
python tests/test_all_features.py
```

## Configuration Tutorials

### 1. AI Configuration

#### Local Model Configuration
```json
// config/ai_config.json
{
  "provider": "lm_studio",
  "lm_studio_url": "http://localhost:1234/v1",
  "lm_studio_model": "auto",
  "max_tokens": 512,
  "temperature": 0.2,
  "conversation_history_limit": 50,
  "decision_confidence_threshold": 0.7,
  "enable_dynamic_loading": true,
  "max_concurrent_models": 3,
  "model_cleanup_timeout": 900
}
```

#### Cloud Provider Configuration
```json
// config/ai_config.json
{
  "provider": "openrouter",
  "openrouter_api_key": "your_key_here",
  "openrouter_url": "https://openrouter.ai/api/v1",
  "openrouter_model": "qwen/qwen3-coder:free",
  "max_tokens": 512,
  "temperature": 0.2,
  "fallback_to_local": true
}
```

### 2. Service Configuration

#### Ecosystem Configuration
```yaml
# config/ecosystem_config.yaml
services:
  webui:
    host: "127.0.0.1"
    port: 8787
    enabled: true

  monitoring:
    host: "127.0.0.1"
    port: 8789
    enabled: true

  api:
    host: "127.0.0.1"
    port: 8790
    enabled: true

  comfyui:
    host: "127.0.0.1"
    port: 8185
    enabled: true

  trellis:
    host: "127.0.0.1"
    port: 8186
    enabled: true

  vibevoice:
    host: "127.0.0.1"
    port: 8187
    enabled: true
```

#### Hardware Configuration
```json
// config/hardware_config.json
{
  "auto_detect": true,
  "gpu_preference": "nvidia",
  "memory_threshold": 85,
  "cpu_threads": 4,
  "optimization_level": "balanced",
  "model_recommendations": {
    "low_end": ["phi-3-mini", "gemma-2b"],
    "mid_range": ["qwen2.5-7b", "llama3-8b"],
    "high_end": ["qwen3-30b", "nemotron-49b"]
  }
}
```

### 3. Feature Configuration

#### Enable/Disable Features
```bash
# In .env file
# ComfyUI features
ENABLE_COMFYUI_FEATURES=true
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8185

# TRELLIS features
ENABLE_TRELLIS_FEATURES=true
TRELLIS_HOST=127.0.0.1
TRELLIS_PORT=8186

# VibeVoice features
ENABLE_VOICE_FEATURES=true
VIBEVOICE_HOST=127.0.0.1
VIBEVOICE_PORT=8187

# Mining features
ENABLE_MINING_FEATURES=true
MINING_POOL_URL=your_pool_url
MINING_WALLET=your_wallet_address
```

#### Custom Model Configuration
```json
// config/custom_models.json
{
  "models": {
    "my_custom_model": {
      "name": "Custom Model",
      "path": "path/to/model",
      "size_gb": 7,
      "specialty": "general",
      "min_ram_gb": 8,
      "min_vram_gb": 4,
      "priority": 5
    }
  }
}
```

## Feature Walkthroughs

### 1. WebUI Dashboard

#### Accessing the Dashboard
```bash
# Start the system
START_ENHANCED_DUCKBOT.bat
# Choose "AI-Enhanced WebUI Dashboard"

# Open browser
http://localhost:8787
```

#### Dashboard Features
- **System Overview**: Real-time system status and resource usage
- **AI Chat**: Interactive AI conversation interface
- **Model Management**: View and manage loaded models
- **Service Control**: Start/stop individual services
- **File Management**: Upload and manage files
- **Settings**: Configure system preferences

#### Using the AI Chat
1. Click on "AI Chat" in the sidebar
2. Select your preferred AI model
3. Type your message in the chat input
4. Press Enter or click "Send"
5. View AI responses in the chat window

#### Managing Models
1. Go to "Model Management" in the sidebar
2. View currently loaded models
3. Check resource usage for each model
4. Load/unload models as needed
5. Monitor model performance metrics

### 2. Desktop Automation (ByteBot)

#### Starting ByteBot
```bash
# Through WebUI
# Go to Services → ByteBot → Start

# Through command line
python -c "from duckbot.integrations.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"
```

#### Basic Automation Commands
```python
# Take screenshot
bytebot.take_screenshot()

# Click on element
bytebot.click_element(button_text="Submit")

# Type text
bytebot.type_text("Hello, World!")

# Open application
bytebot.open_application("notepad.exe")
```

#### Advanced Automation
```python
# Create workflow
workflow = [
    {"action": "open", "target": "calculator.exe"},
    {"action": "click", "target": "5"},
    {"action": "click", "target": "+"},
    {"action": "click", "target": "3"},
    {"action": "click", "target": "="}
]

# Execute workflow
bytebot.execute_workflow(workflow)
```

### 3. Multi-Agent Framework (Archon)

#### Starting Multi-Agent System
```bash
# Through WebUI
# Go to Agents → Start Multi-Agent System

# Through command line
python duckbot/agents/intelligent_agents.py
```

#### Agent Types
- **Code Agent**: Specialized in programming tasks
- **Research Agent**: Handles information gathering and analysis
- **Automation Agent**: Manages desktop automation
- **Creative Agent**: Handles creative tasks and content generation

#### Using Agents
```python
# Create agent team
from duckbot.agents.intelligent_agents import IntelligentAgents

agents = IntelligentAgents()
result = agents.coordinate_agents(
    task="Create a Python script that analyzes stock data",
    agents=["code", "research"]
)
```

### 4. Memory and Learning System (Memento)

#### Memory System Features
- **Persistent Memory**: Remembers conversations across sessions
- **Learning System**: Learns from interactions to improve responses
- **Context Management**: Maintains conversation context
- **Pattern Recognition**: Identifies patterns in user behavior

#### Using Memory System
```python
# Access memory
from duckbot.integrations.memento_integration import MementoIntegration

memento = MementoIntegration()

# Store memory
memento.store_memory(
    key="user_preferences",
    value={"theme": "dark", "language": "en"}
)

# Retrieve memory
preferences = memento.retrieve_memory("user_preferences")
```

### 5. Cryptocurrency Mining Integration

#### Setting Up Mining
```bash
# Configure mining in .env
ENABLE_MINING_FEATURES=true
MINING_POOL_URL=stratum+tcp://pool.example.com:3333
MINING_WALLET=your_wallet_address
MINING_WORKER=duckbot_worker

# Start mining through WebUI
# Go to Mining → Start Mining
```

#### Mining Features
- **Real-time Statistics**: Hash rate, temperature, power usage
- **Profitability Analysis**: Calculate mining profitability
- **Auto-switching**: Automatically switch between coins
- **Temperature Monitoring**: Monitor GPU temperatures
- **Remote Control**: Start/stop mining remotely

#### Using Mining Commands
```python
# Control mining
from duckbot.integrations.mining_manager import MiningManager

mining = MiningManager()

# Start mining
mining.start_mining(
    algorithm="ethash",
    pool_url="stratum+tcp://pool.example.com:3333",
    wallet="your_wallet"
)

# Get statistics
stats = mining.get_mining_stats()
```

## Troubleshooting and FAQ

### Common Issues

#### 1. LM Studio Not Detected
**Problem**: DuckBot can't connect to LM Studio

**Solution**:
```bash
# 1. Ensure LM Studio is running
# 2. Check local server is enabled
#    - Open LM Studio
#    - Go to Settings → Server
#    - Enable "Local Server"
#    - Set Host: localhost, Port: 1234
#    - Click "Apply & Restart"

# 3. Test connection
curl http://localhost:1234/v1/models

# 4. Check DuckBot configuration
#    Edit .env file
#    LM_STUDIO_URL=http://localhost:1234
```

#### 2. Models Not Loading
**Problem**: AI models fail to load or respond

**Solution**:
```bash
# 1. Check system resources
python model_status.py

# 2. Ensure models are downloaded in LM Studio
#    - Open LM Studio
#    - Go to Models tab
#    - Search and download required models

# 3. Check model configuration
#    Edit config/ai_config.json
#    Verify model names and paths

# 4. Restart DuckBot
#    Close and restart START_ENHANCED_DUCKBOT.bat
```

#### 3. WebUI Not Accessible
**Problem**: Can't access WebUI at http://localhost:8787

**Solution**:
```bash
# 1. Check if service is running
python diagnostics/doctor_check_services.py

# 2. Check port availability
netstat -an | findstr 8787

# 3. Verify configuration
#    Check .env file:
#    DUCKBOT_WEBUI_HOST=127.0.0.1
#    DUCKBOT_WEBUI_PORT=8787

# 4. Restart WebUI service
python -m duckbot.enhanced_webui --restart
```

#### 4. Memory/Performance Issues
**Problem**: System running slow or high memory usage

**Solution**:
```bash
# 1. Check system resources
python model_status.py

# 2. Adjust memory threshold
#    Edit .env file:
#    MAX_MEMORY_THRESHOLD=75.0

# 3. Enable dynamic model loading
#    Edit .env file:
#    ENABLE_DYNAMIC_LOADING=true

# 4. Clear cache
python -c "from duckbot.core.cost_management import CostManager; CostManager().clear_cache()"
```

#### 5. Permission Errors
**Problem**: Permission denied errors on Windows

**Solution**:
```bash
# 1. Run as administrator
#    Right-click on START_ENHANCED_DUCKBOT.bat
#    Run as administrator

# 2. Check file permissions
#    Right-click on DuckBot folder
#    Properties → Security → Edit permissions

# 3. Disable Windows Defender real-time protection (temporary)
#    Windows Security → Virus & threat protection → Manage settings
#    Turn off Real-time protection
```

### Performance Optimization

#### 1. System Optimization
```bash
# Optimize for performance
# Edit config/hardware_config.json
{
  "optimization_level": "performance",
  "cpu_threads": "auto",
  "memory_threshold": 80,
  "enable_gpu_acceleration": true
}
```

#### 2. Model Optimization
```bash
# Use smaller models for better performance
# Edit config/ai_config.json
{
  "lm_studio_model": "microsoft/phi-3-mini-4k-instruct",
  "max_tokens": 256,
  "temperature": 0.1
}
```

#### 3. Service Optimization
```bash
# Disable unused services
# Edit .env file
ENABLE_VIDEO_FEATURES=false
ENABLE_MINING_FEATURES=false
ENABLE_COMFYUI_FEATURES=false
```

### FAQ

#### Q: What's the difference between local-only and cloud mode?
**A**: Local-only mode uses only your local hardware for AI processing, ensuring complete privacy. Cloud mode can use external AI services for additional capabilities but requires internet connection.

#### Q: How do I add custom AI models?
**A**: Add models to LM Studio, then configure them in config/ai_config.json or use the WebUI model management interface.

#### Q: Can I use DuckBot without an internet connection?
**A**: Yes, use local-only mode. All features work offline except those requiring external services (like Discord bot).

#### Q: How much RAM do I need for optimal performance?
**A**:
- Basic usage: 8GB RAM
- Multi-agent features: 16GB RAM
- Large models (30B+): 32GB RAM

#### Q: Is DuckBot secure?
**A**: Yes, DuckBot is designed with security in mind:
- All local processing in local-only mode
- No data sent to external servers without permission
- Secure API key handling
- Regular security updates

#### Q: How do I backup my DuckBot data?
**A**:
```bash
# Backup configuration and data
copy config\ backup\config\
copy data\ backup\data\
copy .env backup\

# Backup LM Studio models
# LM Studio models are typically in:
# C:\Users\<username>\.lmstudio\models\
```

#### Q: Can I integrate DuckBot with other applications?
**A**: Yes, DuckBot provides REST APIs and WebSocket interfaces for integration with external applications.

## Advanced Features

### 1. Custom Workflows

#### Creating Custom Workflows
```python
# Create custom workflow
from duckbot.integrations.bytebot_integration import ByteBotIntegration
from duckbot.agents.intelligent_agents import IntelligentAgents

def custom_workflow():
    bytebot = ByteBotIntegration()
    agents = IntelligentAgents()

    # Step 1: Research
    research_result = agents.coordinate_agents(
        task="Research latest AI developments",
        agents=["research"]
    )

    # Step 2: Create content
    content_result = agents.coordinate_agents(
        task="Create blog post about AI developments",
        agents=["creative"]
    )

    # Step 3: Publish
    bytebot.open_application("browser.exe")
    bytebot.navigate_to("https://blog.example.com")
    bytebot.create_blog_post(content_result)

    return content_result
```

### 2. Custom Agent Development

#### Creating Custom Agents
```python
# Create custom agent
from duckbot.agents.intelligent_agents import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "custom_agent"
        self.specialty = "custom_tasks"

    async def process_task(self, task):
        # Custom agent logic
        result = await self.custom_processing(task)
        return result

    async def custom_processing(self, task):
        # Implement custom processing logic
        return f"Processed: {task}"

# Register custom agent
agents = IntelligentAgents()
agents.register_agent(CustomAgent())
```

### 3. API Integration

#### REST API Usage
```python
# Using DuckBot REST API
import requests

# Chat with AI
response = requests.post(
    "http://localhost:8787/api/chat",
    json={
        "message": "Hello, how are you?",
        "model": "qwen3-coder",
        "stream": False
    }
)

# Generate image
response = requests.post(
    "http://localhost:8787/api/generate_image",
    json={
        "prompt": "A beautiful sunset",
        "width": 512,
        "height": 512
    }
)
```

#### WebSocket Integration
```python
# Using WebSocket for real-time communication
import asyncio
import websockets

async def duckbot_websocket():
    async with websockets.connect("ws://localhost:8787/ws") as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "chat",
            "message": "Hello, DuckBot!"
        }))

        # Receive response
        response = await websocket.recv()
        print(f"Received: {response}")

# Run WebSocket client
asyncio.run(duckbot_websocket())
```

### 4. System Monitoring

#### Custom Monitoring Scripts
```python
# Create custom monitoring
from duckbot.core.hardware_detector import HardwareDetector
from duckbot.services.monitoring_dashboard import MonitoringDashboard

class CustomMonitor:
    def __init__(self):
        self.hardware = HardwareDetector()
        self.dashboard = MonitoringDashboard()

    def monitor_system(self):
        while True:
            # Get system metrics
            cpu_usage = self.hardware.get_cpu_usage()
            memory_usage = self.hardware.get_memory_usage()
            gpu_usage = self.hardware.get_gpu_usage()

            # Log metrics
            self.dashboard.log_metrics({
                "cpu": cpu_usage,
                "memory": memory_usage,
                "gpu": gpu_usage
            })

            # Check thresholds
            if cpu_usage > 80:
                self.dashboard.send_alert("High CPU usage detected!")

            time.sleep(5)
```

### 5. Backup and Recovery

#### Automated Backup System
```python
# Automated backup script
import shutil
import json
from datetime import datetime

def backup_duckbot():
    # Create backup directory
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir)

    # Backup configuration files
    shutil.copytree("config", f"{backup_dir}/config")
    shutil.copy(".env", f"{backup_dir}/.env")

    # Backup data
    if os.path.exists("data"):
        shutil.copytree("data", f"{backup_dir}/data")

    # Backup LM Studio models (optional)
    # shutil.copytree("C:/Users/<username>/.lmstudio/models", f"{backup_dir}/models")

    # Create backup manifest
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "version": "4.2",
        "backup_size": sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(backup_dir)
                          for filename in filenames)
    }

    with open(f"{backup_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Backup created: {backup_dir}")

# Schedule backup
# Run daily at 2 AM
# 0 2 * * * python backup_duckbot.py
```

This comprehensive user guide covers all aspects of DuckBot v4.2, from basic installation to advanced features. The guide provides step-by-step instructions, troubleshooting solutions, and practical examples to help users get the most out of their DuckBot experience.
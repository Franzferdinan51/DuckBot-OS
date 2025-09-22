# 🦆 DuckBotOS - Complete AI Web Operating System

**Next-generation AI-powered web operating system combining DaedalOS interface with Handcrafted Persona Engine and full DuckBot AI integration**

![DuckBotOS Logo](https://img.shields.io/badge/DuckBotOS-v1.0.0-blue?style=for-the-badge&logo=python&logoColor=white)

## 🌟 Overview

DuckBotOS represents the evolution of web-based operating systems, combining the powerful DaedalOS interface with the advanced Handcrafted Persona Engine and DuckBot's comprehensive AI capabilities. This creates a truly intelligent, interactive desktop experience with a live AI character persona.

## 🎯 Key Features

### 🤖 AI-Powered Interface
- **Live2D Character Persona**: Animated AI assistant with personality
- **Voice Synthesis**: Natural voice interactions with emotion
- **Real-time AI Processing**: Instant responses to commands and questions
- **Character Animation**: Expressive Live2D avatar with emotions

### 🎭 Handcrafted Persona Engine Integration
- **Advanced Character System**: Full integration with Franzferdinan51/handcrafted-persona-engine
- **Voice Cloning**: Optional RVC voice cloning for custom character voices
- **Emotion Recognition**: AI that understands and expresses emotions
- **Live Animation**: Real-time character animations and lip sync

### 🧠 Complete DuckBot AI Ecosystem
- **Multi-Model AI Routing**: Support for OpenAI, Anthropic, Qwen, and local models
- **Multi-Agent Coordination**: Archon-powered agent collaboration
- **Desktop Automation**: ByteBot integration for computer control
- **Memory & Learning**: Persistent conversation history and adaptive responses

### 🖥️ Modern Web Desktop
- **Intuitive Interface**: Modern, responsive web-based desktop environment
- **Application Management**: Web applications with AI integration
- **File System**: Complete file management with AI assistance
- **System Monitoring**: Real-time performance and resource tracking

## 🚀 Quick Start

### Requirements
- **Windows 10/11** (recommended)
- **Python 3.8+** (3.11+ recommended)
- **NVIDIA GPU** (required for Persona Engine features)
- **4GB RAM** minimum (8GB+ recommended)
- **LM Studio** (for local AI models)

### Installation

1. **Clone or Download DuckBot-Consolidated-v4.2**
```bash
git clone <repository-url>
cd DuckBot-Consolidated-v4.2
```

2. **Run the Enhanced Startup Script**
```bash
START_ENHANCED_DUCKBOT.bat
```

3. **Choose DuckBotOS Mode**
   - Select option `6` for DuckBotOS Complete AI OS
   - Wait for all services to initialize

4. **Access DuckBotOS**
   - Open your web browser to `http://localhost:8080`
   - Interact with your AI-powered desktop environment

## 🎮 Using DuckBotOS

### Web Interface Features

**Desktop Environment:**
- **AI Assistant**: Click the 🦆 icon or desktop shortcut
- **File Manager**: Browse and manage files with AI assistance
- **Terminal**: Command-line interface with AI-powered commands
- **Browser**: Web browsing with AI integration
- **Settings**: Configure AI models and system preferences
- **Automation**: Control desktop applications with natural language

**AI Assistant Capabilities:**
- **Natural Language**: Talk to your AI assistant naturally
- **Task Automation**: "Open notepad and write a hello world program"
- **System Control**: "Show me system resources" or "Organize my windows"
- **Web Search**: "Search for the latest AI developments"
- **File Operations**: "Find my presentation files" or "Create a new folder"

### Voice Interaction (if Persona Engine is running)

**Voice Commands:**
- **Wake Word**: "Hey DuckBot" to activate voice assistant
- **Natural Conversation**: Speak naturally to your AI character
- **Emotional Responses**: AI responds with appropriate emotions
- **Voice Control**: Control your computer with voice commands

### Advanced Features

**Multi-Agent System:**
- **Specialized Agents**: Different AI agents for specific tasks
- **Agent Coordination**: Agents work together on complex problems
- **Knowledge Sharing**: Agents share information and learn from each other

**Desktop Automation:**
- **Application Control**: Control any desktop application
- **Web Automation**: Automate browser tasks and interactions
- **File Operations**: Advanced file management and organization
- **System Administration**: System maintenance and optimization

## ⚙️ Configuration

### AI Model Configuration

DuckBotOS supports multiple AI providers:

**Local Models (LM Studio):**
```json
{
  "provider": "lm_studio",
  "base_url": "http://localhost:1234",
  "model": "local_model_name"
}
```

**Cloud Models:**
```json
{
  "provider": "openai",
  "api_key": "your-api-key",
  "model": "gpt-4"
}
```

**Persona Engine Settings:**
```json
{
  "character_model": "duckbot",
  "voice_model": "friendly",
  "enable_animations": true,
  "enable_speech": true,
  "enable_emotions": true
}
```

### Customization Options

**Character Persona:**
- Customize your AI assistant's personality
- Set up custom voice profiles
- Configure character appearance and animations

**Desktop Theme:**
- Light and dark themes
- Customizable desktop backgrounds
- Adjustable interface transparency

**System Integration:**
- Discord bot integration
- WSL support for Linux environments
- Custom service orchestration

## 🔧 Advanced Setup

### Persona Engine Integration

For full persona engine functionality:

1. **Install Dependencies**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r duckbot/integrations/handcrafted-persona-engine/requirements.txt
```

2. **Download Models**
   - Whisper ASR models for speech recognition
   - TTS models for voice synthesis
   - Live2D models for character animation

3. **Configure Persona**
   - Set up character personality in `personality.txt`
   - Configure voice and animation preferences
   - Test voice synthesis and emotion recognition

### Development Mode

For developers and advanced users:

```bash
# Development server with hot reload
python duckbot/integrations/duckbotos_integration.py --dev

# API-only mode
python duckbot/integrations/duckbotos_integration.py --api-only

# Headless mode for server deployment
python duckbot/integrations/duckbotos_integration.py --headless
```

## 📚 API Documentation

### Core Endpoints

**System Status:**
```http
GET /status
```

**Command Processing:**
```http
POST /command
{
  "command": "Open notepad and write hello world",
  "user_id": "user123",
  "context": {}
}
```

**Persona Engine:**
```http
POST /persona/generate
{
  "text": "Hello, I'm DuckBot!",
  "emotion": "happy",
  "gesture": "wave"
}
```

### WebSocket Interface

Real-time updates and bidirectional communication:

```javascript
const ws = new WebSocket('ws://localhost:8081/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('System update:', data);
};
```

## 🛠️ Troubleshooting

### Common Issues

**Persona Engine Not Starting:**
```bash
# Check NVIDIA GPU drivers
nvidia-smi

# Verify CUDA installation
nvcc --version

# Check if required ports are available
netstat -an | grep 8788
```

**AI Model Connection Issues:**
```bash
# Test LM Studio connection
curl http://localhost:1234/v1/models

# Verify API keys and endpoints
python -c "from duckbot.ai_router_gpt import AIRouter; print(AIRouter().get_available_models())"
```

**Web Interface Not Loading:**
```bash
# Check if port 8080 is available
netstat -an | grep 8080

# Restart web server
python -m http.server 8080 --directory duckbot/integrations/duckbotos-webui
```

### Performance Optimization

**Memory Management:**
- Monitor RAM usage with system monitor
- Adjust model cache sizes in configuration
- Use lighter models for low-resource systems

**GPU Optimization:**
- Configure CUDA memory allocation
- Adjust batch sizes for AI processing
- Monitor GPU temperature and usage

## 🎨 Customization

### Creating Custom Characters

1. **Design Character Assets**
   - Live2D model (.model3.json)
   - Voice samples for cloning
   - Character sprites and animations

2. **Configure Personality**
   ```
   You are [character name], a [description].
   You are [personality traits] and [speaking style].
   You have [knowledge/abilities] and [interests].
   ```

3. **Set Up Voice Profile**
   - Record voice samples for RVC training
   - Configure TTS parameters
   - Test voice synthesis quality

### Developing Applications

DuckBotOS supports web application development:

```javascript
// Example: DuckBotOS App
class DuckBotApp {
  constructor(name, icon) {
    this.name = name;
    this.icon = icon;
    this.aiIntegration = true;
  }

  async executeCommand(command) {
    // Process AI commands
    const result = await duckbotAPI.processCommand(command);
    return result;
  }
}
```

## 🤝 Community & Support

### Getting Help
- **Discord Server**: Join our community for support
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the wiki for detailed guides

### Contributing
We welcome contributions! Please see our contributing guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Showcasing Your DuckBotOS
We'd love to see how you're using DuckBotOS! Share your setups and creations:
- Screenshot your DuckBotOS desktop
- Share your custom characters
- Demonstrate your automation workflows

## 📄 License

DuckBotOS is released under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- **DaedalOS**: For the inspiring web-based operating system interface
- **Handcrafted Persona Engine**: For the amazing character animation system
- **DuckBot Community**: For continuous support and feedback
- **Open Source Community**: For the incredible tools and libraries

---

**🚀 Ready to experience the future of AI-powered computing? Launch DuckBotOS today!**

Remember: With DuckBotOS, you're not just using an operating system—you're interacting with a living, learning AI companion that grows with you.

*DuckBotOS - Where AI meets the desktop* 🦆✨
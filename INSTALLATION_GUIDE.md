# DuckBot v3.1.0+ Ultimate Edition - Installation Guide

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), or WSL2
- **Python**: 3.8 or higher with pip
- **RAM**: 4GB (8GB+ recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for cloud features (optional)

### Recommended Setup
- **GPU**: NVIDIA GPU with CUDA support (for acceleration)
- **RAM**: 16GB+ for optimal performance  
- **WSL**: Windows Subsystem for Linux (for cross-platform features)
- **Docker**: For containerized services (optional)

## Quick Installation

### Windows Users
1. Extract the DuckBot package to your desired location
2. Double-click `START_ULTIMATE_DUCKBOT.bat`
3. Follow the interactive setup prompts
4. Access the WebUI at http://127.0.0.1:8787

### Linux/WSL Users  
1. Extract the package: `unzip DuckBot-v3.1.0-Ultimate-*.zip`
2. Navigate to the folder: `cd DuckBot-*/`
3. Make script executable: `chmod +x start_ultimate_duckbot.sh`
4. Run the launcher: `./start_ultimate_duckbot.sh`

## Manual Installation Steps

### 1. Python Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# For GPU acceleration (NVIDIA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For image/video processing
pip install opencv-python Pillow imageio
```

### 2. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (optional for local-only mode)
nano .env
```

### 3. System Integration
```bash
# Windows: Enable WSL (run as Administrator)
wsl --install

# Linux: Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv
```

## Configuration Options

### AI Provider Setup
- **Local Only**: No API keys needed - uses LM Studio
- **Cloud + Local**: Add OpenRouter API key to .env
- **Discord Bot**: Add Discord token for bot features

### Feature Toggles
Edit `.env` file to enable/disable features:
```bash
# Core settings
AI_LOCAL_ONLY_MODE=true          # Privacy mode
ENABLE_ENHANCED_WEBUI=true       # Modern WebUI
ENABLE_WSL_INTEGRATION=true      # Linux integration
ENABLE_DESKTOP_AUTOMATION=true   # ByteBot features

# Optional services  
ENABLE_VIDEO_FEATURES=false      # Video generation
ENABLE_VOICE_FEATURES=true       # Voice synthesis
ENABLE_NOTEBOOK_FEATURES=true    # Jupyter integration
```

## Launch Modes

### Ultimate Enhanced Mode (Recommended)
- All features enabled
- Best performance and capabilities
- Requires more system resources

### Local-First Privacy Mode  
- Complete offline operation
- Zero external API calls
- Lower system requirements
- Full feature parity with cloud mode

### Hybrid Cloud+Local Mode
- Best of both worlds
- Local models preferred for privacy
- Cloud fallback for advanced features
- Optimal cost efficiency

## Troubleshooting

### Common Issues

**Python not found**
- Install Python 3.8+ from https://python.org
- Ensure Python is added to system PATH

**Permission errors (Windows)**
- Run command prompt as Administrator
- Check antivirus software settings

**WSL not available**
- Enable WSL feature in Windows Features
- Install Ubuntu from Microsoft Store
- Restart system after installation

**Dependencies failed to install**
- Upgrade pip: `python -m pip install --upgrade pip`
- Use virtual environment: `python -m venv duckbot_env`
- Install with --user flag: `pip install --user -r requirements.txt`

**GPU not detected**
- Install NVIDIA drivers
- Install CUDA toolkit
- Verify with: `nvidia-smi`

### Getting Help

1. Check the logs in `logs/` folder
2. Run diagnostics: Choose option 'S' in launcher  
3. Review documentation in `docs/` folder
4. Check GitHub issues for known problems

## Advanced Configuration

### Custom AI Models
1. Install LM Studio from https://lmstudio.ai
2. Download compatible models (Qwen, Gemma, etc.)  
3. Start local server on port 1234
4. DuckBot will automatically detect and use local models

### Docker Deployment
```bash
# Build container (if Dockerfile provided)
docker build -t duckbot:ultimate .

# Run with GPU support
docker run --gpus all -p 8787:8787 duckbot:ultimate
```

### Development Setup
```bash
# Clone for development
git clone <repository-url>
cd duckbot

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **Network**: WebUI binds to localhost by default
- **Logs**: Check logs don't contain sensitive information
- **Updates**: Keep dependencies updated for security patches

## Performance Optimization

### For Limited Resources
- Use Local-First Privacy Mode
- Disable video features
- Reduce AI model sizes
- Close unnecessary services

### For High Performance  
- Enable GPU acceleration
- Use SSD storage
- Increase system RAM
- Use wired network connection

---

**Support**: For additional help, consult the documentation or community resources.
**Version**: 2025-09-07

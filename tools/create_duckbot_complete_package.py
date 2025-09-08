#!/usr/bin/env python3
"""
DuckBot v3.0.7 Complete Package Creator
Creates comprehensive zip package with all features except ComfyUI installation
Includes ComfyUI workflows, action logging system, enhanced AI routing, and all components
"""

import os
import shutil
import zipfile
import time
from pathlib import Path
from datetime import datetime

def create_package():
    """Create comprehensive DuckBot package"""
    
    # Package information
    version = "3.0.7"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"DuckBot-v{version}-Complete-{timestamp}"
    
    print(f"Creating DuckBot v{version} Complete Package...")
    print(f"Package: {package_name}")
    print("="*60)
    
    base_dir = Path(__file__).parent
    temp_dir = base_dir / f"{package_name}_temp"
    zip_path = base_dir / f"{package_name}.zip"
    
    # Clean up any existing temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    temp_dir.mkdir()
    
    # Core DuckBot files and directories to include
    include_files = [
        # Core system files
        "duckbot/",
        "ai_cache/",
        "logs/",
        "notebooks/",
        "output/",
        "workflows/",
        "open-notebook/",
        "python_embeded/",
        
        # Configuration and documentation
        "CLAUDE.md",
        "README.md",
        "QUICKSTART.md",
        "QWEN.md",
        "COMFYUI_SETUP.md",
        "AI-Information.md",
        "AGENTS.md",
        "FIXES_CHANGELOG.md",
        "FINAL_IMPROVEMENTS_SUMMARY.md",
        "qwen_system_prompt.md",
        "ecosystem_config.yaml",
        
        # Setup and launch scripts
        "SETUP_AND_START.bat",
        "SETUP_AND_START_ENHANCED.bat",
        "START_DUCKBOT.bat",
        "START_COMFYUI.bat",
        "launch_ultra_lowvram.bat",
        "EMERGENCY_KILL.bat",
        "QUICK_KILL.bat",
        "install_missing_services.bat",
        
        # Test scripts
        "test_enhanced_system.bat",
        "test_action_reasoning_system.bat",
        "test_all_features.py",
        "test_every_feature.py",
        "test_simple.py",
        
        # Python core scripts
        "start_ecosystem.py",
        "start_ai_ecosystem.py",
        "ai_ecosystem_manager.py",
        "direct_launch.py",
        "start_comfyui.py",
        "start_cost_dashboard.py",
        "chat_with_ai.py",
        "setup_ai_provider.py",
        
        # Configuration files
        "ai_config.json",
        "requirements.txt",
        "requirements-core.txt", 
        "requirements-extras.txt",
        "sitecustomize.py",
        
        # ComfyUI workflows and integrations (but not ComfyUI itself)
        "ChatBot-DuckBot.json",
        "ChatBot-DuckBot-Safe.json", 
        "DuckBot-Audio-DuckTown-Integration.json",
        
        # Database files (if they exist)
        "ecosystem_state.db",
        "cost_tracking.db",
    ]
    
    # Files to exclude (ComfyUI installation and large binaries)
    exclude_patterns = [
        "ComfyUI/",  # Exclude ComfyUI installation
        "ComfyUI_windows_portable/",
        "DuckBotCompleteCOMFYUI.rar",
        "*.zip",  # Exclude existing zip files
        "*.rar",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.tmp",
        ".git/",
        ".gitignore",
        "venv/",
        "env/",
    ]
    
    print("📁 Copying core files and directories...")
    copied_count = 0
    
    for item in include_files:
        src_path = base_dir / item
        if src_path.exists():
            dest_path = temp_dir / item
            
            if src_path.is_dir():
                print(f"  📂 Copying directory: {item}")
                shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns(*exclude_patterns))
            else:
                print(f"  📄 Copying file: {item}")
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
            copied_count += 1
        else:
            print(f"  ⚠️  Not found (skipping): {item}")
    
    print(f"\n✅ Copied {copied_count} items")
    
    # Create comprehensive package documentation
    create_package_docs(temp_dir, version)
    
    # Create the zip package
    print(f"\n📦 Creating zip package: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            # Filter out excluded patterns from directories
            dirs[:] = [d for d in dirs if not any(d.startswith(pattern.rstrip('/')) for pattern in exclude_patterns if pattern.endswith('/'))]
            
            for file in files:
                # Skip excluded file patterns
                if any(file.endswith(pattern.lstrip('*.')) for pattern in exclude_patterns if pattern.startswith('*.')):
                    continue
                
                file_path = Path(root) / file
                arc_name = file_path.relative_to(temp_dir)
                zf.write(file_path, arc_name)
                
    # Clean up temp directory
    shutil.rmtree(temp_dir)
    
    # Get final package size
    package_size = zip_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"\n🎉 Package created successfully!")
    print(f"📦 File: {zip_path.name}")
    print(f"📊 Size: {package_size:.1f} MB")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create summary file
    create_package_summary(zip_path, version, package_size)
    
    return zip_path

def create_package_docs(temp_dir, version):
    """Create comprehensive package documentation"""
    
    # Create main package README
    readme_content = f"""# DuckBot v{version} Complete Package

## 🚀 Professional AI-Powered Crypto Analysis & Broadcasting System

This complete package includes all DuckBot features with the latest enhancements:

### ✅ New in v{version} - Action & Reasoning System
- **Comprehensive AI Decision Tracking**: Every AI routing decision logged with full reasoning
- **Automatic Fallback Logging**: Qwen → GLM 4.5 Air → Local fallbacks with error analysis  
- **Rate Limiting Intelligence**: Separate buckets for chat/background with detailed monitoring
- **Server Management Logging**: All service operations tracked with timing and outcomes
- **Professional WebUI Dashboard**: Beautiful log viewer at `/action-logs` with real-time updates
- **Enterprise Database**: SQLite storage with performance indexing and retention policies

### 🎯 Core Features Included
- **Enhanced AI Routing**: Smart model selection with automatic fallbacks (no more timeout errors!)
- **Separate Rate Limits**: Chat (30/min), Background (30/min) - uninterrupted chat experience
- **Professional WebUI**: Comprehensive dashboard with cost analysis and action logs
- **Server Management**: Auto-start ComfyUI, n8n, Jupyter with intelligent monitoring
- **Discord Integration**: Full bot functionality with crypto analysis and broadcasting
- **Cost Tracking**: Real-time analysis with detailed breakdowns and visualizations
- **Jupyter Integration**: Data analysis notebooks with auto-start capability
- **Voice Features**: TTS/STT integration for audio interactions

### 📁 Package Contents
- **Core System**: Complete DuckBot ecosystem with all enhancements
- **WebUI Dashboard**: Professional interface with action logging and cost analysis
- **AI Router**: Enhanced routing with fallbacks and reasoning capture
- **Server Manager**: Intelligent service management with logging
- **Action Logger**: Comprehensive decision tracking system
- **ComfyUI Workflows**: Ready-to-use workflows (ComfyUI installation sold separately)
- **Documentation**: Complete setup guides and troubleshooting
- **Test Suites**: Comprehensive validation scripts
- **Configuration**: Pre-configured settings and templates

### 🛠️ Installation Requirements
- **Python 3.8+**: Included portable version for Windows
- **Node.js**: Auto-installed by setup scripts
- **ComfyUI**: Separate installation required (workflows included)
- **API Keys**: OpenRouter, Anthropic, etc. (setup wizard included)

### 🚀 Quick Start
1. Extract package to desired location
2. Run `SETUP_AND_START.bat` (Windows) or setup script
3. Choose option 1 for full AI-enhanced experience
4. Follow setup wizard for API keys and configuration
5. Access WebUI dashboard and start analyzing!

### 📊 Enhanced Features
- **Action & Reasoning Logs**: View all AI decisions with full context
- **Real-time Monitoring**: Live service health and performance tracking  
- **Professional UI**: Beautiful, responsive interface with dark/light themes
- **Advanced Analytics**: Cost tracking, performance metrics, error analysis
- **Enterprise Logging**: Structured logs with rotation and retention
- **Smart Recovery**: Automatic service restart with cooldown policies

### 🔧 Technical Details
- **Database**: SQLite with performance indexing
- **API**: RESTful endpoints for programmatic access
- **Security**: Token-based authentication and sanitized logging
- **Performance**: Optimized for production use with minimal overhead
- **Compatibility**: Windows, macOS, Linux support

### 📞 Support
- **Documentation**: Comprehensive guides in `/docs`
- **Testing**: Run `test_enhanced_system.bat` for validation
- **Troubleshooting**: Built-in doctor mode for diagnostics
- **Community**: GitHub issues and discussions

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Version: DuckBot v{version} Complete Package
"""
    
    with open(temp_dir / "PACKAGE_README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Create installation guide
    install_guide = f"""# DuckBot v{version} Installation Guide

## 📋 Prerequisites
- Windows 10/11 (primary support) or macOS/Linux
- 8GB+ RAM recommended
- 10GB+ free disk space
- Internet connection for setup

## 🚀 Quick Installation

### Option 1: Automated Setup (Recommended)
1. Extract package to `C:\\DuckBot\\` (or preferred location)
2. Run `SETUP_AND_START.bat` as Administrator
3. Choose option 1 for "AI-Enhanced WebUI Dashboard"
4. Follow the setup wizard:
   - API keys configuration
   - Service installation
   - System validation
5. Access dashboard at http://localhost:8787

### Option 2: Manual Setup
1. Extract package
2. Install Python 3.8+ (portable version included)
3. Run: `pip install -r requirements.txt`
4. Configure API keys in `ai_config.json`
5. Run: `python start_ecosystem.py`

## 🔑 API Keys Setup
Required for full functionality:
- **OpenRouter**: For cloud AI models (Qwen, GLM)
- **Anthropic**: For Claude integration (optional)
- **OpenAI**: For GPT models (optional)

Setup wizard will guide you through configuration.

## 🧪 Validation
Run comprehensive tests:
```bash
test_enhanced_system.bat          # Complete system test
test_action_reasoning_system.bat  # Action logging test
python test_all_features.py       # Feature validation
```

## 🩺 Troubleshooting
1. Run doctor mode: Choose option 4 in setup menu
2. Check logs in `/logs` directory
3. Review action logs at `/action-logs` in WebUI
4. Use emergency kill: `EMERGENCY_KILL.bat`

## 📁 Directory Structure
```
DuckBot/
├── duckbot/              # Core system
├── workflows/            # ComfyUI workflows
├── logs/                 # System logs
├── notebooks/           # Jupyter notebooks
├── SETUP_AND_START.bat  # Main launcher
└── docs/                # Documentation
```

## 🎯 Next Steps
1. Access WebUI: http://localhost:8787
2. View action logs: http://localhost:8787/action-logs
3. Monitor costs: http://localhost:8787/cost
4. Configure settings: http://localhost:8787/settings
5. Start Discord bot (optional)

For detailed documentation, see CLAUDE.md and README.md files.
"""
    
    with open(temp_dir / "INSTALLATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(install_guide)

def create_package_summary(zip_path, version, package_size):
    """Create package summary file"""
    
    summary_file = zip_path.with_suffix('.txt')
    summary_content = f"""DuckBot v{version} Complete Package Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PACKAGE DETAILS:
- Name: {zip_path.name}
- Size: {package_size:.1f} MB
- Version: {version}
- Type: Complete Package (excludes ComfyUI installation)

FEATURES INCLUDED:
✅ Action & Reasoning Log System v{version}
  - Comprehensive AI decision tracking with full context
  - Automatic fallback logging (Qwen → GLM → Local)
  - Rate limiting intelligence with separate buckets
  - Server management logging with timing analysis
  - Professional WebUI dashboard with real-time updates
  - Enterprise SQLite database with performance indexing

✅ Enhanced AI Routing System
  - Smart model selection with automatic fallbacks
  - No more timeout errors shown to users
  - Separate rate limits: Chat (30/min), Background (30/min)
  - Smart model rotation to prevent OpenRouter limits
  - Circuit breaker patterns for reliability

✅ Fixed WebUI Issues
  - Resolved infinite "waiting for background tasks" loop
  - Removed problematic Unicode characters
  - Enhanced lifespan management with proper timeouts
  - Improved error handling and graceful shutdowns

✅ Professional WebUI Dashboard
  - Beautiful responsive interface
  - Action logs viewer at /action-logs
  - Cost analysis dashboard at /cost
  - Settings management at /settings
  - Real-time monitoring and updates

✅ Server Management System
  - Intelligent ComfyUI startup with GPU optimization
  - Auto-installation scripts for missing services
  - Service health monitoring and auto-restart
  - Comprehensive logging of all operations

✅ Complete Ecosystem
  - Discord bot integration
  - Jupyter notebook support
  - n8n workflow automation
  - Open Notebook AI interface
  - Cost tracking and visualization
  - Voice features (TTS/STT)

INSTALLATION:
1. Extract package to desired location
2. Run SETUP_AND_START.bat (Windows)
3. Choose option 1 for full AI-enhanced experience
4. Follow setup wizard for configuration
5. Access WebUI at http://localhost:8787

REQUIREMENTS:
- Python 3.8+ (portable version included)
- Node.js (auto-installed by setup)
- ComfyUI (separate installation - workflows included)
- API keys (OpenRouter, Anthropic, etc.)

VALIDATION:
- Run test_enhanced_system.bat for complete validation
- Run test_action_reasoning_system.bat for logging tests
- Use doctor mode (option 4) for diagnostics

SUPPORT:
- Documentation: CLAUDE.md, README.md, INSTALLATION_GUIDE.md
- Testing: Comprehensive test suites included
- Troubleshooting: Built-in doctor mode
- Logs: Structured logging in /logs directory

This package represents the complete DuckBot v{version} system with all
enhancements, fixes, and new features. Ready for production deployment
with enterprise-grade reliability and comprehensive decision tracking.
"""
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_content)
    
    print(f"📄 Summary created: {summary_file.name}")

if __name__ == "__main__":
    try:
        package_path = create_package()
        print(f"\n✨ DuckBot Complete Package ready: {package_path.name}")
        
    except Exception as e:
        print(f"\n❌ Error creating package: {e}")
        import traceback
        traceback.print_exc()
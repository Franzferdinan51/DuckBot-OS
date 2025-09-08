#!/usr/bin/env python3
"""
DuckBot OS v4.1 - Complete Deployment Package Creator
Creates a clean, deployment-ready package with only essential files for new users.
"""

import os
import shutil
import zipfile
import json
from datetime import datetime

def create_deployment_package():
    """Create a clean deployment package for DuckBot OS v4.1"""
    
    # Get current directory
    current_dir = os.getcwd()
    package_name = f"DuckBot-OS-v4.1-Complete-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    temp_dir = os.path.join("C:/Users/Ryan/Desktop", package_name)
    
    print("DuckBot OS v4.1 - Deployment Package Creator")
    print("=" * 60)
    print(f"Creating package: {package_name}")
    print(f"Source directory: {current_dir}")
    print(f"Output directory: {temp_dir}")
    print()
    
    # Create temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Essential files for deployment
    essential_files = [
        # Core startup scripts
        "START_ENHANCED_DUCKBOT.bat",
        "START_LOCAL_ONLY.bat", 
        "EMERGENCY_KILL.bat",
        
        # Documentation
        "README.md",
        "CLAUDE.md",
        
        # Python core files
        "requirements.txt",
        "ai_config.json",
        "ecosystem_config.yaml",
        
        # Environment templates
        ".env.example",
        
        # Core Python scripts
        "start_ai_ecosystem.py",
        "start_local_ecosystem.py", 
        "start_ecosystem.py",
        "chat_with_ai.py",
        "test_every_feature.py",
        "hardware_detector.py",
        "dynamic_model_manager.py",
        "test_hardware_detection.py",
        "model_status.py",
        "ai_ecosystem_manager.py",
        
        # Testing and validation
        "test_local_feature_parity.py",
        "TEST_LOCAL_PARITY.bat",
        "CHECK_MODEL_STATUS.bat",
    ]
    
    # Essential directories
    essential_dirs = [
        "duckbot",         # Core DuckBot modules
        "duckbot-os",      # Complete DuckBot OS
        "workflows",       # n8n automation workflows
    ]
    
    # Copy essential files
    print("Copying essential files...")
    for file in essential_files:
        if os.path.exists(file):
            print(f"  OK: {file}")
            shutil.copy2(file, temp_dir)
        else:
            print(f"  WARNING: Missing: {file}")
    
    # Copy essential directories
    print()
    print("Copying essential directories...")
    for dir_name in essential_dirs:
        if os.path.exists(dir_name):
            dest_dir = os.path.join(temp_dir, dir_name)
            
            if dir_name == "duckbot":
                # Copy duckbot directory but exclude certain files
                print(f"  DIR: {dir_name}/ (excluding cache, logs, temp files)")
                shutil.copytree(dir_name, dest_dir, ignore=shutil.ignore_patterns(
                    '*.pyc', '__pycache__', '*.log', '*.db', 'node_modules', '.git*'
                ))
                
            elif dir_name == "duckbot-os":
                # Copy complete DuckBot OS
                print(f"  DIR: {dir_name}/ (complete OS)")
                shutil.copytree(dir_name, dest_dir, ignore=shutil.ignore_patterns(
                    'node_modules', '.git*', 'dist', 'build'
                ))
                
            else:
                # Copy other directories normally
                print(f"  DIR: {dir_name}/")
                shutil.copytree(dir_name, dest_dir, ignore=shutil.ignore_patterns(
                    '*.pyc', '__pycache__', '.git*'
                ))
        else:
            print(f"  WARNING: Missing directory: {dir_name}")
    
    # Create .env.example if it doesn't exist
    env_example_path = os.path.join(temp_dir, ".env.example")
    if not os.path.exists(env_example_path):
        print("Creating .env.example template...")
        with open(env_example_path, 'w') as f:
            f.write("""# DuckBot OS v4.1 Configuration Template
# Copy to .env and fill in your values

# Discord Bot (Optional)
DISCORD_TOKEN=your_discord_token_here

# OpenRouter API (Optional - has free tier)
OPENROUTER_API_KEY=your_openrouter_key_here

# AI Configuration
AI_CONFIDENCE_MIN=0.75
AI_LOCAL_CONF_MIN=0.68
OPENROUTER_BUDGET_PER_MIN=6

# WebUI Configuration  
DUCKBOT_WEBUI_HOST=127.0.0.1
DUCKBOT_WEBUI_PORT=8787

# Feature Toggles
ENABLE_VIDEO_FEATURES=false
ENABLE_VOICE_FEATURES=true
ENABLE_NOTEBOOK_FEATURES=true
MAX_MEMORY_THRESHOLD=85.0

# LM Studio Integration (for local AI)
LM_STUDIO_URL=http://localhost:1234
""")
    
    # Create package info file
    package_info_path = os.path.join(temp_dir, "PACKAGE_INFO.json")
    package_info = {
        "name": "DuckBot OS v4.1 Complete",
        "version": "4.1.0",
        "build_date": datetime.now().isoformat(),
        "description": "Complete AI Operating System with 3D Avatar and Desktop Environment",
        "features": [
            "3D Interactive Avatar with voice synthesis",
            "Chrome OS-like React desktop environment", 
            "Complete application suite (Terminal, Files, Browser, Code Editor)",
            "Universal hardware optimization",
            "Intelligent AI model routing (LM Studio + OpenRouter + Qwen)",
            "SmythOS + SIM.ai integration",
            "Visual workflow designer with n8n",
            "RAG knowledge base management",
            "Cost analytics and usage tracking",
            "Windows device voice integration",
            "Cosmic DuckBot helper"
        ],
        "requirements": {
            "python": "3.8+",
            "node": "16+ (optional for full React desktop)",
            "memory": "8GB+ RAM recommended",
            "storage": "5GB+ free space"
        },
        "quick_start": [
            "1. Extract package to desired location",
            "2. Double-click START_ENHANCED_DUCKBOT.bat",
            "3. Choose Option 1 for complete DuckBot OS experience",
            "4. Copy token URL from terminal to browser",
            "5. Enjoy your AI operating system!"
        ]
    }
    
    with open(package_info_path, 'w') as f:
        json.dump(package_info, f, indent=2)
    
    # Create DEPLOYMENT_INSTRUCTIONS.md
    instructions_path = os.path.join(temp_dir, "DEPLOYMENT_INSTRUCTIONS.md")
    with open(instructions_path, 'w') as f:
        f.write("""# DuckBot OS v4.1 - Deployment Instructions

## Quick Start (3 Minutes)

1. **Extract Package**
   - Extract this zip to your desired location (e.g., `C:\\DuckBot-OS\\`)

2. **One-Click Launch**
   - Double-click `START_ENHANCED_DUCKBOT.bat`
   - Choose **Option 1** for complete DuckBot OS experience

3. **Access Your AI OS**
   - Copy the token URL from terminal output
   - Paste in your web browser
   - Enjoy DuckBot OS with 3D Avatar!

## What You Get

- **Complete AI Operating System**
- 3D Interactive Avatar with voice synthesis
- Chrome OS-like React desktop environment
- All applications: Terminal, Files, Browser, Code Editor
- Real-time system monitoring and analytics

- **Universal Hardware Support**
- Automatically optimizes for your GPU/CPU
- Works on RTX 4090 workstations to integrated graphics
- Smart model recommendations and resource management

- **Advanced AI Features**
- Intelligent model routing (Local + Cloud)
- Natural language command processing
- SmythOS provider abstraction
- Visual workflow designer

## AI Provider Setup (Optional)

### LM Studio (Local AI - Recommended)
1. Download: https://lmstudio.ai
2. Load models (Qwen, Nemotron, etc.)
3. Enable local server (localhost:1234)
4. DuckBot automatically detects your models

### OpenRouter (Cloud AI)
1. Get free API key: https://openrouter.ai
2. Add to `.env` file: `OPENROUTER_API_KEY=your_key`
3. Access hundreds of cloud models

## System Requirements

**Minimum:**
- Windows 10+ / macOS 10.15+ / Linux
- Python 3.8+
- 8GB RAM
- 2GB storage

**Recommended:**
- Windows 11 / Linux
- Python 3.10+
- 16GB+ RAM
- NVIDIA RTX GPU
- 5GB+ storage

## Troubleshooting

**DuckBot OS won't start:**
- Install Node.js from https://nodejs.org
- Run: `cd duckbot/react-webui && npm install`

**3D Avatar not loading:**
- Use modern browser (Chrome/Firefox/Edge)
- Enable WebGL in browser settings

**Need Help:**
- Ask DuckBot OS assistant directly
- Check README.md for detailed documentation
- Use built-in system diagnostics

---

**Welcome to the future of AI operating systems!**
""")
    
    # Create INSTALLATION_CHECKLIST.md
    checklist_path = os.path.join(temp_dir, "INSTALLATION_CHECKLIST.md")
    with open(checklist_path, 'w') as f:
        f.write("""# DuckBot OS v4.1 - Installation Checklist

## Pre-Installation
- [ ] Windows 10+ / macOS 10.15+ / Linux system
- [ ] Python 3.8+ installed (`python --version`)
- [ ] At least 8GB RAM available
- [ ] 5GB+ free storage space
- [ ] Modern web browser (Chrome/Firefox/Edge)

## Installation Steps
- [ ] Download DuckBot OS v4.1 package
- [ ] Extract to desired location
- [ ] Double-click `START_ENHANCED_DUCKBOT.bat`
- [ ] Choose installation option (1 = Complete Experience)
- [ ] Wait for dependency installation (may take a few minutes)
- [ ] Copy token URL to browser

## Verification
- [ ] DuckBot OS desktop loads successfully
- [ ] 3D Avatar responds to voice/text
- [ ] Applications launch properly (Terminal, Files, etc.)
- [ ] System monitoring shows real data
- [ ] Voice synthesis works

## Optional Enhancements  
- [ ] Install LM Studio for local AI (https://lmstudio.ai)
- [ ] Get OpenRouter API key for cloud models (https://openrouter.ai)
- [ ] Configure Discord bot (optional)
- [ ] Set up custom voices and themes

## Post-Installation
- [ ] Explore all desktop applications
- [ ] Try natural language commands
- [ ] Configure AI providers as needed
- [ ] Enjoy your complete AI operating system!

## Support
If any step fails:
1. Check system requirements
2. Try emergency recovery: `EMERGENCY_KILL.bat` then restart
3. Consult README.md for detailed troubleshooting
4. Ask DuckBot OS assistant for help

**Installation completed successfully! Welcome to DuckBot OS!**
""")
    
    # Create the zip file
    zip_path = f"{temp_dir}.zip"
    print()
    print("Creating deployment zip...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arc_path)
                
    # Get zip size
    zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
    
    # Clean up temp directory
    shutil.rmtree(temp_dir)
    
    print(f"Package created successfully!")
    print()
    print("Package Information:")
    print(f"   File: {os.path.basename(zip_path)}")
    print(f"   Size: {zip_size:.1f} MB")
    print(f"   Location: {zip_path}")
    print()
    print("What's Included:")
    print("   - Complete DuckBot OS with 3D Avatar")
    print("   - React desktop environment")
    print("   - All applications (Terminal, Files, Browser, etc.)")
    print("   - Universal hardware optimization")
    print("   - Enhanced AI capabilities") 
    print("   - Complete documentation")
    print("   - One-click installation")
    print()
    print("Ready for deployment to any Windows/Linux/Mac system!")
    
    return zip_path

if __name__ == "__main__":
    try:
        package_path = create_deployment_package()
        print(f"Deployment package ready: {package_path}")
    except Exception as e:
        print(f"Error creating package: {e}")
        import traceback
        traceback.print_exc()
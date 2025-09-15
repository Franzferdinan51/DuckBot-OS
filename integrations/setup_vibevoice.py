#!/usr/bin/env python3
"""
VibeVoice Setup and Installation Script for DuckBot
Installs and configures Microsoft VibeVoice TTS integration
"""
import os
import sys
import subprocess
import yaml
import json
from pathlib import Path
import logging
import asyncio
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class VibeVoiceSetup:
    """Setup and configuration manager for VibeVoice integration."""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.config_path = self.base_dir / "vibevoice_config.yaml"
        self.env_path = self.base_dir / ".env"
        
    def install_dependencies(self):
        """Install required Python packages for VibeVoice."""
        logger.info("Installing VibeVoice dependencies...")
        
        dependencies = [
            "aiohttp>=3.8.0",
            "torch>=2.0.0", 
            "torchaudio>=2.0.0",
            "transformers>=4.30.0",
            "accelerate>=0.20.0",
            "pyyaml>=6.0",
            "gradio>=3.40.0",  # For web interface
        ]
        
        try:
            for dep in dependencies:
                logger.info(f"Installing {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            
            logger.info("[OK] Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[FAIL] Failed to install dependencies: {e}")
            return False
    
    def setup_environment(self):
        """Configure environment variables for VibeVoice."""
        logger.info("Setting up environment configuration...")
        
        env_vars = {
            "ENABLE_VIBEVOICE": "true",
            "VIBEVOICE_API_URL": "http://localhost:8000",
            "VIBEVOICE_MODEL": "microsoft/VibeVoice-1.5B",
            "VIBEVOICE_MAX_TEXT_LENGTH": "2000",
            "VIBEVOICE_OUTPUT_DIR": "output/vibevoice"
        }
        
        try:
            # Read existing .env file if it exists
            existing_env = {}
            if self.env_path.exists():
                with open(self.env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_env[key] = value
            
            # Update with new variables
            existing_env.update(env_vars)
            
            # Write back to .env
            with open(self.env_path, 'w') as f:
                f.write("# DuckBot Environment Configuration\n\n")
                f.write("# VibeVoice TTS Configuration\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
                f.write("\n")
                
                # Write other existing vars
                for key, value in existing_env.items():
                    if key not in env_vars:
                        f.write(f"{key}={value}\n")
            
            logger.info("[OK] Environment configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to setup environment: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories for VibeVoice."""
        logger.info("Creating directories...")
        
        directories = [
            "output/vibevoice",
            "temp/vibevoice",
            "logs"
        ]
        
        try:
            for dir_path in directories:
                full_path = self.base_dir / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            
            logger.info("[OK] Directories created")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to create directories: {e}")
            return False
    
    def update_ai_config(self):
        """Update ai_config.json with VibeVoice settings."""
        logger.info("Updating AI configuration...")
        
        ai_config_path = self.base_dir / "ai_config.json"
        
        try:
            # Read existing config
            if ai_config_path.exists():
                with open(ai_config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Add VibeVoice configuration
            config["vibevoice"] = {
                "enabled": True,
                "api_url": "http://localhost:8000",
                "model": "microsoft/VibeVoice-1.5B",
                "max_text_length": 2000,
                "default_voices": ["en-alice", "en-carter"],
                "presets": {
                    "conversation": ["en-alice", "en-carter"],
                    "news": ["en-emily", "en-carter"],
                    "podcast": ["en-alice", "en-carter", "en-david"]
                }
            }
            
            # Write updated config
            with open(ai_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("[OK] AI configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to update AI config: {e}")
            return False
    
    async def test_vibevoice_server(self, url: str = "http://localhost:8000") -> bool:
        """Test if VibeVoice server is running."""
        logger.info(f"Testing VibeVoice server at {url}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/voices", timeout=10) as response:
                    if response.status == 200:
                        logger.info("[OK] VibeVoice server is running")
                        return True
                    else:
                        logger.warning(f"[WARN] VibeVoice server responded with status {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"[WARN] VibeVoice server not accessible: {e}")
            return False
    
    def create_startup_script(self):
        """Create startup script for VibeVoice server."""
        logger.info("Creating VibeVoice startup script...")
        
        startup_script = '''#!/bin/bash
# VibeVoice Server Startup Script

echo "[EMOJI] Starting VibeVoice TTS Server..."
echo "[LIST] This will download and start Microsoft VibeVoice"

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "[EMOJI] Using Docker for VibeVoice server..."
    
    # Run VibeVoice in Docker container
    docker run --rm -it --gpus all -p 8000:8000 \\
        -v $(pwd)/output:/app/output \\
        vibevoice/fastapi:latest
    
else
    echo "[EMOJI] Using Python for VibeVoice server..."
    
    # Check if VibeVoice is installed
    if [ ! -d "VibeVoice" ]; then
        echo "[EMOJI] Cloning VibeVoice repository..."
        git clone https://github.com/dontriskit/VibeVoice-FastAPI.git VibeVoice
        cd VibeVoice
        pip install -r requirements.txt
        cd ..
    fi
    
    # Start the server
    cd VibeVoice
    python main.py --host 0.0.0.0 --port 8000
fi
'''
        
        script_path = self.base_dir / "start_vibevoice_server.sh"
        
        try:
            with open(script_path, 'w') as f:
                f.write(startup_script)
            
            # Make executable on Unix systems
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            logger.info("[OK] Startup script created: start_vibevoice_server.sh")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to create startup script: {e}")
            return False
    
    def create_windows_startup(self):
        """Create Windows batch file for VibeVoice."""
        logger.info("Creating Windows startup script...")
        
        batch_script = '''@echo off
REM VibeVoice Server Startup Script for Windows

echo [EMOJI] Starting VibeVoice TTS Server...
echo [LIST] This will setup and start Microsoft VibeVoice

REM Check if VibeVoice directory exists
if not exist "VibeVoice-FastAPI" (
    echo [EMOJI] Cloning VibeVoice FastAPI repository...
    git clone https://github.com/dontriskit/VibeVoice-FastAPI.git
    if errorlevel 1 (
        echo [FAIL] Failed to clone repository
        pause
        exit /b 1
    )
)

REM Enter directory and install dependencies
cd VibeVoice-FastAPI

echo [PACKAGE] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [FAIL] Failed to install dependencies
    pause
    exit /b 1
)

echo [LAUNCH] Starting VibeVoice server on http://localhost:8000
echo ⏳ This may take a few minutes to download models...
echo [EMOJI] Web interface will be available once started

python main.py --host 0.0.0.0 --port 8000

pause
'''
        
        script_path = self.base_dir / "START_VIBEVOICE_SERVER.bat"
        
        try:
            with open(script_path, 'w') as f:
                f.write(batch_script)
            
            logger.info("[OK] Windows startup script created: START_VIBEVOICE_SERVER.bat")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to create Windows startup script: {e}")
            return False
    
    def generate_quick_setup(self):
        """Generate a quick setup guide."""
        logger.info("Creating setup guide...")
        
        guide = '''# VibeVoice Setup Guide for DuckBot

## Quick Start

1. **Install VibeVoice Server**:
   - Windows: Run `START_VIBEVOICE_SERVER.bat`
   - Linux/Mac: Run `./start_vibevoice_server.sh`

2. **Start DuckBot**:
   - Run your DuckBot with VibeVoice commands enabled
   - Use `/vibevoice` command in Discord

## VibeVoice Commands

- `/vibevoice` - Generate multi-speaker voice content
- `/voice_presets` - Show available voices and presets  
- `/voice_status` - Check VibeVoice server status
- `/voice_help` - Complete usage guide

## Voice Presets

- `alice` - Single female voice
- `carter` - Single male voice  
- `conversation` - Dialogue (alice + carter)
- `debate` - Formal discussion (david + emily)
- `podcast` - Multi-voice (alice + carter + david)
- `news` - Professional broadcast (emily + carter)

## Examples

```
/vibevoice text:"Hello, welcome to DuckBot!" preset:alice
/vibevoice text:"Alice: Hi there! Bob: Hello!" preset:conversation
/vibevoice text:"Breaking news..." preset:news
```

## Requirements

- NVIDIA GPU recommended (8GB+ VRAM)
- Python 3.8+
- ~5GB disk space for models
- Internet connection for initial model download

## Troubleshooting

- **Server not starting**: Check GPU drivers and CUDA installation
- **Generation fails**: Ensure text is under 2000 characters
- **No audio**: Verify VibeVoice server is running on port 8000

For more help, use `/voice_help` in Discord or check the logs.
'''
        
        guide_path = self.base_dir / "VIBEVOICE_SETUP.md"
        
        try:
            with open(guide_path, 'w') as f:
                f.write(guide)
            
            logger.info("[OK] Setup guide created: VIBEVOICE_SETUP.md")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to create setup guide: {e}")
            return False
    
    async def run_setup(self):
        """Run the complete VibeVoice setup process."""
        logger.info("[EMOJI] Starting VibeVoice setup for DuckBot...")
        
        steps = [
            ("Installing dependencies", self.install_dependencies),
            ("Setting up environment", self.setup_environment),
            ("Creating directories", self.create_directories),
            ("Updating AI config", self.update_ai_config),
            ("Creating startup scripts", self.create_startup_script),
            ("Creating Windows startup", self.create_windows_startup),
            ("Generating setup guide", self.generate_quick_setup)
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            logger.info(f"[LIST] {step_name}...")
            try:
                if step_func():
                    success_count += 1
                    logger.info(f"[OK] {step_name} completed")
                else:
                    logger.error(f"[FAIL] {step_name} failed")
            except Exception as e:
                logger.error(f"[FAIL] {step_name} failed with error: {e}")
        
        # Test server connection
        logger.info("[LIST] Testing VibeVoice server connection...")
        server_available = await self.test_vibevoice_server()
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("[EMOJI] VIBEVOICE SETUP SUMMARY")
        logger.info("="*60)
        logger.info(f"[OK] Setup steps completed: {success_count}/{len(steps)}")
        logger.info(f"[GLOBE] Server available: {'Yes' if server_available else 'No (needs manual start)'}")
        
        if success_count == len(steps):
            logger.info("[SUCCESS] VibeVoice setup completed successfully!")
            logger.info("\n[LIST] Next steps:")
            logger.info("1. Start VibeVoice server: START_VIBEVOICE_SERVER.bat")
            logger.info("2. Start DuckBot with VibeVoice integration")
            logger.info("3. Use /vibevoice command in Discord")
            logger.info("4. Read VIBEVOICE_SETUP.md for complete guide")
        else:
            logger.warning("[WARN] Some setup steps failed. Check logs and retry.")
        
        return success_count == len(steps)

def main():
    """Main setup function."""
    try:
        setup = VibeVoiceSetup()
        
        # Run async setup
        result = asyncio.run(setup.run_setup())
        
        if result:
            print("\n[EMOJI] VibeVoice setup completed successfully!")
            print("[EMOJI] Check VIBEVOICE_SETUP.md for usage instructions")
        else:
            print("\n[FAIL] Setup encountered some issues. Check the logs above.")
            
    except KeyboardInterrupt:
        print("\n[STOP] Setup cancelled by user")
    except Exception as e:
        print(f"\n[FAIL] Setup failed with error: {e}")
        
if __name__ == "__main__":
    main()
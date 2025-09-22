#!/usr/bin/env python3
"""
VibeVoice Setup Script for DuckBot v4.2
Configures environment and tests VibeVoice integration
"""

import os
import sys
import shutil
from pathlib import Path

def setup_vibevoice_environment():
    """Set up VibeVoice environment variables"""
    print("[SETUP] Configuring VibeVoice environment...")

    # Create output directory
    output_dir = Path("output/vibevoice")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Created output directory: {output_dir}")

    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("[INFO] .env file already exists")

        # Read current content
        with open(env_file, 'r') as f:
            env_content = f.read()

        # Add VibeVoice variables if not present
        vibevoice_vars = [
            "ENABLE_VIBEVOICE=true",
            "VIBEVOICE_API_URL=http://localhost:8000",
            "VIBEVOICE_MODEL=microsoft/VibeVoice-1.5B",
            "VIBEVOICE_MAX_TEXT_LENGTH=2000",
            "VIBEVOICE_OUTPUT_DIR=output/vibevoice"
        ]

        missing_vars = []
        for var in vibevoice_vars:
            if var.split('=')[0] not in env_content:
                missing_vars.append(var)

        if missing_vars:
            print("[INFO] Adding missing VibeVoice variables to .env")
            with open(env_file, 'a') as f:
                f.write("\n# VibeVoice TTS Configuration\n")
                for var in missing_vars:
                    f.write(f"{var}\n")
            print("[OK] Added VibeVoice configuration to .env")
        else:
            print("[OK] VibeVoice variables already configured")
    else:
        print("[INFO] Creating new .env file with VibeVoice configuration")
        with open(env_file, 'w') as f:
            f.write("# VibeVoice TTS Configuration\n")
            f.write("ENABLE_VIBEVOICE=true\n")
            f.write("VIBEVOICE_API_URL=http://localhost:8000\n")
            f.write("VIBEVOICE_MODEL=microsoft/VibeVoice-1.5B\n")
            f.write("VIBEVOICE_MAX_TEXT_LENGTH=2000\n")
            f.write("VIBEVOICE_OUTPUT_DIR=output/vibevoice\n")
        print("[OK] Created .env file")

def create_vibevoice_launcher():
    """Create VibeVoice server launcher script"""
    print("[SETUP] Creating VibeVoice launcher script...")

    launcher_content = '''@echo off
echo [EMOJI] Starting VibeVoice TTS Server...
echo [INFO] API URL: http://localhost:8000
echo [INFO] Model: microsoft/VibeVoice-1.5B

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if VibeVoice is installed
python -c "import vibevoice" >nul 2>&1
if errorlevel 1 (
    echo [WARN] VibeVoice not installed. Installing...
    pip install vibevoice-tts
)

REM Start VibeVoice server
echo [OK] Starting VibeVoice server on http://localhost:8000
python -m vibevoice.server --host localhost --port 8000 --model microsoft/VibeVoice-1.5B

pause
'''

    launcher_path = Path("START_VIBEVOICE_SERVER.bat")
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)

    print(f"[OK] Created launcher script: {launcher_path}")

def create_vibevoice_test_script():
    """Create VibeVoice test script"""
    print("[SETUP] Creating VibeVoice test script...")

    test_content = '''#!/usr/bin/env python3
"""
Quick VibeVoice Test Script
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_vibevoice():
    """Test VibeVoice integration"""
    try:
        from duckbot.integrations.vibevoice_client import vibevoice_integration

        print("[TEST] Testing VibeVoice integration...")

        # Test health
        health = await vibevoice_integration.get_health_status()
        print(f"[INFO] Health: {health}")

        # Test capabilities
        capabilities = vibevoice_integration.get_capabilities()
        print(f"[INFO] Capabilities: {capabilities}")

        if capabilities['available']:
            print("[OK] VibeVoice is available!")

            # Test generation (if server is running)
            result = await vibevoice_integration.generate_speech(
                text="Hello! This is a test of VibeVoice integration.",
                speakers=["en-alice"]
            )

            if result.get('success'):
                print(f"[OK] Generation successful: {result.get('audio_path')}")
            else:
                print(f"[WARN] Generation failed: {result.get('error')}")
        else:
            print("[WARN] VibeVoice is not available")
            print("[INFO] Make sure VibeVoice server is running: START_VIBEVOICE_SERVER.bat")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_vibevoice())
'''

    test_path = Path("test_vibevoice.py")
    with open(test_path, 'w') as f:
        f.write(test_content)

    print(f"[OK] Created test script: {test_path}")

def main():
    """Main setup function"""
    print("=" * 60)
    print("VIBEVOICE SETUP - DUCKBOT v4.2")
    print("=" * 60)

    try:
        # Setup environment
        setup_vibevoice_environment()

        # Create launcher
        create_vibevoice_launcher()

        # Create test script
        create_vibevoice_test_script()

        print("\n" + "=" * 60)
        print("SETUP COMPLETE!")
        print("=" * 60)
        print("Next steps:")
        print("1. Install VibeVoice: pip install vibevoice-tts")
        print("2. Start server: START_VIBEVOICE_SERVER.bat")
        print("3. Test integration: python test_vibevoice.py")
        print("4. Use in Discord: /vibevoice commands")
        print("\nConfiguration files created:")
        print("- .env (updated with VibeVoice settings)")
        print("- START_VIBEVOICE_SERVER.bat (server launcher)")
        print("- test_vibevoice.py (quick test script)")
        print("- vibevoice_config.env (configuration reference)")

    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
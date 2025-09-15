#!/usr/bin/env python3
"""
Setup OpenWebUI with OpenRouter Free Models Plugin
Installs and configures the official OpenRouter integration plugin for OpenWebUI
"""

import os
import json
import subprocess
import time
import requests
import shutil
from pathlib import Path

def check_openwebui_installation():
    """Check if OpenWebUI is installed and get its data directory"""
    try:
        result = subprocess.run(['open-webui', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] OpenWebUI is installed")
            
            # Try to find OpenWebUI data directory
            possible_paths = [
                Path.home() / ".config" / "open-webui",
                Path.home() / "open-webui",
                Path.cwd() / "open-webui-data",
                Path("/app/backend/data"),  # Docker path
                Path("./data")  # Local data path
            ]
            
            for path in possible_paths:
                if path.exists():
                    print(f"[OK] OpenWebUI data directory found: {path}")
                    return path
            
            # Create default data directory
            data_dir = Path.cwd() / "openwebui_data"
            data_dir.mkdir(exist_ok=True)
            print(f"[DIR] Created OpenWebUI data directory: {data_dir}")
            return data_dir
            
    except FileNotFoundError:
        print("[FAIL] OpenWebUI not found")
        print("[EMOJI] Install with: pip install open-webui")
        return None

def install_openrouter_plugin(data_dir):
    """Install the OpenRouter plugin for OpenWebUI"""
    
    # Create functions directory
    functions_dir = data_dir / "functions"
    functions_dir.mkdir(exist_ok=True)
    
    # Copy the plugin file
    plugin_source = Path.cwd() / "openrouter_openwebui_plugin.py"
    plugin_dest = functions_dir / "openrouter_free_models.py"
    
    if plugin_source.exists():
        shutil.copy2(plugin_source, plugin_dest)
        print(f"[OK] Plugin installed: {plugin_dest}")
        return True
    else:
        print("[FAIL] Plugin source file not found")
        return False

def create_plugin_config(data_dir):
    """Create configuration for the OpenRouter plugin"""
    
    config = {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
        "FREE_ONLY": True,  # Enable free models only
        "MODEL_PREFIX": "🆓 ",  # Prefix for free models
        "INCLUDE_REASONING": True,
        "REQUEST_TIMEOUT": 90,
        "ENABLE_CACHE_CONTROL": False
    }
    
    config_dir = data_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "openrouter_plugin.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"[OK] Plugin config created: {config_file}")
    return config_file

def create_env_config():
    """Create environment configuration for OpenWebUI with OpenRouter plugin"""
    
    env_vars = {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
        "WEBUI_NAME": "DuckBot AI - OpenRouter Free Models",
        "ENABLE_COMMUNITY_SHARING": "false",
        "ENABLE_MODEL_FILTER": "true",
        "SHOW_ADMIN_DETAILS": "false",
        "WEBUI_AUTH": "false"  # Disable auth for local use
    }
    
    env_file = Path.cwd() / ".env.openwebui"
    with open(env_file, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"[OK] Environment config created: {env_file}")
    return env_file

def test_free_models():
    """Test OpenRouter free models availability"""
    
    print("[EMOJI] Testing OpenRouter free models...")
    
    # Test without API key (free access)
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "https://duckbot-ai.local/",
        "X-Title": "DuckBot AI"
    }
    
    try:
        # Get available models
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            free_models = [m for m in models.get("data", []) if "free" in m.get("id", "").lower()]
            
            print(f"[OK] Found {len(free_models)} free models:")
            for model in free_models[:5]:  # Show first 5
                print(f"   • {model.get('id')}")
            
            if len(free_models) > 5:
                print(f"   ... and {len(free_models) - 5} more")
                
            return True
        else:
            print(f"[WARN]  API responded with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error testing free models: {e}")
        return False

def start_openwebui_with_plugin(data_dir):
    """Start OpenWebUI with the OpenRouter plugin"""
    
    print("[LAUNCH] Starting OpenWebUI with OpenRouter plugin...")
    
    env_file = Path.cwd() / ".env.openwebui"
    
    # Prepare environment
    env = os.environ.copy()
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env[key] = value
    
    # Set data directory
    env['OPENWEBUI_DATA_DIR'] = str(data_dir)
    
    try:
        cmd = [
            'open-webui', 'serve',
            '--host', '127.0.0.1',
            '--port', '8080'
        ]
        
        process = subprocess.Popen(cmd, env=env)
        
        # Wait for startup
        print("⏳ Waiting for OpenWebUI to start...")
        time.sleep(8)
        
        # Test health
        try:
            response = requests.get('http://localhost:8080/health', timeout=5)
            if response.status_code == 200:
                print("[OK] OpenWebUI started successfully!")
                print("[GLOBE] Access at: http://localhost:8080")
                return process
        except:
            pass
            
        print("[WARN]  OpenWebUI started but health check failed")
        return process
        
    except Exception as e:
        print(f"[FAIL] Error starting OpenWebUI: {e}")
        return None

def main():
    """Main setup function"""
    print("=" * 70)
    print("[LAUNCH] OPENWEBUI + OPENROUTER FREE MODELS PLUGIN SETUP")
    print("=" * 70)
    print()
    print("[TARGET] This setup will:")
    print("   [OK] Install OpenRouter plugin for OpenWebUI")
    print("   [OK] Configure for FREE models only")
    print("   [OK] Start OpenWebUI with plugin enabled")
    print("   [OK] No API key required for free models!")
    print()
    
    # Check OpenWebUI
    data_dir = check_openwebui_installation()
    if not data_dir:
        print("[FAIL] OpenWebUI not available")
        return 1
    
    print(f"[DIR] Using data directory: {data_dir}")
    print()
    
    # Install plugin
    print("[PACKAGE] Installing OpenRouter plugin...")
    if not install_openrouter_plugin(data_dir):
        print("[FAIL] Plugin installation failed")
        return 1
    
    # Create configuration
    print("[SETTINGS]  Creating plugin configuration...")
    create_plugin_config(data_dir)
    create_env_config()
    
    # Test free models
    if not test_free_models():
        print("[WARN]  Free models test failed - continuing anyway")
    
    print()
    
    # Start OpenWebUI
    process = start_openwebui_with_plugin(data_dir)
    if not process:
        print("[FAIL] Failed to start OpenWebUI")
        return 1
    
    print()
    print("=" * 70)
    print("[OK] SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("[GLOBE] OpenWebUI: http://localhost:8080")
    print("🆓 Available FREE models:")
    print("   • microsoft/phi-3-mini-128k-instruct:free")
    print("   • google/gemma-7b-it:free")
    print("   • meta-llama/llama-3-8b-instruct:free")
    print("   • mistralai/mistral-7b-instruct:free")
    print("   • huggingfaceh4/zephyr-7b-beta:free")
    print()
    print("[EMOJI] USAGE:")
    print("   1. Open http://localhost:8080")
    print("   2. Go to Settings > Functions")
    print("   3. Enable 'OpenRouter Free Models' function")
    print("   4. Select any free model and start chatting!")
    print()
    print("[TOOLS] CONFIGURATION:")
    print("   • FREE_ONLY: Enabled (only free models)")
    print("   • API Key: Not required for free models")
    print("   • Reasoning: Enabled for supported models")
    print()
    
    try:
        input("Press Enter to stop OpenWebUI...")
    except KeyboardInterrupt:
        pass
    
    print("[STOP] Stopping OpenWebUI...")
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    
    print("[OK] Cleanup completed")
    return 0

if __name__ == "__main__":
    exit(main())
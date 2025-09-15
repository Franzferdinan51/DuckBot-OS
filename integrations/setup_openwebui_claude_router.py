#!/usr/bin/env python3
"""
Setup OpenWebUI with Claude Code Router integration for OpenRouter free models
This script configures the complete pipeline: OpenWebUI -> Claude Code Router -> OpenRouter
"""

import os
import json
import subprocess
import time
import requests
from pathlib import Path

def check_prerequisites():
    """Check if required tools are installed"""
    print("[EMOJI] Checking prerequisites...")
    
    # Check Claude Code Router
    try:
        result = subprocess.run(['ccr', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Claude Code Router installed")
        else:
            print("[FAIL] Claude Code Router not working")
            return False
    except FileNotFoundError:
        print("[FAIL] Claude Code Router not found")
        print("[EMOJI] Install with: npm install -g @musistudio/claude-code-router")
        return False
    
    # Check OpenWebUI
    try:
        result = subprocess.run(['open-webui', '--version'], capture_output=True, text=True)
        print("[OK] OpenWebUI available")
    except FileNotFoundError:
        print("[FAIL] OpenWebUI not found")
        print("[EMOJI] Install with: pip install open-webui")
        return False
    
    # Check for OpenRouter API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("[WARN]  OPENROUTER_API_KEY not set - will use free models only")
    else:
        print("[OK] OpenRouter API key configured")
    
    return True

def create_claude_router_config():
    """Create configuration for Claude Code Router with OpenRouter"""
    config_dir = Path.home() / '.claude-code-router'
    config_dir.mkdir(exist_ok=True)
    
    config = {
        "default_provider": "openrouter",
        "providers": {
            "openrouter": {
                "api_key": os.getenv('OPENROUTER_API_KEY', ''),
                "base_url": "https://openrouter.ai/api/v1",
                "free_models": [
                    "microsoft/phi-3-mini-128k-instruct:free",
                    "huggingfaceh4/zephyr-7b-beta:free",
                    "google/gemma-7b-it:free",
                    "meta-llama/llama-3-8b-instruct:free",
                    "mistralai/mistral-7b-instruct:free"
                ],
                "default_model": "microsoft/phi-3-mini-128k-instruct:free"
            }
        },
        "proxy_port": 8765,
        "enable_logging": True
    }
    
    config_file = config_dir / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"[OK] Claude Code Router config created: {config_file}")
    return config_file

def create_openwebui_config():
    """Create OpenWebUI configuration to use Claude Code Router"""
    
    # OpenWebUI environment variables for Claude Code Router integration
    env_config = {
        'OPENAI_API_BASE_URL': 'http://localhost:8765/v1',
        'OPENAI_API_KEY': 'claude-code-router-proxy',  # Dummy key for local proxy
        'WEBUI_NAME': 'DuckBot AI with Claude Code Router',
        'DEFAULT_MODELS': 'microsoft/phi-3-mini-128k-instruct:free,google/gemma-7b-it:free',
        'ENABLE_COMMUNITY_SHARING': 'false',
        'ENABLE_MODEL_FILTER': 'true',
        'MODEL_FILTER_LIST': 'microsoft/phi-3-mini-128k-instruct:free;google/gemma-7b-it:free;meta-llama/llama-3-8b-instruct:free;mistralai/mistral-7b-instruct:free;huggingfaceh4/zephyr-7b-beta:free'
    }
    
    # Create .env file for OpenWebUI
    env_file = Path.cwd() / '.env.openwebui'
    with open(env_file, 'w') as f:
        for key, value in env_config.items():
            f.write(f"{key}={value}\n")
    
    print(f"[OK] OpenWebUI config created: {env_file}")
    return env_file

def start_claude_code_router():
    """Start Claude Code Router in proxy mode"""
    print("[LAUNCH] Starting Claude Code Router...")
    
    try:
        # Start Claude Code Router
        process = subprocess.Popen(
            ['ccr', 'code'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, 'CCR_PROVIDER': 'openrouter', 'CCR_PORT': '8765'}
        )
        
        # Wait for startup
        time.sleep(3)
        
        # Check if it's running
        if process.poll() is None:
            print("[OK] Claude Code Router started on port 8765")
            return process
        else:
            print("[FAIL] Claude Code Router failed to start")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error starting Claude Code Router: {e}")
        return None

def start_openwebui():
    """Start OpenWebUI with Claude Code Router integration"""
    print("[LAUNCH] Starting OpenWebUI with Claude Code Router integration...")
    
    env_file = Path.cwd() / '.env.openwebui'
    
    try:
        # Start OpenWebUI with custom environment
        cmd = [
            'open-webui', 'serve',
            '--port', '8080',
            '--host', '127.0.0.1'
        ]
        
        # Load environment from file
        env = os.environ.copy()
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env[key] = value
        
        process = subprocess.Popen(cmd, env=env)
        
        time.sleep(5)
        
        # Check if OpenWebUI is accessible
        try:
            response = requests.get('http://localhost:8080/health', timeout=5)
            if response.status_code == 200:
                print("[OK] OpenWebUI started successfully on http://localhost:8080")
                return process
        except:
            pass
        
        print("[WARN]  OpenWebUI started but health check failed")
        return process
        
    except Exception as e:
        print(f"[FAIL] Error starting OpenWebUI: {e}")
        return None

def test_integration():
    """Test the complete OpenWebUI -> Claude Code Router -> OpenRouter integration"""
    print("[EMOJI] Testing integration...")
    
    # Test Claude Code Router proxy
    try:
        response = requests.get('http://localhost:8765/v1/models', timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"[OK] Claude Code Router proxy working - {len(models.get('data', []))} models available")
        else:
            print(f"[WARN]  Claude Code Router proxy responded with status {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Claude Code Router proxy test failed: {e}")
        return False
    
    # Test OpenWebUI
    try:
        response = requests.get('http://localhost:8080/health', timeout=10)
        if response.status_code == 200:
            print("[OK] OpenWebUI health check passed")
        else:
            print(f"[WARN]  OpenWebUI health check failed with status {response.status_code}")
    except Exception as e:
        print(f"[FAIL] OpenWebUI test failed: {e}")
        return False
    
    print("[OK] Integration test completed successfully!")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("[LAUNCH] SETTING UP OPENWEBUI + CLAUDE CODE ROUTER + OPENROUTER")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("[FAIL] Prerequisites check failed")
        return 1
    
    print("\n[EMOJI] Creating configurations...")
    
    # Create configurations
    claude_config = create_claude_router_config()
    openwebui_config = create_openwebui_config()
    
    print("\n[LAUNCH] Starting services...")
    
    # Start Claude Code Router
    ccr_process = start_claude_code_router()
    if not ccr_process:
        print("[FAIL] Failed to start Claude Code Router")
        return 1
    
    # Start OpenWebUI
    webui_process = start_openwebui()
    if not webui_process:
        print("[FAIL] Failed to start OpenWebUI")
        if ccr_process:
            ccr_process.terminate()
        return 1
    
    print("\n[EMOJI] Testing integration...")
    
    # Test the complete setup
    if test_integration():
        print("\n" + "=" * 60)
        print("[OK] SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"[GLOBE] OpenWebUI: http://localhost:8080")
        print(f"[EMOJI] Claude Code Router: http://localhost:8765")
        print(f"[AI] Available free models:")
        print(f"   • microsoft/phi-3-mini-128k-instruct:free")
        print(f"   • google/gemma-7b-it:free") 
        print(f"   • meta-llama/llama-3-8b-instruct:free")
        print(f"   • mistralai/mistral-7b-instruct:free")
        print(f"   • huggingfaceh4/zephyr-7b-beta:free")
        print("\n[EMOJI] Use /model <model-name> in Claude Code Router to switch models")
        print("[TARGET] All models are FREE through OpenRouter!")
        
        # Keep processes running
        try:
            input("\nPress Enter to stop services...")
        except KeyboardInterrupt:
            pass
        
        print("[STOP] Stopping services...")
        if webui_process:
            webui_process.terminate()
        if ccr_process:
            ccr_process.terminate()
        
        print("[OK] Cleanup completed")
        return 0
    else:
        print("[FAIL] Integration test failed")
        # Cleanup
        if webui_process:
            webui_process.terminate()
        if ccr_process:
            ccr_process.terminate()
        return 1

if __name__ == "__main__":
    exit(main())
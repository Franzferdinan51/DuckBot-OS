#!/usr/bin/env python3
"""
Local-Only DuckBot Ecosystem Launcher
Starts DuckBot with LM Studio-only configuration, no cloud dependencies
"""

import os
import sys
import argparse
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass
    # Set console encoding
    os.system("chcp 65001 >nul 2>&1")

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Start DuckBot in local-only mode"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DuckBot Local-Only Ecosystem')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode (no WebUI, Discord bot only)')
    args = parser.parse_args()
    
    if args.headless:
        print("DuckBot Headless Local Mode")
        print("=" * 40)
        print("Privacy-First | Local Processing Only") 
        print("Discord Bot Only | No WebUI")
        print("=" * 40)
    else:
        print("DuckBot Local-Only Ecosystem Launcher")
        print("=" * 50)
        print("Privacy-First | Local Processing Only")
        print("LM Studio Required | ComfyUI Optional")
        print("=" * 50)
    
    # Set local-only environment variables
    os.environ['AI_LOCAL_ONLY_MODE'] = 'true'
    os.environ['DISABLE_OPENROUTER'] = 'true'
    os.environ['ENABLE_LM_STUDIO_ONLY'] = 'true'
    os.environ['ENABLE_DYNAMIC_LOADING'] = 'true'  # Enable dynamic model loading
    # Use LM Studio API root (must include /v1)
    os.environ['LM_STUDIO_URL'] = 'http://localhost:1234/v1'
    os.environ['DUCKBOT_WEBUI_HOST'] = '127.0.0.1'
    os.environ['DUCKBOT_WEBUI_PORT'] = '8787'
    
    # Set headless mode environment variables if requested
    if args.headless:
        os.environ['DUCKBOT_HEADLESS_MODE'] = 'true'
        os.environ['DISABLE_WEBUI'] = 'true'
        os.environ['DISABLE_COST_DASHBOARD'] = 'true'
        os.environ['DISABLE_JUPYTER'] = 'true'
        os.environ['DISABLE_N8N'] = 'true'
        os.environ['DISABLE_OPEN_NOTEBOOK'] = 'true'
        os.environ['ENABLE_DISCORD_BOT'] = 'true'
        os.environ['ENABLE_COMFYUI'] = 'true'
    
    # Verify LM Studio availability
    print("Checking LM Studio availability...")
    try:
        import requests
        response = requests.get('http://localhost:1234/v1/models', timeout=5)
        if response.status_code == 200:
            models = response.json().get('data', [])
            if models:
                print(f"[OK] LM Studio running with {len(models)} model(s)")
                print("Available for dynamic selection:")
                for i, model in enumerate(models):
                    model_id = model.get('id', 'Unknown Model')
                    print(f"   {i+1}. {model_id}")
                    if i >= 2:  # Show max 3 models to avoid clutter
                        if len(models) > 3:
                            print(f"   ... and {len(models)-3} more model(s)")
                        break
                print("DuckBot will automatically select the best model for each task")
            else:
                print("[WARNING] LM Studio running but no models loaded")
        else:
            print(f"[WARNING] LM Studio responded with status {response.status_code}")
    except Exception as e:
        print("[ERROR] LM Studio not accessible!")
        print("Please ensure:")
        print("   1. LM Studio is installed and running")
        print("   2. A chat model is loaded")
        print("   3. Local server is enabled (localhost:1234)")
        print(f"   Error: {e}")
        return False
    
    # Import and start the AI ecosystem
    try:
        from ai_ecosystem_manager import AIEcosystemManager, AIManagerConfig
        
        print("\nInitializing Local-Only AI Configuration...")
        
        # Create local-only AI configuration using existing loaded models
        ai_config = AIManagerConfig(
            provider="lm_studio",  # LM Studio only
            lm_studio_url="http://localhost:1234/v1",
            lm_studio_model="auto-detect",  # Use whatever is already loaded
            openrouter_model=None,  # Disabled
            openrouter_api_key="",  # Not needed
            auto_action_enabled=True,
            monitoring_interval=30,
            report_interval=300,
            decision_confidence_threshold=0.60  # Lower for local models
        )
        
        print("[OK] Local-only configuration created")
        print("\nStarting AI Ecosystem Manager (Local Mode)...")
        
        # Start model cleanup service
        if os.getenv('ENABLE_DYNAMIC_LOADING') == 'true':
            print("Starting model cleanup service...")
            start_model_cleanup_service()
        
        # Create and start the manager
        manager = AIEcosystemManager(ai_config)
        # Warm up LM Studio model to ensure it's loaded
        try:
            import asyncio
            print("Warming up LM Studio model (small ping)...")
            asyncio.run(manager.warm_up_lm_studio("general"))
        except Exception as e:
            print(f"[WARNING] Warm-up step failed (continuing): {e}")
        
        if args.headless:
            print("Starting in headless mode (Discord bot only)...")
        else:
            print("Starting with full WebUI...")
        
        manager.start()
        
    except ImportError as e:
        print(f"[ERROR] Could not import AI ecosystem components: {e}")
        print("Fallback: Starting basic local services...")
        start_basic_local_services(args.headless)
    except Exception as e:
        print(f"[ERROR] Failed to start AI ecosystem: {e}")
        return False
    
    return True

def start_model_cleanup_service():
    """Start background service to cleanup unused models"""
    import threading
    import time
    
    def cleanup_worker():
        """Background worker to cleanup unused models every 10 minutes"""
        try:
            from duckbot.dynamic_model_manager import DynamicModelManager
            manager = DynamicModelManager()
            
            while True:
                time.sleep(600)  # 10 minutes
                try:
                    manager.cleanup_unused_models(max_idle_minutes=15)
                    print("Model cleanup completed")
                except Exception as e:
                    print(f"Model cleanup error: {e}")
        except Exception as e:
            print(f"Model cleanup service failed: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("[OK] Model cleanup service started (runs every 10 minutes)")

def start_basic_local_services(headless=False):
    """Fallback: Start basic local services without AI management"""
    if headless:
        print("\nStarting basic headless services...")
    else:
        print("\nStarting basic local services...")
    
    # Try to start ComfyUI (always enabled for image generation)
    try:
        import subprocess
        comfyui_path = Path("ComfyUI/main.py")
        if comfyui_path.exists():
            print("Starting ComfyUI...")
            subprocess.Popen([
                sys.executable, str(comfyui_path),
                "--listen", "127.0.0.1",
                "--port", "8188",
                "--force-fp16"
            ], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            print("[OK] ComfyUI started")
        else:
            print("[WARNING] ComfyUI not found, skipping")
    except Exception as e:
        print(f"[WARNING] Could not start ComfyUI: {e}")
    
    # Try to start Discord bot directly
    try:
        print("Starting Discord bot...")
        # Import and start Discord bot directly
        import START_DUCKBOT
        print("[OK] Discord bot started")
    except Exception as e:
        print(f"[WARNING] Could not start Discord bot: {e}")
    
    # Try to start WebUI only if not headless
    if not headless:
        try:
            print("Starting WebUI...")
            from duckbot.webui import main as webui_main
            webui_main()
        except Exception as e:
            print(f"[ERROR] Could not start WebUI: {e}")
    else:
        print("WebUI disabled in headless mode")
        print("Bot running in background, Discord only")

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n[ERROR] Local ecosystem startup failed")
            sys.exit(1)
        
        # Keep running if successful
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[STOP] Local ecosystem stopped by user")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n[STOP] Local ecosystem stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

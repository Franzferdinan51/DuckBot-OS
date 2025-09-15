#!/usr/bin/env python3
"""
Quick Start Script for AI-Enhanced DuckBot Ecosystem
"""

import os
import sys
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

from ai_ecosystem_manager import AIEcosystemManager, AIManagerConfig

def main():
    # Check for local-only flag
    local_only_mode = "--local-only" in sys.argv
    
    if local_only_mode:
        try:
            print("[LOCAL] Starting LOCAL-ONLY DuckBot Ecosystem...")
        except UnicodeEncodeError:
            print("Starting LOCAL-ONLY DuckBot Ecosystem...")
    else:
        try:
            print("[AI] Starting AI-Enhanced DuckBot Ecosystem...")
        except UnicodeEncodeError:
            print("Starting AI-Enhanced DuckBot Ecosystem...")
    
    # Initialize Qwen system context
    try:
        from duckbot.ai_router_gpt import initialize_qwen_system_context
        if local_only_mode:
            print("[LOCAL] Initializing LOCAL AI system context...")
        else:
            print("[BRAIN] Initializing AI system context...")
        initialize_qwen_system_context(local_only=local_only_mode)
    except Exception as e:
        print(f"Warning: Could not initialize AI context: {e}")
    
    # Create AI configuration based on mode
    if local_only_mode:
        # Local-only configuration - LM Studio priority, no cloud services
        ai_config = AIManagerConfig(
            provider="lm_studio",  # Force LM Studio only
            lm_studio_url="http://localhost:1234/v1",
            lm_studio_model="local-model",  # Use whatever model is loaded
            openrouter_model=None,  # Disable OpenRouter
            openrouter_api_key="",  # No API key needed
            auto_action_enabled=True,
            monitoring_interval=30,
            report_interval=300,
            decision_confidence_threshold=0.60,  # Lower threshold for local models
            local_only_mode=True  # Enable local-only mode
        )
    else:
        # Standard configuration with cloud fallbacks
        ai_config = AIManagerConfig(
            provider="openrouter",  # Default to OpenRouter with free model
            lm_studio_url="http://localhost:1234/v1",  # Default LM Studio URL
            lm_studio_model="openai/gpt-oss-20b",  # Default LM Studio model
            openrouter_model="qwen/qwen3-coder:free",  # Free Qwen3 Coder model
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY', ''),
            auto_action_enabled=True,  # Enable AI to take actions automatically
            monitoring_interval=30,  # Check system every 30 seconds
            report_interval=300,  # Generate reports every 5 minutes
            decision_confidence_threshold=0.7  # Require 70% confidence for actions
        )
    
    # Override with environment variables if present
    if os.getenv('OPENROUTER_API_KEY'):
        ai_config.provider = "openrouter"
        ai_config.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        ai_config.openrouter_model = os.getenv('AI_MODEL_NAME', 'qwen/qwen3-coder:free')
    elif os.getenv('LM_STUDIO_URL') or os.getenv('LM_STUDIO_MODEL'):
        # Use LM Studio if explicitly configured
        ai_config.provider = "lm_studio"
        if os.getenv('LM_STUDIO_URL'):
            ai_config.lm_studio_url = os.getenv('LM_STUDIO_URL')
        if os.getenv('LM_STUDIO_MODEL'):
            ai_config.lm_studio_model = os.getenv('LM_STUDIO_MODEL')
    
    # Start the AI-enhanced ecosystem
    try:
        manager = AIEcosystemManager(ai_config)
        # Check if manager was created successfully
        if not hasattr(manager, 'run'):
            print("ERROR: Manager initialization failed")
            return 1
        manager.run()
    except KeyboardInterrupt:
        print("\nAI Ecosystem Manager shutting down...")
        return 0
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Try running: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print("Full error details:")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
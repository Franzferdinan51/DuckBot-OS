#!/usr/bin/env python3
"""
Quick setup script for AI provider configuration
"""

import json
import os
from pathlib import Path

def setup_lm_studio():
    """Configure for LM Studio"""
    config = {
        "provider": "lm_studio",
        "lm_studio_url": "http://localhost:1234/v1",
        "model_name": "openai/gpt-oss-20b",
        "max_tokens": 1500,
        "temperature": 0.3,
        "auto_action_enabled": True,
        "monitoring_interval": 30,
        "decision_confidence_threshold": 0.7
    }
    
    print("[EMOJI] Setting up LM Studio configuration...")
    print("[EMOJI] Model: openai/gpt-oss-20b")
    print("[GLOBE] URL: http://localhost:1234/v1")
    
    return config

def setup_openrouter():
    """Configure for OpenRouter"""
    api_key = input("Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("[FAIL] API key required for OpenRouter")
        return None
    
    print("\nChoose your model:")
    print("1. qwen/qwen3-coder:free (RECOMMENDED - Best for system management)")
    print("2. deepseek/deepseek-r1-0528:free (Good reasoning)")
    print("3. moonshotai/kimi-k2:free (General purpose)")
    print("4. z-ai/glm-4.5-air:free (Alternative)")
    
    choice = input("Enter choice (1-4): ").strip()
    
    models = {
        "1": "qwen/qwen3-coder:free",
        "2": "deepseek/deepseek-r1-0528:free", 
        "3": "moonshotai/kimi-k2:free",
        "4": "z-ai/glm-4.5-air:free"
    }
    
    model_name = models.get(choice, "qwen/qwen3-coder:free")
    
    config = {
        "provider": "openrouter",
        "openrouter_api_key": api_key,
        "openrouter_url": "https://openrouter.ai/api/v1",
        "model_name": model_name,
        "max_tokens": 1500,
        "temperature": 0.3,
        "auto_action_enabled": True,
        "monitoring_interval": 30,
        "decision_confidence_threshold": 0.7
    }
    
    print(f"☁[EMOJI] Setting up OpenRouter configuration...")
    print(f"[EMOJI] Model: {model_name}")
    
    return config

def main():
    print("[AI] AI Ecosystem Manager Setup")
    print("=" * 40)
    
    print("Choose your AI provider:")
    print("1. LM Studio (Local)")
    print("2. OpenRouter (Cloud)")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        config = setup_lm_studio()
    elif choice == "2":
        config = setup_openrouter()
    else:
        print("[FAIL] Invalid choice")
        return
    
    if not config:
        return
    
    # Add common settings
    config.update({
        "conversation_history_limit": 50,
        "report_interval": 300,
        "_setup_timestamp": "auto-generated"
    })
    
    # Save configuration
    config_file = Path("ai_config.json")
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n[OK] Configuration saved to {config_file}")
        print("\nNext steps:")
        print("1. If using LM Studio: Make sure it's running with your model loaded")
        print("2. Start the AI ecosystem: python start_ai_ecosystem.py")
        print("3. Or chat with AI: python chat_with_ai.py")
        
    except Exception as e:
        print(f"[FAIL] Failed to save configuration: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Interactive Chat Interface with AI Ecosystem Manager
"""

import asyncio
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_ecosystem_manager import AIEcosystemManager, AIManagerConfig

async def main():
    print("[AI] DuckBot AI Manager - Interactive Chat")
    print("=" * 50)
    
    # Load configuration
    try:
        with open('ai_config.json', 'r') as f:
            config_data = json.load(f)
        ai_config = AIManagerConfig(**config_data)
    except FileNotFoundError:
        print("[WARN] Using default AI configuration")
        ai_config = AIManagerConfig()
    
    # Create AI manager (without starting full ecosystem)
    manager = AIEcosystemManager(ai_config)
    
    print(f"Connected to: {ai_config.provider}")
    print(f"Model: {ai_config.model_name}")
    print("\nCommands:")
    print("  'status' - Get system status")
    print("  'config' - Show AI configuration")
    print("  'exit' - Quit chat")
    print("\nStart chatting with your AI manager!")
    print("-" * 50)
    
    try:
        while True:
            user_input = input("\n[EMOJI] You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            elif user_input.lower() == 'status':
                manager.print_enterprise_status()
                continue
            elif user_input.lower() == 'config':
                manager.print_ai_status()
                continue
            
            print("[AI] AI Manager: ", end="")
            
            # Get AI response
            try:
                response = await manager.chat_with_ai(user_input)
                print(response)
            except Exception as e:
                print(f"[FAIL] Error communicating with AI: {e}")
                print("[EMOJI] Make sure your AI service (LM Studio/OpenRouter) is running and configured correctly")
                
    except KeyboardInterrupt:
        pass
    finally:
        await manager.close_ai_session()
        print("\n[EMOJI] Chat session ended!")

if __name__ == "__main__":
    asyncio.run(main())
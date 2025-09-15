#!/usr/bin/env python3
"""
Test VibeVoice integration in Discord bot
"""
import sys
from pathlib import Path

def test_integration():
    """Test if VibeVoice is properly integrated into Discord bot."""
    
    print("Testing VibeVoice integration in Discord bot...")
    
    bot_file = Path("DuckBot-v2.3.0-Trading-Video-Enhanced.py")
    if not bot_file.exists():
        print("ERROR: Bot file not found")
        return False
    
    with open(bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for VibeVoice imports
    if "from duckbot.vibevoice_commands import setup_vibevoice_commands" in content:
        print("[OK] VibeVoice import found")
    else:
        print("[FAIL] VibeVoice import missing")
        return False
    
    # Check for VIBEVOICE_AVAILABLE variable
    if "VIBEVOICE_AVAILABLE = True" in content:
        print("[OK] VibeVoice availability flag found")
    else:
        print("[FAIL] VibeVoice availability flag missing")
        return False
    
    # Check for initialization in on_ready
    if "await setup_vibevoice_commands(bot, cost_tracker)" in content:
        print("[OK] VibeVoice initialization found in on_ready")
    else:
        print("[FAIL] VibeVoice initialization missing from on_ready")
        return False
    
    # Check for updated startup messages
    if "VibeVoice Multi-Speaker TTS Integration" in content:
        print("[OK] Updated startup messages found")
    else:
        print("[FAIL] Startup messages not updated")
        return False
    
    print("\n[OK] VibeVoice integration test PASSED!")
    print("The Discord bot is ready with VibeVoice TTS commands:")
    print("  /vibevoice - Generate multi-speaker voice content")
    print("  /voice_presets - Show available voices")
    print("  /voice_status - Check VibeVoice server status")
    print("  /voice_help - Complete usage guide")
    
    return True

if __name__ == "__main__":
    success = test_integration()
    if not success:
        sys.exit(1)
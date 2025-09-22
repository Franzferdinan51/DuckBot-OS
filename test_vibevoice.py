#!/usr/bin/env python3
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

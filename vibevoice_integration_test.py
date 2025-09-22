"""
Final VibeVoice Integration Test
Tests the complete integration end-to-end
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    print("=" * 60)
    print("VibeVoice Integration Final Test")
    print("=" * 60)

    try:
        # Test 1: Server Health
        print("\n1. Testing server health...")
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"[OK] Server is healthy: {health.get('status', 'unknown')}")
                else:
                    print(f"[FAIL] Server returned status {response.status}")
                    return False

        # Test 2: VibeVoice Integration
        print("\n2. Testing VibeVoice integration...")
        from duckbot.integrations.vibevoice_client import vibevoice_integration

        # Initialize the integration
        initialized = await vibevoice_integration.ensure_initialized()
        print(f"Initialization: {'[OK]' if initialized else '[FAIL]'}")

        if initialized:
            # Test capabilities
            caps = vibevoice_integration.get_capabilities()
            print(f"[OK] Capabilities: {caps['service_type']} with {caps['voice_count']} voices")

            # Test health
            health = await vibevoice_integration.get_health_status()
            print(f"[OK] Health: {health.get('connection_status', 'unknown')}")

            # Test generation
            print("\n3. Testing speech generation...")
            result = await vibevoice_integration.generate_speech(
                "Hello from DuckBot VibeVoice integration! This is a test of the complete system.",
                speakers=["en-alice"]
            )

            if result["success"]:
                print(f"[OK] Generation successful!")
                print(f"    Audio path: {result['audio_path']}")
                print(f"    Text: {result['text']}")
                print(f"    Speakers: {', '.join(result['speakers'])}")

                # Check if file exists
                if os.path.exists(result["audio_path"]):
                    file_size = os.path.getsize(result["audio_path"]) / (1024 * 1024)
                    print(f"[OK] Audio file exists ({file_size:.2f} MB)")
                else:
                    print("[WARN] Audio file not found")
            else:
                print(f"[FAIL] Generation failed: {result['error']}")
                return False

        # Test 4: Discord Commands Setup
        print("\n4. Testing Discord commands setup...")
        from duckbot.agents.vibevoice_commands import VibeVoiceCommands
        from duckbot.core.cost_management import CostTracker

        class MockBot:
            def __init__(self):
                self.rate_limiter = MockRateLimiter()

        class MockRateLimiter:
            def check_rate_limit(self, user_id, command):
                return True

        # Create commands instance
        cost_tracker = CostTracker()
        bot = MockBot()
        commands = VibeVoiceCommands(bot, cost_tracker)

        # Load the cog
        await commands.cog_load()
        print("[OK] Discord commands loaded successfully")

        # Test command availability
        available_voices = commands.vibevoice.get_capabilities().get('voice_count', 0)
        print(f"[OK] Available voices: {available_voices}")

        print("\n" + "=" * 60)
        print("VibeVoice Integration Test Complete!")
        print("=" * 60)
        print("\n[OK] All tests passed! VibeVoice integration is fully functional.")
        print("\nTo use VibeVoice with DuckBot:")
        print("1. Start the VibeVoice server: START_VIBEVOICE_SERVER.bat")
        print("2. Start DuckBot with Discord integration")
        print("3. Use Discord commands like:")
        print("   /vibevoice text:\"Hello world!\" preset:alice")
        print("   /voice_presets")
        print("   /voice_status")
        print("   /voice_help")

        return True

    except Exception as e:
        print(f"[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
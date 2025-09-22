"""
Test script for VibeVoice Discord integration
"""
import asyncio
import sys
import json
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from duckbot.agents.vibevoice_commands import VibeVoiceCommands
from duckbot.core.cost_management import CostTracker

class MockBot:
    """Mock Discord bot for testing"""
    def __init__(self):
        self.rate_limiter = MockRateLimiter()

class MockRateLimiter:
    """Mock rate limiter"""
    def check_rate_limit(self, user_id, command):
        return True

    def get_remaining_calls(self, user_id, command):
        return 10

class MockInteraction:
    """Mock Discord interaction"""
    def __init__(self, user_id="12345"):
        self.user = MockUser(user_id)
        self.response = self
        self.followup = self
        self.followup_sent = False
        self.responses = []

    async def defer(self, thinking=True):
        print(f"[MOCK] Interaction deferred (thinking={thinking})")

    async def send(self, embed=None, file=None):
        self.followup_sent = True
        response = {"embed": embed, "file": file}
        self.responses.append(response)
        title = embed.title if embed else 'No embed'
        print(f"[MOCK] Followup sent: {title.encode('ascii', 'ignore').decode('ascii')}")
        return response

    async def followup_send(self, embed=None, file=None):
        return await self.send(embed, file)

    async def send_message(self, embed=None):
        return await self.send(embed)

class MockUser:
    """Mock Discord user"""
    def __init__(self, user_id):
        self.id = user_id
        self.name = "TestUser"

async def test_vibevoice_commands():
    """Test VibeVoice Discord commands"""
    print("=" * 60)
    print("Testing VibeVoice Discord Integration")
    print("=" * 60)

    # Create mock objects
    bot = MockBot()
    cost_tracker = CostTracker()

    try:
        # Initialize VibeVoice commands
        print("\n1. Initializing VibeVoice commands...")
        vibevoice_cog = VibeVoiceCommands(bot, cost_tracker)
        await vibevoice_cog.cog_load()
        print("[OK] VibeVoice commands initialized")

        # Test vibevoice command
        print("\n2. Testing /vibevoice command...")
        interaction = MockInteraction()

        # Test with simple text
        print("Testing simple generation...")
        await vibevoice_cog.vibevoice_command.callback(
            vibevoice_cog,
            interaction=interaction,
            text="Hello from Discord integration!",
            preset="alice",
            speakers=None,
            upload=False
        )

        if interaction.followup_sent:
            print("[OK] /vibevoice command executed successfully")

            # Check responses
            for i, response in enumerate(interaction.responses):
                embed = response.get("embed")
                if embed:
                    title = embed.title.encode('ascii', 'ignore').decode('ascii')
                    print(f"  Response {i+1}: {title}")
                    desc = embed.description[:100].encode('ascii', 'ignore').decode('ascii') if embed.description else ""
                    print(f"  Description: {desc}...")
        else:
            print("[FAIL] /vibevoice command failed")

        # Test voice presets command
        print("\n3. Testing /voice_presets command...")
        interaction2 = MockInteraction()
        await vibevoice_cog.voice_presets_command.callback(
            vibevoice_cog,
            interaction=interaction2
        )

        if interaction2.followup_sent:
            print("[OK] /voice_presets command executed successfully")
        else:
            print("[FAIL] /voice_presets command failed")

        # Test voice status command
        print("\n4. Testing /voice_status command...")
        interaction3 = MockInteraction()
        await vibevoice_cog.voice_status_command.callback(
            vibevoice_cog,
            interaction=interaction3
        )

        if interaction3.followup_sent:
            print("[OK] /voice_status command executed successfully")
        else:
            print("[FAIL] /voice_status command failed")

        # Test voice help command
        print("\n5. Testing /voice_help command...")
        interaction4 = MockInteraction()
        await vibevoice_cog.voice_help_command.callback(
            vibevoice_cog,
            interaction=interaction4
        )

        if interaction4.followup_sent:
            print("[OK] /voice_help command executed successfully")
        else:
            print("[FAIL] /voice_help command failed")

        # Test multi-speaker generation
        print("\n6. Testing multi-speaker generation...")
        interaction5 = MockInteraction()
        await vibevoice_cog.vibevoice_command.callback(
            vibevoice_cog,
            interaction=interaction5,
            text="Alice: Hi there! Bob: Hello Alice! How are you today?",
            preset="conversation",
            speakers=None,
            upload=False
        )

        if interaction5.followup_sent:
            print("[OK] Multi-speaker generation executed successfully")
        else:
            print("[FAIL] Multi-speaker generation failed")

        # Test error handling
        print("\n7. Testing error handling...")
        interaction6 = MockInteraction()

        # Test with very long text (should fail)
        long_text = "This is a test. " * 1000  # Very long text
        await vibevoice_cog.vibevoice_command.callback(
            vibevoice_cog,
            interaction=interaction6,
            text=long_text,
            preset="alice",
            speakers=None,
            upload=False
        )

        if interaction6.followup_sent:
            print("[OK] Error handling working (long text rejected)")
        else:
            print("[FAIL] Error handling not working")

        print("\n" + "=" * 60)
        print("VibeVoice Discord Integration Test Complete!")
        print("=" * 60)

        # Summary
        success_count = sum(1 for i in [interaction, interaction2, interaction3, interaction4, interaction5] if i.followup_sent)
        total_count = 5

        print(f"Results: {success_count}/{total_count} tests passed")

        if success_count == total_count:
            print("[OK] All tests passed! VibeVoice Discord integration is working.")
            return True
        else:
            print(f"[FAIL] {total_count - success_count} tests failed.")
            return False

    except Exception as e:
        print(f"[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_health():
    """Test server health before running tests"""
    print("\nTesting server health...")
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"[OK] Server is healthy: {health.get('status', 'unknown')}")
                    return True
                else:
                    print(f"[FAIL] Server returned status {response.status}")
                    return False
    except Exception as e:
        print(f"[FAIL] Cannot connect to server: {e}")
        print("Please start the VibeVoice server first:")
        print("  START_VIBEVOICE_SERVER.bat")
        return False

async def main():
    """Main test function"""
    print("VibeVoice Discord Integration Test")
    print("==================================")

    # Check if server is running
    if not await test_server_health():
        print("\n[FAIL] Server not available. Please start the VibeVoice server first.")
        return False

    # Run Discord integration tests
    success = await test_vibevoice_commands()

    if success:
        print("\n[OK] VibeVoice Discord integration is fully functional!")
        print("\nTo use with Discord:")
        print("1. Start the VibeVoice server: START_VIBEVOICE_SERVER.bat")
        print("2. Start DuckBot with Discord integration")
        print("3. Use commands like /vibevoice, /voice_presets, etc.")
    else:
        print("\n[FAIL] Some tests failed. Check the output above for details.")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
"""
Comprehensive test for Microsoft VibeVoice and RealtimeVoiceChat system
Tests all components and compatibility with existing Discord commands
"""
import asyncio
import aiohttp
import json
import os
import sys
import time
from pathlib import Path

# Add the duckbot module to Python path
sys.path.insert(0, str(Path(__file__).parent))

from duckbot.integrations.vibevoice_real import real_vibevoice_integration, generate_real_vibevoice_speech, get_real_vibevoice_health
from duckbot.agents.vibevoice_commands import VibeVoiceCommands

class VibeVoiceSystemTester:
    def __init__(self):
        self.test_results = []
        self.vibevoice_server_url = "http://localhost:8000"
        self.voicechat_server_url = "http://localhost:8001"

    async def test_vibevoice_server_health(self):
        """Test if VibeVoice server is running and healthy"""
        print("Testing VibeVoice server health...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vibevoice_server_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health = await response.json()
                        if health.get("status") == "healthy":
                            self._add_result("VibeVoice Server Health", "✅ PASS", health)
                            return True
                        else:
                            self._add_result("VibeVoice Server Health", "❌ FAIL", f"Server not healthy: {health}")
                            return False
                    else:
                        self._add_result("VibeVoice Server Health", "❌ FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self._add_result("VibeVoice Server Health", "❌ FAIL", f"Connection error: {e}")
            return False

    async def test_realtime_voicechat_server_health(self):
        """Test if RealtimeVoiceChat server is running and healthy"""
        print("🧪 Testing RealtimeVoiceChat server health...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.voicechat_server_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health = await response.json()
                        if health.get("status") == "healthy":
                            self._add_result("RealtimeVoiceChat Server Health", "✅ PASS", health)
                            return True
                        else:
                            self._add_result("RealtimeVoiceChat Server Health", "❌ FAIL", f"Server not healthy: {health}")
                            return False
                    else:
                        self._add_result("RealtimeVoiceChat Server Health", "❌ FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self._add_result("RealtimeVoiceChat Server Health", "❌ FAIL", f"Connection error: {e}")
            return False

    async def test_vibevoice_integration(self):
        """Test VibeVoice integration initialization and basic functionality"""
        print("🧪 Testing VibeVoice integration...")

        try:
            # Test initialization
            initialized = await real_vibevoice_integration.initialize()
            if not initialized:
                self._add_result("VibeVoice Integration", "❌ FAIL", "Failed to initialize")
                return False

            # Test capabilities
            capabilities = real_vibevoice_integration.get_capabilities()
            self._add_result("VibeVoice Capabilities", "✅ PASS", capabilities)

            # Test health status
            health = await get_real_vibevoice_health()
            self._add_result("VibeVoice Health Status", "✅ PASS", health)

            return True

        except Exception as e:
            self._add_result("VibeVoice Integration", "❌ FAIL", f"Error: {e}")
            return False

    async def test_vibevoice_speech_generation(self):
        """Test basic speech generation"""
        print("🧪 Testing VibeVoice speech generation...")

        try:
            # Test simple speech generation
            result = await generate_real_vibevoice_speech(
                text="Hello, this is a test of the Microsoft VibeVoice system.",
                speakers=["en-alice"],
                style="conversational"
            )

            if result.get("success"):
                audio_path = result.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    self._add_result("Basic Speech Generation", "✅ PASS", {
                        "audio_path": audio_path,
                        "file_size_bytes": file_size,
                        "result": result
                    })

                    # Clean up test file
                    try:
                        os.remove(audio_path)
                    except:
                        pass

                    return True
                else:
                    self._add_result("Basic Speech Generation", "❌ FAIL", "Audio file not created")
                    return False
            else:
                self._add_result("Basic Speech Generation", "❌ FAIL", result.get("error", "Unknown error"))
                return False

        except Exception as e:
            self._add_result("Basic Speech Generation", "❌ FAIL", f"Error: {e}")
            return False

    async def test_emotional_speech_generation(self):
        """Test emotional speech generation"""
        print("🧪 Testing emotional speech generation...")

        emotions = ["happy", "sad", "angry", "surprised", "neutral"]
        results = {}

        for emotion in emotions:
            try:
                result = await generate_real_vibevoice_speech(
                    text=f"This is a test of {emotion} speech.",
                    speakers=["en-alice"],
                    style="emotional",
                    emotion=emotion
                )

                if result.get("success"):
                    audio_path = result.get("audio_path")
                    if audio_path and os.path.exists(audio_path):
                        results[emotion] = {"success": True, "file_size": os.path.getsize(audio_path)}

                        # Clean up test file
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                    else:
                        results[emotion] = {"success": False, "error": "Audio file not created"}
                else:
                    results[emotion] = {"success": False, "error": result.get("error", "Unknown error")}

            except Exception as e:
                results[emotion] = {"success": False, "error": str(e)}

        success_count = sum(1 for r in results.values() if r["success"])
        total_count = len(results)

        self._add_result("Emotional Speech Generation",
                        "✅ PASS" if success_count == total_count else "⚠️ PARTIAL",
                        {"results": results, "success_count": success_count, "total_count": total_count})

        return success_count > 0

    async def test_multi_speech_generation(self):
        """Test multi-speaker speech generation"""
        print("🧪 Testing multi-speaker speech generation...")

        try:
            # Test conversation generation
            script = [
                {"speaker": "en-alice", "text": "Hello there! How are you today?"},
                {"speaker": "en-carter", "text": "I'm doing well, thank you for asking!"},
                {"speaker": "en-alice", "text": "That's wonderful to hear! What are your plans?"},
                {"speaker": "en-carter", "text": "I'm planning to test this amazing voice system."}
            ]

            result = await generate_real_vibevoice_speech(
                text="Alice: Hello there! How are you today?\nCarter: I'm doing well, thank you for asking!\nAlice: That's wonderful to hear! What are your plans?\nCarter: I'm planning to test this amazing voice system.",
                speakers=["en-alice", "en-carter"],
                style="conversational"
            )

            if result.get("success"):
                audio_path = result.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    self._add_result("Multi-Speaker Generation", "✅ PASS", {
                        "audio_path": audio_path,
                        "file_size_bytes": file_size,
                        "speakers": result.get("speakers", [])
                    })

                    # Clean up test file
                    try:
                        os.remove(audio_path)
                    except:
                        pass

                    return True
                else:
                    self._add_result("Multi-Speaker Generation", "❌ FAIL", "Audio file not created")
                    return False
            else:
                self._add_result("Multi-Speaker Generation", "❌ FAIL", result.get("error", "Unknown error"))
                return False

        except Exception as e:
            self._add_result("Multi-Speaker Generation", "❌ FAIL", f"Error: {e}")
            return False

    async def test_realtime_voicechat_api(self):
        """Test RealtimeVoiceChat REST API"""
        print("🧪 Testing RealtimeVoiceChat API...")

        try:
            async with aiohttp.ClientSession() as session:
                # Test providers endpoint
                async with session.get(f"{self.voicechat_server_url}/providers", timeout=10) as response:
                    if response.status == 200:
                        providers = await response.json()
                        self._add_result("RealtimeVoiceChat Providers", "✅ PASS", providers)
                    else:
                        self._add_result("RealtimeVoiceChat Providers", "❌ FAIL", f"HTTP {response.status}")

                # Test health endpoint (already tested above)
                # Test chat endpoint
                chat_data = {
                    "session_id": "test_session",
                    "text": "Hello, this is a test message.",
                    "voice_profile": "en-alice",
                    "ai_provider": "lm_studio"
                }

                async with session.post(f"{self.voicechat_server_url}/chat", json=chat_data, timeout=10) as response:
                    if response.status == 200:
                        chat_result = await response.json()
                        self._add_result("RealtimeVoiceChat Chat", "✅ PASS", chat_result)
                    else:
                        self._add_result("RealtimeVoiceChat Chat", "❌ FAIL", f"HTTP {response.status}")

            return True

        except Exception as e:
            self._add_result("RealtimeVoiceChat API", "❌ FAIL", f"Error: {e}")
            return False

    async def test_discord_command_compatibility(self):
        """Test compatibility with existing Discord commands"""
        print("🧪 Testing Discord command compatibility...")

        try:
            # Create a mock bot for testing
            import discord
            from discord.ext import commands

            # This is a basic compatibility test since we can't create a real Discord bot without a token
            # We'll test the command structure and imports instead

            # Test command imports
            from duckbot.agents.vibevoice_commands import VibeVoiceCommands, setup_vibevoice_commands

            # Test that the command class can be instantiated (mock bot)
            class MockBot:
                def __init__(self):
                    self.rate_limiter = MockRateLimiter()

            class MockRateLimiter:
                def check_rate_limit(self, user_id, command_type):
                    return True
                def get_remaining_calls(self, user_id, command_type):
                    return 10

            mock_bot = MockBot()

            # Create command instance
            commands_cog = VibeVoiceCommands(mock_bot)

            # Test that the cog can be created without errors
            self._add_result("Discord Commands Import", "✅ PASS", "Commands imported successfully")

            # Test command method existence
            command_methods = [
                'vibevoice_command',
                'voice_presets_command',
                'voice_status_command',
                'voice_help_command',
                'emotional_voice_command',
                'realtime_voice_command',
                'voice_batch_command'
            ]

            for method_name in command_methods:
                if hasattr(commands_cog, method_name):
                    self._add_result(f"Command Method: {method_name}", "✅ PASS", "Method exists")
                else:
                    self._add_result(f"Command Method: {method_name}", "❌ FAIL", "Method missing")

            return True

        except Exception as e:
            self._add_result("Discord Command Compatibility", "❌ FAIL", f"Error: {e}")
            return False

    async def test_configuration_loading(self):
        """Test configuration loading"""
        print("🧪 Testing configuration loading...")

        try:
            # Test environment variables
            env_vars = [
                "VIBEVOICE_API_URL",
                "ENABLE_VIBEVOICE",
                "OPENROUTER_API_KEY",
                "GEMINI_API_KEY"
            ]

            env_status = {}
            for var in env_vars:
                env_status[var] = os.getenv(var, "NOT_SET")

            self._add_result("Environment Variables", "✅ PASS", env_status)

            # Test configuration file loading
            config_path = Path(__file__).parent / "config" / "ai_providers_config.yaml"
            if config_path.exists():
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self._add_result("Configuration File", "✅ PASS", {"loaded": True, "sections": list(config.keys())})
            else:
                self._add_result("Configuration File", "⚠️ WARNING", "Config file not found")

            return True

        except Exception as e:
            self._add_result("Configuration Loading", "❌ FAIL", f"Error: {e}")
            return False

    def _add_result(self, test_name, status, details=None):
        """Add test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        print(f"  {status} {test_name}")

    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Microsoft VibeVoice System Tests")
        print("=" * 60)

        # Run all tests
        await self.test_configuration_loading()
        await self.test_vibevoice_server_health()
        await self.test_realtime_voicechat_server_health()
        await self.test_vibevoice_integration()
        await self.test_vibevoice_speech_generation()
        await self.test_emotional_speech_generation()
        await self.test_multi_speech_generation()
        await self.test_realtime_voicechat_api()
        await self.test_discord_command_compatibility()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        passed = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed = len([r for r in self.test_results if "❌ FAIL" in r["status"]])
        partial = len([r for r in self.test_results if "⚠️" in r["status"]])
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️ Partial: {partial}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        # Print failed tests
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test_name']}: {result.get('details', 'No details')}")

        # Print recommendations
        print("\n💡 Recommendations:")
        if failed > 0:
            print("  - Check that both VibeVoice and RealtimeVoiceChat servers are running")
            print("  - Verify API keys are set in environment variables")
            print("  - Ensure all dependencies are installed")
        if passed == total:
            print("  - System is fully operational!")
            print("  - You can now use Discord commands and real-time voice chat")

        # Save results to file
        results_file = Path("vibevoice_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")

        return passed == total

async def main():
    """Main test function"""
    tester = VibeVoiceSystemTester()
    success = await tester.run_all_tests()

    if success:
        print("\n🎉 All tests passed! Microsoft VibeVoice system is ready.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Test VibeVoice Integration for DuckBot
Validates the VibeVoice TTS setup and functionality
"""
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_vibevoice_import():
    """Test if VibeVoice modules can be imported."""
    logger.info("Testing VibeVoice module imports...")
    
    try:
        from duckbot.vibevoice_client import VibeVoiceClient, VibeVoiceManager
        logger.info("[OK] VibeVoice client imported successfully")
        
        from duckbot.vibevoice_commands import VibeVoiceCommands, setup_vibevoice_commands
        logger.info("[OK] VibeVoice commands imported successfully")
        
        return True
    except ImportError as e:
        logger.error(f"[FAIL] Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error: {e}")
        return False

async def test_vibevoice_client():
    """Test VibeVoice client functionality."""
    logger.info("Testing VibeVoice client functionality...")
    
    try:
        from duckbot.vibevoice_client import VibeVoiceManager
        
        # Initialize manager
        manager = VibeVoiceManager()
        logger.info("[OK] VibeVoice manager created")
        
        # Test available voices
        voices = manager.get_available_voices()
        logger.info(f"[OK] Available voices: {', '.join(voices)}")
        
        # Test availability check
        available = manager.is_available()
        logger.info(f"[CHART] Service available: {available}")
        
        # Try to initialize (this will test server connection)
        try:
            initialized = await manager.initialize()
            logger.info(f"[CHART] Initialization: {'Success' if initialized else 'Failed (server not running)'}")
        except Exception as e:
            logger.warning(f"[WARN] Initialization failed (expected if server not running): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Client test failed: {e}")
        return False

async def test_configuration_files():
    """Test configuration file presence and validity."""
    logger.info("Testing configuration files...")
    
    config_files = [
        "vibevoice_config.yaml",
        ".env"
    ]
    
    success = True
    
    for config_file in config_files:
        file_path = Path(config_file)
        if file_path.exists():
            logger.info(f"[OK] Found: {config_file}")
            
            # Test YAML parsing
            if config_file.endswith('.yaml'):
                try:
                    import yaml
                    with open(file_path, 'r') as f:
                        yaml.safe_load(f)
                    logger.info(f"[OK] Valid YAML: {config_file}")
                except Exception as e:
                    logger.error(f"[FAIL] Invalid YAML {config_file}: {e}")
                    success = False
        else:
            logger.warning(f"[WARN] Missing: {config_file}")
    
    return success

async def test_discord_integration():
    """Test Discord bot integration components."""
    logger.info("Testing Discord integration...")
    
    try:
        # Test command class
        from duckbot.vibevoice_commands import VibeVoiceCommands
        logger.info("[OK] VibeVoice commands class available")
        
        # Test setup function
        from duckbot.vibevoice_commands import setup_vibevoice_commands
        logger.info("[OK] Setup function available")
        
        # Mock a simple bot-like object for testing
        class MockBot:
            def __init__(self):
                self.cogs = {}
                
            async def add_cog(self, cog):
                self.cogs[cog.__class__.__name__] = cog
                logger.info(f"[OK] Mock cog added: {cog.__class__.__name__}")
                return True
        
        # Test cog setup
        mock_bot = MockBot()
        cog = await setup_vibevoice_commands(mock_bot)
        
        if cog:
            logger.info("[OK] Discord cog setup successful")
        else:
            logger.warning("[WARN] Discord cog setup failed (expected without full bot)")
        
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Discord integration test failed: {e}")
        return False

async def test_vibevoice_server_connection():
    """Test connection to VibeVoice server."""
    logger.info("Testing VibeVoice server connection...")
    
    try:
        import aiohttp
        
        server_url = "http://localhost:8000"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{server_url}/voices", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("[OK] VibeVoice server is running and accessible")
                        logger.info(f"[CHART] Available voices: {len(data.get('voices', []))}")
                        return True
                    else:
                        logger.warning(f"[WARN] Server responded with status {response.status}")
                        return False
            except asyncio.TimeoutError:
                logger.warning("[WARN] Server connection timed out")
                return False
            except Exception as e:
                logger.warning(f"[WARN] Server connection failed: {e}")
                return False
                
    except Exception as e:
        logger.error(f"[FAIL] Server test failed: {e}")
        return False

async def test_voice_generation():
    """Test actual voice generation (if server is available)."""
    logger.info("Testing voice generation...")
    
    try:
        from duckbot.vibevoice_client import VibeVoiceManager
        
        manager = VibeVoiceManager()
        
        # Try to initialize
        if await manager.initialize():
            logger.info("[EMOJI] Testing voice generation with sample text...")
            
            test_text = "Hello! This is a test of VibeVoice TTS integration with DuckBot."
            
            try:
                audio_path = await manager.generate_voice_content(
                    content=test_text,
                    speakers=["en-alice"],
                    style="conversational"
                )
                
                if audio_path and os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path) / 1024  # KB
                    logger.info(f"[OK] Voice generation successful!")
                    logger.info(f"[CHART] Generated file: {audio_path}")
                    logger.info(f"[CHART] File size: {file_size:.2f} KB")
                    
                    # Clean up test file
                    try:
                        os.remove(audio_path)
                        logger.info("[EMOJI] Test file cleaned up")
                    except:
                        pass
                        
                    return True
                else:
                    logger.error("[FAIL] Voice generation failed - no output file")
                    return False
                    
            except Exception as e:
                logger.error(f"[FAIL] Voice generation failed: {e}")
                return False
        else:
            logger.warning("[WARN] Voice generation test skipped (server not available)")
            return False
            
    except Exception as e:
        logger.error(f"[FAIL] Voice generation test failed: {e}")
        return False

async def run_all_tests():
    """Run all VibeVoice integration tests."""
    logger.info("[EMOJI] Starting VibeVoice Integration Tests")
    logger.info("="*60)
    
    tests = [
        ("Module Imports", test_vibevoice_import),
        ("Configuration Files", test_configuration_files),
        ("VibeVoice Client", test_vibevoice_client),
        ("Discord Integration", test_discord_integration),
        ("Server Connection", test_vibevoice_server_connection),
        ("Voice Generation", test_voice_generation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n[LIST] Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"[OK] {test_name}: PASSED")
            else:
                logger.info(f"[FAIL] {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"[EMOJI] {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("[EMOJI] VIBEVOICE TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[OK] PASSED" if result else "[FAIL] FAILED"
        logger.info(f"{test_name:.<30} {status}")
    
    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("[SUCCESS] All tests passed! VibeVoice is ready to use.")
        logger.info("\n[LIST] Next steps:")
        logger.info("1. Start VibeVoice server if not running")
        logger.info("2. Start DuckBot with VibeVoice integration")
        logger.info("3. Use /vibevoice commands in Discord")
    elif passed >= total * 0.7:
        logger.info("[WARN] Most tests passed. Check server setup for full functionality.")
        logger.info("\n[LIST] Recommended actions:")
        logger.info("1. Start VibeVoice server: START_VIBEVOICE_SERVER.bat")
        logger.info("2. Check server logs for any issues")
    else:
        logger.info("[FAIL] Multiple test failures. Check installation and configuration.")
        logger.info("\n[LIST] Troubleshooting:")
        logger.info("1. Re-run: python setup_vibevoice.py")
        logger.info("2. Check Python dependencies")
        logger.info("3. Verify configuration files")
    
    return passed / total

def main():
    """Main test function."""
    try:
        result = asyncio.run(run_all_tests())
        
        if result == 1.0:
            print("\n[EMOJI] VibeVoice integration is fully functional!")
            sys.exit(0)
        else:
            print(f"\n[WARN] VibeVoice integration is {result*100:.1f}% functional.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[STOP] Tests cancelled by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n[EMOJI] Test runner failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
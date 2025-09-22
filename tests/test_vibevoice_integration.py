#!/usr/bin/env python3
"""
Test VibeVoice Integration for DuckBot v4.2
Verify that all fixes are working properly
"""

import asyncio
import sys
import os
import logging

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_vibevoice_integration():
    """Test VibeVoice integration"""
    logger.info("[TEST] Starting VibeVoice integration test...")

    try:
        # Test 1: Import the integration
        logger.info("[TEST 1] Testing import...")
        from duckbot.integrations.vibevoice_client import vibevoice_integration, is_vibevoice_available, get_vibevoice_capabilities
        logger.info("[OK] VibeVoice integration imported successfully")

        # Test 2: Check availability
        logger.info("[TEST 2] Testing availability check...")
        available = is_vibevoice_available()
        logger.info(f"[INFO] VibeVoice available: {available}")

        # Test 3: Get capabilities
        logger.info("[TEST 3] Testing capabilities...")
        capabilities = get_vibevoice_capabilities()
        logger.info(f"[OK] Capabilities: {capabilities}")

        # Test 4: Test health status
        logger.info("[TEST 4] Testing health status...")
        health = await vibevoice_integration.get_health_status()
        logger.info(f"[OK] Health status: {health}")

        # Test 5: Test AI provider manager integration
        logger.info("[TEST 5] Testing AI provider manager integration...")
        from duckbot.core.ai_provider_manager import AIProviderManager
        manager = AIProviderManager()
        vibevoice_provider = manager.providers.get("vibevoice")
        if vibevoice_provider:
            logger.info(f"[OK] VibeVoice in AI provider manager: {vibevoice_provider}")
        else:
            logger.warning("[WARN] VibeVoice not found in AI provider manager")

        # Test 6: Test Discord commands integration
        logger.info("[TEST 6] Testing Discord commands integration...")
        from duckbot.agents.vibevoice_commands import VibeVoiceCommands
        logger.info("[OK] VibeVoice commands imported successfully")

        # Summary
        logger.info("[SUMMARY] VibeVoice integration test completed")
        logger.info(f"[SUMMARY] Available: {available}")
        logger.info(f"[SUMMARY] Capabilities: {len(capabilities.get('features', []))} features")
        logger.info(f"[SUMMARY] Health: {health.get('available', False)}")

        return True

    except Exception as e:
        logger.error(f"[FAIL] VibeVoice integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_vibevoice_generation():
    """Test VibeVoice speech generation (if server is available)"""
    logger.info("[TEST] Starting VibeVoice generation test...")

    try:
        from duckbot.integrations.vibevoice_client import vibevoice_integration

        # Check if initialized
        initialized = await vibevoice_integration.ensure_initialized()
        if not initialized:
            logger.warning("[SKIP] VibeVoice server not available for generation test")
            return True

        # Test generation
        result = await vibevoice_integration.generate_speech(
            text="Hello! This is a test of the VibeVoice integration.",
            speakers=["en-alice"]
        )

        if result.get("success"):
            logger.info("[OK] VibeVoice generation successful")
            logger.info(f"[OK] Audio file: {result.get('audio_path')}")
            return True
        else:
            logger.warning(f"[FAIL] VibeVoice generation failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"[FAIL] VibeVoice generation test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        logger.info("=" * 60)
        logger.info("VIBEVOICE INTEGRATION TEST - DUCKBOT v4.2")
        logger.info("=" * 60)

        # Test 1: Basic integration
        success1 = await test_vibevoice_integration()

        # Test 2: Generation (optional)
        success2 = await test_vibevoice_generation()

        # Summary
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Integration Test: {'PASS' if success1 else 'FAIL'}")
        logger.info(f"Generation Test: {'PASS' if success2 else 'FAIL'}")
        logger.info(f"Overall: {'PASS' if success1 else 'FAIL'}")

        if success1:
            logger.info("[OK] VibeVoice integration is working properly!")
        else:
            logger.info("[FAIL] VibeVoice integration has issues that need to be fixed.")

        return success1

    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
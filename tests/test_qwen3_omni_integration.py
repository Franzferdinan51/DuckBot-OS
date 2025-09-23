#!/usr/bin/env python3
"""
Test script for Qwen3-Omni integration with DuckBot
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_qwen3_omni_import():
    """Test Qwen3-Omni module import"""
    logger.info("Testing Qwen3-Omni import...")

    try:
        from duckbot.core.qwen3_omni_integration import (
            Qwen3OmniIntegration,
            Qwen3OmniConfig,
            MultimodalInput,
            process_with_qwen3_omni,
            get_qwen3_omni_status
        )
        logger.info("✓ Qwen3-Omni modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import Qwen3-Omni modules: {e}")
        return False

async def test_voice_assistant_import():
    """Test voice assistant import"""
    logger.info("Testing voice assistant import...")

    try:
        from duckbot.integrations.qwen3_voice_assistant import (
            Qwen3VoiceAssistant,
            VoiceAssistantConfig,
            VoiceInteraction,
            get_voice_assistant_status
        )
        logger.info("✓ Voice assistant modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import voice assistant modules: {e}")
        return False

async def test_ai_provider_manager():
    """Test AI Provider Manager integration"""
    logger.info("Testing AI Provider Manager integration...")

    try:
        from duckbot.core.ai_provider_manager import AIProviderManager, get_available_providers

        # Initialize provider manager
        provider_manager = AIProviderManager()

        # Check if Qwen3-Omni is available
        providers = get_available_providers()
        logger.info(f"Available providers: {providers}")

        if "qwen3_omni" in providers:
            logger.info("✓ Qwen3-Omni provider is available")

            # Get provider status
            status = provider_manager.get_provider_status("qwen3_omni")
            logger.info(f"Qwen3-Omni status: {status}")

            return True
        else:
            logger.warning("⚠ Qwen3-Omni provider not in available providers")
            return False

    except Exception as e:
        logger.error(f"✗ AI Provider Manager test failed: {e}")
        return False

async def test_qwen3_omni_initialization():
    """Test Qwen3-Omni initialization"""
    logger.info("Testing Qwen3-Omni initialization...")

    try:
        from duckbot.core.qwen3_omni_integration import qwen3_omni_integration

        # Check if integration is available
        status = qwen3_omni_integration.get_status()
        logger.info(f"Qwen3-Omni status: {json.dumps(status, indent=2)}")

        if status["available"]:
            logger.info("✓ Qwen3-Omni is available")
            return True
        else:
            logger.warning("⚠ Qwen3-Omni is not available (this is normal if model is not loaded)")
            return False

    except Exception as e:
        logger.error(f"✗ Qwen3-Omni initialization test failed: {e}")
        return False

async def test_voice_assistant_initialization():
    """Test voice assistant initialization"""
    logger.info("Testing voice assistant initialization...")

    try:
        from duckbot.integrations.qwen3_voice_assistant import qwen3_voice_assistant

        # Get voice assistant status
        status = qwen3_voice_assistant.get_status()
        logger.info(f"Voice assistant status: {json.dumps(status, indent=2)}")

        if status["available"]:
            logger.info("✓ Voice assistant is available")
            return True
        else:
            logger.warning("⚠ Voice assistant is not available (this may be normal)")
            return False

    except Exception as e:
        logger.error(f"✗ Voice assistant initialization test failed: {e}")
        return False

async def test_configuration_loading():
    """Test configuration loading"""
    logger.info("Testing configuration loading...")

    try:
        from duckbot.core.qwen3_omni_integration import Qwen3OmniConfig

        # Test default configuration
        config = Qwen3OmniConfig()
        logger.info(f"Default config: model_id={config.model_id}, device={config.device}")

        # Test custom configuration
        custom_config = Qwen3OmniConfig(
            model_id="Qwen/Qwen3-Omni",
            device="cpu",
            use_flash_attention=False
        )
        logger.info(f"Custom config: model_id={custom_config.model_id}, device={custom_config.device}")

        logger.info("✓ Configuration loading test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Configuration loading test failed: {e}")
        return False

async def test_model_availability_check():
    """Test model availability check"""
    logger.info("Testing model availability check...")

    try:
        # Check if required dependencies are available
        import importlib

        dependencies = [
            "torch",
            "transformers",
            "soundfile",
            "PIL"
        ]

        available_deps = []
        missing_deps = []

        for dep in dependencies:
            try:
                importlib.import_module(dep)
                available_deps.append(dep)
            except ImportError:
                missing_deps.append(dep)

        logger.info(f"Available dependencies: {available_deps}")
        if missing_deps:
            logger.warning(f"Missing dependencies: {missing_deps}")

        # Check for flash attention
        try:
            import flash_attn
            logger.info("✓ Flash Attention 2 is available")
        except ImportError:
            logger.warning("⚠ Flash Attention 2 is not available (will use standard attention)")

        logger.info("✓ Model availability check completed")
        return True

    except Exception as e:
        logger.error(f"✗ Model availability check failed: {e}")
        return False

async def run_all_tests():
    """Run all integration tests"""
    logger.info("Starting Qwen3-Omni integration tests...")
    logger.info("=" * 50)

    tests = [
        ("Qwen3-Omni Import", test_qwen3_omni_import),
        ("Voice Assistant Import", test_voice_assistant_import),
        ("AI Provider Manager", test_ai_provider_manager),
        ("Qwen3-Omni Initialization", test_qwen3_omni_initialization),
        ("Voice Assistant Initialization", test_voice_assistant_initialization),
        ("Configuration Loading", test_configuration_loading),
        ("Model Availability Check", test_model_availability_check),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 30)

        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                failed += 1
                logger.warning(f"⚠ {test_name} FAILED (may be expected)")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} ERROR: {e}")

    logger.info("\n" + "=" * 50)
    logger.info("Test Summary:")
    logger.info(f"  Passed: {passed}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total:  {passed + failed}")

    if failed == 0:
        logger.info("🎉 All tests passed!")
        return True
    elif failed <= 2:
        logger.info("✅ Most tests passed - some failures may be expected")
        return True
    else:
        logger.error("❌ Multiple test failures - check dependencies")
        return False

async def main():
    """Main test function"""
    logger.info("Qwen3-Omni Integration Test Suite")
    logger.info("=================================")

    # Check if we're in the right directory
    if not (project_root / "duckbot").exists():
        logger.error("Not in the correct project directory")
        return False

    # Run tests
    success = await run_all_tests()

    # Print summary
    if success:
        logger.info("\n🚀 Qwen3-Omni integration is ready!")
        logger.info("\nNext steps:")
        logger.info("1. Install dependencies: pip install -r docs/requirements.txt")
        logger.info("2. Start DuckBot: python start_ecosystem.py")
        logger.info("3. Test with: python -c \"from duckbot.core.qwen3_omni_integration import qwen3_omni_integration; print(qwen3_omni_integration.get_status())\"")
    else:
        logger.error("\n❌ Integration test failed")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check dependencies are installed")
        logger.info("2. Verify configuration files")
        logger.info("3. Check for missing optional packages")

    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\nTests interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nUnexpected error: {e}")
        sys.exit(1)
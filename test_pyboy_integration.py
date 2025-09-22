#!/usr/bin/env python3
"""
Test script for PyBoy integration with DuckBot
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pyboy_basic():
    """Test basic PyBoy integration functionality"""
    logger.info("Testing PyBoy integration...")

    try:
        # Import PyBoy integration
        from duckbot.integrations.pyboy_integration import create_pyboy_integration

        # Create integration
        pyboy = await create_pyboy_integration(headless=True)
        if not pyboy:
            logger.error("Failed to create PyBoy integration")
            return False

        logger.info("✅ PyBoy integration created successfully")

        # Test availability check
        if pyboy.is_available():
            logger.info("✅ PyBoy is available")
        else:
            logger.error("❌ PyBoy is not available")
            return False

        # Test getting available ROMs
        roms = await pyboy.get_available_roms()
        logger.info(f"Available ROMs: {roms}")

        # Create ROMs directory for testing
        roms_dir = Path("roms")
        roms_dir.mkdir(exist_ok=True)

        # Create saves directory
        saves_dir = Path("saves")
        saves_dir.mkdir(exist_ok=True)

        logger.info("✅ ROMs and saves directories created")

        # Test game info without ROM loaded
        info = await pyboy.get_game_info()
        logger.info(f"Game info (no ROM): {info}")

        await pyboy.cleanup()
        logger.info("✅ PyBoy integration cleaned up")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def test_service_manager_integration():
    """Test PyBoy integration with DuckBot service manager"""
    logger.info("Testing PyBoy service manager integration...")

    try:
        # Import service manager
        from duckbot.core.service_manager import UnifiedServiceManager

        # Create service manager
        manager = UnifiedServiceManager()

        # Check if PyBoy service is registered
        if "pyboy" in manager.services:
            pyboy_service = manager.services["pyboy"]
            logger.info(f"✅ PyBoy service registered: {pyboy_service.display_name}")
            logger.info(f"Service type: {pyboy_service.service_type}")
            logger.info(f"Auto-start: {pyboy_service.auto_start}")
            logger.info(f"Config: {pyboy_service.config}")
        else:
            logger.error("❌ PyBoy service not found in service manager")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Service manager test failed: {e}")
        return False

async def test_ai_agent():
    """Test PyBoy AI agent functionality"""
    logger.info("Testing PyBoy AI agent...")

    try:
        from duckbot.integrations.pyboy_integration import create_pyboy_integration, RandomAIAgent

        # Create integration
        pyboy = await create_pyboy_integration(headless=True)
        if not pyboy:
            logger.error("Failed to create PyBoy integration")
            return False

        # Test AI agent creation
        agent = RandomAIAgent(pyboy)
        logger.info(f"✅ AI agent created: {agent.name}")
        logger.info(f"Description: {agent.description}")

        # Test agent decision making (without game loaded)
        action = await agent.decide_action(None, {})
        logger.info(f"✅ AI agent decided action: {action}")

        await pyboy.cleanup()
        return True

    except Exception as e:
        logger.error(f"❌ AI agent test failed: {e}")
        return False

async def test_webui_interface():
    """Test PyBoy WebUI interface"""
    logger.info("Testing PyBoy WebUI interface...")

    try:
        from duckbot.integrations.pyboy_integration import create_pyboy_integration
        from duckbot.integrations.pyboy_webui import PyBoyWebUI

        # Create integration
        pyboy = await create_pyboy_integration(headless=True)
        if not pyboy:
            logger.error("Failed to create PyBoy integration")
            return False

        # Create WebUI interface
        webui = PyBoyWebUI(pyboy)
        logger.info("✅ PyBoy WebUI interface created")

        # Test getting ROMs
        roms = await webui.get_available_roms()
        logger.info(f"Available ROMs via WebUI: {roms}")

        # Test getting game info
        info = await webui.get_game_info()
        logger.info(f"Game info via WebUI: {info}")

        # Test getting controls
        controls = await webui.get_game_controls()
        logger.info(f"Game controls available: {len(controls.get('buttons', []))} buttons")

        # Test performance stats
        perf = await webui.get_performance_stats()
        logger.info(f"Performance stats: {perf}")

        await webui.cleanup()
        await pyboy.cleanup()
        return True

    except Exception as e:
        logger.error(f"❌ WebUI interface test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("PYBOY INTEGRATION TEST SUITE")
    logger.info("=" * 60)

    tests = [
        ("Basic Integration", test_pyboy_basic),
        ("Service Manager Integration", test_service_manager_integration),
        ("AI Agent", test_ai_agent),
        ("WebUI Interface", test_webui_interface)
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            logger.info(f"[{status}] {test_name}")
        except Exception as e:
            logger.error(f"[ERROR] {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name:.<30} {status}")
        if result:
            passed += 1

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! PyBoy integration is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
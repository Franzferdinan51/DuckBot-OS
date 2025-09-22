#!/usr/bin/env python3
"""
PyBoy Integration Demo for DuckBot
Demonstrates Game Boy emulator capabilities with AI agents
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_pyboy_features():
    """Demonstrate PyBoy integration features"""
    logger.info("🎮 PyBoy Integration Demo")
    logger.info("=" * 50)

    try:
        from duckbot.integrations.pyboy_integration import create_pyboy_integration, RandomAIAgent
        from duckbot.integrations.pyboy_webui import PyBoyWebUI

        # Create integration
        pyboy = await create_pyboy_integration(headless=True)
        if not pyboy:
            logger.error("❌ Failed to create PyBoy integration")
            return

        logger.info("✅ PyBoy integration created successfully")

        # Create WebUI interface
        webui = PyBoyWebUI(pyboy)
        logger.info("✅ WebUI interface created")

        # Demo 1: Check available ROMs
        logger.info("\n📁 Demo 1: Checking available ROMs")
        roms = await webui.get_available_roms()
        if roms:
            logger.info(f"✅ Found ROMs: {roms}")
        else:
            logger.info("ℹ️  No ROMs found. Add .gb/.gbc files to 'roms/' directory")

        # Demo 2: Game controls
        logger.info("\n🎮 Demo 2: Game controls")
        controls = await webui.get_game_controls()
        logger.info(f"✅ Available controls: {len(controls['buttons'])} buttons")
        for button in controls['buttons']:
            logger.info(f"   - {button['label']} ({button['name']}) - {button['key']}")

        # Demo 3: AI Agent creation
        logger.info("\n🤖 Demo 3: AI Agent demonstration")
        agent = RandomAIAgent(pyboy)
        logger.info(f"✅ Created AI agent: {agent.name}")
        logger.info(f"   Description: {agent.description}")

        # Demo some AI decisions
        logger.info("\n🎯 Demo AI decisions:")
        for i in range(5):
            action = await agent.decide_action(None, {})
            logger.info(f"   Frame {i+1}: {action}")
            await asyncio.sleep(0.1)

        # Demo 4: Performance monitoring
        logger.info("\n📊 Demo 4: Performance monitoring")
        perf = await webui.get_performance_stats()
        logger.info(f"   FPS: {perf['fps']}")
        logger.info(f"   Frames processed: {perf['frames_processed']}")
        logger.info(f"   Actions taken: {perf['actions_taken']}")
        logger.info(f"   AI enabled: {perf['ai_enabled']}")

        # Demo 5: Service integration
        logger.info("\n🔧 Demo 5: Service manager integration")
        from duckbot.core.service_manager import UnifiedServiceManager

        manager = UnifiedServiceManager()
        if "pyboy" in manager.services:
            service = manager.services["pyboy"]
            logger.info(f"✅ Service registered: {service.display_name}")
            logger.info(f"   Type: {service.service_type}")
            logger.info(f"   Auto-start: {service.auto_start}")
            logger.info(f"   Config: {service.config}")

        # Demo 6: WebUI API endpoints (simulated)
        logger.info("\n🌐 Demo 6: Available WebUI API endpoints")
        endpoints = [
            "GET /api/pyboy/info - Get PyBoy system information",
            "GET /api/pyboy/roms - List available ROM files",
            "POST /api/pyboy/load - Load a game",
            "POST /api/pyboy/stop - Stop current game",
            "GET /api/pyboy/frame - Get current game frame",
            "POST /api/pyboy/control - Press game button",
            "POST /api/pyboy/ai - Run AI agent",
            "POST /api/pyboy/save - Save game state",
            "POST /api/pyboy/load_state - Load game state",
            "GET /api/pyboy/sessions - List game sessions",
            "GET /api/pyboy/performance - Get performance stats",
            "GET /api/pyboy/controls - Get game controls",
            "POST /api/pyboy/run_frame - Run single frame"
        ]

        for endpoint in endpoints:
            logger.info(f"   {endpoint}")

        await webui.cleanup()
        await pyboy.cleanup()

        logger.info("\n🎉 PyBoy integration demo completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Add Game Boy ROM files to 'roms/' directory")
        logger.info("2. Start DuckBot and access PyBoy via WebUI")
        logger.info("3. Try the AI agents with actual games")
        logger.info("4. Develop custom AI agents for specific games")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the demonstration"""
    await demo_pyboy_features()

if __name__ == "__main__":
    asyncio.run(main())
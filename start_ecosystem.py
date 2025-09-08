#!/usr/bin/env python3
"""
DuckBot Ecosystem Starter
Comprehensive service orchestration for DuckBot with all integrations
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

# Add the duckbot module to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from duckbot.cost_tracker import cost_tracker
except ImportError:
    cost_tracker = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EcosystemManager:
    """Manages the complete DuckBot ecosystem"""
    
    def __init__(self):
        self.services = {}
        self.running = False
        
    async def start_core_services(self):
        """Start core DuckBot services"""
        logger.info("Starting core DuckBot services...")
        
        # Start Enhanced WebUI
        try:
            from duckbot.enhanced_webui import start_enhanced_webui
            self.services['enhanced_webui'] = asyncio.create_task(
                start_enhanced_webui(host="127.0.0.1", port=8787)
            )
            logger.info("Enhanced WebUI started on port 8787")
        except Exception as e:
            logger.error(f"Failed to start Enhanced WebUI: {e}")
        
        # Start cost tracking
        try:
            if cost_tracker:
                cost_tracker.start_monitoring()
                logger.info("Cost tracking started")
            else:
                logger.info("Cost tracker not available - continuing without it")
        except Exception as e:
            logger.error(f"Failed to start cost tracking: {e}")
    
    async def start_integration_services(self):
        """Start integration services"""
        logger.info("Starting integration services...")
        
        # ByteBot Integration
        try:
            from duckbot.bytebot_integration import bytebot_integration
            self.services['bytebot'] = asyncio.create_task(
                bytebot_integration.start_service()
            )
            logger.info("ByteBot integration service started")
        except Exception as e:
            logger.error(f"Failed to start ByteBot: {e}")
        
        # Archon Integration
        try:
            from duckbot.archon_integration import ArchonIntegration
            archon = ArchonIntegration()
            self.services['archon'] = asyncio.create_task(
                archon.start_service()
            )
            logger.info("Archon multi-agent service started")
        except Exception as e:
            logger.error(f"Failed to start Archon: {e}")
        
        # WSL Integration
        try:
            from duckbot.wsl_integration import wsl_integration
            self.services['wsl'] = asyncio.create_task(
                wsl_integration.start_service()
            )
            logger.info("WSL integration service started")
        except Exception as e:
            logger.error(f"Failed to start WSL: {e}")
        
        # ChromiumOS Integration  
        try:
            from duckbot.chromium_integration import chromium_integration
            self.services['chromium'] = asyncio.create_task(
                chromium_integration.start_service()
            )
            logger.info("ChromiumOS integration service started")
        except Exception as e:
            logger.error(f"Failed to start ChromiumOS: {e}")
    
    async def start_ecosystem(self):
        """Start the complete ecosystem"""
        logger.info("🚀 Starting DuckBot Complete Ecosystem...")
        
        self.running = True
        
        # Start core services
        await self.start_core_services()
        
        # Start integration services
        await self.start_integration_services()
        
        logger.info("✅ DuckBot Ecosystem fully initialized!")
        logger.info("🎨 Enhanced WebUI: http://127.0.0.1:8787")
        logger.info("📊 All integrations active and monitoring")
        
        # Keep the ecosystem running
        try:
            while self.running:
                await asyncio.sleep(60)  # Ecosystem heartbeat
                logger.debug("Ecosystem running - all services active")
        except KeyboardInterrupt:
            logger.info("Shutting down ecosystem...")
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down DuckBot ecosystem...")
        self.running = False
        
        # Cancel all running tasks
        for name, task in self.services.items():
            if not task.done():
                logger.info(f"Stopping {name}...")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("DuckBot ecosystem shutdown complete")

async def main():
    """Main entry point"""
    ecosystem = EcosystemManager()
    await ecosystem.start_ecosystem()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEcosystem startup cancelled by user")
    except Exception as e:
        logger.error(f"Ecosystem startup failed: {e}")
        sys.exit(1)
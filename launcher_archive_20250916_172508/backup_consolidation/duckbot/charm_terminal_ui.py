#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Charm Terminal Interface
Beautiful interactive terminal experience using Charm tools
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Try to import the existing charm manager
try:
    from duckbot.ui.charm_manager import CharmManager
    CHARM_AVAILABLE = True
except ImportError:
    CHARM_AVAILABLE = False
    print("Warning: Charm manager not found. Terminal interface will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CharmTerminalUI:
    """
    Terminal interface wrapper for Charm tools
    """

    def __init__(self):
        self.charm_manager = None
        if CHARM_AVAILABLE:
            try:
                self.charm_manager = CharmManager()
            except Exception as e:
                logger.error(f"Error initializing Charm manager: {e}")

    async def start_interactive_mode(self):
        """Start interactive terminal mode"""
        if not CHARM_AVAILABLE or not self.charm_manager:
            print("Charm terminal interface not available")
            print("Please install Charm tools: https://charm.sh/")
            return

        try:
            print("Starting Charm Terminal Interface...")
            print("Type 'quit' or 'exit' to return to main menu")
            print("-" * 50)

            # Start the charm manager interactive mode
            await self.charm_manager.start_interactive()

        except Exception as e:
            logger.error(f"Error in terminal interface: {e}")
            print(f"Error: {e}")

    async def start_service(self):
        """Start terminal interface as a service"""
        if not CHARM_AVAILABLE or not self.charm_manager:
            logger.warning("Charm terminal interface not available")
            return

        try:
            logger.info("Starting Charm Terminal Service")
            await self.charm_manager.start_service()
        except Exception as e:
            logger.error(f"Error starting terminal service: {e}")

async def main():
    """Main function"""
    terminal_ui = CharmTerminalUI()
    await terminal_ui.start_interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())
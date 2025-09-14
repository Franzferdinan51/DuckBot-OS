#!/usr/bin/env python3
"""
DuckBot Discord Bot with VibeVoice Integration
Main Discord bot for DuckBot v3.1.0+ with complete VibeVoice TTS functionality
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)

# Import components with error handling
VIBEVOICE_AVAILABLE = False
COST_TRACKING_AVAILABLE = False
LIVEKIT_AVAILABLE = False

try:
    from .vibevoice_commands import VibeVoiceCommands
    VIBEVOICE_AVAILABLE = True
    logger.info("VibeVoice commands available")
except ImportError as e:
    logger.warning(f"VibeVoice commands not available: {e}")
    VibeVoiceCommands = None

try:
    from .cost_commands import CostCommands
    from .cost_tracker import CostTracker
    COST_TRACKING_AVAILABLE = True
    logger.info("Cost tracking available")
except ImportError as e:
    logger.warning(f"Cost tracking not available: {e}")
    CostCommands = None
    CostTracker = None

try:
    from .livekit_integration import LiveKitIntegration, LiveKitCommands
    LIVEKIT_AVAILABLE = True
    logger.info("LiveKit integration available")
except ImportError as e:
    logger.warning(f"LiveKit integration not available: {e}")
    LiveKitIntegration = None
    LiveKitCommands = None

logger = logging.getLogger(__name__)

class DiscordBot:
    """Main DuckBot Discord bot with VibeVoice integration."""

    def __init__(self):
        """Initialize Discord bot with all cogs and functionality."""
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True

        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        # Initialize services
        self.cost_tracker = CostTracker() if COST_TRACKING_AVAILABLE else None
        self.livekit = LiveKitIntegration(cost_tracker=self.cost_tracker) if LIVEKIT_AVAILABLE else None
        self.start_time = datetime.now()

        # Bot configuration
        self.bot_version = "3.1.0+"
        self.activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="DuckBot v3.1.0+ Enhanced | /help"
        )

    async def setup_hook(self):
        """Set up bot when it starts."""
        try:
            # Add cogs if available
            if VIBEVOICE_AVAILABLE and VibeVoiceCommands:
                await self.bot.add_cog(VibeVoiceCommands(self.bot, self.cost_tracker))
                logger.info("VibeVoice commands loaded")

            if COST_TRACKING_AVAILABLE and CostCommands:
                await self.bot.add_cog(CostCommands(self.bot))
                logger.info("Cost commands loaded")

            # Setup LiveKit commands if available
            if LIVEKIT_AVAILABLE and LiveKitCommands and self.livekit:
                livekit_commands = LiveKitCommands(self.bot, self.livekit)
                await livekit_commands.setup_commands()
                logger.info("LiveKit commands loaded")

            # Add basic help command
            @self.bot.tree.command(name="help", description="Show available commands")
            async def help_command(interaction: discord.Interaction):
                embed = discord.Embed(
                    title="DuckBot v3.1.0+ Help",
                    description="Available commands:",
                    color=discord.Color.blue()
                )

                if VIBEVOICE_AVAILABLE:
                    embed.add_field(
                        name="/vibevoice",
                        value="Generate multi-speaker voice content using VibeVoice TTS",
                        inline=False
                    )

                if COST_TRACKING_AVAILABLE:
                    embed.add_field(
                        name="/cost_summary",
                        value="Get AI usage cost summary",
                        inline=False
                    )

                if LIVEKIT_AVAILABLE:
                    embed.add_field(
                        name="/create_voice_room",
                        value="Create a voice conference room",
                        inline=False
                    )
                    embed.add_field(
                        name="/list_voice_rooms",
                        value="List available voice conference rooms",
                        inline=False
                    )

                embed.add_field(
                    name="/status",
                    value="Check bot status and available features",
                    inline=False
                )

                await interaction.response.send_message(embed=embed)

            # Add status command
            @self.bot.tree.command(name="status", description="Check bot status and available features")
            async def status_command(interaction: discord.Interaction):
                embed = discord.Embed(
                    title="DuckBot Status",
                    description=f"Version: {self.bot_version}",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="VibeVoice",
                    value="✅ Available" if VIBEVOICE_AVAILABLE else "❌ Unavailable",
                    inline=True
                )

                embed.add_field(
                    name="Cost Tracking",
                    value="✅ Available" if COST_TRACKING_AVAILABLE else "❌ Unavailable",
                    inline=True
                )

                embed.add_field(
                    name="LiveKit",
                    value="✅ Available" if LIVEKIT_AVAILABLE else "❌ Unavailable",
                    inline=True
                )

                uptime = datetime.now() - self.start_time
                embed.add_field(
                    name="Uptime",
                    value=str(uptime).split('.')[0],
                    inline=True
                )

                await interaction.response.send_message(embed=embed)

            # Sync commands
            synced = await self.bot.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")

        except Exception as e:
            logger.error(f"Failed to setup bot: {e}")
            raise

    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Bot logged in as {self.bot.user}")
        logger.info(f"Bot ID: {self.bot.user.id}")
        logger.info(f"Discord.py Version: {discord.__version__}")
        logger.info(f"DuckBot Version: {self.bot_version}")

        # Set bot activity
        await self.bot.change_presence(activity=self.activity)

        # Log startup info
        logger.info("=== DUCKBOT DISCORD BOT STARTED ===")
        logger.info(f"VibeVoice: {'Available' if VIBEVOICE_AVAILABLE else 'Unavailable'}")
        logger.info(f"Cost Tracking: {'Available' if COST_TRACKING_AVAILABLE else 'Unavailable'}")
        logger.info(f"LiveKit: {'Available' if LIVEKIT_AVAILABLE else 'Unavailable'}")
        logger.info(f"Cost tracker: {'Active' if self.cost_tracker else 'Inactive'}")
        logger.info("Bot is ready to receive commands!")

    async def _check_vibevoice(self) -> bool:
        """Check if VibeVoice is available."""
        return VIBEVOICE_AVAILABLE

    async def start_service(self):
        """Start the Discord bot service."""
        try:
            # Get token from environment
            token = os.getenv('DISCORD_BOT_TOKEN')
            if not token:
                logger.error("DISCORD_BOT_TOKEN environment variable not set")
                return False

            logger.info("Starting Discord bot...")
            await self.bot.start(token)

        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            return False

    async def stop_service(self):
        """Stop the Discord bot service."""
        try:
            logger.info("Stopping Discord bot...")
            await self.bot.close()
            logger.info("Discord bot stopped")

        except Exception as e:
            logger.error(f"Error stopping Discord bot: {e}")

# Command for testing bot startup
async def test_discord_bot():
    """Test function to verify Discord bot can be initialized."""
    try:
        bot = DiscordBot()
        logger.info("Discord bot class initialized successfully")

        # Check if required components are available
        logger.info(f"VibeVoice available: {VIBEVOICE_AVAILABLE}")
        logger.info(f"Cost tracking available: {COST_TRACKING_AVAILABLE}")

        return True

    except Exception as e:
        logger.error(f"Failed to test Discord bot: {e}")
        return False

# Interactive mode function
async def start_interactive_mode():
    """Start Discord bot in interactive mode."""
    print("=== DUCKBOT DISCORD BOT - INTERACTIVE MODE ===")
    print("Initializing Discord bot with VibeVoice integration...")

    try:
        bot = DiscordBot()

        # Check token
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("❌ DISCORD_BOT_TOKEN environment variable not set!")
            print("Please set your Discord bot token:")
            print("set DISCORD_BOT_TOKEN=your_token_here")
            return

        print("✅ Bot initialized successfully")
        print(f"✅ VibeVoice: {'Available' if VIBEVOICE_AVAILABLE else 'Unavailable'}")
        print(f"✅ Cost Tracking: {'Available' if COST_TRACKING_AVAILABLE else 'Unavailable'}")
        print("🚀 Starting bot...")

        await bot.start_service()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down bot...")
        await bot.stop_service()
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Interactive mode error: {e}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/discord_bot.log'),
            logging.StreamHandler()
        ]
    )

    # Start interactive mode if run directly
    asyncio.run(start_interactive_mode())
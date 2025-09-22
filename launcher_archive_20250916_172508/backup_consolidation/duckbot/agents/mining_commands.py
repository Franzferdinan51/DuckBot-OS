#!/usr/bin/env python3
"""
Mining Commands for DuckBot Discord Bot
Comprehensive cryptocurrency mining management commands
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from typing import Optional
from datetime import datetime

from ..integrations.mining_manager import MiningManager, MiningSoftware

logger = logging.getLogger(__name__)

class MiningCommands(commands.Cog):
    """Discord commands for mining management."""

    def __init__(self, bot: commands.Bot, mining_manager: MiningManager):
        self.bot = bot
        self.mining_manager = mining_manager
        self.status_embeds = {}  # Store status embeds for updates

    async def cog_load(self):
        """Initialize mining commands when cog loads."""
        try:
            # Initialize mining manager
            if await self.mining_manager.initialize():
                logger.info("Mining manager initialized successfully")
            else:
                logger.warning("Mining manager initialization failed")
        except Exception as e:
            logger.error(f"Failed to initialize mining commands: {e}")

    @app_commands.command(name="mining_status", description="Get comprehensive mining status and statistics")
    async def mining_status(self, interaction: discord.Interaction):
        """Get current mining status across all mining software."""
        await interaction.response.defer(thinking=True)

        try:
            status = await self.mining_manager.get_mining_status()

            if "error" in status:
                embed = discord.Embed(
                    title="[❌] Mining Status Error",
                    description=f"Error getting status: {status['error']}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            # Create main status embed
            active_miner = status.get("active_miner", "None")
            overall_status = status.get("overall_status", "stopped")

            embed = discord.Embed(
                title="[⛏️] Mining Status Dashboard",
                description=f"**Active Miner:** {active_miner.upper() if active_miner else 'NONE'}\n"
                           f"**Overall Status:** {overall_status.upper()}",
                color=discord.Color.green() if overall_status == "running" else discord.Color.orange()
            )

            # Add miner-specific information
            for miner_name, miner_data in status.get("miners", {}).items():
                miner_status = "🟢 RUNNING" if miner_data.get("is_running") else "🔴 STOPPED"
                available = "✅ Available" if miner_data.get("executable_available") else "❌ Not Available"

                if "error" in miner_data:
                    miner_status = f"❌ ERROR: {miner_data['error'][:50]}..."

                embed.add_field(
                    name=f"{miner_name.upper()}",
                    value=f"{miner_status}\n{available}",
                    inline=True
                )

            # Add active miner details
            if active_miner and active_miner in status.get("miners", {}):
                active_data = status["miners"][active_miner]
                stats = active_data.get("stats", {})

                if stats:
                    embed.add_field(
                        name="📊 Active Miner Stats",
                        value=(
                            f"**Hashrate:** {stats.get('hashrate', 0):,.0f} H/s\n"
                            f"**Power:** {stats.get('power_consumption', 0):.0f}W\n"
                            f"**Efficiency:** {stats.get('efficiency', 0):.2f} H/W\n"
                            f"**Algorithm:** {stats.get('algorithm', 'unknown')}\n"
                            f"**Coin:** {stats.get('coin', 'unknown')}\n"
                            f"**Profitability:** ${stats.get('profitability', 0):.4f}/day"
                        ),
                        inline=False
                    )

                    # Add temperature info if available
                    temps = stats.get("temperature", [])
                    if temps:
                        avg_temp = sum(temps) / len(temps)
                        max_temp = max(temps)
                        temp_color = "🟢" if max_temp < 75 else "🟡" if max_temp < 85 else "🔴"

                        embed.add_field(
                            name="🌡️ Temperature",
                            value=f"{temp_color} Avg: {avg_temp:.1f}°C | Max: {max_temp:.1f}°C",
                            inline=True
                        )

            embed.set_footer(text="Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_thumbnail(url="https://i.imgur.com/8Q7h9qE.png")  # Mining icon

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in mining_status command: {e}")
            await interaction.followup.send(f"Error getting mining status: {e}")

    @app_commands.command(name="mining_start", description="Start cryptocurrency mining")
    @app_commands.describe(
        software="Mining software (MultiPoolMiner or NPlusMiner)",
        algorithm="Mining algorithm (leave blank for auto)",
        coin="Specific coin to mine (leave blank for auto)",
        intensity="Mining intensity (1-100, default: 100)"
    )
    async def mining_start(self,
                          interaction: discord.Interaction,
                          software: str = "multipoolminer",
                          algorithm: Optional[str] = None,
                          coin: Optional[str] = None,
                          intensity: int = 100):
        """Start mining with specified parameters."""
        await interaction.response.defer(thinking=True)

        try:
            # Parse software selection
            software_map = {
                "multipoolminer": MiningSoftware.MULTIPOOLMINER,
                "nplusminer": MiningSoftware.NPLUSMINER,
                "mpm": MiningSoftware.MULTIPOOLMINER,
                "npm": MiningSoftware.NPLUSMINER
            }

            selected_software = software_map.get(software.lower())
            if not selected_software:
                embed = discord.Embed(
                    title="[❌] Invalid Software",
                    description="Available software: MultiPoolMiner, NPlusMiner",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            # Validate intensity
            if not 1 <= intensity <= 100:
                embed = discord.Embed(
                    title="[❌] Invalid Intensity",
                    description="Intensity must be between 1 and 100",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            # Start mining
            success = await self.mining_manager.start_mining(
                software=selected_software,
                algorithm=algorithm,
                coin=coin,
                intensity=intensity
            )

            if success:
                embed = discord.Embed(
                    title="[✅] Mining Started",
                    description=(
                        f"**Software:** {selected_software.value.upper()}\n"
                        f"**Algorithm:** {algorithm or 'Auto'}\n"
                        f"**Coin:** {coin or 'Auto'}\n"
                        f"**Intensity:** {intensity}%"
                    ),
                    color=discord.Color.green()
                )
                embed.add_field(name="Status", value="Mining is now active", inline=False)
                embed.set_thumbnail(url="https://i.imgur.com/Gx9x6Kk.png")  # Green check
            else:
                embed = discord.Embed(
                    title="[❌] Failed to Start Mining",
                    description="Could not start mining. Possible reasons:\n"
                              "• Mining software not installed\n"
                              "• Another instance is running\n"
                              "• Insufficient permissions",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in mining_start command: {e}")
            await interaction.followup.send(f"Error starting mining: {e}")

    @app_commands.command(name="mining_stop", description="Stop all cryptocurrency mining")
    async def mining_stop(self, interaction: discord.Interaction):
        """Stop all mining operations."""
        await interaction.response.defer(thinking=True)

        try:
            success = await self.mining_manager.stop_mining()

            if success:
                embed = discord.Embed(
                    title="[⏹️] Mining Stopped",
                    description="All mining operations have been stopped successfully.",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Status", value="Mining is now inactive", inline=False)
                embed.set_thumbnail(url="https://i.imgur.com/5Q9x6Kk.png")  # Stop icon
            else:
                embed = discord.Embed(
                    title="[❌] Failed to Stop Mining",
                    description="Could not stop mining operations.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in mining_stop command: {e}")
            await interaction.followup.send(f"Error stopping mining: {e}")

    @app_commands.command(name="mining_optimize", description="Get mining optimization recommendations")
    async def mining_optimize(self, interaction: discord.Interaction):
        """Get AI-powered mining optimization recommendations."""
        await interaction.response.defer(thinking=True)

        try:
            recommendations = await self.mining_manager.optimize_mining()

            if "error" in recommendations:
                embed = discord.Embed(
                    title="[❌] Optimization Error",
                    description=f"Error getting recommendations: {recommendations['error']}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=return)

            embed = discord.Embed(
                title="[⚡] Mining Optimization",
                description="AI-powered optimization recommendations",
                color=discord.Color.blue()
            )

            # Current setup
            embed.add_field(
                name="🔧 Current Setup",
                value=(
                    f"**Software:** {recommendations.get('current_software', 'Unknown')}\n"
                    f"**Hashrate:** {recommendations.get('current_hashrate', 0):,.0f} H/s\n"
                    f"**Efficiency:** {recommendations.get('current_efficiency', 0):.2f} H/W"
                ),
                inline=False
            )

            # Power optimization
            power_opt = recommendations.get('power_optimization', {})
            if power_opt:
                suggestions = power_opt.get('suggestions', [])
                if suggestions:
                    embed.add_field(
                        name="⚡ Power Optimization",
                        value="\n".join(f"• {s}" for s in suggestions),
                        inline=False
                    )

            # Temperature analysis
            temp_analysis = recommendations.get('temperature_analysis', {})
            if temp_analysis:
                warnings = temp_analysis.get('warnings', [])
                if warnings:
                    embed.add_field(
                        name="🌡️ Temperature Analysis",
                        value="\n".join(f"⚠️ {w}" for w in warnings),
                        inline=False
                    )

            # Algorithm recommendations
            algo_recs = recommendations.get('algorithm_recommendations', [])
            if algo_recs:
                best_algo = max(algo_recs, key=lambda x: x.get('profitability', 0))
                embed.add_field(
                    name="🎯 Best Algorithm",
                    value=(
                        f"**{best_algo.get('algorithm', 'Unknown').upper()}**\n"
                        f"Coin: {best_algo.get('coin', 'Unknown')}\n"
                        f"Profitability: ${best_algo.get('profitability', 0):.2f}/day"
                    ),
                    inline=True
                )

            # Software recommendations
            sw_recs = recommendations.get('software_recommendations', [])
            if sw_recs:
                rec_text = "\n".join(
                    f"**{rec.get('software', 'Unknown')}**\n" +
                    "\n".join(f"  • {adv}" for adv in rec.get('advantages', []))
                    for rec in sw_recs
                )
                embed.add_field(
                    name="🔄 Software Recommendations",
                    value=rec_text,
                    inline=False
                )

            embed.set_footer(text="Optimization based on current performance and market conditions")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in mining_optimize command: {e}")
            await interaction.followup.send(f"Error getting optimization: {e}")

    @app_commands.command(name="mining_switch", description="Switch between different mining software")
    @app_commands.describe(
        software="Target mining software (multipoolminer or nplusminer)"
    )
    async def mining_switch(self, interaction: discord.Interaction, software: str):
        """Switch to different mining software."""
        await interaction.response.defer(thinking=True)

        try:
            software_map = {
                "multipoolminer": MiningSoftware.MULTIPOOLMINER,
                "nplusminer": MiningSoftware.NPLUSMINER,
                "mpm": MiningSoftware.MULTIPOOLMINER,
                "npm": MiningSoftware.NPLUSMINER
            }

            target_software = software_map.get(software.lower())
            if not target_software:
                embed = discord.Embed(
                    title="[❌] Invalid Software",
                    description="Available software: MultiPoolMiner, NPlusMiner",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            success = await self.mining_manager.switch_miner(target_software)

            if success:
                embed = discord.Embed(
                    title="[🔄] Miner Switched",
                    description=f"Successfully switched to {target_software.value.upper()}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Status", value="Migration completed successfully", inline=False)
            else:
                embed = discord.Embed(
                    title="[❌] Switch Failed",
                    description=f"Could not switch to {target_software.value.upper()}",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in mining_switch command: {e}")
            await interaction.followup.send(f"Error switching miner: {e}")

    @app_commands.command(name="mining_profitability", description="Get current mining profitability data")
    async def mining_profitability(self, interaction: discord.Interaction):
        """Get current profitability data for various algorithms."""
        await interaction.response.defer(thinking=True)

        try:
            profitability_data = await self.mining_manager.get_profitability_data()

            embed = discord.Embed(
                title="[💰] Mining Profitability Dashboard",
                description="Current profitability data across algorithms",
                color=discord.Color.gold()
            )

            # Add timestamp
            embed.add_field(
                name="📅 Data Timestamp",
                value=profitability_data.get("timestamp", "Unknown"),
                inline=False
            )

            # Algorithm profitability
            algorithms = profitability_data.get("algorithms", {})
            if algorithms:
                algo_text = ""
                for algo, data in algorithms.items():
                    profitability = data.get("profitability", 0)
                    coin = data.get("coin", "Unknown")
                    difficulty = data.get("difficulty", 0)

                    algo_text += f"**{algo.upper()}** ({coin}):\n"
                    algo_text += f"  💰 ${profitability:.2f}/day\n"
                    algo_text += f"  📊 Difficulty: {difficulty:,.0f}\n\n"

                embed.add_field(name="🎯 Algorithm Profitability", value=algo_text, inline=False)

            # Pool information
            pools = profitability_data.get("pools", {})
            if pools:
                pool_text = ""
                for pool, data in pools.items():
                    fee = data.get("fee", 0)
                    reliability = data.get("reliability", "unknown")

                    reliability_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(reliability, "⚪")

                    pool_text += f"**{pool}** {reliability_emoji}\n"
                    pool_text += f"  💸 Fee: {fee*100:.1f}%\n"
                    pool_text += f"  📈 Reliability: {reliability.title()}\n\n"

                embed.add_field(name="🏊 Pool Information", value=pool_text, inline=True)

            embed.set_footer(text="Profitability data updates every 5 minutes")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in mining_profitability command: {e}")
            await interaction.followup.send(f"Error getting profitability: {e}")

    @app_commands.command(name="mining_help", description="Get help with mining commands")
    async def mining_help(self, interaction: discord.Interaction):
        """Show help for all mining commands."""
        embed = discord.Embed(
            title="[⛏️] Mining Commands Help",
            description="Comprehensive cryptocurrency mining management commands",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📊 Status & Monitoring",
            value=(
                "`/mining_status` - Get comprehensive mining status\n"
                "`/mining_profitability` - View profitability data"
            ),
            inline=False
        )

        embed.add_field(
            name="🎮 Control Commands",
            value=(
                "`/mining_start` - Start mining with custom settings\n"
                "`/mining_stop` - Stop all mining operations\n"
                "`/mining_switch` - Switch between mining software"
            ),
            inline=False
        )

        embed.add_field(
            name="⚡ Optimization",
            value=(
                "`/mining_optimize` - Get AI-powered recommendations"
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 Available Software",
            value=(
                "**MultiPoolMiner** - Fast switching, wide pool support\n"
                "**NPlusMiner** - AI optimization, built-in GUI"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 Tips",
            value=(
                "• Use `/mining_optimize` before starting for best settings\n"
                "• Monitor temperatures to prevent hardware damage\n"
                "• Switch algorithms based on profitability\n"
                "• Consider power costs vs. mining profits"
            ),
            inline=False
        )

        embed.set_footer(text="Use /help <command> for more details on specific commands")
        await interaction.response.send_message(embed=embed)
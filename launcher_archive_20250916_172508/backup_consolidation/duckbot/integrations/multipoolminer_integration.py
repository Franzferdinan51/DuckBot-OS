#!/usr/bin/env python3
"""
MultiPoolMiner Integration for DuckBot
Cryptocurrency mining profit optimization and monitoring system
"""

import asyncio
import aiohttp
import json
import os
import subprocess
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import psutil
import platform
import discord
from discord.ext import commands
from discord import app_commands

from ..core.cost_management import CostTracker

logger = logging.getLogger(__name__)

class MultiPoolMinerIntegration:
    """MultiPoolMiner integration for cryptocurrency mining optimization."""

    def __init__(self,
                 mpm_path: Optional[str] = None,
                 config_path: Optional[str] = None,
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize MultiPoolMiner integration.

        Args:
            mpm_path: Path to MultiPoolMiner executable
            config_path: Path to MultiPoolMiner configuration
            cost_tracker: Optional cost tracking instance
        """
        self.mpm_path = mpm_path or self._find_mpm_executable()
        self.config_path = config_path or "config/multipoolminer.json"
        self.cost_tracker = cost_tracker
        self.session = None
        self.process = None
        self.is_running = False
        self.stats_cache = {}
        self.last_update = None

        # Mining statistics
        self.total_hashrate = 0
        self.active_pools = []
        self.current_profitability = 0.0
        self.daily_earnings = 0.0
        self.power_consumption = 0

        # Supported algorithms and coins
        self.supported_algorithms = [
            "kawpow", "autolykos2", "ethash", "kheavyhash", "nimiq",
            "randomx", "randomarq", "randomwow", "randomxmonero",
            "firopow", "octopus", "autolykos", "tensority"
        ]

        self.supported_coins = [
            "RVN", "ERG", "ETH", "ETC", "NIM", "XMR", "ARQ", "WOW",
            "FIRO", "CTXC", "LOKI", "CON", "XLA", "TFC", "MTI"
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        if self.process:
            self.process.terminate()

    def _find_mpm_executable(self) -> Optional[str]:
        """Find MultiPoolMiner executable."""
        system = platform.system().lower()

        # Common paths to check
        search_paths = [
            "./MultiPoolMiner",
            "./multipoolminer",
            "./MPM",
            "./mpm",
            "/usr/local/bin/MultiPoolMiner",
            "/usr/bin/MultiPoolMiner",
            "C:\\Program Files\\MultiPoolMiner\\MultiPoolMiner.exe",
            "C:\\MultiPoolMiner\\MultiPoolMiner.exe"
        ]

        for path in search_paths:
            if Path(path).exists():
                return path

        return None

    async def initialize(self) -> bool:
        """Initialize MultiPoolMiner integration."""
        try:
            if not self.mpm_path:
                logger.warning("MultiPoolMiner executable not found")
                return False

            # Check if executable is working
            result = await self._run_mpm_command(["--version"])
            if result and "MultiPoolMiner" in result:
                logger.info("MultiPoolMiner integration initialized successfully")
                return True
            else:
                logger.warning("MultiPoolMiner executable not responding")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize MultiPoolMiner: {e}")
            return False

    async def _run_mpm_command(self, args: List[str]) -> Optional[str]:
        """Run MultiPoolMiner command and return output."""
        try:
            cmd = [self.mpm_path] + args
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                logger.error(f"MPM command failed: {stderr.decode()}")
                return None

        except Exception as e:
            logger.error(f"Error running MPM command: {e}")
            return None

    async def start_mining(self,
                          algorithm: Optional[str] = None,
                          coin: Optional[str] = None,
                          pool: Optional[str] = None,
                          intensity: int = 100) -> bool:
        """Start mining with specified parameters."""
        try:
            if self.is_running:
                logger.warning("Mining already running")
                return False

            # Build command
            cmd = [self.mpm_path]

            if algorithm:
                cmd.extend(["--algorithm", algorithm])
            if coin:
                cmd.extend(["--coin", coin])
            if pool:
                cmd.extend(["--pool", pool])

            cmd.extend([
                "--intensity", str(intensity),
                "--enable",
                "--daemon"
            ])

            # Start process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.is_running = True
            logger.info(f"Mining started with algorithm: {algorithm or 'auto'}")

            # Track cost if available
            if self.cost_tracker:
                await self.cost_tracker.track_custom_usage("mining_start", {
                    "algorithm": algorithm,
                    "coin": coin,
                    "intensity": intensity
                })

            return True

        except Exception as e:
            logger.error(f"Failed to start mining: {e}")
            return False

    async def stop_mining(self) -> bool:
        """Stop mining."""
        try:
            if not self.is_running:
                return True

            if self.process:
                self.process.terminate()
                await self.process.wait()
                self.process = None

            self.is_running = False
            logger.info("Mining stopped")

            # Track cost if available
            if self.cost_tracker:
                await self.cost_tracker.track_custom_usage("mining_stop", {
                    "duration": (datetime.now() - self.last_update).total_seconds() if self.last_update else 0
                })

            return True

        except Exception as e:
            logger.error(f"Failed to stop mining: {e}")
            return False

    async def get_mining_stats(self) -> Dict[str, Any]:
        """Get current mining statistics."""
        try:
            # Update cache if needed
            if not self.last_update or (datetime.now() - self.last_update).seconds > 30:
                await self._update_stats_cache()

            return {
                "is_running": self.is_running,
                "hashrate": self.total_hashrate,
                "active_pools": self.active_pools,
                "profitability": self.current_profitability,
                "daily_earnings": self.daily_earnings,
                "power_consumption": self.power_consumption,
                "uptime": (datetime.now() - self.last_update).total_seconds() if self.last_update else 0,
                "algorithm": self.stats_cache.get("current_algorithm", "unknown"),
                "coin": self.stats_cache.get("current_coin", "unknown"),
                "pool": self.stats_cache.get("current_pool", "unknown"),
                "temperature": self._get_gpu_temperatures(),
                "efficiency": self._calculate_efficiency()
            }

        except Exception as e:
            logger.error(f"Failed to get mining stats: {e}")
            return {"error": str(e)}

    async def _update_stats_cache(self):
        """Update statistics cache."""
        try:
            # Try to get stats from MPM API if available
            stats = await self._run_mpm_command(["--stats"])
            if stats:
                self.stats_cache = self._parse_stats_output(stats)

            # Update system stats
            self.total_hashrate = self.stats_cache.get("hashrate", 0)
            self.active_pools = self.stats_cache.get("pools", [])
            self.current_profitability = self.stats_cache.get("profitability", 0.0)
            self.daily_earnings = self.stats_cache.get("daily_earnings", 0.0)
            self.power_consumption = self._estimate_power_consumption()

            self.last_update = datetime.now()

        except Exception as e:
            logger.error(f"Failed to update stats cache: {e}")

    def _parse_stats_output(self, output: str) -> Dict[str, Any]:
        """Parse MultiPoolMiner stats output."""
        stats = {}

        try:
            lines = output.split('\n')
            for line in lines:
                if 'hasrate' in line.lower():
                    # Extract hashrate value
                    stats['hashrate'] = self._extract_hashrate(line)
                elif 'pool' in line.lower():
                    stats['pools'] = self._extract_pools(line)
                elif 'profitability' in line.lower():
                    stats['profitability'] = self._extract_profitability(line)
                elif 'algorithm' in line.lower():
                    stats['current_algorithm'] = self._extract_algorithm(line)
                elif 'coin' in line.lower():
                    stats['current_coin'] = self._extract_coin(line)

        except Exception as e:
            logger.error(f"Failed to parse stats: {e}")

        return stats

    def _extract_hashrate(self, line: str) -> float:
        """Extract hashrate from line."""
        try:
            # Simple extraction - look for numbers followed by H/s, MH/s, etc.
            import re
            match = re.search(r'(\d+(?:\.\d+)?)\s*([KMGT]?H/s)', line)
            if match:
                value = float(match.group(1))
                unit = match.group(2)

                # Convert to H/s
                multipliers = {"H/s": 1, "KH/s": 1000, "MH/s": 1000000, "GH/s": 1000000000}
                return value * multipliers.get(unit, 1)
        except:
            pass
        return 0.0

    def _extract_pools(self, line: str) -> List[str]:
        """Extract pool information from line."""
        # Simple pool extraction
        if "pool" in line.lower():
            return [line.strip()]
        return []

    def _extract_profitability(self, line: str) -> float:
        """Extract profitability from line."""
        try:
            import re
            match = re.search(r'\$?(\d+(?:\.\d+)?)', line)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0.0

    def _extract_algorithm(self, line: str) -> str:
        """Extract algorithm from line."""
        for algo in self.supported_algorithms:
            if algo.lower() in line.lower():
                return algo
        return "unknown"

    def _extract_coin(self, line: str) -> str:
        """Extract coin from line."""
        for coin in self.supported_coins:
            if coin in line:
                return coin
        return "unknown"

    def _get_gpu_temperatures(self) -> List[float]:
        """Get GPU temperatures."""
        try:
            temps = []
            if platform.system() == "Windows":
                # Use nvidia-smi or similar
                result = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    temps = [float(temp.strip()) for temp in result.stdout.strip().split('\n') if temp.strip()]
            else:
                # Use psutil for basic temperature info
                temps = [psutil.sensors_temperatures().get("coretemp", [{}])[0].get("current", 0)]

            return temps
        except:
            return []

    def _estimate_power_consumption(self) -> float:
        """Estimate power consumption in watts."""
        try:
            # Basic estimation based on GPU count and load
            gpu_count = len(self._get_gpu_temperatures())
            if self.is_running:
                # Estimate 200-300W per GPU under load
                return gpu_count * 250
            else:
                return gpu_count * 50  # Idle power
        except:
            return 0

    def _calculate_efficiency(self) -> float:
        """Calculate mining efficiency (hashrate per watt)."""
        if self.power_consumption > 0:
            return self.total_hashrate / self.power_consumption
        return 0.0

    async def get_profitability_data(self) -> Dict[str, Any]:
        """Get current profitability data for all supported algorithms."""
        try:
            # Get profitability from various sources
            profitability_data = {}

            for algorithm in self.supported_algorithms:
                # Simulate profitability data (in real implementation, this would query APIs)
                profitability_data[algorithm] = {
                    "current_profitability": 0.0,  # $/day
                    "difficulty": 0.0,
                    "network_hashrate": 0.0,
                    "block_reward": 0.0,
                    "recommended_pools": []
                }

            return profitability_data

        except Exception as e:
            logger.error(f"Failed to get profitability data: {e}")
            return {}

    async def optimize_settings(self) -> Dict[str, Any]:
        """Optimize mining settings based on current conditions."""
        try:
            current_stats = await self.get_mining_stats()
            profitability_data = await self.get_profitability_data()

            # Find most profitable algorithm
            best_algorithm = max(profitability_data.items(),
                                key=lambda x: x[1].get("current_profitability", 0))

            recommendations = {
                "current_algorithm": current_stats.get("algorithm"),
                "recommended_algorithm": best_algorithm[0],
                "estimated_improvement": best_algorithm[1].get("current_profitability", 0) - current_stats.get("profitability", 0),
                "power_optimization": self._suggest_power_optimization(current_stats),
                "temperature_warning": self._check_temperature_warnings(current_stats)
            }

            return recommendations

        except Exception as e:
            logger.error(f"Failed to optimize settings: {e}")
            return {"error": str(e)}

    def _suggest_power_optimization(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest power optimization settings."""
        try:
            temps = stats.get("temperature", [])
            efficiency = stats.get("efficiency", 0)

            suggestions = []

            if temps and max(temps) > 80:
                suggestions.append("Reduce intensity to lower temperature")

            if efficiency < 0.5:  # Less than 0.5 MH/s per watt
                suggestions.append("Consider underclocking for better efficiency")

            return {
                "suggestions": suggestions,
                "current_efficiency": efficiency,
                "max_temperature": max(temps) if temps else 0
            }

        except:
            return {"suggestions": []}

    def _check_temperature_warnings(self, stats: Dict[str, Any]) -> List[str]:
        """Check for temperature warnings."""
        warnings = []
        temps = stats.get("temperature", [])

        if temps:
            max_temp = max(temps)
            if max_temp > 85:
                warnings.append(f"CRITICAL: GPU temperature {max_temp}°C is too high!")
            elif max_temp > 75:
                warnings.append(f"WARNING: GPU temperature {max_temp}°C is high")

        return warnings

    async def create_configuration(self,
                                 algorithm: str = "auto",
                                 intensity: int = 100,
                                 pools: List[str] = None,
                                 settings: Dict[str, Any] = None) -> bool:
        """Create MultiPoolMiner configuration file."""
        try:
            config = {
                "version": "1.0",
                "algorithm": algorithm,
                "intensity": intensity,
                "pools": pools or [],
                "settings": settings or {
                    "enable_web_gui": True,
                    "auto_update": True,
                    "benchmark_on_start": True,
                    "log_level": "info"
                }
            }

            # Save configuration
            config_path = Path(self.config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Configuration saved to {config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            return False

class MultiPoolMinerCommands:
    """Discord commands for MultiPoolMiner integration."""

    def __init__(self, bot, multipoolminer_integration):
        self.bot = bot
        self.mpm = multipoolminer_integration
        self.cost_tracker = getattr(multipoolminer_integration, 'cost_tracker', None)

    async def register_commands(self):
        """Register Discord commands."""

        @self.bot.tree.command(name="mining_status", description="Get current mining status and statistics")
        async def mining_status(interaction):
            await interaction.response.defer(thinking=True)

            try:
                stats = await self.mpm.get_mining_stats()

                embed = discord.Embed(
                    title="[⛏️] Mining Status",
                    color=discord.Color.orange() if stats.get("is_running") else discord.Color.red()
                )

                if "error" not in stats:
                    status = "🟢 Active" if stats["is_running"] else "🔴 Inactive"
                    embed.add_field(name="Status", value=status, inline=True)
                    embed.add_field(name="Hashrate", value=f"{stats['hashrate']:,.0f} H/s", inline=True)
                    embed.add_field(name="Profitability", value=f"${stats['profitability']:.4f}/day", inline=True)
                    embed.add_field(name="Daily Earnings", value=f"${stats['daily_earnings']:.4f}", inline=True)
                    embed.add_field(name="Power Usage", value=f"{stats['power_consumption']:.0f}W", inline=True)
                    embed.add_field(name="Efficiency", value=f"{stats['efficiency']:.2f} H/W", inline=True)

                    if stats.get("temperature"):
                        avg_temp = sum(stats["temperature"]) / len(stats["temperature"])
                        embed.add_field(name="GPU Temperature", value=f"{avg_temp:.1f}°C", inline=True)

                    if stats.get("algorithm") != "unknown":
                        embed.add_field(name="Algorithm", value=stats["algorithm"], inline=True)
                    if stats.get("coin") != "unknown":
                        embed.add_field(name="Coin", value=stats["coin"], inline=True)
                else:
                    embed.description = f"Error: {stats['error']}"

                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error getting mining status: {e}")

        @self.bot.tree.command(name="mining_start", description="Start cryptocurrency mining")
        @app_commands.describe(
            algorithm="Mining algorithm (leave blank for auto)",
            coin="Specific coin to mine (leave blank for auto)",
            intensity="Mining intensity (1-100)"
        )
        async def mining_start(interaction, algorithm: str = None, coin: str = None, intensity: int = 100):
            await interaction.response.defer(thinking=True)

            try:
                success = await self.mpm.start_mining(algorithm, coin, intensity=intensity)

                if success:
                    embed = discord.Embed(
                        title="[✅] Mining Started",
                        description=f"Mining started successfully!\nAlgorithm: {algorithm or 'auto'}\nCoin: {coin or 'auto'}\nIntensity: {intensity}%",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="[❌] Failed to Start Mining",
                        description="Could not start mining. Check logs for details.",
                        color=discord.Color.red()
                    )

                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error starting mining: {e}")

        @self.bot.tree.command(name="mining_stop", description="Stop cryptocurrency mining")
        async def mining_stop(interaction):
            await interaction.response.defer(thinking=True)

            try:
                success = await self.mpm.stop_mining()

                if success:
                    embed = discord.Embed(
                        title="[⏹️] Mining Stopped",
                        description="Mining has been stopped successfully.",
                        color=discord.Color.orange()
                    )
                else:
                    embed = discord.Embed(
                        title="[❌] Failed to Stop Mining",
                        description="Could not stop mining. Check logs for details.",
                        color=discord.Color.red()
                    )

                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error stopping mining: {e}")

        @self.bot.tree.command(name="mining_optimize", description="Get mining optimization recommendations")
        async def mining_optimize(interaction):
            await interaction.response.defer(thinking=True)

            try:
                recommendations = await self.mpm.optimize_settings()

                embed = discord.Embed(
                    title="[⚡] Mining Optimization",
                    description="Optimization recommendations based on current conditions",
                    color=discord.Color.blue()
                )

                if "error" not in recommendations:
                    embed.add_field(name="Current Algorithm", value=recommendations["current_algorithm"], inline=True)
                    embed.add_field(name="Recommended Algorithm", value=recommendations["recommended_algorithm"], inline=True)
                    embed.add_field(name="Estimated Improvement", value=f"${recommendations['estimated_improvement']:.4f}/day", inline=True)

                    # Power optimization suggestions
                    power_opt = recommendations.get("power_optimization", {})
                    if power_opt.get("suggestions"):
                        suggestions = "\n".join(f"• {s}" for s in power_opt["suggestions"])
                        embed.add_field(name="Power Optimization", value=suggestions, inline=False)

                    # Temperature warnings
                    warnings = recommendations.get("temperature_warnings", [])
                    if warnings:
                        warning_text = "\n".join(f"⚠️ {w}" for w in warnings)
                        embed.add_field(name="Temperature Warnings", value=warning_text, inline=False)
                else:
                    embed.description = f"Error: {recommendations['error']}"

                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error getting optimization: {e}")

        # Register commands
        logger.info("MultiPoolMiner Discord commands registered")
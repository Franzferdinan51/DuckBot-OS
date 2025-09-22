#!/usr/bin/env python3
"""
Unified Mining Manager for DuckBot
Integrates MultiPoolMiner and NPlusMiner for comprehensive cryptocurrency mining
"""

import asyncio
import aiohttp
import json
import os
import subprocess
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import psutil
import platform
from enum import Enum
from dataclasses import dataclass

from ..core.cost_management import CostTracker

logger = logging.getLogger(__name__)

class MiningSoftware(Enum):
    """Supported mining software."""
    MULTIPOOLMINER = "multipoolminer"
    NPLUSMINER = "nplusminer"

class MiningStatus(Enum):
    """Mining operation status."""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    OPTIMIZING = "optimizing"

@dataclass
class MiningStats:
    """Mining statistics data structure."""
    hashrate: float = 0.0
    power_consumption: float = 0.0
    profitability: float = 0.0
    daily_earnings: float = 0.0
    temperature: List[float] = None
    uptime: float = 0.0
    algorithm: str = "unknown"
    coin: str = "unknown"
    pool: str = "unknown"
    efficiency: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.temperature is None:
            self.temperature = []
        if self.errors is None:
            self.errors = []

class MultiPoolMinerIntegration:
    """MultiPoolMiner integration with DuckBot."""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker
        self.mpm_path = self._find_executable("MultiPoolMiner")
        self.process = None
        self.is_running = False

    def _find_executable(self, name: str) -> Optional[str]:
        """Find mining executable."""
        search_paths = [
            f"./{name}", f"./{name.lower()}",
            f"/usr/local/bin/{name}", f"/usr/bin/{name}",
            f"C:\\Program Files\\{name}\\{name}.exe",
            f"C:\\{name}\\{name}.exe"
        ]
        for path in search_paths:
            if Path(path).exists():
                return path
        return None

    async def start_mining(self, algorithm: str = None, coin: str = None, intensity: int = 100) -> bool:
        """Start mining with MultiPoolMiner."""
        if not self.mpm_path:
            return False

        try:
            cmd = [self.mpm_path]
            if algorithm: cmd.extend(["--algorithm", algorithm])
            if coin: cmd.extend(["--coin", coin])
            cmd.extend(["--intensity", str(intensity), "--enable", "--daemon"])

            self.process = await asyncio.create_subprocess_exec(*cmd)
            self.is_running = True
            return True
        except Exception as e:
            logger.error(f"MultiPoolMiner start failed: {e}")
            return False

    async def stop_mining(self) -> bool:
        """Stop MultiPoolMiner."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.is_running = False
        return True

    async def get_stats(self) -> MiningStats:
        """Get MultiPoolMiner statistics."""
        return MiningStats(
            hashrate=0.0,  # Would parse from MPM output
            power_consumption=self._estimate_power(),
            profitability=0.0,
            algorithm=self._get_current_algorithm(),
            coin=self._get_current_coin()
        )

    def _estimate_power(self) -> float:
        """Estimate power consumption."""
        return 250.0 if self.is_running else 50.0

    def _get_current_algorithm(self) -> str:
        """Get current mining algorithm."""
        return "kawpow"  # Would parse from MPM

    def _get_current_coin(self) -> str:
        """Get current mining coin."""
        return "RVN"  # Would parse from MPM

class NPlusMinerIntegration:
    """NPlusMiner integration with DuckBot."""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker
        self.npm_path = self._find_executable("NPlusMiner")
        self.process = None
        self.is_running = False
        self.api_port = 4068  # Default NPlusMiner API port

    def _find_executable(self, name: str) -> Optional[str]:
        """Find mining executable."""
        search_paths = [
            f"./{name}", f"./{name.lower()}",
            f"/usr/local/bin/{name}", f"/usr/bin/{name}",
            f"C:\\Program Files\\{name}\\{name}.exe",
            f"C:\\{name}\\{name}.exe"
        ]
        for path in search_paths:
            if Path(path).exists():
                return path
        return None

    async def start_mining(self, algorithm: str = None, coin: str = None, intensity: int = 100) -> bool:
        """Start mining with NPlusMiner."""
        if not self.npm_path:
            return False

        try:
            cmd = [self.npm_path]
            if algorithm: cmd.extend(["-a", algorithm])
            if coin: cmd.extend(["-c", coin])
            cmd.extend(["-i", str(intensity), "--api-port", str(self.api_port)])

            self.process = await asyncio.create_subprocess_exec(*cmd)
            self.is_running = True
            return True
        except Exception as e:
            logger.error(f"NPlusMiner start failed: {e}")
            return False

    async def stop_mining(self) -> bool:
        """Stop NPlusMiner."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.is_running = False
        return True

    async def get_stats(self) -> MiningStats:
        """Get NPlusMiner statistics via API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{self.api_port}/api/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        return MiningStats(
                            hashrate=data.get("hashrate", 0),
                            power_consumption=data.get("power", 0),
                            profitability=data.get("profitability", 0),
                            daily_earnings=data.get("daily_earnings", 0),
                            temperature=data.get("temperatures", []),
                            algorithm=data.get("algorithm", "unknown"),
                            coin=data.get("coin", "unknown"),
                            pool=data.get("pool", "unknown")
                        )
        except Exception as e:
            logger.error(f"NPlusMiner API error: {e}")

        return MiningStats(
            hashrate=0.0,
            power_consumption=self._estimate_power(),
            algorithm=self._get_current_algorithm(),
            coin=self._get_current_coin()
        )

    def _estimate_power(self) -> float:
        """Estimate power consumption."""
        return 280.0 if self.is_running else 60.0

    def _get_current_algorithm(self) -> str:
        """Get current mining algorithm."""
        return "kawpow"  # Would parse from API

    def _get_current_coin(self) -> str:
        """Get current mining coin."""
        return "RVN"  # Would parse from API

class MiningManager:
    """Unified mining manager for DuckBot."""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker
        self.miners = {
            MiningSoftware.MULTIPOOLMINER: MultiPoolMinerIntegration(cost_tracker),
            MiningSoftware.NPLUSMINER: NPlusMinerIntegration(cost_tracker)
        }
        self.active_miner = None
        self.mining_history = []
        self.optimization_task = None

    async def initialize(self) -> bool:
        """Initialize mining manager."""
        try:
            # Check which miners are available
            available_miners = []
            for software, miner in self.miners.items():
                if miner._find_executable(software.value):
                    available_miners.append(software)
                    logger.info(f"{software.value} is available")
                else:
                    logger.warning(f"{software.value} not found")

            if not available_miners:
                logger.error("No mining software found")
                return False

            logger.info(f"Mining manager initialized with {len(available_miners)} miners")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize mining manager: {e}")
            return False

    async def start_mining(self,
                          software: MiningSoftware = MiningSoftware.MULTIPOOLMINER,
                          algorithm: str = None,
                          coin: str = None,
                          intensity: int = 100) -> bool:
        """Start mining with specified software."""
        try:
            # Stop any existing mining
            if self.active_miner:
                await self.stop_mining()

            # Start new miner
            miner = self.miners.get(software)
            if not miner:
                logger.error(f"Unknown mining software: {software}")
                return False

            success = await miner.start_mining(algorithm, coin, intensity)
            if success:
                self.active_miner = software
                logger.info(f"Started mining with {software.value}")

                # Track cost if available
                if self.cost_tracker:
                    await self.cost_tracker.track_custom_usage("mining_start", {
                        "software": software.value,
                        "algorithm": algorithm,
                        "coin": coin,
                        "intensity": intensity
                    })

                # Start optimization task
                self._start_optimization_task()

            return success

        except Exception as e:
            logger.error(f"Failed to start mining: {e}")
            return False

    async def stop_mining(self) -> bool:
        """Stop all mining operations."""
        try:
            if self.active_miner:
                miner = self.miners.get(self.active_miner)
                if miner:
                    await miner.stop_mining()

                # Track cost if available
                if self.cost_tracker:
                    await self.cost_tracker.track_custom_usage("mining_stop", {
                        "software": self.active_miner.value
                    })

                self.active_miner = None
                logger.info("Mining stopped")

            # Stop optimization task
            if self.optimization_task:
                self.optimization_task.cancel()
                self.optimization_task = None

            return True

        except Exception as e:
            logger.error(f"Failed to stop mining: {e}")
            return False

    async def get_mining_status(self) -> Dict[str, Any]:
        """Get comprehensive mining status."""
        try:
            status = {
                "active_miner": self.active_miner.value if self.active_miner else None,
                "overall_status": MiningStatus.RUNNING.value if self.active_miner else MiningStatus.STOPPED.value,
                "miners": {}
            }

            # Get stats for all miners
            for software, miner in self.miners.items():
                try:
                    stats = await miner.get_stats()
                    status["miners"][software.value] = {
                        "is_running": miner.is_running,
                        "stats": stats.__dict__,
                        "executable_available": bool(miner._find_executable(software.value))
                    }
                except Exception as e:
                    status["miners"][software.value] = {
                        "error": str(e),
                        "is_running": False,
                        "executable_available": bool(miner._find_executable(software.value))
                    }

            return status

        except Exception as e:
            logger.error(f"Failed to get mining status: {e}")
            return {"error": str(e)}

    async def optimize_mining(self) -> Dict[str, Any]:
        """Optimize mining settings."""
        try:
            if not self.active_miner:
                return {"error": "No active miner"}

            # Get current stats
            current_stats = await self.get_mining_status()
            current_miner = current_stats["miners"].get(self.active_miner.value, {})

            # Analyze profitability and efficiency
            recommendations = {
                "current_software": self.active_miner.value,
                "current_hashrate": current_miner.get("stats", {}).get("hashrate", 0),
                "current_efficiency": current_miner.get("stats", {}).get("efficiency", 0),
                "power_optimization": self._analyze_power_efficiency(current_miner),
                "temperature_analysis": self._analyze_temperatures(current_miner),
                "algorithm_recommendations": self._get_algorithm_recommendations(),
                "software_recommendations": self._get_software_recommendations()
            }

            return recommendations

        except Exception as e:
            logger.error(f"Failed to optimize mining: {e}")
            return {"error": str(e)}

    def _start_optimization_task(self):
        """Start background optimization task."""
        if self.optimization_task:
            self.optimization_task.cancel()

        async def optimization_loop():
            while self.active_miner:
                try:
                    # Run optimization every 5 minutes
                    await asyncio.sleep(300)
                    await self.optimize_mining()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Optimization task error: {e}")

        self.optimization_task = asyncio.create_task(optimization_loop())

    def _analyze_power_efficiency(self, miner_stats: Dict) -> Dict[str, Any]:
        """Analyze power efficiency."""
        stats = miner_stats.get("stats", {})
        efficiency = stats.get("efficiency", 0)
        power = stats.get("power_consumption", 0)

        suggestions = []
        if efficiency < 0.5:  # Less than 0.5 MH/s per watt
            suggestions.append("Consider reducing intensity for better efficiency")
        if power > 500:  # High power consumption
            suggestions.append("High power consumption detected - consider undervolting")

        return {
            "efficiency": efficiency,
            "power_consumption": power,
            "suggestions": suggestions
        }

    def _analyze_temperatures(self, miner_stats: Dict) -> Dict[str, Any]:
        """Analyze GPU temperatures."""
        stats = miner_stats.get("stats", {})
        temperatures = stats.get("temperature", [])

        warnings = []
        if temperatures:
            max_temp = max(temperatures)
            avg_temp = sum(temperatures) / len(temperatures)

            if max_temp > 85:
                warnings.append(f"CRITICAL: GPU temperature {max_temp}°C is too high!")
            elif max_temp > 75:
                warnings.append(f"WARNING: GPU temperature {max_temp}°C is high")

            return {
                "max_temperature": max_temp,
                "average_temperature": avg_temp,
                "warnings": warnings,
                "gpu_count": len(temperatures)
            }

        return {"warnings": ["No temperature data available"]}

    def _get_algorithm_recommendations(self) -> List[Dict[str, Any]]:
        """Get algorithm profitability recommendations."""
        # This would query real profitability APIs
        return [
            {"algorithm": "kawpow", "coin": "RVN", "profitability": 2.5, "efficiency": "high"},
            {"algorithm": "autolykos2", "coin": "ERG", "profitability": 3.2, "efficiency": "medium"},
            {"algorithm": "ethash", "coin": "ETH", "profitability": 1.8, "efficiency": "low"}
        ]

    def _get_software_recommendations(self) -> List[Dict[str, Any]]:
        """Get software recommendations based on current setup."""
        return [
            {"software": "NPlusMiner", "advantages": ["AI optimization", "Built-in GUI", "Multi-rig management"]},
            {"software": "MultiPoolMiner", "advantages": ["Lightweight", "Fast switching", "Wide pool support"]}
        ]

    async def switch_miner(self, new_software: MiningSoftware) -> bool:
        """Switch to different mining software."""
        try:
            # Get current settings
            current_status = await self.get_mining_status()
            current_stats = current_status.get("miners", {}).get(
                self.active_miner.value if self.active_miner else "multipoolminer", {}
            )

            current_settings = {
                "algorithm": current_stats.get("stats", {}).get("algorithm", "kawpow"),
                "coin": current_stats.get("stats", {}).get("coin", "RVN"),
                "intensity": 100
            }

            # Stop current miner
            await self.stop_mining()

            # Start new miner with same settings
            success = await self.start_mining(
                software=new_software,
                **current_settings
            )

            if success:
                logger.info(f"Switched from {self.active_miner.value} to {new_software.value}")

            return success

        except Exception as e:
            logger.error(f"Failed to switch miner: {e}")
            return False

    async def get_profitability_data(self) -> Dict[str, Any]:
        """Get current profitability data."""
        # This would query real mining profitability APIs
        return {
            "timestamp": datetime.now().isoformat(),
            "algorithms": {
                "kawpow": {"rvn": 2.5, "profitability": 2.5, "difficulty": 150000},
                "autolykos2": {"erg": 3.2, "profitability": 3.2, "difficulty": 250000},
                "ethash": {"eth": 1.8, "profitability": 1.8, "difficulty": 500000}
            },
            "pools": {
                "NiceHash": {"fee": 0.02, "reliability": "high"},
                "MiningPoolHub": {"fee": 0.01, "reliability": "medium"},
                "2Miners": {"fee": 0.015, "reliability": "high"}
            }
        }

    async def create_mining_config(self,
                                 software: MiningSoftware,
                                 config: Dict[str, Any]) -> bool:
        """Create mining configuration file."""
        try:
            config_dir = Path("config/mining")
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / f"{software.value}.json"

            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Configuration saved to {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create config: {e}")
            return False
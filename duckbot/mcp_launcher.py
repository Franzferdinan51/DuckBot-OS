#!/usr/bin/env python3
"""
DuckBot MCP Launcher
Unified launcher for DuckBot's MCP server with external integrations
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# DuckBot imports
try:
    from integrations.mcp_server import mcp_server, start_mcp_server, stop_mcp_server
    from integrations.external_mcp_integration import (
        initialize_external_mcp_servers,
        stop_external_mcp_servers,
        get_external_mcp_status
    )
    from integrations.enhanced_mcp_integration import (
        initialize_enhanced_mcp,
        execute_enhanced_mcp_tool,
        get_enhanced_mcp_tools,
        get_enhanced_mcp_status
    )
    from core.logging_setup import setup_logging
    DUCKBOT_AVAILABLE = True
except ImportError as e:
    print(f"DuckBot imports failed: {e}")
    DUCKBOT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPLauncher:
    """Unified MCP launcher for DuckBot"""

    def __init__(self):
        self.running = False
        self.shutdown_requested = False
        self.launcher_config = self._load_launcher_config()
        self.server_stats = {
            "start_time": None,
            "tools_executed": 0,
            "errors_encountered": 0,
            "external_servers_connected": 0
        }

    def _load_launcher_config(self) -> dict:
        """Load launcher configuration"""
        config_path = Path(__file__).parent / "config" / "mcp_launcher_config.json"

        default_config = {
            "launcher": {
                "host": "127.0.0.1",
                "port": 8790,
                "enable_enhanced_integration": True,
                "enable_external_servers": True,
                "auto_start": True,
                "graceful_shutdown": True,
                "health_check_interval": 30
            },
            "startup_sequence": {
                "initialize_duckbot_mcp": True,
                "initialize_external_servers": True,
                "initialize_enhanced_integration": True,
                "health_check_delay": 5
            },
            "monitoring": {
                "enable_metrics": True,
                "metrics_interval": 60,
                "log_performance": True,
                "alert_thresholds": {
                    "error_rate": 0.1,
                    "response_time": 5000,
                    "memory_usage": 0.8
                }
            },
            "features": {
                "unified_tools": True,
                "fallback_handling": True,
                "cross_server_communication": True,
                "ai_enhancement": True
            }
        }

        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default config
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default launcher configuration at {config_path}")
                return default_config
        except Exception as e:
            logger.error(f"Failed to load launcher configuration: {e}")
            return default_config

    async def start(self):
        """Start the MCP launcher"""
        logger.info("Starting DuckBot MCP Launcher...")
        self.running = True
        self.server_stats["start_time"] = datetime.now()

        try:
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Execute startup sequence
            await self._execute_startup_sequence()

            # Start monitoring if enabled
            if self.launcher_config["monitoring"]["enable_metrics"]:
                asyncio.create_task(self._monitoring_loop())

            logger.info("DuckBot MCP Launcher started successfully")

            # Keep the launcher running
            while not self.shutdown_requested:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"MCP Launcher error: {e}")
            raise
        finally:
            await self._graceful_shutdown()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            logger.info("Signal handlers configured")
        except Exception as e:
            logger.warning(f"Failed to setup signal handlers: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    async def _execute_startup_sequence(self):
        """Execute the configured startup sequence"""
        sequence = self.launcher_config["startup_sequence"]
        logger.info("Executing startup sequence...")

        # Initialize DuckBot MCP server
        if sequence["initialize_duckbot_mcp"] and DUCKBOT_AVAILABLE:
            try:
                logger.info("Initializing DuckBot MCP server...")
                await mcp_server.initialize_mcp_server()

                # Start DuckBot MCP server in background
                host = self.launcher_config["launcher"]["host"]
                port = self.launcher_config["launcher"]["port"]
                asyncio.create_task(self._start_duckbot_mcp_server(host, port))
                logger.info("DuckBot MCP server initialization completed")
            except Exception as e:
                logger.error(f"Failed to initialize DuckBot MCP server: {e}")

        # Initialize external MCP servers
        if sequence["initialize_external_servers"]:
            try:
                logger.info("Initializing external MCP servers...")
                await initialize_external_mcp_servers()
                external_status = get_external_mcp_status()
                connected_servers = sum(1 for s in external_status.values() if s.get("status") == "running")
                self.server_stats["external_servers_connected"] = connected_servers
                logger.info(f"External MCP servers initialized: {connected_servers} connected")
            except Exception as e:
                logger.error(f"Failed to initialize external MCP servers: {e}")

        # Initialize enhanced integration
        if sequence["initialize_enhanced_integration"]:
            try:
                logger.info("Initializing enhanced MCP integration...")
                await initialize_enhanced_mcp()
                enhanced_status = get_enhanced_mcp_status()
                logger.info(f"Enhanced MCP integration initialized: {enhanced_status}")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced MCP integration: {e}")

        # Wait for health check delay
        await asyncio.sleep(sequence["health_check_delay"])

        # Perform initial health check
        await self._health_check()

    async def _start_duckbot_mcp_server(self, host: str, port: int):
        """Start DuckBot MCP server"""
        try:
            await start_mcp_server(host, port)
            logger.info(f"DuckBot MCP server started on {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to start DuckBot MCP server: {e}")

    async def _health_check(self):
        """Perform health check on all MCP components"""
        logger.info("Performing health check...")

        try:
            # Check DuckBot MCP server
            if DUCKBOT_AVAILABLE:
                duckbot_status = mcp_server.get_status()
                logger.info(f"DuckBot MCP server status: {duckbot_status}")

            # Check external servers
            external_status = get_external_mcp_status()
            running_external = sum(1 for s in external_status.values() if s.get("status") == "running")
            logger.info(f"External MCP servers: {running_external} running")

            # Check enhanced integration
            enhanced_status = get_enhanced_mcp_status()
            logger.info(f"Enhanced MCP integration: {enhanced_status}")

            # Update statistics
            self.server_stats["external_servers_connected"] = running_external

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    async def _monitoring_loop(self):
        """Monitoring loop for metrics and health checks"""
        monitoring_config = self.launcher_config["monitoring"]
        interval = monitoring_config["metrics_interval"]

        logger.info(f"Starting monitoring loop (interval: {interval}s)")

        while self.running and not self.shutdown_requested:
            try:
                await asyncio.sleep(interval)

                if not self.running:
                    break

                # Collect metrics
                metrics = await self._collect_metrics()

                # Log performance if enabled
                if monitoring_config["log_performance"]:
                    logger.info(f"Performance metrics: {metrics}")

                # Check alert thresholds
                await self._check_alert_thresholds(metrics)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

    async def _collect_metrics(self) -> dict:
        """Collect performance metrics"""
        try:
            import psutil

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                },
                "mcp": {
                    "tools_executed": self.server_stats["tools_executed"],
                    "errors_encountered": self.server_stats["errors_encountered"],
                    "external_servers_connected": self.server_stats["external_servers_connected"]
                }
            }

            # Add uptime
            if self.server_stats["start_time"]:
                uptime = datetime.now() - self.server_stats["start_time"]
                metrics["uptime_seconds"] = uptime.total_seconds()

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}

    async def _check_alert_thresholds(self, metrics: dict):
        """Check alert thresholds"""
        try:
            thresholds = self.launcher_config["monitoring"]["alert_thresholds"]

            # Check error rate
            if self.server_stats["tools_executed"] > 0:
                error_rate = self.server_stats["errors_encountered"] / self.server_stats["tools_executed"]
                if error_rate > thresholds["error_rate"]:
                    logger.warning(f"High error rate detected: {error_rate:.2%}")

            # Check response time (would need to track actual response times)
            # This is a placeholder for actual response time tracking

            # Check memory usage
            if "system" in metrics and "memory_usage" in metrics["system"]:
                memory_usage = metrics["system"]["memory_usage"] / 100
                if memory_usage > thresholds["memory_usage"]:
                    logger.warning(f"High memory usage detected: {memory_usage:.2%}")

        except Exception as e:
            logger.error(f"Failed to check alert thresholds: {e}")

    async def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Initiating graceful shutdown...")

        try:
            # Stop external MCP servers
            if self.launcher_config["launcher"]["enable_external_servers"]:
                try:
                    logger.info("Stopping external MCP servers...")
                    await stop_external_mcp_servers()
                    logger.info("External MCP servers stopped")
                except Exception as e:
                    logger.error(f"Failed to stop external MCP servers: {e}")

            # Stop DuckBot MCP server
            if DUCKBOT_AVAILABLE:
                try:
                    logger.info("Stopping DuckBot MCP server...")
                    await stop_mcp_server()
                    logger.info("DuckBot MCP server stopped")
                except Exception as e:
                    logger.error(f"Failed to stop DuckBot MCP server: {e}")

            logger.info("Graceful shutdown completed")

        except Exception as e:
            logger.error(f"Graceful shutdown failed: {e}")

    def get_launcher_status(self) -> dict:
        """Get launcher status and statistics"""
        return {
            "running": self.running,
            "shutdown_requested": self.shutdown_requested,
            "stats": self.server_stats,
            "config": self.launcher_config,
            "duckbot_available": DUCKBOT_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }

    def get_available_tools(self) -> dict:
        """Get all available tools from all MCP integrations"""
        tools = {}

        # DuckBot MCP tools
        if DUCKBOT_AVAILABLE:
            try:
                duckbot_tools = await mcp_server.get_mcp_tools()
                tools["duckbot"] = duckbot_tools
            except Exception as e:
                logger.error(f"Failed to get DuckBot tools: {e}")

        # External MCP tools
        try:
            from integrations.external_mcp_integration import get_external_mcp_tools
            external_tools = get_external_mcp_tools()
            tools["external"] = external_tools
        except Exception as e:
            logger.error(f"Failed to get external MCP tools: {e}")

        # Enhanced MCP tools
        try:
            enhanced_tools = get_enhanced_mcp_tools()
            tools["enhanced"] = enhanced_tools
        except Exception as e:
            logger.error(f"Failed to get enhanced MCP tools: {e}")

        return tools

# Global launcher instance
mcp_launcher = MCPLauncher()

# Convenience functions
async def start_mcp_launcher():
    """Start the MCP launcher"""
    await mcp_launcher.start()

async def stop_mcp_launcher():
    """Stop the MCP launcher"""
    mcp_launcher.shutdown_requested = True
    await mcp_launcher._graceful_shutdown()

def get_mcp_launcher_status():
    """Get MCP launcher status"""
    return mcp_launcher.get_launcher_status()

async def get_mcp_tools():
    """Get all available MCP tools"""
    return await mcp_launcher.get_available_tools()

if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            print("Starting DuckBot MCP Launcher...")
            await start_mcp_launcher()
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
            await stop_mcp_launcher()
        except Exception as e:
            print(f"Fatal error: {e}")
            await stop_mcp_launcher()
            sys.exit(1)

    asyncio.run(main())
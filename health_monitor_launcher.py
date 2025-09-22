#!/usr/bin/env python3
"""
Health Monitor Startup Script for Electron Launcher
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def run_health_monitor():
    try:
        from duckbot.core.health_monitor import get_health_monitor

        monitor = get_health_monitor()
        await monitor.start_monitoring()
        print("Health monitor started successfully", flush=True)

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await monitor.stop_monitoring()

    except ImportError as e:
        print(f"Failed to import health monitor: {e}", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"Health monitor error: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_health_monitor())
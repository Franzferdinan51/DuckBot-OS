#!/usr/bin/env python3
"""
Real-time Server Monitor for DuckBot Electron Launcher
Monitors server startup, port allocation, WebSocket connectivity, and service health
"""

import asyncio
import json
import logging
import websockets
import aiohttp
import time
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerMonitor:
    def __init__(self):
        self.monitoring = True
        self.start_time = time.time()
        self.port_status = {}
        self.service_status = {}
        self.websocket_status = {}
        self.process_status = {}

    async def monitor_ports(self):
        """Monitor port usage and allocation"""
        ports_to_watch = [8791, 8792, 8793, 8787, 8788, 3000, 5000, 8000]

        while self.monitoring:
            for port in ports_to_watch:
                try:
                    # Check if port is in use
                    for conn in psutil.net_connections():
                        if conn.laddr.port == port:
                            process_name = "Unknown"
                            if conn.pid:
                                try:
                                    process = psutil.Process(conn.pid)
                                    process_name = process.name()
                                except:
                                    pass

                            status = {
                                "port": port,
                                "status": "in_use",
                                "process": process_name,
                                "pid": conn.pid,
                                "timestamp": datetime.now().isoformat()
                            }

                            if port not in self.port_status or self.port_status[port] != status:
                                self.port_status[port] = status
                                logger.info(f"🔌 Port Monitor: {status}")
                            break
                    else:
                        # Port is available
                        status = {
                            "port": port,
                            "status": "available",
                            "timestamp": datetime.now().isoformat()
                        }

                        if port not in self.port_status or self.port_status[port]["status"] != "available":
                            self.port_status[port] = status
                            logger.info(f"🔌 Port Monitor: Port {port} is now available")

                except Exception as e:
                    logger.error(f"Port monitoring error for {port}: {e}")

            await asyncio.sleep(2)

    async def monitor_websocket_connectivity(self):
        """Monitor WebSocket server connectivity"""
        websocket_ports = [8791, 8792, 8793]

        while self.monitoring:
            for port in websocket_ports:
                try:
                    # Test WebSocket connection
                    uri = f"ws://localhost:{port}"
                    async with websockets.connect(uri, timeout=3) as websocket:
                        # Send ping
                        await websocket.send(json.dumps({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        }))

                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=3)
                        data = json.loads(response)

                        status = {
                            "port": port,
                            "status": "connected",
                            "response": data,
                            "timestamp": datetime.now().isoformat()
                        }

                        if port not in self.websocket_status or self.websocket_status[port].get("status") != "connected":
                            self.websocket_status[port] = status
                            logger.info(f"🌐 WebSocket Monitor: Connected to port {port} - {data.get('type', 'unknown')}")

                except Exception as e:
                    status = {
                        "port": port,
                        "status": "disconnected",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

                    if port not in self.websocket_status or self.websocket_status[port].get("status") != "disconnected":
                        self.websocket_status[port] = status
                        logger.warning(f"🌐 WebSocket Monitor: Port {port} disconnected - {e}")

            await asyncio.sleep(5)

    async def monitor_http_endpoints(self):
        """Monitor HTTP endpoint availability"""
        endpoints = [
            ("http://localhost:8787", "Enhanced WebUI"),
            ("http://localhost:8788", "Monitoring Dashboard"),
            ("http://localhost:3000", "React Dev Server"),
            ("http://localhost:5000", "Development Server")
        ]

        while self.monitoring:
            for url, service_name in endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=3) as response:
                            status = {
                                "service": service_name,
                                "url": url,
                                "status": "online",
                                "status_code": response.status,
                                "timestamp": datetime.now().isoformat()
                            }

                            if service_name not in self.service_status or self.service_status[service_name].get("status") != "online":
                                self.service_status[service_name] = status
                                logger.info(f"🌍 HTTP Monitor: {service_name} is online (HTTP {response.status})")

                except Exception as e:
                    status = {
                        "service": service_name,
                        "url": url,
                        "status": "offline",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

                    if service_name not in self.service_status or self.service_status[service_name].get("status") != "offline":
                        self.service_status[service_name] = status
                        logger.warning(f"🌍 HTTP Monitor: {service_name} is offline - {e}")

            await asyncio.sleep(10)

    async def monitor_processes(self):
        """Monitor relevant processes"""
        process_names = ["python.exe", "python3.exe", "python3.11.exe", "electron.exe", "node.exe"]

        while self.monitoring:
            for proc_name in process_names:
                try:
                    count = 0
                    processes = []

                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] == proc_name:
                                count += 1
                                processes.append({
                                    "pid": proc.info['pid'],
                                    "cmdline": ' '.join(proc.info['cmdline'][:3]) if proc.info['cmdline'] else ''
                                })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    status = {
                        "process": proc_name,
                        "count": count,
                        "processes": processes[:3],  # Limit to first 3 processes
                        "timestamp": datetime.now().isoformat()
                    }

                    if proc_name not in self.process_status or self.process_status[proc_name]["count"] != count:
                        self.process_status[proc_name] = status
                        if count > 0:
                            logger.info(f"⚙️ Process Monitor: {count} {proc_name} processes running")
                        else:
                            logger.info(f"⚙️ Process Monitor: No {proc_name} processes running")

                except Exception as e:
                    logger.error(f"Process monitoring error for {proc_name}: {e}")

            await asyncio.sleep(5)

    async def monitor_system_resources(self):
        """Monitor system resource usage"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                status = {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": f"{memory.available / (1024**3):.2f} GB",
                    "disk_percent": disk.percent,
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"📊 System Resources: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {disk.percent}%")

                # Alert if resources are high
                if cpu_percent > 80:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
                if memory.percent > 80:
                    logger.warning(f"⚠️ High Memory usage: {memory.percent}%")
                if disk.percent > 80:
                    logger.warning(f"⚠️ High Disk usage: {disk.percent}%")

            except Exception as e:
                logger.error(f"System resource monitoring error: {e}")

            await asyncio.sleep(10)

    async def display_status_summary(self):
        """Display periodic status summary"""
        while self.monitoring:
            await asyncio.sleep(30)  # Show summary every 30 seconds

            logger.info("=" * 60)
            logger.info("📊 SERVER MONITORING STATUS SUMMARY")
            logger.info("=" * 60)

            # Port Status Summary
            logger.info("🔌 Port Status:")
            for port, status in self.port_status.items():
                emoji = "🟢" if status["status"] == "available" else "🔴"
                process_info = f" ({status['process']})" if status.get("process") else ""
                logger.info(f"  {emoji} Port {port}: {status['status']}{process_info}")

            # WebSocket Status Summary
            logger.info("🌐 WebSocket Status:")
            for port, status in self.websocket_status.items():
                emoji = "🟢" if status["status"] == "connected" else "🔴"
                logger.info(f"  {emoji} Port {port}: {status['status']}")

            # Service Status Summary
            logger.info("🌍 Service Status:")
            for service, status in self.service_status.items():
                emoji = "🟢" if status["status"] == "online" else "🔴"
                logger.info(f"  {emoji} {service}: {status['status']}")

            # Process Summary
            logger.info("⚙️ Process Count:")
            for proc_name, status in self.process_status.items():
                if status["count"] > 0:
                    logger.info(f"  📋 {proc_name}: {status['count']} processes")

            # Runtime
            runtime = time.time() - self.start_time
            logger.info(f"⏱️ Monitoring Runtime: {runtime:.1f} seconds")
            logger.info("=" * 60)

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        logger.info("🚀 Starting comprehensive server monitoring...")
        logger.info("📊 Monitoring will watch:")
        logger.info("   - Port allocation and conflicts")
        logger.info("   - WebSocket connectivity")
        logger.info("   - HTTP endpoint availability")
        logger.info("   - Process management")
        logger.info("   - System resources")
        logger.info("   - Service health and recovery")
        logger.info("Press Ctrl+C to stop monitoring...")

        # Start all monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_ports()),
            asyncio.create_task(self.monitor_websocket_connectivity()),
            asyncio.create_task(self.monitor_http_endpoints()),
            asyncio.create_task(self.monitor_processes()),
            asyncio.create_task(self.monitor_system_resources()),
            asyncio.create_task(self.display_status_summary())
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            self.monitoring = False
            # Cancel all tasks
            for task in tasks:
                task.cancel()

async def main():
    """Main function"""
    monitor = ServerMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
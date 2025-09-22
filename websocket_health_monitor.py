#!/usr/bin/env python3
"""
DuckBot WebSocket Health Monitor
Provides comprehensive health monitoring and diagnostics for WebSocket services
"""

import asyncio
import json
import logging
import websockets
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import port allocation
try:
    from config.port_allocation import DUCKBOT_WEBSOCKET_MCP_PORT, DUCKBOT_WEBSOCKET_CHAT_PORT, DUCKBOT_MCP_SERVER_PORT
except ImportError:
    # Fallback values
    DUCKBOT_WEBSOCKET_MCP_PORT = 8791
    DUCKBOT_WEBSOCKET_CHAT_PORT = 8792
    DUCKBOT_MCP_SERVER_PORT = 8794

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WebSocketHealth:
    """WebSocket service health status"""
    service_name: str
    url: str
    status: str = "unknown"
    response_time: float = 0.0
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    connection_count: int = 0
    uptime_seconds: float = 0.0
    message_count: int = 0

@dataclass
class ServiceHealth:
    """General service health status"""
    service_name: str
    port: int
    protocol: str
    status: str = "unknown"
    response_time: float = 0.0
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    health_endpoint: Optional[str] = None

class WebSocketHealthMonitor:
    """Monitors WebSocket and related service health"""

    def __init__(self):
        self.websocket_services = {
            "mcp_websocket": WebSocketHealth(
                service_name="MCP WebSocket",
                url=f"ws://localhost:{DUCKBOT_WEBSOCKET_MCP_PORT}"
            ),
            "chat_websocket": WebSocketHealth(
                service_name="Chat WebSocket",
                url=f"ws://localhost:{DUCKBOT_WEBSOCKET_CHAT_PORT}"
            )
        }

        self.http_services = {
            "mcp_server": ServiceHealth(
                service_name="MCP Server",
                port=DUCKBOT_MCP_SERVER_PORT,
                protocol="http",
                health_endpoint=f"http://localhost:{DUCKBOT_MCP_SERVER_PORT}/health"
            ),
            "webui": ServiceHealth(
                service_name="WebUI",
                port=8787,
                protocol="http",
                health_endpoint="http://localhost:8787/health"
            ),
            "monitoring": ServiceHealth(
                service_name="Monitoring",
                port=8789,
                protocol="http",
                health_endpoint="http://localhost:8789/health"
            )
        }

        self.start_time = time.time()
        self.monitoring_active = False
        self.health_history = []

    async def check_websocket_health(self, service_name: str) -> bool:
        """Check health of a WebSocket service"""
        if service_name not in self.websocket_services:
            logger.error(f"Unknown WebSocket service: {service_name}")
            return False

        service = self.websocket_services[service_name]
        start_time = time.time()

        try:
            # Attempt to connect to WebSocket
            async with websockets.connect(service.url, timeout=5) as websocket:
                # Send ping message
                ping_message = json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
                await websocket.send(ping_message)

                # Wait for pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)

                # Update health status
                service.response_time = time.time() - start_time
                service.last_check = datetime.now()
                service.status = "healthy"
                service.error_message = None
                service.message_count += 1

                # Update uptime
                if service.uptime_seconds == 0:
                    service.uptime_seconds = time.time() - self.start_time

                logger.debug(f"WebSocket {service_name} health check passed in {service.response_time:.3f}s")
                return True

        except websockets.exceptions.ConnectionClosed:
            service.status = "disconnected"
            service.error_message = "Connection closed"
            service.last_check = datetime.now()
            logger.warning(f"WebSocket {service_name} connection closed")
            return False

        except asyncio.TimeoutError:
            service.status = "timeout"
            service.error_message = "Connection timeout"
            service.last_check = datetime.now()
            logger.warning(f"WebSocket {service_name} connection timeout")
            return False

        except Exception as e:
            service.status = "error"
            service.error_message = str(e)
            service.last_check = datetime.now()
            logger.error(f"WebSocket {service_name} health check failed: {e}")
            return False

    async def check_http_service_health(self, service_name: str) -> bool:
        """Check health of an HTTP service"""
        if service_name not in self.http_services:
            logger.error(f"Unknown HTTP service: {service_name}")
            return False

        service = self.http_services[service_name]
        start_time = time.time()

        try:
            # Check if service is reachable
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                if service.health_endpoint:
                    # Try health endpoint first
                    async with session.get(service.health_endpoint) as response:
                        if response.status == 200:
                            try:
                                health_data = await response.json()
                                service.status = health_data.get("status", "healthy")
                            except:
                                service.status = "healthy"
                        else:
                            service.status = "degraded"
                            service.error_message = f"HTTP {response.status}"
                else:
                    # Just check if port is reachable
                    test_url = f"http://localhost:{service.port}"
                    async with session.get(test_url) as response:
                        service.status = "healthy" if response.status < 500 else "degraded"

                service.response_time = time.time() - start_time
                service.last_check = datetime.now()
                service.error_message = None

                logger.debug(f"HTTP service {service_name} health check passed in {service.response_time:.3f}s")
                return True

        except aiohttp.ClientError as e:
            service.status = "unreachable"
            service.error_message = str(e)
            service.last_check = datetime.now()
            logger.warning(f"HTTP service {service_name} unreachable: {e}")
            return False

        except Exception as e:
            service.status = "error"
            service.error_message = str(e)
            service.last_check = datetime.now()
            logger.error(f"HTTP service {service_name} health check failed: {e}")
            return False

    async def check_all_services(self) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}

        # Check WebSocket services
        for service_name in self.websocket_services:
            results[f"websocket_{service_name}"] = await self.check_websocket_health(service_name)

        # Check HTTP services
        for service_name in self.http_services:
            results[f"http_{service_name}"] = await self.check_http_service_health(service_name)

        # Record health snapshot
        self._record_health_snapshot(results)

        return results

    def _record_health_snapshot(self, results: Dict[str, bool]):
        """Record a health snapshot for trend analysis"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total_services": len(results),
                "healthy_services": sum(results.values()),
                "unhealthy_services": len(results) - sum(results.values())
            }
        }

        self.health_history.append(snapshot)

        # Keep only last 100 snapshots
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

    async def start_monitoring(self, check_interval: int = 30):
        """Start continuous health monitoring"""
        self.monitoring_active = True
        logger.info(f"Starting WebSocket health monitoring (interval: {check_interval}s)")

        try:
            while self.monitoring_active:
                results = await self.check_all_services()

                # Log summary
                healthy_count = sum(results.values())
                total_count = len(results)
                health_percentage = (healthy_count / total_count) * 100 if total_count > 0 else 0

                logger.info(f"Health check: {healthy_count}/{total_count} services healthy ({health_percentage:.1f}%)")

                # Log any unhealthy services
                for service, is_healthy in results.items():
                    if not is_healthy:
                        service_type, service_name = service.split('_', 1)
                        if service_type == "websocket":
                            service_info = self.websocket_services.get(service_name)
                        else:
                            service_info = self.http_services.get(service_name)

                        if service_info:
                            logger.warning(f"Unhealthy service: {service_info.service_name} - {service_info.error_message}")

                # Wait for next check
                await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            logger.info("Health monitoring stopped")
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")

    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("Health monitoring stopped")

    def get_health_summary(self) -> Dict:
        """Get current health summary"""
        all_services = {**self.websocket_services, **self.http_services}

        healthy_count = sum(1 for s in all_services.values() if s.status == "healthy")
        total_count = len(all_services)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_services": total_count,
            "healthy_services": healthy_count,
            "unhealthy_services": total_count - healthy_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "monitoring_uptime": time.time() - self.start_time,
            "services": {name: asdict(service) for name, service in all_services.items()}
        }

    def get_health_trends(self, hours: int = 24) -> Dict:
        """Get health trends over specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [
            s for s in self.health_history
            if datetime.fromisoformat(s["timestamp"]) > cutoff_time
        ]

        if not recent_snapshots:
            return {"error": "No data available for the specified time range"}

        trends = {
            "time_range_hours": hours,
            "snapshot_count": len(recent_snapshots),
            "health_percentages": [s["summary"]["healthy_services"] / s["summary"]["total_services"] * 100 for s in recent_snapshots],
            "average_health_percentage": sum(s["summary"]["healthy_services"] / s["summary"]["total_services"] * 100 for s in recent_snapshots) / len(recent_snapshots),
            "min_health_percentage": min(s["summary"]["healthy_services"] / s["summary"]["total_services"] * 100 for s in recent_snapshots),
            "max_health_percentage": max(s["summary"]["healthy_services"] / s["summary"]["total_services"] * 100 for s in recent_snapshots)
        }

        return trends

    async def generate_health_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive health report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "monitoring_info": {
                "uptime_seconds": time.time() - self.start_time,
                "monitoring_active": self.monitoring_active,
                "health_snapshots_recorded": len(self.health_history)
            },
            "current_status": self.get_health_summary(),
            "health_trends": self.get_health_trends(),
            "configuration": {
                "websocket_mcp_port": DUCKBOT_WEBSOCKET_MCP_PORT,
                "websocket_chat_port": DUCKBOT_WEBSOCKET_CHAT_PORT,
                "mcp_server_port": DUCKBOT_MCP_SERVER_PORT
            }
        }

        report_json = json.dumps(report, indent=2, default=str)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_json)
            logger.info(f"Health report saved to {output_file}")

        return report_json

async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='DuckBot WebSocket Health Monitor')
    parser.add_argument('--interval', type=int, default=30, help='Health check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run health check once and exit')
    parser.add_argument('--report', help='Generate health report to file')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')

    args = parser.parse_args()

    monitor = WebSocketHealthMonitor()

    try:
        if args.once:
            # Run single health check
            results = await monitor.check_all_services()
            print(f"Health check results: {results}")
            summary = monitor.get_health_summary()
            print(f"Summary: {summary['healthy_services']}/{summary['total_services']} services healthy")

        elif args.report:
            # Generate report
            report = await monitor.generate_health_report(args.report)
            print(f"Health report generated: {args.report}")

        elif args.monitor:
            # Start continuous monitoring
            await monitor.start_monitoring(args.interval)

        else:
            # Default: run one check and show summary
            results = await monitor.check_all_services()
            summary = monitor.get_health_summary()

            print("=== DuckBot WebSocket Health Summary ===")
            print(f"Time: {summary['timestamp']}")
            print(f"Health: {summary['healthy_services']}/{summary['total_services']} services ({summary['health_percentage']:.1f}%)")
            print(f"Monitoring uptime: {summary['monitoring_uptime']:.1f}s")
            print()

            print("Service Status:")
            for service_name, service_info in summary['services'].items():
                status_icon = "✅" if service_info['status'] == 'healthy' else "❌"
                print(f"  {status_icon} {service_info['service_name']}: {service_info['status']}")
                if service_info['error_message']:
                    print(f"     Error: {service_info['error_message']}")

    except KeyboardInterrupt:
        print("\n👋 Health monitor stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
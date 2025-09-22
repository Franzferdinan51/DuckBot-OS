#!/usr/bin/env python3
"""
Enhanced DuckBot Monitoring Dashboard
Real-time web dashboard with comprehensive monitoring capabilities
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
from pathlib import Path

import fastapi
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel

# Local imports
from duckbot.core.monitoring_system import (
    get_monitoring, DuckBotMonitoring, AlertLevel, HealthStatus
)
from duckbot.services.server_manager import server_manager, ServiceStatus
from duckbot.core.hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

# Pydantic models for API
class AlertRule(BaseModel):
    name: str
    condition: str
    level: str
    message: str
    enabled: bool = True

class SystemMetrics(BaseModel):
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: float
    network_bytes_recv: float
    process_count: int

class AgentMetrics(BaseModel):
    agent_id: str
    agent_type: str
    total_requests: int
    success_rate: float
    avg_response_time: float
    last_activity: str

class ServiceHealth(BaseModel):
    service_name: str
    display_name: str
    status: str
    response_time_ms: float
    last_check: str
    error_message: str = ""

class DashboardData(BaseModel):
    system_metrics: SystemMetrics
    services: List[ServiceHealth]
    agents: List[AgentMetrics]
    alerts: List[Dict]
    user_activity: Dict
    timestamp: str

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Connection might be closed
                pass

class EnhancedMonitoringDashboard:
    """Enhanced monitoring dashboard with real-time capabilities"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8790):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="DuckBot Enhanced Monitoring Dashboard",
            description="Real-time monitoring and analytics for DuckBot",
            version="1.0.0"
        )

        self.connection_manager = ConnectionManager()
        self.monitoring = get_monitoring()
        self.hardware_detector = HardwareDetector()

        # Setup static files and templates
        self._setup_static_files()

        # Setup routes
        self._setup_routes()

        # Background task for real-time updates
        self.update_task = None

    def _setup_static_files(self):
        """Setup static file serving"""
        # Create templates directory if it doesn't exist
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)

        # Create static directory if it doesn't exist
        static_dir = Path(__file__).parent / "static"
        static_dir.mkdir(exist_ok=True)

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Setup templates
        self.templates = Jinja2Templates(directory=str(templates_dir))

    def _setup_routes(self):
        """Setup all API routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: fastapi.Request):
            """Main dashboard page"""
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "DuckBot Monitoring Dashboard",
                "version": "1.0.0"
            })

        @self.app.get("/api/status")
        async def get_system_status():
            """Get current system status"""
            try:
                status = self.monitoring.get_system_status()
                return JSONResponse(content=status)
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/metrics/system")
        async def get_system_metrics(
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            limit: int = 100
        ):
            """Get system metrics history"""
            try:
                start_dt = datetime.fromisoformat(start_time) if start_time else datetime.now() - timedelta(hours=1)
                end_dt = datetime.fromisoformat(end_time) if end_time else datetime.now()

                metrics = self.monitoring.database.get_system_metrics(
                    start_time=start_dt,
                    end_time=end_dt,
                    limit=limit
                )

                return JSONResponse(content={"metrics": metrics})
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/metrics/agents")
        async def get_agent_metrics(agent_id: Optional[str] = None):
            """Get agent performance metrics"""
            try:
                metrics = self.monitoring.agent_monitor.get_agent_performance_summary(agent_id)
                return JSONResponse(content={"metrics": metrics})
            except Exception as e:
                logger.error(f"Error getting agent metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/services")
        async def get_service_status():
            """Get status of all services"""
            try:
                services = server_manager.get_all_service_status()
                service_data = {}

                for name, info in services.items():
                    service_data[name] = {
                        "name": name,
                        "display_name": info.display_name,
                        "status": info.status.value,
                        "port": info.port,
                        "url": info.url,
                        "pid": info.pid,
                        "last_updated": datetime.now().isoformat()
                    }

                return JSONResponse(content={"services": service_data})
            except Exception as e:
                logger.error(f"Error getting service status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/alerts")
        async def get_alerts(active_only: bool = True):
            """Get alerts"""
            try:
                if active_only:
                    alerts = self.monitoring.database.get_active_alerts()
                else:
                    # Get all alerts (need to implement this method)
                    alerts = []

                return JSONResponse(content={"alerts": alerts})
            except Exception as e:
                logger.error(f"Error getting alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve an alert"""
            try:
                self.monitoring.alert_manager.resolve_alert(alert_id)
                return JSONResponse(content={"message": "Alert resolved"})
            except Exception as e:
                logger.error(f"Error resolving alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/activity")
        async def get_user_activity(hours: int = 24):
            """Get user activity summary"""
            try:
                activity = self.monitoring.user_activity_tracker.get_activity_summary(hours)
                return JSONResponse(content={"activity": activity})
            except Exception as e:
                logger.error(f"Error getting user activity: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/hardware")
        async def get_hardware_info():
            """Get hardware information"""
            try:
                hardware = self.hardware_detector.detect_all_hardware()
                return JSONResponse(content={"hardware": hardware})
            except Exception as e:
                logger.error(f"Error getting hardware info: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    # Send real-time updates
                    data = await self._get_dashboard_data()
                    await websocket.send_text(json.dumps(data))
                    await asyncio.sleep(5)  # Update every 5 seconds
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)

        @self.app.post("/api/services/{service_name}/start")
        async def start_service(service_name: str):
            """Start a service"""
            try:
                success, message = server_manager.start_service(service_name)
                return JSONResponse(content={"success": success, "message": message})
            except Exception as e:
                logger.error(f"Error starting service {service_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/services/{service_name}/stop")
        async def stop_service(service_name: str):
            """Stop a service"""
            try:
                success, message = server_manager.stop_service(service_name)
                return JSONResponse(content={"success": success, "message": message})
            except Exception as e:
                logger.error(f"Error stopping service {service_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/services/{service_name}/restart")
        async def restart_service(service_name: str):
            """Restart a service"""
            try:
                success, message = server_manager.restart_service(service_name)
                return JSONResponse(content={"success": success, "message": message})
            except Exception as e:
                logger.error(f"Error restarting service {service_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/config")
        async def get_dashboard_config():
            """Get dashboard configuration"""
            config = {
                "update_interval": 5,
                "metrics_retention_days": 30,
                "alert_retention_days": 90,
                "max_metrics_points": 1000,
                "features": {
                    "real_time_updates": True,
                    "service_control": True,
                    "alert_management": True,
                    "export_data": True,
                    "hardware_monitoring": True,
                    "agent_monitoring": True,
                    "user_analytics": True
                }
            }
            return JSONResponse(content=config)

    async def _get_dashboard_data(self) -> Dict:
        """Get current dashboard data"""
        try:
            status = self.monitoring.get_system_status()

            # Get service status
            services = []
            service_status = server_manager.get_all_service_status()
            for name, info in service_status.items():
                services.append(ServiceHealth(
                    service_name=name,
                    display_name=info.display_name,
                    status=info.status.value,
                    response_time_ms=0.0,  # TODO: Get actual response time
                    last_check=datetime.now().isoformat()
                ).dict())

            # Get agent metrics
            agents = []
            agent_metrics = self.monitoring.agent_monitor.get_agent_performance_summary()
            for agent_id, metrics in agent_metrics.items():
                agents.append(AgentMetrics(
                    agent_id=agent_id,
                    agent_type=metrics.get("agent_type", "unknown"),
                    total_requests=metrics.get("total_requests", 0),
                    success_rate=metrics.get("successful_requests", 0) / max(metrics.get("total_requests", 1), 1),
                    avg_response_time=metrics.get("avg_response_time", 0),
                    last_activity=metrics.get("last_activity", "").isoformat() if metrics.get("last_activity") else ""
                ).dict())

            return {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": status.get("system_metrics", {}),
                "services": services,
                "agents": agents,
                "alerts": status.get("alerts", {}),
                "user_activity": status.get("user_activity", {})
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def start_real_time_updates(self):
        """Start background task for real-time updates"""
        while True:
            try:
                data = await self._get_dashboard_data()
                await self.connection_manager.broadcast(data)
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error in real-time updates: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    def start(self):
        """Start the monitoring dashboard"""
        logger.info(f"Starting Enhanced Monitoring Dashboard on {self.host}:{self.port}")

        # Start monitoring system
        self.monitoring.start(metrics_interval=2.0, health_check_interval=15.0)

        # Start real-time updates
        self.update_task = asyncio.create_task(self.start_real_time_updates())

        # Create dashboard UI files
        self._create_dashboard_files()

        # Start server
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            reload=False
        )

    def _create_dashboard_files(self):
        """Create dashboard HTML and static files"""
        templates_dir = Path(__file__).parent / "templates"
        static_dir = Path(__file__).parent / "static"

        # Create main dashboard HTML
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckBot Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .metric-card {
            @apply bg-white rounded-lg shadow-md p-6;
        }
        .status-healthy { @apply text-green-600 bg-green-100; }
        .status-warning { @apply text-yellow-600 bg-yellow-100; }
        .status-error { @apply text-red-600 bg-red-100; }
        .status-unknown { @apply text-gray-600 bg-gray-100; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">
                <i class="fas fa-tachometer-alt mr-2"></i>
                DuckBot Monitoring Dashboard
            </h1>
            <div class="flex items-center space-x-4">
                <span id="connection-status" class="flex items-center">
                    <i class="fas fa-circle text-green-400 mr-1"></i>
                    Connected
                </span>
                <span id="last-update" class="text-sm"></span>
            </div>
        </div>
    </nav>

    <div class="container mx-auto p-6">
        <!-- System Overview -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div class="metric-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-600 text-sm">CPU Usage</p>
                        <p class="text-2xl font-bold" id="cpu-percent">0%</p>
                    </div>
                    <i class="fas fa-microchip text-3xl text-blue-500"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-600 text-sm">Memory Usage</p>
                        <p class="text-2xl font-bold" id="memory-percent">0%</p>
                    </div>
                    <i class="fas fa-memory text-3xl text-purple-500"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-600 text-sm">Disk Usage</p>
                        <p class="text-2xl font-bold" id="disk-percent">0%</p>
                    </div>
                    <i class="fas fa-hdd text-3xl text-green-500"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-600 text-sm">Active Alerts</p>
                        <p class="text-2xl font-bold" id="alert-count">0</p>
                    </div>
                    <i class="fas fa-exclamation-triangle text-3xl text-yellow-500"></i>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">System Metrics (Last Hour)</h3>
                <canvas id="system-metrics-chart"></canvas>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Agent Performance</h3>
                <canvas id="agent-performance-chart"></canvas>
            </div>
        </div>

        <!-- Services Status -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold mb-4">Service Status</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full table-auto">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-2 text-left">Service</th>
                            <th class="px-4 py-2 text-left">Status</th>
                            <th class="px-4 py-2 text-left">Port</th>
                            <th class="px-4 py-2 text-left">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="services-table">
                        <!-- Services will be populated here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Alerts and Activity -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Recent Alerts</h3>
                <div id="alerts-list" class="space-y-2">
                    <!-- Alerts will be populated here -->
                </div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">User Activity</h3>
                <div id="activity-summary">
                    <!-- Activity summary will be populated here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let systemMetricsChart;
        let agentPerformanceChart;

        // Initialize WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                updateConnectionStatus(true);
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };

            ws.onclose = function() {
                updateConnectionStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }

        function updateConnectionStatus(connected) {
            const status = document.getElementById('connection-status');
            if (connected) {
                status.innerHTML = '<i class="fas fa-circle text-green-400 mr-1"></i> Connected';
            } else {
                status.innerHTML = '<i class="fas fa-circle text-red-400 mr-1"></i> Disconnected';
            }
        }

        function updateDashboard(data) {
            if (data.error) {
                console.error('Dashboard error:', data.error);
                return;
            }

            // Update last update time
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();

            // Update system metrics
            if (data.system_metrics) {
                document.getElementById('cpu-percent').textContent = data.system_metrics.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory-percent').textContent = data.system_metrics.memory_percent.toFixed(1) + '%';
                document.getElementById('disk-percent').textContent = data.system_metrics.disk_percent.toFixed(1) + '%';
            }

            // Update alert count
            if (data.alerts) {
                document.getElementById('alert-count').textContent = data.alerts.total_active || 0;
            }

            // Update services table
            updateServicesTable(data.services);

            // Update alerts list
            updateAlertsList(data.alerts);

            // Update activity summary
            updateActivitySummary(data.user_activity);

            // Update charts
            updateCharts(data);
        }

        function updateServicesTable(services) {
            const tbody = document.getElementById('services-table');
            tbody.innerHTML = '';

            services.forEach(service => {
                const row = document.createElement('tr');
                row.className = 'border-b';

                const statusClass = service.status === 'running' ? 'status-healthy' :
                                  service.status === 'error' ? 'status-error' :
                                  service.status === 'starting' ? 'status-warning' : 'status-unknown';

                row.innerHTML = `
                    <td class="px-4 py-2 font-medium">${service.display_name}</td>
                    <td class="px-4 py-2">
                        <span class="px-2 py-1 rounded-full text-xs ${statusClass}">
                            ${service.status}
                        </span>
                    </td>
                    <td class="px-4 py-2">${service.port || 'N/A'}</td>
                    <td class="px-4 py-2">
                        <button onclick="controlService('${service.service_name}', 'start')"
                                class="text-green-600 hover:text-green-800 mr-2">
                            <i class="fas fa-play"></i>
                        </button>
                        <button onclick="controlService('${service.service_name}', 'stop')"
                                class="text-red-600 hover:text-red-800 mr-2">
                            <i class="fas fa-stop"></i>
                        </button>
                        <button onclick="controlService('${service.service_name}', 'restart')"
                                class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-redo"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function updateAlertsList(alerts) {
            const alertsList = document.getElementById('alerts-list');
            alertsList.innerHTML = '';

            // For now, show a placeholder since alerts data structure needs to be defined
            alertsList.innerHTML = '<p class="text-gray-500">No active alerts</p>';
        }

        function updateActivitySummary(activity) {
            const summary = document.getElementById('activity-summary');

            if (activity && activity.total_activities > 0) {
                summary.innerHTML = `
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span>Total Activities:</span>
                            <span class="font-semibold">${activity.total_activities}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Avg Response Time:</span>
                            <span class="font-semibold">${activity.avg_response_time?.toFixed(1) || 0}ms</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Avg Satisfaction:</span>
                            <span class="font-semibold">${activity.avg_satisfaction?.toFixed(1) || 0}/5</span>
                        </div>
                    </div>
                `;
            } else {
                summary.innerHTML = '<p class="text-gray-500">No recent activity</p>';
            }
        }

        function updateCharts(data) {
            // Update system metrics chart
            if (systemMetricsChart && data.system_metrics) {
                // Update chart data here
                // This would require storing historical data points
            }

            // Update agent performance chart
            if (agentPerformanceChart && data.agents) {
                updateAgentPerformanceChart(data.agents);
            }
        }

        function updateAgentPerformanceChart(agents) {
            const labels = agents.map(agent => agent.agent_id);
            const responseTimes = agents.map(agent => agent.avg_response_time);
            const successRates = agents.map(agent => agent.success_rate * 100);

            agentPerformanceChart.data.labels = labels;
            agentPerformanceChart.data.datasets[0].data = responseTimes;
            agentPerformanceChart.data.datasets[1].data = successRates;
            agentPerformanceChart.update();
        }

        function controlService(serviceName, action) {
            fetch(`/api/services/${serviceName}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Service ${action} successful:`, data.message);
                } else {
                    console.error(`Service ${action} failed:`, data.message);
                }
            })
            .catch(error => {
                console.error('Error controlling service:', error);
            });
        }

        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize System Metrics Chart
            const sysCtx = document.getElementById('system-metrics-chart').getContext('2d');
            systemMetricsChart = new Chart(sysCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }, {
                        label: 'Memory %',
                        data: [],
                        borderColor: 'rgb(147, 51, 234)',
                        backgroundColor: 'rgba(147, 51, 234, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            // Initialize Agent Performance Chart
            const agentCtx = document.getElementById('agent-performance-chart').getContext('2d');
            agentPerformanceChart = new Chart(agentCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Avg Response Time (ms)',
                        data: [],
                        backgroundColor: 'rgba(34, 197, 94, 0.8)',
                        yAxisID: 'y'
                    }, {
                        label: 'Success Rate (%)',
                        data: [],
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            max: 100,
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });

            // Connect WebSocket
            connectWebSocket();
        });
    </script>
</body>
</html>
        """

        # Write dashboard HTML
        with open(templates_dir / "dashboard.html", "w") as f:
            f.write(dashboard_html)

        logger.info("Dashboard UI files created successfully")

def main():
    """Main function to run the enhanced monitoring dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Enhanced Monitoring Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8790, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    dashboard = EnhancedMonitoringDashboard(host=args.host, port=args.port)
    dashboard.start()

if __name__ == "__main__":
    main()
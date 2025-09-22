#!/usr/bin/env python3
"""
DuckBot Real-time Analytics Dashboard
Live analytics visualization, monitoring, and interactive exploration
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
from pathlib import Path
from collections import defaultdict, deque
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from analytics_engine import AnalyticsEngine, AnalyticsEvent, AnalyticsEventType
from user_behavior_analytics import UserBehaviorAnalyzer
from performance_analytics import PerformanceAnalyzer
from business_intelligence import BusinessIntelligenceEngine

logger = logging.getLogger(__name__)

class DashboardWidget(Enum):
    """Types of dashboard widgets"""
    METRIC_CARD = "metric_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    SCATTER_PLOT = "scatter_plot"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: DashboardWidget
    title: str
    data_source: str
    position: Dict[str, int]  # {row, col}
    size: Dict[str, int]  # {width, height}
    refresh_interval: int  # seconds
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RealtimeMetric:
    """Real-time metric data"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    trend: str  # "up", "down", "stable"
    change_percent: float

@dataclass
class DashboardAlert:
    """Dashboard alert notification"""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    is_resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

class RealtimeAnalyticsDashboard:
    """Real-time analytics dashboard system"""

    def __init__(self, analytics_engine: AnalyticsEngine,
                 user_analyzer: UserBehaviorAnalyzer,
                 performance_analyzer: PerformanceAnalyzer,
                 bi_engine: BusinessIntelligenceEngine):
        self.analytics_engine = analytics_engine
        self.user_analyzer = user_analyzer
        self.performance_analyzer = performance_analyzer
        self.bi_engine = bi_engine

        self.app = FastAPI(title="DuckBot Real-time Analytics Dashboard")
        self.connection_manager = ConnectionManager()

        self.widgets: Dict[str, DashboardWidget] = {}
        self.realtime_metrics: Dict[str, RealtimeMetric] = {}
        self.alerts: List[DashboardAlert] = []
        self.dashboard_config: Dict[str, Any] = {}

        self.is_running = False
        self.update_task = None

        self._setup_routes()
        self._initialize_dashboard()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """Serve the main dashboard page"""
            return self._generate_dashboard_html()

        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get current metrics"""
            return {
                "metrics": {
                    name: {
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat(),
                        "trend": metric.trend,
                        "change_percent": metric.change_percent
                    }
                    for name, metric in self.realtime_metrics.items()
                }
            }

        @self.app.get("/api/widgets")
        async def get_widgets():
            """Get widget configurations"""
            return {
                "widgets": [
                    {
                        "widget_id": widget.widget_id,
                        "widget_type": widget.widget_type.value,
                        "title": widget.title,
                        "data_source": widget.data_source,
                        "position": widget.position,
                        "size": widget.size,
                        "refresh_interval": widget.refresh_interval,
                        "config": widget.config
                    }
                    for widget in self.widgets.values()
                ]
            }

        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get active alerts"""
            return {
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "title": alert.title,
                        "message": alert.message,
                        "severity": alert.severity.value,
                        "timestamp": alert.timestamp.isoformat(),
                        "is_resolved": alert.is_resolved,
                        "metadata": alert.metadata
                    }
                    for alert in self.alerts if not alert.is_resolved
                ]
            }

        @self.app.get("/api/analytics/{data_type}")
        async def get_analytics_data(data_type: str, period: str = "24h"):
            """Get analytics data for specific type"""
            try:
                if data_type == "user_behavior":
                    return await self._get_user_behavior_data(period)
                elif data_type == "performance":
                    return await self._get_performance_data(period)
                elif data_type == "business_intelligence":
                    return await self._get_business_intelligence_data(period)
                elif data_type == "cost_analysis":
                    return await self._get_cost_analysis_data(period)
                else:
                    return {"error": "Invalid data type"}
            except Exception as e:
                logger.error(f"Error getting analytics data for {data_type}: {e}")
                return {"error": str(e)}

        @self.app.post("/api/widgets/{widget_id}/refresh")
        async def refresh_widget(widget_id: str):
            """Force refresh a specific widget"""
            try:
                if widget_id in self.widgets:
                    data = await self._get_widget_data(widget_id)
                    await self.connection_manager.broadcast(json.dumps({
                        "type": "widget_update",
                        "widget_id": widget_id,
                        "data": data
                    }))
                    return {"success": True}
                else:
                    return {"error": "Widget not found"}
            except Exception as e:
                logger.error(f"Error refreshing widget {widget_id}: {e}")
                return {"error": str(e)}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self.connection_manager.connect(websocket)
            try:
                # Send initial data
                initial_data = {
                    "type": "initial_data",
                    "metrics": self.realtime_metrics,
                    "alerts": [alert for alert in self.alerts if not alert.is_resolved]
                }
                await websocket.send_text(json.dumps(initial_data))

                # Keep connection alive
                while True:
                    try:
                        # Wait for messages (keep connection alive)
                        data = await websocket.receive_text()
                        # Could handle client commands here
                    except:
                        break
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)

    def _initialize_dashboard(self):
        """Initialize the dashboard with default widgets"""
        # Create default widgets
        default_widgets = [
            DashboardWidget(
                widget_id="active_users",
                widget_type=DashboardWidget.METRIC_CARD,
                title="Active Users",
                data_source="user_behavior",
                position={"row": 0, "col": 0},
                size={"width": 3, "height": 1},
                refresh_interval=30,
                config={"icon": "users", "color": "blue"}
            ),
            DashboardWidget(
                widget_id="system_performance",
                widget_type=DashboardWidget.GAUGE,
                title="System Performance",
                data_source="performance",
                position={"row": 0, "col": 3},
                size={"width": 3, "height": 1},
                refresh_interval=15,
                config={"min": 0, "max": 100, "unit": "%"}
            ),
            DashboardWidget(
                widget_id="cost_trends",
                widget_type=DashboardWidget.LINE_CHART,
                title="Cost Trends",
                data_source="cost_analysis",
                position={"row": 0, "col": 6},
                size={"width": 6, "height": 2},
                refresh_interval=60,
                config={"time_range": "24h", "show_legend": True}
            ),
            DashboardWidget(
                widget_id="feature_usage",
                widget_type=DashboardWidget.BAR_CHART,
                title="Feature Usage",
                data_source="user_behavior",
                position={"row": 2, "col": 0},
                size={"width": 6, "height": 2},
                refresh_interval=120,
                config={"show_values": True, "max_items": 10}
            ),
            DashboardWidget(
                widget_id="performance_metrics",
                widget_type=DashboardWidget.TABLE,
                title="Performance Metrics",
                data_source="performance",
                position={"row": 2, "col": 6},
                size={"width": 6, "height": 2},
                refresh_interval=30,
                config={"columns": ["Metric", "Value", "Trend"]}
            ),
            DashboardWidget(
                widget_id="business_insights",
                widget_type=DashboardWidget.TABLE,
                title="Business Insights",
                data_source="business_intelligence",
                position={"row": 4, "col": 0},
                size={"width": 12, "height": 2},
                refresh_interval=300,
                config={"columns": ["Insight", "Impact", "Priority"]}
            )
        ]

        for widget in default_widgets:
            self.widgets[widget.widget_id] = widget

        # Start real-time updates
        self.start_realtime_updates()

    def _generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML page"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot Analytics Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                .metric-card {
                    @apply bg-white rounded-lg shadow-md p-6;
                }
                .alert-critical { @apply bg-red-100 border-red-400 text-red-700; }
                .alert-error { @apply bg-orange-100 border-orange-400 text-orange-700; }
                .alert-warning { @apply bg-yellow-100 border-yellow-400 text-yellow-700; }
                .alert-info { @apply bg-blue-100 border-blue-400 text-blue-700; }
            </style>
        </head>
        <body class="bg-gray-100">
            <div class="container mx-auto p-4">
                <header class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-800">DuckBot Analytics Dashboard</h1>
                    <p class="text-gray-600">Real-time analytics and insights</p>
                </header>

                <!-- Alerts Section -->
                <div id="alerts-container" class="mb-6"></div>

                <!-- Metrics Grid -->
                <div id="metrics-grid" class="grid grid-cols-12 gap-4 mb-6"></div>

                <!-- Widget Container -->
                <div id="widgets-container" class="grid grid-cols-12 gap-4"></div>
            </div>

            <script>
                // WebSocket connection
                let ws = new WebSocket('ws://' + window.location.host + '/ws');

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleRealtimeUpdate(data);
                };

                ws.onclose = function() {
                    // Attempt to reconnect after 5 seconds
                    setTimeout(() => {
                        ws = new WebSocket('ws://' + window.location.host + '/ws');
                    }, 5000);
                };

                function handleRealtimeUpdate(data) {
                    if (data.type === 'initial_data') {
                        updateMetrics(data.metrics);
                        updateAlerts(data.alerts);
                    } else if (data.type === 'widget_update') {
                        updateWidget(data.widget_id, data.data);
                    }
                }

                function updateMetrics(metrics) {
                    const container = document.getElementById('metrics-grid');
                    container.innerHTML = '';

                    Object.entries(metrics).forEach(([name, metric]) => {
                        const metricCard = document.createElement('div');
                        metricCard.className = 'metric-card col-span-3';
                        metricCard.innerHTML = `
                            <div class="flex items-center justify-between">
                                <div>
                                    <h3 class="text-lg font-semibold text-gray-700">${name.replace(/_/g, ' ').toUpperCase()}</h3>
                                    <p class="text-2xl font-bold text-gray-900">${metric.value.toFixed(2)} ${metric.unit}</p>
                                    <p class="text-sm ${metric.trend === 'up' ? 'text-red-600' : metric.trend === 'down' ? 'text-green-600' : 'text-gray-600'}">
                                ${metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'} ${metric.change_percent.toFixed(1)}%
                            </p>
                                </div>
                                <div class="text-3xl">
                                    ${getMetricIcon(name)}
                                </div>
                            </div>
                        `;
                        container.appendChild(metricCard);
                    });
                }

                function updateAlerts(alerts) {
                    const container = document.getElementById('alerts-container');
                    container.innerHTML = '';

                    alerts.forEach(alert => {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = `alert-${alert.severity} border-l-4 p-4 mb-2`;
                        alertDiv.innerHTML = `
                            <div class="flex">
                                <div class="flex-1">
                                    <h4 class="font-bold">${alert.title}</h4>
                                    <p>${alert.message}</p>
                                    <small class="text-gray-600">${new Date(alert.timestamp).toLocaleString()}</small>
                                </div>
                            </div>
                        `;
                        container.appendChild(alertDiv);
                    });
                }

                function updateWidget(widgetId, data) {
                    // Update widget data based on widget type
                    console.log('Updating widget:', widgetId, data);
                }

                function getMetricIcon(metricName) {
                    const icons = {
                        'active_users': '👥',
                        'system_performance': '⚡',
                        'cost_analysis': '💰',
                        'error_rate': '⚠️',
                        'response_time': '⏱️'
                    };
                    return icons[metricName] || '📊';
                }

                // Load initial data
                async function loadInitialData() {
                    try {
                        // Load widgets
                        const widgetsResponse = await fetch('/api/widgets');
                        const widgetsData = await widgetsResponse.json();
                        renderWidgets(widgetsData.widgets);

                        // Load alerts
                        const alertsResponse = await fetch('/api/alerts');
                        const alertsData = await alertsResponse.json();
                        updateAlerts(alertsData.alerts);
                    } catch (error) {
                        console.error('Error loading initial data:', error);
                    }
                }

                function renderWidgets(widgets) {
                    const container = document.getElementById('widgets-container');
                    container.innerHTML = '';

                    widgets.forEach(widget => {
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = `bg-white rounded-lg shadow-md p-4 col-span-${widget.size.width}`;
                        widgetDiv.id = `widget-${widget.widget_id}`;
                        widgetDiv.innerHTML = `
                            <h3 class="text-lg font-semibold mb-4">${widget.title}</h3>
                            <div id="widget-content-${widget.widget_id}">Loading...</div>
                        `;
                        container.appendChild(widgetDiv);

                        // Load widget data
                        loadWidgetData(widget);
                    });
                }

                async function loadWidgetData(widget) {
                    try {
                        const response = await fetch(`/api/analytics/${widget.data_source}`);
                        const data = await response.json();
                        renderWidgetContent(widget, data);
                    } catch (error) {
                        console.error('Error loading widget data:', error);
                    }
                }

                function renderWidgetContent(widget, data) {
                    const contentDiv = document.getElementById(`widget-content-${widget.widget_id}`);

                    if (widget.widget_type === 'metric_card') {
                        contentDiv.innerHTML = `<p class="text-3xl font-bold">${data.value || 'N/A'}</p>`;
                    } else if (widget.widget_type === 'line_chart') {
                        // Create line chart
                        const canvas = document.createElement('canvas');
                        contentDiv.innerHTML = '';
                        contentDiv.appendChild(canvas);

                        new Chart(canvas, {
                            type: 'line',
                            data: {
                                labels: data.labels || [],
                                datasets: [{
                                    label: widget.title,
                                    data: data.values || [],
                                    borderColor: 'rgb(75, 192, 192)',
                                    tension: 0.1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false
                            }
                        });
                    } else {
                        contentDiv.innerHTML = '<p>Data loaded</p>';
                    }
                }

                // Initialize dashboard
                document.addEventListener('DOMContentLoaded', loadInitialData);
            </script>
        </body>
        </html>
        '''

    def start_realtime_updates(self):
        """Start real-time data updates"""
        if not self.is_running:
            self.is_running = True
            self.update_task = asyncio.create_task(self._update_loop())

    async def _update_loop(self):
        """Main update loop for real-time data"""
        while self.is_running:
            try:
                # Update metrics
                await self._update_realtime_metrics()

                # Update widgets
                await self._update_widgets()

                # Check for alerts
                await self._check_alerts()

                # Broadcast updates
                await self._broadcast_updates()

                # Wait for next update cycle
                await asyncio.sleep(15)  # Update every 15 seconds

            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    async def _update_realtime_metrics(self):
        """Update real-time metrics"""
        try:
            # Get user behavior metrics
            engagement_metrics = self.user_analyzer._calculate_engagement_metrics()

            self.realtime_metrics["active_users"] = RealtimeMetric(
                metric_name="active_users",
                value=float(engagement_metrics.daily_active_users),
                unit="users",
                timestamp=datetime.now(),
                trend="stable",
                change_percent=0.0
            )

            # Get performance metrics
            perf_summary = self.performance_analyzer.get_performance_summary(1)

            self.realtime_metrics["system_performance"] = RealtimeMetric(
                metric_name="system_performance",
                value=perf_summary.get("system_performance", {}).get("average_cpu", 0.0),
                unit="%",
                timestamp=datetime.now(),
                trend="stable",
                change_percent=0.0
            )

            # Get cost metrics
            cost_summary = self.analytics_engine.get_usage_summary(1)

            self.realtime_metrics["daily_cost"] = RealtimeMetric(
                metric_name="daily_cost",
                value=cost_summary.total_cost,
                unit="$",
                timestamp=datetime.now(),
                trend="stable",
                change_percent=0.0
            )

            # Calculate trends (simplified)
            for metric_name, metric in self.realtime_metrics.items():
                if hasattr(metric, 'previous_value'):
                    change = ((metric.value - metric.previous_value) / metric.previous_value * 100) if metric.previous_value > 0 else 0
                    metric.change_percent = change
                    metric.trend = "up" if change > 1 else "down" if change < -1 else "stable"

                metric.previous_value = metric.value

        except Exception as e:
            logger.error(f"Error updating realtime metrics: {e}")

    async def _update_widgets(self):
        """Update widget data"""
        try:
            for widget_id, widget in self.widgets.items():
                # Check if widget needs refresh
                if time.time() % widget.refresh_interval < 15:  # Refresh every interval
                    data = await self._get_widget_data(widget_id)

                    # Broadcast widget update
                    await self.connection_manager.broadcast(json.dumps({
                        "type": "widget_update",
                        "widget_id": widget_id,
                        "data": data
                    }))

        except Exception as e:
            logger.error(f"Error updating widgets: {e}")

    async def _get_widget_data(self, widget_id: str) -> Dict[str, Any]:
        """Get data for a specific widget"""
        widget = self.widgets.get(widget_id)
        if not widget:
            return {}

        try:
            if widget.data_source == "user_behavior":
                return await self._get_user_behavior_widget_data(widget)
            elif widget.data_source == "performance":
                return await self._get_performance_widget_data(widget)
            elif widget.data_source == "business_intelligence":
                return await self._get_business_intelligence_widget_data(widget)
            elif widget.data_source == "cost_analysis":
                return await self._get_cost_analysis_widget_data(widget)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting data for widget {widget_id}: {e}")
            return {}

    async def _get_user_behavior_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get user behavior widget data"""
        try:
            if widget.widget_type == DashboardWidget.METRIC_CARD:
                engagement_metrics = self.user_analyzer._calculate_engagement_metrics()
                return {
                    "value": engagement_metrics.daily_active_users,
                    "label": "Daily Active Users"
                }
            elif widget.widget_type == DashboardWidget.BAR_CHART:
                feature_popularity = self.user_analyzer.get_feature_popularity_by_segment(self.user_analyzer.UserSegment.POWER_USER)
                return {
                    "labels": list(feature_popularity.keys())[:10],
                    "values": list(feature_popularity.values())[:10]
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting user behavior widget data: {e}")
            return {}

    async def _get_performance_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get performance widget data"""
        try:
            perf_summary = self.performance_analyzer.get_performance_summary(1)

            if widget.widget_type == DashboardWidget.GAUGE:
                cpu_usage = perf_summary.get("system_performance", {}).get("average_cpu", 0.0)
                return {
                    "value": cpu_usage,
                    "max": 100
                }
            elif widget.widget_type == DashboardWidget.TABLE:
                metrics = []
                system_perf = perf_summary.get("system_performance", {})
                metrics.append(["CPU Usage", f"{system_perf.get('average_cpu', 0.0):.1f}%", "→"])
                metrics.append(["Memory Usage", f"{system_perf.get('average_memory', 0.0):.1f}%", "→"])
                metrics.append(["System Load", f"{system_perf.get('average_load', 0.0):.2f}", "→"])

                return {
                    "columns": ["Metric", "Value", "Trend"],
                    "data": metrics
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting performance widget data: {e}")
            return {}

    async def _get_business_intelligence_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get business intelligence widget data"""
        try:
            insights = self.bi_engine.get_business_insights(limit=10)

            if widget.widget_type == DashboardWidget.TABLE:
                insight_data = []
                for insight in insights:
                    insight_data.append([
                        insight['title'],
                        f"{insight['impact_score']}/100",
                        "High" if insight['impact_score'] > 80 else "Medium" if insight['impact_score'] > 50 else "Low"
                    ])

                return {
                    "columns": ["Insight", "Impact", "Priority"],
                    "data": insight_data
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting business intelligence widget data: {e}")
            return {}

    async def _get_cost_analysis_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get cost analysis widget data"""
        try:
            cost_breakdown = self.bi_engine.get_cost_breakdown()

            if widget.widget_type == DashboardWidget.LINE_CHART:
                # Generate sample trend data
                hours = list(range(24))
                costs = [50 + np.random.normal(0, 10) for _ in hours]

                return {
                    "labels": [f"{h:02d}:00" for h in hours],
                    "values": costs
                }
            elif widget.widget_type == DashboardWidget.PIE_CHART:
                categories = list(cost_breakdown.keys())
                amounts = [cost_breakdown[cat]['amount'] for cat in categories]

                return {
                    "labels": [cat.replace('_', ' ').title() for cat in categories],
                    "values": amounts
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting cost analysis widget data: {e}")
            return {}

    async def _check_alerts(self):
        """Check for and generate alerts"""
        try:
            # Check performance alerts
            perf_summary = self.performance_analyzer.get_performance_summary(1)
            system_perf = perf_summary.get("system_performance", {})

            # High CPU alert
            cpu_usage = system_perf.get('average_cpu', 0.0)
            if cpu_usage > 90:
                alert = DashboardAlert(
                    alert_id=str(uuid.uuid4()),
                    title="High CPU Usage",
                    message=f"CPU usage is at {cpu_usage:.1f}%",
                    severity=AlertSeverity.CRITICAL if cpu_usage > 95 else AlertSeverity.ERROR,
                    timestamp=datetime.now(),
                    metadata={"cpu_usage": cpu_usage}
                )
                self._add_alert(alert)

            # High memory alert
            memory_usage = system_perf.get('average_memory', 0.0)
            if memory_usage > 85:
                alert = DashboardAlert(
                    alert_id=str(uuid.uuid4()),
                    title="High Memory Usage",
                    message=f"Memory usage is at {memory_usage:.1f}%",
                    severity=AlertSeverity.WARNING,
                    timestamp=datetime.now(),
                    metadata={"memory_usage": memory_usage}
                )
                self._add_alert(alert)

            # Check cost alerts
            cost_summary = self.analytics_engine.get_usage_summary(1)
            if cost_summary.total_cost > 100:  # High daily cost
                alert = DashboardAlert(
                    alert_id=str(uuid.uuid4()),
                    title="High Daily Cost",
                    message=f"Daily cost is ${cost_summary.total_cost:.2f}",
                    severity=AlertSeverity.WARNING,
                    timestamp=datetime.now(),
                    metadata={"daily_cost": cost_summary.total_cost}
                )
                self._add_alert(alert)

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def _add_alert(self, alert: DashboardAlert):
        """Add an alert to the system"""
        # Check if similar alert already exists and is active
        existing_similar = [a for a in self.alerts
                           if (a.title == alert.title and
                               not a.is_resolved and
                               (datetime.now() - a.timestamp).total_seconds() < 3600)]

        if not existing_similar:
            self.alerts.append(alert)

            # Broadcast alert
            asyncio.create_task(self.connection_manager.broadcast(json.dumps({
                "type": "new_alert",
                "alert": {
                    "alert_id": alert.alert_id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                }
            })))

    async def _broadcast_updates(self):
        """Broadcast updates to all connected clients"""
        try:
            # Broadcast metrics update
            await self.connection_manager.broadcast(json.dumps({
                "type": "metrics_update",
                "metrics": {
                    name: {
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat(),
                        "trend": metric.trend,
                        "change_percent": metric.change_percent
                    }
                    for name, metric in self.realtime_metrics.items()
                }
            }))

        except Exception as e:
            logger.error(f"Error broadcasting updates: {e}")

    # API helper methods
    async def _get_user_behavior_data(self, period: str) -> Dict[str, Any]:
        """Get user behavior analytics data"""
        try:
            # Convert period to days
            if period == "24h":
                days = 1
            elif period == "7d":
                days = 7
            elif period == "30d":
                days = 30
            else:
                days = 1

            engagement_metrics = self.user_analyzer._calculate_engagement_metrics()
            feature_popularity = self.user_analyzer.get_feature_popularity_by_segment(self.user_analyzer.UserSegment.POWER_USER)

            return {
                "engagement": {
                    "daily_active_users": engagement_metrics.daily_active_users,
                    "weekly_active_users": engagement_metrics.weekly_active_users,
                    "monthly_active_users": engagement_metrics.monthly_active_users,
                    "user_retention_rate": engagement_metrics.user_retention_rate
                },
                "feature_popularity": feature_popularity,
                "segment_distribution": self.user_analyzer.get_segment_distribution()
            }

        except Exception as e:
            logger.error(f"Error getting user behavior data: {e}")
            return {}

    async def _get_performance_data(self, period: str) -> Dict[str, Any]:
        """Get performance analytics data"""
        try:
            perf_summary = self.performance_analyzer.get_performance_summary()
            perf_trends = self.performance_analyzer.get_performance_trends()

            return {
                "summary": perf_summary,
                "trends": perf_trends,
                "active_bottlenecks": len(self.performance_analyzer.get_active_bottlenecks())
            }

        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {}

    async def _get_business_intelligence_data(self, period: str) -> Dict[str, Any]:
        """Get business intelligence data"""
        try:
            insights = self.bi_engine.get_business_insights()
            roi_metrics = self.bi_engine.get_roi_metrics()

            return {
                "insights": insights,
                "roi_metrics": roi_metrics,
                "cost_breakdown": self.bi_engine.get_cost_breakdown()
            }

        except Exception as e:
            logger.error(f"Error getting business intelligence data: {e}")
            return {}

    async def _get_cost_analysis_data(self, period: str) -> Dict[str, Any]:
        """Get cost analysis data"""
        try:
            cost_summary = self.analytics_engine.get_usage_summary()
            cost_breakdown = self.bi_engine.get_cost_breakdown()

            return {
                "summary": {
                    "total_cost": cost_summary.total_cost,
                    "total_tokens": cost_summary.total_tokens,
                    "total_requests": cost_summary.total_requests,
                    "projected_monthly": cost_summary.projected_monthly
                },
                "breakdown": cost_breakdown,
                "optimization_opportunities": self.bi_engine.get_cost_optimization_opportunities()
            }

        except Exception as e:
            logger.error(f"Error getting cost analysis data: {e}")
            return {}

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.is_resolved = True
                break

    def add_custom_widget(self, widget: DashboardWidget):
        """Add a custom widget to the dashboard"""
        self.widgets[widget.widget_id] = widget

    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard"""
        if widget_id in self.widgets:
            del self.widgets[widget_id]

    def stop(self):
        """Stop the dashboard"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()

    def run_dashboard(self, host: str = "127.0.0.1", port: int = 8790):
        """Run the dashboard server"""
        logger.info(f"Starting analytics dashboard on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)
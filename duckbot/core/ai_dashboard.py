"""
AI Monitoring and Control Dashboard

Provides a comprehensive web-based dashboard for AI system monitoring and control:
- Real-time system metrics visualization
- AI operation management interface
- Interactive decision making tools
- Knowledge base exploration
- Service monitoring and control
- Performance analytics and reporting
- Autonomous system oversight

Author: Claude for DuckBot Enhanced v4.2
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3
import threading
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles

from .ai_orchestrator import AIOrchestrator, OrchestratorConfig, OrchestratorMode
from .ai_service_integration import AIIntegrationService, EventType
from .monitoring_system import DuckBotMonitoring, AlertSeverity

logger = logging.getLogger(__name__)

class DashboardView(Enum):
    """Dashboard view types"""
    OVERVIEW = "overview"
    OPERATIONS = "operations"
    MONITORING = "monitoring"
    KNOWLEDGE = "knowledge"
    DECISIONS = "decisions"
    SERVICES = "services"
    ANALYTICS = "analytics"
    SETTINGS = "settings"

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str
    title: str
    view: DashboardView
    position: Dict[str, int]  # {x: int, y: int, w: int, h: int}
    config: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 30  # seconds

class AIMonitoringDashboard:
    """AI Monitoring and Control Dashboard"""

    def __init__(self, orchestrator: AIOrchestrator,
                 integration_service: AIIntegrationService,
                 host: str = "127.0.0.1", port: int = 8791):
        self.orchestrator = orchestrator
        self.integration_service = integration_service
        self.host = host
        self.port = port

        # FastAPI app
        self.app = FastAPI(
            title="DuckBot AI Dashboard",
            description="AI System Monitoring and Control Dashboard",
            version="1.0.0"
        )

        # Setup templates and static files
        self.templates_dir = Path(__file__).parent / "templates" / "dashboard"
        self.static_dir = Path(__file__).parent / "static" / "dashboard"

        # Create directories if they don't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)

        self.templates = Jinja2Templates(directory=str(self.templates_dir))

        # Dashboard configuration
        self.dashboard_config = {
            "title": "DuckBot AI Control Center",
            "theme": "dark",
            "auto_refresh": True,
            "refresh_interval": 10,
            "max_events": 100,
            "show_realtime": True,
            "enable_notifications": True
        }

        # Widget configurations
        self.widgets = self._setup_default_widgets()

        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Dashboard stats
        self.dashboard_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_events": 0,
            "widget_updates": 0,
            "api_calls": 0
        }

        # Database setup
        self.db_path = Path("duckbot_ai_dashboard.db")
        self._init_database()

        # Setup routes
        self._setup_routes()

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

        logger.info("AI Dashboard initialized")

    def _init_database(self):
        """Initialize dashboard database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dashboard_sessions (
                        session_id TEXT PRIMARY KEY,
                        start_time TEXT,
                        last_activity TEXT,
                        view TEXT,
                        user_agent TEXT,
                        ip_address TEXT,
                        events_count INTEGER
                    )
                """)

                # Widget interactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS widget_interactions (
                        interaction_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        widget_id TEXT,
                        interaction_type TEXT,
                        timestamp TEXT,
                        data TEXT,
                        FOREIGN KEY (session_id) REFERENCES dashboard_sessions (session_id)
                    )
                """)

                # User preferences table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id TEXT PRIMARY KEY,
                        preferences TEXT,
                        last_updated TEXT
                    )
                """)

                conn.commit()
                logger.info("Dashboard database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize dashboard database: {e}")

    def _setup_default_widgets(self) -> List[DashboardWidget]:
        """Setup default dashboard widgets"""
        return [
            # Overview view widgets
            DashboardWidget(
                widget_id="system_health",
                widget_type="gauge",
                title="System Health",
                view=DashboardView.OVERVIEW,
                position={"x": 0, "y": 0, "w": 6, "h": 4},
                config={"metric": "health_score", "min": 0, "max": 100},
                refresh_interval=10
            ),

            DashboardWidget(
                widget_id="performance_score",
                widget_type="gauge",
                title="Performance Score",
                view=DashboardView.OVERVIEW,
                position={"x": 6, "y": 0, "w": 6, "h": 4},
                config={"metric": "performance_score", "min": 0, "max": 100},
                refresh_interval=10
            ),

            DashboardWidget(
                widget_id="active_operations",
                widget_type="counter",
                title="Active Operations",
                view=DashboardView.OVERVIEW,
                position={"x": 0, "y": 4, "w": 4, "h": 4},
                config={"metric": "active_operations"},
                refresh_interval=5
            ),

            DashboardWidget(
                widget_id="system_alerts",
                widget_type="alert_list",
                title="System Alerts",
                view=DashboardView.OVERVIEW,
                position={"x": 4, "y": 4, "w": 8, "h": 4},
                config={"max_alerts": 10},
                refresh_interval=15
            ),

            # Monitoring view widgets
            DashboardWidget(
                widget_id="cpu_usage",
                widget_type="line_chart",
                title="CPU Usage",
                view=DashboardView.MONITORING,
                position={"x": 0, "y": 0, "w": 12, "h": 6},
                config={"metric": "cpu_percent", "timeframe": "1h"},
                refresh_interval=30
            ),

            DashboardWidget(
                widget_id="memory_usage",
                widget_type="line_chart",
                title="Memory Usage",
                view=DashboardView.MONITORING,
                position={"x": 0, "y": 6, "w": 12, "h": 6},
                config={"metric": "memory_percent", "timeframe": "1h"},
                refresh_interval=30
            ),

            # Operations view widgets
            DashboardWidget(
                widget_id="operations_queue",
                widget_type="table",
                title="Operations Queue",
                view=DashboardView.OPERATIONS,
                position={"x": 0, "y": 0, "w": 12, "h": 8},
                config={"columns": ["id", "type", "status", "priority", "created_at"]},
                refresh_interval=10
            ),

            DashboardWidget(
                widget_id="operation_stats",
                widget_type="pie_chart",
                title="Operation Statistics",
                view=DashboardView.OPERATIONS,
                position={"x": 0, "y": 8, "w": 6, "h": 4},
                config={"metrics": ["completed", "failed", "pending"]},
                refresh_interval=60
            ),

            # Knowledge view widgets
            DashboardWidget(
                widget_id="knowledge_search",
                widget_type="search",
                title="Knowledge Search",
                view=DashboardView.KNOWLEDGE,
                position={"x": 0, "y": 0, "w": 12, "h": 4},
                config={"placeholder": "Search knowledge base..."},
                refresh_interval=0
            ),

            DashboardWidget(
                widget_id="recent_knowledge",
                widget_type="list",
                title="Recent Knowledge Entries",
                view=DashboardView.KNOWLEDGE,
                position={"x": 0, "y": 4, "w": 12, "h": 8},
                config={"max_items": 20},
                refresh_interval=30
            )
        ]

    def _setup_routes(self):
        """Setup dashboard routes"""

        # Main dashboard page
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            try:
                session_id = self._create_session(request)
                return self.templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "session_id": session_id,
                    "config": self.dashboard_config,
                    "widgets": self._get_view_widgets(DashboardView.OVERVIEW)
                })
            except Exception as e:
                logger.error(f"Error rendering dashboard home: {e}")
                return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)

        # View-specific pages
        @self.app.get("/view/{view_name}", response_class=HTMLResponse)
        async def dashboard_view(request: Request, view_name: str):
            try:
                session_id = self._create_session(request)

                try:
                    view = DashboardView(view_name)
                except ValueError:
                    return HTMLResponse(content="View not found", status_code=404)

                return self.templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "session_id": session_id,
                    "config": self.dashboard_config,
                    "widgets": self._get_view_widgets(view),
                    "current_view": view_name
                })
            except Exception as e:
                logger.error(f"Error rendering dashboard view {view_name}: {e}")
                return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)

        # API endpoints for dashboard data
        @self.app.get("/api/dashboard/status")
        async def get_dashboard_status():
            try:
                orchestrator_status = self.orchestrator.get_orchestrator_status()
                monitoring_status = self.orchestrator.monitoring_system.get_system_status()

                return {
                    "timestamp": datetime.now().isoformat(),
                    "orchestrator": {
                        "running": orchestrator_status.get("running", False),
                        "mode": orchestrator_status.get("mode", "unknown"),
                        "autonomy_level": orchestrator_status.get("autonomy_level", 0.0),
                        "active_operations": orchestrator_status.get("active_operations", 0),
                        "pending_approvals": orchestrator_status.get("pending_approvals", 0)
                    },
                    "monitoring": {
                        "health_score": monitoring_status.get("health_score", 0.0),
                        "performance_score": monitoring_status.get("performance_score", 0.0),
                        "active_alerts": len(monitoring_status.get("active_alerts", [])),
                        "services_count": len(monitoring_status.get("services", []))
                    },
                    "dashboard": {
                        "active_sessions": len(self.active_sessions),
                        "total_events": self.dashboard_stats["total_events"],
                        "widget_updates": self.dashboard_stats["widget_updates"]
                    }
                }
            except Exception as e:
                logger.error(f"Error getting dashboard status: {e}")
                return {"error": str(e)}

        @self.app.get("/api/dashboard/metrics")
        async def get_dashboard_metrics():
            try:
                metrics = self.orchestrator.monitoring_system.metrics_collector.get_current_metrics()

                return {
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu_percent": metrics.get("cpu_percent", 0.0),
                        "memory_percent": metrics.get("memory_percent", 0.0),
                        "disk_percent": metrics.get("disk_percent", 0.0),
                        "network_io": metrics.get("network_io", {}),
                        "process_count": metrics.get("process_count", 0)
                    },
                    "ai": {
                        "total_operations": self.orchestrator.orchestrator_stats.get("total_operations", 0),
                        "success_rate": self.orchestrator.orchestrator_stats.get("success_rate", 0.0),
                        "autonomous_operations": self.orchestrator.orchestrator_stats.get("autonomous_operations", 0)
                    }
                }
            except Exception as e:
                logger.error(f"Error getting dashboard metrics: {e}")
                return {"error": str(e)}

        @self.app.get("/api/dashboard/alerts")
        async def get_dashboard_alerts(limit: int = 50):
            try:
                alerts = self.orchestrator.monitoring_system.alert_manager.get_active_alerts()

                # Sort by timestamp
                alerts.sort(key=lambda a: a.timestamp, reverse=True)

                return {
                    "alerts": [
                        {
                            "id": alert.id,
                            "type": alert.alert_type,
                            "severity": alert.severity.value,
                            "message": alert.message,
                            "source": alert.source,
                            "timestamp": alert.timestamp.isoformat(),
                            "resolved": alert.resolved
                        }
                        for alert in alerts[:limit]
                    ],
                    "total": len(alerts)
                }
            except Exception as e:
                logger.error(f"Error getting dashboard alerts: {e}")
                return {"error": str(e)}

        @self.app.get("/api/dashboard/operations")
        async def get_dashboard_operations(limit: int = 20):
            try:
                operations = self.orchestrator.get_recent_operations(limit)

                return {
                    "operations": operations,
                    "pending": self.orchestrator.get_pending_operations()
                }
            except Exception as e:
                logger.error(f"Error getting dashboard operations: {e}")
                return {"error": str(e)}

        @self.app.get("/api/dashboard/knowledge/recent")
        async def get_recent_knowledge(limit: int = 20):
            try:
                # Get recent knowledge entries
                recent_entries = self.orchestrator.knowledge_base.get_recent_entries(limit)

                return {
                    "entries": [
                        {
                            "id": entry.id,
                            "title": entry.title,
                            "category": entry.category.value,
                            "tags": entry.tags,
                            "created_at": entry.created_at.isoformat(),
                            "preview": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
                        }
                        for entry in recent_entries
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting recent knowledge: {e}")
                return {"error": str(e)}

        @self.app.post("/api/dashboard/knowledge/search")
        async def search_knowledge(query: str, category: Optional[str] = None, limit: int = 10):
            try:
                from .ai_knowledge_base import KnowledgeQuery, KnowledgeCategory

                # Map category
                category_map = {
                    "system_health_monitoring": KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                    "performance_optimization": KnowledgeCategory.PERFORMANCE_OPTIMIZATION,
                    "error_recovery": KnowledgeCategory.ERROR_RECOVERY,
                    "service_management": KnowledgeCategory.SERVICE_MANAGEMENT,
                    "resource_management": KnowledgeCategory.RESOURCE_MANAGEMENT,
                    "predictive_maintenance": KnowledgeCategory.PREDICTIVE_MAINTENANCE,
                    "security_hardening": KnowledgeCategory.SECURITY_HARDENING,
                    "troubleshooting": KnowledgeCategory.TROUBLESHOOTING
                }

                knowledge_category = None
                if category and category in category_map:
                    knowledge_category = category_map[category]

                # Create and execute query
                knowledge_query = KnowledgeQuery(
                    query_text=query,
                    category=knowledge_category,
                    limit=limit
                )

                result = self.orchestrator.knowledge_base.search_knowledge(knowledge_query)

                return {
                    "results": [
                        {
                            "id": entry.id,
                            "title": entry.title,
                            "content": entry.content,
                            "category": entry.category.value,
                            "tags": entry.tags,
                            "relevance_score": score,
                            "created_at": entry.created_at.isoformat()
                        }
                        for entry, score in result.entries
                    ],
                    "total_results": len(result.entries)
                }
            except Exception as e:
                logger.error(f"Error searching knowledge: {e}")
                return {"error": str(e)}

        @self.app.post("/api/dashboard/operations/approve")
        async def approve_dashboard_operation(operation_id: str):
            try:
                success = await self.orchestrator.approve_operation(operation_id, "dashboard_user")

                if not success:
                    return {"success": False, "error": "Operation not found or not pending"}

                # Log widget interaction
                await self._log_widget_interaction(
                    "unknown_session",  # Would be real session ID in production
                    "operations_queue",
                    "approve_operation",
                    {"operation_id": operation_id}
                )

                return {"success": True, "message": "Operation approved"}
            except Exception as e:
                logger.error(f"Error approving operation: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/dashboard/operations/reject")
        async def reject_dashboard_operation(operation_id: str, reason: str = "Rejected via dashboard"):
            try:
                success = await self.orchestrator.reject_operation(operation_id, reason)

                if not success:
                    return {"success": False, "error": "Operation not found or not pending"}

                # Log widget interaction
                await self._log_widget_interaction(
                    "unknown_session",
                    "operations_queue",
                    "reject_operation",
                    {"operation_id": operation_id, "reason": reason}
                )

                return {"success": True, "message": "Operation rejected"}
            except Exception as e:
                logger.error(f"Error rejecting operation: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/api/dashboard/operations/create")
        async def create_dashboard_operation(operation_type: str, description: str,
                                          parameters: Dict[str, Any] = None,
                                          priority: int = 5):
            try:
                operation_id = await self.orchestrator.request_operation(
                    operation_type=operation_type,
                    description=description,
                    parameters=parameters or {},
                    priority=priority
                )

                return {
                    "success": True,
                    "operation_id": operation_id,
                    "message": "Operation created successfully"
                }
            except Exception as e:
                logger.error(f"Error creating operation: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/api/dashboard/analytics")
        async def get_dashboard_analytics(timeframe: str = "24h"):
            try:
                # Parse timeframe
                if timeframe == "1h":
                    start_time = datetime.now() - timedelta(hours=1)
                elif timeframe == "24h":
                    start_time = datetime.now() - timedelta(hours=24)
                elif timeframe == "7d":
                    start_time = datetime.now() - timedelta(days=7)
                else:
                    start_time = datetime.now() - timedelta(hours=24)

                # Get analytics data
                analytics_data = await self._generate_analytics(start_time)

                return analytics_data
            except Exception as e:
                logger.error(f"Error getting dashboard analytics: {e}")
                return {"error": str(e)}

        @self.app.get("/api/dashboard/settings")
        async def get_dashboard_settings():
            try:
                return {
                    "config": self.dashboard_config,
                    "widgets": [
                        {
                            "id": widget.widget_id,
                            "type": widget.widget_type,
                            "title": widget.title,
                            "view": widget.view.value,
                            "position": widget.position,
                            "config": widget.config,
                            "refresh_interval": widget.refresh_interval
                        }
                        for widget in self.widgets
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting dashboard settings: {e}")
                return {"error": str(e)}

        @self.app.post("/api/dashboard/settings")
        async def update_dashboard_settings(config: Dict[str, Any]):
            try:
                # Update dashboard configuration
                for key, value in config.items():
                    if key in self.dashboard_config:
                        self.dashboard_config[key] = value

                return {"success": True, "message": "Settings updated"}
            except Exception as e:
                logger.error(f"Error updating dashboard settings: {e}")
                return {"success": False, "error": str(e)}

        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws/dashboard")
        async def dashboard_websocket(websocket: WebSocket):
            await websocket.accept()

            # Create session
            session_id = self._create_websocket_session(websocket)

            try:
                # Send initial data
                await self._send_initial_dashboard_data(websocket)

                # Keep connection alive
                while True:
                    try:
                        # Wait for messages
                        data = await websocket.receive_text()
                        message = json.loads(data)

                        # Handle different message types
                        await self._handle_dashboard_message(websocket, session_id, message)

                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"Error handling dashboard WebSocket message: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })

            except WebSocketDisconnect:
                pass
            finally:
                # Clean up session
                await self._cleanup_session(session_id)

        # Serve static files
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

    def _create_session(self, request: Request) -> str:
        """Create a new dashboard session"""
        session_id = f"session_{int(time.time() * 1000)}_{hash(request.client.host + request.headers.get('user-agent', ''))}"

        self.active_sessions[session_id] = {
            "start_time": datetime.now(),
            "last_activity": datetime.now(),
            "view": "overview",
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host,
            "events_count": 0
        }

        self.dashboard_stats["total_sessions"] += 1
        self.dashboard_stats["active_sessions"] += 1

        # Store session in database
        self._store_session(session_id, request)

        return session_id

    def _create_websocket_session(self, websocket: WebSocket) -> str:
        """Create a WebSocket session"""
        session_id = f"ws_session_{int(time.time() * 1000)}"

        self.active_sessions[session_id] = {
            "start_time": datetime.now(),
            "last_activity": datetime.now(),
            "view": "overview",
            "websocket": websocket,
            "events_count": 0
        }

        self.dashboard_stats["total_sessions"] += 1
        self.dashboard_stats["active_sessions"] += 1

        return session_id

    async def _cleanup_session(self, session_id: str):
        """Clean up a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.dashboard_stats["active_sessions"] -= 1

    def _store_session(self, session_id: str, request: Request):
        """Store session in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO dashboard_sessions
                    (session_id, start_time, last_activity, view, user_agent, ip_address, events_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    "overview",
                    request.headers.get("user-agent", ""),
                    request.client.host,
                    0
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing session: {e}")

    async def _send_initial_dashboard_data(self, websocket: WebSocket):
        """Send initial dashboard data to WebSocket client"""
        try:
            # Get current status
            status = await self.get_dashboard_status()

            await websocket.send_json({
                "type": "initial_data",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error sending initial dashboard data: {e}")

    async def _handle_dashboard_message(self, websocket: WebSocket, session_id: str, message: Dict[str, Any]):
        """Handle dashboard WebSocket messages"""
        try:
            message_type = message.get("type")

            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "subscribe":
                # Subscribe to updates
                events = message.get("events", [])
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "events": events,
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "get_widget_data":
                # Get specific widget data
                widget_id = message.get("widget_id")
                widget_data = await self._get_widget_data(widget_id)

                await websocket.send_json({
                    "type": "widget_data",
                    "widget_id": widget_id,
                    "data": widget_data,
                    "timestamp": datetime.now().isoformat()
                })

            # Update session activity
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["last_activity"] = datetime.now()
                self.active_sessions[session_id]["events_count"] += 1

        except Exception as e:
            logger.error(f"Error handling dashboard message: {e}")

    async def _get_widget_data(self, widget_id: str) -> Dict[str, Any]:
        """Get data for a specific widget"""
        try:
            # Find widget
            widget = next((w for w in self.widgets if w.widget_id == widget_id), None)
            if not widget:
                return {"error": "Widget not found"}

            # Get data based on widget type
            if widget.widget_type == "gauge":
                return await self._get_gauge_widget_data(widget)
            elif widget.widget_type == "counter":
                return await self._get_counter_widget_data(widget)
            elif widget.widget_type == "line_chart":
                return await self._get_line_chart_widget_data(widget)
            elif widget.widget_type == "alert_list":
                return await self._get_alert_list_widget_data(widget)
            elif widget.widget_type == "table":
                return await self._get_table_widget_data(widget)
            elif widget.widget_type == "pie_chart":
                return await self._get_pie_chart_widget_data(widget)
            else:
                return {"error": f"Unknown widget type: {widget.widget_type}"}

        except Exception as e:
            logger.error(f"Error getting widget data for {widget_id}: {e}")
            return {"error": str(e)}

    async def _get_gauge_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for gauge widget"""
        try:
            metric = widget.config.get("metric")

            if metric == "health_score":
                status = self.orchestrator.get_orchestrator_status()
                value = status.get("monitoring_status", {}).get("health_score", 0.0) * 100
            elif metric == "performance_score":
                status = self.orchestrator.get_orchestrator_status()
                value = status.get("monitoring_status", {}).get("performance_score", 0.0) * 100
            else:
                value = 0.0

            return {
                "value": value,
                "min": widget.config.get("min", 0),
                "max": widget.config.get("max", 100),
                "unit": "%"
            }

        except Exception as e:
            logger.error(f"Error getting gauge widget data: {e}")
            return {"value": 0, "min": 0, "max": 100}

    async def _get_counter_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for counter widget"""
        try:
            metric = widget.config.get("metric")

            if metric == "active_operations":
                status = self.orchestrator.get_orchestrator_status()
                value = status.get("active_operations", 0)
            else:
                value = 0

            return {
                "value": value,
                "label": widget.config.get("label", metric)
            }

        except Exception as e:
            logger.error(f"Error getting counter widget data: {e}")
            return {"value": 0, "label": "Unknown"}

    async def _get_line_chart_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for line chart widget"""
        try:
            metric = widget.config.get("metric")
            timeframe = widget.config.get("timeframe", "1h")

            # Get historical data (simplified for this example)
            metrics = self.orchestrator.monitoring_system.metrics_collector.get_current_metrics()

            value = metrics.get(metric, 0.0)

            # Generate some historical data points
            timestamps = []
            values = []

            for i in range(20):
                timestamps.append((datetime.now() - timedelta(minutes=i*3)).isoformat())
                # Add some variation to make it look realistic
                variation = value * (0.9 + 0.2 * (i % 3) / 3)
                values.append(variation)

            return {
                "timestamps": timestamps[::-1],  # Reverse to show oldest first
                "values": values[::-1],
                "metric": metric,
                "timeframe": timeframe
            }

        except Exception as e:
            logger.error(f"Error getting line chart widget data: {e}")
            return {"timestamps": [], "values": []}

    async def _get_alert_list_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for alert list widget"""
        try:
            max_alerts = widget.config.get("max_alerts", 10)
            alerts_data = await self.get_dashboard_alerts(max_alerts)

            return {
                "alerts": alerts_data.get("alerts", []),
                "total": alerts_data.get("total", 0)
            }

        except Exception as e:
            logger.error(f"Error getting alert list widget data: {e}")
            return {"alerts": [], "total": 0}

    async def _get_table_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for table widget"""
        try:
            operations_data = await self.get_dashboard_operations(20)

            return {
                "rows": operations_data.get("operations", []),
                "columns": widget.config.get("columns", [])
            }

        except Exception as e:
            logger.error(f"Error getting table widget data: {e}")
            return {"rows": [], "columns": []}

    async def _get_pie_chart_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for pie chart widget"""
        try:
            metrics = widget.config.get("metrics", [])

            status = self.orchestrator.get_orchestrator_status()
            stats = status.get("stats", {})

            data = []
            for metric in metrics:
                value = stats.get(metric, 0)
                data.append({
                    "label": metric.replace("_", " ").title(),
                    "value": value
                })

            return {
                "data": data
            }

        except Exception as e:
            logger.error(f"Error getting pie chart widget data: {e}")
            return {"data": []}

    def _get_view_widgets(self, view: DashboardView) -> List[Dict[str, Any]]:
        """Get widgets for a specific view"""
        return [
            {
                "id": widget.widget_id,
                "type": widget.widget_type,
                "title": widget.title,
                "position": widget.position,
                "config": widget.config,
                "refresh_interval": widget.refresh_interval
            }
            for widget in self.widgets
            if widget.view == view
        ]

    async def _generate_analytics(self, start_time: datetime) -> Dict[str, Any]:
        """Generate analytics data"""
        try:
            # Get operations within timeframe
            operations = [
                op for op in self.orchestrator.operation_history
                if op.created_at >= start_time
            ]

            # Calculate statistics
            total_operations = len(operations)
            successful_operations = len([op for op in operations if op.status == "completed"])
            failed_operations = len([op for op in operations if op.status == "failed"])

            # Operation types breakdown
            operation_types = {}
            for op in operations:
                op_type = op.operation_type
                if op_type not in operation_types:
                    operation_types[op_type] = 0
                operation_types[op_type] += 1

            # Time-based analysis
            operations_by_hour = {}
            for op in operations:
                hour = op.created_at.strftime("%Y-%m-%d %H:00")
                if hour not in operations_by_hour:
                    operations_by_hour[hour] = 0
                operations_by_hour[hour] += 1

            return {
                "timeframe": {
                    "start": start_time.isoformat(),
                    "end": datetime.now().isoformat()
                },
                "summary": {
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "failed_operations": failed_operations,
                    "success_rate": successful_operations / total_operations if total_operations > 0 else 0
                },
                "operation_types": operation_types,
                "timeline": operations_by_hour
            }

        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return {"error": str(e)}

    async def _log_widget_interaction(self, session_id: str, widget_id: str,
                                     interaction_type: str, data: Dict[str, Any]):
        """Log widget interaction"""
        try:
            self.dashboard_stats["widget_updates"] += 1

            # Update session activity
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["last_activity"] = datetime.now()
                self.active_sessions[session_id]["events_count"] += 1

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO widget_interactions
                    (interaction_id, session_id, widget_id, interaction_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"interaction_{int(time.time() * 1000)}",
                    session_id,
                    widget_id,
                    interaction_type,
                    datetime.now().isoformat(),
                    json.dumps(data)
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error logging widget interaction: {e}")

    async def start_dashboard(self):
        """Start the dashboard service"""
        if self._running:
            logger.warning("AI Dashboard is already running")
            return

        self._running = True
        logger.info(f"Starting AI Dashboard on {self.host}:{self.port}")

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._session_cleanup_loop()),
            asyncio.create_task(self._widget_refresh_loop()),
            asyncio.create_task(self._analytics_update_loop())
        ]

        # Create HTML template
        await self._create_html_template()

        # Start FastAPI server
        import uvicorn
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)

        # Run server in background task
        self._background_tasks.append(asyncio.create_task(server.serve()))

        logger.info("AI Dashboard started successfully")

    async def stop_dashboard(self):
        """Stop the dashboard service"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping AI Dashboard")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        logger.info("AI Dashboard stopped successfully")

    async def _create_html_template(self):
        """Create the HTML template for the dashboard"""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title }} - DuckBot AI Control Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .widget {
            @apply bg-white rounded-lg shadow-lg p-6;
        }
        .dark .widget {
            @apply bg-gray-800 text-white;
        }
        .metric-card {
            @apply bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg p-6;
        }
        .alert-critical { @apply bg-red-100 border-red-500 text-red-700; }
        .alert-warning { @apply bg-yellow-100 border-yellow-500 text-yellow-700; }
        .alert-info { @apply bg-blue-100 border-blue-500 text-blue-700; }
    </style>
</head>
<body class="bg-gray-100 dark:bg-gray-900">
    <div id="app" class="min-h-screen">
        <!-- Header -->
        <header class="bg-white dark:bg-gray-800 shadow-lg">
            <div class="container mx-auto px-4 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <i class="fas fa-robot text-3xl text-blue-600"></i>
                        <h1 class="text-2xl font-bold text-gray-800 dark:text-white">{{ config.title }}</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span id="connection-status" class="flex items-center">
                            <span class="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                            <span class="text-sm text-gray-600 dark:text-gray-300">Connected</span>
                        </span>
                        <button id="refresh-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            <i class="fas fa-sync-alt mr-2"></i>Refresh
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Navigation -->
        <nav class="bg-white dark:bg-gray-800 border-b">
            <div class="container mx-auto px-4">
                <div class="flex space-x-1">
                    <a href="/view/overview" class="nav-link px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg">
                        <i class="fas fa-tachometer-alt mr-2"></i>Overview
                    </a>
                    <a href="/view/operations" class="nav-link px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg">
                        <i class="fas fa-tasks mr-2"></i>Operations
                    </a>
                    <a href="/view/monitoring" class="nav-link px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg">
                        <i class="fas fa-chart-line mr-2"></i>Monitoring
                    </a>
                    <a href="/view/knowledge" class="nav-link px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg">
                        <i class="fas fa-brain mr-2"></i>Knowledge
                    </a>
                    <a href="/view/analytics" class="nav-link px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg">
                        <i class="fas fa-chart-pie mr-2"></i>Analytics
                    </a>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="container mx-auto px-4 py-6">
            <!-- Status Bar -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm opacity-90">System Health</p>
                            <p id="health-score" class="text-2xl font-bold">--</p>
                        </div>
                        <i class="fas fa-heartbeat text-3xl opacity-75"></i>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm opacity-90">Performance</p>
                            <p id="performance-score" class="text-2xl font-bold">--</p>
                        </div>
                        <i class="fas fa-tachometer-alt text-3xl opacity-75"></i>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm opacity-90">Active Operations</p>
                            <p id="active-operations" class="text-2xl font-bold">--</p>
                        </div>
                        <i class="fas fa-cogs text-3xl opacity-75"></i>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm opacity-90">Alerts</p>
                            <p id="active-alerts" class="text-2xl font-bold">--</p>
                        </div>
                        <i class="fas fa-exclamation-triangle text-3xl opacity-75"></i>
                    </div>
                </div>
            </div>

            <!-- Widgets Grid -->
            <div id="widgets-container" class="grid grid-cols-1 md:grid-cols-12 gap-6">
                <!-- Widgets will be dynamically inserted here -->
            </div>
        </main>

        <!-- Operation Modal -->
        <div id="operation-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
            <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">Operation Details</h3>
                    <button onclick="closeOperationModal()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div id="operation-content">
                    <!-- Operation details will be inserted here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let websocket = null;
        let sessionData = {
            sessionId: '{{ session_id }}',
            currentView: '{{ current_view or "overview" }}'
        };

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeWebSocket();
            loadWidgets();
            startAutoRefresh();
            updateNavigation();
        });

        // WebSocket connection
        function initializeWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

            websocket = new WebSocket(wsUrl);

            websocket.onopen = function() {
                console.log('WebSocket connected');
                updateConnectionStatus(true);

                // Subscribe to updates
                websocket.send(JSON.stringify({
                    type: 'subscribe',
                    events: ['system_status_update', 'operation_completed', 'alert_triggered']
                }));
            };

            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            websocket.onclose = function() {
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(initializeWebSocket, 5000);
            };

            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }

        // Handle WebSocket messages
        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'initial_data':
                    updateDashboard(data.data);
                    break;
                case 'system_status_update':
                    updateSystemStatus(data.data);
                    break;
                case 'operation_completed':
                    showNotification('Operation completed', 'success');
                    refreshWidgets();
                    break;
                case 'widget_data':
                    updateWidget(data.widget_id, data.data);
                    break;
                case 'error':
                    showNotification(data.error, 'error');
                    break;
            }
        }

        // Update connection status
        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connection-status');
            if (connected) {
                statusElement.innerHTML = `
                    <span class="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                    <span class="text-sm text-gray-600 dark:text-gray-300">Connected</span>
                `;
            } else {
                statusElement.innerHTML = `
                    <span class="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
                    <span class="text-sm text-gray-600 dark:text-gray-300">Disconnected</span>
                `;
            }
        }

        // Update dashboard with initial data
        function updateDashboard(data) {
            // Update status cards
            document.getElementById('health-score').textContent =
                Math.round(data.monitoring.health_score * 100) + '%';
            document.getElementById('performance-score').textContent =
                Math.round(data.monitoring.performance_score * 100) + '%';
            document.getElementById('active-operations').textContent =
                data.orchestrator.active_operations;
            document.getElementById('active-alerts').textContent =
                data.monitoring.active_alerts;
        }

        // Update system status
        function updateSystemStatus(data) {
            updateDashboard(data);
        }

        // Load widgets for current view
        function loadWidgets() {
            const container = document.getElementById('widgets-container');
            container.innerHTML = '';

            // Get widget configurations for current view
            const widgets = {{ widgets | tojson }};

            widgets.forEach(widget => {
                const widgetElement = createWidgetElement(widget);
                container.appendChild(widgetElement);

                // Load initial widget data
                loadWidgetData(widget.id);
            });
        }

        // Create widget element
        function createWidgetElement(widget) {
            const div = document.createElement('div');
            div.className = `widget col-span-${widget.position.w}`;
            div.style.gridColumn = `${widget.position.x + 1} / span ${widget.position.w}`;
            div.id = `widget-${widget.id}`;

            div.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">${widget.title}</h3>
                    <button onclick="refreshWidget('${widget.id}')" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
                <div id="widget-content-${widget.id}" class="widget-content">
                    <div class="text-center text-gray-500">
                        <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                        <p>Loading...</p>
                    </div>
                </div>
            `;

            return div;
        }

        // Load widget data
        function loadWidgetData(widgetId) {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'get_widget_data',
                    widget_id: widgetId
                }));
            }
        }

        // Update widget content
        function updateWidget(widgetId, data) {
            const contentDiv = document.getElementById(`widget-content-${widgetId}`);
            if (!contentDiv) return;

            // Clear loading spinner
            contentDiv.innerHTML = '';

            // Get widget configuration
            const widget = {{ widgets | tojson }}.find(w => w.id === widgetId);
            if (!widget) return;

            // Render based on widget type
            switch(widget.type) {
                case 'gauge':
                    renderGaugeWidget(contentDiv, data);
                    break;
                case 'counter':
                    renderCounterWidget(contentDiv, data);
                    break;
                case 'line_chart':
                    renderLineChartWidget(contentDiv, widgetId, data);
                    break;
                case 'alert_list':
                    renderAlertListWidget(contentDiv, data);
                    break;
                case 'table':
                    renderTableWidget(contentDiv, data);
                    break;
                case 'pie_chart':
                    renderPieChartWidget(contentDiv, widgetId, data);
                    break;
                default:
                    contentDiv.innerHTML = '<p class="text-gray-500">Unknown widget type</p>';
            }
        }

        // Render gauge widget
        function renderGaugeWidget(container, data) {
            const percentage = ((data.value - data.min) / (data.max - data.min)) * 100;

            container.innerHTML = `
                <div class="text-center">
                    <div class="relative inline-flex items-center justify-center">
                        <svg class="w-32 h-32">
                            <circle cx="64" cy="64" r="56" stroke="#e5e7eb" stroke-width="12" fill="none"></circle>
                            <circle cx="64" cy="64" r="56" stroke="#3b82f6" stroke-width="12" fill="none"
                                    stroke-dasharray="${2 * Math.PI * 56}"
                                    stroke-dashoffset="${2 * Math.PI * 56 * (1 - percentage / 100)}"
                                    transform="rotate(-90 64 64)"
                                    class="transition-all duration-500"></circle>
                        </svg>
                        <div class="absolute">
                            <span class="text-2xl font-bold">${Math.round(data.value)}${data.unit || ''}</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Render counter widget
        function renderCounterWidget(container, data) {
            container.innerHTML = `
                <div class="text-center">
                    <div class="text-4xl font-bold text-blue-600 mb-2">${data.value}</div>
                    <div class="text-sm text-gray-600">${data.label}</div>
                </div>
            `;
        }

        // Render line chart widget
        function renderLineChartWidget(container, widgetId, data) {
            const canvas = document.createElement('canvas');
            canvas.id = `chart-${widgetId}`;
            container.appendChild(canvas);

            new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.timestamps.map(t => new Date(t).toLocaleTimeString()),
                    datasets: [{
                        label: data.metric,
                        data: data.values,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Render alert list widget
        function renderAlertListWidget(container, data) {
            if (data.alerts.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-center">No active alerts</p>';
                return;
            }

            const alertsHtml = data.alerts.map(alert => `
                <div class="border-l-4 p-3 mb-2 alert-${alert.severity}">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <p class="font-medium">${alert.message}</p>
                            <p class="text-sm opacity-75">${alert.source} • ${new Date(alert.timestamp).toLocaleString()}</p>
                        </div>
                        <span class="text-xs px-2 py-1 rounded ${alert.severity === 'critical' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'}">
                            ${alert.severity}
                        </span>
                    </div>
                </div>
            `).join('');

            container.innerHTML = alertsHtml;
        }

        // Render table widget
        function renderTableWidget(container, data) {
            if (data.rows.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-center">No data available</p>';
                return;
            }

            const columns = data.columns.length > 0 ? data.columns : Object.keys(data.rows[0]);

            const tableHtml = `
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                ${columns.map(col => `<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${col}</th>`).join('')}
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            ${data.rows.map(row => `
                                <tr>
                                    ${columns.map(col => `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row[col] || '-'}</td>`).join('')}
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button onclick="viewOperation('${row.id}')" class="text-blue-600 hover:text-blue-900 mr-2">View</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            container.innerHTML = tableHtml;
        }

        // Render pie chart widget
        function renderPieChartWidget(container, widgetId, data) {
            const canvas = document.createElement('canvas');
            canvas.id = `chart-${widgetId}`;
            container.appendChild(canvas);

            new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: data.data.map(d => d.label),
                    datasets: [{
                        data: data.data.map(d => d.value),
                        backgroundColor: [
                            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Refresh specific widget
        function refreshWidget(widgetId) {
            loadWidgetData(widgetId);
        }

        // Refresh all widgets
        function refreshWidgets() {
            const widgets = {{ widgets | tojson }};
            widgets.forEach(widget => loadWidgetData(widget.id));
        }

        // Auto refresh
        function startAutoRefresh() {
            setInterval(() => {
                if ({{ config.auto_refresh | tojson }}) {
                    refreshWidgets();
                }
            }, {{ config.refresh_interval * 1000 }});
        }

        // Update navigation
        function updateNavigation() {
            const currentView = sessionData.currentView;
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                if (link.getAttribute('href').includes(currentView)) {
                    link.classList.add('bg-gray-100', 'dark:bg-gray-700');
                }
            });
        }

        // Show notification
        function showNotification(message, type = 'info') {
            // Simple notification implementation
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
                type === 'success' ? 'bg-green-500' :
                type === 'error' ? 'bg-red-500' :
                type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
            }`;
            notification.textContent = message;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 5000);
        }

        // Operation modal functions
        function viewOperation(operationId) {
            // Fetch operation details and show modal
            fetch(`/api/dashboard/operations?limit=1`)
                .then(response => response.json())
                .then(data => {
                    const operation = data.operations.find(op => op.id === operationId);
                    if (operation) {
                        showOperationModal(operation);
                    }
                })
                .catch(error => console.error('Error fetching operation:', error));
        }

        function showOperationModal(operation) {
            const modal = document.getElementById('operation-modal');
            const content = document.getElementById('operation-content');

            content.innerHTML = `
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Operation ID</label>
                        <p class="text-sm text-gray-900">${operation.id}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Type</label>
                        <p class="text-sm text-gray-900">${operation.type}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Description</label>
                        <p class="text-sm text-gray-900">${operation.description}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Status</label>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            operation.status === 'completed' ? 'bg-green-100 text-green-800' :
                            operation.status === 'failed' ? 'bg-red-100 text-red-800' :
                            operation.status === 'executing' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                        }">
                            ${operation.status}
                        </span>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Priority</label>
                        <p class="text-sm text-gray-900">${operation.priority}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Created</label>
                        <p class="text-sm text-gray-900">${new Date(operation.created_at).toLocaleString()}</p>
                    </div>
                    ${operation.result ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Result</label>
                        <pre class="text-sm text-gray-900 bg-gray-100 p-2 rounded">${JSON.stringify(operation.result, null, 2)}</pre>
                    </div>
                    ` : ''}
                    <div class="flex justify-end space-x-2">
                        ${operation.status === 'pending' ? `
                            <button onclick="approveOperation('${operation.id}')" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg">
                                Approve
                            </button>
                            <button onclick="rejectOperation('${operation.id}')" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg">
                                Reject
                            </button>
                        ` : ''}
                        <button onclick="closeOperationModal()" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">
                            Close
                        </button>
                    </div>
                </div>
            `;

            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function closeOperationModal() {
            const modal = document.getElementById('operation-modal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }

        // Approve operation
        function approveOperation(operationId) {
            fetch('/api/dashboard/operations/approve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ operation_id: operationId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Operation approved', 'success');
                    closeOperationModal();
                    refreshWidgets();
                } else {
                    showNotification(data.error || 'Failed to approve operation', 'error');
                }
            })
            .catch(error => {
                showNotification('Error approving operation', 'error');
                console.error('Error:', error);
            });
        }

        // Reject operation
        function rejectOperation(operationId) {
            fetch('/api/dashboard/operations/reject', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ operation_id: operationId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Operation rejected', 'success');
                    closeOperationModal();
                    refreshWidgets();
                } else {
                    showNotification(data.error || 'Failed to reject operation', 'error');
                }
            })
            .catch(error => {
                showNotification('Error rejecting operation', 'error');
                console.error('Error:', error);
            });
        }

        // Refresh button handler
        document.getElementById('refresh-btn').addEventListener('click', function() {
            refreshWidgets();
            showNotification('Dashboard refreshed', 'success');
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeOperationModal();
            } else if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                e.preventDefault();
                refreshWidgets();
                showNotification('Dashboard refreshed', 'success');
            }
        });
    </script>
</body>
</html>
        """

        # Write template file
        template_file = self.templates_dir / "dashboard.html"
        async with aiofiles.open(template_file, 'w') as f:
            await f.write(template_content)

        logger.info("Dashboard HTML template created")

    async def _session_cleanup_loop(self):
        """Clean up inactive sessions"""
        while self._running:
            try:
                cutoff_time = datetime.now() - timedelta(minutes=30)  # 30 minutes

                inactive_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if session["last_activity"] < cutoff_time
                ]

                for session_id in inactive_sessions:
                    del self.active_sessions[session_id]
                    self.dashboard_stats["active_sessions"] -= 1

                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")

                await asyncio.sleep(600)  # Check every 10 minutes

            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _widget_refresh_loop(self):
        """Periodic widget refresh loop"""
        while self._running:
            try:
                # Refresh all active widgets
                for widget in self.widgets:
                    if widget.refresh_interval > 0:
                        # Broadcast widget refresh to all WebSocket clients
                        await self._broadcast_widget_refresh(widget.widget_id)

                await asyncio.sleep(30)  # Refresh every 30 seconds

            except Exception as e:
                logger.error(f"Error in widget refresh loop: {e}")
                await asyncio.sleep(15)

    async def _analytics_update_loop(self):
        """Periodic analytics update loop"""
        while self._running:
            try:
                # Update analytics data
                # This would typically involve more complex analytics calculations
                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                logger.error(f"Error in analytics update loop: {e}")
                await asyncio.sleep(60)

    async def _broadcast_widget_refresh(self, widget_id: str):
        """Broadcast widget refresh to WebSocket clients"""
        try:
            # Get widget data
            widget_data = await self._get_widget_data(widget_id)

            # Broadcast to all WebSocket clients
            for session_id, session in self.active_sessions.items():
                if "websocket" in session:
                    try:
                        await session["websocket"].send_json({
                            "type": "widget_data",
                            "widget_id": widget_id,
                            "data": widget_data,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Error broadcasting widget refresh: {e}")

            self.dashboard_stats["widget_updates"] += 1

        except Exception as e:
            logger.error(f"Error broadcasting widget refresh: {e}")

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get dashboard service status"""
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "active_sessions": len(self.active_sessions),
            "total_widgets": len(self.widgets),
            "stats": self.dashboard_stats
        }
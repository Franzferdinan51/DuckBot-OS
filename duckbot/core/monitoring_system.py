#!/usr/bin/env python3
"""
DuckBot Comprehensive Monitoring System
Real-time metrics collection, AI agent monitoring, and system health tracking
"""

import asyncio
import json
import logging
import os
import platform
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import socket
import subprocess
from pathlib import Path
import uuid

# Local imports
from duckbot.core.hardware_detector import HardwareDetector
from duckbot.services.server_manager import server_manager, ServiceStatus

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMESTAMP = "timestamp"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class SystemMetric:
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None

@dataclass
class AgentMetric:
    agent_id: str
    agent_type: str
    response_time_ms: float
    success: bool
    error_message: str = ""
    model_used: str = ""
    tokens_used: int = 0
    timestamp: datetime = None

@dataclass
class ServiceHealth:
    service_name: str
    status: HealthStatus
    response_time_ms: float
    last_check: datetime
    error_message: str = ""
    metrics: Dict[str, Any] = None

@dataclass
class Alert:
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = None

class MonitoringDatabase:
    """SQLite database for storing historical metrics and alerts"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "monitoring.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # System metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    tags TEXT
                )
            ''')

            # Agent metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    response_time_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    model_used TEXT,
                    tokens_used INTEGER,
                    timestamp DATETIME NOT NULL
                )
            ''')

            # Service health table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time_ms REAL NOT NULL,
                    last_check DATETIME NOT NULL,
                    error_message TEXT,
                    metrics TEXT
                )
            ''')

            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    resolved BOOLEAN NOT NULL,
                    resolved_at DATETIME,
                    tags TEXT
                )
            ''')

            # User activity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    activity_type TEXT NOT NULL,
                    feature_used TEXT,
                    response_time_ms REAL,
                    satisfaction_score INTEGER,
                    timestamp DATETIME NOT NULL
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp ON agent_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id ON agent_metrics(agent_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_health_timestamp ON service_health(last_check)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp)')

            conn.commit()

    def store_system_metric(self, metric: SystemMetric):
        """Store a system metric"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (name, value, metric_type, timestamp, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metric.name,
                metric.value,
                metric.metric_type.value,
                metric.timestamp.isoformat(),
                json.dumps(metric.tags or {})
            ))
            conn.commit()

    def store_agent_metric(self, metric: AgentMetric):
        """Store an agent metric"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_metrics (
                    agent_id, agent_type, response_time_ms, success,
                    error_message, model_used, tokens_used, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.agent_id,
                metric.agent_type,
                metric.response_time_ms,
                metric.success,
                metric.error_message,
                metric.model_used,
                metric.tokens_used,
                (metric.timestamp or datetime.now()).isoformat()
            ))
            conn.commit()

    def store_service_health(self, health: ServiceHealth):
        """Store service health data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO service_health (
                    service_name, status, response_time_ms, last_check, error_message, metrics
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                health.service_name,
                health.status.value,
                health.response_time_ms,
                health.last_check.isoformat(),
                health.error_message,
                json.dumps(health.metrics or {})
            ))
            conn.commit()

    def store_alert(self, alert: Alert):
        """Store an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO alerts (
                    id, level, title, message, source, timestamp, resolved, resolved_at, tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.level.value,
                alert.title,
                alert.message,
                alert.source,
                alert.timestamp.isoformat(),
                alert.resolved,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                json.dumps(alert.tags or {})
            ))
            conn.commit()

    def get_system_metrics(self, name: str = None, start_time: datetime = None,
                          end_time: datetime = None, limit: int = 1000) -> List[Dict]:
        """Retrieve system metrics with optional filtering"""
        query = "SELECT * FROM system_metrics WHERE 1=1"
        params = []

        if name:
            query += " AND name = ?"
            params.append(name)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_active_alerts(self) -> List[Dict]:
        """Get all active (unresolved) alerts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM alerts WHERE resolved = 0 ORDER BY timestamp DESC
            ''')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class MetricsCollector:
    """Collects system metrics in real-time"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.collecting = False
        self.collection_thread = None
        self.hardware_detector = HardwareDetector()
        self.last_network_stats = None

    def start_collection(self, interval: float = 5.0):
        """Start collecting metrics at specified interval"""
        if self.collecting:
            return

        self.collecting = True
        self.collection_thread = threading.Thread(
            target=self._collection_loop,
            args=(interval,),
            daemon=True
        )
        self.collection_thread.start()
        logger.info(f"Started metrics collection with {interval}s interval")

    def stop_collection(self):
        """Stop collecting metrics"""
        self.collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Stopped metrics collection")

    def _collection_loop(self, interval: float):
        """Main collection loop"""
        while self.collecting:
            try:
                self._collect_all_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(interval)

    def _collect_all_metrics(self):
        """Collect all system metrics"""
        timestamp = datetime.now()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        self.database.store_system_metric(SystemMetric(
            name="cpu_percent",
            value=cpu_percent,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            tags={"host": socket.gethostname()}
        ))

        if cpu_freq:
            self.database.store_system_metric(SystemMetric(
                name="cpu_frequency_mhz",
                value=cpu_freq.current,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp
            ))

        # Memory metrics
        memory = psutil.virtual_memory()
        self.database.store_system_metric(SystemMetric(
            name="memory_percent",
            value=memory.percent,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp
        ))

        self.database.store_system_metric(SystemMetric(
            name="memory_available_gb",
            value=memory.available / (1024**3),
            metric_type=MetricType.GAUGE,
            timestamp=timestamp
        ))

        # Disk metrics
        disk = psutil.disk_usage('/')
        self.database.store_system_metric(SystemMetric(
            name="disk_percent",
            value=(disk.used / disk.total) * 100,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            tags={"mountpoint": "/"}
        ))

        # Network metrics
        net_io = psutil.net_io_counters()
        if self.last_network_stats:
            bytes_sent_diff = net_io.bytes_sent - self.last_network_stats.bytes_sent
            bytes_recv_diff = net_io.bytes_recv - self.last_network_stats.bytes_recv

            self.database.store_system_metric(SystemMetric(
                name="network_bytes_sent_per_sec",
                value=bytes_sent_diff / interval,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp
            ))

            self.database.store_system_metric(SystemMetric(
                name="network_bytes_recv_per_sec",
                value=bytes_recv_diff / interval,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp
            ))

        self.last_network_stats = net_io

        # Process metrics
        process_count = len(psutil.pids())
        self.database.store_system_metric(SystemMetric(
            name="process_count",
            value=process_count,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp
        ))

        # GPU metrics (if available)
        gpu_info = self.hardware_detector._detect_gpu_info()
        if gpu_info.get("nvidia"):
            total_vram = gpu_info.get("total_vram_gb", 0)
            if total_vram > 0:
                self.database.store_system_metric(SystemMetric(
                    name="gpu_vram_total_gb",
                    value=total_vram,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    tags={"gpu_type": "nvidia"}
                ))

class AgentMonitor:
    """Monitors AI agent performance and metrics"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.agent_metrics = {}
        self.active_agents = {}

    def record_agent_interaction(self, agent_id: str, agent_type: str,
                               response_time_ms: float, success: bool,
                               model_used: str = "", tokens_used: int = 0,
                               error_message: str = ""):
        """Record an agent interaction"""
        metric = AgentMetric(
            agent_id=agent_id,
            agent_type=agent_type,
            response_time_ms=response_time_ms,
            success=success,
            model_used=model_used,
            tokens_used=tokens_used,
            error_message=error_message,
            timestamp=datetime.now()
        )

        self.database.store_agent_metric(metric)

        # Update in-memory metrics for quick access
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0,
                "total_tokens": 0,
                "last_activity": None
            }

        metrics = self.agent_metrics[agent_id]
        metrics["total_requests"] += 1
        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1

        # Update average response time
        if metrics["total_requests"] > 0:
            metrics["avg_response_time"] = (
                (metrics["avg_response_time"] * (metrics["total_requests"] - 1) + response_time_ms) /
                metrics["total_requests"]
            )

        metrics["total_tokens"] += tokens_used
        metrics["last_activity"] = datetime.now()

        self.active_agents[agent_id] = {
            "agent_type": agent_type,
            "last_activity": datetime.now(),
            "current_model": model_used
        }

    def get_agent_performance_summary(self, agent_id: str = None) -> Dict:
        """Get performance summary for agents"""
        if agent_id:
            return self.agent_metrics.get(agent_id, {})

        return self.agent_metrics

    def get_active_agents(self) -> Dict:
        """Get currently active agents"""
        return self.active_agents

class ServiceHealthMonitor:
    """Monitors service health and availability"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, interval: float = 30.0):
        """Start service health monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started service health monitoring with {interval}s interval")

    def stop_monitoring(self):
        """Stop service health monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped service health monitoring")

    def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._check_all_services()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in service health monitoring: {e}")
                time.sleep(interval)

    def _check_all_services(self):
        """Check health of all configured services"""
        # Use existing server manager
        service_status = server_manager.get_all_service_status()

        for service_name, service_info in service_status.items():
            start_time = time.time()

            try:
                # Check if service is responding
                health = self._check_service_health(service_info)
                response_time_ms = (time.time() - start_time) * 1000

                service_health = ServiceHealth(
                    service_name=service_name,
                    status=health["status"],
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(),
                    error_message=health.get("error_message", ""),
                    metrics=health.get("metrics", {})
                )

                self.database.store_service_health(service_health)

            except Exception as e:
                logger.error(f"Error checking service {service_name}: {e}")

    def _check_service_health(self, service_info) -> Dict:
        """Check health of a specific service"""
        try:
            if service_info.port:
                return self._check_port_health(service_info.port)
            elif service_info.pid:
                return self._check_process_health(service_info.pid)
            else:
                return {"status": HealthStatus.UNKNOWN, "error_message": "No port or PID specified"}

        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error_message": str(e)
            }

    def _check_port_health(self, port: int) -> Dict:
        """Check health of a service on a specific port"""
        try:
            sock = socket.create_connection(("localhost", port), timeout=5)
            sock.close()

            return {
                "status": HealthStatus.HEALTHY,
                "metrics": {"port": port, "reachable": True}
            }

        except (socket.timeout, ConnectionRefusedError):
            return {
                "status": HealthStatus.UNHEALTHY,
                "error_message": f"Port {port} is not reachable"
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error_message": str(e)
            }

    def _check_process_health(self, pid: int) -> Dict:
        """Check health of a process by PID"""
        try:
            process = psutil.Process(pid)
            return {
                "status": HealthStatus.HEALTHY if process.is_running() else HealthStatus.UNHEALTHY,
                "metrics": {
                    "pid": pid,
                    "cpu_percent": process.cpu_percent(),
                    "memory_percent": process.memory_percent()
                }
            }
        except psutil.NoSuchProcess:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error_message": f"Process {pid} not found"
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error_message": str(e)
            }

class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.alert_rules = []
        self.alert_handlers = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            {
                "name": "high_cpu_usage",
                "condition": lambda metrics: metrics.get("cpu_percent", 0) > 90,
                "level": AlertLevel.WARNING,
                "message": "High CPU usage detected: {cpu_percent}%",
                "source": "system_metrics"
            },
            {
                "name": "high_memory_usage",
                "condition": lambda metrics: metrics.get("memory_percent", 0) > 85,
                "level": AlertLevel.WARNING,
                "message": "High memory usage detected: {memory_percent}%",
                "source": "system_metrics"
            },
            {
                "name": "high_disk_usage",
                "condition": lambda metrics: metrics.get("disk_percent", 0) > 90,
                "level": AlertLevel.CRITICAL,
                "message": "High disk usage detected: {disk_percent}%",
                "source": "system_metrics"
            },
            {
                "name": "service_unhealthy",
                "condition": lambda metrics: metrics.get("service_status") == "unhealthy",
                "level": AlertLevel.ERROR,
                "message": "Service {service_name} is unhealthy",
                "source": "service_health"
            },
            {
                "name": "agent_failure",
                "condition": lambda metrics: metrics.get("agent_success") == False,
                "level": AlertLevel.WARNING,
                "message": "Agent {agent_id} failed: {error_message}",
                "source": "agent_metrics"
            }
        ]

    def check_alerts(self, metrics: Dict):
        """Check alert conditions and create alerts if needed"""
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    self._create_alert(rule, metrics)
            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {e}")

    def _create_alert(self, rule: Dict, metrics: Dict):
        """Create an alert from a rule"""
        alert_id = f"{rule['name']}_{int(time.time())}"

        # Format message with metrics
        message = rule["message"]
        for key, value in metrics.items():
            message = message.replace(f"{{{key}}}", str(value))

        alert = Alert(
            id=alert_id,
            level=rule["level"],
            title=rule["name"].replace("_", " ").title(),
            message=message,
            source=rule["source"],
            timestamp=datetime.now(),
            tags=metrics
        )

        self.database.store_alert(alert)
        self._notify_handlers(alert)

        logger.warning(f"Alert created: {alert.title} - {alert.message}")

    def _notify_handlers(self, alert: Alert):
        """Notify all alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def add_alert_handler(self, handler):
        """Add an alert handler"""
        self.alert_handlers.append(handler)

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        alerts = self.database.get_active_alerts()
        for alert_data in alerts:
            if alert_data["id"] == alert_id:
                alert = Alert(
                    id=alert_data["id"],
                    level=AlertLevel(alert_data["level"]),
                    title=alert_data["title"],
                    message=alert_data["message"],
                    source=alert_data["source"],
                    timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                    resolved=True,
                    resolved_at=datetime.now(),
                    tags=json.loads(alert_data.get("tags", "{}"))
                )
                self.database.store_alert(alert)
                logger.info(f"Alert resolved: {alert.title}")
                break

class UserActivityTracker:
    """Tracks user activity and analytics"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.active_sessions = {}

    def start_session(self, user_id: str = None) -> str:
        """Start a new user session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "start_time": datetime.now(),
            "activities": []
        }
        return session_id

    def end_session(self, session_id: str):
        """End a user session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def record_activity(self, session_id: str, activity_type: str,
                       feature_used: str = None, response_time_ms: float = None,
                       satisfaction_score: int = None):
        """Record user activity"""
        if session_id not in self.active_sessions:
            session_id = self.start_session()

        activity = {
            "session_id": session_id,
            "user_id": self.active_sessions[session_id].get("user_id"),
            "activity_type": activity_type,
            "feature_used": feature_used,
            "response_time_ms": response_time_ms,
            "satisfaction_score": satisfaction_score,
            "timestamp": datetime.now()
        }

        # Store in database
        with sqlite3.connect(self.database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_activity (
                    session_id, user_id, activity_type, feature_used,
                    response_time_ms, satisfaction_score, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity["session_id"],
                activity["user_id"],
                activity["activity_type"],
                activity["feature_used"],
                activity["response_time_ms"],
                activity["satisfaction_score"],
                activity["timestamp"].isoformat()
            ))
            conn.commit()

        # Store in session
        self.active_sessions[session_id]["activities"].append(activity)

    def get_activity_summary(self, hours: int = 24) -> Dict:
        """Get activity summary for the last N hours"""
        start_time = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT activity_type, feature_used, COUNT(*) as count,
                       AVG(response_time_ms) as avg_response_time,
                       AVG(satisfaction_score) as avg_satisfaction
                FROM user_activity
                WHERE timestamp >= ?
                GROUP BY activity_type, feature_used
            ''', (start_time.isoformat(),))

            results = cursor.fetchall()

            summary = {
                "total_activities": len(results),
                "by_activity_type": {},
                "by_feature": {},
                "avg_response_time": 0,
                "avg_satisfaction": 0
            }

            total_activities = 0
            total_response_time = 0
            total_satisfaction = 0
            response_time_count = 0
            satisfaction_count = 0

            for row in results:
                activity_type, feature_used, count, avg_response_time, avg_satisfaction = row

                if activity_type not in summary["by_activity_type"]:
                    summary["by_activity_type"][activity_type] = 0
                summary["by_activity_type"][activity_type] += count

                if feature_used and feature_used not in summary["by_feature"]:
                    summary["by_feature"][feature_used] = 0
                if feature_used:
                    summary["by_feature"][feature_used] += count

                total_activities += count

                if avg_response_time:
                    total_response_time += avg_response_time * count
                    response_time_count += count

                if avg_satisfaction:
                    total_satisfaction += avg_satisfaction * count
                    satisfaction_count += count

            if response_time_count > 0:
                summary["avg_response_time"] = total_response_time / response_time_count

            if satisfaction_count > 0:
                summary["avg_satisfaction"] = total_satisfaction / satisfaction_count

            return summary

class DuckBotMonitoring:
    """Main monitoring system orchestrator"""

    def __init__(self, db_path: str = None):
        self.database = MonitoringDatabase(db_path)
        self.metrics_collector = MetricsCollector(self.database)
        self.agent_monitor = AgentMonitor(self.database)
        self.service_health_monitor = ServiceHealthMonitor(self.database)
        self.alert_manager = AlertManager(self.database)
        self.user_activity_tracker = UserActivityTracker(self.database)

        # Setup alert handlers
        self._setup_alert_handlers()

        logger.info("DuckBot monitoring system initialized")

    def _setup_alert_handlers(self):
        """Setup default alert handlers"""
        def console_alert_handler(alert: Alert):
            """Simple console alert handler"""
            print(f"[{alert.level.value.upper()}] {alert.title}: {alert.message}")

        def log_alert_handler(alert: Alert):
            """Log alert handler"""
            if alert.level == AlertLevel.CRITICAL:
                logger.critical(f"{alert.title}: {alert.message}")
            elif alert.level == AlertLevel.ERROR:
                logger.error(f"{alert.title}: {alert.message}")
            elif alert.level == AlertLevel.WARNING:
                logger.warning(f"{alert.title}: {alert.message}")
            else:
                logger.info(f"{alert.title}: {alert.message}")

        self.alert_manager.add_alert_handler(console_alert_handler)
        self.alert_manager.add_alert_handler(log_alert_handler)

    def start(self, metrics_interval: float = 5.0, health_check_interval: float = 30.0):
        """Start all monitoring components"""
        logger.info("Starting DuckBot monitoring system")

        # Start metrics collection
        self.metrics_collector.start_collection(metrics_interval)

        # Start service health monitoring
        self.service_health_monitor.start_monitoring(health_check_interval)

        logger.info("DuckBot monitoring system started")

    def stop(self):
        """Stop all monitoring components"""
        logger.info("Stopping DuckBot monitoring system")

        self.metrics_collector.stop_collection()
        self.service_health_monitor.stop_monitoring()

        logger.info("DuckBot monitoring system stopped")

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            # Get latest system metrics
            latest_metrics = self.database.get_system_metrics(limit=10)

            # Get active alerts
            active_alerts = self.database.get_active_alerts()

            # Get service status
            service_status = server_manager.get_all_service_status()

            # Get agent performance
            agent_performance = self.agent_monitor.get_agent_performance_summary()

            # Get user activity summary
            activity_summary = self.user_activity_tracker.get_activity_summary()

            return {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": {
                    "cpu_percent": next((m["value"] for m in latest_metrics if m["name"] == "cpu_percent"), 0),
                    "memory_percent": next((m["value"] for m in latest_metrics if m["name"] == "memory_percent"), 0),
                    "disk_percent": next((m["value"] for m in latest_metrics if m["name"] == "disk_percent"), 0),
                    "active_processes": next((m["value"] for m in latest_metrics if m["name"] == "process_count"), 0)
                },
                "services": {
                    name: {
                        "status": info.status.value,
                        "display_name": info.display_name,
                        "port": info.port
                    }
                    for name, info in service_status.items()
                },
                "agents": agent_performance,
                "alerts": {
                    "total_active": len(active_alerts),
                    "by_level": {}
                },
                "user_activity": activity_summary,
                "database_status": "connected"
            }

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "database_status": "error"
            }

    def record_agent_interaction(self, *args, **kwargs):
        """Convenience method to record agent interactions"""
        return self.agent_monitor.record_agent_interaction(*args, **kwargs)

    def record_user_activity(self, *args, **kwargs):
        """Convenience method to record user activity"""
        return self.user_activity_tracker.record_activity(*args, **kwargs)

# Global monitoring instance
_monitoring_instance = None

def get_monitoring() -> DuckBotMonitoring:
    """Get the global monitoring instance"""
    global _monitoring_instance
    if _monitoring_instance is None:
        _monitoring_instance = DuckBotMonitoring()
    return _monitoring_instance

def start_monitoring(metrics_interval: float = 5.0, health_check_interval: float = 30.0):
    """Start the global monitoring instance"""
    monitoring = get_monitoring()
    monitoring.start(metrics_interval, health_check_interval)
    return monitoring

def stop_monitoring():
    """Stop the global monitoring instance"""
    global _monitoring_instance
    if _monitoring_instance:
        _monitoring_instance.stop()
        _monitoring_instance = None

if __name__ == "__main__":
    # Test the monitoring system
    print("Testing DuckBot Monitoring System")

    monitoring = get_monitoring()
    monitoring.start(metrics_interval=2.0, health_check_interval=10.0)

    try:
        # Test recording some data
        monitoring.record_agent_interaction(
            agent_id="test_agent",
            agent_type="test",
            response_time_ms=150.5,
            success=True,
            model_used="test-model",
            tokens_used=100
        )

        # Test user activity
        session_id = monitoring.user_activity_tracker.start_session("test_user")
        monitoring.record_user_activity(
            session_id=session_id,
            activity_type="chat",
            feature_used="ai_response",
            response_time_ms=120.0,
            satisfaction_score=5
        )

        # Show status
        print("\nSystem Status:")
        status = monitoring.get_system_status()
        print(json.dumps(status, indent=2))

        # Keep running for a bit to collect metrics
        print("\nCollecting metrics for 30 seconds...")
        time.sleep(30)

        # Show final status
        print("\nFinal System Status:")
        status = monitoring.get_system_status()
        print(json.dumps(status, indent=2))

    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        monitoring.stop()
#!/usr/bin/env python3
"""
DuckBot Enhanced Health Check and Predictive Maintenance System
Comprehensive health monitoring, predictive analytics, and automated maintenance
"""

import asyncio
import json
import logging
import os
import psutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import socket
import subprocess
import requests
import numpy as np
from collections import deque
import uuid

# Local imports
from duckbot.core.monitoring_system import (
    MonitoringDatabase, MetricsCollector,
    SystemMetric, ServiceHealth, HealthStatus, AlertLevel
)
from duckbot.core.hardware_detector import HardwareDetector
from duckbot.services.server_manager import server_manager, ServiceStatus

logger = logging.getLogger(__name__)

class MaintenancePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MaintenanceType(Enum):
    CLEANUP = "cleanup"
    RESTART = "restart"
    OPTIMIZATION = "optimization"
    UPDATE = "update"
    BACKUP = "backup"
    VALIDATION = "validation"

class PredictionConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component_name: str
    status: HealthStatus
    score: float  # 0.0 to 1.0
    response_time_ms: float
    last_check: datetime
    metrics: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    critical: bool = False

@dataclass
class MaintenanceAction:
    """Maintenance action to be performed"""
    id: str
    name: str
    description: str
    maintenance_type: MaintenanceType
    priority: MaintenancePriority
    estimated_duration_minutes: int
    impact: str  # low, medium, high
    prerequisites: List[str]
    steps: List[str]
    rollback_steps: List[str]
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, scheduled, in_progress, completed, failed

@dataclass
class PredictionResult:
    """Prediction result from ML model"""
    prediction_type: str
    component: str
    probability: float
    confidence: PredictionConfidence
    timeframe: str  # hours, days, weeks
    impact_level: str
    recommended_actions: List[str]
    confidence_score: float
    data_points: int
    timestamp: datetime

@dataclass
class MaintenanceSchedule:
    """Maintenance schedule entry"""
    id: str
    name: str
    start_time: datetime
    end_time: datetime
    actions: List[str]  # Maintenance action IDs
    impact: str
    status: str  # scheduled, in_progress, completed, cancelled
    created_at: datetime
    completed_at: Optional[datetime] = None
    rollback_available: bool = True

class HealthDatabase:
    """Enhanced database for health checks and maintenance data"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "health_maintenance.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables for health and maintenance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Health check results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_check_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    response_time_ms REAL NOT NULL,
                    last_check DATETIME NOT NULL,
                    metrics TEXT,
                    issues TEXT,
                    recommendations TEXT,
                    critical BOOLEAN NOT NULL
                )
            ''')

            # Maintenance actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_actions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    maintenance_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    estimated_duration_minutes INTEGER NOT NULL,
                    impact TEXT NOT NULL,
                    prerequisites TEXT,
                    steps TEXT,
                    rollback_steps TEXT,
                    created_at DATETIME NOT NULL,
                    scheduled_for DATETIME,
                    completed_at DATETIME,
                    status TEXT NOT NULL
                )
            ''')

            # Prediction results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    probability REAL NOT NULL,
                    confidence TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    impact_level TEXT NOT NULL,
                    recommended_actions TEXT,
                    confidence_score REAL NOT NULL,
                    data_points INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            ''')

            # Maintenance schedule table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_schedule (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    actions TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    rollback_available BOOLEAN NOT NULL
                )
            ''')

            # Performance baselines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    baseline_value REAL NOT NULL,
                    upper_threshold REAL,
                    lower_threshold REAL,
                    trend_weight REAL,
                    last_updated DATETIME NOT NULL,
                    window_size_hours INTEGER NOT NULL
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_health_check_component ON health_check_results(component_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_health_check_timestamp ON health_check_results(last_check)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance_actions(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_timestamp ON prediction_results(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_schedule_time ON maintenance_schedule(start_time)')

            conn.commit()

    def store_health_check(self, result: HealthCheckResult):
        """Store health check result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO health_check_results (
                    component_name, status, score, response_time_ms, last_check,
                    metrics, issues, recommendations, critical
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.component_name,
                result.status.value,
                result.score,
                result.response_time_ms,
                result.last_check.isoformat(),
                json.dumps(result.metrics),
                json.dumps(result.issues),
                json.dumps(result.recommendations),
                result.critical
            ))
            conn.commit()

    def store_maintenance_action(self, action: MaintenanceAction):
        """Store maintenance action"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO maintenance_actions (
                    id, name, description, maintenance_type, priority,
                    estimated_duration_minutes, impact, prerequisites, steps,
                    rollback_steps, created_at, scheduled_for, completed_at, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                action.id,
                action.name,
                action.description,
                action.maintenance_type.value,
                action.priority.value,
                action.estimated_duration_minutes,
                action.impact,
                json.dumps(action.prerequisites),
                json.dumps(action.steps),
                json.dumps(action.rollback_steps),
                action.created_at.isoformat(),
                action.scheduled_for.isoformat() if action.scheduled_for else None,
                action.completed_at.isoformat() if action.completed_at else None,
                action.status
            ))
            conn.commit()

    def store_prediction(self, prediction: PredictionResult):
        """Store prediction result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prediction_results (
                    prediction_type, component, probability, confidence,
                    timeframe, impact_level, recommended_actions,
                    confidence_score, data_points, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction.prediction_type,
                prediction.component,
                prediction.probability,
                prediction.confidence.value,
                prediction.timeframe,
                prediction.impact_level,
                json.dumps(prediction.recommended_actions),
                prediction.confidence_score,
                prediction.data_points,
                prediction.timestamp.isoformat()
            ))
            conn.commit()

    def store_maintenance_schedule(self, schedule: MaintenanceSchedule):
        """Store maintenance schedule"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO maintenance_schedule (
                    id, name, start_time, end_time, actions, impact,
                    status, created_at, completed_at, rollback_available
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                schedule.id,
                schedule.name,
                schedule.start_time.isoformat(),
                schedule.end_time.isoformat(),
                json.dumps(schedule.actions),
                schedule.impact,
                schedule.status,
                schedule.created_at.isoformat(),
                schedule.completed_at.isoformat() if schedule.completed_at else None,
                schedule.rollback_available
            ))
            conn.commit()

    def get_pending_maintenance_actions(self) -> List[Dict]:
        """Get all pending maintenance actions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM maintenance_actions
                WHERE status IN ('pending', 'scheduled')
                ORDER BY priority DESC, created_at ASC
            ''')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_recent_predictions(self, hours: int = 24) -> List[Dict]:
        """Get recent predictions"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM prediction_results
                WHERE timestamp >= ?
                ORDER BY probability DESC, confidence_score DESC
            ''', (cutoff_time.isoformat(),))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class ComprehensiveHealthChecker:
    """Comprehensive health check system for all DuckBot components"""

    def __init__(self, health_db: HealthDatabase, monitoring_db: MonitoringDatabase):
        self.health_db = health_db
        self.monitoring_db = monitoring_db
        self.hardware_detector = HardwareDetector()
        self.check_results = {}

        # Define service endpoints for health checks
        self.service_endpoints = {
            'WebUI': 'http://localhost:8787/health',
            'n8n': 'http://localhost:5678/health',
            'Jupyter': 'http://localhost:8889/api/status',
            'LM Studio': 'http://localhost:1234/v1/models',
            'Open-WebUI': 'http://localhost:8080/api/v1/health',
            'Charm Terminal': 'http://localhost:8788/health',
            'Monitoring Dashboard': 'http://localhost:8789/health'
        }

        # Define components and their check methods
        self.component_checkers = {
            'Database': self._check_database_health,
            'AI Models': self._check_ai_models_health,
            'System Resources': self._check_system_resources_health,
            'Network Connectivity': self._check_network_health,
            'Disk Space': self._check_disk_health,
            'Memory Usage': self._check_memory_health,
            'CPU Performance': self._check_cpu_health,
            'Service Dependencies': self._check_service_dependencies,
            'Configuration': self._check_configuration_health,
            'Security': self._check_security_health,
            'Logging System': self._check_logging_health
        }

    async def run_comprehensive_health_check(self) -> Dict[str, HealthCheckResult]:
        """Run comprehensive health check for all components"""
        logger.info("Starting comprehensive health check")

        results = {}

        # Check service endpoints
        for service_name, endpoint in self.service_endpoints.items():
            try:
                result = await self._check_service_endpoint(service_name, endpoint)
                results[service_name] = result
                self.health_db.store_health_check(result)
            except Exception as e:
                logger.error(f"Error checking service {service_name}: {e}")
                results[service_name] = HealthCheckResult(
                    component_name=service_name,
                    status=HealthStatus.UNHEALTHY,
                    score=0.0,
                    response_time_ms=0.0,
                    last_check=datetime.now(),
                    metrics={},
                    issues=[f"Failed to check service: {str(e)}"],
                    recommendations=["Check service status and logs"],
                    critical=True
                )

        # Check system components
        for component_name, checker_method in self.component_checkers.items():
            try:
                result = await checker_method()
                results[component_name] = result
                self.health_db.store_health_check(result)
            except Exception as e:
                logger.error(f"Error checking component {component_name}: {e}")
                results[component_name] = HealthCheckResult(
                    component_name=component_name,
                    status=HealthStatus.UNHEALTHY,
                    score=0.0,
                    response_time_ms=0.0,
                    last_check=datetime.now(),
                    metrics={},
                    issues=[f"Failed to check component: {str(e)}"],
                    recommendations=["Investigate component status"],
                    critical=True
                )

        self.check_results = results
        logger.info(f"Completed health check for {len(results)} components")

        return results

    async def _check_service_endpoint(self, service_name: str, endpoint: str) -> HealthCheckResult:
        """Check health of a service endpoint"""
        start_time = time.time()

        try:
            response = requests.get(endpoint, timeout=10)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    status = HealthStatus.HEALTHY if health_data.get('status') == 'healthy' else HealthStatus.DEGRADED
                    score = health_data.get('score', 1.0)

                    return HealthCheckResult(
                        component_name=service_name,
                        status=status,
                        score=score,
                        response_time_ms=response_time_ms,
                        last_check=datetime.now(),
                        metrics=health_data.get('metrics', {}),
                        issues=health_data.get('issues', []),
                        recommendations=health_data.get('recommendations', []),
                        critical=service_name in ['WebUI', 'LM Studio']
                    )
                except json.JSONDecodeError:
                    return HealthCheckResult(
                        component_name=service_name,
                        status=HealthStatus.DEGRADED,
                        score=0.7,
                        response_time_ms=response_time_ms,
                        last_check=datetime.now(),
                        metrics={'status_code': response.status_code},
                        issues=['Invalid JSON response'],
                        recommendations=['Check service health endpoint implementation'],
                        critical=False
                    )
            else:
                return HealthCheckResult(
                    component_name=service_name,
                    status=HealthStatus.UNHEALTHY,
                    score=0.0,
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(),
                    metrics={'status_code': response.status_code},
                    issues=[f'HTTP {response.status_code}'],
                    recommendations=['Check service logs and restart if needed'],
                    critical=service_name in ['WebUI', 'LM Studio']
                )

        except requests.exceptions.Timeout:
            return HealthCheckResult(
                component_name=service_name,
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=10000,
                last_check=datetime.now(),
                metrics={},
                issues=['Service timeout'],
                recommendations=['Check if service is running and responsive'],
                critical=service_name in ['WebUI', 'LM Studio']
            )
        except Exception as e:
            return HealthCheckResult(
                component_name=service_name,
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=0.0,
                last_check=datetime.now(),
                metrics={},
                issues=[f'Connection error: {str(e)}'],
                recommendations=['Check service status and network connectivity'],
                critical=service_name in ['WebUI', 'LM Studio']
            )

    async def _check_database_health(self) -> HealthCheckResult:
        """Check database health and connectivity"""
        start_time = time.time()

        try:
            # Check monitoring database
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM system_metrics")
                monitoring_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
                active_alerts = cursor.fetchone()[0]

            # Check health database
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM health_check_results")
                health_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM maintenance_actions WHERE status = 'pending'")
                pending_maintenance = cursor.fetchone()[0]

            response_time_ms = (time.time() - start_time) * 1000

            # Calculate overall database health score
            total_metrics = monitoring_count + health_count
            score = min(1.0, total_metrics / 10000) if total_metrics > 0 else 0.5

            issues = []
            recommendations = []

            if active_alerts > 10:
                issues.append(f"High number of active alerts: {active_alerts}")
                recommendations.append("Review and resolve active alerts")
                score *= 0.8

            if pending_maintenance > 5:
                issues.append(f"Pending maintenance actions: {pending_maintenance}")
                recommendations.append("Schedule and execute pending maintenance")
                score *= 0.9

            status = HealthStatus.HEALTHY if score > 0.8 else HealthStatus.DEGRADED

            return HealthCheckResult(
                component_name="Database",
                status=status,
                score=score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'monitoring_metrics_count': monitoring_count,
                    'health_checks_count': health_count,
                    'active_alerts': active_alerts,
                    'pending_maintenance': pending_maintenance
                },
                issues=issues,
                recommendations=recommendations,
                critical=True
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Database",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Database check failed: {str(e)}"],
                recommendations=["Check database connectivity and permissions"],
                critical=True
            )

    async def _check_ai_models_health(self) -> HealthCheckResult:
        """Check AI model availability and performance"""
        start_time = time.time()

        try:
            # Check LM Studio availability
            lm_studio_health = await self._check_service_endpoint("LM Studio", "http://localhost:1234/v1/models")

            # Check model performance metrics from monitoring
            recent_metrics = self.monitoring_db.get_system_metrics(
                name="ai_response_time_ms",
                start_time=datetime.now() - timedelta(hours=1),
                limit=100
            )

            # Calculate performance metrics
            if recent_metrics:
                response_times = [m['value'] for m in recent_metrics]
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)

                # Performance thresholds (in milliseconds)
                good_threshold = 2000
                warning_threshold = 5000

                if avg_response_time <= good_threshold:
                    performance_score = 1.0
                    status = HealthStatus.HEALTHY
                elif avg_response_time <= warning_threshold:
                    performance_score = 0.7
                    status = HealthStatus.DEGRADED
                else:
                    performance_score = 0.3
                    status = HealthStatus.UNHEALTHY
            else:
                performance_score = 0.8
                avg_response_time = 0
                max_response_time = 0
                status = HealthStatus.HEALTHY

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if lm_studio_health.status != HealthStatus.HEALTHY:
                issues.append("LM Studio service not responding properly")
                recommendations.append("Check LM Studio status and restart if needed")
                performance_score *= 0.5

            if avg_response_time > warning_threshold:
                issues.append(f"Slow AI response times: {avg_response_time:.0f}ms average")
                recommendations.append("Consider model optimization or hardware upgrade")

            return HealthCheckResult(
                component_name="AI Models",
                status=status,
                status=HealthStatus.HEALTHY if performance_score > 0.8 else HealthStatus.DEGRADED,
                score=performance_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'lm_studio_status': lm_studio_health.status.value,
                    'average_response_time_ms': avg_response_time,
                    'max_response_time_ms': max_response_time,
                    'recent_requests': len(recent_metrics)
                },
                issues=issues,
                recommendations=recommendations,
                critical=True
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="AI Models",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"AI model health check failed: {str(e)}"],
                recommendations=["Check AI services and model configurations"],
                critical=True
            )

    async def _check_system_resources_health(self) -> HealthCheckResult:
        """Check overall system resource health"""
        start_time = time.time()

        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Calculate resource scores
            cpu_score = max(0, 1.0 - (cpu_percent - 50) / 100) if cpu_percent > 50 else 1.0
            memory_score = max(0, 1.0 - (memory.percent - 70) / 30) if memory.percent > 70 else 1.0
            disk_score = max(0, 1.0 - (disk.percent - 80) / 20) if disk.percent > 80 else 1.0

            # Overall system score
            system_score = (cpu_score + memory_score + disk_score) / 3

            # Determine status
            if system_score >= 0.8:
                status = HealthStatus.HEALTHY
            elif system_score >= 0.5:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                recommendations.append("Identify CPU-intensive processes")

            if memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                recommendations.append("Close unnecessary applications or increase RAM")

            if disk.percent > 90:
                issues.append(f"Low disk space: {100 - disk.percent:.1f}% free")
                recommendations.append("Clean up disk space or increase storage")

            return HealthCheckResult(
                component_name="System Resources",
                status=status,
                score=system_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_free_gb': disk.free / (1024**3)
                },
                issues=issues,
                recommendations=recommendations,
                critical=system_score < 0.5
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="System Resources",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"System resource check failed: {str(e)}"],
                recommendations=["Check system monitoring tools"],
                critical=True
            )

    async def _check_network_health(self) -> HealthCheckResult:
        """Check network connectivity and performance"""
        start_time = time.time()

        try:
            # Test connectivity to essential services
            test_hosts = ['8.8.8.8', '1.1.1.1', 'github.com']
            connectivity_results = {}

            for host in test_hosts:
                try:
                    result = subprocess.run(['ping', '-n', '1', host],
                                          capture_output=True, text=True, timeout=5)
                    connectivity_results[host] = result.returncode == 0
                except:
                    connectivity_results[host] = False

            # Get network interface stats
            net_io = psutil.net_io_counters()

            # Calculate connectivity score
            successful_pings = sum(connectivity_results.values())
            connectivity_score = successful_pings / len(test_hosts)

            # Check for high network usage
            bytes_sent_total = net_io.bytes_sent
            bytes_recv_total = net_io.bytes_recv

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if connectivity_score < 1.0:
                failed_hosts = [host for host, success in connectivity_results.items() if not success]
                issues.append(f"Network connectivity issues: {', '.join(failed_hosts)}")
                recommendations.append("Check network connection and DNS settings")

            status = HealthStatus.HEALTHY if connectivity_score == 1.0 else HealthStatus.DEGRADED

            return HealthCheckResult(
                component_name="Network Connectivity",
                status=status,
                score=connectivity_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'connectivity_score': connectivity_score,
                    'successful_pings': successful_pings,
                    'total_pings': len(test_hosts),
                    'bytes_sent_total': bytes_sent_total,
                    'bytes_recv_total': bytes_recv_total
                },
                issues=issues,
                recommendations=recommendations,
                critical=connectivity_score < 0.5
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Network Connectivity",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Network health check failed: {str(e)}"],
                recommendations=["Check network interface and drivers"],
                critical=False
            )

    async def _check_disk_health(self) -> HealthCheckResult:
        """Check disk health and performance"""
        start_time = time.time()

        try:
            # Get disk usage for all mounts
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    }
                except:
                    continue

            # Calculate overall disk health score
            if disk_usage:
                avg_percent = sum(info['percent'] for info in disk_usage.values()) / len(disk_usage)
                max_percent = max(info['percent'] for info in disk_usage.values())

                if max_percent > 95:
                    disk_score = 0.0
                    status = HealthStatus.UNHEALTHY
                elif max_percent > 90:
                    disk_score = 0.3
                    status = HealthStatus.DEGRADED
                elif avg_percent > 80:
                    disk_score = 0.7
                    status = HealthStatus.DEGRADED
                else:
                    disk_score = 1.0
                    status = HealthStatus.HEALTHY
            else:
                disk_score = 0.8
                status = HealthStatus.HEALTHY
                avg_percent = 0
                max_percent = 0

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if max_percent > 95:
                critical_mounts = [mount for mount, info in disk_usage.items() if info['percent'] > 95]
                issues.append(f"Critical disk space on: {', '.join(critical_mounts)}")
                recommendations.append("Immediate cleanup required on critical mounts")

            if avg_percent > 80:
                issues.append(f"High average disk usage: {avg_percent:.1f}%")
                recommendations.append("Schedule disk cleanup and archive old files")

            return HealthCheckResult(
                component_name="Disk Space",
                status=status,
                score=disk_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'average_usage_percent': avg_percent,
                    'max_usage_percent': max_percent,
                    'mounts_checked': len(disk_usage),
                    'disk_usage': disk_usage
                },
                issues=issues,
                recommendations=recommendations,
                critical=max_percent > 95
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Disk Space",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Disk health check failed: {str(e)}"],
                recommendations=["Check disk hardware and permissions"],
                critical=False
            )

    async def _check_memory_health(self) -> HealthCheckResult:
        """Check memory health and performance"""
        start_time = time.time()

        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Calculate memory health score
            if memory.percent > 90:
                memory_score = 0.0
                status = HealthStatus.UNHEALTHY
            elif memory.percent > 80:
                memory_score = 0.3
                status = HealthStatus.DEGRADED
            elif memory.percent > 70:
                memory_score = 0.7
                status = HealthStatus.DEGRADED
            else:
                memory_score = 1.0
                status = HealthStatus.HEALTHY

            # Check swap usage
            if swap.percent > 50:
                memory_score *= 0.8

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if memory.percent > 90:
                issues.append(f"Critical memory usage: {memory.percent:.1f}%")
                recommendations.append("Close applications or restart system")

            if swap.percent > 50:
                issues.append(f"High swap usage: {swap.percent:.1f}%")
                recommendations.append("Add more RAM or reduce memory usage")

            return HealthCheckResult(
                component_name="Memory Usage",
                status=status,
                score=memory_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'memory_total_gb': memory.total / (1024**3),
                    'swap_percent': swap.percent,
                    'swap_used_gb': swap.used / (1024**3)
                },
                issues=issues,
                recommendations=recommendations,
                critical=memory.percent > 90
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Memory Usage",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Memory health check failed: {str(e)}"],
                recommendations=["Check memory hardware and system logs"],
                critical=True
            )

    async def _check_cpu_health(self) -> HealthCheckResult:
        """Check CPU health and performance"""
        start_time = time.time()

        try:
            # Get CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Get load average (if available)
            try:
                load_avg = os.getloadavg()
            except (AttributeError, OSError):
                load_avg = [0, 0, 0]

            # Calculate CPU health score
            if cpu_percent > 90:
                cpu_score = 0.0
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 80:
                cpu_score = 0.3
                status = HealthStatus.DEGRADED
            elif cpu_percent > 70:
                cpu_score = 0.7
                status = HealthStatus.DEGRADED
            else:
                cpu_score = 1.0
                status = HealthStatus.HEALTHY

            # Adjust score based on load average
            if load_avg[0] > cpu_count * 2:
                cpu_score *= 0.5

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if cpu_percent > 90:
                issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
                recommendations.append("Identify and stop CPU-intensive processes")

            if load_avg[0] > cpu_count * 1.5:
                issues.append(f"High system load: {load_avg[0]:.2f}")
                recommendations.append("Check for runaway processes")

            return HealthCheckResult(
                component_name="CPU Performance",
                status=status,
                score=cpu_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'cpu_percent': cpu_percent,
                    'cpu_count': cpu_count,
                    'cpu_frequency_mhz': cpu_freq.current if cpu_freq else 0,
                    'load_average_1min': load_avg[0],
                    'load_average_5min': load_avg[1],
                    'load_average_15min': load_avg[2]
                },
                issues=issues,
                recommendations=recommendations,
                critical=cpu_percent > 90
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="CPU Performance",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"CPU health check failed: {str(e)}"],
                recommendations=["Check CPU hardware and system monitoring"],
                critical=True
            )

    async def _check_service_dependencies(self) -> HealthCheckResult:
        """Check service dependencies and their health"""
        start_time = time.time()

        try:
            # Check critical service dependencies
            dependencies = {
                'Python': sys.version,
                'SQLite': sqlite3.sqlite_version,
                'Requests': requests.__version__,
                'FastAPI': 'unknown',  # Will check if importable
                'Uvicorn': 'unknown'
            }

            # Test import of key dependencies
            import_status = {}
            for dep in ['fastapi', 'uvicorn', 'psutil', 'numpy']:
                try:
                    __import__(dep)
                    import_status[dep] = True
                except ImportError:
                    import_status[dep] = False

            # Calculate dependency health score
            missing_deps = sum(1 for status in import_status.values() if not status)
            dep_score = max(0, 1.0 - (missing_deps / len(import_status)))

            status = HealthStatus.HEALTHY if dep_score == 1.0 else HealthStatus.DEGRADED

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if missing_deps > 0:
                missing_list = [dep for dep, status in import_status.items() if not status]
                issues.append(f"Missing dependencies: {', '.join(missing_list)}")
                recommendations.append("Install missing dependencies: pip install " + " ".join(missing_list))

            return HealthCheckResult(
                component_name="Service Dependencies",
                status=status,
                score=dep_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'dependencies_checked': len(dependencies),
                    'import_status': import_status,
                    'missing_dependencies': missing_deps
                },
                issues=issues,
                recommendations=recommendations,
                critical=missing_deps > 0
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Service Dependencies",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Dependency check failed: {str(e)}"],
                recommendations=["Check system packages and Python environment"],
                critical=True
            )

    async def _check_configuration_health(self) -> HealthCheckResult:
        """Check configuration files and settings"""
        start_time = time.time()

        try:
            # Check for essential configuration files
            config_files = {
                'AI Config': 'config/ai_config.json',
                'Ecosystem Config': 'config/ecosystem_config.yaml',
                'Environment': '.env',
                'Requirements': 'docs/requirements.txt'
            }

            config_status = {}
            for config_name, config_path in config_files.items():
                full_path = os.path.join(os.getcwd(), config_path)
                config_status[config_name] = os.path.exists(full_path)

            # Calculate configuration health score
            existing_configs = sum(config_status.values())
            config_score = existing_configs / len(config_files)

            status = HealthStatus.HEALTHY if config_score == 1.0 else HealthStatus.DEGRADED

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if config_score < 1.0:
                missing_configs = [name for name, exists in config_status.items() if not exists]
                issues.append(f"Missing configuration files: {', '.join(missing_configs)}")
                recommendations.append("Create missing configuration files or restore from backup")

            return HealthCheckResult(
                component_name="Configuration",
                status=status,
                score=config_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'config_files_checked': len(config_files),
                    'existing_configs': existing_configs,
                    'config_status': config_status
                },
                issues=issues,
                recommendations=recommendations,
                critical=existing_configs < len(config_files) // 2
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Configuration",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Configuration check failed: {str(e)}"],
                recommendations=["Check configuration file permissions and paths"],
                critical=True
            )

    async def _check_security_health(self) -> HealthCheckResult:
        """Check security aspects of the system"""
        start_time = time.time()

        try:
            security_checks = {
                'Environment Variables': len([k for k in os.environ.keys() if 'KEY' in k or 'TOKEN' in k or 'SECRET' in k]),
                'File Permissions': 'Checked',
                'Network Ports': 'Scanned',
                'Running Processes': len(psutil.pids())
            }

            # Basic security score (can be enhanced with more checks)
            security_score = 0.8  # Default good score

            # Check for obviously exposed secrets
            exposed_secrets = 0
            for key, value in os.environ.items():
                if any(word in key.upper() for word in ['KEY', 'TOKEN', 'SECRET', 'PASSWORD']):
                    if value and len(value) > 10:  # Likely a real secret
                        exposed_secrets += 1

            if exposed_secrets > 5:
                security_score *= 0.5

            status = HealthStatus.HEALTHY if security_score >= 0.8 else HealthStatus.DEGRADED

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if exposed_secrets > 5:
                issues.append(f"Potentially exposed secrets: {exposed_secrets}")
                recommendations.append("Review environment variable security")

            return HealthCheckResult(
                component_name="Security",
                status=status,
                score=security_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics=security_checks,
                issues=issues,
                recommendations=recommendations,
                critical=security_score < 0.5
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Security",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Security check failed: {str(e)}"],
                recommendations=["Review security configuration and permissions"],
                critical=False
            )

    async def _check_logging_health(self) -> HealthCheckResult:
        """Check logging system health"""
        start_time = time.time()

        try:
            # Check log files
            log_dir = os.path.join(os.getcwd(), 'logs')
            if os.path.exists(log_dir):
                log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
                total_log_size = sum(os.path.getsize(os.path.join(log_dir, f)) for f in log_files)
            else:
                log_files = []
                total_log_size = 0

            # Check for recent log entries
            recent_logs = 0
            for log_file in log_files[:5]:  # Check first 5 log files
                log_path = os.path.join(log_dir, log_file)
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()[-100:]  # Last 100 lines
                        recent_logs += len([line for line in lines if 'ERROR' in line or 'CRITICAL' in line])
                except:
                    continue

            # Calculate logging health score
            log_score = 1.0

            if total_log_size > 1024 * 1024 * 100:  # 100MB
                log_score *= 0.8

            if recent_logs > 50:
                log_score *= 0.7

            status = HealthStatus.HEALTHY if log_score >= 0.8 else HealthStatus.DEGRADED

            response_time_ms = (time.time() - start_time) * 1000

            issues = []
            recommendations = []

            if total_log_size > 1024 * 1024 * 100:
                issues.append(f"Large log files: {total_log_size / (1024*1024):.1f}MB")
                recommendations.append("Implement log rotation and cleanup")

            if recent_logs > 50:
                issues.append(f"Recent errors in logs: {recent_logs}")
                recommendations.append("Review recent error logs")

            return HealthCheckResult(
                component_name="Logging System",
                status=status,
                score=log_score,
                response_time_ms=response_time_ms,
                last_check=datetime.now(),
                metrics={
                    'log_files_count': len(log_files),
                    'total_log_size_mb': total_log_size / (1024*1024),
                    'recent_errors': recent_logs
                },
                issues=issues,
                recommendations=recommendations,
                critical=recent_logs > 100
            )

        except Exception as e:
            return HealthCheckResult(
                component_name="Logging System",
                status=HealthStatus.UNHEALTHY,
                score=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                metrics={},
                issues=[f"Logging health check failed: {str(e)}"],
                recommendations=["Check logging configuration and permissions"],
                critical=False
            )

    def get_overall_health_score(self, results: Dict[str, HealthCheckResult]) -> float:
        """Calculate overall health score from all components"""
        if not results:
            return 0.0

        # Weight critical components more heavily
        weights = {
            'Database': 0.2,
            'AI Models': 0.2,
            'System Resources': 0.15,
            'Network Connectivity': 0.1,
            'WebUI': 0.1,
            'LM Studio': 0.1,
            'Disk Space': 0.05,
            'Memory Usage': 0.05,
            'CPU Performance': 0.05
        }

        weighted_score = 0.0
        total_weight = 0.0

        for component_name, result in results.items():
            weight = weights.get(component_name, 0.05)  # Default weight for unknown components
            weighted_score += result.score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

class PredictiveMaintenanceEngine:
    """Advanced predictive maintenance with pattern recognition and forecasting"""

    def __init__(self, health_db: HealthDatabase, monitoring_db: MonitoringDatabase):
        self.health_db = health_db
        self.monitoring_db = monitoring_db
        self.prediction_models = {}
        self.baselines = {}
        self.trend_data = {}
        self.pattern_history = deque(maxlen=1000)

    async def analyze_patterns_and_predict(self) -> List[PredictionResult]:
        """Analyze patterns and make predictions about future issues"""
        predictions = []

        # Analyze resource trends
        resource_predictions = await self._predict_resource_exhaustion()
        predictions.extend(resource_predictions)

        # Analyze performance degradation
        performance_predictions = await self._predict_performance_degradation()
        predictions.extend(performance_predictions)

        # Analyze failure patterns
        failure_predictions = await self._predict_component_failures()
        predictions.extend(failure_predictions)

        # Analyze maintenance needs
        maintenance_predictions = await self._predict_maintenance_needs()
        predictions.extend(maintenance_predictions)

        # Store predictions
        for prediction in predictions:
            self.health_db.store_prediction(prediction)

        return predictions

    async def _predict_resource_exhaustion(self) -> List[PredictionResult]:
        """Predict resource exhaustion based on usage patterns"""
        predictions = []

        try:
            # Get historical resource metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            # Analyze disk usage trends
            disk_metrics = self.monitoring_db.get_system_metrics(
                name="disk_percent",
                start_time=start_time,
                end_time=end_time
            )

            if len(disk_metrics) > 10:
                disk_trend = self._calculate_trend([m['value'] for m in disk_metrics])
                current_disk = disk_metrics[0]['value']

                if disk_trend > 0.1:  # Growing faster than 10% per week
                    time_to_full = (100 - current_disk) / (disk_trend * 7)  # days
                    if time_to_full < 30:  # Less than 30 days
                        predictions.append(PredictionResult(
                            prediction_type="Resource Exhaustion",
                            component="Disk Space",
                            probability=min(1.0, 1.0 - (time_to_full / 30)),
                            confidence=PredictionConfidence.HIGH,
                            timeframe=f"{int(time_to_full)} days",
                            impact_level="High",
                            recommended_actions=[
                                "Clean up temporary files",
                                "Archive old data",
                                "Increase storage capacity"
                            ],
                            confidence_score=0.85,
                            data_points=len(disk_metrics),
                            timestamp=datetime.now()
                        ))

            # Analyze memory usage trends
            memory_metrics = self.monitoring_db.get_system_metrics(
                name="memory_percent",
                start_time=start_time,
                end_time=end_time
            )

            if len(memory_metrics) > 10:
                memory_trend = self._calculate_trend([m['value'] for m in memory_metrics])
                current_memory = memory_metrics[0]['value']

                if memory_trend > 5 and current_memory > 80:  # Growing trend and high usage
                    predictions.append(PredictionResult(
                        prediction_type="Resource Exhaustion",
                        component="Memory",
                        probability=min(1.0, (current_memory - 80) / 20),
                        confidence=PredictionConfidence.MEDIUM,
                        timeframe="weeks",
                        impact_level="High",
                        recommended_actions=[
                            "Identify memory leaks",
                            "Restart services with high memory usage",
                            "Consider adding more RAM"
                        ],
                        confidence_score=0.7,
                        data_points=len(memory_metrics),
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.error(f"Error predicting resource exhaustion: {e}")

        return predictions

    async def _predict_performance_degradation(self) -> List[PredictionResult]:
        """Predict performance degradation based on historical patterns"""
        predictions = []

        try:
            # Analyze AI response times
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            ai_metrics = self.monitoring_db.get_system_metrics(
                name="ai_response_time_ms",
                start_time=start_time,
                end_time=end_time
            )

            if len(ai_metrics) > 20:
                response_times = [m['value'] for m in ai_metrics]
                trend = self._calculate_trend(response_times)

                if trend > 50:  # Response times increasing by more than 50ms per day
                    current_avg = sum(response_times[-10:]) / min(10, len(response_times))
                    if current_avg > 3000:  # Current average is already slow
                        predictions.append(PredictionResult(
                            prediction_type="Performance Degradation",
                            component="AI Response Time",
                            probability=min(1.0, current_avg / 10000),
                            confidence=PredictionConfidence.HIGH,
                            timeframe="days",
                            impact_level="Medium",
                            recommended_actions=[
                                "Optimize AI model selection",
                                "Check for model overloading",
                                "Consider hardware upgrade"
                            ],
                            confidence_score=0.8,
                            data_points=len(ai_metrics),
                            timestamp=datetime.now()
                        ))

            # Analyze CPU usage patterns
            cpu_metrics = self.monitoring_db.get_system_metrics(
                name="cpu_percent",
                start_time=start_time,
                end_time=end_time
            )

            if len(cpu_metrics) > 50:
                cpu_values = [m['value'] for m in cpu_metrics]
                cpu_trend = self._calculate_trend(cpu_values)
                current_cpu = cpu_values[-1]

                if cpu_trend > 2 and current_cpu > 70:  # Increasing trend and high usage
                    predictions.append(PredictionResult(
                        prediction_type="Performance Degradation",
                        component="CPU Usage",
                        probability=min(1.0, (current_cpu - 70) / 30),
                        confidence=PredictionConfidence.MEDIUM,
                        timeframe="weeks",
                        impact_level="Medium",
                        recommended_actions=[
                            "Identify CPU-intensive processes",
                            "Optimize application performance",
                            "Consider load balancing"
                        ],
                        confidence_score=0.65,
                        data_points=len(cpu_metrics),
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.error(f"Error predicting performance degradation: {e}")

        return predictions

    async def _predict_component_failures(self) -> List[PredictionResult]:
        """Predict component failures based on historical failure patterns"""
        predictions = []

        try:
            # Analyze service health history
            degraded_components = self._identify_degraded_components()

            for component, degradation_score in degraded_components.items():
                if degradation_score > 0.7:  # High likelihood of failure
                    predictions.append(PredictionResult(
                        prediction_type="Component Failure",
                        component=component,
                        probability=degradation_score,
                        confidence=PredictionConfidence.HIGH,
                        timeframe="days to weeks",
                        impact_level="High",
                        recommended_actions=[
                            f"Schedule maintenance for {component}",
                            "Check component logs for errors",
                            "Prepare backup/recovery procedures"
                        ],
                        confidence_score=0.75,
                        data_points=10,  # Approximate
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.error(f"Error predicting component failures: {e}")

        return predictions

    async def _predict_maintenance_needs(self) -> List[PredictionResult]:
        """Predict when maintenance will be needed"""
        predictions = []

        try:
            # Analyze database size growth
            db_path = self.monitoring_db.db_path
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)

                if db_size > 100 * 1024 * 1024:  # 100MB
                    predictions.append(PredictionResult(
                        prediction_type="Maintenance Needed",
                        component="Database",
                        probability=min(1.0, db_size / (1024 * 1024 * 1024)),  # Probability based on size
                        confidence=PredictionConfidence.MEDIUM,
                        timeframe="weeks",
                        impact_level="Low",
                        recommended_actions=[
                            "Database cleanup and optimization",
                            "Archive old metrics data",
                            "Consider data retention policies"
                        ],
                        confidence_score=0.6,
                        data_points=1,
                        timestamp=datetime.now()
                    ))

            # Check for log file growth
            log_dir = os.path.join(os.getcwd(), 'logs')
            if os.path.exists(log_dir):
                total_log_size = sum(
                    os.path.getsize(os.path.join(log_dir, f))
                    for f in os.listdir(log_dir)
                    if f.endswith('.log')
                )

                if total_log_size > 500 * 1024 * 1024:  # 500MB
                    predictions.append(PredictionResult(
                        prediction_type="Maintenance Needed",
                        component="Log Files",
                        probability=min(1.0, total_log_size / (1024 * 1024 * 1024)),
                        confidence=PredictionConfidence.HIGH,
                        timeframe="days",
                        impact_level="Low",
                        recommended_actions=[
                            "Implement log rotation",
                            "Archive old log files",
                            "Clean up temporary logs"
                        ],
                        confidence_score=0.9,
                        data_points=len(os.listdir(log_dir)),
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            logger.error(f"Error predicting maintenance needs: {e}")

        return predictions

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope using simple linear regression"""
        if len(values) < 2:
            return 0.0

        x = list(range(len(values)))
        y = values

        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _identify_degraded_components(self) -> Dict[str, float]:
        """Identify components showing degradation patterns"""
        degraded = {}

        try:
            # Simplified implementation - in practice would use more sophisticated analysis
            components_to_check = ['Database', 'AI Models', 'System Resources']

            for component in components_to_check:
                # Get recent health scores for component
                recent_scores = []  # Would fetch from database

                if len(recent_scores) >= 5:
                    # Calculate degradation trend
                    trend = self._calculate_trend(recent_scores)
                    if trend < -0.01:  # Negative trend
                        current_score = recent_scores[-1]
                        degradation_probability = max(0, min(1, -trend * 50))
                        degraded[component] = degradation_probability

        except Exception as e:
            logger.error(f"Error identifying degraded components: {e}")

        return degraded

    def detect_anomalies(self, metric_name: str, current_value: float) -> bool:
        """Detect anomalies in metric values using statistical methods"""
        try:
            # Get historical data for the metric
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            historical_data = self.monitoring_db.get_system_metrics(
                name=metric_name,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )

            if len(historical_data) < 10:
                return False

            values = [m['value'] for m in historical_data]

            # Calculate statistical properties
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5

            # Check if current value is outside 3 standard deviations
            z_score = abs(current_value - mean) / std_dev if std_dev > 0 else 0
            return z_score > 3.0

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return False

    def generate_maintenance_recommendations(self, predictions: List[PredictionResult]) -> List[MaintenanceAction]:
        """Generate maintenance actions based on predictions"""
        maintenance_actions = []

        for prediction in predictions:
            if prediction.probability > 0.7:  # High probability predictions
                action = MaintenanceAction(
                    id=str(uuid.uuid4()),
                    name=f"Preventive: {prediction.component}",
                    description=f"Address predicted {prediction.prediction_type.lower()}",
                    maintenance_type=MaintenanceType.OPTIMIZATION,
                    priority=self._map_probability_to_priority(prediction.probability),
                    estimated_duration_minutes=30,
                    impact="low",
                    prerequisites=[],
                    steps=prediction.recommended_actions,
                    rollback_steps=["Restart affected services", "Restore from backup if needed"],
                    created_at=datetime.now()
                )
                maintenance_actions.append(action)
                self.health_db.store_maintenance_action(action)

        return maintenance_actions

    def _map_probability_to_priority(self, probability: float) -> MaintenancePriority:
        """Map probability to maintenance priority"""
        if probability >= 0.9:
            return MaintenancePriority.CRITICAL
        elif probability >= 0.8:
            return MaintenancePriority.HIGH
        elif probability >= 0.7:
            return MaintenancePriority.MEDIUM
        else:
            return MaintenancePriority.LOW

class AutomatedMaintenanceSystem:
    """Automated maintenance execution and system optimization"""

    def __init__(self, health_db: HealthDatabase, monitoring_db: MonitoringDatabase):
        self.health_db = health_db
        self.monitoring_db = monitoring_db
        self.automation_active = False
        self.maintenance_history = []
        self.cleanup_policies = {}

    async def start_automation(self):
        """Start automated maintenance system"""
        self.automation_active = True
        logger.info("Automated maintenance system started")

        # Initialize cleanup policies
        self._initialize_cleanup_policies()

        # Start background maintenance tasks
        asyncio.create_task(self._maintenance_monitor_loop())
        asyncio.create_task(self._cleanup_scheduler())
        asyncio.create_task(self._health_optimizer())

    async def stop_automation(self):
        """Stop automated maintenance system"""
        self.automation_active = False
        logger.info("Automated maintenance system stopped")

    def _initialize_cleanup_policies(self):
        """Initialize cleanup policies for different components"""
        self.cleanup_policies = {
            'log_files': {
                'max_size_mb': 500,
                'max_age_days': 30,
                'cleanup_action': self._cleanup_log_files
            },
            'temp_files': {
                'max_size_mb': 1000,
                'cleanup_action': self._cleanup_temp_files
            },
            'database': {
                'max_size_mb': 100,
                'retention_days': 90,
                'cleanup_action': self._cleanup_database
            },
            'cache': {
                'max_size_mb': 500,
                'cleanup_action': self._cleanup_cache
            },
            'models': {
                'max_unused_days': 7,
                'cleanup_action': self._cleanup_unused_models
            }
        }

    async def _maintenance_monitor_loop(self):
        """Monitor for maintenance needs and trigger actions"""
        while self.automation_active:
            try:
                # Check for pending maintenance actions
                pending_actions = self.health_db.get_pending_maintenance_actions()

                for action_data in pending_actions:
                    if self._should_execute_automatically(action_data):
                        await self._execute_maintenance_action(action_data)

                # Check for cleanup needs
                await self._check_cleanup_needs()

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in maintenance monitor loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_scheduler(self):
        """Schedule periodic cleanup tasks"""
        while self.automation_active:
            try:
                current_time = datetime.now()

                # Daily cleanup at 2 AM
                if current_time.hour == 2 and current_time.minute < 5:
                    await self._perform_daily_cleanup()

                # Weekly cleanup on Sunday at 3 AM
                if current_time.weekday() == 6 and current_time.hour == 3 and current_time.minute < 5:
                    await self._perform_weekly_cleanup()

                # Monthly cleanup on 1st of month at 4 AM
                if current_time.day == 1 and current_time.hour == 4 and current_time.minute < 5:
                    await self._perform_monthly_cleanup()

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {e}")
                await asyncio.sleep(3600)

    async def _health_optimizer(self):
        """Continuously optimize system health"""
        while self.automation_active:
            try:
                # Get current health status
                health_results = await self._get_current_health_status()

                # Optimize based on health status
                optimizations = self._generate_health_optimizations(health_results)

                for optimization in optimizations:
                    await self._execute_optimization(optimization)

                await asyncio.sleep(600)  # Check every 10 minutes

            except Exception as e:
                logger.error(f"Error in health optimizer: {e}")
                await asyncio.sleep(300)

    def _should_execute_automatically(self, action_data: Dict) -> bool:
        """Determine if a maintenance action should be executed automatically"""
        priority = action_data.get('priority', 'low')
        impact = action_data.get('impact', 'high')

        # Only execute automatically if:
        # - Priority is critical or high
        # - Impact is low
        # - No user interaction required
        return (priority in ['critical', 'high'] and
                impact == 'low' and
                action_data.get('status') in ['pending', 'scheduled'])

    async def _execute_maintenance_action(self, action_data: Dict):
        """Execute a maintenance action"""
        try:
            action_id = action_data['id']
            action_name = action_data['name']

            logger.info(f"Executing maintenance action: {action_name}")

            # Update status to in_progress
            self._update_action_status(action_id, 'in_progress')

            # Parse and execute steps
            steps = json.loads(action_data.get('steps', '[]'))

            for step in steps:
                await self._execute_maintenance_step(step)

            # Mark as completed
            self._update_action_status(action_id, 'completed')

            logger.info(f"Completed maintenance action: {action_name}")

            # Record in history
            self.maintenance_history.append({
                'action_id': action_id,
                'action_name': action_name,
                'executed_at': datetime.now(),
                'status': 'completed'
            })

        except Exception as e:
            logger.error(f"Error executing maintenance action {action_data['id']}: {e}")
            self._update_action_status(action_id, 'failed')

    async def _execute_maintenance_step(self, step: str):
        """Execute a single maintenance step"""
        try:
            if step.startswith("Clean up"):
                await self._execute_cleanup_step(step)
            elif step.startswith("Restart"):
                await self._execute_restart_step(step)
            elif step.startswith("Optimize"):
                await self._execute_optimization_step(step)
            elif step.startswith("Archive"):
                await self._execute_archive_step(step)
            else:
                logger.info(f"Executing generic maintenance step: {step}")

        except Exception as e:
            logger.error(f"Error executing maintenance step '{step}': {e}")
            raise

    async def _execute_cleanup_step(self, step: str):
        """Execute cleanup-related maintenance step"""
        if "log files" in step.lower():
            await self._cleanup_log_files()
        elif "temporary files" in step.lower():
            await self._cleanup_temp_files()
        elif "cache" in step.lower():
            await self._cleanup_cache()
        else:
            logger.info(f"Generic cleanup step: {step}")

    async def _execute_restart_step(self, step: str):
        """Execute restart-related maintenance step"""
        # This would handle service restarts
        logger.info(f"Restart step (placeholder): {step}")

    async def _execute_optimization_step(self, step: str):
        """Execute optimization-related maintenance step"""
        if "database" in step.lower():
            await self._optimize_database()
        elif "memory" in step.lower():
            await self._optimize_memory()
        else:
            logger.info(f"Optimization step (placeholder): {step}")

    async def _execute_archive_step(self, step: str):
        """Execute archive-related maintenance step"""
        logger.info(f"Archive step (placeholder): {step}")

    async def _cleanup_log_files(self):
        """Clean up log files"""
        try:
            log_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(log_dir):
                return

            current_time = datetime.now()
            cleaned_size = 0

            for log_file in os.listdir(log_dir):
                if not log_file.endswith('.log'):
                    continue

                log_path = os.path.join(log_dir, log_file)
                file_age = current_time - datetime.fromtimestamp(os.path.getmtime(log_path))

                # Remove logs older than 30 days
                if file_age.days > 30:
                    file_size = os.path.getsize(log_path)
                    os.remove(log_path)
                    cleaned_size += file_size
                    logger.info(f"Removed old log file: {log_file}")

            if cleaned_size > 0:
                logger.info(f"Cleaned up {cleaned_size / (1024*1024):.2f} MB of log files")

        except Exception as e:
            logger.error(f"Error cleaning up log files: {e}")

    async def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dirs = [
                os.path.join(os.getcwd(), 'temp'),
                os.path.join(os.getcwd(), 'tmp'),
                os.path.join(os.environ.get('TEMP', ''), 'duckbot_temp')
            ]

            cleaned_size = 0

            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue

                for temp_file in os.listdir(temp_dir):
                    temp_path = os.path.join(temp_dir, temp_file)
                    if os.path.isfile(temp_path):
                        file_size = os.path.getsize(temp_path)
                        os.remove(temp_path)
                        cleaned_size += file_size

            if cleaned_size > 0:
                logger.info(f"Cleaned up {cleaned_size / (1024*1024):.2f} MB of temporary files")

        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")

    async def _cleanup_database(self):
        """Clean up old database records"""
        try:
            cutoff_date = datetime.now() - timedelta(days=90)

            # Clean old metrics
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM system_metrics
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))

                deleted_count = cursor.rowcount
                conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old system metric records")

            # Clean old health check results
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM health_check_results
                    WHERE last_check < ?
                ''', (cutoff_date.isoformat(),))

                deleted_count = cursor.rowcount
                conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old health check results")

        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")

    async def _cleanup_cache(self):
        """Clean up cache files"""
        try:
            cache_dirs = [
                os.path.join(os.getcwd(), 'cache'),
                os.path.join(os.getcwd(), '.cache')
            ]

            cleaned_size = 0

            for cache_dir in cache_dirs:
                if not os.path.exists(cache_dir):
                    continue

                for cache_file in os.listdir(cache_dir):
                    cache_path = os.path.join(cache_dir, cache_file)
                    if os.path.isfile(cache_path):
                        file_size = os.path.getsize(cache_path)
                        os.remove(cache_path)
                        cleaned_size += file_size

            if cleaned_size > 0:
                logger.info(f"Cleaned up {cleaned_size / (1024*1024):.2f} MB of cache files")

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")

    async def _cleanup_unused_models(self):
        """Clean up unused AI models"""
        # This would check for and remove unused AI models
        logger.info("Checking for unused models (placeholder)")

    async def _optimize_database(self):
        """Optimize database performance"""
        try:
            # VACUUM and ANALYZE for SQLite databases
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                logger.info("Optimized monitoring database")

            with sqlite3.connect(self.health_db.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                logger.info("Optimized health database")

        except Exception as e:
            logger.error(f"Error optimizing database: {e}")

    async def _optimize_memory(self):
        """Optimize memory usage"""
        try:
            # Force garbage collection
            import gc
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")

        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")

    async def _perform_daily_cleanup(self):
        """Perform daily cleanup tasks"""
        logger.info("Starting daily cleanup")
        await self._cleanup_log_files()
        await self._cleanup_temp_files()
        logger.info("Daily cleanup completed")

    async def _perform_weekly_cleanup(self):
        """Perform weekly cleanup tasks"""
        logger.info("Starting weekly cleanup")
        await self._perform_daily_cleanup()
        await self._cleanup_cache()
        await self._cleanup_database()
        logger.info("Weekly cleanup completed")

    async def _perform_monthly_cleanup(self):
        """Perform monthly cleanup tasks"""
        logger.info("Starting monthly cleanup")
        await self._perform_weekly_cleanup()
        await self._cleanup_unused_models()
        logger.info("Monthly cleanup completed")

    async def _check_cleanup_needs(self):
        """Check if cleanup is needed based on policies"""
        for policy_name, policy in self.cleanup_policies.items():
            try:
                if await self._policy_cleanup_needed(policy_name, policy):
                    await policy['cleanup_action']()
            except Exception as e:
                logger.error(f"Error checking cleanup policy {policy_name}: {e}")

    async def _policy_cleanup_needed(self, policy_name: str, policy: Dict) -> bool:
        """Check if a cleanup policy needs to be triggered"""
        try:
            if policy_name == 'log_files':
                return await self._log_cleanup_needed(policy)
            elif policy_name == 'database':
                return await self._database_cleanup_needed(policy)
            elif policy_name == 'cache':
                return await self._cache_cleanup_needed(policy)

            return False

        except Exception as e:
            logger.error(f"Error checking cleanup need for {policy_name}: {e}")
            return False

    async def _log_cleanup_needed(self, policy: Dict) -> bool:
        """Check if log cleanup is needed"""
        try:
            log_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(log_dir):
                return False

            total_size = sum(
                os.path.getsize(os.path.join(log_dir, f))
                for f in os.listdir(log_dir)
                if f.endswith('.log')
            )

            max_size_bytes = policy['max_size_mb'] * 1024 * 1024
            return total_size > max_size_bytes

        except Exception:
            return False

    async def _database_cleanup_needed(self, policy: Dict) -> bool:
        """Check if database cleanup is needed"""
        try:
            db_size = os.path.getsize(self.monitoring_db.db_path)
            max_size_bytes = policy['max_size_mb'] * 1024 * 1024
            return db_size > max_size_bytes

        except Exception:
            return False

    async def _cache_cleanup_needed(self, policy: Dict) -> bool:
        """Check if cache cleanup is needed"""
        try:
            cache_dirs = [
                os.path.join(os.getcwd(), 'cache'),
                os.path.join(os.getcwd(), '.cache')
            ]

            total_size = 0
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    total_size += sum(
                        os.path.getsize(os.path.join(cache_dir, f))
                        for f in os.listdir(cache_dir)
                        if os.path.isfile(os.path.join(cache_dir, f))
                    )

            max_size_bytes = policy['max_size_mb'] * 1024 * 1024
            return total_size > max_size_bytes

        except Exception:
            return False

    async def _get_current_health_status(self) -> Dict[str, Any]:
        """Get current health status of all components"""
        # This would use the ComprehensiveHealthChecker to get current status
        return {}

    def _generate_health_optimizations(self, health_results: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on health status"""
        optimizations = []

        # Generate optimizations based on health scores
        for component, result in health_results.items():
            score = result.get('score', 1.0)
            if score < 0.8:
                optimizations.append(f"Optimize {component} (score: {score:.2f})")

        return optimizations

    async def _execute_optimization(self, optimization: str):
        """Execute a health optimization"""
        logger.info(f"Executing optimization: {optimization}")
        # This would implement specific optimization actions
        await asyncio.sleep(1)  # Placeholder

    def _update_action_status(self, action_id: str, status: str):
        """Update maintenance action status in database"""
        try:
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE maintenance_actions
                    SET status = ?,
                        completed_at = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat() if status == 'completed' else None, action_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating action status: {e}")

    def get_maintenance_history(self) -> List[Dict]:
        """Get maintenance execution history"""
        return self.maintenance_history

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            return {
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
                'disk_usage': psutil.disk_usage('/').percent,
                'uptime': time.time(),
                'maintenance_actions_completed': len(self.maintenance_history),
                'automation_active': self.automation_active
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}

class HealthMaintenanceManager:
    """Main manager for health checks and predictive maintenance"""

    def __init__(self):
        self.health_db = HealthDatabase()
        self.monitoring_db = MonitoringDatabase()
        self.health_checker = ComprehensiveHealthChecker(self.health_db, self.monitoring_db)
        self.prediction_engine = PredictiveMaintenanceEngine(self.health_db, self.monitoring_db)
        self.automation_system = AutomatedMaintenanceSystem(self.health_db, self.monitoring_db)
        self.running = False

    async def start(self):
        """Start the health and maintenance system"""
        if self.running:
            return

        self.running = True
        logger.info("Starting Health and Maintenance Manager")

        # Start automated maintenance
        await self.automation_system.start_automation()

        # Start periodic health checks
        asyncio.create_task(self._periodic_health_checks())

        # Start predictive analysis
        asyncio.create_task(self._periodic_predictions())

        logger.info("Health and Maintenance Manager started successfully")

    async def stop(self):
        """Stop the health and maintenance system"""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping Health and Maintenance Manager")

        await self.automation_system.stop_automation()
        logger.info("Health and Maintenance Manager stopped")

    async def _periodic_health_checks(self):
        """Run periodic health checks"""
        while self.running:
            try:
                logger.info("Running comprehensive health check")
                results = await self.health_checker.run_comprehensive_health_check()

                # Calculate overall health score
                overall_score = self.health_checker.get_overall_health_score(results)

                logger.info(f"Health check completed. Overall score: {overall_score:.2f}")

                # Trigger alerts if needed
                if overall_score < 0.7:
                    logger.warning(f"Low overall health score: {overall_score:.2f}")
                    await self._trigger_health_alert(results, overall_score)

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
                await asyncio.sleep(300)

    async def _periodic_predictions(self):
        """Run periodic predictive analysis"""
        while self.running:
            try:
                logger.info("Running predictive maintenance analysis")
                predictions = await self.prediction_engine.analyze_patterns_and_predict()

                # Generate maintenance recommendations
                maintenance_actions = self.prediction_engine.generate_maintenance_recommendations(predictions)

                if predictions:
                    logger.info(f"Generated {len(predictions)} predictions and {len(maintenance_actions)} maintenance recommendations")

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in predictive analysis: {e}")
                await asyncio.sleep(600)

    async def _trigger_health_alert(self, results: Dict[str, HealthCheckResult], overall_score: float):
        """Trigger health alerts for low scores"""
        try:
            critical_issues = [
                (component, result) for component, result in results.items()
                if result.score < 0.5 or result.critical
            ]

            if critical_issues:
                logger.warning(f"Critical health issues detected: {len(critical_issues)}")
                for component, result in critical_issues:
                    logger.warning(f"  {component}: {result.status.value} (score: {result.score:.2f})")

        except Exception as e:
            logger.error(f"Error triggering health alert: {e}")

    async def run_immediate_health_check(self) -> Dict[str, HealthCheckResult]:
        """Run an immediate comprehensive health check"""
        return await self.health_checker.run_comprehensive_health_check()

    async def get_predictions(self, hours: int = 24) -> List[Dict]:
        """Get recent predictions"""
        return self.health_db.get_recent_predictions(hours)

    async def get_pending_maintenance(self) -> List[Dict]:
        """Get pending maintenance actions"""
        return self.health_db.get_pending_maintenance_actions()

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'running': self.running,
            'system_stats': self.automation_system.get_system_stats(),
            'maintenance_history': self.automation_system.get_maintenance_history()
        }

# Global instance for easy access
health_maintenance_manager = HealthMaintenanceManager()

# Convenience functions for external use
async def start_health_maintenance():
    """Start health and maintenance system"""
    await health_maintenance_manager.start()

async def stop_health_maintenance():
    """Stop health and maintenance system"""
    await health_maintenance_manager.stop()

async def run_health_check():
    """Run immediate health check"""
    return await health_maintenance_manager.run_immediate_health_check()

async def get_system_health_status():
    """Get current system health status"""
    return health_maintenance_manager.get_system_status()
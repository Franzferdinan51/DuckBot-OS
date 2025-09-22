#!/usr/bin/env python3
"""
DuckBot Performance Analytics
Advanced system performance monitoring, bottleneck detection, and optimization insights
"""

import asyncio
import json
import logging
import sqlite3
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from pathlib import Path
import uuid

from analytics_engine import AnalyticsEngine, AnalyticsEvent, AnalyticsEventType

logger = logging.getLogger(__name__)

class PerformanceLevel(Enum):
    """Performance levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class BottleneckType(Enum):
    """Types of performance bottlenecks"""
    CPU_BOTTLENECK = "cpu_bottleneck"
    MEMORY_BOTTLENECK = "memory_bottleneck"
    DISK_BOTTLENECK = "disk_bottleneck"
    NETWORK_BOTTLENECK = "network_bottleneck"
    API_LATENCY = "api_latency"
    DATABASE_BOTTLENECK = "database_bottleneck"
    CONCURRENCY_LIMIT = "concurrency_limit"

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    disk_io_read: float
    disk_io_write: float
    network_io_sent: float
    network_io_recv: float
    load_average: float
    process_count: int
    thread_count: int

@dataclass
class ServiceMetrics:
    """Individual service performance metrics"""
    service_name: str
    response_time: float
    error_rate: float
    throughput: float
    success_rate: float
    availability: float
    timestamp: datetime

@dataclass
class BottleneckAlert:
    """Performance bottleneck alert"""
    alert_id: str
    bottleneck_type: BottleneckType
    severity: PerformanceLevel
    description: str
    affected_components: List[str]
    metrics: Dict[str, float]
    recommendations: List[str]
    detected_at: datetime
    resolved_at: Optional[datetime] = None

@dataclass
class PerformanceBenchmark:
    """Performance benchmark data"""
    benchmark_id: str
    metric_name: str
    baseline_value: float
    current_value: float
    deviation_percent: float
    trend_direction: str
    status: PerformanceLevel
    last_updated: datetime

class PerformanceAnalyzer:
    """Advanced performance analytics engine"""

    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.db_path = analytics_engine.db.db_path
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.bottlenecks: Dict[str, BottleneckAlert] = {}
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        self.is_monitoring = False
        self._initialize_analyzer()

    def _initialize_analyzer(self):
        """Initialize the performance analyzer"""
        # Create database tables
        self._create_database_tables()
        # Load existing benchmarks
        self._load_benchmarks()
        # Start monitoring
        self.start_monitoring()

    def _create_database_tables(self):
        """Create performance analytics database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # System metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage_percent REAL,
                    disk_io_read REAL,
                    disk_io_write REAL,
                    network_io_sent REAL,
                    network_io_recv REAL,
                    load_average REAL,
                    process_count INTEGER,
                    thread_count INTEGER
                )
            ''')

            # Service metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS service_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    response_time REAL,
                    error_rate REAL,
                    throughput REAL,
                    success_rate REAL,
                    availability REAL,
                    timestamp DATETIME NOT NULL
                )
            ''')

            # Bottleneck alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bottleneck_alerts (
                    alert_id TEXT PRIMARY KEY,
                    bottleneck_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    affected_components TEXT,
                    metrics TEXT,
                    recommendations TEXT,
                    detected_at DATETIME NOT NULL,
                    resolved_at DATETIME
                )
            ''')

            # Performance benchmarks table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_benchmarks (
                    benchmark_id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    baseline_value REAL,
                    current_value REAL,
                    deviation_percent REAL,
                    trend_direction TEXT,
                    status TEXT,
                    last_updated DATETIME NOT NULL
                )
            ''')

            # Performance trends table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    time_period TEXT NOT NULL,
                    trend_value REAL,
                    trend_direction TEXT,
                    confidence_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp ON service_metrics(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_service_name ON service_metrics(service_name)',
                'CREATE INDEX IF NOT EXISTS idx_bottlenecks_detected ON bottleneck_alerts(detected_at)',
                'CREATE INDEX IF NOT EXISTS idx_benchmarks_metric ON performance_benchmarks(metric_name)'
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

    def _load_benchmarks(self):
        """Load existing performance benchmarks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM performance_benchmarks')
                for row in cursor.fetchall():
                    self.benchmarks[row[1]] = PerformanceBenchmark(*row)
        except Exception as e:
            logger.error(f"Error loading benchmarks: {e}")

    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                await self._process_system_metrics(metrics)

                # Check for bottlenecks
                await self._detect_bottlenecks(metrics)

                # Update benchmarks
                await self._update_benchmarks(metrics)

                # Sleep for monitoring interval
                await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Get CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0

            # Get memory information
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get disk information
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent

            # Get disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_read = disk_io.read_bytes if disk_io else 0
            disk_io_write = disk_io.write_bytes if disk_io else 0

            # Get network I/O
            net_io = psutil.net_io_counters()
            network_io_sent = net_io.bytes_sent if net_io else 0
            network_io_recv = net_io.bytes_recv if net_io else 0

            # Get process/thread count
            process_count = len(psutil.pids())
            thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) if p.info['num_threads'])

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                disk_io_read=disk_io_read,
                disk_io_write=disk_io_write,
                network_io_sent=network_io_sent,
                network_io_recv=network_io_recv,
                load_average=load_avg,
                process_count=process_count,
                thread_count=thread_count
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                disk_io_read=0.0,
                disk_io_write=0.0,
                network_io_sent=0.0,
                network_io_recv=0.0,
                load_average=0.0,
                process_count=0,
                thread_count=0
            )

    async def _process_system_metrics(self, metrics: SystemMetrics):
        """Process and store system metrics"""
        try:
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO system_metrics
                    (timestamp, cpu_percent, memory_percent, disk_usage_percent,
                     disk_io_read, disk_io_write, network_io_sent, network_io_recv,
                     load_average, process_count, thread_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp,
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_usage_percent,
                    metrics.disk_io_read,
                    metrics.disk_io_write,
                    metrics.network_io_sent,
                    metrics.network_io_recv,
                    metrics.load_average,
                    metrics.process_count,
                    metrics.thread_count
                ))

            # Add to history
            self.metrics_history.append(metrics)

            # Track as analytics event
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type=AnalyticsEventType.PERFORMANCE_METRIC,
                timestamp=metrics.timestamp,
                metrics={
                    'cpu_usage': metrics.cpu_percent,
                    'memory_usage': metrics.memory_percent,
                    'disk_usage': metrics.disk_usage_percent,
                    'network_io': {
                        'sent': metrics.network_io_sent,
                        'recv': metrics.network_io_recv
                    },
                    'system_load': metrics.load_average
                }
            )

            await self.analytics_engine.track_event(event)

        except Exception as e:
            logger.error(f"Error processing system metrics: {e}")

    async def track_service_metrics(self, service_name: str, response_time: float,
                                  error_rate: float = 0.0, throughput: float = 0.0,
                                  success_rate: float = 100.0, availability: float = 100.0):
        """Track service-specific performance metrics"""
        try:
            metrics = ServiceMetrics(
                service_name=service_name,
                response_time=response_time,
                error_rate=error_rate,
                throughput=throughput,
                success_rate=success_rate,
                availability=availability,
                timestamp=datetime.now()
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO service_metrics
                    (service_name, response_time, error_rate, throughput,
                     success_rate, availability, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    service_name,
                    response_time,
                    error_rate,
                    throughput,
                    success_rate,
                    availability,
                    metrics.timestamp
                ))

            # Track as analytics event
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                event_type=AnalyticsEventType.PERFORMANCE_METRIC,
                timestamp=metrics.timestamp,
                feature_name=service_name,
                metrics={
                    'response_time': response_time,
                    'error_rate': error_rate,
                    'throughput': throughput,
                    'success_rate': success_rate,
                    'availability': availability
                }
            )

            await self.analytics_engine.track_event(event)

        except Exception as e:
            logger.error(f"Error tracking service metrics for {service_name}: {e}")

    async def _detect_bottlenecks(self, metrics: SystemMetrics):
        """Detect performance bottlenecks"""
        try:
            bottlenecks = []

            # CPU bottleneck
            if metrics.cpu_percent > 85:
                bottlenecks.append(BottleneckAlert(
                    alert_id=str(uuid.uuid4()),
                    bottleneck_type=BottleneckType.CPU_BOTTLENECK,
                    severity=PerformanceLevel.CRITICAL if metrics.cpu_percent > 95 else PerformanceLevel.POOR,
                    description=f"High CPU usage detected: {metrics.cpu_percent:.1f}%",
                    affected_components=["system"],
                    metrics={'cpu_percent': metrics.cpu_percent},
                    recommendations=[
                        "Identify CPU-intensive processes",
                        "Consider scaling up resources",
                        "Optimize code efficiency"
                    ],
                    detected_at=metrics.timestamp
                ))

            # Memory bottleneck
            if metrics.memory_percent > 85:
                bottlenecks.append(BottleneckAlert(
                    alert_id=str(uuid.uuid4()),
                    bottleneck_type=BottleneckType.MEMORY_BOTTLENECK,
                    severity=PerformanceLevel.CRITICAL if metrics.memory_percent > 95 else PerformanceLevel.POOR,
                    description=f"High memory usage detected: {metrics.memory_percent:.1f}%",
                    affected_components=["system"],
                    metrics={'memory_percent': metrics.memory_percent},
                    recommendations=[
                        "Identify memory-intensive processes",
                        "Clear cache if applicable",
                        "Consider adding more RAM"
                    ],
                    detected_at=metrics.timestamp
                ))

            # Disk bottleneck
            if metrics.disk_usage_percent > 90:
                bottlenecks.append(BottleneckAlert(
                    alert_id=str(uuid.uuid4()),
                    bottleneck_type=BottleneckType.DISK_BOTTLENECK,
                    severity=PerformanceLevel.CRITICAL,
                    description=f"High disk usage detected: {metrics.disk_usage_percent:.1f}%",
                    affected_components=["storage"],
                    metrics={'disk_usage_percent': metrics.disk_usage_percent},
                    recommendations=[
                        "Clean up disk space",
                        "Archive old data",
                        "Consider additional storage"
                    ],
                    detected_at=metrics.timestamp
                ))

            # Store new bottlenecks
            for bottleneck in bottlenecks:
                if bottleneck.alert_id not in self.bottlenecks:
                    self.bottlenecks[bottleneck.alert_id] = bottleneck
                    self._store_bottleneck(bottleneck)
                    logger.warning(f"New bottleneck detected: {bottleneck.description}")

        except Exception as e:
            logger.error(f"Error detecting bottlenecks: {e}")

    def _store_bottleneck(self, bottleneck: BottleneckAlert):
        """Store bottleneck alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO bottleneck_alerts
                    (alert_id, bottleneck_type, severity, description,
                     affected_components, metrics, recommendations, detected_at, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bottleneck.alert_id,
                    bottleneck.bottleneck_type.value,
                    bottleneck.severity.value,
                    bottleneck.description,
                    json.dumps(bottleneck.affected_components),
                    json.dumps(bottleneck.metrics),
                    json.dumps(bottleneck.recommendations),
                    bottleneck.detected_at,
                    bottleneck.resolved_at
                ))
        except Exception as e:
            logger.error(f"Error storing bottleneck: {e}")

    async def _update_benchmarks(self, metrics: SystemMetrics):
        """Update performance benchmarks"""
        try:
            # Update CPU benchmark
            await self._update_benchmark('cpu_usage', metrics.cpu_percent)

            # Update memory benchmark
            await self._update_benchmark('memory_usage', metrics.memory_percent)

            # Update system load benchmark
            await self._update_benchmark('system_load', metrics.load_average)

        except Exception as e:
            logger.error(f"Error updating benchmarks: {e}")

    async def _update_benchmark(self, metric_name: str, current_value: float):
        """Update a specific benchmark"""
        try:
            if metric_name not in self.benchmarks:
                # Create new benchmark
                benchmark = PerformanceBenchmark(
                    benchmark_id=str(uuid.uuid4()),
                    metric_name=metric_name,
                    baseline_value=current_value,
                    current_value=current_value,
                    deviation_percent=0.0,
                    trend_direction="stable",
                    status=PerformanceLevel.GOOD,
                    last_updated=datetime.now()
                )
            else:
                # Update existing benchmark
                benchmark = self.benchmarks[metric_name]
                baseline = benchmark.baseline_value
                deviation = ((current_value - baseline) / baseline * 100) if baseline > 0 else 0.0

                # Determine trend
                if abs(deviation) < 5:
                    trend_direction = "stable"
                elif deviation > 0:
                    trend_direction = "increasing"
                else:
                    trend_direction = "decreasing"

                # Determine status
                if metric_name == 'cpu_usage':
                    status = self._get_cpu_performance_level(current_value)
                elif metric_name == 'memory_usage':
                    status = self._get_memory_performance_level(current_value)
                elif metric_name == 'system_load':
                    status = self._get_load_performance_level(current_value)
                else:
                    status = PerformanceLevel.GOOD

                benchmark.current_value = current_value
                benchmark.deviation_percent = deviation
                benchmark.trend_direction = trend_direction
                benchmark.status = status
                benchmark.last_updated = datetime.now()

            self.benchmarks[metric_name] = benchmark
            self._store_benchmark(benchmark)

        except Exception as e:
            logger.error(f"Error updating benchmark {metric_name}: {e}")

    def _get_cpu_performance_level(self, cpu_usage: float) -> PerformanceLevel:
        """Get CPU performance level based on usage"""
        if cpu_usage < 50:
            return PerformanceLevel.EXCELLENT
        elif cpu_usage < 70:
            return PerformanceLevel.GOOD
        elif cpu_usage < 85:
            return PerformanceLevel.FAIR
        elif cpu_usage < 95:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL

    def _get_memory_performance_level(self, memory_usage: float) -> PerformanceLevel:
        """Get memory performance level based on usage"""
        if memory_usage < 60:
            return PerformanceLevel.EXCELLENT
        elif memory_usage < 75:
            return PerformanceLevel.GOOD
        elif memory_usage < 85:
            return PerformanceLevel.FAIR
        elif memory_usage < 95:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL

    def _get_load_performance_level(self, load_avg: float) -> PerformanceLevel:
        """Get load performance level based on system load"""
        cpu_count = psutil.cpu_count()
        normalized_load = load_avg / cpu_count if cpu_count > 0 else load_avg

        if normalized_load < 0.5:
            return PerformanceLevel.EXCELLENT
        elif normalized_load < 0.8:
            return PerformanceLevel.GOOD
        elif normalized_load < 1.0:
            return PerformanceLevel.FAIR
        elif normalized_load < 2.0:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL

    def _store_benchmark(self, benchmark: PerformanceBenchmark):
        """Store benchmark in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO performance_benchmarks
                    (benchmark_id, metric_name, baseline_value, current_value,
                     deviation_percent, trend_direction, status, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    benchmark.benchmark_id,
                    benchmark.metric_name,
                    benchmark.baseline_value,
                    benchmark.current_value,
                    benchmark.deviation_percent,
                    benchmark.trend_direction,
                    benchmark.status.value,
                    benchmark.last_updated
                ))
        except Exception as e:
            logger.error(f"Error storing benchmark: {e}")

    # Analytics Methods
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                # System metrics summary
                cursor = conn.execute('''
                    SELECT
                        AVG(cpu_percent) as avg_cpu,
                        MAX(cpu_percent) as max_cpu,
                        AVG(memory_percent) as avg_memory,
                        MAX(memory_percent) as max_memory,
                        AVG(load_average) as avg_load,
                        MAX(load_average) as max_load
                    FROM system_metrics
                    WHERE timestamp >= ?
                ''', (start_time,))

                system_summary = cursor.fetchone()

                # Service metrics summary
                cursor = conn.execute('''
                    SELECT
                        service_name,
                        AVG(response_time) as avg_response_time,
                        AVG(error_rate) as avg_error_rate,
                        AVG(availability) as avg_availability
                    FROM service_metrics
                    WHERE timestamp >= ?
                    GROUP BY service_name
                ''', (start_time,))

                service_summary = cursor.fetchall()

                # Active bottlenecks
                cursor = conn.execute('''
                    SELECT COUNT(*) as active_bottlenecks
                    FROM bottleneck_alerts
                    WHERE resolved_at IS NULL
                ''')

                active_bottlenecks = cursor.fetchone()[0] or 0

                return {
                    'period_hours': hours,
                    'start_time': start_time.isoformat(),
                    'system_performance': {
                        'average_cpu': system_summary[0] or 0.0,
                        'max_cpu': system_summary[1] or 0.0,
                        'average_memory': system_summary[2] or 0.0,
                        'max_memory': system_summary[3] or 0.0,
                        'average_load': system_summary[4] or 0.0,
                        'max_load': system_summary[5] or 0.0
                    },
                    'service_performance': [
                        {
                            'service': row[0],
                            'average_response_time': row[1] or 0.0,
                            'average_error_rate': row[2] or 0.0,
                            'average_availability': row[3] or 0.0
                        } for row in service_summary
                    ],
                    'active_bottlenecks': active_bottlenecks,
                    'overall_status': self._calculate_overall_status(system_summary)
                }

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

    def _calculate_overall_status(self, system_summary) -> PerformanceLevel:
        """Calculate overall system performance status"""
        avg_cpu = system_summary[0] or 0.0
        avg_memory = system_summary[2] or 0.0
        avg_load = system_summary[4] or 0.0

        cpu_status = self._get_cpu_performance_level(avg_cpu)
        memory_status = self._get_memory_performance_level(avg_memory)
        load_status = self._get_load_performance_level(avg_load)

        # Return the worst status among the three
        status_priority = {
            PerformanceLevel.CRITICAL: 4,
            PerformanceLevel.POOR: 3,
            PerformanceLevel.FAIR: 2,
            PerformanceLevel.GOOD: 1,
            PerformanceLevel.EXCELLENT: 0
        }

        worst_status = max([cpu_status, memory_status, load_status],
                          key=lambda x: status_priority[x])

        return worst_status

    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            start_time = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                # Hourly averages
                cursor = conn.execute('''
                    SELECT
                        strftime('%Y-%m-%d %H', timestamp) as hour_bucket,
                        AVG(cpu_percent) as avg_cpu,
                        AVG(memory_percent) as avg_memory,
                        AVG(load_average) as avg_load
                    FROM system_metrics
                    WHERE timestamp >= ?
                    GROUP BY hour_bucket
                    ORDER BY hour_bucket
                ''', (start_time,))

                hourly_trends = cursor.fetchall()

                # Daily averages
                cursor = conn.execute('''
                    SELECT
                        DATE(timestamp) as date,
                        AVG(cpu_percent) as avg_cpu,
                        AVG(memory_percent) as avg_memory,
                        AVG(load_average) as avg_load
                    FROM system_metrics
                    WHERE timestamp >= ?
                    GROUP BY date
                    ORDER BY date
                ''', (start_time,))

                daily_trends = cursor.fetchall()

                return {
                    'period_days': days,
                    'hourly_trends': [
                        {
                            'hour': row[0],
                            'cpu_usage': row[1] or 0.0,
                            'memory_usage': row[2] or 0.0,
                            'system_load': row[3] or 0.0
                        } for row in hourly_trends
                    ],
                    'daily_trends': [
                        {
                            'date': row[0],
                            'cpu_usage': row[1] or 0.0,
                            'memory_usage': row[2] or 0.0,
                            'system_load': row[3] or 0.0
                        } for row in daily_trends
                    ]
                }

        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {}

    def get_service_performance_comparison(self, days: int = 7) -> Dict[str, Any]:
        """Compare performance across services"""
        try:
            start_time = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT
                        service_name,
                        AVG(response_time) as avg_response_time,
                        AVG(error_rate) as avg_error_rate,
                        AVG(throughput) as avg_throughput,
                        AVG(success_rate) as avg_success_rate,
                        AVG(availability) as avg_availability,
                        COUNT(*) as measurement_count
                    FROM service_metrics
                    WHERE timestamp >= ?
                    GROUP BY service_name
                    ORDER BY avg_response_time DESC
                ''', (start_time,))

                services = cursor.fetchall()

                # Calculate percentiles for comparison
                all_response_times = [row[1] for row in services if row[1]]
                if all_response_times:
                    p50 = np.percentile(all_response_times, 50)
                    p90 = np.percentile(all_response_times, 90)
                    p95 = np.percentile(all_response_times, 95)
                else:
                    p50 = p90 = p95 = 0.0

                return {
                    'period_days': days,
                    'services': [
                        {
                            'service_name': row[0],
                            'average_response_time': row[1] or 0.0,
                            'average_error_rate': row[2] or 0.0,
                            'average_throughput': row[3] or 0.0,
                            'average_success_rate': row[4] or 0.0,
                            'average_availability': row[5] or 0.0,
                            'measurement_count': row[6] or 0,
                            'performance_tier': self._get_service_performance_tier(row[1] or 0.0, p50, p90, p95)
                        } for row in services
                    ],
                    'benchmarks': {
                        'p50_response_time': p50,
                        'p90_response_time': p90,
                        'p95_response_time': p95
                    }
                }

        except Exception as e:
            logger.error(f"Error getting service performance comparison: {e}")
            return {}

    def _get_service_performance_tier(self, response_time: float, p50: float, p90: float, p95: float) -> str:
        """Get performance tier for a service based on response time"""
        if response_time <= p50:
            return "excellent"
        elif response_time <= p90:
            return "good"
        elif response_time <= p95:
            return "fair"
        else:
            return "poor"

    def get_active_bottlenecks(self) -> List[BottleneckAlert]:
        """Get currently active bottlenecks"""
        return [bottleneck for bottleneck in self.bottlenecks.values()
                if bottleneck.resolved_at is None]

    def resolve_bottleneck(self, alert_id: str):
        """Mark a bottleneck as resolved"""
        if alert_id in self.bottlenecks:
            self.bottlenecks[alert_id].resolved_at = datetime.now()
            self._store_bottleneck(self.bottlenecks[alert_id])

    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance optimization recommendations"""
        recommendations = []

        # Check active bottlenecks
        active_bottlenecks = self.get_active_bottlenecks()
        for bottleneck in active_bottlenecks:
            recommendations.extend([
                {
                    'type': 'bottleneck_resolution',
                    'priority': 'high' if bottleneck.severity == PerformanceLevel.CRITICAL else 'medium',
                    'description': bottleneck.description,
                    'recommendations': bottleneck.recommendations,
                    'affected_components': bottleneck.affected_components
                }
            ])

        # Check performance trends
        trends = self.get_performance_trends(1)  # Last 24 hours
        if trends.get('hourly_trends'):
            recent_cpu = [t['cpu_usage'] for t in trends['hourly_trends'][-6:]]  # Last 6 hours
            if recent_cpu and avg(recent_cpu) > 80:
                recommendations.append({
                    'type': 'trend_analysis',
                    'priority': 'medium',
                    'description': 'CPU usage has been consistently high',
                    'recommendations': [
                        'Review CPU-intensive processes',
                        'Consider load balancing',
                        'Optimize resource allocation'
                    ],
                    'affected_components': ['system']
                })

        # Check service performance
        service_comparison = self.get_service_performance_comparison(1)
        for service in service_comparison.get('services', []):
            if service['average_response_time'] > 1000:  # More than 1 second
                recommendations.append({
                    'type': 'service_optimization',
                    'priority': 'medium',
                    'description': f"Service {service['service_name']} has high response time",
                    'recommendations': [
                        'Review service code for optimization',
                        'Check database queries',
                        'Consider caching strategies'
                    ],
                    'affected_components': [service['service_name']]
                })

        return recommendations

    def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old performance data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            with sqlite3.connect(self.db_path) as conn:
                tables = ['system_metrics', 'service_metrics']
                for table in tables:
                    conn.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_date,))

                # Keep only recent bottleneck alerts
                conn.execute('''
                    DELETE FROM bottleneck_alerts
                    WHERE detected_at < ? AND resolved_at IS NOT NULL
                ''', (cutoff_date,))

            logger.info(f"Cleaned up performance data older than {retention_days} days")

        except Exception as e:
            logger.error(f"Error cleaning up performance data: {e}")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
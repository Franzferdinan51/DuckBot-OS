#!/usr/bin/env python3
"""
Enhanced Health Monitoring Service for DuckBot Electron Launcher
Provides comprehensive monitoring, metrics collection, and intelligent alerting
"""

import asyncio
import json
import logging
import time
import psutil
import socket
import aiohttp
import async_timeout
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    """Service health status data"""
    name: str
    status: str  # 'healthy', 'unhealthy', 'degraded', 'unknown'
    last_check: datetime
    response_time: float
    error: Optional[str] = None
    uptime: float = 0.0
    restart_count: int = 0
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    process_count: int
    load_average: Optional[List[float]] = None

class HealthMonitor:
    """Comprehensive health monitoring service"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or "health_monitor.db"
        self.services: Dict[str, Dict[str, Any]] = {}
        self.health_history: List[ServiceHealth] = []
        self.metrics_history: List[SystemMetrics] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.event_subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.monitor_tasks: Set[asyncio.Task] = set()

        # Initialize database
        self._init_database()

        # Load default alert rules
        self._load_default_alert_rules()

        # Service configurations
        self.service_configs = {
            'lm_studio': {
                'port': 1234,
                'health_endpoint': '/v1/models',
                'check_type': 'http',
                'timeout': 5,
                'critical': True
            },
            'enhanced_webui': {
                'port': 8787,
                'health_endpoint': '/',
                'check_type': 'http',
                'timeout': 3,
                'critical': True
            },
            'mcp_server': {
                'port': 8790,
                'health_endpoint': '/health',
                'check_type': 'http',
                'timeout': 3,
                'critical': True
            },
            'monitoring_dashboard': {
                'port': 8789,
                'health_endpoint': '/',
                'check_type': 'http',
                'timeout': 3,
                'critical': False
            },
            'vibevoice': {
                'port': 8000,
                'health_endpoint': '/health',
                'check_type': 'http',
                'timeout': 5,
                'critical': False
            }
        }

    def _init_database(self):
        """Initialize SQLite database for health data storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Service health table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response_time REAL,
                        error_message TEXT,
                        uptime REAL,
                        restart_count INTEGER,
                        metrics TEXT,
                        timestamp DATETIME NOT NULL
                    )
                ''')

                # System metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        memory_used INTEGER,
                        memory_total INTEGER,
                        disk_usage TEXT,
                        network_io TEXT,
                        process_count INTEGER,
                        load_average TEXT
                    )
                ''')

                # Alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        service_name TEXT,
                        metrics TEXT,
                        timestamp DATETIME NOT NULL,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                ''')

                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_health_timestamp ON service_health(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')

                conn.commit()
                logger.info("Health monitoring database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _load_default_alert_rules(self):
        """Load default alerting rules"""
        self.alert_rules = {
            'high_cpu_usage': {
                'condition': lambda metrics: metrics['cpu_percent'] > 80,
                'severity': 'warning',
                'message': 'High CPU usage detected: {cpu_percent}%',
                'cooldown': 300  # 5 minutes
            },
            'high_memory_usage': {
                'condition': lambda metrics: metrics['memory_percent'] > 85,
                'severity': 'critical',
                'message': 'High memory usage detected: {memory_percent}%',
                'cooldown': 300
            },
            'service_down': {
                'condition': lambda health: health['status'] == 'unhealthy',
                'severity': 'critical',
                'message': 'Service {service_name} is down',
                'cooldown': 60
            },
            'slow_response': {
                'condition': lambda health: health['response_time'] > 5,
                'severity': 'warning',
                'message': 'Service {service_name} response time: {response_time}s',
                'cooldown': 300
            },
            'frequent_restarts': {
                'condition': lambda health: health['restart_count'] > 3,
                'severity': 'warning',
                'message': 'Service {service_name} has restarted {restart_count} times',
                'cooldown': 600
            }
        }

    async def start_monitoring(self):
        """Start the health monitoring service"""
        if self.running:
            return

        self.running = True
        logger.info("Starting health monitoring service")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_services()),
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._analyze_patterns()),
            asyncio.create_task(self._cleanup_old_data())
        ]

        self.monitor_tasks.update(tasks)

    async def stop_monitoring(self):
        """Stop the health monitoring service"""
        self.running = False
        logger.info("Stopping health monitoring service")

        # Cancel all monitoring tasks
        for task in self.monitor_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitor_tasks:
            await asyncio.gather(*self.monitor_tasks, return_exceptions=True)

        self.monitor_tasks.clear()

    async def _monitor_services(self):
        """Monitor all configured services"""
        while self.running:
            try:
                tasks = []
                for service_name, config in self.service_configs.items():
                    task = asyncio.create_task(self._check_service_health(service_name, config))
                    tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                await asyncio.sleep(10)

    async def _check_service_health(self, service_name: str, config: Dict[str, Any]) -> ServiceHealth:
        """Check health of a specific service"""
        start_time = time.time()

        try:
            if config['check_type'] == 'http':
                health = await self._check_http_health(service_name, config)
            elif config['check_type'] == 'tcp':
                health = await self._check_tcp_health(service_name, config)
            else:
                health = ServiceHealth(
                    name=service_name,
                    status='unknown',
                    last_check=datetime.now(),
                    response_time=0,
                    error='Unknown check type'
                )

        except Exception as e:
            health = ServiceHealth(
                name=service_name,
                status='unhealthy',
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error=str(e)
            )

        # Update service state
        if service_name not in self.services:
            self.services[service_name] = {
                'health_history': [],
                'restart_count': 0,
                'last_restart': None
            }

        # Check if service status changed
        prev_status = self.services[service_name].get('current_status')
        if prev_status != health.status:
            await self._emit_event('service_status_changed', {
                'service_name': service_name,
                'old_status': prev_status,
                'new_status': health.status,
                'timestamp': health.last_check
            })

            # Handle status changes
            if health.status == 'unhealthy' and prev_status == 'healthy':
                self.services[service_name]['restart_count'] += 1
                health.restart_count = self.services[service_name]['restart_count']

        self.services[service_name]['current_status'] = health.status
        self.services[service_name]['health_history'].append(health)

        # Store in database
        await self._store_service_health(health)

        # Check alert rules
        await self._check_alert_rules(health)

        return health

    async def _check_http_health(self, service_name: str, config: Dict[str, Any]) -> ServiceHealth:
        """Check service health via HTTP endpoint"""
        url = f"http://localhost:{config['port']}{config['health_endpoint']}"
        start_time = time.time()

        try:
            async with async_timeout.timeout(config['timeout']):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response_time = time.time() - start_time

                        if response.status < 400:
                            # Try to parse JSON response for additional metrics
                            try:
                                data = await response.json()
                                metrics = data.get('metrics', {})
                                status = data.get('status', 'healthy')
                            except:
                                metrics = {}
                                status = 'healthy'

                            return ServiceHealth(
                                name=service_name,
                                status=status,
                                last_check=datetime.now(),
                                response_time=response_time,
                                metrics=metrics
                            )
                        else:
                            return ServiceHealth(
                                name=service_name,
                                status='unhealthy',
                                last_check=datetime.now(),
                                response_time=response_time,
                                error=f'HTTP {response.status}'
                            )

        except asyncio.TimeoutError:
            return ServiceHealth(
                name=service_name,
                status='unhealthy',
                last_check=datetime.now(),
                response_time=config['timeout'],
                error='Timeout'
            )
        except Exception as e:
            return ServiceHealth(
                name=service_name,
                status='unhealthy',
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error=str(e)
            )

    async def _check_tcp_health(self, service_name: str, config: Dict[str, Any]) -> ServiceHealth:
        """Check service health via TCP connection"""
        start_time = time.time()

        try:
            async with async_timeout.timeout(config['timeout']):
                reader, writer = await asyncio.open_connection('localhost', config['port'])
                writer.close()
                await writer.wait_closed()

                response_time = time.time() - start_time
                return ServiceHealth(
                    name=service_name,
                    status='healthy',
                    last_check=datetime.now(),
                    response_time=response_time
                )

        except Exception as e:
            return ServiceHealth(
                name=service_name,
                status='unhealthy',
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error=str(e)
            )

    async def _monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.running:
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)

                # Store in database
                await self._store_system_metrics(metrics)

                # Keep only last 1000 metrics in memory
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                # Check system alert rules
                await self._check_system_alert_rules(metrics)

                await asyncio.sleep(10)  # Collect every 10 seconds

            except Exception as e:
                logger.error(f"Error in system metrics monitoring: {e}")
                await asyncio.sleep(5)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk_usage = {}
            for disk in ['/', 'C:']:
                try:
                    usage = psutil.disk_usage(disk)
                    disk_usage[disk] = usage.percent
                except:
                    pass

            # Network I/O
            net_io = psutil.net_io_counters()
            network_io = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }

            # Process count
            process_count = len(psutil.pids())

            # Load average (Unix-like systems)
            load_avg = None
            try:
                load_avg = list(psutil.getloadavg())
            except:
                pass

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=load_avg
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                memory_used=0,
                memory_total=0,
                disk_usage={},
                network_io={},
                process_count=0
            )

    async def _analyze_patterns(self):
        """Analyze patterns in health data for early warning"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Analyze every minute

                # Analyze service health patterns
                await self._analyze_service_patterns()

                # Analyze system metric patterns
                await self._analyze_system_patterns()

            except Exception as e:
                logger.error(f"Error in pattern analysis: {e}")

    async def _analyze_service_patterns(self):
        """Analyze service health patterns"""
        for service_name, service_data in self.services.items():
            history = service_data.get('health_history', [])
            if len(history) < 5:
                continue

            # Check for frequent failures
            recent_failures = [h for h in history[-10:] if h.status == 'unhealthy']
            if len(recent_failures) >= 5:
                await self._emit_event('pattern_detected', {
                    'type': 'frequent_failures',
                    'service_name': service_name,
                    'failure_count': len(recent_failures),
                    'time_window': '10 checks'
                })

            # Check for degradation trends
            response_times = [h.response_time for h in history[-10:]]
            if len(response_times) >= 5:
                # Simple trend detection
                recent_avg = sum(response_times[-5:]) / 5
                older_avg = sum(response_times[-10:-5]) / 5
                if recent_avg > older_avg * 1.5:  # 50% increase
                    await self._emit_event('pattern_detected', {
                        'type': 'performance_degradation',
                        'service_name': service_name,
                        'current_avg': recent_avg,
                        'previous_avg': older_avg
                    })

    async def _analyze_system_patterns(self):
        """Analyze system metric patterns"""
        if len(self.metrics_history) < 10:
            return

        recent_metrics = self.metrics_history[-60:]  # Last 10 minutes

        # Check for memory leaks
        memory_usage = [m.memory_percent for m in recent_metrics]
        if len(memory_usage) >= 10:
            trend = sum(memory_usage[-5:]) / 5 - sum(memory_usage[-10:-5]) / 5
            if trend > 5:  # 5% increase over 5 minutes
                await self._emit_event('pattern_detected', {
                    'type': 'memory_leak_detected',
                    'trend': trend
                })

    async def _check_alert_rules(self, health: ServiceHealth):
        """Check alert rules for service health"""
        health_dict = asdict(health)

        for rule_name, rule in self.alert_rules.items():
            try:
                if 'service' in rule_name or rule['condition'](health_dict):
                    # Check cooldown
                    last_alert = await self._get_last_alert_time(rule_name, health.name)
                    if last_alert and (datetime.now() - last_alert).seconds < rule['cooldown']:
                        continue

                    # Create alert
                    message = rule['message'].format(**health_dict)
                    await self._create_alert(
                        rule_name=rule_name,
                        severity=rule['severity'],
                        message=message,
                        service_name=health.name,
                        metrics=health_dict
                    )

            except Exception as e:
                logger.error(f"Error checking alert rule {rule_name}: {e}")

    async def _check_system_alert_rules(self, metrics: SystemMetrics):
        """Check alert rules for system metrics"""
        metrics_dict = asdict(metrics)

        for rule_name, rule in self.alert_rules.items():
            try:
                if rule['condition'](metrics_dict):
                    # Check cooldown
                    last_alert = await self._get_last_alert_time(rule_name)
                    if last_alert and (datetime.now() - last_alert).seconds < rule['cooldown']:
                        continue

                    # Create alert
                    message = rule['message'].format(**metrics_dict)
                    await self._create_alert(
                        rule_name=rule_name,
                        severity=rule['severity'],
                        message=message,
                        metrics=metrics_dict
                    )

            except Exception as e:
                logger.error(f"Error checking system alert rule {rule_name}: {e}")

    async def _create_alert(self, rule_name: str, severity: str, message: str,
                           service_name: str = None, metrics: Dict[str, Any] = None):
        """Create and store an alert"""
        try:
            alert_data = {
                'rule_name': rule_name,
                'severity': severity,
                'message': message,
                'service_name': service_name,
                'metrics': json.dumps(metrics) if metrics else None,
                'timestamp': datetime.now().isoformat()
            }

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts (rule_name, severity, message, service_name, metrics, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (rule_name, severity, message, service_name,
                      json.dumps(metrics) if metrics else None, datetime.now()))
                conn.commit()

            # Emit alert event
            await self._emit_event('alert_created', alert_data)

            logger.warning(f"Alert created: {severity} - {message}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _get_last_alert_time(self, rule_name: str, service_name: str = None) -> Optional[datetime]:
        """Get the last alert time for a rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if service_name:
                    cursor.execute('''
                        SELECT timestamp FROM alerts
                        WHERE rule_name = ? AND service_name = ?
                        ORDER BY timestamp DESC LIMIT 1
                    ''', (rule_name, service_name))
                else:
                    cursor.execute('''
                        SELECT timestamp FROM alerts
                        WHERE rule_name = ?
                        ORDER BY timestamp DESC LIMIT 1
                    ''', (rule_name,))

                result = cursor.fetchone()
                return datetime.fromisoformat(result[0]) if result else None

        except Exception as e:
            logger.error(f"Error getting last alert time: {e}")
            return None

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to subscribers"""
        if event_type in self.event_subscribers:
            for callback in self.event_subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")

    def subscribe_to_events(self, event_type: str, callback: Callable):
        """Subscribe to events"""
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        self.event_subscribers[event_type].append(callback)

    def unsubscribe_from_events(self, event_type: str, callback: Callable):
        """Unsubscribe from events"""
        if event_type in self.event_subscribers:
            try:
                self.event_subscribers[event_type].remove(callback)
            except ValueError:
                pass

    async def _store_service_health(self, health: ServiceHealth):
        """Store service health in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO service_health
                    (service_name, status, response_time, error_message, uptime, restart_count, metrics, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    health.name,
                    health.status,
                    health.response_time,
                    health.error,
                    health.uptime,
                    health.restart_count,
                    json.dumps(health.metrics),
                    health.last_check
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing service health: {e}")

    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_metrics
                    (timestamp, cpu_percent, memory_percent, memory_used, memory_total, disk_usage, network_io, process_count, load_average)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp,
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.memory_used,
                    metrics.memory_total,
                    json.dumps(metrics.disk_usage),
                    json.dumps(metrics.network_io),
                    metrics.process_count,
                    json.dumps(metrics.load_average) if metrics.load_average else None
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")

    async def _cleanup_old_data(self):
        """Clean up old data from database"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Clean up every hour

                cutoff_date = datetime.now() - timedelta(days=7)

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Clean old service health data
                    cursor.execute('''
                        DELETE FROM service_health WHERE timestamp < ?
                    ''', (cutoff_date,))

                    # Clean old system metrics
                    cursor.execute('''
                        DELETE FROM system_metrics WHERE timestamp < ?
                    ''', (cutoff_date,))

                    # Clean resolved alerts older than 30 days
                    alert_cutoff = datetime.now() - timedelta(days=30)
                    cursor.execute('''
                        DELETE FROM alerts WHERE timestamp < ? AND resolved = TRUE
                    ''', (alert_cutoff,))

                    conn.commit()
                    logger.info("Cleaned up old monitoring data")

            except Exception as e:
                logger.error(f"Error in data cleanup: {e}")

    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        status = {
            'monitoring_active': self.running,
            'services': {},
            'system_metrics': self.metrics_history[-1] if self.metrics_history else None,
            'total_services': len(self.service_configs),
            'healthy_services': 0,
            'unhealthy_services': 0
        }

        for service_name, service_data in self.services.items():
            current_health = service_data.get('health_history', [])[-1] if service_data.get('health_history') else None
            if current_health:
                status['services'][service_name] = {
                    'status': current_health.status,
                    'response_time': current_health.response_time,
                    'last_check': current_health.last_check.isoformat(),
                    'restart_count': current_health.restart_count
                }

                if current_health.status == 'healthy':
                    status['healthy_services'] += 1
                else:
                    status['unhealthy_services'] += 1

        return status

    def get_service_history(self, service_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get service health history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM service_health
                WHERE service_name = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (service_name, cutoff_time))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'service_name': row[1],
                    'status': row[2],
                    'response_time': row[3],
                    'error_message': row[4],
                    'uptime': row[5],
                    'restart_count': row[6],
                    'metrics': json.loads(row[7]) if row[7] else {},
                    'timestamp': row[8]
                })

            return results

    def get_system_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM system_metrics
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'cpu_percent': row[2],
                    'memory_percent': row[3],
                    'memory_used': row[4],
                    'memory_total': row[5],
                    'disk_usage': json.loads(row[6]) if row[6] else {},
                    'network_io': json.loads(row[7]) if row[7] else {},
                    'process_count': row[8],
                    'load_average': json.loads(row[9]) if row[9] else None
                })

            return results

    def get_alerts(self, limit: int = 100, unresolved_only: bool = False) -> List[Dict[str, Any]]:
        """Get alerts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if unresolved_only:
                cursor.execute('''
                    SELECT * FROM alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT * FROM alerts
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'rule_name': row[1],
                    'severity': row[2],
                    'message': row[3],
                    'service_name': row[4],
                    'metrics': json.loads(row[5]) if row[5] else {},
                    'timestamp': row[6],
                    'acknowledged': bool(row[7]),
                    'resolved': bool(row[8])
                })

            return results

# Global health monitor instance
health_monitor = None

def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    global health_monitor
    if health_monitor is None:
        health_monitor = HealthMonitor()
    return health_monitor

async def start_health_monitoring():
    """Start global health monitoring"""
    monitor = get_health_monitor()
    await monitor.start_monitoring()
    return monitor

async def stop_health_monitoring():
    """Stop global health monitoring"""
    monitor = get_health_monitor()
    await monitor.stop_monitoring()
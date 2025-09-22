#!/usr/bin/env python3
"""
Performance Monitoring System for DuckBot Training
Monitors system resources, training throughput, and performance metrics in real-time.
"""

import os
import sys
import json
import time
import threading
import logging
import platform
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from pathlib import Path
import sqlite3
import numpy as np
from contextlib import contextmanager
import queue
import psutil
import GPUtil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ResourceType(Enum):
    """Types of system resources"""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"

class PerformanceMetric(Enum):
    """Types of performance metrics"""
    UTILIZATION = "utilization"
    TEMPERATURE = "temperature"
    MEMORY_USED = "memory_used"
    MEMORY_AVAILABLE = "memory_available"
    POWER_USAGE = "power_usage"
    FAN_SPEED = "fan_speed"
    CLOCK_SPEED = "clock_speed"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    IOPS = "iops"
    BANDWIDTH = "bandwidth"

@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring"""
    sampling_interval: float = 1.0  # seconds
    database_path: str = "performance_metrics.db"
    enable_gpu_monitoring: bool = True
    enable_network_monitoring: bool = True
    enable_disk_monitoring: bool = True
    max_memory_samples: int = 10000
    log_performance_stats: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'cpu_utilization': 95.0,
        'gpu_utilization': 95.0,
        'memory_utilization': 90.0,
        'gpu_temperature': 85.0,
        'disk_utilization': 95.0
    })
    performance_tracking: bool = True
    detailed_metrics: bool = True

@dataclass
class ResourceMetric:
    """Individual resource metric measurement"""
    timestamp: datetime
    resource_type: ResourceType
    metric_type: PerformanceMetric
    device_id: str
    value: float
    unit: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrainingThroughput:
    """Training performance metrics"""
    timestamp: datetime
    samples_per_second: float
    batches_per_second: float
    epochs_per_second: float
    step_time_ms: float
    data_loading_time_ms: float
    forward_time_ms: float
    backward_time_ms: float
    optimization_time_ms: float
    batch_size: int
    sequence_length: Optional[int] = None
    model_parameters: Optional[int] = None

@dataclass
class PerformanceAlert:
    """Performance alert information"""
    timestamp: datetime
    alert_type: str
    severity: str  # 'info', 'warning', 'critical'
    message: str
    resource_type: Optional[ResourceType] = None
    metric_type: Optional[PerformanceMetric] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    device_id: Optional[str] = None

class ResourceMonitor:
    """Base class for resource monitoring"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.is_running = False
        self.metrics_queue = queue.Queue()
        self.alerts_queue = queue.Queue()
        self.callbacks = []

    def start(self):
        """Start monitoring"""
        self.is_running = True
        self._start_monitoring_thread()

    def stop(self):
        """Stop monitoring"""
        self.is_running = False

    def add_callback(self, callback: Callable[[ResourceMetric], None]):
        """Add callback for metric updates"""
        self.callbacks.append(callback)

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback for alerts"""
        self.alerts_queue = callback

    def _start_monitoring_thread(self):
        """Start monitoring thread"""
        def monitor_loop():
            while self.is_running:
                try:
                    metrics = self._collect_metrics()
                    for metric in metrics:
                        self.metrics_queue.put(metric)
                        for callback in self.callbacks:
                            callback(metric)
                    time.sleep(self.config.sampling_interval)
                except Exception as e:
                    logging.error(f"Error in {self.__class__.__name__}: {e}")
                    time.sleep(1.0)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def _collect_metrics(self) -> List[ResourceMetric]:
        """Collect metrics - to be implemented by subclasses"""
        return []

class CPUMonitor(ResourceMonitor):
    """CPU resource monitoring"""

    def __init__(self, config: PerformanceConfig):
        super().__init__(config)
        self.device_id = "cpu"
        self.cpu_count = psutil.cpu_count(logical=True)
        self.cpu_count_physical = psutil.cpu_count(logical=False)

    def _collect_metrics(self) -> List[ResourceMetric]:
        """Collect CPU metrics"""
        metrics = []
        timestamp = datetime.now()

        try:
            # CPU utilization
            cpu_percent = psutil.cpu_percent(interval=None)
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.CPU,
                metric_type=PerformanceMetric.UTILIZATION,
                device_id=self.device_id,
                value=cpu_percent,
                unit="%",
                metadata={'core_count': self.cpu_count, 'physical_cores': self.cpu_count_physical}
            ))

            # Per-core utilization
            if self.config.detailed_metrics:
                cpu_percent_per_core = psutil.cpu_percent(interval=None, percpu=True)
                for i, core_util in enumerate(cpu_percent_per_core):
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.CPU,
                        metric_type=PerformanceMetric.UTILIZATION,
                        device_id=f"cpu_core_{i}",
                        value=core_util,
                        unit="%",
                        metadata={'core_index': i}
                    ))

            # CPU frequency
            if hasattr(psutil, 'cpu_freq'):
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.CPU,
                        metric_type=PerformanceMetric.CLOCK_SPEED,
                        device_id=self.device_id,
                        value=cpu_freq.current,
                        unit="MHz",
                        metadata={'min_freq': cpu_freq.min, 'max_freq': cpu_freq.max}
                    ))

            # CPU temperature (Linux only)
            if platform.system() == 'Linux':
                try:
                    temps = psutil.sensors_temperatures()
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current:
                                metrics.append(ResourceMetric(
                                    timestamp=timestamp,
                                    resource_type=ResourceType.CPU,
                                    metric_type=PerformanceMetric.TEMPERATURE,
                                    device_id=f"cpu_{name}_{entry.label or 'default'}",
                                    value=entry.current,
                                    unit="°C",
                                    metadata={'sensor_name': name, 'label': entry.label}
                                ))
                except Exception:
                    pass

            # Check for alerts
            if cpu_percent > self.config.alert_thresholds.get('cpu_utilization', 95.0):
                alert = PerformanceAlert(
                    timestamp=timestamp,
                    alert_type="high_cpu_utilization",
                    severity="warning",
                    message=f"High CPU utilization: {cpu_percent:.1f}%",
                    resource_type=ResourceType.CPU,
                    metric_type=PerformanceMetric.UTILIZATION,
                    current_value=cpu_percent,
                    threshold=self.config.alert_thresholds.get('cpu_utilization', 95.0),
                    device_id=self.device_id
                )
                self.alerts_queue.put(alert)

        except Exception as e:
            logging.error(f"Error collecting CPU metrics: {e}")

        return metrics

class GPUMonitor(ResourceMonitor):
    """GPU resource monitoring"""

    def __init__(self, config: PerformanceConfig):
        super().__init__(config)
        self.gpus = []
        self._init_gpus()

    def _init_gpus(self):
        """Initialize GPU monitoring"""
        if not self.config.enable_gpu_monitoring:
            return

        try:
            self.gpus = GPUtil.getGPUs()
        except Exception as e:
            logging.warning(f"GPU monitoring not available: {e}")

    def _collect_metrics(self) -> List[ResourceMetric]:
        """Collect GPU metrics"""
        metrics = []
        timestamp = datetime.now()

        if not self.gpus:
            return metrics

        try:
            for i, gpu in enumerate(self.gpus):
                device_id = f"gpu_{i}"

                # GPU utilization
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.GPU,
                    metric_type=PerformanceMetric.UTILIZATION,
                    device_id=device_id,
                    value=gpu.load * 100,
                    unit="%",
                    metadata={'gpu_name': gpu.name, 'gpu_id': i}
                ))

                # GPU memory
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.GPU,
                    metric_type=PerformanceMetric.MEMORY_USED,
                    device_id=device_id,
                    value=gpu.memoryUsed,
                    unit="MB",
                    metadata={'total_memory': gpu.memoryTotal, 'memory_free': gpu.memoryFree}
                ))

                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.GPU,
                    metric_type=PerformanceMetric.MEMORY_AVAILABLE,
                    device_id=device_id,
                    value=gpu.memoryFree,
                    unit="MB",
                    metadata={'total_memory': gpu.memoryTotal, 'memory_used': gpu.memoryUsed}
                ))

                # GPU temperature
                if gpu.temperature:
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.GPU,
                        metric_type=PerformanceMetric.TEMPERATURE,
                        device_id=device_id,
                        value=gpu.temperature,
                        unit="°C",
                        metadata={'gpu_name': gpu.name}
                    ))

                # GPU power usage
                if hasattr(gpu, 'powerLimit') and gpu.powerLimit:
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.GPU,
                        metric_type=PerformanceMetric.POWER_USAGE,
                        device_id=device_id,
                        value=gpu.powerLimit,
                        unit="W",
                        metadata={'gpu_name': gpu.name}
                    ))

                # GPU fan speed
                if hasattr(gpu, 'fanSpeed') and gpu.fanSpeed:
                    metrics.append(ResourceMetric(
                        timestamp=timestamp,
                        resource_type=ResourceType.GPU,
                        metric_type=PerformanceMetric.FAN_SPEED,
                        device_id=device_id,
                        value=gpu.fanSpeed,
                        unit="%",
                        metadata={'gpu_name': gpu.name}
                    ))

                # Check for alerts
                if gpu.load * 100 > self.config.alert_thresholds.get('gpu_utilization', 95.0):
                    alert = PerformanceAlert(
                        timestamp=timestamp,
                        alert_type="high_gpu_utilization",
                        severity="warning",
                        message=f"High GPU utilization: {gpu.load * 100:.1f}%",
                        resource_type=ResourceType.GPU,
                        metric_type=PerformanceMetric.UTILIZATION,
                        current_value=gpu.load * 100,
                        threshold=self.config.alert_thresholds.get('gpu_utilization', 95.0),
                        device_id=device_id
                    )
                    self.alerts_queue.put(alert)

                if gpu.temperature and gpu.temperature > self.config.alert_thresholds.get('gpu_temperature', 85.0):
                    alert = PerformanceAlert(
                        timestamp=timestamp,
                        alert_type="high_gpu_temperature",
                        severity="critical",
                        message=f"High GPU temperature: {gpu.temperature:.1f}°C",
                        resource_type=ResourceType.GPU,
                        metric_type=PerformanceMetric.TEMPERATURE,
                        current_value=gpu.temperature,
                        threshold=self.config.alert_thresholds.get('gpu_temperature', 85.0),
                        device_id=device_id
                    )
                    self.alerts_queue.put(alert)

        except Exception as e:
            logging.error(f"Error collecting GPU metrics: {e}")

        return metrics

class MemoryMonitor(ResourceMonitor):
    """Memory resource monitoring"""

    def __init__(self, config: PerformanceConfig):
        super().__init__(config)
        self.device_id = "memory"

    def _collect_metrics(self) -> List[ResourceMetric]:
        """Collect memory metrics"""
        metrics = []
        timestamp = datetime.now()

        try:
            # Virtual memory
            virtual_memory = psutil.virtual_memory()

            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_type=PerformanceMetric.MEMORY_USED,
                device_id=self.device_id,
                value=virtual_memory.used,
                unit="bytes",
                metadata={
                    'total': virtual_memory.total,
                    'available': virtual_memory.available,
                    'percent': virtual_memory.percent
                }
            ))

            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_type=PerformanceMetric.MEMORY_AVAILABLE,
                device_id=self.device_id,
                value=virtual_memory.available,
                unit="bytes",
                metadata={
                    'total': virtual_memory.total,
                    'used': virtual_memory.used,
                    'percent': virtual_memory.percent
                }
            ))

            # Memory utilization percentage
            metrics.append(ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.MEMORY,
                metric_type=PerformanceMetric.UTILIZATION,
                device_id=self.device_id,
                value=virtual_memory.percent,
                unit="%",
                metadata={
                    'total': virtual_memory.total,
                    'used': virtual_memory.used,
                    'available': virtual_memory.available
                }
            ))

            # Swap memory
            swap_memory = psutil.swap_memory()
            if swap_memory.total > 0:
                metrics.append(ResourceMetric(
                    timestamp=timestamp,
                    resource_type=ResourceType.MEMORY,
                    metric_type=PerformanceMetric.UTILIZATION,
                    device_id="swap_memory",
                    value=swap_memory.percent,
                    unit="%",
                    metadata={
                        'total': swap_memory.total,
                        'used': swap_memory.used,
                        'free': swap_memory.free
                    }
                ))

            # Check for memory alerts
            if virtual_memory.percent > self.config.alert_thresholds.get('memory_utilization', 90.0):
                alert = PerformanceAlert(
                    timestamp=timestamp,
                    alert_type="high_memory_utilization",
                    severity="warning",
                    message=f"High memory utilization: {virtual_memory.percent:.1f}%",
                    resource_type=ResourceType.MEMORY,
                    metric_type=PerformanceMetric.UTILIZATION,
                    current_value=virtual_memory.percent,
                    threshold=self.config.alert_thresholds.get('memory_utilization', 90.0),
                    device_id=self.device_id
                )
                self.alerts_queue.put(alert)

        except Exception as e:
            logging.error(f"Error collecting memory metrics: {e}")

        return metrics

class PerformanceDatabase:
    """Database for storing performance metrics"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Resource metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resource_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    resource_type TEXT,
                    metric_type TEXT,
                    device_id TEXT,
                    value REAL,
                    unit TEXT,
                    metadata TEXT
                )
            """)

            # Training throughput table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_throughput (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    samples_per_second REAL,
                    batches_per_second REAL,
                    epochs_per_second REAL,
                    step_time_ms REAL,
                    data_loading_time_ms REAL,
                    forward_time_ms REAL,
                    backward_time_ms REAL,
                    optimization_time_ms REAL,
                    batch_size INTEGER,
                    sequence_length INTEGER,
                    model_parameters INTEGER
                )
            """)

            # Performance alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    resource_type TEXT,
                    metric_type TEXT,
                    current_value REAL,
                    threshold REAL,
                    device_id TEXT
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resource_metrics_timestamp ON resource_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resource_metrics_device ON resource_metrics(device_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_throughput_timestamp ON training_throughput(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp)")

    def store_resource_metric(self, metric: ResourceMetric):
        """Store resource metric in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO resource_metrics (
                    timestamp, resource_type, metric_type, device_id, value, unit, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp.isoformat(),
                metric.resource_type.value,
                metric.metric_type.value,
                metric.device_id,
                metric.value,
                metric.unit,
                json.dumps(metric.metadata)
            ))

    def store_throughput(self, throughput: TrainingThroughput):
        """Store training throughput in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO training_throughput (
                    timestamp, samples_per_second, batches_per_second, epochs_per_second,
                    step_time_ms, data_loading_time_ms, forward_time_ms, backward_time_ms,
                    optimization_time_ms, batch_size, sequence_length, model_parameters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                throughput.timestamp.isoformat(),
                throughput.samples_per_second,
                throughput.batches_per_second,
                throughput.epochs_per_second,
                throughput.step_time_ms,
                throughput.data_loading_time_ms,
                throughput.forward_time_ms,
                throughput.backward_time_ms,
                throughput.optimization_time_ms,
                throughput.batch_size,
                throughput.sequence_length,
                throughput.model_parameters
            ))

    def store_alert(self, alert: PerformanceAlert):
        """Store performance alert in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_alerts (
                    timestamp, alert_type, severity, message, resource_type,
                    metric_type, current_value, threshold, device_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.timestamp.isoformat(),
                alert.alert_type,
                alert.severity,
                alert.message,
                alert.resource_type.value if alert.resource_type else None,
                alert.metric_type.value if alert.metric_type else None,
                alert.current_value,
                alert.threshold,
                alert.device_id
            ))

    def get_resource_metrics(self, device_id: str, metric_type: PerformanceMetric,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> List[Dict]:
        """Get resource metrics from database"""
        query = """
            SELECT timestamp, value, unit, metadata
            FROM resource_metrics
            WHERE device_id = ? AND metric_type = ?
        """
        params = [device_id, metric_type.value]

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [
                {
                    'timestamp': datetime.fromisoformat(row[0]),
                    'value': row[1],
                    'unit': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                }
                for row in cursor.fetchall()
            ]

    def get_throughput_stats(self, start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> List[Dict]:
        """Get training throughput statistics"""
        query = "SELECT * FROM training_throughput"
        params = []

        conditions = []
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

class TrainingThroughputTracker:
    """Tracks training performance metrics"""

    def __init__(self, config: PerformanceConfig, database: PerformanceDatabase):
        self.config = config
        self.database = database
        self.timers = {}
        self.counters = {}
        self.current_batch_size = 32
        self.current_step = 0

    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        start_time = time.time()
        yield
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        if operation_name not in self.timers:
            self.timers[operation_name] = []
        self.timers[operation_name].append(duration_ms)

    def update_batch_size(self, batch_size: int):
        """Update current batch size"""
        self.current_batch_size = batch_size

    def increment_step(self):
        """Increment step counter"""
        self.current_step += 1

    def record_throughput(self, samples_processed: int, step_time_ms: float):
        """Record training throughput metrics"""
        current_time = datetime.now()

        throughput = TrainingThroughput(
            timestamp=current_time,
            samples_per_second=(samples_processed / step_time_ms) * 1000 if step_time_ms > 0 else 0,
            batches_per_second=1000 / step_time_ms if step_time_ms > 0 else 0,
            epochs_per_second=0,  # To be calculated based on epoch duration
            step_time_ms=step_time_ms,
            data_loading_time_ms=np.mean(self.timers.get('data_loading', [0])),
            forward_time_ms=np.mean(self.timers.get('forward_pass', [0])),
            backward_time_ms=np.mean(self.timers.get('backward_pass', [0])),
            optimization_time_ms=np.mean(self.timers.get('optimization', [0])),
            batch_size=self.current_batch_size,
            sequence_length=None,  # To be set based on model
            model_parameters=None  # To be set based on model
        )

        self.database.store_throughput(throughput)

        # Clear timers for next measurement
        self.timers.clear()

    def get_current_throughput(self) -> Dict[str, float]:
        """Get current throughput statistics"""
        return {
            'avg_step_time_ms': np.mean(self.timers.get('step_time', [0])),
            'avg_data_loading_ms': np.mean(self.timers.get('data_loading', [0])),
            'avg_forward_pass_ms': np.mean(self.timers.get('forward_pass', [0])),
            'avg_backward_pass_ms': np.mean(self.timers.get('backward_pass', [0])),
            'avg_optimization_ms': np.mean(self.timers.get('optimization', [0])),
            'current_batch_size': self.current_batch_size,
            'current_step': self.current_step
        }

class PerformanceMonitor:
    """Main performance monitoring system"""

    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.is_running = False

        # Initialize database
        self.database = PerformanceDatabase(self.config.database_path)

        # Initialize monitors
        self.cpu_monitor = CPUMonitor(self.config)
        self.gpu_monitor = GPUMonitor(self.config)
        self.memory_monitor = MemoryMonitor(self.config)

        # Initialize throughput tracker
        self.throughput_tracker = TrainingThroughputTracker(self.config, self.database)

        # Set up alert handling
        self.alert_callbacks = []
        self._setup_alert_handling()

        # Initialize stats
        self.stats = {
            'metrics_collected': 0,
            'alerts_generated': 0,
            'start_time': None,
            'last_metric_time': None
        }

    def _setup_alert_handling(self):
        """Set up alert handling for all monitors"""
        def alert_handler(alert: PerformanceAlert):
            self.database.store_alert(alert)
            self.stats['alerts_generated'] += 1

            # Call registered callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logging.error(f"Error in alert callback: {e}")

        self.cpu_monitor.add_alert_callback(alert_handler)
        self.gpu_monitor.add_alert_callback(alert_handler)
        self.memory_monitor.add_alert_callback(alert_handler)

    def start(self):
        """Start performance monitoring"""
        if self.is_running:
            return

        self.is_running = True
        self.stats['start_time'] = datetime.now()

        # Set up metric collection
        def metric_handler(metric: ResourceMetric):
            self.database.store_resource_metric(metric)
            self.stats['metrics_collected'] += 1
            self.stats['last_metric_time'] = metric.timestamp

        self.cpu_monitor.add_callback(metric_handler)
        self.gpu_monitor.add_callback(metric_handler)
        self.memory_monitor.add_callback(metric_handler)

        # Start all monitors
        self.cpu_monitor.start()
        self.gpu_monitor.start()
        self.memory_monitor.start()

        logging.info("Performance monitoring started")

    def stop(self):
        """Stop performance monitoring"""
        if not self.is_running:
            return

        self.is_running = False

        # Stop all monitors
        self.cpu_monitor.stop()
        self.gpu_monitor.stop()
        self.memory_monitor.stop()

        logging.info("Performance monitoring stopped")

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(logical=True),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'gpu_count': len(self.gpu_monitor.gpus) if hasattr(self.gpu_monitor, 'gpus') else 0,
            'python_version': sys.version,
            'psutil_version': psutil.__version__
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {
            'monitoring_active': self.is_running,
            'stats': self.stats.copy(),
            'system_info': self.get_system_info(),
            'current_throughput': self.throughput_tracker.get_current_throughput(),
            'alert_thresholds': self.config.alert_thresholds
        }

        if self.stats['start_time']:
            summary['monitoring_duration'] = (datetime.now() - self.stats['start_time']).total_seconds()

        return summary

    def get_resource_utilization(self) -> Dict[str, float]:
        """Get current resource utilization"""
        utilization = {}

        # Get latest metrics for each device
        devices = ['cpu', 'memory']
        if hasattr(self.gpu_monitor, 'gpus') and self.gpu_monitor.gpus:
            devices.extend([f'gpu_{i}' for i in range(len(self.gpu_monitor.gpus))])

        for device in devices:
            metrics = self.database.get_resource_metrics(
                device, PerformanceMetric.UTILIZATION,
                start_time=datetime.now() - timedelta(seconds=10)
            )
            if metrics:
                utilization[device] = metrics[-1]['value']

        return utilization

# Example usage and demo
def demo_performance_monitoring():
    """Demonstrate performance monitoring functionality"""
    print("🔧 Performance Monitoring Demo")
    print("=" * 40)

    # Create performance monitor
    monitor = PerformanceMonitor()

    # Add alert callback
    def handle_alert(alert: PerformanceAlert):
        print(f"🚨 ALERT [{alert.severity.upper()}]: {alert.message}")

    monitor.add_alert_callback(handle_alert)

    # Start monitoring
    print("\n🚀 Starting performance monitoring...")
    monitor.start()

    try:
        # Monitor for 30 seconds
        print("📊 Monitoring system resources for 30 seconds...")
        start_time = time.time()

        while time.time() - start_time < 30:
            # Simulate some training activity
            with monitor.throughput_tracker.time_operation('data_loading'):
                time.sleep(0.01)  # Simulate data loading

            with monitor.throughput_tracker.time_operation('forward_pass'):
                time.sleep(0.05)  # Simulate forward pass

            with monitor.throughput_tracker.time_operation('backward_pass'):
                time.sleep(0.03)  # Simulate backward pass

            with monitor.throughput_tracker.time_operation('optimization'):
                time.sleep(0.01)  # Simulate optimization

            # Record throughput
            monitor.throughput_tracker.increment_step()
            monitor.throughput_tracker.record_throughput(
                samples_processed=monitor.throughput_tracker.current_batch_size,
                step_time_ms=100  # Simulated step time
            )

            # Print summary every 5 seconds
            if int(time.time() - start_time) % 5 == 0:
                summary = monitor.get_performance_summary()
                print(f"\n📈 Performance Summary (t+{int(time.time() - start_time)}s):")
                print(f"  Metrics collected: {summary['stats']['metrics_collected']}")
                print(f"  Alerts generated: {summary['stats']['alerts_generated']}")
                print(f"  Monitoring duration: {summary.get('monitoring_duration', 0):.1f}s")

                # Show current utilization
                utilization = monitor.get_resource_utilization()
                print(f"  Current utilization:")
                for device, util in utilization.items():
                    print(f"    {device}: {util:.1f}%")

                # Show throughput
                throughput = summary['current_throughput']
                print(f"  Current throughput:")
                print(f"    Batch size: {throughput['current_batch_size']}")
                print(f"    Steps completed: {throughput['current_step']}")
                print(f"    Avg step time: {throughput['avg_step_time_ms']:.2f}ms")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")

    finally:
        # Stop monitoring
        monitor.stop()

        # Show final summary
        print("\n📊 Final Performance Summary:")
        summary = monitor.get_performance_summary()
        print(f"  Total monitoring time: {summary.get('monitoring_duration', 0):.1f}s")
        print(f"  Total metrics collected: {summary['stats']['metrics_collected']}")
        print(f"  Total alerts generated: {summary['stats']['alerts_generated']}")
        print(f"  System info:")
        print(f"    Platform: {summary['system_info']['platform']}")
        print(f"    CPU cores: {summary['system_info']['cpu_count']}")
        print(f"    Memory: {summary['system_info']['memory_total'] / (1024**3):.1f}GB")
        print(f"    GPUs: {summary['system_info']['gpu_count']}")

        return monitor

if __name__ == "__main__":
    demo_performance_monitoring()
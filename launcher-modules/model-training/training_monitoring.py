#!/usr/bin/env python3
"""
DuckBot Enhanced Training Monitoring System
Professional-grade real-time monitoring for model training with comprehensive metrics, logging, and visualization

Features:
- Real-time training metrics (loss, accuracy, gradient norms, learning rate)
- Performance monitoring (GPU/CPU, memory, throughput)
- Advanced logging with structured data
- Early stopping and checkpoint management
- Alerting and notifications
- Visualization dashboard
- Integration with DuckBot monitoring infrastructure
"""

import asyncio
import json
import logging
import os
import psutil
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import queue
import weakref
from contextlib import contextmanager
import traceback

# Try to import optional dependencies
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

try:
    from tensorboardX import SummaryWriter
    TENSORBOARD_AVAILABLE = True
except ImportError:
    TENSORBOARD_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DuckBot modules
try:
    from duckbot.core.monitoring_system import DuckBotMonitoring, SystemMetric, MetricType, AlertLevel
    from duckbot.core.logging_setup import setup_logging
    from duckbot.analytics.analytics_engine import AdvancedAnalyticsEngine, AnalyticsEvent, AnalyticsEventType
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    # Fallback logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class TrainingPhase(Enum):
    """Training phases for monitoring"""
    INITIALIZATION = "initialization"
    DATA_PREPARATION = "data_preparation"
    MODEL_LOADING = "model_loading"
    TRAINING = "training"
    VALIDATION = "validation"
    CHECKPOINTING = "checkpointing"
    EVALUATION = "evaluation"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class MetricCategory(Enum):
    """Categories of training metrics"""
    LOSS = "loss"
    ACCURACY = "accuracy"
    GRADIENT = "gradient"
    LEARNING_RATE = "learning_rate"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    GPU_UTILIZATION = "gpu_utilization"
    CPU_UTILIZATION = "cpu_utilization"
    CUSTOM = "custom"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class TrainingMetric:
    """Individual training metric"""
    name: str
    value: float
    category: MetricCategory
    timestamp: datetime
    step: int
    epoch: int
    phase: TrainingPhase
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemResourceMetric:
    """System resource metric"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    gpu_memory_used_gb: float = 0.0
    gpu_memory_total_gb: float = 0.0
    gpu_utilization_percent: float = 0.0
    gpu_temperature: float = 0.0
    disk_io_mb_s: float = 0.0
    network_io_mb_s: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TrainingAlert:
    """Training alert structure"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metric_name: str
    current_value: float
    threshold_value: float
    phase: TrainingPhase
    step: int
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CheckpointInfo:
    """Checkpoint information"""
    checkpoint_id: str
    step: int
    epoch: int
    loss: float
    accuracy: float
    learning_rate: float
    timestamp: datetime
    file_path: str
    is_best: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)

class TrainingMonitoringConfig:
    """Configuration for training monitoring"""

    def __init__(self):
        self.enable_real_time_monitoring = True
        self.metrics_collection_interval = 1.0  # seconds
        self.system_metrics_interval = 5.0  # seconds
        self.enable_tensorboard = TENSORBOARD_AVAILABLE
        self.enable_wandb = WANDB_AVAILABLE
        self.wandb_project = "duckbot-training"
        self.wandb_run_name = None
        self.enable_database_logging = True
        self.database_path = "training_monitoring.db"
        self.enable_alerts = True
        self.alert_cooldown_minutes = 5
        self.enable_early_stopping = True
        self.early_stopping_patience = 5
        self.early_stopping_min_delta = 0.001
        self.checkpoint_save_interval = 100  # steps
        self.max_checkpoints_to_keep = 5
        self.enable_performance_profiling = True
        self.log_level = "INFO"

class TrainingMetricsDatabase:
    """Database for storing training metrics and logs"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Training metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    category TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    epoch INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT
                )
            ''')

            # System metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    memory_used_gb REAL NOT NULL,
                    memory_available_gb REAL NOT NULL,
                    gpu_memory_used_gb REAL DEFAULT 0.0,
                    gpu_memory_total_gb REAL DEFAULT 0.0,
                    gpu_utilization_percent REAL DEFAULT 0.0,
                    gpu_temperature REAL DEFAULT 0.0,
                    disk_io_mb_s REAL DEFAULT 0.0,
                    network_io_mb_s REAL DEFAULT 0.0,
                    timestamp DATETIME NOT NULL
                )
            ''')

            # Checkpoints table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    epoch INTEGER NOT NULL,
                    loss REAL NOT NULL,
                    accuracy REAL DEFAULT 0.0,
                    learning_rate REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    file_path TEXT NOT NULL,
                    is_best BOOLEAN DEFAULT FALSE,
                    metrics TEXT
                )
            ''')

            # Alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_alerts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    phase TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME,
                    metadata TEXT
                )
            ''')

            # Training runs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_runs (
                    id TEXT PRIMARY KEY,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    status TEXT NOT NULL,
                    total_steps INTEGER DEFAULT 0,
                    total_epochs INTEGER DEFAULT 0,
                    current_step INTEGER DEFAULT 0,
                    current_epoch INTEGER DEFAULT 0,
                    best_loss REAL DEFAULT 0.0,
                    best_accuracy REAL DEFAULT 0.0,
                    config TEXT,
                    metadata TEXT
                )
            ''')

            # Create indexes for performance
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_metrics_run_step ON training_metrics(run_id, step)',
                'CREATE INDEX IF NOT EXISTS idx_metrics_run_timestamp ON training_metrics(run_id, timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_system_run_timestamp ON system_metrics(run_id, timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_checkpoints_run_step ON checkpoints(run_id, step)',
                'CREATE INDEX IF NOT EXISTS idx_alerts_run_timestamp ON training_alerts(run_id, timestamp)'
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

    def start_training_run(self, run_id: str, config: Dict[str, Any]) -> str:
        """Start a new training run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO training_runs (id, start_time, status, config)
                VALUES (?, ?, ?, ?)
            ''', (run_id, datetime.now(), "running", json.dumps(config)))
        return run_id

    def end_training_run(self, run_id: str, status: str):
        """End a training run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE training_runs
                SET end_time = ?, status = ?
                WHERE id = ?
            ''', (datetime.now(), status, run_id))

    def store_metric(self, run_id: str, metric: TrainingMetric):
        """Store a training metric"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO training_metrics
                (run_id, metric_name, value, category, step, epoch, phase, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_id, metric.name, metric.value, metric.category.value,
                metric.step, metric.epoch, metric.phase.value,
                metric.timestamp, json.dumps(metric.metadata)
            ))

    def store_system_metric(self, run_id: str, metric: SystemResourceMetric):
        """Store a system resource metric"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO system_metrics
                (run_id, cpu_percent, memory_percent, memory_used_gb, memory_available_gb,
                 gpu_memory_used_gb, gpu_memory_total_gb, gpu_utilization_percent, gpu_temperature,
                 disk_io_mb_s, network_io_mb_s, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_id, metric.cpu_percent, metric.memory_percent,
                metric.memory_used_gb, metric.memory_available_gb,
                metric.gpu_memory_used_gb, metric.gpu_memory_total_gb,
                metric.gpu_utilization_percent, metric.gpu_temperature,
                metric.disk_io_mb_s, metric.network_io_mb_s, metric.timestamp
            ))

    def store_checkpoint(self, run_id: str, checkpoint: CheckpointInfo):
        """Store checkpoint information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO checkpoints
                (run_id, checkpoint_id, step, epoch, loss, accuracy, learning_rate,
                 timestamp, file_path, is_best, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_id, checkpoint.checkpoint_id, checkpoint.step, checkpoint.epoch,
                checkpoint.loss, checkpoint.accuracy, checkpoint.learning_rate,
                checkpoint.timestamp, checkpoint.file_path, checkpoint.is_best,
                json.dumps(checkpoint.metrics)
            ))

    def store_alert(self, run_id: str, alert: TrainingAlert):
        """Store a training alert"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO training_alerts
                (id, run_id, severity, title, message, metric_name, current_value,
                 threshold_value, phase, step, timestamp, resolved, resolved_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id, run_id, alert.severity.value, alert.title, alert.message,
                alert.metric_name, alert.current_value, alert.threshold_value,
                alert.phase.value, alert.step, alert.timestamp, alert.resolved,
                alert.resolved_at, json.dumps(alert.metadata)
            ))

    def get_training_metrics(self, run_id: str, metric_name: str = None,
                           start_step: int = None, end_step: int = None) -> List[Dict]:
        """Retrieve training metrics"""
        query = "SELECT * FROM training_metrics WHERE run_id = ?"
        params = [run_id]

        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)

        if start_step is not None:
            query += " AND step >= ?"
            params.append(start_step)

        if end_step is not None:
            query += " AND step <= ?"
            params.append(end_step)

        query += " ORDER BY step, timestamp"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get training run summary"""
        with sqlite3.connect(self.db_path) as conn:
            # Get run info
            cursor = conn.execute('''
                SELECT * FROM training_runs WHERE id = ?
            ''', (run_id,))
            columns = [desc[0] for desc in cursor.description]
            run_info = dict(zip(columns, cursor.fetchone()))

            # Get metric statistics
            cursor = conn.execute('''
                SELECT metric_name, COUNT(*) as count, AVG(value) as avg, MIN(value) as min, MAX(value) as max
                FROM training_metrics
                WHERE run_id = ?
                GROUP BY metric_name
            ''', (run_id,))
            metric_stats = [dict(zip([desc[0] for desc in cursor.description], row))
                           for row in cursor.fetchall()]

            # Get checkpoint count
            cursor = conn.execute('''
                SELECT COUNT(*) as checkpoint_count FROM checkpoints WHERE run_id = ?
            ''', (run_id,))
            checkpoint_count = cursor.fetchone()[0]

            # Get alert count
            cursor = conn.execute('''
                SELECT COUNT(*) as alert_count FROM training_alerts WHERE run_id = ?
            ''', (run_id,))
            alert_count = cursor.fetchone()[0]

            return {
                "run_info": run_info,
                "metric_statistics": metric_stats,
                "checkpoint_count": checkpoint_count,
                "alert_count": alert_count
            }

class RealTimeMetricsCollector:
    """Real-time metrics collector for training"""

    def __init__(self, config: TrainingMonitoringConfig, database: TrainingMetricsDatabase):
        self.config = config
        self.database = database
        self.is_collecting = False
        self.collection_thread = None
        self.metrics_queue = queue.Queue()
        self.system_metrics_queue = queue.Queue()
        self.processors = []
        self.alert_manager = TrainingAlertManager(config, database)

        # System monitoring
        self.last_disk_io = None
        self.last_network_io = None

    def start_collection(self, run_id: str):
        """Start real-time metrics collection"""
        if self.is_collecting:
            return

        self.run_id = run_id
        self.is_collecting = True

        # Start metrics processors
        self._start_metrics_processor()
        self._start_system_metrics_processor()

        logging.info(f"Started real-time metrics collection for run {run_id}")

    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False

        # Wait for processors to finish
        for processor in self.processors:
            if processor.is_alive():
                processor.join(timeout=5)

        logging.info("Stopped real-time metrics collection")

    def record_metric(self, metric: TrainingMetric):
        """Record a training metric"""
        if self.is_collecting:
            self.metrics_queue.put(metric)

    def record_system_metric(self, metric: SystemResourceMetric):
        """Record a system resource metric"""
        if self.is_collecting:
            self.system_metrics_queue.put(metric)

    def _start_metrics_processor(self):
        """Start the metrics processing thread"""
        def process_metrics():
            while self.is_collecting:
                try:
                    metric = self.metrics_queue.get(timeout=1.0)

                    # Store in database
                    self.database.store_metric(self.run_id, metric)

                    # Send to alert manager
                    self.alert_manager.check_metric_alerts(metric)

                    # Integrate with DuckBot monitoring if available
                    if DUCKBOT_AVAILABLE:
                        self._integrate_with_duckbot_monitoring(metric)

                except queue.Empty:
                    continue
                except Exception as e:
                    logging.error(f"Error processing training metric: {e}")

        processor = threading.Thread(target=process_metrics, daemon=True)
        processor.start()
        self.processors.append(processor)

    def _start_system_metrics_processor(self):
        """Start the system metrics processing thread"""
        def collect_system_metrics():
            while self.is_collecting:
                try:
                    # Collect system metrics
                    system_metric = self._collect_system_metrics()
                    self.database.store_system_metric(self.run_id, system_metric)

                    # Check system alerts
                    self.alert_manager.check_system_alerts(system_metric)

                    time.sleep(self.config.system_metrics_interval)

                except Exception as e:
                    logging.error(f"Error collecting system metrics: {e}")
                    time.sleep(self.config.system_metrics_interval)

        processor = threading.Thread(target=collect_system_metrics, daemon=True)
        processor.start()
        self.processors.append(processor)

    def _collect_system_metrics(self) -> SystemResourceMetric:
        """Collect system resource metrics"""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()

        # GPU metrics (if available)
        gpu_memory_used = 0.0
        gpu_memory_total = 0.0
        gpu_utilization = 0.0
        gpu_temperature = 0.0

        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                gpu_memory_used = torch.cuda.memory_allocated() / (1024**3)  # GB
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                gpu_utilization = torch.cuda.utilization()

                # Try to get GPU temperature (nvidia-ml-py required)
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except ImportError:
                    pass
            except Exception:
                pass

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io_mb_s = 0.0
        if self.last_disk_io:
            disk_io_mb_s = (disk_io.read_bytes + disk_io.write_bytes -
                           (self.last_disk_io.read_bytes + self.last_disk_io.write_bytes)) / (1024**2)
        self.last_disk_io = disk_io

        # Network I/O
        net_io = psutil.net_io_counters()
        network_io_mb_s = 0.0
        if self.last_network_io:
            network_io_mb_s = (net_io.bytes_sent + net_io.bytes_recv -
                             (self.last_network_io.bytes_sent + self.last_network_io.bytes_recv)) / (1024**2)
        self.last_network_io = net_io

        return SystemResourceMetric(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            gpu_memory_used_gb=gpu_memory_used,
            gpu_memory_total_gb=gpu_memory_total,
            gpu_utilization_percent=gpu_utilization,
            gpu_temperature=gpu_temperature,
            disk_io_mb_s=disk_io_mb_s,
            network_io_mb_s=network_io_mb_s
        )

    def _integrate_with_duckbot_monitoring(self, metric: TrainingMetric):
        """Integrate with DuckBot monitoring system"""
        try:
            from duckbot.core.monitoring_system import get_monitoring

            monitoring = get_monitoring()

            # Map training metrics to system metrics
            metric_mapping = {
                MetricCategory.LOSS: "training_loss",
                MetricCategory.ACCURACY: "training_accuracy",
                MetricCategory.LEARNING_RATE: "learning_rate",
                MetricCategory.THROUGHPUT: "training_throughput"
            }

            if metric.category in metric_mapping:
                system_metric = SystemMetric(
                    name=metric_mapping[metric.category],
                    value=metric.value,
                    metric_type=MetricType.GAUGE,
                    timestamp=metric.timestamp,
                    tags={
                        "run_id": self.run_id,
                        "phase": metric.phase.value,
                        "step": str(metric.step),
                        "epoch": str(metric.epoch)
                    }
                )
                monitoring.database.store_system_metric(system_metric)
        except Exception as e:
            logging.debug(f"Could not integrate with DuckBot monitoring: {e}")

class TrainingAlertManager:
    """Manages training alerts and notifications"""

    def __init__(self, config: TrainingMonitoringConfig, database: TrainingMetricsDatabase):
        self.config = config
        self.database = database
        self.alert_rules = []
        self.alert_handlers = []
        self.last_alert_time = {}  # For cooldown
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            {
                "name": "high_loss",
                "condition": lambda metric: (metric.category == MetricCategory.LOSS and
                                           metric.value > 10.0),
                "severity": AlertSeverity.WARNING,
                "message": "High training loss detected: {value:.4f}",
                "cooldown_minutes": 10
            },
            {
                "name": "exploding_gradients",
                "condition": lambda metric: (metric.category == MetricCategory.GRADIENT and
                                           abs(metric.value) > 100.0),
                "severity": AlertSeverity.ERROR,
                "message": "Exploding gradients detected: {value:.4f}",
                "cooldown_minutes": 5
            },
            {
                "name": "vanishing_gradients",
                "condition": lambda metric: (metric.category == MetricCategory.GRADIENT and
                                           abs(metric.value) < 1e-8),
                "severity": AlertSeverity.WARNING,
                "message": "Vanishing gradients detected: {value:.4e}",
                "cooldown_minutes": 10
            },
            {
                "name": "low_accuracy",
                "condition": lambda metric: (metric.category == MetricCategory.ACCURACY and
                                           metric.value < 0.5 and metric.step > 100),
                "severity": AlertSeverity.WARNING,
                "message": "Low accuracy detected: {value:.2%}",
                "cooldown_minutes": 15
            },
            {
                "name": "high_memory_usage",
                "condition": lambda metric: (metric.category == MetricCategory.MEMORY and
                                           metric.value > 90.0),
                "severity": AlertSeverity.ERROR,
                "message": "High memory usage detected: {value:.1f}%",
                "cooldown_minutes": 5
            },
            {
                "name": "gpu_memory_full",
                "condition": lambda metric: (metric.category == MetricCategory.MEMORY and
                                           metric.value > 95.0),
                "severity": AlertSeverity.CRITICAL,
                "message": "GPU memory nearly full: {value:.1f}%",
                "cooldown_minutes": 2
            }
        ]

    def check_metric_alerts(self, metric: TrainingMetric):
        """Check for metric-based alerts"""
        if not self.config.enable_alerts:
            return

        for rule in self.alert_rules:
            try:
                if rule["condition"](metric):
                    self._create_alert_from_rule(rule, metric)
            except Exception as e:
                logging.error(f"Error checking alert rule {rule['name']}: {e}")

    def check_system_alerts(self, metric: SystemResourceMetric):
        """Check for system-based alerts"""
        if not self.config.enable_alerts:
            return

        # High CPU usage
        if metric.cpu_percent > 95:
            self._create_system_alert(
                "high_cpu_usage",
                AlertSeverity.CRITICAL,
                f"Critical CPU usage: {metric.cpu_percent:.1f}%",
                metric
            )
        elif metric.cpu_percent > 85:
            self._create_system_alert(
                "high_cpu_usage",
                AlertSeverity.WARNING,
                f"High CPU usage: {metric.cpu_percent:.1f}%",
                metric
            )

        # High memory usage
        if metric.memory_percent > 95:
            self._create_system_alert(
                "high_memory_usage",
                AlertSeverity.CRITICAL,
                f"Critical memory usage: {metric.memory_percent:.1f}%",
                metric
            )
        elif metric.memory_percent > 85:
            self._create_system_alert(
                "high_memory_usage",
                AlertSeverity.WARNING,
                f"High memory usage: {metric.memory_percent:.1f}%",
                metric
            )

        # High GPU usage
        if metric.gpu_utilization_percent > 95:
            self._create_system_alert(
                "high_gpu_usage",
                AlertSeverity.WARNING,
                f"High GPU utilization: {metric.gpu_utilization_percent:.1f}%",
                metric
            )

        # High GPU temperature
        if metric.gpu_temperature > 85:
            self._create_system_alert(
                "high_gpu_temperature",
                AlertSeverity.ERROR,
                f"High GPU temperature: {metric.gpu_temperature:.1f}°C",
                metric
            )
        elif metric.gpu_temperature > 75:
            self._create_system_alert(
                "high_gpu_temperature",
                AlertSeverity.WARNING,
                f"Elevated GPU temperature: {metric.gpu_temperature:.1f}°C",
                metric
            )

    def _create_alert_from_rule(self, rule: Dict, metric: TrainingMetric):
        """Create an alert from a rule"""
        # Check cooldown
        rule_name = rule["name"]
        last_time = self.last_alert_time.get(rule_name, datetime.min)
        cooldown = timedelta(minutes=rule.get("cooldown_minutes", self.config.alert_cooldown_minutes))

        if datetime.now() - last_time < cooldown:
            return

        # Create alert
        alert_id = f"{rule_name}_{metric.step}_{int(time.time())}"

        message = rule["message"].format(value=metric.value)

        alert = TrainingAlert(
            id=alert_id,
            severity=rule["severity"],
            title=rule["name"].replace("_", " ").title(),
            message=message,
            timestamp=datetime.now(),
            metric_name=metric.name,
            current_value=metric.value,
            threshold_value=0.0,  # Will be set based on rule
            phase=metric.phase,
            step=metric.step,
            metadata={
                "rule_name": rule_name,
                "category": metric.category.value,
                "epoch": metric.epoch
            }
        )

        self._handle_alert(alert)
        self.last_alert_time[rule_name] = datetime.now()

    def _create_system_alert(self, alert_name: str, severity: AlertSeverity,
                            message: str, metric: SystemResourceMetric):
        """Create a system alert"""
        # Check cooldown
        last_time = self.last_alert_time.get(alert_name, datetime.min)
        cooldown = timedelta(minutes=self.config.alert_cooldown_minutes)

        if datetime.now() - last_time < cooldown:
            return

        alert_id = f"{alert_name}_{int(time.time())}"

        alert = TrainingAlert(
            id=alert_id,
            severity=severity,
            title=alert_name.replace("_", " ").title(),
            message=message,
            timestamp=datetime.now(),
            metric_name=alert_name,
            current_value=0.0,
            threshold_value=0.0,
            phase=TrainingPhase.TRAINING,
            step=0,
            metadata={
                "cpu_percent": metric.cpu_percent,
                "memory_percent": metric.memory_percent,
                "gpu_utilization": metric.gpu_utilization_percent,
                "gpu_temperature": metric.gpu_temperature
            }
        )

        self._handle_alert(alert)
        self.last_alert_time[alert_name] = datetime.now()

    def _handle_alert(self, alert: TrainingAlert):
        """Handle an alert (store and notify)"""
        # Store in database
        self.database.store_alert(self.run_id, alert)

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logging.error(f"Error in alert handler: {e}")

        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }[alert.severity]

        logging.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")

    def add_alert_handler(self, handler: Callable[[TrainingAlert], None]):
        """Add an alert handler"""
        self.alert_handlers.append(handler)

class TrainingVisualizationManager:
    """Manages training visualization and dashboards"""

    def __init__(self, config: TrainingMonitoringConfig):
        self.config = config
        self.tensorboard_writer = None
        self.wandb_run = None
        self._setup_visualization()

    def _setup_visualization(self):
        """Setup visualization tools"""
        # TensorBoard
        if self.config.enable_tensorboard and TENSORBOARD_AVAILABLE:
            log_dir = Path("logs") / "tensorboard" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            log_dir.mkdir(parents=True, exist_ok=True)
            self.tensorboard_writer = SummaryWriter(log_dir)
            logging.info(f"TensorBoard logging enabled at: {log_dir}")

        # Weights & Biases
        if self.config.enable_wandb and WANDB_AVAILABLE:
            wandb.init(
                project=self.config.wandb_project,
                name=self.config.wandb_run_name,
                config=asdict(self.config) if hasattr(self.config, '__dict__') else {}
            )
            self.wandb_run = wandb
            logging.info("W&B logging enabled")

    def log_metric(self, metric: TrainingMetric):
        """Log a metric to visualization tools"""
        step = metric.step

        # TensorBoard
        if self.tensorboard_writer:
            self.tensorboard_writer.add_scalar(f"training/{metric.name}", metric.value, step)
            self.tensorboard_writer.add_scalar(f"phase/{metric.phase.value}/{metric.name}", metric.value, step)

        # W&B
        if self.wandb_run:
            self.wandb_run.log({
                f"training/{metric.name}": metric.value,
                f"phase/{metric.phase.value}/{metric.name}": metric.value,
                "step": step,
                "epoch": metric.epoch
            })

    def log_system_metrics(self, metrics: SystemResourceMetric, step: int):
        """Log system metrics to visualization tools"""
        if self.tensorboard_writer:
            self.tensorboard_writer.add_scalar("system/cpu_percent", metrics.cpu_percent, step)
            self.tensorboard_writer.add_scalar("system/memory_percent", metrics.memory_percent, step)
            self.tensorboard_writer.add_scalar("system/gpu_utilization", metrics.gpu_utilization_percent, step)
            self.tensorboard_writer.add_scalar("system/gpu_temperature", metrics.gpu_temperature, step)

        if self.wandb_run:
            self.wandb_run.log({
                "system/cpu_percent": metrics.cpu_percent,
                "system/memory_percent": metrics.memory_percent,
                "system/gpu_utilization": metrics.gpu_utilization_percent,
                "system/gpu_temperature": metrics.gpu_temperature,
                "step": step
            })

    def close(self):
        """Close visualization tools"""
        if self.tensorboard_writer:
            self.tensorboard_writer.close()

        if self.wandb_run:
            self.wandb_run.finish()

class EarlyStoppingManager:
    """Manages early stopping logic"""

    def __init__(self, patience: int = 5, min_delta: float = 0.001, monitor: str = "loss"):
        self.patience = patience
        self.min_delta = min_delta
        self.monitor = monitor
        self.best_value = float('inf') if monitor == "loss" else float('-inf')
        self.wait = 0
        self.stopped_epoch = 0
        self.should_stop = False

    def update(self, current_value: float, epoch: int) -> bool:
        """Update early stopping state and return if should stop"""
        if self.monitor == "loss":
            improved = current_value < self.best_value - self.min_delta
        else:  # accuracy or other higher-is-better metric
            improved = current_value > self.best_value + self.min_delta

        if improved:
            self.best_value = current_value
            self.wait = 0
        else:
            self.wait += 1

            if self.wait >= self.patience:
                self.stopped_epoch = epoch
                self.should_stop = True
                return True

        return False

    def reset(self):
        """Reset early stopping state"""
        self.best_value = float('inf') if self.monitor == "loss" else float('-inf')
        self.wait = 0
        self.stopped_epoch = 0
        self.should_stop = False

class TrainingMonitor:
    """Main training monitoring system"""

    def __init__(self, config: TrainingMonitoringConfig = None):
        self.config = config or TrainingMonitoringConfig()

        # Initialize logging
        self.logger = setup_logging("training_monitor", self.config.log_level)

        # Initialize database
        if self.config.enable_database_logging:
            self.database = TrainingMetricsDatabase(self.config.database_path)
        else:
            self.database = None

        # Initialize components
        self.metrics_collector = RealTimeMetricsCollector(self.config, self.database)
        self.visualization_manager = TrainingVisualizationManager(self.config)
        self.early_stopping_manager = EarlyStoppingManager(
            self.config.early_stopping_patience,
            self.config.early_stopping_min_delta
        )

        # Training state
        self.current_run_id = None
        self.current_step = 0
        self.current_epoch = 0
        self.current_phase = TrainingPhase.INITIALIZATION
        self.start_time = None
        self.checkpoints = []
        self.best_metrics = {}

        # Performance tracking
        self.step_times = []
        self.epoch_times = []
        self.last_step_time = None

        # Callbacks
        self.callbacks = {
            "on_metric": [],
            "on_checkpoint": [],
            "on_alert": [],
            "on_phase_change": [],
            "on_epoch_end": [],
            "on_step_end": []
        }

    def start_training_run(self, run_id: str = None, config: Dict[str, Any] = None) -> str:
        """Start a new training run"""
        self.current_run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        self.start_time = datetime.now()
        self.current_step = 0
        self.current_epoch = 0
        self.current_phase = TrainingPhase.INITIALIZATION

        # Reset state
        self.checkpoints = []
        self.best_metrics = {}
        self.step_times = []
        self.epoch_times = []
        self.early_stopping_manager.reset()

        # Start database run
        if self.database:
            self.database.start_training_run(self.current_run_id, config or {})

        # Start metrics collection
        if self.config.enable_real_time_monitoring:
            self.metrics_collector.start_collection(self.current_run_id)

        # Log start event
        self.record_metric(
            name="training_start",
            value=1.0,
            category=MetricCategory.CUSTOM,
            phase=TrainingPhase.INITIALIZATION,
            metadata={"config": config or {}}
        )

        self.logger.info(f"Started training run: {self.current_run_id}")
        return self.current_run_id

    def end_training_run(self, status: str = "completed"):
        """End the current training run"""
        if not self.current_run_id:
            return

        # Calculate total training time
        total_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        # Record final metrics
        self.record_metric(
            name="training_end",
            value=1.0,
            category=MetricCategory.CUSTOM,
            phase=TrainingPhase.COMPLETED,
            metadata={
                "status": status,
                "total_time_seconds": total_time,
                "total_steps": self.current_step,
                "total_epochs": self.current_epoch,
                "best_metrics": self.best_metrics
            }
        )

        # Stop metrics collection
        if self.config.enable_real_time_monitoring:
            self.metrics_collector.stop_collection()

        # Close visualization tools
        self.visualization_manager.close()

        # End database run
        if self.database:
            self.database.end_training_run(self.current_run_id, status)

        self.logger.info(f"Ended training run: {self.current_run_id} (status: {status})")
        self.current_run_id = None

    def set_phase(self, phase: TrainingPhase):
        """Set the current training phase"""
        if phase != self.current_phase:
            old_phase = self.current_phase
            self.current_phase = phase

            # Record phase change
            self.record_metric(
                name="phase_change",
                value=1.0,
                category=MetricCategory.CUSTOM,
                phase=phase,
                metadata={"old_phase": old_phase.value, "new_phase": phase.value}
            )

            # Trigger callbacks
            self._trigger_callbacks("on_phase_change", {
                "old_phase": old_phase,
                "new_phase": phase,
                "step": self.current_step,
                "epoch": self.current_epoch
            })

    def record_metric(self, name: str, value: float, category: MetricCategory,
                     phase: TrainingPhase = None, metadata: Dict[str, Any] = None):
        """Record a training metric"""
        if not self.current_run_id:
            return

        metric = TrainingMetric(
            name=name,
            value=value,
            category=category,
            timestamp=datetime.now(),
            step=self.current_step,
            epoch=self.current_epoch,
            phase=phase or self.current_phase,
            metadata=metadata or {}
        )

        # Send to metrics collector
        self.metrics_collector.record_metric(metric)

        # Send to visualization tools
        self.visualization_manager.log_metric(metric)

        # Update best metrics
        if name in ["loss", "accuracy", "val_loss", "val_accuracy"]:
            if name not in self.best_metrics or (
                (name.endswith("loss") and value < self.best_metrics[name]) or
                (name.endswith("accuracy") and value > self.best_metrics[name])
            ):
                self.best_metrics[name] = value

        # Trigger callbacks
        self._trigger_callbacks("on_metric", metric)

    def record_loss(self, loss: float, phase: TrainingPhase = TrainingPhase.TRAINING):
        """Record training loss"""
        self.record_metric("loss", loss, MetricCategory.LOSS, phase)

    def record_accuracy(self, accuracy: float, phase: TrainingPhase = TrainingPhase.TRAINING):
        """Record training accuracy"""
        self.record_metric("accuracy", accuracy, MetricCategory.ACCURACY, phase)

    def record_gradient_norm(self, grad_norm: float):
        """Record gradient norm"""
        self.record_metric("gradient_norm", grad_norm, MetricCategory.GRADIENT)

    def record_learning_rate(self, lr: float):
        """Record learning rate"""
        self.record_metric("learning_rate", lr, MetricCategory.LEARNING_RATE)

    def record_throughput(self, samples_per_second: float):
        """Record training throughput"""
        self.record_metric("throughput", samples_per_second, MetricCategory.THROUGHPUT)

    def step_start(self):
        """Called at the start of a training step"""
        self.last_step_time = time.time()

    def step_end(self):
        """Called at the end of a training step"""
        if self.last_step_time:
            step_time = time.time() - self.last_step_time
            self.step_times.append(step_time)

            # Keep only last 100 step times for average
            if len(self.step_times) > 100:
                self.step_times.pop(0)

            # Calculate and record average step time
            avg_step_time = sum(self.step_times) / len(self.step_times)
            self.record_metric("avg_step_time", avg_step_time, MetricCategory.CUSTOM)

        self.current_step += 1

        # Trigger callbacks
        self._trigger_callbacks("on_step_end", {
            "step": self.current_step,
            "epoch": self.current_epoch
        })

    def epoch_end(self):
        """Called at the end of a training epoch"""
        epoch_time = 0
        if self.start_time and len(self.epoch_times) > 0:
            epoch_time = time.time() - self.epoch_times[-1]

        self.epoch_times.append(time.time())
        self.current_epoch += 1

        # Record epoch metrics
        self.record_metric("epoch", self.current_epoch, MetricCategory.CUSTOM)

        # Trigger callbacks
        self._trigger_callbacks("on_epoch_end", {
            "step": self.current_step,
            "epoch": self.current_epoch,
            "epoch_time": epoch_time
        })

    def save_checkpoint(self, checkpoint_path: str, is_best: bool = False,
                       metrics: Dict[str, float] = None):
        """Record checkpoint information"""
        checkpoint = CheckpointInfo(
            checkpoint_id=f"checkpoint_{self.current_step}",
            step=self.current_step,
            epoch=self.current_epoch,
            loss=self.best_metrics.get("loss", float('inf')),
            accuracy=self.best_metrics.get("accuracy", 0.0),
            learning_rate=self.best_metrics.get("learning_rate", 0.0),
            timestamp=datetime.now(),
            file_path=checkpoint_path,
            is_best=is_best,
            metrics=metrics or {}
        )

        self.checkpoints.append(checkpoint)

        # Store in database
        if self.database:
            self.database.store_checkpoint(self.current_run_id, checkpoint)

        # Trigger callbacks
        self._trigger_callbacks("on_checkpoint", checkpoint)

        self.logger.info(f"Checkpoint saved: {checkpoint_path} (step {self.current_step}, loss: {checkpoint.loss:.4f})")

    def check_early_stopping(self, current_value: float) -> bool:
        """Check if training should stop early"""
        if not self.config.enable_early_stopping:
            return False

        should_stop = self.early_stopping_manager.update(current_value, self.current_epoch)

        if should_stop:
            self.record_metric(
                name="early_stopping_triggered",
                value=1.0,
                category=MetricCategory.CUSTOM,
                metadata={
                    "patience": self.early_stopping_manager.patience,
                    "best_value": self.early_stopping_manager.best_value,
                    "current_value": current_value
                }
            )

            self.logger.info(f"Early stopping triggered at epoch {self.current_epoch}")

        return should_stop

    def get_training_summary(self) -> Dict[str, Any]:
        """Get current training summary"""
        if not self.current_run_id:
            return {}

        summary = {
            "run_id": self.current_run_id,
            "current_step": self.current_step,
            "current_epoch": self.current_epoch,
            "current_phase": self.current_phase.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_time": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "best_metrics": self.best_metrics,
            "total_checkpoints": len(self.checkpoints),
            "avg_step_time": sum(self.step_times) / len(self.step_times) if self.step_times else 0
        }

        # Add database summary if available
        if self.database:
            try:
                db_summary = self.database.get_run_summary(self.current_run_id)
                summary["database_summary"] = db_summary
            except Exception as e:
                self.logger.error(f"Error getting database summary: {e}")

        return summary

    def get_metrics_history(self, metric_name: str, steps: int = None) -> List[Dict]:
        """Get historical data for a specific metric"""
        if not self.database or not self.current_run_id:
            return []

        return self.database.get_training_metrics(
            self.current_run_id,
            metric_name,
            end_step=self.current_step if steps is None else self.current_step - steps
        )

    def add_callback(self, event_type: str, callback: Callable):
        """Add a callback for a specific event"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    def _trigger_callbacks(self, event_type: str, data: Any):
        """Trigger callbacks for a specific event"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in callback for {event_type}: {e}")

    def add_alert_handler(self, handler: Callable[[TrainingAlert], None]):
        """Add an alert handler"""
        if hasattr(self.metrics_collector, 'alert_manager'):
            self.metrics_collector.alert_manager.add_alert_handler(handler)

# Convenience functions for easy integration
def create_training_monitor(config: TrainingMonitoringConfig = None) -> TrainingMonitor:
    """Create a training monitor with default configuration"""
    return TrainingMonitor(config)

def get_default_config() -> TrainingMonitoringConfig:
    """Get default training monitoring configuration"""
    return TrainingMonitoringConfig()

# Example usage and testing
if __name__ == "__main__":
    # Test the training monitoring system
    print("Testing DuckBot Training Monitoring System")

    # Create monitor with default config
    monitor = create_training_monitor()

    # Start a training run
    run_id = monitor.start_training_run(
        config={"model": "test_model", "dataset": "test_dataset"}
    )

    print(f"Started training run: {run_id}")

    # Simulate training
    monitor.set_phase(TrainingPhase.TRAINING)

    for epoch in range(3):
        monitor.epoch_end()

        for step in range(10):
            monitor.step_start()

            # Simulate some metrics
            loss = 2.0 / (epoch + 1) + 0.1 * np.random.random()
            accuracy = 0.5 + 0.1 * epoch + 0.05 * np.random.random()

            monitor.record_loss(loss)
            monitor.record_accuracy(accuracy)
            monitor.record_learning_rate(0.001 * (0.9 ** epoch))
            monitor.record_throughput(100.0 + 10.0 * np.random.random())

            monitor.step_end()

            time.sleep(0.1)  # Simulate training time

        # Save checkpoint at end of epoch
        monitor.save_checkpoint(
            checkpoint_path=f"checkpoints/epoch_{epoch}.pt",
            is_best=(epoch == 2),
            metrics={"loss": loss, "accuracy": accuracy}
        )

        # Check early stopping
        if monitor.check_early_stopping(loss):
            print("Early stopping triggered!")
            break

    # Get training summary
    summary = monitor.get_training_summary()
    print("\nTraining Summary:")
    print(json.dumps(summary, indent=2, default=str))

    # End training run
    monitor.end_training_run("completed")

    print("\nTraining monitoring test completed!")
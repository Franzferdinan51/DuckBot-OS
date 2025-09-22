#!/usr/bin/env python3
"""
DuckBot Structured Training Logger
Professional-grade structured logging system for model training with comprehensive data capture

Features:
- Structured JSON logging with standardized schema
- Automatic correlation IDs for traceability
- Performance timing and profiling
- Error tracking and exception handling
- Log aggregation and filtering
- Integration with external logging services
- Multi-format output (JSON, CSV, database)
"""

import json
import logging
import os
import sys
import time
import traceback
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from contextlib import contextmanager
import threading
import queue
import sqlite3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DuckBot modules
try:
    from duckbot.core.logging_setup import setup_logging
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False

class LogLevel(Enum):
    """Log levels with standardized values"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Categories of training logs"""
    SYSTEM = "system"
    TRAINING = "training"
    VALIDATION = "validation"
    DATA = "data"
    MODEL = "model"
    OPTIMIZER = "optimizer"
    HARDWARE = "hardware"
    CHECKPOINT = "checkpoint"
    METRIC = "metric"
    ERROR = "error"
    PERFORMANCE = "performance"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    EXTERNAL_SERVICE = "external_service"

class EventPhase(Enum):
    """Phases of training events"""
    INITIALIZATION = "initialization"
    CONFIGURATION = "configuration"
    DATA_LOADING = "data_loading"
    DATA_PREPROCESSING = "data_preprocessing"
    MODEL_LOADING = "model_loading"
    TRAINING_START = "training_start"
    EPOCH_START = "epoch_start"
    BATCH_START = "batch_start"
    BATCH_END = "batch_end"
    EPOCH_END = "epoch_end"
    VALIDATION_START = "validation_start"
    VALIDATION_END = "validation_end"
    CHECKPOINT_SAVE = "checkpoint_save"
    CHECKPOINT_LOAD = "checkpoint_load"
    TRAINING_END = "training_end"
    ERROR = "error"
    RECOVERY = "recovery"

@dataclass
class StructuredLogEntry:
    """Structured log entry with comprehensive metadata"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    event_phase: EventPhase
    message: str
    correlation_id: str
    run_id: str
    step: int = 0
    epoch: int = 0
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None
    user_context: Optional[Dict[str, Any]] = None
    system_info: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category.value,
            "event_phase": self.event_phase.value,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "run_id": self.run_id,
            "step": self.step,
            "epoch": self.epoch,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "error_info": self.error_info,
            "performance_metrics": self.performance_metrics,
            "user_context": self.user_context,
            "system_info": self.system_info
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)

@dataclass
class PerformanceTimer:
    """Performance timing context"""
    start_time: float
    checkpoint_times: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def checkpoint(self, name: str):
        """Record a checkpoint time"""
        self.checkpoint_times[name] = time.time()

    def get_duration(self, checkpoint: str = None) -> float:
        """Get duration from start or from checkpoint"""
        end_time = self.checkpoint_times.get(checkpoint, time.time())
        return (end_time - self.start_time) * 1000  # Return in milliseconds

class StructuredLoggerConfig:
    """Configuration for structured logging"""

    def __init__(self):
        self.enable_json_logging = True
        self.enable_database_logging = True
        self.enable_file_logging = True
        self.enable_console_logging = True
        self.enable_performance_profiling = True
        self.log_file_path = "logs/training_structured.log"
        self.database_path = "training_logs.db"
        self.max_log_file_size = 100 * 1024 * 1024  # 100MB
        self.backup_count = 5
        self.log_level_filter = LogLevel.DEBUG
        self.enable_correlation_ids = True
        self.enable_timing = True
        self.compression_enabled = True
        self.external_logging_services = []  # List of service names
        self.batch_size = 100  # For batch processing
        self.flush_interval = 5.0  # seconds

class LogDatabase:
    """Database for storing structured logs"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
        self._setup_indexes()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Main logs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS structured_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    event_phase TEXT NOT NULL,
                    message TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    step INTEGER DEFAULT 0,
                    epoch INTEGER DEFAULT 0,
                    duration_ms REAL,
                    metadata TEXT,
                    error_info TEXT,
                    performance_metrics TEXT,
                    user_context TEXT,
                    system_info TEXT
                )
            ''')

            # Performance metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id INTEGER,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    FOREIGN KEY (log_id) REFERENCES structured_logs (id)
                )
            ''')

            # Error tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id INTEGER,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    context TEXT,
                    FOREIGN KEY (log_id) REFERENCES structured_logs (id)
                )
            ''')

            # Log aggregation table for summaries
            conn.execute('''
                CREATE TABLE IF NOT EXISTS log_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    event_phase TEXT NOT NULL,
                    log_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    avg_duration_ms REAL,
                    min_duration_ms REAL,
                    max_duration_ms REAL,
                    first_timestamp DATETIME,
                    last_timestamp DATETIME,
                    summary_date DATE DEFAULT CURRENT_DATE
                )
            ''')

    def _setup_indexes(self):
        """Setup database indexes for performance"""
        with sqlite3.connect(self.db_path) as conn:
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON structured_logs(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_logs_run_id ON structured_logs(run_id)',
                'CREATE INDEX IF NOT EXISTS idx_logs_level ON structured_logs(level)',
                'CREATE INDEX IF NOT EXISTS idx_logs_category ON structured_logs(category)',
                'CREATE INDEX IF NOT EXISTS idx_logs_correlation ON structured_logs(correlation_id)',
                'CREATE INDEX IF NOT EXISTS idx_performance_log_id ON performance_metrics(log_id)',
                'CREATE INDEX IF NOT EXISTS idx_error_log_id ON error_logs(log_id)',
                'CREATE INDEX IF NOT EXISTS idx_summary_run_phase ON log_summaries(run_id, event_phase)',
                'CREATE INDEX IF NOT EXISTS idx_summary_date ON log_summaries(summary_date)'
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

    def store_log(self, log_entry: StructuredLogEntry) -> int:
        """Store a log entry and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO structured_logs
                (timestamp, level, category, event_phase, message, correlation_id, run_id,
                 step, epoch, duration_ms, metadata, error_info, performance_metrics,
                 user_context, system_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.timestamp,
                log_entry.level.value,
                log_entry.category.value,
                log_entry.event_phase.value,
                log_entry.message,
                log_entry.correlation_id,
                log_entry.run_id,
                log_entry.step,
                log_entry.epoch,
                log_entry.duration_ms,
                json.dumps(log_entry.metadata),
                json.dumps(log_entry.error_info) if log_entry.error_info else None,
                json.dumps(log_entry.performance_metrics) if log_entry.performance_metrics else None,
                json.dumps(log_entry.user_context) if log_entry.user_context else None,
                json.dumps(log_entry.system_info) if log_entry.system_info else None
            ))
            return cursor.lastrowid

    def store_performance_metrics(self, log_id: int, metrics: Dict[str, float]):
        """Store performance metrics for a log entry"""
        with sqlite3.connect(self.db_path) as conn:
            for metric_name, value in metrics.items():
                conn.execute('''
                    INSERT INTO performance_metrics (log_id, metric_name, value)
                    VALUES (?, ?, ?)
                ''', (log_id, metric_name, value))

    def store_error_log(self, log_id: int, error_info: Dict[str, Any]):
        """Store error information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO error_logs
                (log_id, error_type, error_message, stack_trace, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                log_id,
                error_info.get("type", "Unknown"),
                error_info.get("message", ""),
                error_info.get("stack_trace", ""),
                json.dumps(error_info.get("context", {}))
            ))

    def query_logs(self, run_id: str = None, level: LogLevel = None,
                   category: LogCategory = None, start_time: datetime = None,
                   end_time: datetime = None, limit: int = 1000) -> List[Dict]:
        """Query logs with various filters"""
        query = "SELECT * FROM structured_logs WHERE 1=1"
        params = []

        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)

        if level:
            query += " AND level = ?"
            params.append(level.value)

        if category:
            query += " AND category = ?"
            params.append(category.value)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_log_summary(self, run_id: str) -> Dict[str, Any]:
        """Get summary statistics for a training run"""
        with sqlite3.connect(self.db_path) as conn:
            # Basic counts
            cursor = conn.execute('''
                SELECT level, category, COUNT(*) as count
                FROM structured_logs
                WHERE run_id = ?
                GROUP BY level, category
            ''', (run_id,))

            level_category_counts = {}
            for row in cursor.fetchall():
                level, category, count = row
                if level not in level_category_counts:
                    level_category_counts[level] = {}
                level_category_counts[level][category] = count

            # Performance metrics
            cursor = conn.execute('''
                SELECT metric_name, AVG(value) as avg_value, MIN(value) as min_value,
                       MAX(value) as max_value, COUNT(*) as count
                FROM performance_metrics pm
                JOIN structured_logs sl ON pm.log_id = sl.id
                WHERE sl.run_id = ?
                GROUP BY metric_name
            ''', (run_id,))

            performance_summary = {}
            for row in cursor.fetchall():
                metric_name, avg_value, min_value, max_value, count = row
                performance_summary[metric_name] = {
                    "avg": avg_value,
                    "min": min_value,
                    "max": max_value,
                    "count": count
                }

            # Error summary
            cursor = conn.execute('''
                SELECT el.error_type, COUNT(*) as count
                FROM error_logs el
                JOIN structured_logs sl ON el.log_id = sl.id
                WHERE sl.run_id = ?
                GROUP BY el.error_type
            ''', (run_id,))

            error_summary = dict(cursor.fetchall())

            # Time range
            cursor = conn.execute('''
                SELECT MIN(timestamp) as start_time, MAX(timestamp) as end_time
                FROM structured_logs
                WHERE run_id = ?
            ''', (run_id,))

            time_range = cursor.fetchone()

            return {
                "run_id": run_id,
                "level_category_counts": level_category_counts,
                "performance_summary": performance_summary,
                "error_summary": error_summary,
                "time_range": {
                    "start": time_range[0],
                    "end": time_range[1]
                } if time_range[0] else None
            }

class LogBatchProcessor:
    """Processes log entries in batches for performance"""

    def __init__(self, database: LogDatabase, batch_size: int = 100, flush_interval: float = 5.0):
        self.database = database
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_queue = queue.Queue()
        self.batch = []
        self.is_processing = False
        self.processor_thread = None
        self.last_flush_time = time.time()

    def start(self):
        """Start the batch processor"""
        if self.is_processing:
            return

        self.is_processing = True
        self.processor_thread = threading.Thread(target=self._process_batches, daemon=True)
        self.processor_thread.start()

    def stop(self):
        """Stop the batch processor and flush remaining logs"""
        self.is_processing = False
        if self.processor_thread:
            self.processor_thread.join(timeout=10)

        # Flush remaining batch
        if self.batch:
            self._flush_batch()

    def add_log(self, log_entry: StructuredLogEntry):
        """Add a log entry to the batch processor"""
        self.log_queue.put(log_entry)

    def _process_batches(self):
        """Process log batches in the background"""
        while self.is_processing:
            try:
                # Add logs from queue to batch
                while len(self.batch) < self.batch_size:
                    try:
                        log_entry = self.log_queue.get(timeout=0.1)
                        self.batch.append(log_entry)
                    except queue.Empty:
                        break

                # Flush if batch is full or interval has passed
                if (len(self.batch) >= self.batch_size or
                    time.time() - self.last_flush_time >= self.flush_interval):
                    self._flush_batch()

                time.sleep(0.1)

            except Exception as e:
                print(f"Error in batch processor: {e}")
                time.sleep(1)

    def _flush_batch(self):
        """Flush the current batch to database"""
        if not self.batch:
            return

        try:
            with self.database.lock:
                for log_entry in self.batch:
                    log_id = self.database.store_log(log_entry)

                    # Store performance metrics if present
                    if log_entry.performance_metrics:
                        self.database.store_performance_metrics(log_id, log_entry.performance_metrics)

                    # Store error info if present
                    if log_entry.error_info:
                        self.database.store_error_log(log_id, log_entry.error_info)

            self.batch.clear()
            self.last_flush_time = time.time()

        except Exception as e:
            print(f"Error flushing log batch: {e}")

class StructuredLogger:
    """Main structured logging system"""

    def __init__(self, config: StructuredLoggerConfig = None):
        self.config = config or StructuredLoggerConfig()
        self.run_id = None
        self.correlation_id = None
        self.timers = {}  # Active performance timers
        self.custom_fields = {}  # Custom fields to include in all logs
        self.filters = []  # Log filters

        # Initialize traditional logger
        if DUCKBOT_AVAILABLE:
            self.traditional_logger = setup_logging("structured_training", self.config.log_level_filter.value)
        else:
            self.traditional_logger = logging.getLogger("structured_training")
            self.traditional_logger.setLevel(getattr(logging, self.config.log_level_filter.value))

        # Initialize database
        if self.config.enable_database_logging:
            self.database = LogDatabase(self.config.database_path)
            self.batch_processor = LogBatchProcessor(self.database, self.config.batch_size, self.config.flush_interval)
            self.batch_processor.start()

        # Setup file logging
        if self.config.enable_file_logging:
            self._setup_file_logging()

        # Performance tracking
        self.performance_metrics = {}

    def _setup_file_logging(self):
        """Setup file logging with rotation"""
        log_path = Path(self.config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup JSON file handler
        if self.config.enable_json_logging:
            json_handler = logging.handlers.RotatingFileHandler(
                log_path.with_suffix('.json'),
                maxBytes=self.config.max_log_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            json_handler.setLevel(getattr(logging, self.config.log_level_filter.value))
            json_handler.setFormatter(JSONFormatter())
            self.traditional_logger.addHandler(json_handler)

        # Setup human-readable file handler
        human_handler = logging.handlers.RotatingFileHandler(
            log_path.with_suffix('.log'),
            maxBytes=self.config.max_log_file_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        human_handler.setLevel(getattr(logging, self.config.log_level_filter.value))
        human_handler.setFormatter(HumanReadableFormatter())
        self.traditional_logger.addHandler(human_handler)

    def set_run_id(self, run_id: str):
        """Set the current training run ID"""
        self.run_id = run_id

    def set_correlation_id(self, correlation_id: str = None):
        """Set the correlation ID for traceability"""
        if correlation_id is None and self.config.enable_correlation_ids:
            correlation_id = str(uuid.uuid4())
        self.correlation_id = correlation_id

    def add_custom_field(self, key: str, value: Any):
        """Add a custom field to all subsequent logs"""
        self.custom_fields[key] = value

    def clear_custom_fields(self):
        """Clear all custom fields"""
        self.custom_fields.clear()

    @contextmanager
    def timer(self, name: str, metadata: Dict[str, Any] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        timer = PerformanceTimer(start_time, metadata or {})

        try:
            yield timer
        finally:
            duration = timer.get_duration()
            self._log_performance_timer(name, duration, timer.metadata)

    def start_timer(self, name: str, metadata: Dict[str, Any] = None) -> PerformanceTimer:
        """Start a performance timer"""
        timer = PerformanceTimer(time.time(), metadata or {})
        self.timers[name] = timer
        return timer

    def end_timer(self, name: str) -> float:
        """End a performance timer and return duration"""
        if name not in self.timers:
            return 0.0

        timer = self.timers.pop(name)
        duration = timer.get_duration()
        self._log_performance_timer(name, duration, timer.metadata)
        return duration

    def _log_performance_timer(self, name: str, duration_ms: float, metadata: Dict[str, Any]):
        """Log a performance timer result"""
        self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.PERFORMANCE,
            event_phase=EventPhase.TRAINING_START,
            message=f"Timer '{name}' completed",
            metadata={
                "timer_name": name,
                "duration_ms": duration_ms,
                **metadata
            },
            performance_metrics={"duration_ms": duration_ms}
        )

    def log(self, level: LogLevel, category: LogCategory, event_phase: EventPhase,
            message: str, step: int = 0, epoch: int = 0,
            metadata: Dict[str, Any] = None, error_info: Dict[str, Any] = None,
            performance_metrics: Dict[str, float] = None, **kwargs):
        """Log a structured message"""
        if level.value < self.config.log_level_filter.value:
            return

        # Create log entry
        log_entry = self._create_log_entry(
            level=level,
            category=category,
            event_phase=event_phase,
            message=message,
            step=step,
            epoch=epoch,
            metadata=metadata,
            error_info=error_info,
            performance_metrics=performance_metrics,
            **kwargs
        )

        # Apply filters
        if not self._should_log(log_entry):
            return

        # Store in database
        if self.config.enable_database_logging:
            self.batch_processor.add_log(log_entry)

        # Log to traditional logger
        self._log_to_traditional_logger(log_entry)

    def _create_log_entry(self, level: LogLevel, category: LogCategory, event_phase: EventPhase,
                         message: str, step: int = 0, epoch: int = 0,
                         metadata: Dict[str, Any] = None, error_info: Dict[str, Any] = None,
                         performance_metrics: Dict[str, float] = None,
                         duration_ms: float = None, **kwargs) -> StructuredLogEntry:
        """Create a structured log entry"""
        # Generate correlation ID if needed
        if self.correlation_id is None and self.config.enable_correlation_ids:
            self.set_correlation_id()

        # Merge metadata
        final_metadata = self.custom_fields.copy()
        if metadata:
            final_metadata.update(metadata)
        final_metadata.update(kwargs)

        # Collect system info if needed
        system_info = None
        if category in [LogCategory.SYSTEM, LogCategory.HARDWARE, LogCategory.PERFORMANCE]:
            system_info = self._collect_system_info()

        return StructuredLogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            event_phase=event_phase,
            message=message,
            correlation_id=self.correlation_id,
            run_id=self.run_id,
            step=step,
            epoch=epoch,
            duration_ms=duration_ms,
            metadata=final_metadata,
            error_info=error_info,
            performance_metrics=performance_metrics,
            system_info=system_info
        )

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_usage": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids())
            }
        except ImportError:
            return {}

    def _should_log(self, log_entry: StructuredLogEntry) -> bool:
        """Check if log entry should be logged based on filters"""
        for filter_func in self.filters:
            if not filter_func(log_entry):
                return False
        return True

    def _log_to_traditional_logger(self, log_entry: StructuredLogEntry):
        """Log to traditional logger for compatibility"""
        if not self.config.enable_console_logging:
            return

        # Convert to traditional log format
        log_level = getattr(logging, log_entry.level.value)
        formatted_message = self._format_traditional_message(log_entry)

        self.traditional_logger.log(log_level, formatted_message, extra={"structured_entry": log_entry})

    def _format_traditional_message(self, log_entry: StructuredLogEntry) -> str:
        """Format log entry for traditional logger"""
        parts = [
            f"[{log_entry.category.value}]",
            f"[{log_entry.event_phase.value}]",
            log_entry.message
        ]

        if log_entry.step > 0:
            parts.append(f"(step={log_entry.step})")

        if log_entry.epoch > 0:
            parts.append(f"(epoch={log_entry.epoch})")

        if log_entry.duration_ms:
            parts.append(f"({log_entry.duration_ms:.2f}ms)")

        return " ".join(parts)

    # Convenience methods
    def debug(self, category: LogCategory, event_phase: EventPhase, message: str, **kwargs):
        """Log a debug message"""
        self.log(LogLevel.DEBUG, category, event_phase, message, **kwargs)

    def info(self, category: LogCategory, event_phase: EventPhase, message: str, **kwargs):
        """Log an info message"""
        self.log(LogLevel.INFO, category, event_phase, message, **kwargs)

    def warning(self, category: LogCategory, event_phase: EventPhase, message: str, **kwargs):
        """Log a warning message"""
        self.log(LogLevel.WARNING, category, event_phase, message, **kwargs)

    def error(self, category: LogCategory, event_phase: EventPhase, message: str,
              error: Exception = None, **kwargs):
        """Log an error message"""
        error_info = None
        if error:
            error_info = {
                "type": type(error).__name__,
                "message": str(error),
                "stack_trace": traceback.format_exc()
            }

        self.log(LogLevel.ERROR, category, event_phase, message, error_info=error_info, **kwargs)

    def critical(self, category: LogCategory, event_phase: EventPhase, message: str,
                 error: Exception = None, **kwargs):
        """Log a critical message"""
        error_info = None
        if error:
            error_info = {
                "type": type(error).__name__,
                "message": str(error),
                "stack_trace": traceback.format_exc()
            }

        self.log(LogLevel.CRITICAL, category, event_phase, message, error_info=error_info, **kwargs)

    # Training-specific convenience methods
    def log_training_start(self, config: Dict[str, Any] = None, **kwargs):
        """Log training start"""
        self.info(
            category=LogCategory.TRAINING,
            event_phase=EventPhase.TRAINING_START,
            message="Training started",
            metadata={"config": config or {}},
            **kwargs
        )

    def log_epoch_start(self, epoch: int, **kwargs):
        """Log epoch start"""
        self.info(
            category=LogCategory.TRAINING,
            event_phase=EventPhase.EPOCH_START,
            message=f"Epoch {epoch} started",
            epoch=epoch,
            **kwargs
        )

    def log_epoch_end(self, epoch: int, metrics: Dict[str, float] = None, **kwargs):
        """Log epoch end"""
        self.info(
            category=LogCategory.TRAINING,
            event_phase=EventPhase.EPOCH_END,
            message=f"Epoch {epoch} completed",
            epoch=epoch,
            metadata={"epoch_metrics": metrics or {}},
            **kwargs
        )

    def log_batch_start(self, step: int, epoch: int, batch_size: int = None, **kwargs):
        """Log batch start"""
        self.debug(
            category=LogCategory.TRAINING,
            event_phase=EventPhase.BATCH_START,
            message=f"Batch step {step} started",
            step=step,
            epoch=epoch,
            metadata={"batch_size": batch_size},
            **kwargs
        )

    def log_batch_end(self, step: int, epoch: int, loss: float = None,
                     accuracy: float = None, **kwargs):
        """Log batch end"""
        metadata = {}
        if loss is not None:
            metadata["loss"] = loss
        if accuracy is not None:
            metadata["accuracy"] = accuracy

        self.debug(
            category=LogCategory.TRAINING,
            event_phase=EventPhase.BATCH_END,
            message=f"Batch step {step} completed",
            step=step,
            epoch=epoch,
            metadata=metadata,
            **kwargs
        )

    def log_checkpoint_save(self, checkpoint_path: str, metrics: Dict[str, float] = None, **kwargs):
        """Log checkpoint save"""
        self.info(
            category=LogCategory.CHECKPOINT,
            event_phase=EventPhase.CHECKPOINT_SAVE,
            message=f"Checkpoint saved: {checkpoint_path}",
            metadata={"checkpoint_path": checkpoint_path, "metrics": metrics or {}},
            **kwargs
        )

    def log_validation_start(self, **kwargs):
        """Log validation start"""
        self.info(
            category=LogCategory.VALIDATION,
            event_phase=EventPhase.VALIDATION_START,
            message="Validation started",
            **kwargs
        )

    def log_validation_end(self, metrics: Dict[str, float] = None, **kwargs):
        """Log validation end"""
        self.info(
            category=LogCategory.VALIDATION,
            event_phase=EventPhase.VALIDATION_END,
            message="Validation completed",
            metadata={"validation_metrics": metrics or {}},
            **kwargs
        )

    def log_metric(self, name: str, value: float, category: LogCategory = LogCategory.METRIC, **kwargs):
        """Log a custom metric"""
        self.info(
            category=category,
            event_phase=EventPhase.TRAINING_START,
            message=f"Metric {name}: {value}",
            metadata={"metric_name": name, "metric_value": value},
            performance_metrics={name: value},
            **kwargs
        )

    def log_system_metrics(self, **kwargs):
        """Log system metrics"""
        system_info = self._collect_system_info()
        if system_info:
            self.info(
                category=LogCategory.SYSTEM,
                event_phase=EventPhase.TRAINING_START,
                message="System metrics collected",
                metadata=system_info,
                performance_metrics=system_info,
                **kwargs
            )

    def add_filter(self, filter_func: Callable[[StructuredLogEntry], bool]):
        """Add a log filter function"""
        self.filters.append(filter_func)

    def export_logs(self, output_path: str, format: str = "json", run_id: str = None):
        """Export logs to various formats"""
        logs = self.database.query_logs(run_id=run_id, limit=10000)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(logs, f, indent=2, default=str)

        elif format.lower() == "csv":
            df = pd.DataFrame(logs)
            df.to_csv(output_path, index=False)

        elif format.lower() == "parquet":
            df = pd.DataFrame(logs)
            df.to_parquet(output_path, index=False)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_logs_summary(self, run_id: str = None) -> Dict[str, Any]:
        """Get logs summary"""
        if self.database and run_id:
            return self.database.get_log_summary(run_id)
        return {}

    def close(self):
        """Close the logger and flush remaining logs"""
        if hasattr(self, 'batch_processor'):
            self.batch_processor.stop()

class JSONFormatter(logging.Formatter):
    """JSON formatter for traditional logging"""

    def format(self, record):
        """Format log record as JSON"""
        if hasattr(record, 'structured_entry'):
            log_entry = record.structured_entry
            return json.dumps(log_entry.to_dict(), default=str)
        else:
            # Fallback for non-structured logs
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno
            })

class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for traditional logging"""

    def format(self, record):
        """Format log record in human-readable format"""
        if hasattr(record, 'structured_entry'):
            log_entry = record.structured_entry
            return f"{log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{log_entry.level.value}] {log_entry.category.value}: {log_entry.message}"
        else:
            return super().format(record)

# Global logger instance
_logger_instance = None

def get_structured_logger(config: StructuredLoggerConfig = None) -> StructuredLogger:
    """Get the global structured logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(config)
    return _logger_instance

def set_run_id(run_id: str):
    """Set the run ID for the global logger"""
    logger = get_structured_logger()
    logger.set_run_id(run_id)

# Convenience functions for global logger
def log_training_start(config: Dict[str, Any] = None, **kwargs):
    """Log training start using global logger"""
    logger = get_structured_logger()
    logger.log_training_start(config, **kwargs)

def log_epoch_start(epoch: int, **kwargs):
    """Log epoch start using global logger"""
    logger = get_structured_logger()
    logger.log_epoch_start(epoch, **kwargs)

def log_epoch_end(epoch: int, metrics: Dict[str, float] = None, **kwargs):
    """Log epoch end using global logger"""
    logger = get_structured_logger()
    logger.log_epoch_end(epoch, metrics, **kwargs)

def log_metric(name: str, value: float, **kwargs):
    """Log a metric using global logger"""
    logger = get_structured_logger()
    logger.log_metric(name, value, **kwargs)

def log_error(category: LogCategory, event_phase: EventPhase, message: str, error: Exception = None, **kwargs):
    """Log an error using global logger"""
    logger = get_structured_logger()
    logger.error(category, event_phase, message, error, **kwargs)

if __name__ == "__main__":
    # Test the structured logger
    print("Testing DuckBot Structured Logger")

    # Create logger
    logger = StructuredLogger()

    # Set run ID
    run_id = f"test_run_{uuid.uuid4().hex[:8]}"
    logger.set_run_id(run_id)

    # Log various events
    logger.log_training_start({"model": "test_model", "epochs": 3})

    for epoch in range(3):
        logger.log_epoch_start(epoch)

        # Use timer context manager
        with logger.timer("epoch_timer", {"epoch": epoch}):
            time.sleep(0.1)

            for step in range(5):
                logger.log_batch_start(step, epoch, batch_size=32)

                with logger.timer("batch_timer", {"step": step, "epoch": epoch}):
                    time.sleep(0.01)

                # Log metrics
                logger.log_metric("loss", 2.0 / (epoch + 1))
                logger.log_metric("accuracy", 0.5 + 0.1 * epoch)

                logger.log_batch_end(step, epoch, loss=0.1, accuracy=0.8)

        logger.log_epoch_end(epoch, {"avg_loss": 0.1, "avg_accuracy": 0.8})

    # Log checkpoint
    logger.log_checkpoint_save(f"checkpoints/epoch_2.pt", {"loss": 0.05, "accuracy": 0.9})

    # Log system metrics
    logger.log_system_metrics()

    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.error(LogCategory.ERROR, EventPhase.ERROR, "Test error occurred", e)

    # Export logs
    logger.export_logs("test_logs.json", format="json")

    # Get summary
    summary = logger.get_logs_summary(run_id)
    print(f"\nLogs Summary for {run_id}:")
    print(json.dumps(summary, indent=2, default=str))

    # Close logger
    logger.close()

    print("\nStructured logger test completed!")
#!/usr/bin/env python3
"""
DuckBot AutoTrain Job Manager
Comprehensive job management and monitoring system for AutoTrain-Advanced
Provides real-time monitoring, logging, and job orchestration

Features:
- Real-time job monitoring and status tracking
- Comprehensive logging system
- Job queue management and prioritization
- Resource monitoring and optimization
- Automatic error recovery and retry logic
- Job scheduling and batch processing
- Integration with DuckBot monitoring system
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from autotrain_integration import AutoTrainJob, AutoTrainConfig, AutoTrainManager

class JobStatus(Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    SUBMITTED = "submitted"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class JobMetrics:
    """Job performance metrics"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    gpu_usage: List[float] = field(default_factory=list)
    training_loss: List[float] = field(default_factory=list)
    learning_rate: List[float] = field(default_factory=list)
    epoch_times: List[float] = field(default_factory=list)

    def get_duration(self) -> Optional[timedelta]:
        """Get job duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def get_avg_cpu_usage(self) -> Optional[float]:
        """Get average CPU usage"""
        return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else None

    def get_avg_memory_usage(self) -> Optional[float]:
        """Get average memory usage"""
        return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else None

    def get_avg_gpu_usage(self) -> Optional[float]:
        """Get average GPU usage"""
        return sum(self.gpu_usage) / len(self.gpu_usage) if self.gpu_usage else None

@dataclass
class QueuedJob:
    """Job in queue"""
    job_id: str
    config: AutoTrainConfig
    priority: JobPriority = JobPriority.NORMAL
    submit_time: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AutoTrainJobManager:
    """Advanced job management system for AutoTrain"""

    def __init__(self, db_path: Optional[str] = None, max_concurrent_jobs: int = 2):
        self.db_path = db_path or project_root / "autotrain_jobs.db"
        self.max_concurrent_jobs = max_concurrent_jobs

        # Initialize database
        self._init_database()

        # Job storage
        self.queued_jobs: Dict[str, QueuedJob] = {}
        self.running_jobs: Dict[str, AutoTrainJob] = {}
        self.completed_jobs: Dict[str, AutoTrainJob] = {}

        # Resource monitoring
        self.resource_monitor = ResourceMonitor()

        # Thread pool for concurrent operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # Job processing
        self._running = False
        self._processor_thread = None

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            "job_submitted": [],
            "job_started": [],
            "job_completed": [],
            "job_failed": [],
            "job_cancelled": []
        }

        # Initialize AutoTrain manager
        self.autotrain_manager = AutoTrainManager()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _init_database(self):
        """Initialize SQLite database for job persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    submit_time TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    metrics_json TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    priority INTEGER DEFAULT 2,
                    tags TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs (job_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_dependencies (
                    job_id TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs (job_id),
                    FOREIGN KEY (depends_on) REFERENCES jobs (job_id)
                )
            """)

    def submit_job(self, config: AutoTrainConfig, priority: JobPriority = JobPriority.NORMAL,
                  tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
                  dependencies: Optional[List[str]] = None) -> str:
        """Submit a new job to the queue"""
        job_id = f"{config.project_name}_{int(time.time())}"

        queued_job = QueuedJob(
            job_id=job_id,
            config=config,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
            dependencies=dependencies or []
        )

        self.queued_jobs[job_id] = queued_job

        # Save to database
        self._save_job_to_db(queued_job)

        # Trigger event
        self._trigger_event("job_submitted", job_id)

        self.logger.info(f"Job {job_id} submitted to queue")

        return job_id

    def _save_job_to_db(self, queued_job: QueuedJob):
        """Save job to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs (
                    job_id, project_name, status, config_json, submit_time,
                    retry_count, priority, tags, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                queued_job.job_id,
                queued_job.config.project_name,
                JobStatus.QUEUED.value,
                json.dumps(queued_job.config.to_dict()),
                queued_job.submit_time.isoformat(),
                queued_job.retry_count,
                queued_job.priority.value,
                json.dumps(queued_job.tags),
                json.dumps(queued_job.metadata)
            ))

            # Save dependencies
            conn.execute("DELETE FROM job_dependencies WHERE job_id = ?", (queued_job.job_id,))
            for dep in queued_job.dependencies:
                conn.execute(
                    "INSERT INTO job_dependencies (job_id, depends_on) VALUES (?, ?)",
                    (queued_job.job_id, dep)
                )

    def start_processing(self):
        """Start job processing"""
        if self._running:
            return

        self._running = True
        self._processor_thread = threading.Thread(target=self._process_jobs_loop)
        self._processor_thread.daemon = True
        self._processor_thread.start()

        self.logger.info("Job processing started")

    def stop_processing(self):
        """Stop job processing"""
        self._running = False
        if self._processor_thread:
            self._processor_thread.join(timeout=5)

        self.logger.info("Job processing stopped")

    def _process_jobs_loop(self):
        """Main job processing loop"""
        while self._running:
            try:
                self._check_job_dependencies()
                self._process_next_job()
                self._update_running_jobs()
                self._cleanup_completed_jobs()
            except Exception as e:
                self.logger.error(f"Error in job processing loop: {e}")

            time.sleep(5)  # Check every 5 seconds

    def _check_job_dependencies(self):
        """Check and update jobs based on dependencies"""
        for job_id, queued_job in list(self.queued_jobs.items()):
            if queued_job.dependencies:
                all_deps_completed = all(
                    dep_id in self.completed_jobs and
                    self.completed_jobs[dep_id].status == JobStatus.COMPLETED.value
                    for dep_id in queued_job.dependencies
                )

                if not all_deps_completed:
                    # Check if any dependency failed
                    failed_deps = [
                        dep_id for dep_id in queued_job.dependencies
                        if dep_id in self.completed_jobs and
                        self.completed_jobs[dep_id].status == JobStatus.FAILED.value
                    ]

                    if failed_deps:
                        # Cancel job due to failed dependencies
                        self.cancel_job(job_id, f"Dependencies failed: {failed_deps}")

    def _process_next_job(self):
        """Process next job in queue"""
        if len(self.running_jobs) >= self.max_concurrent_jobs:
            return

        # Find next eligible job
        eligible_jobs = [
            job for job in self.queued_jobs.values()
            if not job.dependencies or all(
                dep_id in self.completed_jobs and
                self.completed_jobs[dep_id].status == JobStatus.COMPLETED.value
                for dep_id in job.dependencies
            )
        ]

        if not eligible_jobs:
            return

        # Sort by priority and submit time
        eligible_jobs.sort(key=lambda j: (j.priority.value, j.submit_time), reverse=True)
        next_job = eligible_jobs[0]

        # Start job
        self._start_job(next_job)

    def _start_job(self, queued_job: QueuedJob):
        """Start a queued job"""
        try:
            # Remove from queue
            del self.queued_jobs[queued_job.job_id]

            # Submit to AutoTrain
            job_id = self.autotrain_manager.submit_training_job(queued_job.config)

            # Get job from AutoTrain manager
            auto_train_job = self.autotrain_manager.get_job_status(job_id)

            if auto_train_job:
                self.running_jobs[job_id] = auto_train_job

                # Update database
                self._update_job_status(job_id, JobStatus.RUNNING)

                # Start monitoring
                self.thread_pool.submit(self._monitor_job, job_id)

                # Trigger event
                self._trigger_event("job_started", job_id)

                self.logger.info(f"Job {job_id} started")

        except Exception as e:
            self.logger.error(f"Failed to start job {queued_job.job_id}: {e}")
            self._handle_job_failure(queued_job.job_id, str(e))

    def _monitor_job(self, job_id: str):
        """Monitor a running job"""
        metrics = JobMetrics()
        metrics.start_time = datetime.now()

        try:
            while True:
                job = self.autotrain_manager.get_job_status(job_id)
                if not job:
                    break

                # Update metrics
                if job.status == JobStatus.RUNNING.value:
                    # Collect resource metrics
                    resource_metrics = self.resource_monitor.get_metrics()
                    metrics.cpu_usage.append(resource_metrics.get("cpu_percent", 0))
                    metrics.memory_usage.append(resource_metrics.get("memory_percent", 0))
                    metrics.gpu_usage.append(resource_metrics.get("gpu_percent", 0))

                    # Collect training metrics
                    if "loss" in job.metrics:
                        metrics.training_loss.append(job.metrics["loss"])
                    if "learning_rate" in job.metrics:
                        metrics.learning_rate.append(job.metrics["learning_rate"])

                # Check if job completed
                if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                    metrics.end_time = datetime.now()

                    # Update job with metrics
                    job.metrics.update({
                        "duration": metrics.get_duration().total_seconds() if metrics.get_duration() else 0,
                        "avg_cpu_usage": metrics.get_avg_cpu_usage(),
                        "avg_memory_usage": metrics.get_avg_memory_usage(),
                        "avg_gpu_usage": metrics.get_avg_gpu_usage(),
                        "final_loss": metrics.training_loss[-1] if metrics.training_loss else None
                    })

                    # Move to completed jobs
                    if job_id in self.running_jobs:
                        del self.running_jobs[job_id]
                    self.completed_jobs[job_id] = job

                    # Update database
                    self._update_job_status(job_id, JobStatus(job.status), metrics)

                    # Trigger event
                    if job.status == JobStatus.COMPLETED.value:
                        self._trigger_event("job_completed", job_id)
                    elif job.status == JobStatus.FAILED.value:
                        self._trigger_event("job_failed", job_id)
                    elif job.status == JobStatus.CANCELLED.value:
                        self._trigger_event("job_cancelled", job_id)

                    break

                time.sleep(10)  # Monitor every 10 seconds

        except Exception as e:
            self.logger.error(f"Error monitoring job {job_id}: {e}")
            self._handle_job_failure(job_id, str(e))

    def _update_job_status(self, job_id: str, status: JobStatus, metrics: Optional[JobMetrics] = None):
        """Update job status in database"""
        with sqlite3.connect(self.db_path) as conn:
            update_fields = ["status = ?"]
            params = [status.value]

            if status == JobStatus.RUNNING:
                update_fields.append("start_time = ?")
                params.append(datetime.now().isoformat())
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_fields.append("end_time = ?")
                params.append(datetime.now().isoformat())

            if metrics:
                update_fields.append("metrics_json = ?")
                params.append(json.dumps({
                    "duration": metrics.get_duration().total_seconds() if metrics.get_duration() else 0,
                    "avg_cpu_usage": metrics.get_avg_cpu_usage(),
                    "avg_memory_usage": metrics.get_avg_memory_usage(),
                    "avg_gpu_usage": metrics.get_avg_gpu_usage(),
                    "training_loss": metrics.training_loss,
                    "learning_rate": metrics.learning_rate
                }))

            conn.execute(
                f"UPDATE jobs SET {', '.join(update_fields)} WHERE job_id = ?",
                params + [job_id]
            )

    def _handle_job_failure(self, job_id: str, error_message: str):
        """Handle job failure with retry logic"""
        queued_job = self.queued_jobs.get(job_id)
        if not queued_job:
            return

        if queued_job.retry_count < queued_job.max_retries:
            # Retry job
            queued_job.retry_count += 1
            self.logger.info(f"Retrying job {job_id} (attempt {queued_job.retry_count})")
            self._update_job_retry_count(job_id, queued_job.retry_count)
        else:
            # Mark as failed
            self._update_job_status(job_id, JobStatus.FAILED)
            self._update_job_error(job_id, error_message)

            if job_id in self.queued_jobs:
                del self.queued_jobs[job_id]

            # Trigger event
            self._trigger_event("job_failed", job_id)

    def _update_job_retry_count(self, job_id: str, retry_count: int):
        """Update job retry count in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET retry_count = ? WHERE job_id = ?",
                        (retry_count, job_id))

    def _update_job_error(self, job_id: str, error_message: str):
        """Update job error message in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET error_message = ? WHERE job_id = ?",
                        (error_message, job_id))

    def _update_running_jobs(self):
        """Update status of running jobs"""
        completed_jobs = []
        for job_id, job in list(self.running_jobs.items()):
            auto_train_job = self.autotrain_manager.get_job_status(job_id)
            if auto_train_job:
                if auto_train_job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                    completed_jobs.append(job_id)

        # Move completed jobs
        for job_id in completed_jobs:
            if job_id in self.running_jobs:
                job = self.running_jobs[job_id]
                del self.running_jobs[job_id]
                self.completed_jobs[job_id] = job

    def _cleanup_completed_jobs(self):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(days=7)

        for job_id, job in list(self.completed_jobs.items()):
            if job.completed_at and job.completed_at < cutoff_time:
                del self.completed_jobs[job_id]
                self.logger.info(f"Cleaned up completed job {job_id}")

    def cancel_job(self, job_id: str, reason: str = "") -> bool:
        """Cancel a job"""
        success = False

        # Cancel in queue
        if job_id in self.queued_jobs:
            del self.queued_jobs[job_id]
            success = True

        # Cancel running job
        elif job_id in self.running_jobs:
            success = self.autotrain_manager.cancel_job(job_id)
            if success:
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
                self.completed_jobs[job_id] = self.autotrain_manager.get_job_status(job_id)

        if success:
            self._update_job_status(job_id, JobStatus.CANCELLED)
            if reason:
                self._update_job_error(job_id, reason)
            self._trigger_event("job_cancelled", job_id)
            self.logger.info(f"Job {job_id} cancelled: {reason}")

        return success

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed job status"""
        # Check queue
        if job_id in self.queued_jobs:
            job = self.queued_jobs[job_id]
            return {
                "job_id": job_id,
                "status": JobStatus.QUEUED.value,
                "priority": job.priority.value,
                "submit_time": job.submit_time,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "dependencies": job.dependencies,
                "tags": job.tags,
                "metadata": job.metadata
            }

        # Check running jobs
        if job_id in self.running_jobs:
            job = self.running_jobs[job_id]
            auto_train_job = self.autotrain_manager.get_job_status(job_id)
            if auto_train_job:
                return {
                    "job_id": job_id,
                    "status": auto_train_job.status,
                    "config": auto_train_job.config.to_dict(),
                    "created_at": auto_train_job.created_at,
                    "started_at": auto_train_job.started_at,
                    "metrics": auto_train_job.metrics,
                    "logs": auto_train_job.logs[-50:]  # Last 50 log lines
                }

        # Check completed jobs
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            return {
                "job_id": job_id,
                "status": job.status,
                "config": job.config.to_dict(),
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "metrics": job.metrics,
                "output_path": job.output_path,
                "error_message": job.error_message
            }

        # Check database
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

            if row:
                return {
                    "job_id": row["job_id"],
                    "project_name": row["project_name"],
                    "status": row["status"],
                    "config": json.loads(row["config_json"]),
                    "submit_time": row["submit_time"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "metrics": json.loads(row["metrics_json"]) if row["metrics_json"] else None,
                    "error_message": row["error_message"],
                    "retry_count": row["retry_count"],
                    "priority": row["priority"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }

        return None

    def list_jobs(self, status: Optional[JobStatus] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List jobs with optional filtering"""
        jobs = []

        # Get jobs from database
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM jobs"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status.value)

            if tags:
                if status:
                    query += " AND"
                else:
                    query += " WHERE"
                query += f" tags LIKE '%{json.dumps(tags)}%'"

            query += " ORDER BY submit_time DESC"

            rows = conn.execute(query, params).fetchall()
            for row in rows:
                jobs.append({
                    "job_id": row["job_id"],
                    "project_name": row["project_name"],
                    "status": row["status"],
                    "submit_time": row["submit_time"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "retry_count": row["retry_count"],
                    "priority": row["priority"],
                    "tags": json.loads(row["tags"]) if row["tags"] else []
                })

        return jobs

    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        return {
            "queued": len(self.queued_jobs),
            "running": len(self.running_jobs),
            "completed": len(self.completed_jobs),
            "max_concurrent": self.max_concurrent_jobs,
            "processing": self._running
        }

    def get_job_logs(self, job_id: str) -> List[str]:
        """Get job logs"""
        # Try AutoTrain manager first
        auto_train_job = self.autotrain_manager.get_job_status(job_id)
        if auto_train_job:
            return auto_train_job.logs

        # Check database
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT message, timestamp FROM job_logs WHERE job_id = ? ORDER BY timestamp",
                (job_id,)
            ).fetchall()

            return [f"{row['timestamp']}: {row['message']}" for row in rows]

        return []

    def add_event_callback(self, event: str, callback: Callable[[str], None]):
        """Add event callback"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)

    def _trigger_event(self, event: str, job_id: str):
        """Trigger event callbacks"""
        if event in self.event_callbacks:
            for callback in self.event_callbacks[event]:
                try:
                    callback(job_id)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event}: {e}")

    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Basic counts
            total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            completed_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = ?", (JobStatus.COMPLETED.value,)).fetchone()[0]
            failed_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = ?", (JobStatus.FAILED.value,)).fetchone()[0]

            # Average duration
            duration_result = conn.execute("""
                SELECT AVG(julianday(end_time) - julianday(start_time)) * 24 * 60 * 60
                FROM jobs WHERE status = ? AND start_time IS NOT NULL AND end_time IS NOT NULL
            """, (JobStatus.COMPLETED.value,)).fetchone()

            avg_duration = duration_result[0] if duration_result[0] else 0

            # Success rate
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": success_rate,
                "average_duration_seconds": avg_duration,
                "queue_status": self.get_queue_status()
            }

class ResourceMonitor:
    """System resource monitoring"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current resource metrics"""
        metrics = {"cpu_percent": 0, "memory_percent": 0, "gpu_percent": 0}

        try:
            import psutil
            metrics["cpu_percent"] = psutil.cpu_percent()
            metrics["memory_percent"] = psutil.virtual_memory().percent
        except ImportError:
            pass

        try:
            import torch
            if torch.cuda.is_available():
                metrics["gpu_percent"] = torch.cuda.utilization()
                metrics["gpu_memory_used"] = torch.cuda.memory_allocated() / 1024**3  # GB
                metrics["gpu_memory_total"] = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
        except ImportError:
            pass

        return metrics

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    from autotrain_integration import AutoTrainConfig, AutoTrainProjectType

    # Create job manager
    job_manager = AutoTrainJobManager()

    # Start processing
    job_manager.start_processing()

    # Create sample configuration
    config = AutoTrainConfig(
        project_name="example_project",
        project_type=AutoTrainProjectType.TEXT_CLASSIFICATION,
        data_path="./example_data",
        model_name="distilbert-base-uncased"
    )

    # Submit job
    job_id = job_manager.submit_job(config, priority=JobPriority.HIGH)
    print(f"Submitted job: {job_id}")

    # Monitor job
    try:
        while True:
            status = job_manager.get_job_status(job_id)
            if status:
                print(f"Job status: {status['status']}")
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping job manager...")
        job_manager.stop_processing()
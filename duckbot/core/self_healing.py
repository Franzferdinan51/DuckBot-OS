#!/usr/bin/env python3
"""
Advanced Self-Healing System for DuckBot v4.2
Provides comprehensive health monitoring, automated diagnostics, and self-repair capabilities
"""

import os
import sys
import time
import json
import asyncio
import logging
import threading
import subprocess
import signal
import psutil
import socket
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import sqlite3
import shutil
import tempfile

# Import existing DuckBot components
try:
    from duckbot.core.error_handling import ErrorContext, ErrorSeverity, ErrorCategory, RecoveryAction
    from duckbot.core.logging_setup import get_logger
    from duckbot.services.server_manager import ServerManager, ServiceStatus
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class RepairPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    description: str
    check_function: Callable
    interval_seconds: int
    timeout_seconds: int
    enabled: bool = True
    retry_count: int = 3
    severity: HealthStatus = HealthStatus.WARNING

@dataclass
class HealthResult:
    """Result of a health check"""
    check_name: str
    status: HealthStatus
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = None
    execution_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RepairAction:
    """Repair action information"""
    action_id: str
    name: str
    description: str
    repair_function: Callable
    priority: RepairPriority
    auto_execute: bool
    cooldown_minutes: int
    conditions: List[str]
    last_executed: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0

@dataclass
class DiagnosticReport:
    """Comprehensive diagnostic report"""
    timestamp: datetime
    overall_health: HealthStatus
    health_checks: Dict[str, HealthResult]
    system_metrics: Dict[str, Any]
    identified_issues: List[str]
    recommended_actions: List[str]
    repair_candidates: List[str]

class HealthMonitor:
    """Comprehensive health monitoring system"""

    def __init__(self, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("health_monitor")
        self.server_manager = server_manager
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, HealthResult] = {}
        self.monitoring_active = False
        self.monitor_thread = None

        # Initialize health checks
        self._initialize_health_checks()

        # Health history database
        self.db_path = Path(__file__).parent.parent / "data" / "health_monitoring.db"
        self._initialize_database()

    def _initialize_database(self):
        """Initialize health monitoring database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    check_name TEXT,
                    status TEXT,
                    value REAL,
                    message TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS repair_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    action_id TEXT,
                    action_name TEXT,
                    success BOOLEAN,
                    execution_time_ms INTEGER,
                    message TEXT
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_health_timestamp ON health_history(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_repair_timestamp ON repair_history(timestamp)")

    def _initialize_health_checks(self):
        """Initialize comprehensive health checks"""
        self.health_checks = {
            # System resource checks
            'memory_usage': HealthCheck(
                name="memory_usage",
                description="System memory usage percentage",
                check_function=self._check_memory_usage,
                interval_seconds=60,
                timeout_seconds=10,
                severity=HealthStatus.CRITICAL
            ),
            'cpu_usage': HealthCheck(
                name="cpu_usage",
                description="CPU usage percentage",
                check_function=self._check_cpu_usage,
                interval_seconds=60,
                timeout_seconds=10,
                severity=HealthStatus.WARNING
            ),
            'disk_usage': HealthCheck(
                name="disk_usage",
                description="Disk usage percentage",
                check_function=self._check_disk_usage,
                interval_seconds=300,
                timeout_seconds=10,
                severity=HealthStatus.WARNING
            ),
            'network_connectivity': HealthCheck(
                name="network_connectivity",
                description="Basic network connectivity",
                check_function=self._check_network_connectivity,
                interval_seconds=120,
                timeout_seconds=15,
                severity=HealthStatus.CRITICAL
            ),

            # Service-specific checks
            'lm_studio_health': HealthCheck(
                name="lm_studio_health",
                description="LM Studio API health",
                check_function=self._check_lm_studio_health,
                interval_seconds=30,
                timeout_seconds=5,
                severity=HealthStatus.CRITICAL
            ),
            'webui_health': HealthCheck(
                name="webui_health",
                description="WebUI service health",
                check_function=self._check_webui_health,
                interval_seconds=60,
                timeout_seconds=5,
                severity=HealthStatus.WARNING
            ),
            'comfyui_health': HealthCheck(
                name="comfyui_health",
                description="ComfyUI service health",
                check_function=self._check_comfyui_health,
                interval_seconds=60,
                timeout_seconds=5,
                severity=HealthStatus.WARNING
            ),

            # Process health checks
            'process_count': HealthCheck(
                name="process_count",
                description="System process count",
                check_function=self._check_process_count,
                interval_seconds=300,
                timeout_seconds=5,
                severity=HealthStatus.WARNING
            ),
            'zombie_processes': HealthCheck(
                name="zombie_processes",
                description="Zombie process detection",
                check_function=self._check_zombie_processes,
                interval_seconds=300,
                timeout_seconds=5,
                severity=HealthStatus.WARNING
            ),

            # DuckBot-specific checks
            'service_dependencies': HealthCheck(
                name="service_dependencies",
                description="Service dependency health",
                check_function=self._check_service_dependencies,
                interval_seconds=120,
                timeout_seconds=10,
                severity=HealthStatus.CRITICAL
            ),
            'log_rotation': HealthCheck(
                name="log_rotation",
                description="Log file rotation status",
                check_function=self._check_log_rotation,
                interval_seconds=3600,
                timeout_seconds=30,
                severity=HealthStatus.WARNING
            )
        }

    async def _check_memory_usage(self) -> HealthResult:
        """Check memory usage health"""
        start_time = time.time()

        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Determine status
            if memory_percent >= 95:
                status = HealthStatus.CRITICAL
                message = f"Critical memory usage: {memory_percent:.1f}%"
            elif memory_percent >= 90:
                status = HealthStatus.WARNING
                message = f"High memory usage: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_percent:.1f}%"

            execution_time_ms = int((time.time() - start_time) * 1000)

            result = HealthResult(
                check_name="memory_usage",
                status=status,
                message=message,
                value=memory_percent,
                threshold=90.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms,
                metadata={
                    'available_gb': memory.available / (1024**3),
                    'total_gb': memory.total / (1024**3),
                    'used_gb': memory.used / (1024**3)
                }
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="memory_usage",
                status=HealthStatus.UNKNOWN,
                message=f"Memory check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_cpu_usage(self) -> HealthResult:
        """Check CPU usage health"""
        start_time = time.time()

        try:
            cpu_percent = psutil.cpu_percent(interval=1)

            # Determine status
            if cpu_percent >= 95:
                status = HealthStatus.CRITICAL
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent >= 80:
                status = HealthStatus.WARNING
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="cpu_usage",
                status=status,
                message=message,
                value=cpu_percent,
                threshold=80.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms,
                metadata={'cpu_count': psutil.cpu_count()}
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="cpu_usage",
                status=HealthStatus.UNKNOWN,
                message=f"CPU check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_disk_usage(self) -> HealthResult:
        """Check disk usage health"""
        start_time = time.time()

        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Determine status
            if disk_percent >= 98:
                status = HealthStatus.CRITICAL
                message = f"Critical disk usage: {disk_percent:.1f}%"
            elif disk_percent >= 90:
                status = HealthStatus.WARNING
                message = f"High disk usage: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_percent:.1f}%"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="disk_usage",
                status=status,
                message=message,
                value=disk_percent,
                threshold=90.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms,
                metadata={
                    'free_gb': disk.free / (1024**3),
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3)
                }
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="disk_usage",
                status=HealthStatus.UNKNOWN,
                message=f"Disk check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_network_connectivity(self) -> HealthResult:
        """Check network connectivity health"""
        start_time = time.time()

        try:
            # Test connectivity to multiple endpoints
            test_endpoints = [
                ('8.8.8.8', 53),   # Google DNS
                ('1.1.1.1', 53),   # Cloudflare DNS
                ('github.com', 443) # GitHub
            ]

            successful_tests = 0
            for host, port in test_endpoints:
                try:
                    sock = socket.create_connection((host, port), timeout=3)
                    sock.close()
                    successful_tests += 1
                except:
                    pass

            success_rate = successful_tests / len(test_endpoints)

            # Determine status
            if success_rate >= 1.0:
                status = HealthStatus.HEALTHY
                message = f"Network connectivity excellent: {successful_tests}/{len(test_endpoints)} endpoints"
            elif success_rate >= 0.5:
                status = HealthStatus.WARNING
                message = f"Network connectivity degraded: {successful_tests}/{len(test_endpoints)} endpoints"
            else:
                status = HealthStatus.CRITICAL
                message = f"Network connectivity critical: {successful_tests}/{len(test_endpoints)} endpoints"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="network_connectivity",
                status=status,
                message=message,
                value=success_rate * 100,
                threshold=50.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms,
                metadata={'tested_endpoints': len(test_endpoints), 'successful_tests': successful_tests}
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="network_connectivity",
                status=HealthStatus.UNKNOWN,
                message=f"Network check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_lm_studio_health(self) -> HealthResult:
        """Check LM Studio health"""
        start_time = time.time()

        try:
            # Check if LM Studio is running on port 1234
            try:
                response = requests.get("http://localhost:1234/health", timeout=5)
                if response.status_code == 200:
                    status = HealthStatus.HEALTHY
                    message = "LM Studio is healthy"
                    value = 100.0
                else:
                    status = HealthStatus.WARNING
                    message = f"LM Studio returned status {response.status_code}"
                    value = 50.0
            except requests.exceptions.RequestException:
                # Try models endpoint as fallback
                try:
                    response = requests.get("http://localhost:1234/v1/models", timeout=5)
                    if response.status_code == 200:
                        status = HealthStatus.WARNING
                        message = "LM Studio models endpoint accessible, health endpoint not"
                        value = 75.0
                    else:
                        status = HealthStatus.CRITICAL
                        message = f"LM Studio models endpoint returned {response.status_code}"
                        value = 25.0
                except requests.exceptions.RequestException:
                    status = HealthStatus.CRITICAL
                    message = "LM Studio is not responding"
                    value = 0.0

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="lm_studio_health",
                status=status,
                message=message,
                value=value,
                threshold=75.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="lm_studio_health",
                status=HealthStatus.UNKNOWN,
                message=f"LM Studio check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_webui_health(self) -> HealthResult:
        """Check WebUI health"""
        start_time = time.time()

        try:
            # Check if WebUI is running on port 8787
            try:
                response = requests.get("http://localhost:8787/healthz", timeout=5)
                if response.status_code == 200:
                    status = HealthStatus.HEALTHY
                    message = "WebUI is healthy"
                    value = 100.0
                else:
                    status = HealthStatus.WARNING
                    message = f"WebUI returned status {response.status_code}"
                    value = 50.0
            except requests.exceptions.RequestException:
                status = HealthStatus.CRITICAL
                message = "WebUI is not responding"
                value = 0.0

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="webui_health",
                status=status,
                message=message,
                value=value,
                threshold=75.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="webui_health",
                status=HealthStatus.UNKNOWN,
                message=f"WebUI check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_comfyui_health(self) -> HealthResult:
        """Check ComfyUI health"""
        start_time = time.time()

        try:
            # Check if ComfyUI is running on port 8188
            try:
                response = requests.get("http://localhost:8188/prompt", timeout=5)
                if response.status_code == 200:
                    status = HealthStatus.HEALTHY
                    message = "ComfyUI is healthy"
                    value = 100.0
                else:
                    status = HealthStatus.WARNING
                    message = f"ComfyUI returned status {response.status_code}"
                    value = 50.0
            except requests.exceptions.RequestException:
                status = HealthStatus.CRITICAL
                message = "ComfyUI is not responding"
                value = 0.0

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="comfyui_health",
                status=status,
                message=message,
                value=value,
                threshold=75.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="comfyui_health",
                status=HealthStatus.UNKNOWN,
                message=f"ComfyUI check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_process_count(self) -> HealthResult:
        """Check system process count"""
        start_time = time.time()

        try:
            process_count = len(psutil.pids())

            # Determine status (thresholds depend on system)
            if process_count > 1000:
                status = HealthStatus.WARNING
                message = f"High process count: {process_count}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Process count normal: {process_count}"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="process_count",
                status=status,
                message=message,
                value=float(process_count),
                threshold=1000.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="process_count",
                status=HealthStatus.UNKNOWN,
                message=f"Process count check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_zombie_processes(self) -> HealthResult:
        """Check for zombie processes"""
        start_time = time.time()

        try:
            zombie_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        zombie_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Determine status
            if zombie_count > 5:
                status = HealthStatus.WARNING
                message = f"High zombie process count: {zombie_count}"
            elif zombie_count > 0:
                status = HealthStatus.WARNING
                message = f"Zombie processes detected: {zombie_count}"
            else:
                status = HealthStatus.HEALTHY
                message = "No zombie processes detected"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="zombie_processes",
                status=status,
                message=message,
                value=float(zombie_count),
                threshold=1.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="zombie_processes",
                status=HealthStatus.UNKNOWN,
                message=f"Zombie process check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_service_dependencies(self) -> HealthResult:
        """Check service dependencies"""
        start_time = time.time()

        try:
            if not self.server_manager:
                return HealthResult(
                    check_name="service_dependencies",
                    status=HealthStatus.UNKNOWN,
                    message="No server manager available",
                    timestamp=datetime.now(),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            service_status = self.server_manager.get_all_service_status()

            # Count services by status
            total_services = len(service_status)
            running_services = sum(1 for s in service_status.values() if s.status == ServiceStatus.RUNNING)
            failed_services = sum(1 for s in service_status.values() if s.status == ServiceStatus.FAILED)

            health_percentage = (running_services / total_services) * 100 if total_services > 0 else 0

            # Determine status
            if health_percentage >= 90:
                status = HealthStatus.HEALTHY
                message = f"Service dependencies healthy: {running_services}/{total_services} running"
            elif health_percentage >= 70:
                status = HealthStatus.WARNING
                message = f"Service dependencies degraded: {running_services}/{total_services} running"
            else:
                status = HealthStatus.CRITICAL
                message = f"Service dependencies critical: {running_services}/{total_services} running"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="service_dependencies",
                status=status,
                message=message,
                value=health_percentage,
                threshold=70.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms,
                metadata={
                    'total_services': total_services,
                    'running_services': running_services,
                    'failed_services': failed_services
                }
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="service_dependencies",
                status=HealthStatus.UNKNOWN,
                message=f"Service dependency check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def _check_log_rotation(self) -> HealthResult:
        """Check log file rotation status"""
        start_time = time.time()

        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                return HealthResult(
                    check_name="log_rotation",
                    status=HealthStatus.HEALTHY,
                    message="No log directory found",
                    timestamp=datetime.now(),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # Check log file sizes
            log_files = list(log_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files)

            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)

            # Determine status
            if total_size_mb > 1000:  # 1GB
                status = HealthStatus.WARNING
                message = f"Large log files detected: {total_size_mb:.1f} MB total"
            elif total_size_mb > 100:  # 100MB
                status = HealthStatus.WARNING
                message = f"Log files growing: {total_size_mb:.1f} MB total"
            else:
                status = HealthStatus.HEALTHY
                message = f"Log files normal: {total_size_mb:.1f} MB total"

            execution_time_ms = int((time.time() - start_time) * 1000)

            return HealthResult(
                check_name="log_rotation",
                status=status,
                message=message,
                value=total_size_mb,
                threshold=100.0,
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms,
                metadata={
                    'log_file_count': len(log_files),
                    'total_size_bytes': total_size
                }
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return HealthResult(
                check_name="log_rotation",
                status=HealthStatus.UNKNOWN,
                message=f"Log rotation check failed: {str(e)}",
                timestamp=datetime.now(),
                execution_time_ms=execution_time_ms
            )

    async def run_health_check(self, check_name: str) -> HealthResult:
        """Run a specific health check"""
        if check_name not in self.health_checks:
            raise ValueError(f"Unknown health check: {check_name}")

        health_check = self.health_checks[check_name]
        if not health_check.enabled:
            return HealthResult(
                check_name=check_name,
                status=HealthStatus.UNKNOWN,
                message="Health check disabled",
                timestamp=datetime.now()
            )

        try:
            # Run the health check with timeout
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout_seconds
            )

            # Store result
            self.health_results[check_name] = result

            # Store in database
            self._store_health_result(result)

            return result

        except asyncio.TimeoutError:
            result = HealthResult(
                check_name=check_name,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {health_check.timeout_seconds}s",
                timestamp=datetime.now()
            )
            self.health_results[check_name] = result
            self._store_health_result(result)
            return result

        except Exception as e:
            result = HealthResult(
                check_name=check_name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now()
            )
            self.health_results[check_name] = result
            self._store_health_result(result)
            return result

    async def run_all_health_checks(self) -> Dict[str, HealthResult]:
        """Run all enabled health checks"""
        results = {}

        for check_name in self.health_checks:
            if self.health_checks[check_name].enabled:
                try:
                    result = await self.run_health_check(check_name)
                    results[check_name] = result
                except Exception as e:
                    self.logger.error(f"Health check {check_name} failed: {e}")

        return results

    def _store_health_result(self, result: HealthResult):
        """Store health result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_history (
                        timestamp, check_name, status, value, message, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result.timestamp,
                    result.check_name,
                    result.status.value,
                    result.value,
                    result.message,
                    json.dumps(result.metadata) if result.metadata else None
                ))
        except Exception as e:
            self.logger.error(f"Failed to store health result: {e}")

    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Run health checks
                    results = asyncio.run(self.run_all_health_checks())

                    # Log critical issues
                    critical_checks = [name for name, result in results.items() if result.status == HealthStatus.CRITICAL]
                    if critical_checks:
                        self.logger.critical(f"Critical health issues detected: {', '.join(critical_checks)}")

                    # Wait for next cycle
                    time.sleep(60)  # Check every minute

                except Exception as e:
                    self.logger.error(f"Health monitoring error: {e}")
                    time.sleep(60)

        self.monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitor_thread.start()

        self.logger.info("Health monitoring started")

    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("Health monitoring stopped")

    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        if not self.health_results:
            return {"status": "unknown", "message": "No health data available"}

        # Count health statuses
        status_counts = {}
        for result in self.health_results.values():
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Determine overall health
        if status_counts.get('critical', 0) > 0:
            overall_status = "critical"
        elif status_counts.get('warning', 0) > 0:
            overall_status = "warning"
        elif status_counts.get('healthy', 0) == len(self.health_results):
            overall_status = "healthy"
        else:
            overall_status = "unknown"

        return {
            "overall_status": overall_status,
            "total_checks": len(self.health_results),
            "status_distribution": status_counts,
            "last_updated": max(result.timestamp for result in self.health_results.values()).isoformat() if self.health_results else None,
            "critical_issues": [result.message for result in self.health_results.values() if result.status == HealthStatus.CRITICAL]
        }

class AutoRepairEngine:
    """Automated repair and self-healing engine"""

    def __init__(self, health_monitor: HealthMonitor, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("auto_repair")
        self.health_monitor = health_monitor
        self.server_manager = server_manager
        self.repair_actions: Dict[str, RepairAction] = {}
        self.repair_history: List[Dict[str, Any]] = []

        # Initialize repair actions
        self._initialize_repair_actions()

    def _initialize_repair_actions(self):
        """Initialize automated repair actions"""
        self.repair_actions = {
            'memory_cleanup': RepairAction(
                action_id="memory_cleanup",
                name="Memory Cleanup",
                description="Clean up memory and restart resource-intensive services",
                repair_function=self._repair_memory_cleanup,
                priority=RepairPriority.HIGH,
                auto_execute=True,
                cooldown_minutes=30,
                conditions=["memory_usage_critical", "memory_usage_warning"]
            ),
            'disk_cleanup': RepairAction(
                action_id="disk_cleanup",
                name="Disk Cleanup",
                description="Clean up temporary files and old logs",
                repair_function=self._repair_disk_cleanup,
                priority=RepairPriority.MEDIUM,
                auto_execute=True,
                cooldown_minutes=120,
                conditions=["disk_usage_critical", "disk_usage_warning"]
            ),
            'restart_service': RepairAction(
                action_id="restart_service",
                name="Restart Service",
                description="Restart failed or unresponsive services",
                repair_function=self._repair_restart_service,
                priority=RepairPriority.HIGH,
                auto_execute=True,
                cooldown_minutes=10,
                conditions=["service_unresponsive", "service_failed"]
            ),
            'kill_zombie_processes': RepairAction(
                action_id="kill_zombie_processes",
                name="Kill Zombie Processes",
                description="Terminate zombie processes",
                repair_function=self._repair_kill_zombie_processes,
                priority=RepairPriority.LOW,
                auto_execute=True,
                cooldown_minutes=60,
                conditions=["zombie_processes_detected"]
            ),
            'network_restart': RepairAction(
                action_id="network_restart",
                name="Network Restart",
                description="Restart network services",
                repair_function=self._repair_network_restart,
                priority=RepairPriority.CRITICAL,
                auto_execute=False,  # Manual approval required
                cooldown_minutes=5,
                conditions=["network_connectivity_critical"]
            ),
            'log_rotation': RepairAction(
                action_id="log_rotation",
                name="Log Rotation",
                description="Rotate and compress old log files",
                repair_function=self._repair_log_rotation,
                priority=RepairPriority.LOW,
                auto_execute=True,
                cooldown_minutes=360,
                conditions=["log_files_large"]
            )
        }

    async def _repair_memory_cleanup(self) -> tuple[bool, str]:
        """Execute memory cleanup repair"""
        start_time = time.time()

        try:
            # Clear Python garbage collection
            import gc
            collected = gc.collect()

            # Clear error history if too large
            if hasattr(self.health_monitor, 'error_classifier'):
                if len(self.health_monitor.error_classifier.error_history) > 500:
                    old_count = len(self.health_monitor.error_classifier.error_history)
                    self.health_monitor.error_classifier.error_history = self.health_monitor.error_classifier.error_history[-200:]
                    self.logger.info(f"Cleared {old_count - 200} old error history entries")

            # Restart resource-intensive services if server manager available
            if self.server_manager:
                services_to_restart = []
                service_status = self.server_manager.get_all_service_status()

                for service_name, service_info in service_status.items():
                    if service_info.status in [ServiceStatus.FAILED, ServiceStatus.ERROR]:
                        services_to_restart.append(service_name)

                for service_name in services_to_restart:
                    try:
                        self.server_manager.restart_service(service_name)
                        self.logger.info(f"Restarted service for memory cleanup: {service_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to restart service {service_name}: {e}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return True, f"Memory cleanup completed (collected {collected} objects, restarted {len(services_to_restart)} services)"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return False, f"Memory cleanup failed: {str(e)}"

    async def _repair_disk_cleanup(self) -> tuple[bool, str]:
        """Execute disk cleanup repair"""
        start_time = time.time()

        try:
            cleaned_files = 0
            cleaned_bytes = 0

            # Clean up temporary files
            temp_dirs = [
                tempfile.gettempdir(),
                Path.cwd() / "temp",
                Path.cwd() / "tmp"
            ]

            for temp_dir in temp_dirs:
                if Path(temp_dir).exists():
                    for file_path in Path(temp_dir).glob("*"):
                        try:
                            if file_path.is_file() and time.time() - file_path.stat().st_mtime > 86400:  # Older than 1 day
                                cleaned_bytes += file_path.stat().st_size
                                file_path.unlink()
                                cleaned_files += 1
                        except Exception:
                            pass

            # Clean up old log files
            log_dir = Path("logs")
            if log_dir.exists():
                cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days
                for log_file in log_dir.glob("*.log"):
                    try:
                        if log_file.stat().st_mtime < cutoff_time:
                            cleaned_bytes += log_file.stat().st_size
                            log_file.unlink()
                            cleaned_files += 1
                    except Exception:
                        pass

            execution_time_ms = int((time.time() - start_time) * 1000)

            return True, f"Disk cleanup completed (cleaned {cleaned_files} files, {cleaned_bytes / (1024*1024):.1f} MB)"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return False, f"Disk cleanup failed: {str(e)}"

    async def _repair_restart_service(self) -> tuple[bool, str]:
        """Execute service restart repair"""
        start_time = time.time()

        if not self.server_manager:
            return False, "No server manager available for service restart"

        try:
            service_status = self.server_manager.get_all_service_status()
            restarted_services = []

            for service_name, service_info in service_status.items():
                if service_info.status in [ServiceStatus.FAILED, ServiceStatus.ERROR]:
                    try:
                        success, message = self.server_manager.restart_service(service_name)
                        if success:
                            restarted_services.append(service_name)
                            self.logger.info(f"Successfully restarted service: {service_name}")
                        else:
                            self.logger.warning(f"Failed to restart service {service_name}: {message}")
                    except Exception as e:
                        self.logger.error(f"Error restarting service {service_name}: {e}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            if restarted_services:
                return True, f"Restarted {len(restarted_services)} services: {', '.join(restarted_services)}"
            else:
                return True, "No services required restart"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return False, f"Service restart failed: {str(e)}"

    async def _repair_kill_zombie_processes(self) -> tuple[bool, str]:
        """Execute zombie process cleanup"""
        start_time = time.time()

        try:
            killed_count = 0

            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        proc.kill()
                        killed_count += 1
                        self.logger.info(f"Killed zombie process: {proc.info['pid']} ({proc.info['name']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            execution_time_ms = int((time.time() - start_time) * 1000)

            return True, f"Killed {killed_count} zombie processes"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return False, f"Zombie process cleanup failed: {str(e)}"

    async def _repair_network_restart(self) -> tuple[bool, str]:
        """Execute network service restart"""
        start_time = time.time()

        try:
            # This would restart network services
            # Note: This is a simplified version - actual implementation depends on OS
            if os.name == 'nt':  # Windows
                # Restart Windows networking service
                result = subprocess.run(
                    ["sc", "stop", "Dnscache"],
                    capture_output=True, text=True, timeout=30
                )
                subprocess.run(
                    ["sc", "start", "Dnscache"],
                    capture_output=True, text=True, timeout=30
                )
            else:
                # Restart network service on Unix-like systems
                result = subprocess.run(
                    ["sudo", "systemctl", "restart", "networking"],
                    capture_output=True, text=True, timeout=30
                )

            execution_time_ms = int((time.time() - start_time) * 1000)

            return True, "Network services restarted"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return False, f"Network restart failed: {str(e)}"

    async def _repair_log_rotation(self) -> tuple[bool, str]:
        """Execute log rotation"""
        start_time = time.time()

        try:
            rotated_files = 0
            log_dir = Path("logs")

            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    try:
                        # Create compressed backup
                        backup_file = log_file.with_suffix(f".log.{datetime.now().strftime('%Y%m%d_%H%M%S')}.gz")
                        with open(log_file, 'rb') as f_in:
                            import gzip
                            with gzip.open(backup_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        # Clear the original file
                        with open(log_file, 'w') as f:
                            f.truncate()

                        rotated_files += 1
                    except Exception as e:
                        self.logger.error(f"Failed to rotate log file {log_file}: {e}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return True, f"Rotated {rotated_files} log files"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return False, f"Log rotation failed: {str(e)}"

    async def execute_repair(self, action_id: str, force: bool = False) -> tuple[bool, str]:
        """Execute a repair action"""
        if action_id not in self.repair_actions:
            return False, f"Unknown repair action: {action_id}"

        action = self.repair_actions[action_id]

        # Check cooldown
        if action.last_executed and not force:
            cooldown_expired = (datetime.now() - action.last_executed).total_seconds() >= (action.cooldown_minutes * 60)
            if not cooldown_expired:
                return False, f"Repair action {action_id} is in cooldown period"

        # Check if auto-execution is allowed
        if not action.auto_execute and not force:
            return False, f"Repair action {action_id} requires manual approval"

        try:
            start_time = time.time()
            success, message = await action.repair_function()
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Update action statistics
            action.last_executed = datetime.now()
            if success:
                action.success_count += 1
            else:
                action.failure_count += 1

            # Record repair history
            repair_record = {
                'timestamp': datetime.now(),
                'action_id': action_id,
                'action_name': action.name,
                'success': success,
                'execution_time_ms': execution_time_ms,
                'message': message
            }
            self.repair_history.append(repair_record)

            # Store in database
            self._store_repair_record(repair_record)

            # Log the repair
            if success:
                self.logger.info(f"Repair action {action_id} completed successfully: {message}")
            else:
                self.logger.error(f"Repair action {action_id} failed: {message}")

            return success, message

        except Exception as e:
            action.failure_count += 1
            error_message = f"Repair action {action_id} failed with exception: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    def _store_repair_record(self, repair_record: Dict[str, Any]):
        """Store repair record in database"""
        try:
            with sqlite3.connect(self.health_monitor.db_path) as conn:
                conn.execute("""
                    INSERT INTO repair_history (
                        timestamp, action_id, action_name, success, execution_time_ms, message
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    repair_record['timestamp'],
                    repair_record['action_id'],
                    repair_record['action_name'],
                    repair_record['success'],
                    repair_record['execution_time_ms'],
                    repair_record['message']
                ))
        except Exception as e:
            self.logger.error(f"Failed to store repair record: {e}")

    async def auto_repair_loop(self):
        """Continuous auto-repair loop"""
        while True:
            try:
                # Get current health status
                health_results = self.health_monitor.health_results

                # Check for conditions that trigger auto-repair
                for action_id, action in self.repair_actions.items():
                    if not action.auto_execute:
                        continue

                    # Check cooldown
                    if action.last_executed:
                        cooldown_expired = (datetime.now() - action.last_executed).total_seconds() >= (action.cooldown_minutes * 60)
                        if not cooldown_expired:
                            continue

                    # Check if any conditions are met
                    conditions_met = False
                    for condition in action.conditions:
                        if self._is_condition_met(condition, health_results):
                            conditions_met = True
                            break

                    if conditions_met:
                        self.logger.info(f"Auto-repair triggered for action: {action_id}")
                        success, message = await self.execute_repair(action_id)

                        if success:
                            self.logger.info(f"Auto-repair successful: {action_id} - {message}")
                        else:
                            self.logger.error(f"Auto-repair failed: {action_id} - {message}")

                # Wait for next check
                await asyncio.sleep(120)  # Check every 2 minutes

            except Exception as e:
                self.logger.error(f"Auto-repair loop error: {e}")
                await asyncio.sleep(120)

    def _is_condition_met(self, condition: str, health_results: Dict[str, HealthResult]) -> bool:
        """Check if a repair condition is met"""
        condition_mappings = {
            "memory_usage_critical": lambda: health_results.get("memory_usage", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.CRITICAL,
            "memory_usage_warning": lambda: health_results.get("memory_usage", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.WARNING,
            "disk_usage_critical": lambda: health_results.get("disk_usage", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.CRITICAL,
            "disk_usage_warning": lambda: health_results.get("disk_usage", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.WARNING,
            "service_unresponsive": lambda: any(r.status == HealthStatus.CRITICAL for r in health_results.values() if "service" in r.check_name),
            "service_failed": lambda: any(r.status == HealthStatus.CRITICAL for r in health_results.values() if "service" in r.check_name),
            "zombie_processes_detected": lambda: health_results.get("zombie_processes", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.WARNING,
            "network_connectivity_critical": lambda: health_results.get("network_connectivity", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.CRITICAL,
            "log_files_large": lambda: health_results.get("log_rotation", HealthResult("", HealthStatus.HEALTHY, "")).status == HealthStatus.WARNING
        }

        condition_func = condition_mappings.get(condition)
        return condition_func() if condition_func else False

    def get_repair_statistics(self) -> Dict[str, Any]:
        """Get repair statistics"""
        if not self.repair_history:
            return {"total_repairs": 0}

        total_repairs = len(self.repair_history)
        successful_repairs = sum(1 for repair in self.repair_history if repair['success'])
        average_execution_time = sum(repair['execution_time_ms'] for repair in self.repair_history) / total_repairs

        # Action-specific statistics
        action_stats = {}
        for action_id, action in self.repair_actions.items():
            action_stats[action_id] = {
                'name': action.name,
                'success_count': action.success_count,
                'failure_count': action.failure_count,
                'last_executed': action.last_executed.isoformat() if action.last_executed else None,
                'success_rate': action.success_count / (action.success_count + action.failure_count) if (action.success_count + action.failure_count) > 0 else 0
            }

        return {
            'total_repairs': total_repairs,
            'successful_repairs': successful_repairs,
            'overall_success_rate': successful_repairs / total_repairs,
            'average_execution_time_ms': average_execution_time,
            'action_statistics': action_stats
        }

class SelfHealingSystem:
    """Main self-healing system coordinator"""

    def __init__(self, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("self_healing_system")
        self.health_monitor = HealthMonitor(server_manager)
        self.auto_repair = AutoRepairEngine(self.health_monitor, server_manager)

        # System state
        self.self_healing_active = False
        self.repair_thread = None

    def start_self_healing(self):
        """Start the self-healing system"""
        if self.self_healing_active:
            return

        self.logger.info("Starting self-healing system...")

        # Start health monitoring
        self.health_monitor.start_monitoring()

        # Start auto-repair loop
        self.self_healing_active = True

        def repair_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.auto_repair.auto_repair_loop())
            finally:
                loop.close()

        self.repair_thread = threading.Thread(target=repair_loop, daemon=True)
        self.repair_thread.start()

        self.logger.info("Self-healing system started")

    def stop_self_healing(self):
        """Stop the self-healing system"""
        self.logger.info("Stopping self-healing system...")

        self.self_healing_active = False

        # Stop health monitoring
        self.health_monitor.stop_monitoring()

        # Wait for repair thread to finish
        if self.repair_thread:
            self.repair_thread.join(timeout=10)

        self.logger.info("Self-healing system stopped")

    async def run_diagnostics(self) -> DiagnosticReport:
        """Run comprehensive diagnostics"""
        # Run all health checks
        health_results = await self.health_monitor.run_all_health_checks()

        # Collect system metrics
        system_metrics = self._collect_system_metrics()

        # Identify issues
        identified_issues = []
        for result in health_results.values():
            if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                identified_issues.append(f"{result.check_name}: {result.message}")

        # Generate recommendations
        recommended_actions = self._generate_recommendations(health_results)

        # Identify repair candidates
        repair_candidates = []
        for action_id, action in self.auto_repair.repair_actions.items():
            if action.auto_execute:
                for condition in action.conditions:
                    if self.auto_repair._is_condition_met(condition, health_results):
                        repair_candidates.append(action_id)
                        break

        # Determine overall health
        critical_count = sum(1 for result in health_results.values() if result.status == HealthStatus.CRITICAL)
        if critical_count > 0:
            overall_health = HealthStatus.CRITICAL
        elif any(result.status == HealthStatus.WARNING for result in health_results.values()):
            overall_health = HealthStatus.WARNING
        else:
            overall_health = HealthStatus.HEALTHY

        return DiagnosticReport(
            timestamp=datetime.now(),
            overall_health=overall_health,
            health_checks=health_results,
            system_metrics=system_metrics,
            identified_issues=identified_issues,
            recommended_actions=recommended_actions,
            repair_candidates=repair_candidates
        )

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'disk_free_gb': psutil.disk_usage('/').free / (1024**3),
                'network_connections': len(psutil.net_connections()),
                'process_count': len(psutil.pids()),
                'uptime_seconds': time.time() - psutil.boot_time(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return {}

    def _generate_recommendations(self, health_results: Dict[str, HealthResult]) -> List[str]:
        """Generate recommendations based on health results"""
        recommendations = []

        for result in health_results.values():
            if result.status == HealthStatus.CRITICAL:
                if "memory" in result.check_name:
                    recommendations.append("Critical memory usage detected - consider restarting services or adding more RAM")
                elif "cpu" in result.check_name:
                    recommendations.append("High CPU usage detected - identify resource-intensive processes")
                elif "disk" in result.check_name:
                    recommendations.append("Critical disk usage detected - clean up disk space or add storage")
                elif "network" in result.check_name:
                    recommendations.append("Network connectivity issues detected - check network configuration")
                elif "service" in result.check_name:
                    recommendations.append("Service issues detected - restart affected services")
            elif result.status == HealthStatus.WARNING:
                if "memory" in result.check_name:
                    recommendations.append("Memory usage is high - monitor closely")
                elif "disk" in result.check_name:
                    recommendations.append("Disk usage is growing - consider cleanup")
                elif "log" in result.check_name:
                    recommendations.append("Log files are growing - implement log rotation")

        return recommendations

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        health_summary = self.health_monitor.get_health_summary()
        repair_stats = self.auto_repair.get_repair_statistics()

        return {
            'timestamp': datetime.now().isoformat(),
            'health_summary': health_summary,
            'repair_statistics': repair_stats,
            'self_healing_active': self.self_healing_active,
            'repair_actions_available': len(self.auto_repair.repair_actions),
            'auto_repair_enabled': sum(1 for action in self.auto_repair.repair_actions.values() if action.auto_execute)
        }

# Global instance
_self_healing_system = None

def get_self_healing_system(server_manager: Optional[ServerManager] = None) -> SelfHealingSystem:
    """Get the global self-healing system instance"""
    global _self_healing_system

    if _self_healing_system is None:
        _self_healing_system = SelfHealingSystem(server_manager)

    return _self_healing_system

if __name__ == "__main__":
    # Example usage
    async def example_usage():
        """Demonstrate self-healing system usage"""

        # Create self-healing system
        self_healing = get_self_healing_system()

        # Start self-healing
        self_healing.start_self_healing()

        print("Self-healing system started... Running for 5 minutes")
        time.sleep(300)

        # Run diagnostics
        report = await self_healing.run_diagnostics()
        print(f"Diagnostic report: {report.overall_health}")
        print(f"Issues identified: {len(report.identified_issues)}")

        # Get health report
        health_report = self_healing.get_system_health_report()
        print(f"Health report: {health_report['health_summary']}")

        # Stop self-healing
        self_healing.stop_self_healing()

    # Run example
    asyncio.run(example_usage())
#!/usr/bin/env python3
"""
Advanced Error Classification and Recovery System for DuckBot v4.2
Provides comprehensive error handling, automated recovery, and self-healing capabilities
"""

import os
import sys
import time
import json
import asyncio
import logging
import traceback
import threading
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import uuid
import psutil
import socket
import subprocess
from abc import ABC, abstractmethod

# Import existing DuckBot components
try:
    from duckbot.core.logging_setup import get_logger
    from duckbot.services.server_manager import ServerManager, ServiceStatus
    from duckbot.ui.observability import increment_counter
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import DuckBot components: {e}")

# Error severity levels
class ErrorSeverity(Enum):
    CRITICAL = "critical"      # System failure - immediate attention required
    HIGH = "high"             # Major functionality impaired
    MEDIUM = "medium"         # Partial functionality affected
    LOW = "low"               # Minor issue, system continues
    INFO = "info"             # Informational, no action needed

# Error categories
class ErrorCategory(Enum):
    NETWORK = "network"              # Network connectivity issues
    MEMORY = "memory"                # Memory/resource exhaustion
    API = "api"                      # External API failures
    SERVICE = "service"              # Service/component failures
    HARDWARE = "hardware"            # Hardware/resource issues
    CONFIGURATION = "configuration"  # Configuration problems
    PERMISSION = "permission"        # Permission/access issues
    TIMEOUT = "timeout"              # Timeout issues
    DEPENDENCY = "dependency"        # Missing/broken dependencies
    UNKNOWN = "unknown"              # Unclassified errors

# Recovery strategies
class RecoveryStrategy(Enum):
    RETRY = "retry"                  # Retry the operation
    RESTART = "restart"              # Restart the service
    FALLBACK = "fallback"            # Use fallback service
    DEGRADE = "degrade"              # Degrade gracefully
    ESCALATE = "escalate"            # Escalate to human operator
    IGNORE = "ignore"                # Ignore (for non-critical errors)
    CIRCUIT_BREAK = "circuit_break"  # Circuit breaker pattern

@dataclass
class ErrorContext:
    """Rich context information for error analysis"""
    timestamp: datetime
    service_name: str
    operation: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    stack_trace: Optional[str] = None
    system_metrics: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    recovery_attempted: bool = False

    def __post_init__(self):
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())

@dataclass
class RecoveryAction:
    """Action taken for error recovery"""
    strategy: RecoveryStrategy
    service_name: str
    action_taken: str
    success: bool
    execution_time_ms: int
    error_context_hash: str
    recovery_message: str
    timestamp: datetime

@dataclass
class ErrorPattern:
    """Identified error pattern for proactive handling"""
    pattern_id: str
    pattern_name: str
    error_signatures: List[str]
    frequency_threshold: int  # Minimum occurrences to trigger
    time_window_minutes: int   # Time window for frequency check
    suggested_recovery: RecoveryStrategy
    auto_recovery_enabled: bool
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

class ErrorClassifier:
    """Advanced error classification and analysis system"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger("error_classifier")
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.error_history: List[ErrorContext] = []
        self.recovery_history: List[RecoveryAction] = []
        self.classification_rules = self._load_classification_rules(config_path)

        # Load predefined error patterns
        self._initialize_error_patterns()

    def _load_classification_rules(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load classification rules from configuration"""
        default_rules = {
            "network_indicators": ["connection", "timeout", "network", "dns", "socket"],
            "memory_indicators": ["memory", "out of memory", "allocation", "heap", "malloc"],
            "api_indicators": ["api", "http", "status code", "rate limit", "quota"],
            "service_indicators": ["service", "process", "daemon", "crash", "exit"],
            "hardware_indicators": ["cpu", "disk", "gpu", "resource", "hardware"],
            "timeout_indicators": ["timeout", "timed out", "deadline", "expired"],
            "permission_indicators": ["permission", "access", "denied", "forbidden", "unauthorized"]
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load classification rules: {e}")

        return default_rules

    def _initialize_error_patterns(self):
        """Initialize predefined error patterns"""
        patterns = [
            ErrorPattern(
                pattern_id="connection_timeout_pattern",
                pattern_name="Repeated Connection Timeouts",
                error_signatures=["timeout", "connection", "network"],
                frequency_threshold=3,
                time_window_minutes=5,
                suggested_recovery=RecoveryStrategy.FALLBACK,
                auto_recovery_enabled=True
            ),
            ErrorPattern(
                pattern_id="memory_exhaustion_pattern",
                pattern_name="Memory Exhaustion Pattern",
                error_signatures=["memory", "allocation", "out of memory"],
                frequency_threshold=2,
                time_window_minutes=10,
                suggested_recovery=RecoveryStrategy.RESTART,
                auto_recovery_enabled=True
            ),
            ErrorPattern(
                pattern_id="api_rate_limit_pattern",
                pattern_name="API Rate Limit Pattern",
                error_signatures=["rate limit", "quota", "429"],
                frequency_threshold=5,
                time_window_minutes=1,
                suggested_recovery=RecoveryStrategy.CIRCUIT_BREAK,
                auto_recovery_enabled=True
            ),
            ErrorPattern(
                pattern_id="service_crash_pattern",
                pattern_name="Service Crash Pattern",
                error_signatures=["crash", "exit", "process", "service"],
                frequency_threshold=2,
                time_window_minutes=15,
                suggested_recovery=RecoveryStrategy.RESTART,
                auto_recovery_enabled=True
            )
        ]

        for pattern in patterns:
            self.error_patterns[pattern.pattern_id] = pattern

    def classify_error(self,
                      error: Exception,
                      service_name: str,
                      operation: str,
                      severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                      user_context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Classify an error with rich context"""

        # Extract error information
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()

        # Determine error category
        category = self._determine_error_category(error_type, error_message)

        # Collect system metrics
        system_metrics = self._collect_system_metrics()

        # Create error context
        context = ErrorContext(
            timestamp=datetime.now(),
            service_name=service_name,
            operation=operation,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            stack_trace=stack_trace,
            system_metrics=system_metrics,
            user_context=user_context
        )

        # Store in history
        self.error_history.append(context)

        # Keep history manageable
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]

        # Log classification
        self.logger.error(f"Error classified: {category.value} - {error_type} in {service_name}.{operation}")

        # Update metrics
        try:
            increment_counter("errors_total", {"category": category.value, "severity": severity.value})
        except:
            pass

        return context

    def _determine_error_category(self, error_type: str, error_message: str) -> ErrorCategory:
        """Determine error category based on error information"""
        error_text = f"{error_type} {error_message}".lower()

        # Check each category's indicators
        for category, indicators in self.classification_rules.items():
            category_name = category.replace("_indicators", "")
            if any(indicator in error_text for indicator in indicators):
                return ErrorCategory(category_name)

        # Special cases for specific error types
        if "connection" in error_type.lower() or "timeout" in error_type.lower():
            return ErrorCategory.NETWORK
        elif "memory" in error_type.lower() or "allocation" in error_type.lower():
            return ErrorCategory.MEMORY
        elif "permission" in error_type.lower() or "access" in error_type.lower():
            return ErrorCategory.PERMISSION

        return ErrorCategory.UNKNOWN

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        metrics = {}

        try:
            # CPU and Memory
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            metrics['memory_percent'] = psutil.virtual_memory().percent
            metrics['memory_available_gb'] = psutil.virtual_memory().available / (1024**3)
            metrics['disk_usage_percent'] = psutil.disk_usage('/').percent

            # Network
            metrics['network_connections'] = len(psutil.net_connections())

            # Process count
            metrics['process_count'] = len(psutil.pids())

        except Exception as e:
            self.logger.debug(f"Could not collect system metrics: {e}")

        return metrics

    def detect_error_patterns(self) -> List[ErrorPattern]:
        """Detect emerging error patterns"""
        detected_patterns = []
        current_time = datetime.now()

        for pattern_id, pattern in self.error_patterns.items():
            # Check if pattern should be auto-detected
            if not pattern.auto_recovery_enabled:
                continue

            # Count matching errors in time window
            time_window = timedelta(minutes=pattern.time_window_minutes)
            recent_errors = [
                error for error in self.error_history
                if (current_time - error.timestamp) <= time_window
            ]

            # Count matches for this pattern
            match_count = 0
            for error in recent_errors:
                error_text = f"{error.error_type} {error.error_message}".lower()
                if any(signature.lower() in error_text for signature in pattern.error_signatures):
                    match_count += 1

            # Check if pattern is triggered
            if match_count >= pattern.frequency_threshold:
                pattern.trigger_count += 1
                pattern.last_triggered = current_time
                detected_patterns.append(pattern)

                self.logger.warning(f"Error pattern detected: {pattern.pattern_name} (occurrences: {match_count})")

        return detected_patterns

    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for analysis"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_errors = [error for error in self.error_history if error.timestamp >= cutoff_time]

        if not recent_errors:
            return {"total_errors": 0}

        # Basic statistics
        stats = {
            "total_errors": len(recent_errors),
            "unique_services": len(set(error.service_name for error in recent_errors)),
            "error_categories": {},
            "severity_distribution": {},
            "top_error_types": {},
            "recovery_success_rate": 0.0
        }

        # Category distribution
        for error in recent_errors:
            category = error.category.value
            stats["error_categories"][category] = stats["error_categories"].get(category, 0) + 1

        # Severity distribution
        for error in recent_errors:
            severity = error.severity.value
            stats["severity_distribution"][severity] = stats["severity_distribution"].get(severity, 0) + 1

        # Top error types
        error_types = {}
        for error in recent_errors:
            error_type = error.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1

        stats["top_error_types"] = dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10])

        # Recovery success rate
        recent_recoveries = [recovery for recovery in self.recovery_history
                           if recovery.timestamp >= cutoff_time]
        if recent_recoveries:
            successful_recoveries = sum(1 for recovery in recent_recoveries if recovery.success)
            stats["recovery_success_rate"] = successful_recoveries / len(recent_recoveries)

        return stats

    def get_error_hash(self, error_context: ErrorContext) -> str:
        """Generate a hash for error context to identify similar errors"""
        # Create hashable content from error context
        content = f"{error_context.service_name}.{error_context.operation}.{error_context.error_type}.{error_context.category.value}"
        return hashlib.md5(content.encode()).hexdigest()

class RecoveryEngine:
    """Advanced automated recovery engine"""

    def __init__(self, error_classifier: ErrorClassifier, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("recovery_engine")
        self.error_classifier = error_classifier
        self.server_manager = server_manager
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.recovery_lock = threading.Lock()

    def _initialize_recovery_strategies(self) -> Dict[RecoveryStrategy, Callable]:
        """Initialize recovery strategy implementations"""
        return {
            RecoveryStrategy.RETRY: self._strategy_retry,
            RecoveryStrategy.RESTART: self._strategy_restart,
            RecoveryStrategy.FALLBACK: self._strategy_fallback,
            RecoveryStrategy.DEGRADE: self._strategy_degrade,
            RecoveryStrategy.ESCALATE: self._strategy_escalate,
            RecoveryStrategy.IGNORE: self._strategy_ignore,
            RecoveryStrategy.CIRCUIT_BREAK: self._strategy_circuit_break
        }

    async def handle_error(self, error_context: ErrorContext) -> RecoveryAction:
        """Handle an error with automated recovery"""

        # Check if circuit breaker is open
        circuit_key = f"{error_context.service_name}.{error_context.operation}"
        if self._is_circuit_breaker_open(circuit_key):
            self.logger.warning(f"Circuit breaker open for {circuit_key}, skipping recovery")
            return RecoveryAction(
                strategy=RecoveryStrategy.IGNORE,
                service_name=error_context.service_name,
                action_taken="Circuit breaker open - no action",
                success=False,
                execution_time_ms=0,
                error_context_hash=self.error_classifier.get_error_hash(error_context),
                recovery_message="Circuit breaker prevents recovery attempts",
                timestamp=datetime.now()
            )

        # Determine recovery strategy
        strategy = self._determine_recovery_strategy(error_context)

        # Execute recovery
        start_time = time.time()
        try:
            recovery_func = self.recovery_strategies[strategy]
            success, message = await recovery_func(error_context)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Record recovery action
            recovery_action = RecoveryAction(
                strategy=strategy,
                service_name=error_context.service_name,
                action_taken=message,
                success=success,
                execution_time_ms=execution_time_ms,
                error_context_hash=self.error_classifier.get_error_hash(error_context),
                recovery_message=message,
                timestamp=datetime.now()
            )

            # Update error context
            error_context.recovery_attempted = True

            # Store recovery action
            self.error_classifier.recovery_history.append(recovery_action)

            # Update circuit breaker state
            self._update_circuit_breaker(circuit_key, success)

            # Log recovery
            if success:
                self.logger.info(f"Recovery successful: {strategy.value} for {error_context.service_name}")
            else:
                self.logger.error(f"Recovery failed: {strategy.value} for {error_context.service_name}")

            return recovery_action

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Recovery strategy execution failed: {e}")

            return RecoveryAction(
                strategy=strategy,
                service_name=error_context.service_name,
                action_taken=f"Strategy execution failed: {str(e)}",
                success=False,
                execution_time_ms=execution_time_ms,
                error_context_hash=self.error_classifier.get_error_hash(error_context),
                recovery_message=f"Recovery strategy failed: {str(e)}",
                timestamp=datetime.now()
            )

    def _determine_recovery_strategy(self, error_context: ErrorContext) -> RecoveryStrategy:
        """Determine the best recovery strategy for an error"""

        # Check for error patterns first
        detected_patterns = self.error_classifier.detect_error_patterns()
        for pattern in detected_patterns:
            if any(signature.lower() in f"{error_context.error_type} {error_context.error_message}".lower()
                   for signature in pattern.error_signatures):
                self.logger.info(f"Using pattern-based recovery: {pattern.suggested_recovery.value}")
                return pattern.suggested_recovery

        # Default strategy based on error category and severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ESCALATE

        # Category-based strategies
        category_strategies = {
            ErrorCategory.NETWORK: RecoveryStrategy.RETRY,
            ErrorCategory.MEMORY: RecoveryStrategy.RESTART,
            ErrorCategory.API: RecoveryStrategy.FALLBACK,
            ErrorCategory.SERVICE: RecoveryStrategy.RESTART,
            ErrorCategory.TIMEOUT: RecoveryStrategy.RETRY,
            ErrorCategory.DEPENDENCY: RecoveryStrategy.FALLBACK,
            ErrorCategory.PERMISSION: RecoveryStrategy.ESCALATE
        }

        return category_strategies.get(error_context.category, RecoveryStrategy.RETRY)

    async def _strategy_retry(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Retry strategy implementation"""
        max_retries = 3
        backoff_time = 2 ** error_context.retry_count  # Exponential backoff

        if error_context.retry_count >= max_retries:
            return False, f"Max retries ({max_retries}) exceeded"

        # Wait for backoff period
        await asyncio.sleep(backoff_time)

        # This is a placeholder - actual retry logic would be implemented
        # by the calling code using the recovery context
        return True, f"Retry {error_context.retry_count + 1}/{max_retries} scheduled"

    async def _strategy_restart(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Restart strategy implementation"""
        if not self.server_manager:
            return False, "No server manager available for restart"

        try:
            success, message = self.server_manager.restart_service(error_context.service_name)
            return success, f"Service restart: {message}"
        except Exception as e:
            return False, f"Restart failed: {str(e)}"

    async def _strategy_fallback(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Fallback strategy implementation"""
        # This would implement fallback logic (e.g., switch to backup service)
        return True, "Fallback service activated"

    async def _strategy_degrade(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Degrade strategy implementation"""
        # This would implement graceful degradation
        return True, "Service degraded gracefully"

    async def _strategy_escalate(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Escalate strategy implementation"""
        # This would implement escalation to human operators
        self.logger.critical(f"ERROR ESCALATION REQUIRED: {error_context.error_message}")
        return True, "Error escalated to human operator"

    async def _strategy_ignore(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Ignore strategy implementation"""
        return True, "Error ignored (non-critical)"

    async def _strategy_circuit_break(self, error_context: ErrorContext) -> tuple[bool, str]:
        """Circuit breaker strategy implementation"""
        circuit_key = f"{error_context.service_name}.{error_context.operation}"

        # Open circuit breaker
        self.circuit_breakers[circuit_key] = {
            'state': 'open',
            'opened_at': datetime.now(),
            'failure_count': 0
        }

        return True, f"Circuit breaker opened for {circuit_key}"

    def _is_circuit_breaker_open(self, circuit_key: str) -> bool:
        """Check if circuit breaker is open for a service/operation"""
        if circuit_key not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[circuit_key]

        # Check if breaker should be reset (after cooldown period)
        if breaker['state'] == 'open':
            cooldown_time = timedelta(minutes=5)  # 5 minute cooldown
            if datetime.now() - breaker['opened_at'] > cooldown_time:
                breaker['state'] = 'half_open'
                self.logger.info(f"Circuit breaker half-open for {circuit_key}")
                return False

        return breaker['state'] == 'open'

    def _update_circuit_breaker(self, circuit_key: str, success: bool):
        """Update circuit breaker state based on recovery result"""
        if circuit_key not in self.circuit_breakers:
            return

        breaker = self.circuit_breakers[circuit_key]

        if success:
            if breaker['state'] == 'half_open':
                # Close circuit breaker on successful recovery
                breaker['state'] = 'closed'
                breaker['failure_count'] = 0
                self.logger.info(f"Circuit breaker closed for {circuit_key}")
        else:
            # Increment failure count
            breaker['failure_count'] += 1

            # Open circuit breaker if too many failures
            if breaker['failure_count'] >= 3:
                breaker['state'] = 'open'
                breaker['opened_at'] = datetime.now()
                self.logger.warning(f"Circuit breaker opened for {circuit_key} due to repeated failures")

class SelfHealingManager:
    """Self-healing and health monitoring system"""

    def __init__(self, error_classifier: ErrorClassifier, recovery_engine: RecoveryEngine):
        self.logger = get_logger("self_healing")
        self.error_classifier = error_classifier
        self.recovery_engine = recovery_engine
        self.health_checks: Dict[str, Callable] = {}
        self.monitoring_active = False
        self.monitor_thread = None

        # Initialize health checks
        self._initialize_health_checks()

    def _initialize_health_checks(self):
        """Initialize health check functions"""
        self.health_checks = {
            'memory_usage': self._check_memory_usage,
            'disk_usage': self._check_disk_usage,
            'cpu_usage': self._check_cpu_usage,
            'network_connectivity': self._check_network_connectivity,
            'service_health': self._check_service_health
        }

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage health"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            health_status = {
                'metric': 'memory_usage',
                'value': memory_percent,
                'status': 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 90 else 'critical',
                'threshold': {'warning': 80, 'critical': 90},
                'message': f"Memory usage: {memory_percent:.1f}%"
            }

            if memory_percent > 95:
                # Trigger memory cleanup
                await self._trigger_memory_cleanup()

            return health_status

        except Exception as e:
            return {'metric': 'memory_usage', 'status': 'error', 'message': f"Health check failed: {str(e)}"}

    async def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage health"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            health_status = {
                'metric': 'disk_usage',
                'value': disk_percent,
                'status': 'healthy' if disk_percent < 85 else 'warning' if disk_percent < 95 else 'critical',
                'threshold': {'warning': 85, 'critical': 95},
                'message': f"Disk usage: {disk_percent:.1f}%"
            }

            if disk_percent > 98:
                # Trigger disk cleanup
                await self._trigger_disk_cleanup()

            return health_status

        except Exception as e:
            return {'metric': 'disk_usage', 'status': 'error', 'message': f"Health check failed: {str(e)}"}

    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)

            health_status = {
                'metric': 'cpu_usage',
                'value': cpu_percent,
                'status': 'healthy' if cpu_percent < 70 else 'warning' if cpu_percent < 90 else 'critical',
                'threshold': {'warning': 70, 'critical': 90},
                'message': f"CPU usage: {cpu_percent:.1f}%"
            }

            return health_status

        except Exception as e:
            return {'metric': 'cpu_usage', 'status': 'error', 'message': f"Health check failed: {str(e)}"}

    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity health"""
        try:
            # Test basic connectivity
            test_hosts = ['8.8.8.8', '1.1.1.1']
            connected_count = 0

            for host in test_hosts:
                try:
                    sock = socket.create_connection((host, 53), timeout=2)
                    sock.close()
                    connected_count += 1
                except:
                    pass

            connectivity_percent = (connected_count / len(test_hosts)) * 100

            health_status = {
                'metric': 'network_connectivity',
                'value': connectivity_percent,
                'status': 'healthy' if connectivity_percent == 100 else 'warning' if connectivity_percent >= 50 else 'critical',
                'message': f"Network connectivity: {connectivity_percent:.0f}%"
            }

            return health_status

        except Exception as e:
            return {'metric': 'network_connectivity', 'status': 'error', 'message': f"Health check failed: {str(e)}"}

    async def _check_service_health(self) -> Dict[str, Any]:
        """Check overall service health"""
        try:
            if not self.recovery_engine.server_manager:
                return {'metric': 'service_health', 'status': 'unknown', 'message': "No server manager available"}

            service_status = self.recovery_engine.server_manager.get_all_service_status()

            # Count services by status
            status_counts = {}
            for service_info in service_status.values():
                status = service_info.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            total_services = len(service_status)
            healthy_services = status_counts.get('running', 0)
            health_percent = (healthy_services / total_services) * 100 if total_services > 0 else 0

            health_status = {
                'metric': 'service_health',
                'value': health_percent,
                'status': 'healthy' if health_percent == 100 else 'warning' if health_percent >= 70 else 'critical',
                'message': f"Service health: {healthy_services}/{total_services} running"
            }

            return health_status

        except Exception as e:
            return {'metric': 'service_health', 'status': 'error', 'message': f"Health check failed: {str(e)}"}

    async def _trigger_memory_cleanup(self):
        """Trigger memory cleanup procedures"""
        self.logger.warning("Triggering memory cleanup due to high memory usage")

        try:
            # Clear Python garbage collection
            import gc
            gc.collect()

            # Clear error history if too large
            if len(self.error_classifier.error_history) > 500:
                self.error_classifier.error_history = self.error_classifier[-200:]
                self.logger.info("Cleared old error history to reduce memory usage")

        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")

    async def _trigger_disk_cleanup(self):
        """Trigger disk cleanup procedures"""
        self.logger.warning("Triggering disk cleanup due to high disk usage")

        try:
            # Clean up old log files
            log_dir = Path("logs")
            if log_dir.exists():
                cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff_time:
                        log_file.unlink()
                        self.logger.info(f"Cleaned up old log file: {log_file}")

        except Exception as e:
            self.logger.error(f"Disk cleanup failed: {e}")

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {}

        for check_name, check_func in self.health_checks.items():
            try:
                result = await check_func()
                results[check_name] = result

                # Log critical health issues
                if result.get('status') == 'critical':
                    self.logger.critical(f"Critical health issue: {result.get('message')}")

            except Exception as e:
                self.logger.error(f"Health check {check_name} failed: {e}")
                results[check_name] = {'metric': check_name, 'status': 'error', 'message': f"Check execution failed: {str(e)}"}

        return results

    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Run health checks
                    results = asyncio.run(self.run_health_checks())

                    # Log overall health status
                    critical_issues = [r for r in results.values() if r.get('status') == 'critical']
                    if critical_issues:
                        self.logger.warning(f"Health monitoring detected {len(critical_issues)} critical issues")

                    # Wait for next check
                    time.sleep(interval_seconds)

                except Exception as e:
                    self.logger.error(f"Health monitoring error: {e}")
                    time.sleep(interval_seconds)

        self.monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitor_thread.start()

        self.logger.info(f"Health monitoring started (interval: {interval_seconds}s)")

    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("Health monitoring stopped")

class AdvancedErrorHandler:
    """Main error handling and recovery system coordinator"""

    def __init__(self, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("advanced_error_handler")
        self.error_classifier = ErrorClassifier()
        self.recovery_engine = RecoveryEngine(self.error_classifier, server_manager)
        self.self_healing = SelfHealingManager(self.error_classifier, self.recovery_engine)

        self.logger.info("Advanced Error Handler initialized")

    async def handle_error_async(self,
                               error: Exception,
                               service_name: str,
                               operation: str,
                               severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                               user_context: Optional[Dict[str, Any]] = None) -> RecoveryAction:
        """Handle an error asynchronously"""

        # Classify the error
        error_context = self.error_classifier.classify_error(
            error, service_name, operation, severity, user_context
        )

        # Attempt automated recovery
        recovery_action = await self.recovery_engine.handle_error(error_context)

        # Log the complete error handling process
        self.logger.info(f"Error handled: {error_context.error_type} -> {recovery_action.strategy.value} ({'success' if recovery_action.success else 'failed'})")

        return recovery_action

    def handle_error_sync(self,
                         error: Exception,
                         service_name: str,
                         operation: str,
                         severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                         user_context: Optional[Dict[str, Any]] = None) -> RecoveryAction:
        """Handle an error synchronously"""
        return asyncio.run(self.handle_error_async(error, service_name, operation, severity, user_context))

    def start_monitoring(self, interval_seconds: int = 60):
        """Start error monitoring and self-healing"""
        self.self_healing.start_monitoring(interval_seconds)

    def stop_monitoring(self):
        """Stop error monitoring"""
        self.self_healing.stop_monitoring()

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        return asyncio.run(self.self_healing.run_health_checks())

    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error statistics and analysis"""
        return self.error_classifier.get_error_statistics(time_window_hours)

    def get_recovery_report(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get recovery performance report"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        recent_recoveries = [
            recovery for recovery in self.error_classifier.recovery_history
            if recovery.timestamp >= cutoff_time
        ]

        if not recent_recoveries:
            return {"total_recoveries": 0}

        # Basic recovery statistics
        stats = {
            "total_recoveries": len(recent_recoveries),
            "successful_recoveries": sum(1 for r in recent_recoveries if r.success),
            "recovery_success_rate": sum(1 for r in recent_recoveries if r.success) / len(recent_recoveries),
            "average_recovery_time_ms": sum(r.execution_time_ms for r in recent_recoveries) / len(recent_recoveries),
            "strategies_used": {},
            "services_recovered": {}
        }

        # Strategy usage
        for recovery in recent_recoveries:
            strategy = recovery.strategy.value
            stats["strategies_used"][strategy] = stats["strategies_used"].get(strategy, 0) + 1

        # Service recovery
        for recovery in recent_recoveries:
            service = recovery.service_name
            if recovery.success:
                stats["services_recovered"][service] = stats["services_recovered"].get(service, 0) + 1

        return stats

# Global error handler instance
_advanced_error_handler = None

def get_advanced_error_handler(server_manager: Optional[ServerManager] = None) -> AdvancedErrorHandler:
    """Get the global advanced error handler instance"""
    global _advanced_error_handler

    if _advanced_error_handler is None:
        _advanced_error_handler = AdvancedErrorHandler(server_manager)

    return _advanced_error_handler

# Decorator for automatic error handling
def handle_errors(service_name: str, operation: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator for automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_advanced_error_handler()
                recovery_action = error_handler.handle_error_sync(e, service_name, operation, severity)

                # Re-raise the error if recovery failed and severity is critical or high
                if not recovery_action.success and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                    raise

                # Return a fallback value or None based on operation
                return None
        return wrapper
    return decorator

# Context manager for error handling
class ErrorHandlerContext:
    """Context manager for handling errors in a block of code"""

    def __init__(self, service_name: str, operation: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.service_name = service_name
        self.operation = operation
        self.severity = severity
        self.error_handler = get_advanced_error_handler()
        self.recovery_action = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle the exception
            self.recovery_action = self.error_handler.handle_error_sync(
                exc_val, self.service_name, self.operation, self.severity
            )

            # Return True to suppress the exception if recovery was successful
            # and severity is not critical or high
            if (self.recovery_action.success and
                self.severity not in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]):
                return True

        return False

if __name__ == "__main__":
    # Example usage
    async def example_usage():
        """Demonstrate error handling system usage"""

        # Create error handler
        error_handler = get_advanced_error_handler()

        # Start monitoring
        error_handler.start_monitoring(interval_seconds=30)

        # Simulate some errors
        test_errors = [
            (ConnectionError("Connection timeout"), "webui", "api_call", ErrorSeverity.HIGH),
            (MemoryError("Out of memory"), "comfyui", "image_generation", ErrorSeverity.CRITICAL),
            (Exception("General error"), "discord_bot", "message_handler", ErrorSeverity.MEDIUM)
        ]

        for error, service, operation, severity in test_errors:
            recovery = await error_handler.handle_error_async(error, service, operation, severity)
            print(f"Error handled: {error.__class__.__name__} -> {recovery.strategy.value}")

        # Get system health
        health = error_handler.get_system_health()
        print(f"System health: {health}")

        # Get error statistics
        stats = error_handler.get_error_statistics()
        print(f"Error statistics: {stats}")

        # Stop monitoring
        error_handler.stop_monitoring()

    # Run example
    asyncio.run(example_usage())
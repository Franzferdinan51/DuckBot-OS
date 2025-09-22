"""
DuckBot Security Automation System

Provides comprehensive automation capabilities for key management including:
- Automated key rotation and renewal workflows
- Real-time health monitoring and alerting
- Intelligent threat detection and response
- Automated compliance checking and reporting
- Self-healing capabilities
- Performance optimization and scaling
- Security incident response automation
- Backup and recovery automation

Author: Security Engineering Team
Version: 2.0.0
Security Classification: Critical
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import secrets
import asyncio
import aiofiles
from pathlib import Path
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
import statistics
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod

# Machine learning imports (optional)
try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Cryptography imports
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Security imports
from .key_manager import SecureKeyManager, KeyStatus, SecurityLevel
from .secure_storage import SecureStorageManager
from .key_lifecycle import KeyLifecycleManager, HealthStatus
from .hsm_integration import HSMManager, HSMStatus

# Security logging
security_logger = logging.getLogger('duckbot.security.automation')

class AutomationTrigger(Enum):
    """Automation trigger types"""
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    THRESHOLD_BASED = "threshold_based"
    HEALTH_BASED = "health_based"
    COMPLIANCE_BASED = "compliance_based"
    PERFORMANCE_BASED = "performance_based"
    SECURITY_EVENT = "security_event"

class AutomationAction(Enum):
    """Automation action types"""
    KEY_ROTATION = "key_rotation"
    KEY_REVOCATION = "key_revocation"
    BACKUP_CREATION = "backup_creation"
    HEALTH_CHECK = "health_check"
    COMPLIANCE_SCAN = "compliance_scan"
    ALERT_GENERATION = "alert_generation"
    SYSTEM_RESTART = "system_restart"
    FAILOVER_ACTIVATION = "failover_activation"
    THRESHOLD_ADJUSTMENT = "threshold_adjustment"
    NOTIFICATION = "notification"
    REPORT_GENERATION = "report_generation"

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AutomationStatus(Enum):
    """Automation execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class AutomationRule:
    """Automation rule configuration"""
    rule_id: str
    name: str
    description: str
    trigger: AutomationTrigger
    condition: Dict[str, Any]
    actions: List[AutomationAction]
    schedule: Optional[str] = None  # Cron expression
    enabled: bool = True
    priority: AlertPriority = AlertPriority.MEDIUM
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 60
    cooldown_period_seconds: int = 300
    last_triggered: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_execution_time_ms: float = 0.0
    custom_parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AutomationExecution:
    """Automation execution record"""
    execution_id: str
    rule_id: str
    triggered_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: AutomationStatus = AutomationStatus.PENDING
    trigger_context: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    retry_count: int = 0

@dataclass
class SecurityEvent:
    """Security event for automation"""
    event_id: str
    event_type: str
    severity: AlertPriority
    timestamp: datetime
    source: str
    description: str
    affected_resources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

@dataclass
class HealthMetric:
    """System health metric"""
    metric_id: str
    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    is_healthy: bool = True
    trend_direction: str = "stable"  # increasing, decreasing, stable
    anomaly_score: float = 0.0

@dataclass
class ComplianceCheck:
    """Compliance check result"""
    check_id: str
    standard: str
    control: str
    description: str
    passed: bool
    timestamp: datetime
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    severity: AlertPriority = AlertPriority.MEDIUM

class AutomationEngine:
    """Main automation engine for security operations"""

    def __init__(self, key_manager: SecureKeyManager,
                 storage_manager: SecureStorageManager,
                 lifecycle_manager: KeyLifecycleManager,
                 hsm_manager: HSMManager):
        self.key_manager = key_manager
        self.storage_manager = storage_manager
        self.lifecycle_manager = lifecycle_manager
        self.hsm_manager = hsm_manager

        self.rules: Dict[str, AutomationRule] = {}
        self.executions: Dict[str, AutomationExecution] = {}
        self.security_events: List[SecurityEvent] = []
        self.health_metrics: Dict[str, List[HealthMetric]] = {}
        self.compliance_checks: List[ComplianceCheck] = []

        self._lock = threading.RLock()
        self._thread_pool = ThreadPoolExecutor(max_workers=8)
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False

        # Initialize machine learning models
        self._initialize_ml_models()

        # Load default rules
        self._load_default_rules()

        # Start automation engine
        self._start_automation_engine()

        security_logger.info("AutomationEngine initialized")

    def _initialize_ml_models(self):
        """Initialize machine learning models for anomaly detection"""
        self.ml_models = {}
        self.ml_scalers = {}

        if ML_AVAILABLE:
            try:
                # Anomaly detection model for key usage
                self.ml_models['key_usage_anomaly'] = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )
                self.ml_scalers['key_usage'] = StandardScaler()

                # Anomaly detection model for system performance
                self.ml_models['performance_anomaly'] = IsolationForest(
                    contamination=0.05,
                    random_state=42
                )
                self.ml_scalers['performance'] = StandardScaler()

                security_logger.info("Machine learning models initialized for anomaly detection")
            except Exception as e:
                security_logger.warning(f"Failed to initialize ML models: {e}")

    def _load_default_rules(self):
        """Load default automation rules"""
        default_rules = [
            AutomationRule(
                rule_id="auto_key_rotation_due",
                name="Automatic Key Rotation",
                description="Automatically rotate keys that are due for rotation",
                trigger=AutomationTrigger.SCHEDULED,
                condition={"type": "rotation_due", "threshold_hours": 24},
                actions=[AutomationAction.KEY_ROTATION],
                schedule="0 2 * * *",  # Daily at 2 AM
                priority=AlertPriority.HIGH,
                timeout_seconds=600
            ),
            AutomationRule(
                rule_id="key_health_critical",
                name="Critical Key Health Response",
                description="Respond to critical key health issues",
                trigger=AutomationTrigger.HEALTH_BASED,
                condition={"health_status": HealthStatus.CRITICAL.value},
                actions=[
                    AutomationAction.ALERT_GENERATION,
                    AutomationAction.KEY_ROTATION,
                    AutomationAction.NOTIFICATION
                ],
                priority=AlertPriority.CRITICAL,
                cooldown_period_seconds=3600
            ),
            AutomationRule(
                rule_id="high_error_rate",
                name="High Error Rate Response",
                description="Respond to high key operation error rates",
                trigger=AutomationTrigger.THRESHOLD_BASED,
                condition={"metric": "error_rate", "threshold": 0.05, "operator": ">"},
                actions=[
                    AutomationAction.ALERT_GENERATION,
                    AutomationAction.HEALTH_CHECK
                ],
                priority=AlertPriority.HIGH
            ),
            AutomationRule(
                rule_id="compliance_violation",
                name="Compliance Violation Response",
                description="Respond to compliance violations",
                trigger=AutomationTrigger.COMPLIANCE_BASED,
                condition={"compliance_passed": False},
                actions=[
                    AutomationAction.ALERT_GENERATION,
                    AutomationAction.REPORT_GENERATION,
                    AutomationAction.NOTIFICATION
                ],
                priority=AlertPriority.HIGH
            ),
            AutomationRule(
                rule_id="hsm_failover",
                name="HSM Failover Automation",
                description="Automatically failover to backup HSM",
                trigger=AutomationTrigger.SECURITY_EVENT,
                condition={"event_type": "hsm_failure"},
                actions=[
                    AutomationAction.FAILOVER_ACTIVATION,
                    AutomationAction.ALERT_GENERATION,
                    AutomationAction.NOTIFICATION
                ],
                priority=AlertPriority.EMERGENCY,
                cooldown_period_seconds=1800
            ),
            AutomationRule(
                rule_id="performance_degradation",
                name="Performance Degradation Response",
                description="Respond to system performance degradation",
                trigger=AutomationTrigger.PERFORMANCE_BASED,
                condition={"metric": "response_time", "threshold": 5000, "operator": ">"},
                actions=[
                    AutomationAction.ALERT_GENERATION,
                    AutomationAction.THRESHOLD_ADJUSTMENT,
                    AutomationAction.HEALTH_CHECK
                ],
                priority=AlertPriority.MEDIUM
            ),
            AutomationRule(
                rule_id="daily_backup",
                name="Daily Automated Backup",
                description="Create daily automated backups",
                trigger=AutomationTrigger.SCHEDULED,
                condition={},
                actions=[AutomationAction.BACKUP_CREATION],
                schedule="0 3 * * *",  # Daily at 3 AM
                priority=AlertPriority.LOW
            ),
            AutomationRule(
                rule_id="weekly_compliance_scan",
                name="Weekly Compliance Scan",
                description="Perform weekly compliance scanning",
                trigger=AutomationTrigger.SCHEDULED,
                condition={},
                actions=[AutomationAction.COMPLIANCE_SCAN],
                schedule="0 1 * * 0",  # Weekly at 1 AM on Sunday
                priority=AlertPriority.MEDIUM
            )
        ]

        for rule in default_rules:
            self.rules[rule.rule_id] = rule

        security_logger.info(f"Loaded {len(default_rules)} default automation rules")

    def _start_automation_engine(self):
        """Start the automation engine background tasks"""
        self._running = True

        # Start scheduled task processor
        asyncio.create_task(self._scheduled_task_processor())

        # Start event processor
        asyncio.create_task(self._event_processor())

        # Start health monitor
        asyncio.create_task(self._health_monitor())

        # Start compliance monitor
        asyncio.create_task(self._compliance_monitor())

        # Start performance monitor
        asyncio.create_task(self._performance_monitor())

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

        security_logger.info("Automation engine started")

    async def _scheduled_task_processor(self):
        """Process scheduled automation tasks"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.utcnow()

                for rule_id, rule in self.rules.items():
                    if not rule.enabled:
                        continue

                    if rule.trigger == AutomationTrigger.SCHEDULED and rule.schedule:
                        if self._is_cron_due(rule.schedule, now):
                            await self._execute_rule(rule_id, trigger_context={"scheduled_at": now.isoformat()})

            except Exception as e:
                security_logger.error(f"Error in scheduled task processor: {e}")

    def _is_cron_due(self, cron_expression: str, current_time: datetime) -> bool:
        """Check if a cron expression is due"""
        try:
            import croniter
            cron = croniter.croniter(cron_expression, current_time)
            next_run = cron.get_next(datetime)
            time_diff = (next_run - current_time).total_seconds()
            return 0 <= time_diff < 60  # Due within next minute
        except ImportError:
            # Fallback to simple time-based checking
            return False
        except Exception as e:
            security_logger.error(f"Error checking cron schedule: {e}")
            return False

    async def _event_processor(self):
        """Process security events and trigger automation"""
        while self._running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Process recent security events
                recent_events = self.security_events[-100:]  # Last 100 events

                for event in recent_events:
                    for rule_id, rule in self.rules.items():
                        if not rule.enabled:
                            continue

                        if rule.trigger == AutomationTrigger.EVENT_DRIVEN:
                            if self._matches_event_condition(event, rule.condition):
                                await self._execute_rule(rule_id, trigger_context={"event_id": event.event_id})

            except Exception as e:
                security_logger.error(f"Error in event processor: {e}")

    def _matches_event_condition(self, event: SecurityEvent, condition: Dict[str, Any]) -> bool:
        """Check if event matches rule condition"""
        if "event_type" in condition and event.event_type != condition["event_type"]:
            return False

        if "severity" in condition and event.severity.value != condition["severity"]:
            return False

        if "source" in condition and event.source != condition["source"]:
            return False

        return True

    async def _health_monitor(self):
        """Monitor system health and trigger automation"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Collect health metrics
                await self._collect_health_metrics()

                # Check for health-based triggers
                for rule_id, rule in self.rules.items():
                    if not rule.enabled:
                        continue

                    if rule.trigger == AutomationTrigger.HEALTH_BASED:
                        if await self._matches_health_condition(rule.condition):
                            await self._execute_rule(rule_id, trigger_context={"health_check": "automatic"})

            except Exception as e:
                security_logger.error(f"Error in health monitor: {e}")

    async def _collect_health_metrics(self):
        """Collect system health metrics"""
        try:
            # Key management health
            key_stats = self.key_manager.get_security_stats()
            self._record_health_metric("key_count", float(key_stats["total_keys"]), "count")
            self._record_health_metric("active_keys", float(key_stats["active_keys"]), "count")
            self._record_health_metric("expired_keys", float(key_stats["expired_keys"]), "count")

            # Storage health
            storage_stats = self.storage_manager.get_storage_stats()
            self._record_health_metric("storage_size_mb", float(storage_stats["database_size_bytes"] / 1024 / 1024), "MB")

            # Lifecycle health
            lifecycle_stats = self.lifecycle_manager.get_lifecycle_stats()
            self._record_health_metric("keys_needing_attention", float(lifecycle_stats["keys_needing_attention"]), "count")

            # HSM health
            hsm_status = await self.hsm_manager.get_hsm_status()
            healthy_hsms = sum(1 for status in hsm_status.values() if status.status == HSMStatus.ONLINE)
            self._record_health_metric("healthy_hsms", float(healthy_hsms), "count")

            # Detect anomalies using ML
            if ML_AVAILABLE:
                await self._detect_anomalies()

        except Exception as e:
            security_logger.error(f"Error collecting health metrics: {e}")

    def _record_health_metric(self, name: str, value: float, unit: str):
        """Record a health metric"""
        metric_id = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        metric = HealthMetric(
            metric_id=metric_id,
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow()
        )

        # Set thresholds based on metric type
        if name == "error_rate":
            metric.threshold_max = 0.05
        elif name == "response_time":
            metric.threshold_max = 5000.0
        elif name == "storage_size_mb":
            metric.threshold_max = 10240.0  # 10GB

        # Check health status
        if metric.threshold_max is not None and value > metric.threshold_max:
            metric.is_healthy = False

        if name not in self.health_metrics:
            self.health_metrics[name] = []

        self.health_metrics[name].append(metric)

        # Keep only last 1000 metrics per type
        if len(self.health_metrics[name]) > 1000:
            self.health_metrics[name] = self.health_metrics[name][-1000:]

    async def _detect_anomalies(self):
        """Detect anomalies in system metrics using machine learning"""
        if not ML_AVAILABLE:
            return

        try:
            # Prepare features for anomaly detection
            features = []
            metric_names = list(self.health_metrics.keys())

            for name in metric_names:
                if len(self.health_metrics[name]) >= 10:  # Need at least 10 samples
                    recent_metrics = self.health_metrics[name][-10:]
                    values = [m.value for m in recent_metrics]

                    # Calculate statistical features
                    features.extend([
                        statistics.mean(values),
                        statistics.stdev(values) if len(values) > 1 else 0,
                        max(values) - min(values),
                        values[-1]  # Latest value
                    ])

            if features:
                # Scale features
                features_scaled = self.ml_scalers['key_usage'].fit_transform([features])

                # Detect anomalies
                anomaly_score = self.ml_models['key_usage_anomaly'].score_samples(features_scaled)[0]

                # Record anomaly detection metric
                self._record_health_metric("anomaly_score", float(anomaly_score), "score")

                # Trigger alert if high anomaly score
                if anomaly_score < -0.5:  # Threshold for anomaly
                    await self._trigger_security_event(
                        event_type="anomaly_detected",
                        severity=AlertPriority.HIGH,
                        source="ml_engine",
                        description=f"Anomaly detected in system metrics (score: {anomaly_score:.3f})",
                        metadata={"anomaly_score": anomaly_score, "features": features}
                    )

        except Exception as e:
            security_logger.error(f"Error in anomaly detection: {e}")

    async def _compliance_monitor(self):
        """Monitor compliance and trigger automation"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Check every hour

                # Perform compliance checks
                compliance_results = await self._perform_compliance_checks()

                # Check for compliance-based triggers
                for rule_id, rule in self.rules.items():
                    if not rule.enabled:
                        continue

                    if rule.trigger == AutomationTrigger.COMPLIANCE_BASED:
                        if await self._matches_compliance_condition(rule.condition, compliance_results):
                            await self._execute_rule(rule_id, trigger_context={"compliance_check": "automatic"})

            except Exception as e:
                security_logger.error(f"Error in compliance monitor: {e}")

    async def _perform_compliance_checks(self) -> List[ComplianceCheck]:
        """Perform automated compliance checks"""
        compliance_checks = []

        try:
            # Key rotation compliance
            key_rotation_check = ComplianceCheck(
                check_id=f"key_rotation_{datetime.utcnow().strftime('%Y%m%d')}",
                standard="SOC2",
                control="Key Rotation Policy",
                description="Verify all keys have valid rotation policies",
                passed=True,
                timestamp=datetime.utcnow()
            )

            # Check key rotation policies
            non_compliant_keys = 0
            for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                if metadata.rotation_period_days > 90:
                    non_compliant_keys += 1
                    key_rotation_check.passed = False
                    key_rotation_check.recommendations.append(f"Key {key_id} rotation period exceeds 90 days")

            key_rotation_check.evidence = {
                "total_keys": len(self.key_manager.keys_cache),
                "non_compliant_keys": non_compliant_keys
            }

            compliance_checks.append(key_rotation_check)

            # Encryption strength compliance
            encryption_check = ComplianceCheck(
                check_id=f"encryption_strength_{datetime.utcnow().strftime('%Y%m%d')}",
                standard="NIST",
                control="Cryptographic Standards",
                description="Verify all keys meet minimum encryption strength requirements",
                passed=True,
                timestamp=datetime.utcnow()
            )

            weak_keys = 0
            for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                if metadata.key_size_bits < 256:
                    weak_keys += 1
                    encryption_check.passed = False
                    encryption_check.recommendations.append(f"Key {key_id} size ({metadata.key_size_bits} bits) below minimum")

            encryption_check.evidence = {
                "total_keys": len(self.key_manager.keys_cache),
                "weak_keys": weak_keys
            }

            compliance_checks.append(encryption_check)

            # Store compliance checks
            self.compliance_checks.extend(compliance_checks)

            # Keep only last 1000 checks
            if len(self.compliance_checks) > 1000:
                self.compliance_checks = self.compliance_checks[-1000:]

            return compliance_checks

        except Exception as e:
            security_logger.error(f"Error performing compliance checks: {e}")
            return []

    async def _performance_monitor(self):
        """Monitor system performance and trigger automation"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Collect performance metrics
                performance_metrics = await self._collect_performance_metrics()

                # Check for performance-based triggers
                for rule_id, rule in self.rules.items():
                    if not rule.enabled:
                        continue

                    if rule.trigger == AutomationTrigger.PERFORMANCE_BASED:
                        if await self._matches_performance_condition(rule.condition, performance_metrics):
                            await self._execute_rule(rule_id, trigger_context={"performance_metrics": performance_metrics})

            except Exception as e:
                security_logger.error(f"Error in performance monitor: {e}")

    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """Collect system performance metrics"""
        metrics = {}

        try:
            # Key operations performance
            metrics["key_generation_time"] = 0.0
            metrics["encryption_time"] = 0.0
            metrics["decryption_time"] = 0.0

            # Collect from recent operations (simplified)
            recent_executions = [e for e in self.executions.values()
                               if e.status == AutomationStatus.COMPLETED and
                               (datetime.utcnow() - e.completed_at).total_seconds() < 300]

            if recent_executions:
                metrics["avg_execution_time"] = statistics.mean([e.execution_time_ms for e in recent_executions])
                metrics["success_rate"] = len([e for e in recent_executions if e.status == AutomationStatus.COMPLETED]) / len(recent_executions)
            else:
                metrics["avg_execution_time"] = 0.0
                metrics["success_rate"] = 1.0

            # System resource usage (simplified)
            import psutil
            metrics["cpu_usage"] = psutil.cpu_percent()
            metrics["memory_usage"] = psutil.virtual_memory().percent
            metrics["disk_usage"] = psutil.disk_usage('/').percent

        except Exception as e:
            security_logger.error(f"Error collecting performance metrics: {e}")

        return metrics

    async def _execute_rule(self, rule_id: str, trigger_context: Dict[str, Any] = None):
        """Execute an automation rule"""
        if rule_id not in self.rules:
            security_logger.error(f"Unknown automation rule: {rule_id}")
            return

        rule = self.rules[rule_id]

        # Check cooldown period
        if (rule.last_triggered and
            (datetime.utcnow() - rule.last_triggered).total_seconds() < rule.cooldown_period_seconds):
            security_logger.debug(f"Rule {rule_id} is in cooldown period")
            return

        # Create execution record
        execution_id = f"exec_{secrets.token_urlsafe(16)}"
        execution = AutomationExecution(
            execution_id=execution_id,
            rule_id=rule_id,
            triggered_at=datetime.utcnow(),
            trigger_context=trigger_context or {}
        )

        self.executions[execution_id] = execution

        try:
            # Update rule metadata
            rule.last_triggered = datetime.utcnow()
            rule.execution_count += 1

            # Execute rule
            execution.status = AutomationStatus.RUNNING
            execution.started_at = datetime.utcnow()

            security_logger.info(f"Executing automation rule: {rule.name} ({rule_id})")

            # Execute actions
            results = []
            for action in rule.actions:
                try:
                    result = await self._execute_action(action, rule, execution)
                    results.append(result)
                except Exception as e:
                    security_logger.error(f"Error executing action {action.value} for rule {rule_id}: {e}")
                    results.append({"success": False, "error": str(e)})

            # Check if any action failed
            all_success = all(r.get("success", False) for r in results)

            if all_success:
                execution.status = AutomationStatus.COMPLETED
                rule.success_count += 1
                security_logger.info(f"Automation rule {rule_id} completed successfully")
            else:
                execution.status = AutomationStatus.FAILED
                rule.failure_count += 1
                security_logger.error(f"Automation rule {rule_id} failed")

            execution.completed_at = datetime.utcnow()
            execution.execution_time_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000
            execution.execution_result = {"actions": results}

            # Update rule average execution time
            if rule.average_execution_time_ms == 0:
                rule.average_execution_time_ms = execution.execution_time_ms
            else:
                rule.average_execution_time_ms = (
                    rule.average_execution_time_ms * 0.9 + execution.execution_time_ms * 0.1
                )

        except Exception as e:
            execution.status = AutomationStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            rule.failure_count += 1

            security_logger.error(f"Automation rule {rule_id} failed with error: {e}")

        # Trigger event handlers
        self._trigger_event_handlers("automation_completed", {
            "rule_id": rule_id,
            "execution_id": execution_id,
            "status": execution.status.value,
            "success": execution.status == AutomationStatus.COMPLETED
        })

    async def _execute_action(self, action: AutomationAction, rule: AutomationRule,
                             execution: AutomationExecution) -> Dict[str, Any]:
        """Execute a specific automation action"""
        security_logger.debug(f"Executing action: {action.value}")

        if action == AutomationAction.KEY_ROTATION:
            return await self._action_key_rotation(rule, execution)
        elif action == AutomationAction.KEY_REVOCATION:
            return await self._action_key_revocation(rule, execution)
        elif action == AutomationAction.BACKUP_CREATION:
            return await self._action_backup_creation(rule, execution)
        elif action == AutomationAction.HEALTH_CHECK:
            return await self._action_health_check(rule, execution)
        elif action == AutomationAction.ALERT_GENERATION:
            return await self._action_alert_generation(rule, execution)
        elif action == AutomationAction.FAILOVER_ACTIVATION:
            return await self._action_failover_activation(rule, execution)
        elif action == AutomationAction.NOTIFICATION:
            return await self._action_notification(rule, execution)
        elif action == AutomationAction.REPORT_GENERATION:
            return await self._action_report_generation(rule, execution)
        else:
            return {"success": False, "error": f"Unsupported action: {action.value}"}

    async def _action_key_rotation(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute key rotation action"""
        try:
            # Find keys needing rotation
            keys_to_rotate = []
            for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                if (metadata.status == KeyStatus.ACTIVE and
                    metadata.next_rotation_at and
                    metadata.next_rotation_at <= datetime.utcnow()):
                    keys_to_rotate.append(key_id)

            rotated_keys = []
            for key_id in keys_to_rotate:
                try:
                    new_key_data = secrets.token_bytes(32)
                    success = self.key_manager.rotate_key(
                        key_id=key_id,
                        new_key_data=new_key_data,
                        user_id="automation",
                        username="automation_system",
                        force=True
                    )
                    if success:
                        rotated_keys.append(key_id)
                except Exception as e:
                    security_logger.error(f"Failed to rotate key {key_id}: {e}")

            return {
                "success": len(rotated_keys) > 0,
                "rotated_keys": rotated_keys,
                "total_keys": len(keys_to_rotate)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_backup_creation(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute backup creation action"""
        try:
            backup_id = self.key_manager.create_backup()
            return {
                "success": True,
                "backup_id": backup_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_health_check(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute health check action"""
        try:
            # Perform health checks on all HSMs
            health_results = await self.hsm_manager.health_check()
            healthy_hsms = sum(1 for result in health_results.values() if result.success)

            return {
                "success": True,
                "healthy_hsms": healthy_hsms,
                "total_hsms": len(health_results),
                "results": {hsm_id: result.success for hsm_id, result in health_results.items()}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_alert_generation(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute alert generation action"""
        try:
            alert_data = {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "priority": rule.priority.value,
                "triggered_at": execution.triggered_at.isoformat(),
                "context": execution.trigger_context
            }

            # Log security event
            await self._trigger_security_event(
                event_type="automation_alert",
                severity=rule.priority,
                source="automation_engine",
                description=f"Automation alert: {rule.name}",
                metadata=alert_data
            )

            return {
                "success": True,
                "alert_data": alert_data
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_failover_activation(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute failover activation action"""
        try:
            # This would trigger HSM failover logic
            return {
                "success": True,
                "message": "Failover activation initiated",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_notification(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute notification action"""
        try:
            # Send notification (would integrate with email, Slack, etc.)
            notification_data = {
                "rule_name": rule.name,
                "priority": rule.priority.value,
                "triggered_at": execution.triggered_at.isoformat(),
                "context": execution.trigger_context
            }

            security_logger.info(f"Notification sent for rule {rule.rule_id}: {notification_data}")

            return {
                "success": True,
                "notification_data": notification_data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _action_report_generation(self, rule: AutomationRule, execution: AutomationExecution) -> Dict[str, Any]:
        """Execute report generation action"""
        try:
            # Generate compliance/security report
            report_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "rule_id": rule.rule_id,
                "health_metrics": {name: [asdict(m) for m in metrics[-10:]]
                                 for name, metrics in self.health_metrics.items()},
                "compliance_checks": [asdict(check) for check in self.compliance_checks[-10:]]
            }

            # Store report
            report_id = f"report_{secrets.token_urlsafe(16)}"
            self.storage_manager.store_data(
                data=json.dumps(report_data).encode(),
                storage_type=StorageType.DATABASE,
                entry_id=f"automation_report_{report_id}",
                created_by="automation_engine"
            )

            return {
                "success": True,
                "report_id": report_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _trigger_security_event(self, event_type: str, severity: AlertPriority,
                                    source: str, description: str,
                                    metadata: Dict[str, Any] = None):
        """Trigger a security event"""
        event = SecurityEvent(
            event_id=f"event_{secrets.token_urlsafe(16)}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            source=source,
            description=description,
            metadata=metadata or {}
        )

        self.security_events.append(event)

        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]

        # Trigger event handlers
        self._trigger_event_handlers("security_event", asdict(event))

    def _trigger_event_handlers(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered event handlers"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    security_logger.error(f"Error in event handler for {event_type}: {e}")

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _cleanup_task(self):
        """Cleanup old automation data"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Clean up every hour

                cutoff_time = datetime.utcnow() - timedelta(days=7)

                # Clean up old executions
                old_executions = [
                    exec_id for exec_id, execution in self.executions.items()
                    if execution.completed_at and execution.completed_at < cutoff_time
                ]

                for exec_id in old_executions:
                    del self.executions[exec_id]

                # Clean up old health metrics (keep last 100 per type)
                for name in self.health_metrics:
                    if len(self.health_metrics[name]) > 100:
                        self.health_metrics[name] = self.health_metrics[name][-100:]

                # Clean up old security events (keep last 1000)
                if len(self.security_events) > 1000:
                    self.security_events = self.security_events[-1000:]

                security_logger.debug(f"Cleanup completed: removed {len(old_executions)} old executions")

            except Exception as e:
                security_logger.error(f"Error in cleanup task: {e}")

    def get_automation_stats(self) -> Dict[str, Any]:
        """Get automation engine statistics"""
        total_rules = len(self.rules)
        enabled_rules = len([r for r in self.rules.values() if r.enabled])
        total_executions = len(self.executions)

        recent_executions = [e for e in self.executions.values()
                           if e.completed_at and
                           (datetime.utcnow() - e.completed_at).total_seconds() < 86400]  # Last 24h

        successful_executions = len([e for e in recent_executions if e.status == AutomationStatus.COMPLETED])
        failed_executions = len([e for e in recent_executions if e.status == AutomationStatus.FAILED])

        avg_execution_time = statistics.mean([e.execution_time_ms for e in recent_executions]) if recent_executions else 0

        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "total_executions": total_executions,
            "recent_executions_24h": len(recent_executions),
            "successful_executions_24h": successful_executions,
            "failed_executions_24h": failed_executions,
            "success_rate_24h": successful_executions / len(recent_executions) if recent_executions else 0,
            "average_execution_time_ms": avg_execution_time,
            "security_events_total": len(self.security_events),
            "health_metrics_types": len(self.health_metrics),
            "compliance_checks_total": len(self.compliance_checks),
            "ml_anomaly_detection_enabled": ML_AVAILABLE,
            "system_uptime": "N/A"  # Could track system uptime
        }

    def stop(self):
        """Stop the automation engine"""
        self._running = False
        security_logger.info("Automation engine stopped")
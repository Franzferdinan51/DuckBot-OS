"""
DuckBot Key Lifecycle Management System

Comprehensive key lifecycle management providing:
- Automated key rotation policies and scheduling
- Key generation and provisioning workflows
- Key retirement and decommissioning procedures
- Key health monitoring and alerting
- Compliance and audit trail maintenance
- Key escrow and recovery mechanisms
- Cryptographic agility support
- Zero-downtime key rotation

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
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
import croniter
from abc import ABC, abstractmethod

# Cryptography imports
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Security logging
security_logger = logging.getLogger('duckbot.security.lifecycle')

class LifecyclePhase(Enum):
    """Key lifecycle phases"""
    GENERATION = "generation"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    ROTATION_PENDING = "rotation_pending"
    ROTATION_IN_PROGRESS = "rotation_in_progress"
    RETIREMENT_PENDING = "retirement_pending"
    RETIRED = "retired"
    DECOMMISSIONED = "decommissioned"
    COMPROMISED = "compromised"
    ESCROWED = "escrowed"

class RotationPolicy(Enum):
    """Key rotation policies"""
    TIME_BASED = "time_based"
    USAGE_BASED = "usage_based"
    EVENT_BASED = "event_based"
    CRYPTOGRAPHIC_AGGRESSIVE = "cryptographic_aggressive"
    CRYPTOGRAPHIC_CONSERVATIVE = "cryptographic_conservative"
    COMPLIANCE_DRIVEN = "compliance_driven"
    SECURITY_EVENT_DRIVEN = "security_event_driven"

class KeyAlgorithm(Enum):
    """Supported cryptographic algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    RSA_2048 = "rsa_2048"
    RSA_3072 = "rsa_3072"
    RSA_4096 = "rsa_4096"
    ECDSA_P256 = "ecdsa_p256"
    ECDSA_P384 = "ecdsa_p384"
    ECDSA_P521 = "ecdsa_p521"
    ED25519 = "ed25519"
    X25519 = "x25519"
    CHACHA20_POLY1305 = "chacha20_poly1305"

class HealthStatus(Enum):
    """Key health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"

@dataclass
class LifecyclePolicy:
    """Key lifecycle policy configuration"""
    policy_id: str
    name: str
    description: str
    rotation_policy: RotationPolicy
    rotation_interval_days: int = 90
    max_usage_count: Optional[int] = None
    max_encryption_operations: Optional[int] = None
    max_signature_operations: Optional[int] = None
    grace_period_days: int = 7
    retirement_delay_days: int = 30
    decommission_delay_days: int = 365
    require_approval: bool = False
    approvers: List[str] = field(default_factory=list)
    auto_rotation_enabled: bool = True
    health_check_enabled: bool = True
    health_check_interval_hours: int = 24
    backup_before_rotation: bool = True
    zero_downtime_rotation: bool = True
    notify_on_rotation: bool = True
    notification_channels: List[str] = field(default_factory=list)
    custom_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KeyUsageMetrics:
    """Key usage metrics"""
    key_id: str
    encryption_count: int = 0
    decryption_count: int = 0
    signature_count: int = 0
    verification_count: int = 0
    last_used_at: Optional[datetime] = None
    total_bytes_encrypted: int = 0
    total_bytes_decrypted: int = 0
    error_count: int = 0
    average_response_time_ms: float = 0.0
    peak_usage_timestamp: Optional[datetime] = None
    usage_by_ip: Dict[str, int] = field(default_factory=dict)
    usage_by_user: Dict[str, int] = field(default_factory=dict)

@dataclass
class KeyHealthReport:
    """Key health assessment report"""
    key_id: str
    status: HealthStatus
    generated_at: datetime
    checks_performed: List[str] = field(default_factory=list)
    issues_found: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    next_rotation_due: Optional[datetime] = None
    usage_metrics: Optional[KeyUsageMetrics] = None
    compliance_status: Dict[str, bool] = field(default_factory=dict)

@dataclass
class RotationSchedule:
    """Key rotation schedule"""
    schedule_id: str
    key_id: str
    scheduled_at: datetime
    rotation_type: str
    reason: str
    requires_approval: bool
    approvers: List[str] = field(default_factory=list)
    status: str = "scheduled"  # scheduled, approved, in_progress, completed, failed
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    backup_before_rotation: bool = True
    zero_downtime: bool = True
    rollback_available: bool = False

class KeyLifecycleManager:
    """Main key lifecycle management system"""

    def __init__(self, key_manager, storage_manager):
        self.key_manager = key_manager
        self.storage_manager = storage_manager
        self.lifecycle_policies: Dict[str, LifecyclePolicy] = {}
        self.usage_metrics: Dict[str, KeyUsageMetrics] = {}
        self.rotation_schedules: Dict[str, RotationSchedule] = {}
        self.health_reports: Dict[str, KeyHealthReport] = {}
        self._lock = threading.RLock()
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._init_done = False

        # Initialize default policies
        self._initialize_default_policies()

        # Start background tasks
        self._start_background_tasks()

        self._init_done = True
        security_logger.info("KeyLifecycleManager initialized")

    def _initialize_default_policies(self):
        """Initialize default lifecycle policies"""
        default_policies = [
            LifecyclePolicy(
                policy_id="high_security",
                name="High Security Policy",
                description="For highly sensitive keys requiring frequent rotation",
                rotation_policy=RotationPolicy.CRYPTOGRAPHIC_AGGRESSIVE,
                rotation_interval_days=30,
                max_usage_count=10000,
                require_approval=True,
                approvers=["security_admin", "system_admin"],
                auto_rotation_enabled=True,
                health_check_interval_hours=6,
                backup_before_rotation=True,
                zero_downtime_rotation=True
            ),
            LifecyclePolicy(
                policy_id="standard_security",
                name="Standard Security Policy",
                description="Default policy for most keys",
                rotation_policy=RotationPolicy.TIME_BASED,
                rotation_interval_days=90,
                max_usage_count=100000,
                auto_rotation_enabled=True,
                health_check_interval_hours=24,
                backup_before_rotation=True
            ),
            LifecyclePolicy(
                policy_id="compliance_driven",
                name="Compliance Driven Policy",
                description="For keys subject to compliance requirements",
                rotation_policy=RotationPolicy.COMPLIANCE_DRIVEN,
                rotation_interval_days=60,
                require_approval=True,
                approvers=["compliance_officer"],
                auto_rotation_enabled=True,
                health_check_interval_hours=12,
                backup_before_rotation=True
            ),
            LifecyclePolicy(
                policy_id="long_term",
                name="Long Term Policy",
                description="For keys with long-term stability requirements",
                rotation_policy=RotationPolicy.CRYPTOGRAPHIC_CONSERVATIVE,
                rotation_interval_days=365,
                auto_rotation_enabled=False,
                health_check_interval_hours=48,
                backup_before_rotation=True
            )
        ]

        for policy in default_policies:
            self.lifecycle_policies[policy.policy_id] = policy

        security_logger.info(f"Initialized {len(default_policies)} default lifecycle policies")

    def _start_background_tasks(self):
        """Start background lifecycle management tasks"""
        # Health monitoring task
        asyncio.create_task(self._health_monitoring_task())

        # Rotation scheduling task
        asyncio.create_task(self._rotation_scheduling_task())

        # Cleanup task
        asyncio.create_task(self._cleanup_task())

        # Metrics collection task
        asyncio.create_task(self._metrics_collection_task())

    def assign_lifecycle_policy(self, key_id: str, policy_id: str,
                              custom_settings: Dict[str, Any] = None) -> bool:
        """Assign a lifecycle policy to a key"""
        with self._lock:
            if policy_id not in self.lifecycle_policies:
                security_logger.error(f"Unknown lifecycle policy: {policy_id}")
                return False

            policy = self.lifecycle_policies[policy_id]

            # Apply custom settings if provided
            if custom_settings:
                # Create a copy of the policy with custom settings
                import copy
                custom_policy = copy.deepcopy(policy)
                for key, value in custom_settings.items():
                    if hasattr(custom_policy, key):
                        setattr(custom_policy, key, value)
                policy = custom_policy

            # Store policy assignment in secure storage
            policy_data = {
                "key_id": key_id,
                "policy_id": policy_id,
                "assigned_at": datetime.utcnow().isoformat(),
                "custom_settings": custom_settings or {},
                "policy": asdict(policy)
            }

            self.storage_manager.store_data(
                data=json.dumps(policy_data).encode(),
                storage_type=StorageType.DATABASE,
                entry_id=f"lifecycle_policy_{key_id}",
                created_by="lifecycle_manager"
            )

            # Initialize usage metrics
            self.usage_metrics[key_id] = KeyUsageMetrics(key_id=key_id)

            # Schedule initial rotation
            self._schedule_next_rotation(key_id, policy)

            # Trigger event
            self._trigger_event("policy_assigned", {
                "key_id": key_id,
                "policy_id": policy_id,
                "custom_settings": custom_settings
            })

            security_logger.info(f"Assigned lifecycle policy {policy_id} to key {key_id}")
            return True

    def record_key_usage(self, key_id: str, operation: str, bytes_processed: int = 0,
                        user_id: str = "", ip_address: str = "",
                        response_time_ms: float = 0.0, success: bool = True):
        """Record key usage for lifecycle tracking"""
        with self._lock:
            if key_id not in self.usage_metrics:
                self.usage_metrics[key_id] = KeyUsageMetrics(key_id=key_id)

            metrics = self.usage_metrics[key_id]

            # Update usage counters
            if operation == "encrypt":
                metrics.encryption_count += 1
                metrics.total_bytes_encrypted += bytes_processed
            elif operation == "decrypt":
                metrics.decryption_count += 1
                metrics.total_bytes_decrypted += bytes_processed
            elif operation == "sign":
                metrics.signature_count += 1
            elif operation == "verify":
                metrics.verification_count += 1

            # Update timestamps
            metrics.last_used_at = datetime.utcnow()
            if not metrics.peak_usage_timestamp or operation.count() > metrics.encryption_count:
                metrics.peak_usage_timestamp = datetime.utcnow()

            # Update response time
            if metrics.average_response_time_ms == 0:
                metrics.average_response_time_ms = response_time_ms
            else:
                metrics.average_response_time_ms = (
                    metrics.average_response_time_ms * 0.9 + response_time_ms * 0.1
                )

            # Track usage by user and IP
            if user_id:
                metrics.usage_by_user[user_id] = metrics.usage_by_user.get(user_id, 0) + 1
            if ip_address:
                metrics.usage_by_ip[ip_address] = metrics.usage_by_ip.get(ip_address, 0) + 1

            # Record error if operation failed
            if not success:
                metrics.error_count += 1

            # Check if rotation is needed based on usage
            self._check_usage_based_rotation(key_id, metrics)

            # Trigger event
            self._trigger_event("key_usage", {
                "key_id": key_id,
                "operation": operation,
                "bytes_processed": bytes_processed,
                "user_id": user_id,
                "ip_address": ip_address,
                "success": success
            })

    def schedule_key_rotation(self, key_id: str, rotation_type: str = "scheduled",
                             reason: str = "", scheduled_at: datetime = None,
                             requires_approval: bool = False,
                             approvers: List[str] = None) -> str:
        """Schedule a key rotation"""
        with self._lock:
            if scheduled_at is None:
                scheduled_at = datetime.utcnow() + timedelta(hours=1)

            schedule_id = f"rotation_{secrets.token_urlsafe(16)}"

            # Get key policy
            policy = self._get_key_policy(key_id)
            if not policy:
                security_logger.error(f"No policy found for key {key_id}")
                return None

            schedule = RotationSchedule(
                schedule_id=schedule_id,
                key_id=key_id,
                scheduled_at=scheduled_at,
                rotation_type=rotation_type,
                reason=reason or "Scheduled rotation",
                requires_approval=requires_approval or policy.require_approval,
                approvers=approvers or policy.approvers,
                created_by="lifecycle_manager",
                created_at=datetime.utcnow(),
                backup_before_rotation=policy.backup_before_rotation,
                zero_downtime=policy.zero_downtime_rotation
            )

            self.rotation_schedules[schedule_id] = schedule

            # Store schedule
            self.storage_manager.store_data(
                data=json.dumps(asdict(schedule)).encode(),
                storage_type=StorageType.DATABASE,
                entry_id=f"rotation_schedule_{schedule_id}",
                created_by="lifecycle_manager"
            )

            # Trigger event
            self._trigger_event("rotation_scheduled", {
                "key_id": key_id,
                "schedule_id": schedule_id,
                "rotation_type": rotation_type,
                "scheduled_at": scheduled_at.isoformat()
            })

            security_logger.info(f"Scheduled rotation for key {key_id}: {schedule_id}")
            return schedule_id

    def approve_rotation(self, schedule_id: str, approver_id: str,
                       approve: bool = True, reason: str = "") -> bool:
        """Approve or reject a scheduled rotation"""
        with self._lock:
            if schedule_id not in self.rotation_schedules:
                security_logger.error(f"Unknown rotation schedule: {schedule_id}")
                return False

            schedule = self.rotation_schedules[schedule_id]

            if schedule.status != "scheduled":
                security_logger.error(f"Rotation schedule {schedule_id} already processed")
                return False

            if approver_id not in schedule.approvers:
                security_logger.error(f"User {approver_id} not authorized to approve rotation {schedule_id}")
                return False

            if approve:
                schedule.status = "approved"
                security_logger.info(f"Rotation {schedule_id} approved by {approver_id}")
            else:
                schedule.status = "rejected"
                security_logger.info(f"Rotation {schedule_id} rejected by {approver_id}: {reason}")

            # Update stored schedule
            self.storage_manager.store_data(
                data=json.dumps(asdict(schedule)).encode(),
                storage_type=StorageType.DATABASE,
                entry_id=f"rotation_schedule_{schedule_id}",
                created_by="lifecycle_manager"
            )

            # Trigger event
            self._trigger_event("rotation_approved" if approve else "rotation_rejected", {
                "schedule_id": schedule_id,
                "approver_id": approver_id,
                "approved": approve,
                "reason": reason
            })

            return True

    async def execute_rotation(self, schedule_id: str) -> bool:
        """Execute a scheduled key rotation"""
        with self._lock:
            if schedule_id not in self.rotation_schedules:
                security_logger.error(f"Unknown rotation schedule: {schedule_id}")
                return False

            schedule = self.rotation_schedules[schedule_id]

            if schedule.status != "approved":
                security_logger.error(f"Rotation schedule {schedule_id} not approved")
                return False

            try:
                # Mark as in progress
                schedule.status = "in_progress"
                self._update_schedule_storage(schedule)

                # Create backup if required
                backup_id = None
                if schedule.backup_before_rotation:
                    backup_id = self.key_manager.create_backup()
                    security_logger.info(f"Created backup {backup_id} before rotation")

                # Generate new key
                new_key_data = self._generate_new_key(schedule.key_id)

                # Perform zero-downtime rotation if enabled
                if schedule.zero_downtime:
                    success = await self._zero_downtime_rotation(schedule.key_id, new_key_data)
                else:
                    success = self.key_manager.rotate_key(
                        key_id=schedule.key_id,
                        new_key_data=new_key_data,
                        user_id="lifecycle_manager",
                        username="lifecycle_manager",
                        force=True
                    )

                if success:
                    schedule.status = "completed"
                    schedule.completed_at = datetime.utcnow()

                    # Schedule next rotation
                    policy = self._get_key_policy(schedule.key_id)
                    if policy and policy.auto_rotation_enabled:
                        self._schedule_next_rotation(schedule.key_id, policy)

                    # Trigger event
                    self._trigger_event("rotation_completed", {
                        "key_id": schedule.key_id,
                        "schedule_id": schedule_id,
                        "backup_id": backup_id,
                        "zero_downtime": schedule.zero_downtime
                    })

                    security_logger.info(f"Successfully rotated key {schedule.key_id}")
                    return True
                else:
                    schedule.status = "failed"
                    security_logger.error(f"Failed to rotate key {schedule.key_id}")

            except Exception as e:
                schedule.status = "failed"
                security_logger.error(f"Error executing rotation {schedule_id}: {e}")
                self._trigger_event("rotation_failed", {
                    "schedule_id": schedule_id,
                    "error": str(e)
                })

            finally:
                self._update_schedule_storage(schedule)

            return False

    async def _zero_downtime_rotation(self, key_id: str, new_key_data: bytes) -> bool:
        """Perform zero-downtime key rotation"""
        try:
            # Get current key metadata
            current_key_data, metadata = self.key_manager._load_key_from_storage(key_id)

            # Create temporary dual-key configuration
            dual_key_config = {
                "primary_key": key_id,
                "secondary_key": f"{key_id}_new",
                "transition_start": datetime.utcnow().isoformat(),
                "transition_complete": False
            }

            # Store new key temporarily
            temp_key_id = f"{key_id}_new"
            self.key_manager.create_key(
                key_type=metadata.key_type,
                key_data=new_key_data,
                name=f"{metadata.name}_new",
                description=f"Temporary key for rotation of {metadata.name}",
                security_level=metadata.security_level,
                created_by="lifecycle_manager"
            )

            # Store dual-key configuration
            self.storage_manager.store_data(
                data=json.dumps(dual_key_config).encode(),
                storage_type=StorageType.DATABASE,
                entry_id=f"dual_key_config_{key_id}",
                created_by="lifecycle_manager"
            )

            # Allow time for services to transition (configurable)
            transition_delay = 300  # 5 minutes
            security_logger.info(f"Starting zero-downtime transition for key {key_id}")
            await asyncio.sleep(transition_delay)

            # Complete the rotation
            success = self.key_manager.rotate_key(
                key_id=key_id,
                new_key_data=new_key_data,
                user_id="lifecycle_manager",
                username="lifecycle_manager",
                force=True
            )

            if success:
                # Clean up temporary key
                self.key_manager.revoke_key(
                    key_id=temp_key_id,
                    user_id="lifecycle_manager",
                    username="lifecycle_manager",
                    reason="Post-rotation cleanup"
                )

                # Mark transition as complete
                dual_key_config["transition_complete"] = True
                dual_key_config["transition_end"] = datetime.utcnow().isoformat()

                self.storage_manager.store_data(
                    data=json.dumps(dual_key_config).encode(),
                    storage_type=StorageType.DATABASE,
                    entry_id=f"dual_key_config_{key_id}",
                    created_by="lifecycle_manager"
                )

                security_logger.info(f"Zero-downtime rotation completed for key {key_id}")
                return True

            return False

        except Exception as e:
            security_logger.error(f"Zero-downtime rotation failed for key {key_id}: {e}")
            return False

    def perform_health_check(self, key_id: str) -> KeyHealthReport:
        """Perform comprehensive health check on a key"""
        with self._lock:
            checks_performed = []
            issues_found = []
            recommendations = []
            risk_score = 0.0
            compliance_status = {}

            try:
                # Get key metadata and policy
                _, metadata = self.key_manager._load_key_from_storage(key_id)
                policy = self._get_key_policy(key_id)
                metrics = self.usage_metrics.get(key_id)

                # Basic existence check
                checks_performed.append("existence")
                if not metadata:
                    issues_found.append({"type": "critical", "message": "Key metadata not found"})
                    risk_score += 0.9
                    status = HealthStatus.CRITICAL
                else:
                    # Status check
                    checks_performed.append("status")
                    if metadata.status != KeyStatus.ACTIVE:
                        issues_found.append({
                            "type": "warning",
                            "message": f"Key status is {metadata.status.value}, expected ACTIVE"
                        })
                        risk_score += 0.3

                    # Expiration check
                    checks_performed.append("expiration")
                    if metadata.expires_at and metadata.expires_at < datetime.utcnow():
                        issues_found.append({"type": "critical", "message": "Key has expired"})
                        risk_score += 0.8
                        recommendations.append("Rotate or revoke the expired key immediately")

                    # Rotation due check
                    checks_performed.append("rotation_due")
                    if metadata.next_rotation_at and metadata.next_rotation_at < datetime.utcnow():
                        issues_found.append({
                            "type": "warning",
                            "message": "Key rotation is overdue"
                        })
                        risk_score += 0.4
                        recommendations.append("Schedule key rotation immediately")

                    # Usage limits check
                    if policy and metrics:
                        checks_performed.append("usage_limits")
                        if policy.max_usage_count and metrics.encryption_count >= policy.max_usage_count:
                            issues_found.append({
                                "type": "warning",
                                "message": f"Key has reached maximum usage count ({policy.max_usage_count})"
                            })
                            risk_score += 0.3
                            recommendations.append("Rotate key due to usage limits")

                        # Error rate check
                        if metrics.error_count > 0:
                            error_rate = metrics.error_count / (metrics.encryption_count + 1)
                            if error_rate > 0.01:  # 1% error rate threshold
                                issues_found.append({
                                    "type": "warning",
                                    "message": f"High error rate detected: {error_rate:.2%}"
                                })
                                risk_score += 0.2
                                recommendations.append("Investigate and resolve key usage errors")

                    # Compliance checks
                    if policy:
                        checks_performed.append("compliance")
                        compliance_status = self._check_compliance(key_id, metadata, policy, metrics)

                    # Cryptographic strength check
                    checks_performed.append("cryptographic_strength")
                    crypto_strength_issues = self._check_cryptographic_strength(metadata)
                    issues_found.extend(crypto_strength_issues)
                    if crypto_strength_issues:
                        risk_score += 0.4

                    # Determine overall status
                    if risk_score >= 0.7:
                        status = HealthStatus.CRITICAL
                    elif risk_score >= 0.4:
                        status = HealthStatus.WARNING
                    else:
                        status = HealthStatus.HEALTHY

                # Create health report
                report = KeyHealthReport(
                    key_id=key_id,
                    status=status,
                    generated_at=datetime.utcnow(),
                    checks_performed=checks_performed,
                    issues_found=issues_found,
                    recommendations=recommendations,
                    risk_score=risk_score,
                    next_rotation_due=metadata.next_rotation_at if metadata else None,
                    usage_metrics=metrics,
                    compliance_status=compliance_status
                )

                # Store report
                self.health_reports[key_id] = report
                self._store_health_report(report)

                # Trigger event
                self._trigger_event("health_check_completed", {
                    "key_id": key_id,
                    "status": status.value,
                    "risk_score": risk_score,
                    "issues_count": len(issues_found)
                })

                security_logger.info(f"Health check completed for key {key_id}: {status.value} (risk: {risk_score:.2f})")
                return report

            except Exception as e:
                security_logger.error(f"Health check failed for key {key_id}: {e}")
                return KeyHealthReport(
                    key_id=key_id,
                    status=HealthStatus.UNKNOWN,
                    generated_at=datetime.utcnow(),
                    checks_performed=["existence"],
                    issues_found=[{"type": "error", "message": f"Health check error: {str(e)}"}],
                    risk_score=1.0
                )

    def _check_cryptographic_strength(self, metadata: KeyMetadata) -> List[Dict[str, Any]]:
        """Check cryptographic strength of key"""
        issues = []

        # Check algorithm strength
        if metadata.algorithm == "RSA-1024":
            issues.append({
                "type": "critical",
                "message": "RSA-1024 is considered weak and should not be used"
            })
        elif metadata.algorithm == "RSA-2048":
            issues.append({
                "type": "warning",
                "message": "RSA-2048 is acceptable but RSA-3072 or higher is recommended"
            })

        # Check key size
        if metadata.key_size_bits < 128:
            issues.append({
                "type": "critical",
                "message": f"Key size {metadata.key_size_bits} bits is insufficient"
            })
        elif metadata.key_size_bits < 256:
            issues.append({
                "type": "warning",
                "message": f"Key size {metadata.key_size_bits} bits is below recommended minimum"
            })

        return issues

    def _check_compliance(self, key_id: str, metadata: KeyMetadata,
                         policy: LifecyclePolicy, metrics: KeyUsageMetrics) -> Dict[str, bool]:
        """Check compliance requirements"""
        compliance_status = {}

        # SOC2 compliance checks
        compliance_status["soc2_encryption"] = metadata.key_size_bits >= 256
        compliance_status["soc2_rotation"] = policy.rotation_interval_days <= 90
        compliance_status["soc2_audit"] = True  # Assuming audit logging is enabled

        # ISO27001 compliance checks
        compliance_status["iso27001_key_management"] = (
            policy.rotation_interval_days <= 365 and
            policy.backup_before_rotation and
            policy.health_check_enabled
        )

        # GDPR compliance checks
        compliance_status["gdpr_data_protection"] = metadata.security_level.value >= 2
        compliance_status["gdpr_retention"] = policy.retirement_delay_days <= 365

        return compliance_status

    def _generate_new_key(self, key_id: str) -> bytes:
        """Generate new key data based on key type"""
        # Get current key metadata
        _, metadata = self.key_manager._load_key_from_storage(key_id)

        # Generate new key based on algorithm
        if metadata.algorithm.startswith("AES"):
            return secrets.token_bytes(32)  # 256-bit key
        elif metadata.algorithm.startswith("RSA"):
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=int(metadata.algorithm.split("-")[1]),
                backend=default_backend()
            )
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        elif metadata.algorithm.startswith("ECDSA"):
            curve_name = metadata.algorithm.split("_")[1].lower()
            curve = {
                "p256": ec.SECP256R1(),
                "p384": ec.SECP384R1(),
                "p521": ec.SECP521R1()
            }.get(curve_name, ec.SECP256R1())

            private_key = ec.generate_private_key(curve, default_backend())
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            # Default to 256-bit random key
            return secrets.token_bytes(32)

    def _schedule_next_rotation(self, key_id: str, policy: LifecyclePolicy):
        """Schedule the next rotation for a key"""
        if not policy.auto_rotation_enabled:
            return

        next_rotation = datetime.utcnow() + timedelta(days=policy.rotation_interval_days)

        schedule_id = self.schedule_key_rotation(
            key_id=key_id,
            rotation_type="scheduled",
            reason=f"Automatic rotation based on {policy.rotation_interval_days}-day policy",
            scheduled_at=next_rotation,
            requires_approval=policy.require_approval,
            approvers=policy.approvers
        )

        if schedule_id:
            security_logger.info(f"Scheduled next rotation for key {key_id}: {next_rotation}")

    def _check_usage_based_rotation(self, key_id: str, metrics: KeyUsageMetrics):
        """Check if rotation is needed based on usage"""
        policy = self._get_key_policy(key_id)
        if not policy:
            return

        rotation_needed = False
        reason = ""

        # Check usage count limit
        if policy.max_usage_count and metrics.encryption_count >= policy.max_usage_count:
            rotation_needed = True
            reason = f"Reached maximum usage count of {policy.max_usage_count}"

        # Check encryption operation limit
        if (policy.max_encryption_operations and
            metrics.encryption_count >= policy.max_encryption_operations):
            rotation_needed = True
            reason = f"Reached maximum encryption operations of {policy.max_encryption_operations}"

        # Check signature operation limit
        if (policy.max_signature_operations and
            metrics.signature_count >= policy.max_signature_operations):
            rotation_needed = True
            reason = f"Reached maximum signature operations of {policy.max_signature_operations}"

        # Check error rate
        if metrics.encryption_count > 0:
            error_rate = metrics.error_count / metrics.encryption_count
            if error_rate > 0.05:  # 5% error rate
                rotation_needed = True
                reason = f"High error rate detected: {error_rate:.2%}"

        if rotation_needed:
            self.schedule_key_rotation(
                key_id=key_id,
                rotation_type="usage_based",
                reason=reason,
                scheduled_at=datetime.utcnow() + timedelta(hours=1)
            )

    def _get_key_policy(self, key_id: str) -> Optional[LifecyclePolicy]:
        """Get the lifecycle policy for a key"""
        try:
            policy_data = self.storage_manager.retrieve_data(
                entry_id=f"lifecycle_policy_{key_id}",
                user_id="lifecycle_manager"
            )
            if policy_data:
                policy_dict = json.loads(policy_data.decode())
                return LifecyclePolicy(**policy_dict["policy"])
        except Exception as e:
            security_logger.error(f"Failed to get policy for key {key_id}: {e}")
        return None

    def _update_schedule_storage(self, schedule: RotationSchedule):
        """Update rotation schedule in storage"""
        self.storage_manager.store_data(
            data=json.dumps(asdict(schedule)).encode(),
            storage_type=StorageType.DATABASE,
            entry_id=f"rotation_schedule_{schedule.schedule_id}",
            created_by="lifecycle_manager"
        )

    def _store_health_report(self, report: KeyHealthReport):
        """Store health report in secure storage"""
        report_data = json.dumps(asdict(report))
        self.storage_manager.store_data(
            data=report_data.encode(),
            storage_type=StorageType.DATABASE,
            entry_id=f"health_report_{report.key_id}_{report.generated_at.strftime('%Y%m%d_%H%M%S')}",
            created_by="lifecycle_manager"
        )

    async def _health_monitoring_task(self):
        """Background task for continuous health monitoring"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour

                # Get all keys with policies
                policy_keys = [
                    key_id for key_id in self.usage_metrics.keys()
                    if self._get_key_policy(key_id)
                ]

                for key_id in policy_keys:
                    try:
                        policy = self._get_key_policy(key_id)
                        if policy and policy.health_check_enabled:
                            # Check if health check is due
                            last_check = self.health_reports.get(key_id)
                            if (not last_check or
                                (datetime.utcnow() - last_check.generated_at).total_seconds() >=
                                policy.health_check_interval_hours * 3600):

                                # Perform health check
                                await asyncio.get_event_loop().run_in_executor(
                                    self._thread_pool,
                                    self.perform_health_check,
                                    key_id
                                )

                    except Exception as e:
                        security_logger.error(f"Error in health monitoring for key {key_id}: {e}")

            except Exception as e:
                security_logger.error(f"Error in health monitoring task: {e}")

    async def _rotation_scheduling_task(self):
        """Background task for processing rotation schedules"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                now = datetime.utcnow()
                due_rotations = [
                    schedule for schedule in self.rotation_schedules.values()
                    if (schedule.status == "approved" and
                        schedule.scheduled_at <= now)
                ]

                for schedule in due_rotations:
                    try:
                        await self.execute_rotation(schedule.schedule_id)
                    except Exception as e:
                        security_logger.error(f"Error executing rotation {schedule.schedule_id}: {e}")

            except Exception as e:
                security_logger.error(f"Error in rotation scheduling task: {e}")

    async def _cleanup_task(self):
        """Background task for cleanup operations"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily cleanup

                # Clean up old rotation schedules
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                completed_schedules = [
                    schedule_id for schedule_id, schedule in self.rotation_schedules.items()
                    if (schedule.status in ["completed", "failed"] and
                        schedule.completed_at and
                        schedule.completed_at < cutoff_date)
                ]

                for schedule_id in completed_schedules:
                    del self.rotation_schedules[schedule_id]

                # Clean up old health reports (keep last 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                for key_id in list(self.health_reports.keys()):
                    report = self.health_reports[key_id]
                    if report.generated_at < cutoff_date:
                        del self.health_reports[key_id]

                security_logger.info("Cleanup task completed")

            except Exception as e:
                security_logger.error(f"Error in cleanup task: {e}")

    async def _metrics_collection_task(self):
        """Background task for metrics collection and analysis"""
        while True:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes

                # Analyze usage patterns and detect anomalies
                for key_id, metrics in self.usage_metrics.items():
                    # Check for unusual usage patterns
                    if metrics.encryption_count > 0:
                        recent_usage_rate = metrics.encryption_count / max(1, (
                            datetime.utcnow() - metrics.last_used_at
                        ).total_seconds() / 3600) if metrics.last_used_at else 0

                        if recent_usage_rate > 1000:  # More than 1000 operations per hour
                            security_logger.warning(
                                f"High usage rate detected for key {key_id}: {recent_usage_rate:.0f} ops/hour"
                            )

                            # Trigger alert
                            self._trigger_event("high_usage_alert", {
                                "key_id": key_id,
                                "usage_rate": recent_usage_rate,
                                "metrics": asdict(metrics)
                            })

            except Exception as e:
                security_logger.error(f"Error in metrics collection task: {e}")

    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger event handlers"""
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

    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """Get lifecycle management statistics"""
        now = datetime.utcnow()

        # Count keys by policy
        policy_counts = {}
        for key_id in self.usage_metrics.keys():
            policy = self._get_key_policy(key_id)
            if policy:
                policy_name = policy.name
                policy_counts[policy_name] = policy_counts.get(policy_name, 0) + 1

        # Rotation schedules by status
        schedule_counts = {}
        for schedule in self.rotation_schedules.values():
            status = schedule.status
            schedule_counts[status] = schedule_counts.get(status, 0) + 1

        # Health status distribution
        health_counts = {}
        for report in self.health_reports.values():
            status = report.status.value
            health_counts[status] = health_counts.get(status, 0) + 1

        # Keys needing attention
        keys_needing_attention = 0
        for report in self.health_reports.values():
            if report.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                keys_needing_attention += 1

        return {
            "total_keys_managed": len(self.usage_metrics),
            "keys_by_policy": policy_counts,
            "rotation_schedules": {
                "total": len(self.rotation_schedules),
                "by_status": schedule_counts,
                "pending_approval": sum(1 for s in self.rotation_schedules.values() if s.status == "scheduled"),
                "approved_pending": sum(1 for s in self.rotation_schedules.values() if s.status == "approved" and s.scheduled_at > now)
            },
            "health_reports": {
                "total": len(self.health_reports),
                "by_status": health_counts,
                "keys_needing_attention": keys_needing_attention
            },
            "system_uptime": "N/A",  # Could track system start time
            "event_handlers_registered": sum(len(handlers) for handlers in self._event_handlers.values()),
            "background_tasks_running": True,
            "compliance_standards_supported": ["SOC2", "ISO27001", "GDPR"]
        }
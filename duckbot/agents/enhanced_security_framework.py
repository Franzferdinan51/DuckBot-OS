"""
Enhanced Security Framework with AP2-inspired Authorization
Advanced mandate-based security system for agent authorization and access control

Features:
- Mandate-based authorization system
- Dynamic permission management
- Agent-specific security policies
- Advanced audit logging
- Threat detection and prevention
- Secure agent communication
- Role-based access control (RBAC) enhancement
- Zero-trust architecture principles

Author: Enhanced Security Framework Module
Version: 1.0.0
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import hashlib
import hmac
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import ipaddress
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Enhanced security levels"""
    PUBLIC = 0
    RESTRICTED = 1
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4
    SYSTEM_CRITICAL = 5

class MandateType(Enum):
    """Types of security mandates"""
    TASK_EXECUTION = "task_execution"
    DATA_ACCESS = "data_access"
    SYSTEM_CONFIG = "system_config"
    AGENT_CONTROL = "agent_control"
    NETWORK_ACCESS = "network_access"
    RESOURCE_ALLOCATION = "resource_allocation"
    SECURITY_ADMIN = "security_admin"
    USER_DATA = "user_data"
    EXTERNAL_COMMUNICATION = "external_communication"

class PermissionScope(Enum):
    """Permission scope levels"""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    TEAM = "team"
    PROJECT = "project"
    AGENT = "agent"
    TASK = "task"

class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(Enum):
    """Enhanced security event types"""
    # Authentication events
    AGENT_AUTH_SUCCESS = "agent_auth_success"
    AGENT_AUTH_FAILURE = "agent_auth_failure"
    MANDATE_GRANTED = "mandate_granted"
    MANDATE_REVOKED = "mandate_revoked"
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # Authorization events
    MANDATE_VALIDATION_SUCCESS = "mandate_validation_success"
    MANDATE_VALIDATION_FAILURE = "mandate_validation_failure"
    AUTHORIZATION_CHECK_SUCCESS = "authorization_check_success"
    AUTHORIZATION_CHECK_FAILURE = "authorization_check_failure"

    # Threat detection events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    THREAT_DETECTED = "threat_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    POLICY_VIOLATION = "policy_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Agent communication events
    AGENT_COMMUNICATION = "agent_communication"
    AGENT_COLLABORATION = "agent_collaboration"
    DATA_SHARING = "data_sharing"
    RESOURCE_ACCESS = "resource_access"

@dataclass
class SecurityMandate:
    """AP2-inspired security mandate"""
    id: str
    grantee_id: str  # Agent or user ID
    grantor_id: str  # Authority granting the mandate
    mandate_type: MandateType
    permissions: List[str]
    scope: PermissionScope
    scope_id: Optional[str] = None  # Specific scope identifier
    conditions: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)

    # Temporal constraints
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    max_uses: Optional[int] = None
    use_count: int = 0

    # Delegation
    allow_delegation: bool = False
    delegated_from: Optional[str] = None

    # Audit and revocation
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str
    last_used: Optional[datetime] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None

    # Security level
    security_level: SecurityLevel = SecurityLevel.RESTRICTED

    def is_valid(self) -> bool:
        """Check if mandate is currently valid"""
        now = datetime.now()

        # Check temporal validity
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False

        # Check revocation status
        if self.revoked:
            return False

        # Check usage limits
        if self.max_uses and self.use_count >= self.max_uses:
            return False

        # Check conditions
        if not self._check_conditions():
            return False

        return True

    def _check_conditions(self) -> bool:
        """Check mandate conditions"""
        # Time-based conditions
        if "time_windows" in self.conditions:
            current_time = datetime.now()
            allowed_windows = self.conditions["time_windows"]
            current_window = f"{current_time.hour:02d}:{current_time.minute:02d}"

            if not any(window[0] <= current_window <= window[1] for window in allowed_windows):
                return False

        # IP-based conditions
        if "allowed_ips" in self.conditions:
            # IP checking would be done at validation time with actual IP
            pass

        # Resource-based conditions
        if "max_resources" in self.constraints:
            # Resource checking would be done at validation time
            pass

        return True

    def can_delegate(self) -> bool:
        """Check if mandate can be delegated"""
        return self.allow_delegation and not self.revoked

    def record_use(self):
        """Record mandate usage"""
        self.use_count += 1
        self.last_used = datetime.now()

@dataclass
class SecurityContext:
    """Enhanced security context for agents"""
    context_id: str
    principal_id: str  # Agent or user ID
    principal_type: str  # "agent", "user", "system"
    authentication_method: str
    authentication_strength: float  # 0.0 to 1.0

    # Mandates and permissions
    active_mandates: List[str] = field(default_factory=list)
    effective_permissions: Set[str] = field(default_factory=set)
    roles: List[str] = field(default_factory=list)

    # Session information
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)

    # Security attributes
    security_level: SecurityLevel = SecurityLevel.RESTRICTED
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None

    # Risk assessment
    risk_score: float = 0.0  # 0.0 to 1.0
    trust_level: float = 0.5  # 0.0 to 1.0

    def is_valid(self) -> bool:
        """Check if security context is valid"""
        now = datetime.now()

        # Check expiration
        if self.expires_at and now > self.expires_at:
            return False

        # Check session timeout (30 minutes of inactivity)
        if (now - self.last_activity).total_seconds() > 1800:
            return False

        # Check risk level
        if self.risk_score > 0.8:
            return False

        return True

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission"""
        return permission in self.effective_permissions

    def add_mandate(self, mandate_id: str, mandate_permissions: List[str]):
        """Add mandate to security context"""
        if mandate_id not in self.active_mandates:
            self.active_mandates.append(mandate_id)
            self.effective_permissions.update(mandate_permissions)

@dataclass
class SecurityPolicy:
    """Comprehensive security policy"""
    id: str
    name: str
    description: str
    version: str
    enabled: bool = True

    # Authentication policies
    mfa_required: bool = False
    min_password_strength: float = 0.7
    session_timeout: timedelta = timedelta(hours=1)
    max_concurrent_sessions: int = 5

    # Authorization policies
    default_security_level: SecurityLevel = SecurityLevel.RESTRICTED
    require_mandates: bool = True
    allow_permission_inheritance: bool = True
    delegation_allowed: bool = True

    # Threat prevention
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    enable_ip_reputation: bool = True
    enable_anomaly_detection: bool = True

    # Data protection
    encrypt_sensitive_data: bool = True
    enable_audit_logging: bool = True
    audit_retention_days: int = 365
    data_classification_required: bool = True

    # Network security
    allowed_networks: List[str] = field(default_factory=list)
    blocked_networks: List[str] = field(default_factory=list)
    require_encryption: bool = True

    # Agent-specific policies
    agent_isolation: bool = False
    agent_sandboxing: bool = True
    agent_resource_limits: Dict[str, Any] = field(default_factory=dict)

    # Compliance
    compliance_standards: List[str] = field(default_factory=list)
    regular_audits: bool = True
    audit_frequency_days: int = 30

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    threat_id: str
    threat_type: str
    severity: ThreatLevel
    description: str
    indicators: Dict[str, Any]
    affected_resources: List[str]
    mitigation_steps: List[str]
    detected_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def is_relevant(self) -> bool:
        """Check if threat is still relevant"""
        now = datetime.now()
        return self.expires_at is None or now < self.expires_at

class MandateManager:
    """Manager for security mandates"""

    def __init__(self):
        self.mandates: Dict[str, SecurityMandate] = {}
        self.mandate_index: Dict[str, List[str]] = defaultdict(list)  # grantee_id -> mandate_ids
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)

    async def create_mandate(self, grantee_id: str, grantor_id: str, mandate_type: MandateType,
                           permissions: List[str], scope: PermissionScope, scope_id: str = None,
                           **kwargs) -> SecurityMandate:
        """Create new security mandate"""
        mandate_id = str(uuid.uuid4())

        mandate = SecurityMandate(
            id=mandate_id,
            grantee_id=grantee_id,
            grantor_id=grantor_id,
            mandate_type=mandate_type,
            permissions=permissions,
            scope=scope,
            scope_id=scope_id,
            created_by=grantor_id,
            **kwargs
        )

        # Store mandate
        self.mandates[mandate_id] = mandate
        self.mandate_index[grantee_id].append(mandate_id)

        logger.info(f"Created mandate {mandate_id} for {grantee_id}")
        return mandate

    async def validate_mandate(self, mandate_id: str, context: SecurityContext) -> bool:
        """Validate mandate for given context"""
        mandate = self.mandates.get(mandate_id)
        if not mandate:
            return False

        # Check basic validity
        if not mandate.is_valid():
            return False

        # Check scope validity
        if mandate.scope == PermissionScope.AGENT and mandate.scope_id != context.principal_id:
            return False

        # Check temporal constraints
        if "allowed_times" in mandate.constraints:
            current_time = datetime.now()
            current_hour = current_time.hour
            allowed_hours = mandate.constraints["allowed_times"]
            if current_hour not in allowed_hours:
                return False

        # Check resource constraints
        if "max_cpu_usage" in mandate.constraints:
            # Would check actual resource usage
            pass

        return True

    async def use_mandate(self, mandate_id: str) -> bool:
        """Record mandate usage"""
        mandate = self.mandates.get(mandate_id)
        if not mandate:
            return False

        if mandate.is_valid():
            mandate.record_use()
            return True

        return False

    async def revoke_mandate(self, mandate_id: str, revoked_by: str, reason: str = None):
        """Revoke a mandate"""
        mandate = self.mandates.get(mandate_id)
        if mandate:
            mandate.revoked = True
            mandate.revoked_at = datetime.now()
            mandate.revoked_by = revoked_by
            if reason:
                mandate.constraints["revocation_reason"] = reason

            logger.info(f"Revoked mandate {mandate_id} by {revoked_by}")

    async def get_agent_mandates(self, agent_id: str) -> List[SecurityMandate]:
        """Get all valid mandates for an agent"""
        mandate_ids = self.mandate_index.get(agent_id, [])
        return [self.mandates[mid] for mid in mandate_ids
                if self.mandates[mid].is_valid()]

    async def delegate_mandate(self, mandate_id: str, new_grantee_id: str, delegated_by: str,
                              permissions: List[str] = None) -> Optional[SecurityMandate]:
        """Delegate mandate to another agent"""
        original_mandate = self.mandates.get(mandate_id)
        if not original_mandate or not original_mandate.can_delegate():
            return None

        # Create delegated mandate
        delegated_permissions = permissions or original_mandate.permissions
        delegated_mandate = await self.create_mandate(
            grantee_id=new_grantee_id,
            grantor_id=delegated_by,
            mandate_type=original_mandate.mandate_type,
            permissions=delegated_permissions,
            scope=original_mandate.scope,
            scope_id=original_mandate.scope_id,
            valid_from=datetime.now(),
            valid_until=original_mandate.valid_until,
            delegated_from=mandate_id,
            allow_delegation=False,  # Prevent further delegation by default
            security_level=min(original_mandate.security_level, SecurityLevel.RESTRICTED)
        )

        return delegated_mandate

class AuthorizationEngine:
    """Advanced authorization engine with mandate support"""

    def __init__(self, mandate_manager: MandateManager):
        self.mandate_manager = mandate_manager
        self.policies: Dict[str, SecurityPolicy] = {}
        self.permission_mapping: Dict[str, List[str]] = {}
        self.role_permissions: Dict[str, List[str]] = {}

    async def check_permission(self, context: SecurityContext, permission: str,
                             resource: str = None, action: str = None) -> bool:
        """Check if context has permission for action on resource"""
        # Update context activity
        context.update_activity()

        # Check basic context validity
        if not context.is_valid():
            return False

        # Check direct permissions
        if context.has_permission(permission):
            return True

        # Check mandate-based permissions
        for mandate_id in context.active_mandates:
            mandate = self.mandate_manager.mandates.get(mandate_id)
            if mandate and await self.mandate_manager.validate_mandate(mandate_id, context):
                if permission in mandate.permissions:
                    # Record mandate usage
                    await self.mandate_manager.use_mandate(mandate_id)
                    return True

        # Check role-based permissions
        for role in context.roles:
            if role in self.role_permissions:
                if permission in self.role_permissions[role]:
                    return True

        # Check implicit permissions based on security level
        if self._has_implicit_permission(context, permission):
            return True

        return False

    async def request_permission(self, context: SecurityContext, permission: str,
                               reason: str = None, duration: timedelta = None) -> bool:
        """Request temporary permission"""
        # Check if permission can be granted
        if await self._can_grant_permission(context, permission):
            # Create temporary mandate
            mandate = await self.mandate_manager.create_mandate(
                grantee_id=context.principal_id,
                grantor_id="system",  # System-granted
                mandate_type=MandateType.TASK_EXECUTION,
                permissions=[permission],
                scope=PermissionScope.AGENT,
                scope_id=context.principal_id,
                valid_until=datetime.now() + (duration or timedelta(hours=1)),
                conditions={"auto_granted": True, "reason": reason},
                security_level=SecurityLevel.RESTRICTED
            )

            # Add to context
            context.add_mandate(mandate.id, mandate.permissions)

            logger.info(f"Granted temporary permission {permission} to {context.principal_id}")
            return True

        return False

    async def _can_grant_permission(self, context: SecurityContext, permission: str) -> bool:
        """Check if permission can be granted to context"""
        # Check context trust level
        if context.trust_level < 0.3:
            return False

        # Check risk score
        if context.risk_score > 0.6:
            return False

        # Check permission sensitivity
        sensitive_permissions = [
            "security_admin", "system_config", "user_data", "agent_control"
        ]
        if permission in sensitive_permissions and context.security_level.value < SecurityLevel.SECRET.value:
            return False

        return True

    def _has_implicit_permission(self, context: SecurityContext, permission: str) -> bool:
        """Check for implicit permissions based on security level"""
        security_level_permissions = {
            SecurityLevel.PUBLIC: ["read_public"],
            SecurityLevel.RESTRICTED: ["read_restricted"],
            SecurityLevel.CONFIDENTIAL: ["read_confidential", "write_restricted"],
            SecurityLevel.SECRET: ["read_secret", "write_confidential"],
            SecurityLevel.TOP_SECRET: ["read_top_secret", "write_secret"],
            SecurityLevel.SYSTEM_CRITICAL: ["system_critical", "write_top_secret"]
        }

        return permission in security_level_permissions.get(context.security_level, [])

class ThreatDetector:
    """Advanced threat detection system"""

    def __init__(self):
        self.threat_intelligence: Dict[str, ThreatIntelligence] = {}
        self.behavioral_patterns: Dict[str, Any] = {}
        self.anomaly_thresholds: Dict[str, float] = {
            "failed_login_attempts": 5,
            "permission_denials": 10,
            "suspicious_requests": 20,
            "resource_usage": 0.9
        }

    async def analyze_activity(self, context: SecurityContext, activity: Dict[str, Any]) -> List[ThreatIntelligence]:
        """Analyze activity for potential threats"""
        threats = []

        # Check for failed authentication attempts
        if activity.get("type") == "auth_failure":
            failed_attempts = activity.get("failed_attempts", 0)
            if failed_attempts > self.anomaly_thresholds["failed_login_attempts"]:
                threats.append(ThreatIntelligence(
                    threat_id=f"brute_force_{context.principal_id}",
                    threat_type="brute_force",
                    severity=ThreatLevel.HIGH,
                    description=f"Multiple failed authentication attempts for {context.principal_id}",
                    indicators={"failed_attempts": failed_attempts, "ip": context.ip_address},
                    affected_resources=[context.principal_id],
                    mitigation_steps=["Block IP address", "Enable CAPTCHA", "Implement rate limiting"]
                ))

        # Check for permission denial patterns
        if activity.get("type") == "permission_denied":
            permission_denials = activity.get("denial_count", 0)
            if permission_denials > self.anomaly_thresholds["permission_denials"]:
                threats.append(ThreatIntelligence(
                    threat_id=f"privilege_escalation_{context.principal_id}",
                    threat_type="privilege_escalation",
                    severity=ThreatLevel.MEDIUM,
                    description=f"Excessive permission denial attempts by {context.principal_id}",
                    indicators={"denial_count": permission_denials},
                    affected_resources=[context.principal_id],
                    mitigation_steps=["Review user permissions", "Enable additional authentication"]
                ))

        # Check for unusual resource usage
        if activity.get("type") == "resource_usage":
            cpu_usage = activity.get("cpu_usage", 0)
            memory_usage = activity.get("memory_usage", 0)

            if cpu_usage > self.anomaly_thresholds["resource_usage"] or memory_usage > self.anomaly_thresholds["resource_usage"]:
                threats.append(ThreatIntelligence(
                    threat_id=f"resource_abuse_{context.principal_id}",
                    threat_type="resource_abuse",
                    severity=ThreatLevel.MEDIUM,
                    description=f"Unusual resource usage by {context.principal_id}",
                    indicators={"cpu_usage": cpu_usage, "memory_usage:": memory_usage},
                    affected_resources=[context.principal_id],
                    mitigation_steps=["Implement resource quotas", "Monitor system performance"]
                ))

        # Check for suspicious network activity
        if activity.get("type") == "network_activity":
            request_rate = activity.get("requests_per_minute", 0)
            if request_rate > self.anomaly_thresholds["suspicious_requests"]:
                threats.append(ThreatIntelligence(
                    threat_id=f"dos_attempt_{context.principal_id}",
                    threat_type="dos_attempt",
                    severity=ThreatLevel.HIGH,
                    description=f"High request rate from {context.principal_id}",
                    indicators={"requests_per_minute": request_rate, "ip": context.ip_address},
                    affected_resources=[context.principal_id],
                    mitigation_steps=["Implement rate limiting", "Block suspicious IPs"]
                ))

        return threats

    async def add_threat_intelligence(self, threat: ThreatIntelligence):
        """Add threat intelligence data"""
        self.threat_intelligence[threat.threat_id] = threat

    async def get_active_threats(self) -> List[ThreatIntelligence]:
        """Get currently active threats"""
        return [threat for threat in self.threat_intelligence.values() if threat.is_relevant()]

class EnhancedSecurityManager:
    """Enhanced security manager with AP2-inspired features"""

    def __init__(self):
        self.mandate_manager = MandateManager()
        self.authorization_engine = AuthorizationEngine(self.mandate_manager)
        self.threat_detector = ThreatDetector()

        # Security contexts
        self.active_contexts: Dict[str, SecurityContext] = {}
        self.context_sessions: Dict[str, str] = {}  # session_id -> context_id

        # Security policies
        self.default_policy = SecurityPolicy(
            id="default",
            name="Default Security Policy",
            description="Default security policy for all agents",
            version="1.0"
        )

        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []
        self.security_events: List[Dict[str, Any]] = []

        # Configuration
        self.encryption_enabled = True
        self.audit_enabled = True
        self.threat_detection_enabled = True

        # Background services
        self.session_cleaner = SessionCleaner(self)
        self.threat_monitor = ThreatMonitor(self)

    async def initialize(self) -> bool:
        """Initialize enhanced security manager"""
        try:
            # Initialize default permissions and roles
            await self._initialize_default_permissions()

            # Start background services
            await self.session_cleaner.start()
            await self.threat_monitor.start()

            logger.info("Enhanced Security Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize enhanced security manager: {e}")
            return False

    async def _initialize_default_permissions(self):
        """Initialize default permissions and roles"""
        # Default role permissions
        self.authorization_engine.role_permissions = {
            "admin": ["system_config", "security_admin", "agent_control", "user_management"],
            "security_admin": ["security_admin", "audit_view", "policy_management"],
            "agent": ["task_execution", "data_access", "resource_allocation"],
            "user": ["basic_access", "read_public"],
            "guest": ["read_public"]
        }

    async def authenticate_agent(self, agent_id: str, credentials: Dict[str, Any],
                              ip_address: str = None) -> Optional[SecurityContext]:
        """Authenticate agent and create security context"""
        # Basic authentication validation
        if not await self._validate_agent_credentials(agent_id, credentials):
            await self._log_security_event(
                SecurityEventType.AGENT_AUTH_FAILURE,
                {"agent_id": agent_id, "ip": ip_address, "reason": "invalid_credentials"}
            )
            return None

        # Create security context
        context_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        context = SecurityContext(
            context_id=context_id,
            principal_id=agent_id,
            principal_type="agent",
            authentication_method="credentials",
            authentication_strength=0.8,  # Basic credential strength
            session_id=session_id,
            ip_address=ip_address,
            security_level=SecurityLevel.RESTRICTED,
            expires_at=datetime.now() + timedelta(hours=1)
        )

        # Load agent mandates
        mandates = await self.mandate_manager.get_agent_mandates(agent_id)
        for mandate in mandates:
            context.add_mandate(mandate.id, mandate.permissions)

        # Store context
        self.active_contexts[context_id] = context
        self.context_sessions[session_id] = context_id

        await self._log_security_event(
            SecurityEventType.AGENT_AUTH_SUCCESS,
            {"agent_id": agent_id, "context_id": context_id, "session_id": session_id}
        )

        logger.info(f"Agent {agent_id} authenticated successfully")
        return context

    async def _validate_agent_credentials(self, agent_id: str, credentials: Dict[str, Any]) -> bool:
        """Validate agent credentials"""
        # This is a simplified implementation
        # In production, this would use proper authentication mechanisms
        required_fields = ["token", "agent_secret"]
        return all(field in credentials for field in required_fields)

    async def authorize_action(self, context: SecurityContext, permission: str,
                             resource: str = None, action: str = None) -> bool:
        """Authorize agent action"""
        is_authorized = await self.authorization_engine.check_permission(
            context, permission, resource, action
        )

        event_type = (SecurityEventType.AUTHORIZATION_CHECK_SUCCESS if is_authorized
                     else SecurityEventType.AUTHORIZATION_CHECK_FAILURE)

        await self._log_security_event(
            event_type,
            {
                "context_id": context.context_id,
                "permission": permission,
                "resource": resource,
                "action": action,
                "authorized": is_authorized
            }
        )

        return is_authorized

    async def create_agent_mandate(self, agent_id: str, permissions: List[str],
                                  scope: PermissionScope = PermissionScope.AGENT,
                                  duration: timedelta = timedelta(hours=24)) -> SecurityMandate:
        """Create mandate for agent"""
        mandate = await self.mandate_manager.create_mandate(
            grantee_id=agent_id,
            grantor_id="system",
            mandate_type=MandateType.TASK_EXECUTION,
            permissions=permissions,
            scope=scope,
            scope_id=agent_id,
            valid_until=datetime.now() + duration,
            security_level=SecurityLevel.RESTRICTED
        )

        # Update active contexts with new mandate
        for context in self.active_contexts.values():
            if context.principal_id == agent_id:
                context.add_mandate(mandate.id, mandate.permissions)

        await self._log_security_event(
            SecurityEventType.MANDATE_GRANTED,
            {"mandate_id": mandate.id, "agent_id": agent_id, "permissions": permissions}
        )

        return mandate

    async def revoke_agent_mandate(self, mandate_id: str, revoked_by: str):
        """Revoke agent mandate"""
        await self.mandate_manager.revoke_mandate(mandate_id, revoked_by)

        # Remove from active contexts
        for context in self.active_contexts.values():
            if mandate_id in context.active_mandates:
                context.active_mandates.remove(mandate_id)

        await self._log_security_event(
            SecurityEventType.MANDATE_REVOKED,
            {"mandate_id": mandate_id, "revoked_by": revoked_by}
        )

    async def detect_threats(self, context: SecurityContext, activity: Dict[str, Any]) -> List[ThreatIntelligence]:
        """Detect threats from agent activity"""
        threats = await self.threat_detector.analyze_activity(context, activity)

        for threat in threats:
            await self.threat_detector.add_threat_intelligence(threat)
            await self._log_security_event(
                SecurityEventType.THREAT_DETECTED,
                {
                    "threat_id": threat.threat_id,
                    "threat_type": threat.threat_type.value,
                    "severity": threat.severity.value,
                    "agent_id": context.principal_id,
                    "context_id": context.context_id
                },
                severity=threat.severity.value
            )

        return threats

    async def _log_security_event(self, event_type: SecurityEventType, details: Dict[str, Any],
                                severity: str = "info"):
        """Log security event"""
        if not self.audit_enabled:
            return

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "details": details
        }

        self.audit_log.append(event)
        self.security_events.append(event)

        # Maintain log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]

        if len(self.security_events) > 5000:
            self.security_events = self.security_events[-2500:]

        # Log to file system
        logger.info(f"Security Event: {event_type.value} - {json.dumps(details, default=str)}")

    async def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        active_threats = await self.threat_detector.get_active_threats()

        return {
            "active_contexts": len(self.active_contexts),
            "total_mandates": len(self.mandate_manager.mandates),
            "active_threats": len(active_threats),
            "threat_levels": {
                threat_level.value: len([t for t in active_threats if t.severity == threat_level])
                for threat_level in ThreatLevel
            },
            "audit_events": len(self.audit_log),
            "policies_enabled": len(self.authorization_engine.policies),
            "encryption_enabled": self.encryption_enabled,
            "threat_detection_enabled": self.threat_detection_enabled
        }

    async def validate_context(self, context_id: str) -> Optional[SecurityContext]:
        """Validate and return security context"""
        context = self.active_contexts.get(context_id)
        if context and context.is_valid():
            context.update_activity()
            return context
        elif context:
            # Remove invalid context
            del self.active_contexts[context_id]
            if context.session_id in self.context_sessions:
                del self.context_sessions[context.session_id]

        return None

class SessionCleaner:
    """Background service for cleaning expired sessions"""

    def __init__(self, security_manager: EnhancedSecurityManager):
        self.security_manager = security_manager
        self.is_running = False

    async def start(self):
        """Start session cleaner"""
        self.is_running = True
        asyncio.create_task(self._cleaning_loop())
        logger.info("Session Cleaner started")

    async def stop(self):
        """Stop session cleaner"""
        self.is_running = False
        logger.info("Session Cleaner stopped")

    async def _cleaning_loop(self):
        """Main cleaning loop"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Clean every 5 minutes

                now = datetime.now()
                expired_contexts = []

                for context_id, context in self.security_manager.active_contexts.items():
                    if not context.is_valid():
                        expired_contexts.append(context_id)

                # Remove expired contexts
                for context_id in expired_contexts:
                    context = self.security_manager.active_contexts.pop(context_id, None)
                    if context and context.session_id in self.security_manager.context_sessions:
                        del self.security_manager.context_sessions[context.session_id]

                if expired_contexts:
                    logger.info(f"Cleaned {len(expired_contexts)} expired security contexts")

            except Exception as e:
                logger.error(f"Error in session cleaning loop: {e}")

class ThreatMonitor:
    """Background threat monitoring service"""

    def __init__(self, security_manager: EnhancedSecurityManager):
        self.security_manager = security_manager
        self.is_running = False

    async def start(self):
        """Start threat monitor"""
        self.is_running = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("Threat Monitor started")

    async def stop(self):
        """Stop threat monitor"""
        self.is_running = False
        logger.info("Threat Monitor stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Monitor every minute

                # Analyze recent security events
                recent_events = [
                    event for event in self.security_manager.security_events[-100:]
                    if datetime.fromisoformat(event["timestamp"]) > datetime.now() - timedelta(minutes=5)
                ]

                if recent_events:
                    # Look for patterns indicating threats
                    await self._analyze_event_patterns(recent_events)

            except Exception as e:
                logger.error(f"Error in threat monitoring loop: {e}")

    async def _analyze_event_patterns(self, events: List[Dict[str, Any]]):
        """Analyze event patterns for threats"""
        # Count events by type
        event_counts = defaultdict(int)
        for event in events:
            event_type = event["event_type"]
            event_counts[event_type] += 1

        # Check for suspicious patterns
        if event_counts.get("permission_denied", 0) > 10:
            logger.warning("Detected pattern of excessive permission denials")

        if event_counts.get("auth_failure", 0) > 5:
            logger.warning("Detected pattern of authentication failures")

# Global enhanced security manager instance
enhanced_security_manager = EnhancedSecurityManager()

# Convenience functions
async def initialize_enhanced_security() -> bool:
    """Initialize enhanced security system"""
    return await enhanced_security_manager.initialize()

async def authenticate_agent(agent_id: str, credentials: Dict[str, Any],
                           ip_address: str = None) -> Optional[SecurityContext]:
    """Authenticate agent with enhanced security"""
    return await enhanced_security_manager.authenticate_agent(agent_id, credentials, ip_address)

async def authorize_agent_action(context: SecurityContext, permission: str,
                              resource: str = None, action: str = None) -> bool:
    """Authorize agent action"""
    return await enhanced_security_manager.authorize_action(context, permission, resource, action)

async def create_agent_mandate(agent_id: str, permissions: List[str],
                             duration: timedelta = timedelta(hours=24)) -> SecurityMandate:
    """Create mandate for agent"""
    return await enhanced_security_manager.create_agent_mandate(agent_id, permissions, duration)

async def get_security_status() -> Dict[str, Any]:
    """Get security system status"""
    return await enhanced_security_manager.get_security_status()

if __name__ == "__main__":
    # Test the enhanced security framework
    import asyncio

    async def test():
        print("Enhanced Security Framework Test")
        print("================================")

        # Initialize security system
        if await initialize_enhanced_security():
            print("✅ Enhanced security system initialized")

            # Test agent authentication
            credentials = {"token": "test_token", "agent_secret": "test_secret"}
            context = await authenticate_agent("test_agent", credentials, "127.0.0.1")
            if context:
                print("✅ Agent authenticated successfully")

                # Test authorization
                is_authorized = await authorize_agent_action(context, "task_execution")
                print(f"✅ Authorization test: {'Authorized' if is_authorized else 'Unauthorized'}")

                # Test mandate creation
                mandate = await create_agent_mandate("test_agent", ["data_access", "resource_allocation"])
                print(f"✅ Mandate created: {mandate.id}")

                # Show security status
                status = await get_security_status()
                print(f"Security Status: {json.dumps(status, indent=2, default=str)}")
            else:
                print("❌ Agent authentication failed")
        else:
            print("❌ Failed to initialize enhanced security system")

    asyncio.run(test())
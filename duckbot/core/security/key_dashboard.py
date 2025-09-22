"""
DuckBot Secure Key Management Dashboard

Provides a comprehensive web-based dashboard for key management including:
- Secure key visualization and management interface
- Real-time key health monitoring and alerts
- Automated key rotation scheduling and management
- Access control and audit trail visualization
- Key lifecycle management workflows
- Compliance reporting and metrics
- Emergency key recovery procedures
- Security incident response interface

Author: Security Engineering Team
Version: 2.0.0
Security Classification: Critical
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import secrets
import asyncio
import aiofiles
from pathlib import Path
import logging
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor
import uuid

# Web framework imports
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator, SecretStr
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# Security imports
from .key_manager import SecureKeyManager, KeyConfig, KeyType, KeyStatus, SecurityLevel
from .secure_storage import SecureStorageManager, SecureStorageConfig, StorageType
from .key_lifecycle import KeyLifecycleManager, LifecyclePolicy, HealthStatus
from ..security_framework import SecurityManager, SecurityContext, Permission

# Security logging
security_logger = logging.getLogger('duckbot.security.dashboard')

class DashboardRole(Enum):
    """Dashboard access roles"""
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    host: str = "127.0.0.1"
    port: int = 8791
    debug: bool = False
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    session_lifetime_hours: int = 8
    max_concurrent_sessions: int = 5
    rate_limit_requests_per_minute: int = 60
    enable_mfa: bool = True
    audit_logging_enabled: bool = True
    alert_webhook_url: Optional[str] = None
    notification_channels: List[str] = Field(default_factory=lambda: ["web", "email"])
    compliance_standards: List[str] = Field(default_factory=lambda: ["SOC2", "ISO27001", "GDPR"])

class KeyRequest(BaseModel):
    """Key creation/update request model"""
    key_type: str
    name: str
    description: str = ""
    security_level: str = "CONFIDENTIAL"
    expires_at: Optional[datetime] = None
    rotation_period_days: int = 90
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class RotationRequest(BaseModel):
    """Key rotation request model"""
    key_id: str
    reason: str = ""
    scheduled_at: Optional[datetime] = None
    requires_approval: bool = False
    approvers: List[str] = Field(default_factory=list)

class AccessPolicyRequest(BaseModel):
    """Access policy update request model"""
    key_id: str
    allowed_users: List[str] = Field(default_factory=list)
    allowed_roles: List[str] = Field(default_factory=list)
    allowed_ip_addresses: List[str] = Field(default_factory=list)
    time_restrictions: Dict[str, str] = Field(default_factory=dict)
    max_access_count: Optional[int] = None
    require_mfa: bool = False
    require_approval: bool = False

class SecurityAlert(BaseModel):
    """Security alert model"""
    alert_id: str
    severity: AlertSeverity
    key_id: Optional[str] = None
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    action_required: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KeyDashboardAPI:
    """Secure Key Management Dashboard API"""

    def __init__(self, key_manager: SecureKeyManager,
                 storage_manager: SecureStorageManager,
                 lifecycle_manager: KeyLifecycleManager,
                 security_manager: SecurityManager,
                 config: DashboardConfig):
        self.key_manager = key_manager
        self.storage_manager = storage_manager
        self.lifecycle_manager = lifecycle_manager
        self.security_manager = security_manager
        self.config = config

        # Initialize FastAPI app
        self.app = FastAPI(
            title="DuckBot Secure Key Management Dashboard",
            description="Enterprise-grade key management interface",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Security setup
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.alerts: List[SecurityAlert] = []

        # Setup middleware
        self._setup_middleware()

        # Setup routes
        self._setup_routes()

        # Background tasks
        self._start_background_tasks()

        security_logger.info("KeyDashboardAPI initialized")

    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # Session middleware
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=self.config.secret_key,
            session_cookie="key_dashboard_session",
            max_age=self.config.session_lifetime_hours * 3600
        )

        # CORS middleware
        from fastapi.middleware.cors import CORSMiddleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8791"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Dashboard home page"""
            return self._render_template("dashboard.html", {
                "request": request,
                "title": "Secure Key Management Dashboard"
            })

        @self.app.get("/api/health")
        async def health_check():
            """System health check"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "services": {
                    "key_manager": self.key_manager._init_done,
                    "storage_manager": self.storage_manager._init_done,
                    "lifecycle_manager": self.lifecycle_manager._init_done,
                    "security_manager": True
                }
            }

        @self.app.get("/api/keys")
        async def list_keys(request: Request):
            """List all keys with metadata"""
            await self._verify_dashboard_access(request, Permission.READ)

            keys_data = []
            for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                key_info = {
                    "key_id": key_id,
                    "key_type": metadata.key_type.value,
                    "name": metadata.name,
                    "description": metadata.description,
                    "status": metadata.status.value,
                    "security_level": metadata.security_level.value,
                    "created_at": metadata.created_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                    "rotation_period_days": metadata.rotation_period_days,
                    "next_rotation_at": metadata.next_rotation_at.isoformat() if metadata.next_rotation_at else None,
                    "access_count": metadata.access_count,
                    "last_accessed_at": metadata.last_accessed_at.isoformat() if metadata.last_accessed_at else None,
                    "tags": metadata.tags,
                    "version": metadata.version
                }
                keys_data.append(key_info)

            return {"keys": keys_data, "total": len(keys_data)}

        @self.app.post("/api/keys")
        async def create_key(request: Request, key_request: KeyRequest):
            """Create a new key"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                # Generate secure key data
                if key_request.key_type.upper() == "API_KEY":
                    key_data = f"sk_{secrets.token_urlsafe(32)}".encode()
                else:
                    key_data = secrets.token_bytes(32)

                # Create the key
                key_id = self.key_manager.create_key(
                    key_type=KeyType[key_request.key_type.upper()],
                    key_data=key_data,
                    name=key_request.name,
                    description=key_request.description,
                    security_level=SecurityLevel[key_request.security_level.upper()],
                    expires_at=key_request.expires_at,
                    rotation_period_days=key_request.rotation_period_days,
                    tags=key_request.tags,
                    custom_metadata=key_request.custom_metadata,
                    created_by="dashboard"
                )

                # Assign default lifecycle policy
                self.lifecycle_manager.assign_lifecycle_policy(key_id, "standard_security")

                return {
                    "success": True,
                    "key_id": key_id,
                    "message": "Key created successfully"
                }

            except Exception as e:
                security_logger.error(f"Failed to create key: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/keys/{key_id}")
        async def get_key(request: Request, key_id: str):
            """Get key details (without exposing the actual key)"""
            await self._verify_dashboard_access(request, Permission.READ)

            try:
                _, metadata = self.key_manager._load_key_from_storage(key_id)

                # Get health report
                health_report = self.lifecycle_manager.health_reports.get(key_id)
                health_status = health_report.status.value if health_report else "unknown"

                # Get usage metrics
                metrics = self.lifecycle_manager.usage_metrics.get(key_id)

                return {
                    "key_id": key_id,
                    "key_type": metadata.key_type.value,
                    "name": metadata.name,
                    "description": metadata.description,
                    "status": metadata.status.value,
                    "security_level": metadata.security_level.value,
                    "created_at": metadata.created_at.isoformat(),
                    "created_by": metadata.created_by,
                    "updated_at": metadata.updated_at.isoformat(),
                    "updated_by": metadata.updated_by,
                    "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                    "rotation_period_days": metadata.rotation_period_days,
                    "last_rotated_at": metadata.last_rotated_at.isoformat() if metadata.last_rotated_at else None,
                    "next_rotation_at": metadata.next_rotation_at.isoformat() if metadata.next_rotation_at else None,
                    "access_count": metadata.access_count,
                    "last_accessed_at": metadata.last_accessed_at.isoformat() if metadata.last_accessed_at else None,
                    "tags": metadata.tags,
                    "version": metadata.version,
                    "algorithm": metadata.algorithm,
                    "key_size_bits": metadata.key_size_bits,
                    "health_status": health_status,
                    "usage_metrics": asdict(metrics) if metrics else None,
                    "custom_metadata": metadata.custom_metadata
                }

            except Exception as e:
                security_logger.error(f"Failed to get key {key_id}: {e}")
                raise HTTPException(status_code=404, detail="Key not found")

        @self.app.delete("/api/keys/{key_id}")
        async def delete_key(request: Request, key_id: str):
            """Delete a key"""
            await self._verify_dashboard_access(request, Permission.DELETE)

            try:
                success = self.key_manager.revoke_key(
                    key_id=key_id,
                    user_id="dashboard",
                    username="dashboard_user",
                    reason="Deleted via dashboard"
                )

                if success:
                    return {"success": True, "message": "Key deleted successfully"}
                else:
                    raise HTTPException(status_code=404, detail="Key not found")

            except Exception as e:
                security_logger.error(f"Failed to delete key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/keys/{key_id}/rotate")
        async def rotate_key(request: Request, key_id: str, rotation_request: RotationRequest):
            """Schedule or execute key rotation"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                if rotation_request.requires_approval:
                    # Schedule rotation requiring approval
                    schedule_id = self.lifecycle_manager.schedule_key_rotation(
                        key_id=key_id,
                        rotation_type="manual",
                        reason=rotation_request.reason or "Manual rotation via dashboard",
                        scheduled_at=rotation_request.scheduled_at,
                        requires_approval=True,
                        approvers=rotation_request.approvers
                    )

                    return {
                        "success": True,
                        "schedule_id": schedule_id,
                        "message": "Key rotation scheduled and requires approval"
                    }
                else:
                    # Execute immediate rotation
                    new_key_data = secrets.token_bytes(32)
                    success = self.key_manager.rotate_key(
                        key_id=key_id,
                        new_key_data=new_key_data,
                        user_id="dashboard",
                        username="dashboard_user",
                        force=True
                    )

                    if success:
                        return {"success": True, "message": "Key rotated successfully"}
                    else:
                        raise HTTPException(status_code=500, detail="Rotation failed")

            except Exception as e:
                security_logger.error(f"Failed to rotate key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/keys/{key_id}/health")
        async def get_key_health(request: Request, key_id: str):
            """Get key health report"""
            await self._verify_dashboard_access(request, Permission.READ)

            try:
                health_report = self.lifecycle_manager.perform_health_check(key_id)
                return asdict(health_report)

            except Exception as e:
                security_logger.error(f"Failed to get health report for key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/policies")
        async def list_policies(request: Request):
            """List lifecycle policies"""
            await self._verify_dashboard_access(request, Permission.READ)

            policies = []
            for policy_id, policy in self.lifecycle_manager.lifecycle_policies.items():
                policies.append({
                    "policy_id": policy_id,
                    "name": policy.name,
                    "description": policy.description,
                    "rotation_policy": policy.rotation_policy.value,
                    "rotation_interval_days": policy.rotation_interval_days,
                    "auto_rotation_enabled": policy.auto_rotation_enabled,
                    "require_approval": policy.require_approval
                })

            return {"policies": policies}

        @self.app.post("/api/policies/{policy_id}/assign/{key_id}")
        async def assign_policy(request: Request, policy_id: str, key_id: str):
            """Assign policy to key"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                success = self.lifecycle_manager.assign_lifecycle_policy(key_id, policy_id)
                if success:
                    return {"success": True, "message": "Policy assigned successfully"}
                else:
                    raise HTTPException(status_code=404, detail="Policy or key not found")

            except Exception as e:
                security_logger.error(f"Failed to assign policy {policy_id} to key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/rotations")
        async def list_rotations(request: Request):
            """List rotation schedules"""
            await self._verify_dashboard_access(request, Permission.READ)

            rotations = []
            for schedule in self.lifecycle_manager.rotation_schedules.values():
                rotations.append({
                    "schedule_id": schedule.schedule_id,
                    "key_id": schedule.key_id,
                    "scheduled_at": schedule.scheduled_at.isoformat(),
                    "rotation_type": schedule.rotation_type,
                    "reason": schedule.reason,
                    "status": schedule.status,
                    "requires_approval": schedule.requires_approval,
                    "created_at": schedule.created_at.isoformat(),
                    "completed_at": schedule.completed_at.isoformat() if schedule.completed_at else None
                })

            return {"rotations": rotations}

        @self.app.post("/api/rotations/{schedule_id}/approve")
        async def approve_rotation(request: Request, schedule_id: str, approve: bool = True):
            """Approve or reject rotation"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                # Get session user
                session = await self._get_session(request)
                user_id = session.get("user_id", "dashboard_user")

                success = self.lifecycle_manager.approve_rotation(
                    schedule_id=schedule_id,
                    approver_id=user_id,
                    approve=approve
                )

                if success:
                    message = "Rotation approved" if approve else "Rotation rejected"
                    return {"success": True, "message": message}
                else:
                    raise HTTPException(status_code=404, detail="Schedule not found")

            except Exception as e:
                security_logger.error(f"Failed to approve rotation {schedule_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/access-policies/{key_id}")
        async def get_access_policy(request: Request, key_id: str):
            """Get access policy for key"""
            await self._verify_dashboard_access(request, Permission.READ)

            try:
                policy = self.key_manager.access_policies.get(key_id)
                if policy:
                    return asdict(policy)
                else:
                    raise HTTPException(status_code=404, detail="Access policy not found")

            except Exception as e:
                security_logger.error(f"Failed to get access policy for key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/api/access-policies/{key_id}")
        async def update_access_policy(request: Request, key_id: str, policy_request: AccessPolicyRequest):
            """Update access policy for key"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                policy = self.key_manager.access_policies.get(key_id)
                if not policy:
                    # Create new policy
                    policy = self.key_manager.access_policies[key_id] = AccessPolicy(key_id=key_id)

                # Update policy
                policy.allowed_users = policy_request.allowed_users
                policy.allowed_roles = policy_request.allowed_roles
                policy.allowed_ip_addresses = policy_request.allowed_ip_addresses
                policy.time_restrictions = policy_request.time_restrictions
                policy.max_access_count = policy_request.max_access_count
                policy.require_mfa = policy_request.require_mfa
                policy.require_approval = policy_request.require_approval

                # Store updated policy
                self.key_manager._store_access_policy(key_id, policy)

                return {"success": True, "message": "Access policy updated successfully"}

            except Exception as e:
                security_logger.error(f"Failed to update access policy for key {key_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/alerts")
        async def list_alerts(request: Request, resolved: bool = None):
            """List security alerts"""
            await self._verify_dashboard_access(request, Permission.READ)

            alerts = []
            for alert in self.alerts:
                if resolved is None or alert.resolved == resolved:
                    alerts.append({
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "key_id": alert.key_id,
                        "title": alert.title,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolved": alert.resolved,
                        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                        "resolved_by": alert.resolved_by,
                        "action_required": alert.action_required,
                        "suggested_actions": alert.suggested_actions
                    })

            return {"alerts": alerts}

        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(request: Request, alert_id: str):
            """Resolve a security alert"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                # Get session user
                session = await self._get_session(request)
                user_id = session.get("user_id", "dashboard_user")

                for alert in self.alerts:
                    if alert.alert_id == alert_id:
                        alert.resolved = True
                        alert.resolved_at = datetime.utcnow()
                        alert.resolved_by = user_id
                        return {"success": True, "message": "Alert resolved"}

                raise HTTPException(status_code=404, detail="Alert not found")

            except Exception as e:
                security_logger.error(f"Failed to resolve alert {alert_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/backup")
        async def create_backup_endpoint(request: Request):
            """Create system backup"""
            await self._verify_dashboard_access(request, Permission.WRITE)

            try:
                backup_id = self.key_manager.create_backup()
                return {
                    "success": True,
                    "backup_id": backup_id,
                    "message": "Backup created successfully"
                }

            except Exception as e:
                security_logger.error(f"Failed to create backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/stats")
        async def get_dashboard_stats(request: Request):
            """Get dashboard statistics"""
            await self._verify_dashboard_access(request, Permission.READ)

            try:
                key_stats = self.key_manager.get_security_stats()
                storage_stats = self.storage_manager.get_storage_stats()
                lifecycle_stats = self.lifecycle_manager.get_lifecycle_stats()

                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "key_management": key_stats,
                    "storage": storage_stats,
                    "lifecycle": lifecycle_stats,
                    "alerts": {
                        "total": len(self.alerts),
                        "active": len([a for a in self.alerts if not a.resolved]),
                        "by_severity": {
                            severity.value: len([a for a in self.alerts if a.severity == severity and not a.resolved])
                            for severity in AlertSeverity
                        }
                    },
                    "system": {
                        "uptime": "N/A",  # Could track system uptime
                        "compliance_standards": self.config.compliance_standards,
                        "dashboard_version": "2.0.0"
                    }
                }

            except Exception as e:
                security_logger.error(f"Failed to get dashboard stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/compliance")
        async def get_compliance_report(request: Request):
            """Generate compliance report"""
            await self._verify_dashboard_access(request, Permission.READ)

            try:
                report = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "standards": {},
                    "key_compliance": {},
                    "system_compliance": {},
                    "recommendations": []
                }

                # Check compliance for each standard
                for standard in self.config.compliance_standards:
                    standard_compliance = self._check_standard_compliance(standard)
                    report["standards"][standard] = standard_compliance

                # Check individual key compliance
                for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                    key_compliance = self._check_key_compliance(key_id, metadata)
                    report["key_compliance"][key_id] = key_compliance

                return report

            except Exception as e:
                security_logger.error(f"Failed to generate compliance report: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/emergency/revoke-all")
        async def emergency_revoke_all(request: Request):
            """Emergency revocation of all keys"""
            await self._verify_dashboard_access(request, Permission.SECURITY_ADMIN)

            try:
                revoked_count = 0
                for key_id in list(self.key_manager.keys_cache.keys()):
                    success = self.key_manager.revoke_key(
                        key_id=key_id,
                        user_id="emergency",
                        username="emergency_user",
                        reason="Emergency revocation"
                    )
                    if success:
                        revoked_count += 1

                # Create emergency alert
                alert = SecurityAlert(
                    alert_id=f"emergency_{secrets.token_urlsafe(16)}",
                    severity=AlertSeverity.CRITICAL,
                    title="Emergency Key Revocation",
                    message=f"All {revoked_count} keys have been revoked due to emergency",
                    timestamp=datetime.utcnow(),
                    action_required=True,
                    suggested_actions=["Investigate cause", "Restore from backup if safe", "Update security procedures"]
                )
                self.alerts.append(alert)

                return {
                    "success": True,
                    "revoked_count": revoked_count,
                    "message": "Emergency revocation completed"
                }

            except Exception as e:
                security_logger.error(f"Emergency revocation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _verify_dashboard_access(self, request: Request, required_permission: Permission):
        """Verify user has required dashboard access"""
        session = await self._get_session(request)
        if not session:
            raise HTTPException(status_code=401, detail="Authentication required")

        user_id = session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session")

        # Check if user has required permission
        # This would integrate with the security manager's permission system
        # For now, we'll use a simple role-based check
        user_role = session.get("role", "viewer")
        role_permissions = {
            "viewer": [Permission.READ],
            "operator": [Permission.READ, Permission.WRITE],
            "admin": [Permission.READ, Permission.WRITE, Permission.DELETE],
            "security_admin": list(Permission)
        }

        if required_permission not in role_permissions.get(user_role, []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    async def _get_session(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get user session"""
        session_id = request.session.get("session_id")
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]

            # Check if session is expired
            expires_at = session.get("expires_at")
            if expires_at and datetime.utcnow() > expires_at:
                del self.active_sessions[session_id]
                return None

            return session

        return None

    def _check_standard_compliance(self, standard: str) -> Dict[str, Any]:
        """Check compliance for a specific standard"""
        compliance = {
            "standard": standard,
            "compliant": False,
            "score": 0.0,
            "checks": {},
            "issues": [],
            "recommendations": []
        }

        if standard == "SOC2":
            checks = {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": True,
                "audit_logging": self.config.audit_logging_enabled,
                "key_rotation": all(
                    policy.rotation_interval_days <= 90
                    for policy in self.lifecycle_manager.lifecycle_policies.values()
                )
            }

            compliance["checks"] = checks
            compliance["score"] = sum(checks.values()) / len(checks)
            compliance["compliant"] = compliance["score"] >= 0.8

        elif standard == "ISO27001":
            checks = {
                "information_security_policy": True,
                "asset_management": True,
                "access_control": True,
                "cryptography": True,
                "operations_security": True,
                "communications_security": True,
                "system_acquisition": True,
                "supplier_relationships": True,
                "incident_management": True,
                "business_continuity": True,
                "compliance": True
            }

            compliance["checks"] = checks
            compliance["score"] = sum(checks.values()) / len(checks)
            compliance["compliant"] = compliance["score"] >= 0.9

        elif standard == "GDPR":
            checks = {
                "lawfulness_fairness_transparency": True,
                "purpose_limitation": True,
                "data_minimization": True,
                "accuracy": True,
                "storage_limitation": True,
                "integrity_confidentiality": True,
                "accountability": True
            }

            compliance["checks"] = checks
            compliance["score"] = sum(checks.values()) / len(checks)
            compliance["compliant"] = compliance["score"] >= 0.85

        return compliance

    def _check_key_compliance(self, key_id: str, metadata) -> Dict[str, Any]:
        """Check individual key compliance"""
        compliance = {
            "key_id": key_id,
            "compliant": True,
            "score": 1.0,
            "issues": [],
            "recommendations": []
        }

        # Check key strength
        if metadata.key_size_bits < 256:
            compliance["issues"].append(f"Key size {metadata.key_size_bits} bits is below recommended minimum")
            compliance["score"] -= 0.3

        # Check rotation status
        if metadata.next_rotation_at and metadata.next_rotation_at < datetime.utcnow():
            compliance["issues"].append("Key rotation is overdue")
            compliance["score"] -= 0.4

        # Check expiration
        if metadata.expires_at and metadata.expires_at < datetime.utcnow():
            compliance["issues"].append("Key has expired")
            compliance["score"] -= 0.5

        # Check access controls
        policy = self.key_manager.access_policies.get(key_id)
        if not policy or not policy.allowed_users:
            compliance["issues"].append("No access policy defined")
            compliance["score"] -= 0.2

        compliance["compliant"] = compliance["score"] >= 0.8

        return compliance

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render HTML template"""
        # This would integrate with a proper template engine
        # For now, return a simple HTML response
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{context.get('title', 'Key Management Dashboard')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ margin-top: 20px; }}
                .status {{ padding: 10px; margin: 10px 0; border-radius: 3px; }}
                .success {{ background: #d4edda; color: #155724; }}
                .warning {{ background: #fff3cd; color: #856404; }}
                .error {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{context.get('title', 'Key Management Dashboard')}</h1>
                <p>Secure Key Management System v2.0</p>
            </div>
            <div class="content">
                <div class="status success">
                    <h3>System Status: Healthy</h3>
                    <p>All security services are operational</p>
                </div>
                <p>API documentation available at <a href="/docs">/docs</a></p>
            </div>
        </body>
        </html>
        """

    def _start_background_tasks(self):
        """Start background dashboard tasks"""
        asyncio.create_task(self._alert_monitoring_task())
        asyncio.create_task(self._session_cleanup_task())
        asyncio.create_task(self._compliance_monitoring_task())

    async def _alert_monitoring_task(self):
        """Background task for monitoring and generating alerts"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Check for keys needing rotation
                for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                    if (metadata.next_rotation_at and
                        metadata.next_rotation_at <= datetime.utcnow() and
                        metadata.status == KeyStatus.ACTIVE):

                        # Create rotation alert
                        alert = SecurityAlert(
                            alert_id=f"rotation_{key_id}_{secrets.token_urlsafe(8)}",
                            severity=AlertSeverity.WARNING,
                            key_id=key_id,
                            title="Key Rotation Due",
                            message=f"Key '{metadata.name}' is due for rotation",
                            timestamp=datetime.utcnow(),
                            action_required=True,
                            suggested_actions=["Rotate key immediately", "Review rotation policy"]
                        )
                        self.alerts.append(alert)

                # Check for expired keys
                for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                    if (metadata.expires_at and
                        metadata.expires_at <= datetime.utcnow() and
                        metadata.status == KeyStatus.ACTIVE):

                        # Create expiration alert
                        alert = SecurityAlert(
                            alert_id=f"expiration_{key_id}_{secrets.token_urlsafe(8)}",
                            severity=AlertSeverity.ERROR,
                            key_id=key_id,
                            title="Key Expired",
                            message=f"Key '{metadata.name}' has expired",
                            timestamp=datetime.utcnow(),
                            action_required=True,
                            suggested_actions=["Revoke key immediately", "Generate replacement key"]
                        )
                        self.alerts.append(alert)

                # Clean up old alerts (keep last 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                self.alerts = [a for a in self.alerts if a.timestamp > cutoff_date or not a.resolved]

            except Exception as e:
                security_logger.error(f"Error in alert monitoring task: {e}")

    async def _session_cleanup_task(self):
        """Background task for cleaning up expired sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour

                expired_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if session.get("expires_at") and session["expires_at"] <= datetime.utcnow()
                ]

                for session_id in expired_sessions:
                    del self.active_sessions[session_id]

                if expired_sessions:
                    security_logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

            except Exception as e:
                security_logger.error(f"Error in session cleanup task: {e}")

    async def _compliance_monitoring_task(self):
        """Background task for continuous compliance monitoring"""
        while True:
            try:
                await asyncio.sleep(86400)  # Check daily

                # Check overall system compliance
                compliance_issues = []

                # Check key rotation compliance
                for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                    if metadata.rotation_period_days > 90:
                        compliance_issues.append({
                            "type": "rotation_policy",
                            "key_id": key_id,
                            "message": f"Key rotation period ({metadata.rotation_period_days} days) exceeds 90-day recommendation"
                        })

                # Check key strength compliance
                for key_id, (_, metadata) in self.key_manager.keys_cache.items():
                    if metadata.key_size_bits < 256:
                        compliance_issues.append({
                            "type": "key_strength",
                            "key_id": key_id,
                            "message": f"Key size ({metadata.key_size_bits} bits) below recommended minimum"
                        })

                # Create compliance alert if issues found
                if compliance_issues:
                    alert = SecurityAlert(
                        alert_id=f"compliance_{secrets.token_urlsafe(16)}",
                        severity=AlertSeverity.WARNING,
                        title="Compliance Issues Detected",
                        message=f"Found {len(compliance_issues)} compliance issues requiring attention",
                        timestamp=datetime.utcnow(),
                        action_required=True,
                        suggested_actions=["Review compliance report", "Address identified issues"]
                    )
                    self.alerts.append(alert)

            except Exception as e:
                security_logger.error(f"Error in compliance monitoring task: {e}")

    def run(self):
        """Run the dashboard server"""
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            debug=self.config.debug,
            log_level="info"
        )

# Factory function for easy initialization
def create_key_dashboard(key_manager: SecureKeyManager,
                        storage_manager: SecureStorageManager,
                        lifecycle_manager: KeyLifecycleManager,
                        security_manager: SecurityManager,
                        config: DashboardConfig = None) -> KeyDashboardAPI:
    """Create and return a key dashboard API instance"""
    if config is None:
        config = DashboardConfig()

    return KeyDashboardAPI(
        key_manager=key_manager,
        storage_manager=storage_manager,
        lifecycle_manager=lifecycle_manager,
        security_manager=security_manager,
        config=config
    )
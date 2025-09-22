"""
DuckBot Security Integration Module

Integration layer that connects all security components with existing DuckBot systems.
Provides unified security interface and automatic protection for all components.

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import logging
import json
from functools import wraps

from .security_framework import (
    SecurityManager, SecurityContext, SecurityEvent, SecurityEventType,
    Permission, ResourceType, SecurityLevel, SecurityConfig, SecurityPolicy
)
from .audit_logger import AuditLogger, AuditFilter, ComplianceStandard
from .authentication_system import (
    AuthenticationSystem, AuthResult, PasswordPolicy, TokenConfig,
    SessionConfig, OAuth2Config, InputType
)
from .security_hardening import (
    SecurityHardening, SecurityHeaders, RateLimitConfig, FileUploadConfig,
    ValidationResult, SecurityThreatLevel, require_csrf_token, rate_limit, validate_input
)
from .security_monitoring import (
    SecurityMonitor, SecurityAlert, ThreatLevel, AlertStatus, EventType,
    AnomalyDetection, SecurityMetrics
)

security_integration_logger = logging.getLogger('duckbot.security.integration')

class SecurityIntegration:
    """Main security integration system for DuckBot"""

    def __init__(self, config_path: str = "config/security_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Initialize security components
        self.security_manager = self._init_security_manager()
        self.audit_logger = self._init_audit_logger()
        self.auth_system = self._init_authentication_system()
        self.security_hardening = self._init_security_hardening()
        self.security_monitor = self._init_security_monitoring()

        # Integration state
        self.is_initialized = False
        self.component_protection = {}
        self.active_sessions = {}
        self.api_keys = {}

        security_integration_logger.info("SecurityIntegration initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            security_integration_logger.warning(f"Security config not found at {self.config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            security_integration_logger.error(f"Failed to load security config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default security configuration"""
        return {
            "security_framework": {"enabled": True},
            "authentication": {"jwt_secret": "default_secret_key"},
            "authorization": {"rbac_enabled": True},
            "audit_logging": {"enabled": True},
            "threat_detection": {"enabled": True}
        }

    def _init_security_manager(self) -> SecurityManager:
        """Initialize security manager"""
        security_config = SecurityConfig(
            jwt_secret_key=self.config["authentication"].get("jwt_secret", "default_secret"),
            encryption_key=self.config["encryption"].get("encryption_key", "default_encryption_key")
        )

        security_policy = SecurityPolicy(
            session_timeout_minutes=self.config["authorization"].get("session_timeout_minutes", 60),
            mfa_required=self.config["authentication"].get("mfa_enabled", False),
            rate_limit_requests_per_minute=self.config["rate_limiting"].get("requests_per_minute", 60),
            enable_audit_logging=self.config["audit_logging"].get("enabled", True),
            enable_threat_detection=self.config["threat_detection"].get("enabled", True)
        )

        return SecurityManager(security_config, security_policy)

    def _init_audit_logger(self) -> AuditLogger:
        """Initialize audit logger"""
        audit_config = self.config["audit_logging"]
        storage_backend = getattr(AuditLogger.StorageBackend, audit_config.get("storage_backend", "SQLITE").upper())

        return AuditLogger(
            storage_backend=storage_backend,
            database_path=audit_config.get("database_path", "audit_log.db"),
            log_directory=audit_config.get("log_directory", "audit_logs"),
            max_file_size_mb=audit_config.get("max_file_size_mb", 100),
            retention_days=self.config.get("audit_retention_days", 365)
        )

    def _init_authentication_system(self) -> AuthenticationSystem:
        """Initialize authentication system"""
        auth_config = self.config["authentication"]
        password_policy_config = self.config["password_policy"]

        password_policy = PasswordPolicy(
            min_length=password_policy_config.get("min_length", 12),
            max_length=password_policy_config.get("max_length", 128),
            require_uppercase=password_policy_config.get("require_uppercase", True),
            require_lowercase=password_policy_config.get("require_lowercase", True),
            require_numbers=password_policy_config.get("require_numbers", True),
            require_special_chars=password_policy_config.get("require_special_chars", True),
            complexity_score_min=password_policy_config.get("complexity_score_min", 60)
        )

        token_config = TokenConfig(
            access_token_expire_minutes=auth_config.get("jwt_expiration_minutes", 60),
            refresh_token_expire_days=auth_config.get("refresh_token_expire_days", 7)
        )

        session_config = SessionConfig(
            timeout_minutes=self.config["authorization"].get("session_timeout_minutes", 60),
            max_concurrent_sessions=self.config["authorization"].get("max_concurrent_sessions", 5)
        )

        return AuthenticationSystem(
            jwt_secret=auth_config.get("jwt_secret", "default_secret"),
            encryption_key=self.config["encryption"].get("encryption_key", "default_encryption_key"),
            password_policy=password_policy,
            token_config=token_config,
            session_config=session_config
        )

    def _init_security_hardening(self) -> SecurityHardening:
        """Initialize security hardening"""
        headers_config = self.config["security_headers"]
        rate_limit_config = self.config["rate_limiting"]
        file_upload_config = self.config["file_upload"]

        security_headers = SecurityHeaders(
            content_security_policy=headers_config.get("content_security_policy"),
            x_frame_options=headers_config.get("x_frame_options"),
            x_content_type_options=headers_config.get("x_content_type_options"),
            x_xss_protection=headers_config.get("x_xss_protection"),
            referrer_policy=headers_config.get("referrer_policy"),
            permissions_policy=headers_config.get("permissions_policy"),
            strict_transport_security=headers_config.get("strict_transport_security")
        )

        rate_limit = RateLimitConfig(
            requests_per_minute=rate_limit_config.get("requests_per_minute", 60),
            requests_per_hour=rate_limit_config.get("requests_per_hour", 3600),
            requests_per_day=rate_limit_config.get("requests_per_day", 86400),
            burst_limit=rate_limit_config.get("burst_limit", 10)
        )

        file_upload = FileUploadConfig(
            max_file_size_mb=file_upload_config.get("max_file_size_mb", 10),
            allowed_extensions=set(file_upload_config.get("allowed_extensions", [])),
            allowed_mime_types=set(file_upload_config.get("allowed_mime_types", [])),
            scan_for_malware=file_upload_config.get("scan_for_malware", True),
            sanitize_filenames=file_upload_config.get("sanitize_filenames", True)
        )

        return SecurityHardening(security_headers, rate_limit, file_upload)

    def _init_security_monitoring(self) -> SecurityMonitor:
        """Initialize security monitoring"""
        anomaly_config = self.config["threat_detection"]["anomaly_detection"]

        anomaly_detection = AnomalyDetection(
            enabled=anomaly_config.get("enabled", True),
            sensitivity=anomaly_config.get("sensitivity", 0.7),
            window_size=anomaly_config.get("window_size", 100),
            baseline_period=anomaly_config.get("baseline_period_days", 7),
            check_interval=anomaly_config.get("check_interval_seconds", 60)
        )

        return SecurityMonitor(anomaly_detection)

    async def initialize(self):
        """Initialize security integration"""
        try:
            if not self.config["security_framework"].get("enabled", True):
                security_integration_logger.info("Security framework disabled in configuration")
                return

            # Start monitoring
            await self.security_monitor.start_monitoring()

            # Start audit logger background tasks
            await self.audit_logger.start_background_tasks()

            # Set up default users and roles
            await self._setup_default_configuration()

            # Register alert handlers
            self._register_alert_handlers()

            self.is_initialized = True
            security_integration_logger.info("Security integration initialized successfully")

        except Exception as e:
            security_integration_logger.error(f"Failed to initialize security integration: {e}")
            raise

    async def _setup_default_configuration(self):
        """Set up default users and roles"""
        try:
            # Create default roles
            default_roles = self.config.get("default_roles", [])
            for role_data in default_roles:
                from .security_framework import Role
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=[Permission(p) for p in role_data["permissions"]]
                )
                self.security_manager.roles[role.name] = role

            # Create default users
            default_users = self.config.get("default_users", [])
            for user_data in default_users:
                try:
                    await self.auth_system.create_user(
                        username=user_data["username"],
                        email=user_data["email"],
                        password=user_data["password"],
                        roles=user_data["roles"]
                    )
                    security_integration_logger.info(f"Created default user: {user_data['username']}")
                except Exception as e:
                    security_integration_logger.warning(f"Failed to create default user {user_data['username']}: {e}")

        except Exception as e:
            security_integration_logger.error(f"Failed to setup default configuration: {e}")

    def _register_alert_handlers(self):
        """Register alert handlers"""
        self.security_monitor.add_alert_handler(self._handle_security_alert)

    async def _handle_security_alert(self, alert: SecurityAlert):
        """Handle security alerts"""
        try:
            # Log alert to audit log
            await self.audit_logger.log_event(SecurityEvent(
                id=f"alert_{alert.id}",
                event_type=SecurityEventType.THREAT_DETECTED,
                action=f"Security alert: {alert.title}",
                result="alert_generated",
                severity=alert.severity.value,
                details={
                    "threat_type": alert.threat_type.value,
                    "description": alert.description,
                    "affected_resources": alert.affected_resources
                }
            ))

            # Send notification (implementation depends on notification system)
            await self._send_alert_notification(alert)

        except Exception as e:
            security_integration_logger.error(f"Failed to handle security alert: {e}")

    async def _send_alert_notification(self, alert: SecurityAlert):
        """Send alert notification"""
        # Implementation depends on notification system
        security_integration_logger.warning(f"SECURITY ALERT: {alert.title} - {alert.description}")

    # Public API methods

    async def authenticate(self, username: str, password: str,
                         ip_address: str = None, user_agent: str = None) -> Optional[SecurityContext]:
        """Authenticate user and return security context"""
        try:
            auth_result = await self.auth_system.authenticate_user(username, password, ip_address, user_agent)

            if auth_result.success:
                if auth_result.mfa_required:
                    # MFA required, return incomplete context
                    return None

                # Create security context
                security_context = SecurityContext(
                    user_id=auth_result.user_id,
                    username=auth_result.username,
                    roles=auth_result.additional_info.get("roles", ["user"]),
                    permissions=set(),  # Will be populated by security manager
                    security_level=SecurityLevel.USER,
                    session_id=auth_result.session_id,
                    ip_address=ip_address or "unknown",
                    user_agent=user_agent or "unknown",
                    created_at=datetime.utcnow(),
                    expires_at=auth_result.expires_at
                )

                # Store active session
                self.active_sessions[auth_result.session_id] = security_context

                # Log successful authentication
                await self.audit_logger.log_event(SecurityEvent(
                    id=f"auth_{auth_result.session_id}",
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=auth_result.user_id,
                    username=auth_result.username,
                    session_id=auth_result.session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    action=f"User {username} authenticated successfully",
                    result="success"
                ))

                return security_context

            else:
                # Log failed authentication
                await self.audit_logger.log_event(SecurityEvent(
                    id=f"auth_fail_{datetime.utcnow().timestamp()}",
                    event_type=SecurityEventType.LOGIN_FAILURE,
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    action=f"Failed authentication attempt for {username}",
                    result="failure",
                    details={"error": auth_result.error_message}
                ))

                return None

        except Exception as e:
            security_integration_logger.error(f"Authentication failed for {username}: {e}")
            return None

    async def validate_session(self, session_id: str) -> Optional[SecurityContext]:
        """Validate and return security context for session"""
        return self.active_sessions.get(session_id)

    async def logout(self, session_id: str) -> bool:
        """Logout user session"""
        try:
            context = self.active_sessions.get(session_id)
            if context:
                del self.active_sessions[session_id]

                await self.audit_logger.log_event(SecurityEvent(
                    id=f"logout_{session_id}",
                    event_type=SecurityEventType.LOGOUT,
                    user_id=context.user_id,
                    username=context.username,
                    session_id=session_id,
                    ip_address=context.ip_address,
                    action=f"User {context.username} logged out",
                    result="success"
                ))

                return True

            return False

        except Exception as e:
            security_integration_logger.error(f"Logout failed: {e}")
            return False

    async def check_permission(self, session_id: str, permission: Permission,
                              resource_type: ResourceType = None, resource_id: str = None) -> bool:
        """Check if user has permission"""
        try:
            context = self.active_sessions.get(session_id)
            if not context:
                return False

            return self.security_manager.check_permission(context, permission, resource_type, resource_id)

        except Exception as e:
            security_integration_logger.error(f"Permission check failed: {e}")
            return False

    async def protect_component(self, component_name: str, component_type: str,
                              required_permissions: List[Permission] = None,
                              resource_type: ResourceType = None) -> bool:
        """Register component for security protection"""
        try:
            self.component_protection[component_name] = {
                "type": component_type,
                "required_permissions": required_permissions or [Permission.READ],
                "resource_type": resource_type
            }

            security_integration_logger.info(f"Component {component_name} registered for security protection")
            return True

        except Exception as e:
            security_integration_logger.error(f"Failed to protect component {component_name}: {e}")
            return False

    def require_authentication(self, func):
        """Decorator to require authentication for function"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            session_id = kwargs.get('session_id') or getattr(args[0], 'session_id', None)
            if not session_id:
                return {"error": "Authentication required", "status": 401}

            context = self.active_sessions.get(session_id)
            if not context:
                return {"error": "Invalid or expired session", "status": 401}

            # Add context to function
            kwargs['security_context'] = context
            return await func(*args, **kwargs)

        return wrapper

    def require_permission(self, permission: Permission, resource_type: ResourceType = None):
        """Decorator to require specific permission"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                session_id = kwargs.get('session_id') or getattr(args[0], 'session_id', None)
                if not session_id:
                    return {"error": "Authentication required", "status": 401}

                context = self.active_sessions.get(session_id)
                if not context:
                    return {"error": "Invalid or expired session", "status": 401}

                if not await self.check_permission(session_id, permission, resource_type):
                    return {"error": "Insufficient permissions", "status": 403}

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    async def validate_and_sanitize_input(self, input_value: str, input_type: InputType) -> ValidationResult:
        """Validate and sanitize input"""
        return self.security_hardening.validate_input(input_value, input_type)

    async def log_security_event(self, event_type: SecurityEventType, **kwargs):
        """Log security event"""
        event = SecurityEvent(event_type=event_type, **kwargs)
        await self.audit_logger.log_event(event)

        # Also send to monitoring system
        from .security_monitoring import SecurityEvent as MonitoringEvent
        monitoring_event = MonitoringEvent(
            id=event.id,
            event_type=getattr(EventType, event_type.value, EventType.SECURITY_EVENT),
            timestamp=event.timestamp,
            user_id=event.user_id,
            username=event.username,
            session_id=event.session_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            resource=event.resource_id,
            action=event.action,
            result=event.result,
            details=event.details,
            severity=getattr(ThreatLevel, event.severity, ThreatLevel.LOW)
        )
        self.security_monitor.add_security_event(monitoring_event)

    async def generate_api_key(self, user_id: str, description: str = None) -> str:
        """Generate API key for user"""
        return await self.auth_system.generate_api_key(user_id, description)

    async def revoke_api_key(self, user_id: str, api_key: str) -> bool:
        """Revoke API key"""
        return await self.auth_system.revoke_api_key(user_id, api_key)

    async def get_security_statistics(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        return {
            "security_manager": self.security_manager.get_security_stats(),
            "audit_logger": await self.audit_logger.get_audit_statistics(),
            "security_monitor": self.security_monitor.get_security_metrics(),
            "security_hardening": self.security_hardening.get_security_stats(),
            "active_sessions": len(self.active_sessions),
            "protected_components": len(self.component_protection)
        }

    async def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        return {
            "security_enabled": self.is_initialized,
            "framework_status": "active" if self.is_initialized else "inactive",
            "components_protected": len(self.component_protection),
            "active_sessions": len(self.active_sessions),
            "recent_threats": len(self.security_monitor.get_alerts(status=AlertStatus.OPEN)),
            "system_health": "healthy" if self.is_initialized else "unhealthy",
            "last_updated": datetime.utcnow().isoformat()
        }

    async def export_security_report(self, format: str = "json", hours: int = 24) -> str:
        """Export comprehensive security report"""
        return await self.security_monitor.export_security_report(format, hours)

    async def generate_compliance_report(self, standard: ComplianceStandard,
                                       period_start: datetime, period_end: datetime):
        """Generate compliance report"""
        return await self.audit_logger.generate_compliance_report(standard, period_start, period_end)

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for web responses"""
        return self.security_hardening.get_security_headers()

    async def validate_file_upload(self, file_data: bytes, filename: str,
                                 content_type: str) -> ValidationResult:
        """Validate file upload"""
        return self.security_hardening.validate_file_upload(file_data, filename, content_type)

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        return self.security_hardening.generate_csrf_token(session_id)

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        return self.security_hardening.validate_csrf_token(token, session_id)

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            now = datetime.utcnow()
            expired_sessions = [
                session_id for session_id, context in self.active_sessions.items()
                if not context.is_valid()
            ]

            for session_id in expired_sessions:
                del self.active_sessions[session_id]

            security_integration_logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        except Exception as e:
            security_integration_logger.error(f"Failed to cleanup expired sessions: {e}")

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        try:
            # Session cleanup
            asyncio.create_task(self._session_cleanup_loop())

            # Token cleanup
            asyncio.create_task(self._token_cleanup_loop())

            security_integration_logger.info("Background security tasks started")

        except Exception as e:
            security_integration_logger.error(f"Failed to start background tasks: {e}")

    async def _session_cleanup_loop(self):
        """Background session cleanup loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.cleanup_expired_sessions()
            except Exception as e:
                security_integration_logger.error(f"Session cleanup loop error: {e}")

    async def _token_cleanup_loop(self):
        """Background token cleanup loop"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                self.security_hardening.cleanup_expired_tokens()
            except Exception as e:
                security_integration_logger.error(f"Token cleanup loop error: {e}")

    # Integration with DuckBot components

    async def protect_webui_endpoint(self, endpoint_name: str, required_permissions: List[Permission] = None):
        """Protect WebUI endpoint"""
        return await self.protect_component(
            f"webui_{endpoint_name}",
            "webui_endpoint",
            required_permissions or [Permission.READ],
            ResourceType.WEBUI_ROUTE
        )

    async def protect_api_endpoint(self, endpoint_name: str, required_permissions: List[Permission] = None):
        """Protect API endpoint"""
        return await self.protect_component(
            f"api_{endpoint_name}",
            "api_endpoint",
            required_permissions or [Permission.READ],
            ResourceType.API_ENDPOINT
        )

    async def protect_terminal_command(self, command_name: str, required_permissions: List[Permission] = None):
        """Protect terminal command"""
        return await self.protect_component(
            f"terminal_{command_name}",
            "terminal_command",
            required_permissions or [Permission.EXECUTE],
            ResourceType.TERMINAL_COMMAND
        )

    async def protect_ai_model_access(self, model_name: str, required_permissions: List[Permission] = None):
        """Protect AI model access"""
        return await self.protect_component(
            f"ai_model_{model_name}",
            "ai_model",
            required_permissions or [Permission.AI_MODEL_ACCESS],
            ResourceType.AI_MODEL
        )

    async def protect_desktop_automation(self, action_name: str, required_permissions: List[Permission] = None):
        """Protect desktop automation action"""
        return await self.protect_component(
            f"desktop_{action_name}",
            "desktop_automation",
            required_permissions or [Permission.DESKTOP_AUTOMATION],
            ResourceType.DESKTOP_APP
        )

    def get_integration_info(self) -> Dict[str, Any]:
        """Get integration information"""
        return {
            "version": "1.0.0",
            "components": {
                "security_manager": "active",
                "audit_logger": "active",
                "authentication_system": "active",
                "security_hardening": "active",
                "security_monitoring": "active"
            },
            "protected_components": list(self.component_protection.keys()),
            "configuration": {
                "rbac_enabled": self.config["authorization"].get("rbac_enabled", True),
                "mfa_enabled": self.config["authentication"].get("mfa_enabled", False),
                "audit_logging_enabled": self.config["audit_logging"].get("enabled", True),
                "threat_detection_enabled": self.config["threat_detection"].get("enabled", True)
            },
            "status": "initialized" if self.is_initialized else "uninitialized"
        }
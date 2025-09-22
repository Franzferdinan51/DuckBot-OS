"""
DuckBot Security Framework

A comprehensive security framework providing:
- Role-Based Access Control (RBAC)
- Audit logging and monitoring
- Enhanced authentication and authorization
- Security hardening and threat detection
- Compliance and security reporting

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Set, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import secrets
import re
import ipaddress
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, validator
import bcrypt
import jwt
from cryptography.fernet import Fernet
import logging

# Security logger setup
security_logger = logging.getLogger('duckbot.security')

class SecurityLevel(Enum):
    """Security levels for system access"""
    PUBLIC = 0
    USER = 1
    ADMIN = 2
    SUPER_ADMIN = 3
    SYSTEM = 4

class Permission(Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    AUDIT_VIEW = "audit_view"
    API_ACCESS = "api_access"
    DESKTOP_AUTOMATION = "desktop_automation"
    AI_MODEL_ACCESS = "ai_model_access"
    WEBUI_ACCESS = "webui_access"
    TERMINAL_ACCESS = "terminal_access"

class ResourceType(Enum):
    """Protected resource types"""
    API_ENDPOINT = "api_endpoint"
    WEBUI_ROUTE = "webui_route"
    TERMINAL_COMMAND = "terminal_command"
    AI_MODEL = "ai_model"
    DESKTOP_APP = "desktop_app"
    SYSTEM_CONFIG = "system_config"
    USER_DATA = "user_data"
    AUDIT_LOG = "audit_log"
    SECURITY_CONFIG = "security_config"

class SecurityEventType(Enum):
    """Security event types for audit logging"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"
    ACCESS_GRANTED = "access_granted"
    SECURITY_CONFIG_CHANGE = "security_config_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_CREATE = "role_create"
    ROLE_UPDATE = "role_update"
    ROLE_DELETE = "role_delete"
    POLICY_VIOLATION = "policy_violation"
    THREAT_DETECTED = "threat_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    API_KEY_GENERATED = "api_key_generated"
    API_KEY_REVOKED = "api_key_revoked"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"

@dataclass
class SecurityContext:
    """Security context for user sessions"""
    user_id: str
    username: str
    roles: List[str]
    permissions: Set[Permission]
    security_level: SecurityLevel
    session_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    mfa_verified: bool = False
    api_key: Optional[str] = None

    def has_permission(self, permission: Permission) -> bool:
        """Check if context has required permission"""
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if context has required role"""
        return role in self.roles

    def is_valid(self) -> bool:
        """Check if session is still valid"""
        return datetime.utcnow() < self.expires_at

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_max_age_days: int = 90
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    mfa_required: bool = False
    api_key_required: bool = False
    ip_whitelist: List[str] = None
    ip_blacklist: List[str] = None
    rate_limit_requests_per_minute: int = 60
    enable_audit_logging: bool = True
    enable_threat_detection: bool = True

    def __post_init__(self):
        if self.ip_whitelist is None:
            self.ip_whitelist = []
        if self.ip_blacklist is None:
            self.ip_blacklist = []

class Role(BaseModel):
    """User role with permissions"""
    name: str
    description: str
    permissions: List[Permission]
    security_level: SecurityLevel
    is_system_role: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Role name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

class User(BaseModel):
    """User account with security attributes"""
    id: str
    username: str
    email: str
    password_hash: str
    roles: List[str]
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    last_login_at: Optional[datetime] = None
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    mfa_secret: Optional[str] = None
    mfa_enabled: bool = False
    api_keys: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

class SecurityEvent(BaseModel):
    """Security event for audit logging"""
    id: str
    event_type: SecurityEventType
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    action: str
    result: str  # "success" or "failure"
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str = "info"  # "low", "medium", "high", "critical"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging"""
        return asdict(self)

class SecurityConfig(BaseModel):
    """Security configuration"""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    encryption_key: str
    bcrypt_rounds: int = 12
    mfa_issuer: str = "DuckBot-v4.2"
    audit_log_retention_days: int = 365
    threat_detection_enabled: bool = True
    rate_limiting_enabled: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8787"]
    csrf_protection_enabled: bool = True
    input_validation_enabled: bool = True
    security_headers_enabled: bool = True

class SecurityManager:
    """Main security manager for DuckBot"""

    def __init__(self, config: SecurityConfig, policy: SecurityPolicy):
        self.config = config
        self.policy = policy
        self.fernet = Fernet(config.encryption_key.encode())
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.active_sessions: Dict[str, SecurityContext] = {}
        self.audit_log: List[SecurityEvent] = []
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.ip_reputation: Dict[str, Dict[str, Any]] = {}

        # Initialize default roles
        self._initialize_default_roles()

        security_logger.info("SecurityManager initialized")

    def _initialize_default_roles(self):
        """Initialize default system roles"""
        default_roles = [
            Role(
                name="super_admin",
                description="Super administrator with full system access",
                permissions=list(Permission),
                security_level=SecurityLevel.SUPER_ADMIN,
                is_system_role=True
            ),
            Role(
                name="admin",
                description="Administrator with elevated privileges",
                permissions=[
                    Permission.READ, Permission.WRITE, Permission.EXECUTE,
                    Permission.ADMIN, Permission.USER_MANAGEMENT,
                    Permission.AUDIT_VIEW, Permission.SYSTEM_CONFIG,
                    Permission.WEBUI_ACCESS, Permission.TERMINAL_ACCESS
                ],
                security_level=SecurityLevel.ADMIN,
                is_system_role=True
            ),
            Role(
                name="security_admin",
                description="Security administrator role",
                permissions=[
                    Permission.READ, Permission.WRITE, Permission.SECURITY_ADMIN,
                    Permission.AUDIT_VIEW, Permission.USER_MANAGEMENT,
                    Permission.SYSTEM_CONFIG, Permission.WEBUI_ACCESS
                ],
                security_level=SecurityLevel.ADMIN,
                is_system_role=True
            ),
            Role(
                name="user",
                description="Standard user role",
                permissions=[
                    Permission.READ, Permission.WRITE, Permission.EXECUTE,
                    Permission.WEBUI_ACCESS, Permission.TERMINAL_ACCESS,
                    Permission.DESKTOP_AUTOMATION, Permission.AI_MODEL_ACCESS
                ],
                security_level=SecurityLevel.USER,
                is_system_role=True
            ),
            Role(
                name="guest",
                description="Guest user with read-only access",
                permissions=[Permission.READ],
                security_level=SecurityLevel.PUBLIC,
                is_system_role=True
            )
        ]

        for role in default_roles:
            self.roles[role.name] = role

    def create_user(self, username: str, email: str, password: str, roles: List[str] = None) -> User:
        """Create a new user with security validation"""
        if roles is None:
            roles = ["user"]

        # Validate password against policy
        self._validate_password(password)

        # Check if user already exists
        if any(u.username == username for u in self.users.values()):
            raise ValueError(f"Username '{username}' already exists")

        if any(u.email == email for u in self.users.values()):
            raise ValueError(f"Email '{email}' already exists")

        # Validate roles exist
        for role_name in roles:
            if role_name not in self.roles:
                raise ValueError(f"Role '{role_name}' does not exist")

        # Hash password
        password_hash = self._hash_password(password)

        # Create user
        user_id = hashlib.sha256(username.encode()).hexdigest()
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles
        )

        self.users[user_id] = user

        # Log security event
        self.log_security_event(
            SecurityEventType.USER_CREATE,
            user_id=user_id,
            username=username,
            action=f"Created user {username}",
            result="success",
            details={"roles": roles}
        )

        security_logger.info(f"Created user: {username}")
        return user

    def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Optional[SecurityContext]:
        """Authenticate user and create security context"""
        user = self._get_user_by_username(username)
        if not user:
            self._record_failed_attempt(username, ip_address)
            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                username=username,
                ip_address=ip_address,
                action=f"Failed login attempt for {username}",
                result="failure",
                details={"reason": "user_not_found"}
            )
            return None

        # Check if account is locked
        if user.is_locked:
            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=user.id,
                username=username,
                ip_address=ip_address,
                action=f"Login attempt for locked account {username}",
                result="failure",
                details={"reason": "account_locked"}
            )
            return None

        # Check if account is active
        if not user.is_active:
            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=user.id,
                username=username,
                ip_address=ip_address,
                action=f"Login attempt for inactive account {username}",
                result="failure",
                details={"reason": "account_inactive"}
            )
            return None

        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._record_failed_attempt(username, ip_address)
            self._handle_failed_login(user, ip_address)
            return None

        # Check IP reputation
        if ip_address and self._is_ip_malicious(ip_address):
            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=user.id,
                username=username,
                ip_address=ip_address,
                action=f"Login attempt from malicious IP {ip_address}",
                result="failure",
                details={"reason": "malicious_ip"}
            )
            return None

        # Check rate limiting
        if ip_address and not self._check_rate_limit(ip_address):
            self.log_security_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                user_id=user.id,
                username=username,
                ip_address=ip_address,
                action=f"Rate limit exceeded for {username}",
                result="failure"
            )
            return None

        # Create security context
        session_id = secrets.token_urlsafe(32)
        permissions = self._get_user_permissions(user)
        security_level = self._get_user_security_level(user)

        context = SecurityContext(
            user_id=user.id,
            username=user.username,
            roles=user.roles,
            permissions=permissions,
            security_level=security_level,
            session_id=session_id,
            ip_address=ip_address or "unknown",
            user_agent="unknown",  # Would be passed from request
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=self.policy.session_timeout_minutes)
        )

        # Store active session
        self.active_sessions[session_id] = context

        # Update user last login
        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0

        # Log successful login
        self.log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            user_id=user.id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            action=f"Successful login for {username}",
            result="success"
        )

        security_logger.info(f"User authenticated: {username}")
        return context

    def validate_session(self, session_id: str) -> Optional[SecurityContext]:
        """Validate and return security context for session"""
        context = self.active_sessions.get(session_id)
        if not context:
            return None

        if not context.is_valid():
            self.terminate_session(session_id)
            return None

        return context

    def terminate_session(self, session_id: str) -> bool:
        """Terminate user session"""
        context = self.active_sessions.get(session_id)
        if context:
            del self.active_sessions[session_id]

            self.log_security_event(
                SecurityEventType.SESSION_TERMINATED,
                user_id=context.user_id,
                username=context.username,
                session_id=session_id,
                action=f"Session terminated for {context.username}",
                result="success"
            )

            security_logger.info(f"Session terminated: {context.username}")
            return True
        return False

    def check_permission(self, context: SecurityContext, permission: Permission,
                        resource_type: ResourceType = None, resource_id: str = None) -> bool:
        """Check if user has permission to access resource"""
        if not context.has_permission(permission):
            self.log_security_event(
                SecurityEventType.PERMISSION_DENIED,
                user_id=context.user_id,
                username=context.username,
                session_id=context.session_id,
                ip_address=context.ip_address,
                resource_type=resource_type,
                resource_id=resource_id,
                action=f"Permission denied for {permission.value}",
                result="failure",
                details={"required_permission": permission.value}
            )
            return False

        # Log successful access
        self.log_security_event(
            SecurityEventType.ACCESS_GRANTED,
            user_id=context.user_id,
            username=context.username,
            session_id=context.session_id,
            ip_address=context.ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=f"Access granted for {permission.value}",
            result="success"
        )

        return True

    def generate_jwt_token(self, context: SecurityContext) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            "user_id": context.user_id,
            "username": context.username,
            "roles": context.roles,
            "permissions": [p.value for p in context.permissions],
            "security_level": context.security_level.value,
            "session_id": context.session_id,
            "exp": datetime.utcnow() + timedelta(minutes=self.config.jwt_expiration_minutes),
            "iat": datetime.utcnow()
        }

        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
        return token

    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            security_logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            security_logger.warning(f"Invalid JWT token: {e}")
            return None

    def generate_api_key(self, user_id: str, description: str = None) -> str:
        """Generate new API key for user"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")

        api_key = f"db_{secrets.token_urlsafe(32)}"
        user.api_keys.append(api_key)
        user.updated_at = datetime.utcnow()

        self.log_security_event(
            SecurityEventType.API_KEY_GENERATED,
            user_id=user_id,
            username=user.username,
            action=f"API key generated for {user.username}",
            result="success",
            details={"description": description}
        )

        security_logger.info(f"API key generated for user: {user.username}")
        return api_key

    def revoke_api_key(self, user_id: str, api_key: str) -> bool:
        """Revoke API key for user"""
        user = self.users.get(user_id)
        if not user:
            return False

        if api_key in user.api_keys:
            user.api_keys.remove(api_key)
            user.updated_at = datetime.utcnow()

            self.log_security_event(
                SecurityEventType.API_KEY_REVOKED,
                user_id=user_id,
                username=user.username,
                action=f"API key revoked for {user.username}",
                result="success"
            )

            security_logger.info(f"API key revoked for user: {user.username}")
            return True
        return False

    def validate_api_key(self, api_key: str) -> Optional[SecurityContext]:
        """Validate API key and return security context"""
        for user in self.users.values():
            if api_key in user.api_keys and user.is_active and not user.is_locked:
                permissions = self._get_user_permissions(user)
                security_level = self._get_user_security_level(user)

                context = SecurityContext(
                    user_id=user.id,
                    username=user.username,
                    roles=user.roles,
                    permissions=permissions,
                    security_level=security_level,
                    session_id=f"api_{secrets.token_urlsafe(16)}",
                    ip_address="api_client",
                    user_agent="api_client",
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    api_key=api_key
                )

                self.log_security_event(
                    SecurityEventType.ACCESS_GRANTED,
                    user_id=user.id,
                    username=user.username,
                    action=f"API key validated for {user.username}",
                    result="success"
                )

                return context
        return None

    def log_security_event(self, event_type: SecurityEventType, **kwargs):
        """Log security event to audit trail"""
        event = SecurityEvent(
            id=secrets.token_urlsafe(16),
            event_type=event_type,
            **kwargs
        )

        self.audit_log.append(event)

        # Maintain log retention
        cutoff_date = datetime.utcnow() - timedelta(days=self.policy.audit_log_retention_days)
        self.audit_log = [e for e in self.audit_log if e.timestamp > cutoff_date]

        # Log to security logger
        log_message = f"[{event.event_type.value}] {event.action}"
        if event.username:
            log_message += f" - User: {event.username}"
        if event.ip_address:
            log_message += f" - IP: {event.ip_address}"

        if event.severity == "critical":
            security_logger.critical(log_message)
        elif event.severity == "high":
            security_logger.error(log_message)
        elif event.severity == "medium":
            security_logger.warning(log_message)
        else:
            security_logger.info(log_message)

    def get_audit_log(self, user_id: str = None, event_type: SecurityEventType = None,
                     start_date: datetime = None, end_date: datetime = None) -> List[SecurityEvent]:
        """Retrieve filtered audit log entries"""
        filtered_log = self.audit_log

        if user_id:
            filtered_log = [e for e in filtered_log if e.user_id == user_id]

        if event_type:
            filtered_log = [e for e in filtered_log if e.event_type == event_type]

        if start_date:
            filtered_log = [e for e in filtered_log if e.timestamp >= start_date]

        if end_date:
            filtered_log = [e for e in filtered_log if e.timestamp <= end_date]

        return sorted(filtered_log, key=lambda x: x.timestamp, reverse=True)

    def _validate_password(self, password: str):
        """Validate password against security policy"""
        if len(password) < self.policy.password_min_length:
            raise ValueError(f"Password must be at least {self.policy.password_min_length} characters long")

        if self.policy.password_require_uppercase and not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")

        if self.policy.password_require_lowercase and not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")

        if self.policy.password_require_numbers and not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")

        if self.policy.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=self.config.bcrypt_rounds)
        return bcrypt.hashpw(password.encode(), salt).decode()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def _get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for user based on roles"""
        permissions = set()
        for role_name in user.roles:
            if role_name in self.roles:
                permissions.update(self.roles[role_name].permissions)
        return permissions

    def _get_user_security_level(self, user: User) -> SecurityLevel:
        """Get highest security level for user based on roles"""
        highest_level = SecurityLevel.PUBLIC
        for role_name in user.roles:
            if role_name in self.roles:
                role_level = self.roles[role_name].security_level
                if role_level.value > highest_level.value:
                    highest_level = role_level
        return highest_level

    def _record_failed_attempt(self, username: str, ip_address: str = None):
        """Record failed login attempt"""
        timestamp = datetime.utcnow()

        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        self.failed_attempts[username].append(timestamp)

        if ip_address:
            if ip_address not in self.failed_attempts:
                self.failed_attempts[ip_address] = []
            self.failed_attempts[ip_address].append(timestamp)

    def _handle_failed_login(self, user: User, ip_address: str = None):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1

        # Lock account if max attempts exceeded
        if user.failed_login_attempts >= self.policy.max_login_attempts:
            user.is_locked = True
            user.updated_at = datetime.utcnow()

            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=user.id,
                username=user.username,
                ip_address=ip_address,
                action=f"Account locked for {user.username} due to too many failed attempts",
                result="failure",
                details={"failed_attempts": user.failed_login_attempts},
                severity="high"
            )

            security_logger.warning(f"Account locked due to failed attempts: {user.username}")
        else:
            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=user.id,
                username=user.username,
                ip_address=ip_address,
                action=f"Failed login attempt for {user.username}",
                result="failure",
                details={"failed_attempts": user.failed_login_attempts}
            )

    def _is_ip_malicious(self, ip_address: str) -> bool:
        """Check if IP address is malicious"""
        try:
            ip = ipaddress.ip_address(ip_address)

            # Check against blacklist
            if str(ip) in self.policy.ip_blacklist:
                return True

            # Check IP reputation
            reputation = self.ip_reputation.get(str(ip), {})
            if reputation.get("threat_score", 0) > 0.8:
                return True

            return False
        except ValueError:
            return True  # Invalid IP format

    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP address has exceeded rate limit"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        if ip_address not in self.rate_limits:
            self.rate_limits[ip_address] = []

        # Clean old requests
        self.rate_limits[ip_address] = [t for t in self.rate_limits[ip_address] if t > cutoff]

        # Check limit
        if len(self.rate_limits[ip_address]) >= self.policy.rate_limit_requests_per_minute:
            return False

        # Record this request
        self.rate_limits[ip_address].append(now)
        return True

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def sanitize_input(self, input_string: str, input_type: str = "text") -> str:
        """Sanitize input to prevent injection attacks"""
        if not self.policy.input_validation_enabled:
            return input_string

        if input_type == "text":
            # Remove HTML/XML tags
            sanitized = re.sub(r'<[^>]*>', '', input_string)
            # Escape special characters
            sanitized = sanitized.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return sanitized
        elif input_type == "sql":
            # Basic SQL injection prevention
            sanitized = re.sub(r'(\'|\"|;|--|\n|\r)', '', input_string)
            return sanitized
        elif input_type == "command":
            # Command injection prevention
            dangerous_chars = ['|', '&', ';', '$', '`', '>', '<', '\\', '!']
            sanitized = input_string
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '')
            return sanitized
        else:
            return input_string

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics and metrics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        recent_events = [e for e in self.audit_log if e.timestamp > last_24h]
        weekly_events = [e for e in self.audit_log if e.timestamp > last_7d]

        failed_logins_24h = len([e for e in recent_events if e.event_type == SecurityEventType.LOGIN_FAILURE])
        failed_logins_7d = len([e for e in weekly_events if e.event_type == SecurityEventType.LOGIN_FAILURE])

        active_sessions_count = len([s for s in self.active_sessions.values() if s.is_valid()])

        threat_events = len([e for e in recent_events if e.severity in ["high", "critical"]])

        return {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.is_active]),
            "locked_accounts": len([u for u in self.users.values() if u.is_locked]),
            "active_sessions": active_sessions_count,
            "failed_logins_24h": failed_logins_24h,
            "failed_logins_7d": failed_logins_7d,
            "threat_events_24h": threat_events,
            "audit_log_entries": len(self.audit_log),
            "rate_limited_ips": len([ip for ip, requests in self.rate_limits.items() if len(requests) >= self.policy.rate_limit_requests_per_minute]),
            "mfa_enabled_users": len([u for u in self.users.values() if u.mfa_enabled]),
            "api_keys_active": sum(len(u.api_keys) for u in self.users.values())
        }
"""
DuckBot Enhanced Authentication System

Advanced authentication system supporting:
- JWT token management
- Multi-factor authentication (MFA)
- OAuth2 integration
- Session management
- API key authentication
- Password policies and rotation

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import secrets
import hashlib
import re
import base64
import io
import qrcode
import pyotp
from pathlib import Path
import asyncio
import logging
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, validator, EmailStr
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import aiohttp
import aiofiles

auth_logger = logging.getLogger('duckbot.authentication')

class AuthMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    JWT = "jwt"
    API_KEY = "api_key"
    MFA_TOTP = "mfa_totp"
    OAUTH2 = "oauth2"
    SAML = "saml"
    CERTIFICATE = "certificate"

class OAuth2Provider(Enum):
    """OAuth2 providers"""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    APPLE = "apple"

class TokenType(Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    ID_TOKEN = "id_token"
    API_KEY = "api_key"

@dataclass
class AuthResult:
    """Authentication result"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    mfa_required: bool = False
    mfa_methods: List[str] = None
    error_message: Optional[str] = None
    additional_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.mfa_methods is None:
            self.mfa_methods = []
        if self.additional_info is None:
            self.additional_info = {}

class PasswordPolicy(BaseModel):
    """Password policy configuration"""
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    forbid_common_passwords: bool = True
    forbid_personal_info: bool = True
    max_repeated_chars: int = 2
    password_history: int = 5
    expiry_days: int = 90
    warning_days: int = 7
    complexity_score_min: int = 60

class MFASecret(BaseModel):
    """MFA secret configuration"""
    secret: str
    backup_codes: List[str]
    method: str = "totp"
    issuer: str = "DuckBot-v4.2"
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None

class OAuth2Config(BaseModel):
    """OAuth2 configuration"""
    provider: OAuth2Provider
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]
    auth_url: str
    token_url: str
    user_info_url: str
    enabled: bool = True

class TokenConfig(BaseModel):
    """Token configuration"""
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    id_token_expire_minutes: int = 60
    api_key_expire_days: int = 365
    issuer: str = "DuckBot-v4.2"
    audience: str = "duckbot-users"

class SessionConfig(BaseModel):
    """Session configuration"""
    timeout_minutes: int = 60
    max_concurrent_sessions: int = 5
    extend_on_activity: bool = True
    idle_timeout_minutes: int = 30
    secure_cookies: bool = True
    same_site_policy: str = "lax"

class AuthenticationSystem:
    """Main authentication system"""

    def __init__(self, jwt_secret: str, encryption_key: str,
                 password_policy: PasswordPolicy = None,
                 token_config: TokenConfig = None,
                 session_config: SessionConfig = None):
        self.jwt_secret = jwt_secret
        self.encryption_key = encryption_key
        self.fernet = Fernet(encryption_key.encode())
        self.password_policy = password_policy or PasswordPolicy()
        self.token_config = token_config or TokenConfig()
        self.session_config = session_config or SessionConfig()

        # Storage
        self.user_tokens: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.password_history: Dict[str, List[str]] = {}
        self.mfa_secrets: Dict[str, MFASecret] = {}
        self.oauth2_configs: Dict[str, OAuth2Config] = {}
        self.api_keys: Dict[str, Dict[str, Any]] = {}

        # Common passwords for validation
        self.common_passwords = self._load_common_passwords()

        auth_logger.info("AuthenticationSystem initialized")

    def _load_common_passwords(self) -> Set[str]:
        """Load common passwords for validation"""
        try:
            # This would typically be loaded from a file
            common_passwords = {
                "password", "123456", "12345678", "123456789", "12345",
                "qwerty", "abc123", "password1", "admin", "welcome",
                "letmein", "monkey", "sunshine", "password123", "admin123"
            }
            return common_passwords
        except Exception as e:
            auth_logger.error(f"Failed to load common passwords: {e}")
            return set()

    async def authenticate_user(self, username: str, password: str,
                               ip_address: str = None,
                               user_agent: str = None) -> AuthResult:
        """Authenticate user with username and password"""
        try:
            # This would typically query the user database
            user = await self._get_user_by_username(username)
            if not user:
                return AuthResult(
                    success=False,
                    error_message="Invalid username or password"
                )

            # Check if user is active
            if not user.get("is_active", True):
                return AuthResult(
                    success=False,
                    error_message="Account is disabled"
                )

            # Check if account is locked
            if user.get("is_locked", False):
                return AuthResult(
                    success=False,
                    error_message="Account is locked due to too many failed attempts"
                )

            # Verify password
            if not await self._verify_password(password, user["password_hash"]):
                await self._handle_failed_login(user["id"], username, ip_address)
                return AuthResult(
                    success=False,
                    error_message="Invalid username or password"
                )

            # Check if MFA is required
            mfa_required = await self._is_mfa_required(user["id"])
            if mfa_required:
                return AuthResult(
                    success=True,
                    user_id=user["id"],
                    username=username,
                    mfa_required=True,
                    mfa_methods=await self._get_available_mfa_methods(user["id"])
                )

            # Create session and tokens
            return await self._create_auth_session(user, ip_address, user_agent)

        except Exception as e:
            auth_logger.error(f"Authentication failed for {username}: {e}")
            return AuthResult(
                success=False,
                error_message="Authentication failed"
            )

    async def verify_mfa(self, user_id: str, mfa_code: str, method: str = "totp") -> AuthResult:
        """Verify MFA code"""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    error_message="User not found"
                )

            if method == "totp":
                if not await self._verify_totp(user_id, mfa_code):
                    return AuthResult(
                        success=False,
                        error_message="Invalid MFA code"
                    )

            elif method == "backup_code":
                if not await self._verify_backup_code(user_id, mfa_code):
                    return AuthResult(
                        success=False,
                        error_message="Invalid backup code"
                    )

            else:
                return AuthResult(
                    success=False,
                    error_message="Unsupported MFA method"
                )

            # Create session and tokens
            return await self._create_auth_session(user)

        except Exception as e:
            auth_logger.error(f"MFA verification failed for user {user_id}: {e}")
            return AuthResult(
                success=False,
                error_message="MFA verification failed"
            )

    async def authenticate_with_jwt(self, token: str) -> AuthResult:
        """Authenticate with JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            # Check if token is blacklisted
            if await self._is_token_blacklisted(token):
                return AuthResult(
                    success=False,
                    error_message="Token has been revoked"
                )

            user_id = payload.get("sub")
            if not user_id:
                return AuthResult(
                    success=False,
                    error_message="Invalid token"
                )

            user = await self._get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    error_message="User not found"
                )

            return AuthResult(
                success=True,
                user_id=user_id,
                username=user["username"],
                access_token=token,
                expires_at=datetime.fromtimestamp(payload.get("exp"))
            )

        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            auth_logger.warning(f"Invalid JWT token: {e}")
            return AuthResult(
                success=False,
                error_message="Invalid token"
            )

    async def authenticate_with_api_key(self, api_key: str) -> AuthResult:
        """Authenticate with API key"""
        try:
            key_info = self.api_keys.get(api_key)
            if not key_info:
                return AuthResult(
                    success=False,
                    error_message="Invalid API key"
                )

            # Check if key is expired
            if key_info.get("expires_at") and datetime.utcnow() > key_info["expires_at"]:
                return AuthResult(
                    success=False,
                    error_message="API key has expired"
                )

            # Check if key is revoked
            if key_info.get("revoked", False):
                return AuthResult(
                    success=False,
                    error_message="API key has been revoked"
                )

            user_id = key_info["user_id"]
            user = await self._get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    error_message="User not found"
                )

            return AuthResult(
                success=True,
                user_id=user_id,
                username=user["username"],
                session_id=f"api_{secrets.token_urlsafe(16)}"
            )

        except Exception as e:
            auth_logger.error(f"API key authentication failed: {e}")
            return AuthResult(
                success=False,
                error_message="API key authentication failed"
            )

    async def generate_oauth2_url(self, provider: str, state: str = None) -> str:
        """Generate OAuth2 authorization URL"""
        try:
            config = self.oauth2_configs.get(provider)
            if not config:
                raise ValueError(f"OAuth2 provider '{provider}' not configured")

            params = {
                "client_id": config.client_id,
                "redirect_uri": config.redirect_uri,
                "response_type": "code",
                "scope": " ".join(config.scopes)
            }

            if state:
                params["state"] = state

            return f"{config.auth_url}?{self._urlencode(params)}"

        except Exception as e:
            auth_logger.error(f"Failed to generate OAuth2 URL for {provider}: {e}")
            raise

    async def exchange_oauth2_code(self, provider: str, code: str, state: str = None) -> AuthResult:
        """Exchange OAuth2 authorization code for tokens"""
        try:
            config = self.oauth2_configs.get(provider)
            if not config:
                return AuthResult(
                    success=False,
                    error_message=f"OAuth2 provider '{provider}' not configured"
                )

            # Exchange code for tokens
            async with aiohttp.ClientSession() as session:
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": config.redirect_uri,
                    "client_id": config.client_id,
                    "client_secret": config.client_secret
                }

                async with session.post(config.token_url, data=data) as response:
                    if response.status != 200:
                        return AuthResult(
                            success=False,
                            error_message="Failed to exchange OAuth2 code"
                        )

                    token_data = await response.json()

                # Get user information
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                async with session.get(config.user_info_url, headers=headers) as response:
                    if response.status != 200:
                        return AuthResult(
                            success=False,
                            error_message="Failed to get user information"
                        )

                    user_info = await response.json()

            # Find or create user
            user = await self._find_or_create_oauth2_user(provider, user_info)
            if not user:
                return AuthResult(
                    success=False,
                    error_message="Failed to create user account"
                )

            return await self._create_auth_session(user)

        except Exception as e:
            auth_logger.error(f"OAuth2 code exchange failed for {provider}: {e}")
            return AuthResult(
                success=False,
                error_message="OAuth2 authentication failed"
            )

    async def create_user(self, username: str, email: str, password: str,
                         roles: List[str] = None) -> Dict[str, Any]:
        """Create a new user with validation"""
        try:
            # Validate input
            if not await self._validate_username(username):
                raise ValueError("Invalid username")

            if not await self._validate_email(email):
                raise ValueError("Invalid email address")

            # Validate password against policy
            password_validation = await self._validate_password_policy(password, username, email)
            if not password_validation["valid"]:
                raise ValueError(f"Password validation failed: {password_validation['message']}")

            # Check if user already exists
            if await self._user_exists(username):
                raise ValueError("Username already exists")

            if await self._email_exists(email):
                raise ValueError("Email already registered")

            # Hash password
            password_hash = await self._hash_password(password)

            # Create user
            user_id = hashlib.sha256(username.encode()).hexdigest()
            user = {
                "id": user_id,
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "roles": roles or ["user"],
                "is_active": True,
                "is_locked": False,
                "failed_login_attempts": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login_at": None,
                "password_changed_at": datetime.utcnow()
            }

            # Store user (in real implementation, this would save to database)
            await self._save_user(user)

            # Store password history
            self.password_history[user_id] = [password_hash]

            auth_logger.info(f"User created: {username}")
            return user

        except Exception as e:
            auth_logger.error(f"Failed to create user {username}: {e}")
            raise

    async def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """Setup MFA for user"""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")

            # Generate TOTP secret
            secret = pyotp.random_base32()
            backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]

            mfa_secret = MFASecret(
                secret=secret,
                backup_codes=backup_codes,
                issuer=self.token_config.issuer
            )

            self.mfa_secrets[user_id] = mfa_secret

            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user["email"],
                issuer_name=self.token_config.issuer
            )

            qr_img = qrcode.make(totp_uri)
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()

            return {
                "secret": secret,
                "backup_codes": backup_codes,
                "qr_code_base64": qr_base64,
                "totp_uri": totp_uri
            }

        except Exception as e:
            auth_logger.error(f"Failed to setup MFA for user {user_id}: {e}")
            raise

    async def enable_mfa(self, user_id: str, mfa_code: str) -> bool:
        """Enable MFA after verification"""
        try:
            if not await self._verify_totp(user_id, mfa_code):
                return False

            mfa_secret = self.mfa_secrets.get(user_id)
            if mfa_secret:
                mfa_secret.enabled = True
                mfa_secret.last_used = datetime.utcnow()

                # Update user record
                await self._update_user_mfa_status(user_id, True)

                auth_logger.info(f"MFA enabled for user {user_id}")
                return True

            return False

        except Exception as e:
            auth_logger.error(f"Failed to enable MFA for user {user_id}: {e}")
            return False

    async def disable_mfa(self, user_id: str, password: str) -> bool:
        """Disable MFA for user"""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return False

            # Verify password
            if not await self._verify_password(password, user["password_hash"]):
                return False

            # Remove MFA secret
            if user_id in self.mfa_secrets:
                del self.mfa_secrets[user_id]

            # Update user record
            await self._update_user_mfa_status(user_id, False)

            auth_logger.info(f"MFA disabled for user {user_id}")
            return True

        except Exception as e:
            auth_logger.error(f"Failed to disable MFA for user {user_id}: {e}")
            return False

    async def generate_api_key(self, user_id: str, description: str = None,
                              expires_days: int = None) -> str:
        """Generate new API key"""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")

            # Generate API key
            api_key = f"db_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Calculate expiration
            expire_days = expires_days or self.token_config.api_key_expire_days
            expires_at = datetime.utcnow() + timedelta(days=expire_days)

            # Store API key info
            self.api_keys[api_key] = {
                "key_hash": key_hash,
                "user_id": user_id,
                "description": description,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "revoked": False,
                "last_used": None
            }

            auth_logger.info(f"API key generated for user {user_id}")
            return api_key

        except Exception as e:
            auth_logger.error(f"Failed to generate API key for user {user_id}: {e}")
            raise

    async def revoke_api_key(self, user_id: str, api_key: str) -> bool:
        """Revoke API key"""
        try:
            key_info = self.api_keys.get(api_key)
            if key_info and key_info["user_id"] == user_id:
                key_info["revoked"] = True
                key_info["revoked_at"] = datetime.utcnow()

                auth_logger.info(f"API key revoked for user {user_id}")
                return True

            return False

        except Exception as e:
            auth_logger.error(f"Failed to revoke API key for user {user_id}: {e}")
            return False

    async def change_password(self, user_id: str, current_password: str,
                            new_password: str) -> bool:
        """Change user password"""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return False

            # Verify current password
            if not await self._verify_password(current_password, user["password_hash"]):
                return False

            # Validate new password
            password_validation = await self._validate_password_policy(
                new_password, user["username"], user["email"]
            )
            if not password_validation["valid"]:
                raise ValueError(f"Password validation failed: {password_validation['message']}")

            # Check password history
            if user_id in self.password_history:
                for old_hash in self.password_history[user_id]:
                    if await self._verify_password(new_password, old_hash):
                        raise ValueError("New password cannot be the same as a previous password")

            # Hash new password
            new_password_hash = await self._hash_password(new_password)

            # Update user
            user["password_hash"] = new_password_hash
            user["password_changed_at"] = datetime.utcnow()
            user["updated_at"] = datetime.utcnow()

            # Update password history
            if user_id not in self.password_history:
                self.password_history[user_id] = []
            self.password_history[user_id].append(new_password_hash)

            # Limit history size
            if len(self.password_history[user_id]) > self.password_policy.password_history:
                self.password_history[user_id] = self.password_history[user_id][-self.password_policy.password_history:]

            await self._save_user(user)

            # Revoke all active sessions
            await self._revoke_user_sessions(user_id)

            auth_logger.info(f"Password changed for user {user_id}")
            return True

        except Exception as e:
            auth_logger.error(f"Failed to change password for user {user_id}: {e}")
            return False

    async def _create_auth_session(self, user: Dict[str, Any],
                                 ip_address: str = None,
                                 user_agent: str = None) -> AuthResult:
        """Create authentication session and tokens"""
        try:
            # Generate session ID
            session_id = secrets.token_urlsafe(32)

            # Generate tokens
            access_token = await self._generate_access_token(user["id"], session_id)
            refresh_token = await self._generate_refresh_token(user["id"], session_id)
            id_token = await self._generate_id_token(user)

            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(minutes=self.token_config.access_token_expire_minutes)

            # Store session
            self.user_sessions[session_id] = {
                "user_id": user["id"],
                "username": user["username"],
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "active": True,
                "last_activity": datetime.utcnow()
            }

            # Store token
            self.user_tokens[access_token] = {
                "user_id": user["id"],
                "session_id": session_id,
                "type": TokenType.ACCESS.value,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "revoked": False
            }

            # Update user's last login
            user["last_login_at"] = datetime.utcnow()
            user["failed_login_attempts"] = 0
            await self._save_user(user)

            return AuthResult(
                success=True,
                user_id=user["id"],
                username=user["username"],
                session_id=session_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )

        except Exception as e:
            auth_logger.error(f"Failed to create auth session: {e}")
            return AuthResult(
                success=False,
                error_message="Failed to create session"
            )

    async def _generate_access_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT access token"""
        payload = {
            "sub": user_id,
            "session_id": session_id,
            "type": TokenType.ACCESS.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.token_config.access_token_expire_minutes),
            "iss": self.token_config.issuer,
            "aud": self.token_config.audience
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    async def _generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT refresh token"""
        payload = {
            "sub": user_id,
            "session_id": session_id,
            "type": TokenType.REFRESH.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=self.token_config.refresh_token_expire_days),
            "iss": self.token_config.issuer,
            "aud": self.token_config.audience
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    async def _generate_id_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT ID token"""
        payload = {
            "sub": user["id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "type": TokenType.ID_TOKEN.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.token_config.id_token_expire_minutes),
            "iss": self.token_config.issuer,
            "aud": self.token_config.audience
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    async def _verify_totp(self, user_id: str, mfa_code: str) -> bool:
        """Verify TOTP code"""
        try:
            mfa_secret = self.mfa_secrets.get(user_id)
            if not mfa_secret or not mfa_secret.enabled:
                return False

            totp = pyotp.TOTP(mfa_secret.secret)
            return totp.verify(mfa_code, valid_window=1)  # Allow 1 step window

        except Exception as e:
            auth_logger.error(f"TOTP verification failed for user {user_id}: {e}")
            return False

    async def _verify_backup_code(self, user_id: str, backup_code: str) -> bool:
        """Verify backup code"""
        try:
            mfa_secret = self.mfa_secrets.get(user_id)
            if not mfa_secret or not mfa_secret.enabled:
                return False

            if backup_code in mfa_secret.backup_codes:
                mfa_secret.backup_codes.remove(backup_code)
                return True

            return False

        except Exception as e:
            auth_logger.error(f"Backup code verification failed for user {user_id}: {e}")
            return False

    async def _validate_password_policy(self, password: str, username: str, email: str) -> Dict[str, Any]:
        """Validate password against security policy"""
        errors = []

        # Check length
        if len(password) < self.password_policy.min_length:
            errors.append(f"Password must be at least {self.password_policy.min_length} characters long")

        if len(password) > self.password_policy.max_length:
            errors.append(f"Password must be no more than {self.password_policy.max_length} characters long")

        # Check character requirements
        if self.password_policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if self.password_policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if self.password_policy.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        if self.password_policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Check common passwords
        if self.password_policy.forbid_common_passwords and password.lower() in self.common_passwords:
            errors.append("Password is too common")

        # Check personal information
        if self.password_policy.forbid_personal_info:
            username_lower = username.lower()
            email_lower = email.lower()
            password_lower = password.lower()

            if username_lower in password_lower:
                errors.append("Password cannot contain username")

            email_username = email_lower.split('@')[0]
            if email_username in password_lower:
                errors.append("Password cannot contain email username")

        # Check repeated characters
        if self.password_policy.max_repeated_chars > 0:
            for char in set(password):
                if password.count(char) > self.password_policy.max_repeated_chars:
                    errors.append(f"Character '{char}' is repeated too many times")
                    break

        # Calculate complexity score
        complexity_score = self._calculate_password_complexity(password)
        if complexity_score < self.password_policy.complexity_score_min:
            errors.append(f"Password complexity score too low: {complexity_score}")

        return {
            "valid": len(errors) == 0,
            "message": "; ".join(errors) if errors else "Password is valid",
            "complexity_score": complexity_score,
            "errors": errors
        }

    def _calculate_password_complexity(self, password: str) -> int:
        """Calculate password complexity score"""
        score = 0
        length = len(password)

        # Length score (0-30 points)
        score += min(length * 2, 30)

        # Character variety (0-40 points)
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 10

        # Entropy calculation (0-30 points)
        import math
        char_set_size = 0
        if re.search(r'[a-z]', password):
            char_set_size += 26
        if re.search(r'[A-Z]', password):
            char_set_size += 26
        if re.search(r'\d', password):
            char_set_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            char_set_size += 32

        if char_set_size > 0:
            entropy = length * math.log2(char_set_size)
            score += min(entropy / 2, 30)

        return min(int(score), 100)

    async def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    async def _is_mfa_required(self, user_id: str) -> bool:
        """Check if MFA is required for user"""
        mfa_secret = self.mfa_secrets.get(user_id)
        return mfa_secret and mfa_secret.enabled

    async def _get_available_mfa_methods(self, user_id: str) -> List[str]:
        """Get available MFA methods for user"""
        methods = []
        mfa_secret = self.mfa_secrets.get(user_id)

        if mfa_secret:
            if mfa_secret.backup_codes:
                methods.append("backup_code")
            methods.append("totp")

        return methods

    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        token_info = self.user_tokens.get(token)
        return token_info and token_info.get("revoked", False)

    async def _handle_failed_login(self, user_id: str, username: str, ip_address: str):
        """Handle failed login attempt"""
        # This would update failed login count and potentially lock account
        auth_logger.warning(f"Failed login attempt for {username} from {ip_address}")

    def _urlencode(self, params: Dict[str, str]) -> str:
        """URL encode parameters"""
        return "&".join(f"{k}={v}" for k, v in params.items())

    # Placeholder methods for database operations
    async def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (placeholder)"""
        # In real implementation, this would query the database
        return None

    async def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID (placeholder)"""
        # In real implementation, this would query the database
        return None

    async def _user_exists(self, username: str) -> bool:
        """Check if user exists (placeholder)"""
        # In real implementation, this would query the database
        return False

    async def _email_exists(self, email: str) -> bool:
        """Check if email exists (placeholder)"""
        # In real implementation, this would query the database
        return False

    async def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        return re.match(r'^[a-zA-Z0-9_-]+$', username) is not None

    async def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

    async def _save_user(self, user: Dict[str, Any]):
        """Save user to database (placeholder)"""
        # In real implementation, this would save to database
        pass

    async def _update_user_mfa_status(self, user_id: str, enabled: bool):
        """Update user MFA status (placeholder)"""
        # In real implementation, this would update the database
        pass

    async def _revoke_user_sessions(self, user_id: str):
        """Revoke all user sessions (placeholder)"""
        # In real implementation, this would update the database
        pass

    async def _find_or_create_oauth2_user(self, provider: str, user_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find or create user from OAuth2 (placeholder)"""
        # In real implementation, this would query the database
        return None
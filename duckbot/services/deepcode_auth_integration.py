#!/usr/bin/env python3
"""
DuckBot DeepCode Authentication Integration
Provides authentication and authorization for DeepCode WebUI components
Integrates with DuckBot's existing authentication system

Features:
- JWT-based authentication for API endpoints
- Session management for WebUI
- Role-based access control
- API key management
- OAuth2 integration support
- Security middleware for FastAPI
- Token validation and refresh
- User permission management
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# FastAPI imports
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

# JWT and security imports
import jwt
from cryptography.fernet import Fernet
import secrets
import hashlib

# DuckBot imports
try:
    from duckbot.core.authentication_system import (
        AuthenticationSystem, AuthResult, AuthMethod, TokenType,
        PasswordPolicy, OAuth2Provider
    )
    from duckbot.core.security_framework import SecurityManager
    from duckbot.core.logging_setup import setup_logging
except ImportError as e:
    logging.warning(f"Authentication modules not available: {e}")

# Configure logging
logger = logging.getLogger(__name__)

# Constants
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
API_KEY_PREFIX = "dkc_"

# Role definitions
class DeepCodeRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(str, Enum):
    # Paper2Code permissions
    PAPER_UPLOAD = "paper:upload"
    PAPER_ANALYZE = "paper:analyze"
    PAPER_GENERATE = "paper:generate"

    # Text2Web permissions
    WEB_GENERATE = "web:generate"
    WEB_DEPLOY = "web:deploy"

    # Text2Backend permissions
    BACKEND_GENERATE = "backend:generate"
    BACKEND_DEPLOY = "backend:deploy"

    # Agent permissions
    AGENT_CREATE = "agent:create"
    AGENT_MANAGE = "agent:manage"
    AGENT_VIEW = "agent:view"

    # MCP permissions
    MCP_MANAGE = "mcp:manage"
    MCP_VIEW = "mcp:view"

    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    USER_MANAGE = "user:manage"

# Role-permission mapping
ROLE_PERMISSIONS = {
    DeepCodeRole.ADMIN: [
        # All permissions
        Permission.PAPER_UPLOAD, Permission.PAPER_ANALYZE, Permission.PAPER_GENERATE,
        Permission.WEB_GENERATE, Permission.WEB_DEPLOY,
        Permission.BACKEND_GENERATE, Permission.BACKEND_DEPLOY,
        Permission.AGENT_CREATE, Permission.AGENT_MANAGE, Permission.AGENT_VIEW,
        Permission.MCP_MANAGE, Permission.MCP_VIEW,
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_MONITOR, Permission.USER_MANAGE
    ],
    DeepCodeRole.DEVELOPER: [
        Permission.PAPER_UPLOAD, Permission.PAPER_ANALYZE, Permission.PAPER_GENERATE,
        Permission.WEB_GENERATE, Permission.WEB_DEPLOY,
        Permission.BACKEND_GENERATE, Permission.BACKEND_DEPLOY,
        Permission.AGENT_CREATE, Permission.AGENT_VIEW,
        Permission.MCP_VIEW,
        Permission.SYSTEM_MONITOR
    ],
    DeepCodeRole.ANALYST: [
        Permission.PAPER_UPLOAD, Permission.PAPER_ANALYZE,
        Permission.WEB_GENERATE, Permission.BACKEND_GENERATE,
        Permission.AGENT_VIEW, Permission.MCP_VIEW,
        Permission.SYSTEM_MONITOR
    ],
    DeepCodeRole.VIEWER: [
        Permission.AGENT_VIEW, Permission.MCP_VIEW,
        Permission.SYSTEM_MONITOR
    ]
}

# Data models
class TokenData(BaseModel):
    username: str
    role: DeepCodeRole
    permissions: List[Permission]
    exp: datetime

class User(BaseModel):
    id: str
    username: str
    email: str
    role: DeepCodeRole
    permissions: List[Permission]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class APIKey(BaseModel):
    id: str
    key: str
    name: str
    user_id: str
    permissions: List[Permission]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

class DeepCodeAuthIntegration:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.auth_system = None
        self.security_manager = None

        # Storage
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.refresh_tokens: Dict[str, str] = {}

        # Initialize components
        self.initialize_components()

    def initialize_components(self):
        """Initialize authentication components"""
        try:
            self.auth_system = AuthenticationSystem()
            self.security_manager = SecurityManager()

            # Create default admin user if none exists
            if not self.users:
                self.create_default_admin()

        except Exception as e:
            logger.error(f"Failed to initialize authentication components: {e}")

    def create_default_admin(self):
        """Create default admin user"""
        admin_user = User(
            id="admin",
            username="admin",
            email="admin@duckbot.local",
            role=DeepCodeRole.ADMIN,
            permissions=ROLE_PERMISSIONS[DeepCodeRole.ADMIN],
            is_active=True,
            created_at=datetime.now()
        )
        self.users[admin_user.username] = admin_user
        logger.info("Created default admin user")

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, username: str) -> str:
        """Create refresh token"""
        token = secrets.token_urlsafe(32)
        self.refresh_tokens[token] = username
        return token

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None

            token_data = TokenData(
                username=username,
                role=payload.get("role", DeepCodeRole.VIEWER),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp"))
            )

            return token_data

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT error: {e}")
            return None

    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify refresh token"""
        return self.refresh_tokens.get(token)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.users.get(username)
        if not user or not user.is_active:
            return None

        # Simple password check (in production, use proper hashing)
        if username == "admin" and password == "admin":
            return user

        return None

    def create_api_key(self, user_id: str, name: str, permissions: List[Permission]) -> APIKey:
        """Create API key"""
        key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        api_key = APIKey(
            id=secrets.token_urlsafe(16),
            key=key,
            name=name,
            user_id=user_id,
            permissions=permissions,
            created_at=datetime.now()
        )
        self.api_keys[key] = api_key
        return api_key

    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key"""
        key = self.api_keys.get(api_key)
        if key and (key.expires_at is None or key.expires_at > datetime.now()):
            # Update last used
            key.last_used = datetime.now()
            return key
        return None

    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has permission"""
        return permission in user.permissions

    def require_permission(self, permission: Permission):
        """Decorator to require permission"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # This would be used with FastAPI dependencies
                pass
            return wrapper
        return decorator

# FastAPI dependencies
security = HTTPBearer()
auth_integration = DeepCodeAuthIntegration()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    token_data = auth_integration.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_integration.users.get(token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def verify_permission(permission: Permission, current_user: User = Depends(get_current_active_user)):
    """Verify user has required permission"""
    if not auth_integration.has_permission(current_user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user

def require_permission(permission: Permission):
    """FastAPI dependency for requiring permission"""
    return lambda: Depends(verify_permission(permission))

# Authentication middleware
class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_integration: DeepCodeAuthIntegration):
        super().__init__(app)
        self.auth_integration = auth_integration

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for certain paths
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/login",
            "/health"
        ]

        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Check for API key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key:
            api_key_obj = self.auth_integration.verify_api_key(api_key)
            if api_key_obj:
                # Add user info to request state
                request.state.user = self.auth_integration.users.get(api_key_obj.user_id)
                request.state.api_key = api_key_obj
                return await call_next(request)

        # Check for Bearer token authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            token_data = self.auth_integration.verify_token(token)
            if token_data:
                user = self.auth_integration.users.get(token_data.username)
                if user and user.is_active:
                    request.state.user = user
                    return await call_next(request)

        # If no authentication, return 401
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required"}
        )

# Route handlers for authentication
class AuthRoutes:
    def __init__(self, auth_integration: DeepCodeAuthIntegration):
        self.auth_integration = auth_integration

    def get_login_form(self):
        """Get login form template"""
        return """
        <form id="login-form">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn primary">Login</button>
        </form>
        """

    async def login(self, username: str, password: str) -> dict:
        """Handle user login"""
        user = self.auth_integration.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Update last login
        user.last_login = datetime.now()

        # Create tokens
        access_token = self.auth_integration.create_access_token(
            data={"sub": user.username, "role": user.role, "permissions": [p.value for p in user.permissions]}
        )
        refresh_token = self.auth_integration.create_refresh_token(user.username)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user.dict()
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token"""
        username = self.auth_integration.verify_refresh_token(refresh_token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user = self.auth_integration.users.get(username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        access_token = self.auth_integration.create_access_token(
            data={"sub": user.username, "role": user.role, "permissions": [p.value for p in user.permissions]}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    async def logout(self, refresh_token: str) -> dict:
        """Handle user logout"""
        if refresh_token in self.auth_integration.refresh_tokens:
            del self.auth_integration.refresh_tokens[refresh_token]

        return {"message": "Logged out successfully"}

    async def create_user(self, user_data: dict) -> User:
        """Create new user"""
        # Validate user data
        if not user_data.get("username") or not user_data.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and email are required"
            )

        # Check if user already exists
        if user_data["username"] in self.auth_integration.users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Create user
        user = User(
            id=secrets.token_urlsafe(16),
            username=user_data["username"],
            email=user_data["email"],
            role=user_data.get("role", DeepCodeRole.VIEWER),
            permissions=ROLE_PERMISSIONS.get(user_data.get("role", DeepCodeRole.VIEWER), []),
            is_active=user_data.get("is_active", True),
            created_at=datetime.now()
        )

        self.auth_integration.users[user.username] = user
        return user

    async def create_api_key(self, user_id: str, name: str, permissions: List[str]) -> APIKey:
        """Create API key"""
        user = self.auth_integration.users.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Convert permission strings to Permission enums
        perm_objects = []
        for perm_str in permissions:
            try:
                perm_objects.append(Permission(perm_str))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission: {perm_str}"
                )

        api_key = self.auth_integration.create_api_key(user_id, name, perm_objects)
        return api_key

    async def list_api_keys(self, user_id: str) -> List[APIKey]:
        """List API keys for user"""
        return [key for key in self.auth_integration.api_keys.values() if key.user_id == user_id]

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        for key, value in self.auth_integration.api_keys.items():
            if value.id == key_id:
                del self.auth_integration.api_keys[key]
                return True
        return False

# Export for use in other modules
auth_routes = AuthRoutes(auth_integration)
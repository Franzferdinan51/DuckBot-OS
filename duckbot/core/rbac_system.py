"""
DuckBot Role-Based Access Control (RBAC) System

Advanced RBAC implementation providing:
- Fine-grained permission management
- Role inheritance and composition
- Dynamic permission assignment
- Hierarchical role structure
- Permission templates and policies

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Set, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from pathlib import Path
import asyncio
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field, validator
import logging
from .security_framework import Permission, SecurityLevel

rbac_logger = logging.getLogger('duckbot.rbac')

class PermissionScope(Enum):
    """Permission scopes for granular access control"""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    DEPARTMENT = "department"
    TEAM = "team"
    PERSONAL = "personal"
    RESOURCE = "resource"

class AccessLevel(Enum):
    """Access levels for permissions"""
    NONE = 0
    READ = 1
    WRITE = 2
    EXECUTE = 3
    DELETE = 4
    ADMIN = 5

class RoleType(Enum):
    """Role types for different organizational levels"""
    SYSTEM = "system"
    ORGANIZATION = "organization"
    DEPARTMENT = "department"
    TEAM = "team"
    CUSTOM = "custom"

@dataclass
class PermissionGrant:
    """Individual permission grant with context"""
    permission: Permission
    scope: PermissionScope
    access_level: AccessLevel
    resource_id: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    granted_by: Optional[str] = None
    granted_at: datetime = field(default_factory=datetime.utcnow)

class RolePermission(BaseModel):
    """Role permission with enhanced attributes"""
    permission: Permission
    scope: PermissionScope = PermissionScope.GLOBAL
    access_level: AccessLevel = AccessLevel.READ
    resource_filter: Optional[str] = None  # JSON filter for resource selection
    conditions: Dict[str, Any] = Field(default_factory=dict)
    inheritable: bool = True
    temporary: bool = False
    expires_at: Optional[datetime] = None

class Role(BaseModel):
    """Enhanced role with RBAC features"""
    name: str
    display_name: str
    description: str
    role_type: RoleType
    permissions: List[RolePermission] = Field(default_factory=list)
    parent_roles: List[str] = Field(default_factory=list)  # Role inheritance
    child_roles: List[str] = Field(default_factory=list)   # Role composition
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_system_role: bool = False
    priority: int = 0  # For conflict resolution
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Role name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

    @validator('parent_roles')
    def validate_parent_roles(cls, v, values):
        # Prevent circular inheritance
        if 'name' in values and values['name'] in v:
            raise ValueError('Role cannot inherit from itself')
        return v

class PermissionTemplate(BaseModel):
    """Reusable permission template"""
    name: str
    description: str
    permissions: List[RolePermission]
    resource_types: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True

class AccessPolicy(BaseModel):
    """Access policy with conditional logic"""
    name: str
    description: str
    effect: str  # "allow" or "deny"
    permissions: List[Permission]
    conditions: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    scope: PermissionScope = PermissionScope.GLOBAL
    resource_patterns: List[str] = Field(default_factory=list)
    is_active: bool = True

@dataclass
class AccessRequest:
    """Access request for evaluation"""
    user_id: str
    username: str
    roles: List[str]
    requested_permission: Permission
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class AccessDecision:
    """Access control decision"""
    granted: bool
    reason: str
    decision_time: datetime
    policy_matches: List[str] = field(default_factory=list)
    conditions_met: bool = True
    expires_at: Optional[datetime] = None
    cached: bool = False

class RBACManager:
    """Advanced Role-Based Access Control Manager"""

    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, Dict[str, Any]] = {}  # user_id -> {roles, permissions, metadata}
        self.permission_templates: Dict[str, PermissionTemplate] = {}
        self.access_policies: Dict[str, AccessPolicy] = {}
        self.role_inheritance_cache: Dict[str, Set[str]] = {}
        self.permission_cache: Dict[str, Set[Permission]] = {}
        self.access_decision_cache: Dict[str, AccessDecision] = {}

        # Performance metrics
        self.access_requests_total = 0
        self.cache_hits = 0
        self.cache_misses = 0

        # Initialize default roles and templates
        self._initialize_default_roles()
        self._initialize_default_templates()
        self._initialize_default_policies()

        rbac_logger.info("RBACManager initialized")

    def _initialize_default_roles(self):
        """Initialize default system roles with enhanced permissions"""
        # Super Admin Role
        super_admin_role = Role(
            name="super_admin",
            display_name="Super Administrator",
            description="Complete system access with all permissions",
            role_type=RoleType.SYSTEM,
            is_system_role=True,
            priority=100
        )

        # Grant all permissions at global scope
        for permission in Permission:
            super_admin_role.permissions.append(RolePermission(
                permission=permission,
                scope=PermissionScope.GLOBAL,
                access_level=AccessLevel.ADMIN
            ))

        self.roles["super_admin"] = super_admin_role

        # Security Admin Role
        security_admin_role = Role(
            name="security_admin",
            display_name="Security Administrator",
            description="Security management and monitoring",
            role_type=RoleType.SYSTEM,
            is_system_role=True,
            priority=90,
            parent_roles=["admin"]  # Inherits from admin
        )

        security_permissions = [
            Permission.READ, Permission.WRITE, Permission.SECURITY_ADMIN,
            Permission.AUDIT_VIEW, Permission.USER_MANAGEMENT,
            Permission.SYSTEM_CONFIG, Permission.WEBUI_ACCESS
        ]

        for permission in security_permissions:
            security_admin_role.permissions.append(RolePermission(
                permission=permission,
                scope=PermissionScope.GLOBAL,
                access_level=AccessLevel.ADMIN
            ))

        self.roles["security_admin"] = security_admin_role

        # Admin Role
        admin_role = Role(
            name="admin",
            display_name="Administrator",
            description="System administration with elevated privileges",
            role_type=RoleType.SYSTEM,
            is_system_role=True,
            priority=80
        )

        admin_permissions = [
            Permission.READ, Permission.WRITE, Permission.EXECUTE,
            Permission.ADMIN, Permission.USER_MANAGEMENT,
            Permission.AUDIT_VIEW, Permission.SYSTEM_CONFIG,
            Permission.WEBUI_ACCESS, Permission.TERMINAL_ACCESS
        ]

        for permission in admin_permissions:
            admin_role.permissions.append(RolePermission(
                permission=permission,
                scope=PermissionScope.GLOBAL,
                access_level=AccessLevel.ADMIN
            ))

        self.roles["admin"] = admin_role

        # User Role
        user_role = Role(
            name="user",
            display_name="Standard User",
            description="Standard user with basic permissions",
            role_type=RoleType.SYSTEM,
            is_system_role=True,
            priority=50
        )

        user_permissions = [
            Permission.READ, Permission.WRITE, Permission.EXECUTE,
            Permission.WEBUI_ACCESS, Permission.TERMINAL_ACCESS,
            Permission.DESKTOP_AUTOMATION, Permission.AI_MODEL_ACCESS
        ]

        for permission in user_permissions:
            user_role.permissions.append(RolePermission(
                permission=permission,
                scope=PermissionScope.PERSONAL,
                access_level=AccessLevel.WRITE
            ))

        self.roles["user"] = user_role

        # Guest Role
        guest_role = Role(
            name="guest",
            display_name="Guest",
            description="Read-only access for temporary users",
            role_type=RoleType.SYSTEM,
            is_system_role=True,
            priority=10
        )

        guest_role.permissions.append(RolePermission(
            permission=Permission.READ,
            scope=PermissionScope.GLOBAL,
            access_level=AccessLevel.READ
        ))

        self.roles["guest"] = guest_role

    def _initialize_default_templates(self):
        """Initialize default permission templates"""
        # Read-only template
        readonly_template = PermissionTemplate(
            name="readonly",
            description="Read-only access template",
            permissions=[RolePermission(
                permission=Permission.READ,
                scope=PermissionScope.GLOBAL,
                access_level=AccessLevel.READ
            )],
            tags=["basic", "readonly"]
        )
        self.permission_templates["readonly"] = readonly_template

        # Web access template
        web_template = PermissionTemplate(
            name="web_access",
            description="Web UI access template",
            permissions=[
                RolePermission(
                    permission=Permission.READ,
                    scope=PermissionScope.GLOBAL,
                    access_level=AccessLevel.READ
                ),
                RolePermission(
                    permission=Permission.WEBUI_ACCESS,
                    scope=PermissionScope.GLOBAL,
                    access_level=AccessLevel.EXECUTE
                )
            ],
            tags=["web", "ui"]
        )
        self.permission_templates["web_access"] = web_template

    def _initialize_default_policies(self):
        """Initialize default access policies"""
        # Time-based access policy
        time_policy = AccessPolicy(
            name="business_hours_only",
            description="Restrict access to business hours",
            effect="allow",
            permissions=list(Permission),
            conditions={
                "time_range": {
                    "start": "09:00",
                    "end": "17:00",
                    "timezone": "UTC",
                    "weekdays": [1, 2, 3, 4, 5]  # Monday to Friday
                }
            },
            priority=50
        )
        self.access_policies["business_hours_only"] = time_policy

        # IP whitelist policy
        ip_policy = AccessPolicy(
            name="ip_whitelist",
            description="Allow access only from whitelisted IPs",
            effect="allow",
            permissions=list(Permission),
            conditions={
                "ip_whitelist": ["127.0.0.1", "::1", "192.168.1.0/24"]
            },
            priority=75
        )
        self.access_policies["ip_whitelist"] = ip_policy

    def create_role(self, role: Role) -> Role:
        """Create a new role"""
        if role.name in self.roles:
            raise ValueError(f"Role '{role.name}' already exists")

        # Validate parent roles exist
        for parent_name in role.parent_roles:
            if parent_name not in self.roles:
                raise ValueError(f"Parent role '{parent_name}' does not exist")

        # Update child roles in parent
        for parent_name in role.parent_roles:
            parent_role = self.roles[parent_name]
            if role.name not in parent_role.child_roles:
                parent_role.child_roles.append(role.name)

        self.roles[role.name] = role
        self._invalidate_inheritance_cache()

        rbac_logger.info(f"Created role: {role.name}")
        return role

    def update_role(self, role_name: str, updates: Dict[str, Any]) -> Role:
        """Update an existing role"""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' does not exist")

        role = self.roles[role_name]

        # Apply updates
        for key, value in updates.items():
            if hasattr(role, key):
                setattr(role, key, value)

        role.updated_at = datetime.utcnow()
        self._invalidate_inheritance_cache()

        rbac_logger.info(f"Updated role: {role_name}")
        return role

    def delete_role(self, role_name: str) -> bool:
        """Delete a role"""
        if role_name not in self.roles:
            return False

        role = self.roles[role_name]

        # Check if it's a system role
        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        # Remove from parent roles' child lists
        for parent_role in self.roles.values():
            if role_name in parent_role.child_roles:
                parent_role.child_roles.remove(role_name)

        # Remove from child roles' parent lists
        for child_role in self.roles.values():
            if role_name in child_role.parent_roles:
                child_role.parent_roles.remove(role_name)

        del self.roles[role_name]
        self._invalidate_inheritance_cache()

        rbac_logger.info(f"Deleted role: {role_name}")
        return True

    def assign_role_to_user(self, user_id: str, role_name: str,
                           assigned_by: str = None, expires_at: datetime = None) -> bool:
        """Assign a role to a user"""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' does not exist")

        if user_id not in self.users:
            self.users[user_id] = {
                "roles": [],
                "direct_permissions": [],
                "metadata": {},
                "role_assignments": {}
            }

        # Check if role is already assigned
        for assignment in self.users[user_id]["role_assignments"].values():
            if assignment["role_name"] == role_name and assignment["active"]:
                return False

        # Create role assignment
        assignment_id = f"{user_id}_{role_name}_{datetime.utcnow().timestamp()}"
        self.users[user_id]["role_assignments"][assignment_id] = {
            "role_name": role_name,
            "assigned_by": assigned_by,
            "assigned_at": datetime.utcnow(),
            "expires_at": expires_at,
            "active": True
        }

        # Add to roles list
        if role_name not in self.users[user_id]["roles"]:
            self.users[user_id]["roles"].append(role_name)

        self._invalidate_permission_cache(user_id)

        rbac_logger.info(f"Assigned role '{role_name}' to user '{user_id}'")
        return True

    def remove_role_from_user(self, user_id: str, role_name: str,
                            removed_by: str = None) -> bool:
        """Remove a role from a user"""
        if user_id not in self.users:
            return False

        # Deactivate role assignment
        for assignment_id, assignment in self.users[user_id]["role_assignments"].items():
            if assignment["role_name"] == role_name and assignment["active"]:
                assignment["active"] = False
                assignment["removed_by"] = removed_by
                assignment["removed_at"] = datetime.utcnow()

                # Remove from roles list
                if role_name in self.users[user_id]["roles"]:
                    self.users[user_id]["roles"].remove(role_name)

                self._invalidate_permission_cache(user_id)

                rbac_logger.info(f"Removed role '{role_name}' from user '{user_id}'")
                return True

        return False

    def grant_permission_to_user(self, user_id: str, permission_grant: PermissionGrant,
                               granted_by: str = None) -> bool:
        """Grant direct permission to user"""
        if user_id not in self.users:
            self.users[user_id] = {
                "roles": [],
                "direct_permissions": [],
                "metadata": {},
                "role_assignments": {}
            }

        # Add permission grant
        self.users[user_id]["direct_permissions"].append({
            "permission": permission_grant.permission.value,
            "scope": permission_grant.scope.value,
            "access_level": permission_grant.access_level.value,
            "resource_id": permission_grant.resource_id,
            "conditions": permission_grant.conditions,
            "expires_at": permission_grant.expires_at,
            "granted_by": granted_by,
            "granted_at": permission_grant.granted_at
        })

        self._invalidate_permission_cache(user_id)

        rbac_logger.info(f"Granted permission '{permission_grant.permission.value}' to user '{user_id}'")
        return True

    def revoke_permission_from_user(self, user_id: str, permission: Permission,
                                  scope: PermissionScope = None, resource_id: str = None) -> bool:
        """Revoke permission from user"""
        if user_id not in self.users:
            return False

        revoked = False
        updated_permissions = []

        for perm_grant in self.users[user_id]["direct_permissions"]:
            should_remove = (
                perm_grant["permission"] == permission.value and
                (scope is None or perm_grant["scope"] == scope.value) and
                (resource_id is None or perm_grant["resource_id"] == resource_id)
            )

            if not should_remove:
                updated_permissions.append(perm_grant)
            else:
                revoked = True

        if revoked:
            self.users[user_id]["direct_permissions"] = updated_permissions
            self._invalidate_permission_cache(user_id)

            rbac_logger.info(f"Revoked permission '{permission.value}' from user '{user_id}'")

        return revoked

    def evaluate_access(self, request: AccessRequest) -> AccessDecision:
        """Evaluate access request and return decision"""
        self.access_requests_total += 1

        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_decision = self.access_decision_cache.get(cache_key)

        if cached_decision and cached_decision.expires_at and cached_decision.expires_at > datetime.utcnow():
            self.cache_hits += 1
            cached_decision.cached = True
            return cached_decision

        self.cache_misses += 1

        # Get user's effective permissions
        effective_permissions = self._get_user_effective_permissions(request.user_id)

        # Check direct permission grants
        permission_granted = False
        grant_reasons = []

        # Check role-based permissions
        for role_name in request.roles:
            role_permissions = self._get_role_effective_permissions(role_name)
            for perm_grant in role_permissions:
                if self._evaluate_permission_grant(perm_grant, request):
                    permission_granted = True
                    grant_reasons.append(f"Role '{role_name}' grants {request.requested_permission.value}")

        # Check direct permissions
        for perm_grant in self.users.get(request.user_id, {}).get("direct_permissions", []):
            if (Permission(perm_grant["permission"]) == request.requested_permission and
                self._evaluate_permission_grant(perm_grant, request)):
                permission_granted = True
                grant_reasons.append("Direct permission grant")

        # Evaluate access policies
        policy_decisions = self._evaluate_access_policies(request)

        # Make final decision
        # Policies override role permissions
        if policy_decisions:
            final_decision = policy_decisions[0].effect == "allow"
            reason = f"Policy '{policy_decisions[0].name}' decision"
        else:
            final_decision = permission_granted
            reason = "; ".join(grant_reasons) if grant_reasons else "Permission not granted"

        # Create decision
        decision = AccessDecision(
            granted=final_decision,
            reason=reason,
            decision_time=datetime.utcnow(),
            policy_matches=[p.name for p in policy_decisions],
            expires_at=datetime.utcnow() + timedelta(minutes=30)  # Cache for 30 minutes
        )

        # Cache decision
        self.access_decision_cache[cache_key] = decision

        # Log access request
        self._log_access_request(request, decision)

        return decision

    def _get_user_effective_permissions(self, user_id: str) -> Set[Permission]:
        """Get all effective permissions for a user including inheritance"""
        cache_key = f"user_permissions_{user_id}"

        if cache_key in self.permission_cache:
            return self.permission_cache[cache_key]

        permissions = set()

        if user_id in self.users:
            # Get permissions from roles
            for role_name in self.users[user_id]["roles"]:
                role_permissions = self._get_role_effective_permissions(role_name)
                permissions.update(role_permissions)

            # Add direct permissions
            for perm_grant in self.users[user_id]["direct_permissions"]:
                permissions.add(Permission(perm_grant["permission"]))

        # Cache result
        self.permission_cache[cache_key] = permissions
        return permissions

    def _get_role_effective_permissions(self, role_name: str) -> Set[Permission]:
        """Get effective permissions for a role including inheritance"""
        if role_name not in self.roles:
            return set()

        permissions = set()

        # Get all roles in inheritance chain
        all_roles = self._get_role_inheritance_chain(role_name)

        for current_role_name in all_roles:
            role = self.roles[current_role_name]
            for perm in role.permissions:
                permissions.add(perm.permission)

        return permissions

    def _get_role_inheritance_chain(self, role_name: str) -> Set[str]:
        """Get all roles in inheritance chain"""
        cache_key = f"role_inheritance_{role_name}"

        if cache_key in self.role_inheritance_cache:
            return self.role_inheritance_cache[cache_key]

        inheritance_chain = set()

        if role_name in self.roles:
            self._build_inheritance_chain(role_name, inheritance_chain)

        # Cache result
        self.role_inheritance_cache[cache_key] = inheritance_chain
        return inheritance_chain

    def _build_inheritance_chain(self, role_name: str, chain: Set[str], visited: Set[str] = None):
        """Recursively build inheritance chain"""
        if visited is None:
            visited = set()

        if role_name in visited:
            return  # Prevent circular inheritance

        visited.add(role_name)
        chain.add(role_name)

        if role_name in self.roles:
            for parent_role in self.roles[role_name].parent_roles:
                self._build_inheritance_chain(parent_role, chain, visited)

    def _evaluate_permission_grant(self, permission_grant: Dict[str, Any], request: AccessRequest) -> bool:
        """Evaluate if a permission grant matches the request"""
        # Check if permission matches
        if Permission(permission_grant["permission"]) != request.requested_permission:
            return False

        # Check scope
        scope = PermissionScope(permission_grant["scope"])
        if scope == PermissionScope.PERSONAL and request.resource_id != request.user_id:
            return False

        # Check expiration
        if permission_grant.get("expires_at") and permission_grant["expires_at"] <= datetime.utcnow():
            return False

        # Check conditions
        conditions = permission_grant.get("conditions", {})
        if not self._evaluate_conditions(conditions, request.context):
            return False

        return True

    def _evaluate_access_policies(self, request: AccessRequest) -> List[AccessPolicy]:
        """Evaluate access policies for the request"""
        matching_policies = []

        for policy in self.access_policies.values():
            if not policy.is_active:
                continue

            # Check if policy applies to requested permission
            if request.requested_permission not in policy.permissions:
                continue

            # Check conditions
            if not self._evaluate_conditions(policy.conditions, request.context):
                continue

            matching_policies.append(policy)

        # Sort by priority (higher priority first)
        matching_policies.sort(key=lambda p: p.priority, reverse=True)
        return matching_policies

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate policy conditions"""
        if not conditions:
            return True

        # Time-based conditions
        if "time_range" in conditions:
            time_range = conditions["time_range"]
            if not self._evaluate_time_condition(time_range):
                return False

        # IP-based conditions
        if "ip_whitelist" in conditions and context.get("ip_address"):
            if context["ip_address"] not in conditions["ip_whitelist"]:
                return False

        # Custom conditions
        if "custom" in conditions:
            # Implement custom condition evaluation logic here
            pass

        return True

    def _evaluate_time_condition(self, time_range: Dict[str, Any]) -> bool:
        """Evaluate time-based conditions"""
        try:
            from datetime import time
            import pytz

            now = datetime.utcnow()
            if "timezone" in time_range:
                tz = pytz.timezone(time_range["timezone"])
                now = datetime.now(tz)

            current_time = now.time()
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday

            # Check weekday
            if "weekdays" in time_range:
                if current_weekday not in time_range["weekdays"]:
                    return False

            # Check time range
            if "start" in time_range and "end" in time_range:
                start_time = time.fromisoformat(time_range["start"])
                end_time = time.fromisoformat(time_range["end"])

                if start_time <= current_time <= end_time:
                    return True
                else:
                    return False

            return True

        except Exception as e:
            rbac_logger.warning(f"Failed to evaluate time condition: {e}")
            return True  # Fail open for time conditions

    def _generate_cache_key(self, request: AccessRequest) -> str:
        """Generate cache key for access decision"""
        key_parts = [
            request.user_id,
            request.requested_permission.value,
            str(sorted(request.roles)),
            request.resource_type or "",
            request.resource_id or ""
        ]
        return "|".join(key_parts)

    def _invalidate_inheritance_cache(self):
        """Clear role inheritance cache"""
        self.role_inheritance_cache.clear()

    def _invalidate_permission_cache(self, user_id: str = None):
        """Clear permission cache"""
        if user_id:
            cache_key = f"user_permissions_{user_id}"
            if cache_key in self.permission_cache:
                del self.permission_cache[cache_key]
        else:
            self.permission_cache.clear()

    def _log_access_request(self, request: AccessRequest, decision: AccessDecision):
        """Log access request for audit purposes"""
        log_message = (
            f"Access Request: User={request.username}, "
            f"Permission={request.requested_permission.value}, "
            f"Decision={'GRANTED' if decision.granted else 'DENIED'}, "
            f"Reason={decision.reason}"
        )

        if decision.granted:
            rbac_logger.info(log_message)
        else:
            rbac_logger.warning(log_message)

    def get_user_roles(self, user_id: str) -> List[str]:
        """Get all roles assigned to a user"""
        return self.users.get(user_id, {}).get("roles", [])

    def get_role_users(self, role_name: str) -> List[str]:
        """Get all users assigned to a role"""
        users = []
        for user_id, user_data in self.users.items():
            if role_name in user_data["roles"]:
                users.append(user_id)
        return users

    def get_role_details(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed role information"""
        if role_name not in self.roles:
            return None

        role = self.roles[role_name]
        return {
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "role_type": role.role_type.value,
            "permissions": [
                {
                    "permission": perm.permission.value,
                    "scope": perm.scope.value,
                    "access_level": perm.access_level.value
                }
                for perm in role.permissions
            ],
            "parent_roles": role.parent_roles,
            "child_roles": role.child_roles,
            "priority": role.priority,
            "is_active": role.is_active,
            "is_system_role": role.is_system_role,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }

    def get_rbac_stats(self) -> Dict[str, Any]:
        """Get RBAC system statistics"""
        active_roles = len([r for r in self.roles.values() if r.is_active])
        total_users = len(self.users)
        active_users = len([u for u in self.users.values() if u.get("roles")])

        return {
            "total_roles": len(self.roles),
            "active_roles": active_roles,
            "system_roles": len([r for r in self.roles.values() if r.is_system_role]),
            "custom_roles": len([r for r in self.roles.values() if not r.is_system_role]),
            "total_users": total_users,
            "active_users": active_users,
            "total_permission_templates": len(self.permission_templates),
            "total_access_policies": len(self.access_policies),
            "access_requests_total": self.access_requests_total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "cache_size": len(self.access_decision_cache)
        }

    def cleanup_expired_grants(self):
        """Clean up expired permission grants and role assignments"""
        now = datetime.utcnow()
        cleaned_count = 0

        for user_data in self.users.values():
            # Clean up expired direct permissions
            active_permissions = []
            for perm_grant in user_data.get("direct_permissions", []):
                if not perm_grant.get("expires_at") or perm_grant["expires_at"] > now:
                    active_permissions.append(perm_grant)
                else:
                    cleaned_count += 1

            if "direct_permissions" in user_data:
                user_data["direct_permissions"] = active_permissions

            # Clean up expired role assignments
            active_roles = []
            for role_assignment in user_data.get("role_assignments", {}).values():
                if (role_assignment["active"] and
                    (not role_assignment.get("expires_at") or role_assignment["expires_at"] > now)):
                    active_roles.append(role_assignment["role_name"])
                elif role_assignment["active"]:
                    role_assignment["active"] = False
                    cleaned_count += 1

            user_data["roles"] = active_roles

        # Clean up expired cache entries
        expired_cache_keys = []
        for key, decision in self.access_decision_cache.items():
            if decision.expires_at and decision.expires_at <= now:
                expired_cache_keys.append(key)

        for key in expired_cache_keys:
            del self.access_decision_cache[key]
            cleaned_count += 1

        # Clear caches if data was modified
        if cleaned_count > 0:
            self._invalidate_permission_cache()
            rbac_logger.info(f"Cleaned up {cleaned_count} expired grants and cache entries")

        return cleaned_count
"""
Role-Based Access Control (RBAC) System
Comprehensive roles and permissions mapping for JWT authentication
"""

import logging
from enum import Enum
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, status

try:
    from jwt_auth_service import get_current_active_user
except ImportError:
    from .jwt_auth_service import get_current_active_user

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles enumeration"""

    ADMIN = "admin"
    USER = "user"
    DEVELOPER = "developer"
    GUEST = "guest"
    SERVICE_ACCOUNT = "service_account"


class Permission(str, Enum):
    """System permissions enumeration"""

    # Agent Management
    AGENT_VIEW = "agent:view"
    AGENT_CREATE = "agent:create"
    AGENT_EDIT = "agent:edit"
    AGENT_DELETE = "agent:delete"
    AGENT_RELOAD = "agent:reload"

    # Conversation Management
    CONVERSATION_VIEW = "conversation:view"
    CONVERSATION_CREATE = "conversation:create"
    CONVERSATION_EDIT = "conversation:edit"
    CONVERSATION_DELETE = "conversation:delete"
    CONVERSATION_VIEW_ALL = "conversation:view_all"

    # Workflow Management
    WORKFLOW_VIEW = "workflow:view"
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_EDIT = "workflow:edit"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_VIEW_ALL = "workflow:view_all"

    # File Processing
    FILE_UPLOAD = "file:upload"
    FILE_PROCESS = "file:process"
    FILE_VIEW = "file:view"
    FILE_DELETE = "file:delete"
    FILE_VIEW_ALL = "file:view_all"

    # System Management
    SYSTEM_VIEW = "system:view"
    SYSTEM_STATS = "system:stats"
    SYSTEM_HEALTH = "system:health"
    SYSTEM_MONITOR = "system:monitor"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_BASIC = "analytics:basic"
    ANALYTICS_ADVANCED = "analytics:advanced"
    ANALYTICS_EXPORT = "analytics:export"

    # User Management
    USER_VIEW_SELF = "user:view_self"
    USER_EDIT_SELF = "user:edit_self"
    USER_VIEW_ALL = "user:view_all"
    USER_EDIT_ALL = "user:edit_all"
    USER_DELETE = "user:delete"
    USER_CREATE = "user:create"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Session Management
    SESSION_VIEW_SELF = "session:view_self"
    SESSION_MANAGE_SELF = "session:manage_self"
    SESSION_VIEW_ALL = "session:view_all"
    SESSION_MANAGE_ALL = "session:manage_all"

    # API Key Management
    API_KEY_CREATE = "api_key:create"
    API_KEY_VIEW_SELF = "api_key:view_self"
    API_KEY_MANAGE_SELF = "api_key:manage_self"
    API_KEY_VIEW_ALL = "api_key:view_all"
    API_KEY_MANAGE_ALL = "api_key:manage_all"

    # Administration
    ADMIN_ALL = "admin:all"
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_ANALYTICS = "admin:analytics"
    ADMIN_CLEANUP = "admin:cleanup"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: {
        # Full system access
        Permission.ADMIN_ALL,
        Permission.ADMIN_USERS,
        Permission.ADMIN_SYSTEM,
        Permission.ADMIN_ANALYTICS,
        Permission.ADMIN_CLEANUP,
        # Full agent management
        Permission.AGENT_VIEW,
        Permission.AGENT_CREATE,
        Permission.AGENT_EDIT,
        Permission.AGENT_DELETE,
        Permission.AGENT_RELOAD,
        # Full conversation management
        Permission.CONVERSATION_VIEW,
        Permission.CONVERSATION_CREATE,
        Permission.CONVERSATION_EDIT,
        Permission.CONVERSATION_DELETE,
        Permission.CONVERSATION_VIEW_ALL,
        # Full workflow management
        Permission.WORKFLOW_VIEW,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_EDIT,
        Permission.WORKFLOW_DELETE,
        Permission.WORKFLOW_EXECUTE,
        Permission.WORKFLOW_VIEW_ALL,
        # Full file management
        Permission.FILE_UPLOAD,
        Permission.FILE_PROCESS,
        Permission.FILE_VIEW,
        Permission.FILE_DELETE,
        Permission.FILE_VIEW_ALL,
        # Full system access
        Permission.SYSTEM_VIEW,
        Permission.SYSTEM_STATS,
        Permission.SYSTEM_HEALTH,
        Permission.SYSTEM_MONITOR,
        # Full analytics
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_BASIC,
        Permission.ANALYTICS_ADVANCED,
        Permission.ANALYTICS_EXPORT,
        # Full user management
        Permission.USER_VIEW_SELF,
        Permission.USER_EDIT_SELF,
        Permission.USER_VIEW_ALL,
        Permission.USER_EDIT_ALL,
        Permission.USER_DELETE,
        Permission.USER_CREATE,
        Permission.USER_MANAGE_ROLES,
        # Full session management
        Permission.SESSION_VIEW_SELF,
        Permission.SESSION_MANAGE_SELF,
        Permission.SESSION_VIEW_ALL,
        Permission.SESSION_MANAGE_ALL,
        # Full API key management
        Permission.API_KEY_CREATE,
        Permission.API_KEY_VIEW_SELF,
        Permission.API_KEY_MANAGE_SELF,
        Permission.API_KEY_VIEW_ALL,
        Permission.API_KEY_MANAGE_ALL,
    },
    UserRole.DEVELOPER: {
        # Agent management (create/edit)
        Permission.AGENT_VIEW,
        Permission.AGENT_CREATE,
        Permission.AGENT_EDIT,
        Permission.AGENT_RELOAD,
        # Conversation management
        Permission.CONVERSATION_VIEW,
        Permission.CONVERSATION_CREATE,
        Permission.CONVERSATION_EDIT,
        Permission.CONVERSATION_DELETE,
        # Workflow management
        Permission.WORKFLOW_VIEW,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_EDIT,
        Permission.WORKFLOW_DELETE,
        Permission.WORKFLOW_EXECUTE,
        # File processing
        Permission.FILE_UPLOAD,
        Permission.FILE_PROCESS,
        Permission.FILE_VIEW,
        Permission.FILE_DELETE,
        # System access (limited)
        Permission.SYSTEM_VIEW,
        Permission.SYSTEM_HEALTH,
        # Analytics (advanced)
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_BASIC,
        Permission.ANALYTICS_ADVANCED,
        Permission.ANALYTICS_EXPORT,
        # Self management
        Permission.USER_VIEW_SELF,
        Permission.USER_EDIT_SELF,
        Permission.SESSION_VIEW_SELF,
        Permission.SESSION_MANAGE_SELF,
        # API key management
        Permission.API_KEY_CREATE,
        Permission.API_KEY_VIEW_SELF,
        Permission.API_KEY_MANAGE_SELF,
    },
    UserRole.USER: {
        # Agent viewing
        Permission.AGENT_VIEW,
        # Conversation management (own)
        Permission.CONVERSATION_VIEW,
        Permission.CONVERSATION_CREATE,
        Permission.CONVERSATION_EDIT,
        Permission.CONVERSATION_DELETE,
        # Workflow viewing and execution
        Permission.WORKFLOW_VIEW,
        Permission.WORKFLOW_EXECUTE,
        # File processing
        Permission.FILE_UPLOAD,
        Permission.FILE_PROCESS,
        Permission.FILE_VIEW,
        # System health check
        Permission.SYSTEM_HEALTH,
        # Basic analytics
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_BASIC,
        # Self management
        Permission.USER_VIEW_SELF,
        Permission.USER_EDIT_SELF,
        Permission.SESSION_VIEW_SELF,
        Permission.SESSION_MANAGE_SELF,
        # Limited API key management
        Permission.API_KEY_CREATE,
        Permission.API_KEY_VIEW_SELF,
        Permission.API_KEY_MANAGE_SELF,
    },
    UserRole.GUEST: {
        # Very limited access - mostly read-only
        Permission.AGENT_VIEW,
        Permission.SYSTEM_HEALTH,
        # Self management
        Permission.USER_VIEW_SELF,
        Permission.SESSION_VIEW_SELF,
    },
    UserRole.SERVICE_ACCOUNT: {
        # API-focused permissions
        Permission.AGENT_VIEW,
        # Conversation creation (for bots/services)
        Permission.CONVERSATION_CREATE,
        Permission.CONVERSATION_VIEW,
        # Workflow execution
        Permission.WORKFLOW_VIEW,
        Permission.WORKFLOW_EXECUTE,
        # File processing
        Permission.FILE_UPLOAD,
        Permission.FILE_PROCESS,
        # System health monitoring
        Permission.SYSTEM_HEALTH,
        Permission.SYSTEM_VIEW,
        # Self management
        Permission.USER_VIEW_SELF,
        Permission.SESSION_VIEW_SELF,
        Permission.API_KEY_VIEW_SELF,
    },
}


class RolePermissionManager:
    """Manages role and permission operations"""

    @staticmethod
    def get_permissions_for_role(role: UserRole) -> set[Permission]:
        """Get all permissions for a specific role"""
        return ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def user_has_permission(user: dict[str, Any], permission: Permission) -> bool:
        """Check if user has a specific permission"""
        user_role = UserRole(user.get("role", UserRole.GUEST))
        user_permissions = RolePermissionManager.get_permissions_for_role(user_role)

        # Admin has all permissions
        if Permission.ADMIN_ALL in user_permissions:
            return True

        return permission in user_permissions

    @staticmethod
    def user_has_any_permission(user: dict[str, Any], permissions: list[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(RolePermissionManager.user_has_permission(user, perm) for perm in permissions)

    @staticmethod
    def user_has_all_permissions(user: dict[str, Any], permissions: list[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(RolePermissionManager.user_has_permission(user, perm) for perm in permissions)

    @staticmethod
    def get_user_permissions(user: dict[str, Any]) -> set[Permission]:
        """Get all permissions for a user"""
        user_role = UserRole(user.get("role", UserRole.GUEST))
        return RolePermissionManager.get_permissions_for_role(user_role)

    @staticmethod
    def is_valid_role(role: str) -> bool:
        """Check if role is valid"""
        try:
            UserRole(role)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_all_roles() -> list[str]:
        """Get all available roles"""
        return [role.value for role in UserRole]

    @staticmethod
    def get_all_permissions() -> list[str]:
        """Get all available permissions"""
        return [perm.value for perm in Permission]


# FastAPI Permission Dependencies
def require_permission(permission: Permission):
    """FastAPI dependency factory to require specific permission"""

    def permission_checker(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        if not RolePermissionManager.user_has_permission(current_user, permission):
            logger.warning(
                f"User {current_user.get('username')} with role {current_user.get('role')} "
                f"attempted to access endpoint requiring permission: {permission.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}",
            )
        return current_user

    return permission_checker


def require_any_permission(permissions: list[Permission]):
    """FastAPI dependency factory to require any of the specified permissions"""

    def permission_checker(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        if not RolePermissionManager.user_has_any_permission(current_user, permissions):
            permission_list = [perm.value for perm in permissions]
            logger.warning(
                f"User {current_user.get('username')} with role {current_user.get('role')} "
                f"attempted to access endpoint requiring one of permissions: {permission_list}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions. Need one of: {permission_list}",
            )
        return current_user

    return permission_checker


def require_all_permissions(permissions: list[Permission]):
    """FastAPI dependency factory to require all of the specified permissions"""

    def permission_checker(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        if not RolePermissionManager.user_has_all_permissions(current_user, permissions):
            permission_list = [perm.value for perm in permissions]
            logger.warning(
                f"User {current_user.get('username')} with role {current_user.get('role')} "
                f"attempted to access endpoint requiring all permissions: {permission_list}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions. Need all of: {permission_list}",
            )
        return current_user

    return permission_checker


# Common permission combinations as convenience dependencies
def require_admin_access(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require admin role (backward compatibility)"""
    return require_permission(Permission.ADMIN_ALL)(current_user)


def require_agent_management(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require agent management permissions"""
    return require_any_permission(
        [Permission.AGENT_CREATE, Permission.AGENT_EDIT, Permission.ADMIN_ALL]
    )(current_user)


def require_conversation_access(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require conversation access permissions"""
    return require_permission(Permission.CONVERSATION_CREATE)(current_user)


def require_workflow_access(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require workflow access permissions"""
    return require_permission(Permission.WORKFLOW_EXECUTE)(current_user)


def require_file_access(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require file processing permissions"""
    return require_permission(Permission.FILE_UPLOAD)(current_user)


def require_analytics_access(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require analytics access permissions"""
    return require_permission(Permission.ANALYTICS_VIEW)(current_user)


def require_user_management(
    current_user: dict[str, Any] = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Require user management permissions"""
    return require_permission(Permission.USER_EDIT_ALL)(current_user)


# Permission checking decorator for non-FastAPI functions
def check_permission(permission: Permission):
    """Decorator to check permissions for regular functions"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first argument is user dict
            user = args[0] if args else None
            if not user or not isinstance(user, dict):
                raise ValueError("First argument must be user dictionary")

            if not RolePermissionManager.user_has_permission(user, permission):
                raise PermissionError(f"User missing required permission: {permission.value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Role hierarchy helper
ROLE_HIERARCHY = {
    UserRole.ADMIN: 5,
    UserRole.DEVELOPER: 4,
    UserRole.USER: 3,
    UserRole.SERVICE_ACCOUNT: 2,
    UserRole.GUEST: 1,
}


def get_role_level(role: UserRole) -> int:
    """Get numeric level for role (higher = more permissions)"""
    return ROLE_HIERARCHY.get(role, 0)


def role_has_higher_or_equal_level(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if user role has higher or equal level than required role"""
    return get_role_level(user_role) >= get_role_level(required_role)


# Export commonly used permissions and roles
__all__ = [
    "UserRole",
    "Permission",
    "RolePermissionManager",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_admin_access",
    "require_agent_management",
    "require_conversation_access",
    "require_workflow_access",
    "require_file_access",
    "require_analytics_access",
    "require_user_management",
    "check_permission",
    "ROLE_PERMISSIONS",
    "ROLE_HIERARCHY",
]

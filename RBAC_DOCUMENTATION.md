# Role-Based Access Control (RBAC) System

## 🎯 Overview

The JWT authentication system now includes a comprehensive Role-Based Access Control (RBAC) system that provides granular permission management for all API endpoints. This system defines specific roles and their associated permissions, enabling fine-grained access control throughout the application.

## 🏷️ User Roles

### 1. **Admin** (`admin`)

**Highest privilege level** - Full system access and management capabilities.

**Use Cases:**

- System administrators
- IT managers
- Platform owners

**Access Level:** Complete system control, user management, analytics, system monitoring

---

### 2. **Developer** (`developer`)

**High privilege level** - Development and content creation focused.

**Use Cases:**

- Software developers
- AI model developers
- Content creators
- Technical users building agents/workflows

**Access Level:** Agent creation, advanced analytics, workflow development, system monitoring (limited)

---

### 3. **User** (`user`)

**Standard privilege level** - Regular user access for daily operations.

**Use Cases:**

- Business users
- End users consuming AI services
- Regular platform members

**Access Level:** Agent interaction, conversation management, workflow execution, file processing

---

### 4. **Guest** (`guest`)

**Limited privilege level** - Read-only access for evaluation.

**Use Cases:**

- Trial users
- Temporary access
- Public demos
- Evaluation accounts

**Access Level:** View agents, system health check, basic profile management

---

### 5. **Service Account** (`service_account`)

**API-focused privilege level** - Programmatic access for integrations.

**Use Cases:**

- API integrations
- Automated systems
- Bots and services
- Third-party applications

**Access Level:** API-driven operations, conversation creation, workflow execution, monitoring

## 🔐 Permission Categories

### Agent Management

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `agent:view` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `agent:create` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `agent:edit` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `agent:delete` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `agent:reload` | ✅ | ✅ | ❌ | ❌ | ❌ |

### Conversation Management

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `conversation:view` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `conversation:create` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `conversation:edit` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `conversation:delete` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `conversation:view_all` | ✅ | ❌ | ❌ | ❌ | ❌ |

### Workflow Management

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `workflow:view` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `workflow:create` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `workflow:edit` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `workflow:delete` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `workflow:execute` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `workflow:view_all` | ✅ | ❌ | ❌ | ❌ | ❌ |

### File Processing

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `file:upload` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `file:process` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `file:view` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `file:delete` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `file:view_all` | ✅ | ❌ | ❌ | ❌ | ❌ |

### System Access

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `system:view` | ✅ | ✅ | ❌ | ❌ | ✅ |
| `system:stats` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `system:health` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `system:monitor` | ✅ | ❌ | ❌ | ❌ | ❌ |

### Analytics

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `analytics:view` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `analytics:basic` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `analytics:advanced` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `analytics:export` | ✅ | ✅ | ❌ | ❌ | ❌ |

### User Management

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `user:view_self` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `user:edit_self` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `user:view_all` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `user:edit_all` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `user:delete` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `user:create` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `user:manage_roles` | ✅ | ❌ | ❌ | ❌ | ❌ |

### Administration

| Permission | Admin | Developer | User | Guest | Service |
|------------|-------|-----------|------|-------|---------|
| `admin:all` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `admin:users` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `admin:system` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `admin:analytics` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `admin:cleanup` | ✅ | ❌ | ❌ | ❌ | ❌ |

## 🛠️ API Endpoints for Role Management

### Get All Roles

```http
GET /api/v1/admin/roles
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "roles": {
    "admin": {
      "name": "admin",
      "permissions": ["admin:all", "agent:view", ...],
      "permission_count": 45
    },
    "user": {
      "name": "user", 
      "permissions": ["agent:view", "conversation:create", ...],
      "permission_count": 15
    }
  },
  "total_roles": 5
}
```

### Get All Permissions

```http
GET /api/v1/admin/permissions
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "permissions": {
    "agent": ["agent:view", "agent:create", "agent:edit"],
    "conversation": ["conversation:view", "conversation:create"],
    "workflow": ["workflow:view", "workflow:create"],
    "file": ["file:upload", "file:process"],
    "system": ["system:view", "system:stats"],
    "analytics": ["analytics:view", "analytics:basic"],
    "user": ["user:view_self", "user:edit_self"],
    "admin": ["admin:all", "admin:users"]
  },
  "total_permissions": 45
}
```

### Get User Permissions

```http
GET /api/v1/admin/users/{user_id}/permissions
Authorization: Bearer <admin_token>
```

### Change User Role

```http
POST /api/v1/admin/users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "developer"
}
```

### Get My Permissions

```http
GET /api/v1/users/me/permissions
Authorization: Bearer <user_token>
```

### Check Specific Permission

```http
POST /api/v1/users/me/check-permission
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "permission": "agent:create"
}
```

## 🔧 Usage in Code

### Using Permission Dependencies

```python
from roles_permissions import require_permission, Permission

@app.post("/api/v1/custom-endpoint")
async def custom_endpoint(
    current_user: dict = Depends(require_permission(Permission.AGENT_CREATE))
):
    # Only users with agent:create permission can access
    pass
```

### Multiple Permission Options

```python
from roles_permissions import require_any_permission, Permission

@app.post("/api/v1/flexible-endpoint")
async def flexible_endpoint(
    current_user: dict = Depends(require_any_permission([
        Permission.ADMIN_ALL,
        Permission.AGENT_EDIT,
        Permission.WORKFLOW_EDIT
    ]))
):
    # Users with ANY of these permissions can access
    pass
```

### Checking Permissions Programmatically

```python
from roles_permissions import RolePermissionManager, Permission

def business_logic(user: dict):
    if RolePermissionManager.user_has_permission(user, Permission.ANALYTICS_ADVANCED):
        # Provide advanced analytics
        return generate_advanced_report()
    else:
        # Provide basic analytics
        return generate_basic_report()
```

## 🔄 Migration from Simple Roles

The system maintains backward compatibility with the existing `require_admin` dependency:

```python
# Old way (still works)
@app.get("/admin/endpoint")
async def admin_endpoint(current_user: dict = Depends(require_admin)):
    pass

# New way (recommended)
@app.get("/admin/endpoint")  
async def admin_endpoint(current_user: dict = Depends(require_admin_access)):
    pass
```

## 🎯 Permission Best Practices

### 1. **Principle of Least Privilege**

- Grant minimum permissions necessary for the role
- Regular permission audits
- Role-based assignment rather than individual permissions

### 2. **Permission Naming Convention**

- Format: `category:action`
- Categories: agent, conversation, workflow, file, system, analytics, user, session, api_key, admin
- Actions: view, create, edit, delete, execute, manage, all

### 3. **Role Assignment Guidelines**

**Admin Role:**

- Only for system administrators
- Complete access to all functions
- User management capabilities

**Developer Role:**

- For technical users building content
- Agent and workflow creation
- Advanced analytics access

**User Role:**

- Standard business users
- Consumption-focused permissions
- Self-management capabilities

**Guest Role:**

- Trial and evaluation users
- Read-only access
- Limited functionality

**Service Account:**

- API integrations and automation
- Programmatic access patterns
- No user management functions

## 🛡️ Security Features

### 1. **Permission Inheritance**

- Roles have hierarchical permission sets
- Admin role includes all permissions
- Clear role boundaries

### 2. **Dynamic Permission Checking**

- Real-time permission validation
- Flexible permission combinations
- Detailed access logging

### 3. **Role Management Controls**

- Admin-only role assignment
- Self-role-change prevention
- Audit trail for role changes

### 4. **API Security**

- Permission-based endpoint protection
- Granular access control
- Comprehensive error handling

## 📊 Role Usage Analytics

The system provides analytics on role usage and permission patterns through the admin endpoints:

- **Role Distribution:** View how users are distributed across roles
- **Permission Usage:** Track which permissions are used most frequently
- **Access Patterns:** Monitor endpoint access by role
- **Security Events:** Track permission denials and role changes

## 🔧 Customization

### Adding New Permissions

1. Add to `Permission` enum in `roles_permissions.py`
2. Update `ROLE_PERMISSIONS` mapping
3. Apply to relevant endpoints
4. Update documentation

### Creating Custom Roles

1. Add to `UserRole` enum
2. Define permission set in `ROLE_PERMISSIONS`
3. Update role hierarchy if needed
4. Test permission assignments

The RBAC system provides enterprise-grade access control while maintaining flexibility for various use cases and organizational structures.

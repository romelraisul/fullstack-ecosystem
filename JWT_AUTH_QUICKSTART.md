# JWT Authentication System - Quick Start Guide

## 🚀 Overview

This JWT authentication system provides complete login, token issuance, and expiry management for your FastAPI backend. It includes user registration, secure password handling, role-based access control, and comprehensive session management.

## 📋 Features Implemented

### ✅ Core JWT Authentication

- **User Registration** - Create new user accounts with validation
- **User Login** - Authenticate users and issue JWT tokens  
- **Token Issuance** - Generate access tokens (60min) and refresh tokens (30 days)
- **Token Expiry** - Automatic token expiration with configurable timeouts
- **Token Validation** - Verify tokens on protected endpoints
- **Logout** - Invalidate tokens and clear sessions

### ✅ Security Features

- **Password Hashing** - bcrypt with secure salt rounds
- **Role-Based Access** - admin, user, developer, guest, service_account roles
- **Account Locking** - Automatic locking after failed login attempts
- **Session Tracking** - Track active user sessions with device info
- **API Key Management** - Generate and manage API keys for service access
- **Rate Limiting** - Configurable rate limits per user/API key

### ✅ Database Schema

- **Users Table** - Complete user profiles with security fields
- **JWT Sessions** - Track active sessions with refresh tokens
- **API Keys** - Manage programmatic access keys

### ✅ API Endpoints

- **Authentication** - `/api/v1/auth/*` (login, register, profile, logout)
- **Protected Endpoints** - All existing endpoints secured with JWT
- **Admin Functions** - User management and system statistics
- **Password Management** - Password reset and change workflows

## 🛠️ Quick Start

### 1. Start the Backend Server

```bash
cd c:\Users\romel\fullstack-ecosystem
python autogen/advanced_backend.py
```

The server will start on `http://localhost:8011`

### 2. Test the Authentication System

```bash
# Run comprehensive test suite
python test_jwt_auth.py

# Run interactive demo
python jwt_auth_demo.py
```

### 3. Create Admin User (if needed)

The system automatically creates an admin user on startup:

- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin`

## 🔐 Authentication Flow

### 1. User Registration

```bash
POST /api/v1/auth/register
{
  "username": "testuser",
  "email": "test@example.com", 
  "password": "SecurePass123!",
  "full_name": "Test User"
}
```

### 2. User Login

```bash
POST /api/v1/auth/login
{
  "username": "testuser",
  "password": "SecurePass123!",
  "remember_me": true
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "username": "testuser",
    "email": "test@example.com",
    "role": "user"
  }
}
```

### 3. Access Protected Endpoints

```bash
GET /api/v1/auth/profile
Authorization: Bearer <access_token>
```

### 4. Refresh Token (when access token expires)

```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "<refresh_token>"
}
```

### 5. Logout

```bash
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

## 🎯 API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login user | No |
| POST | `/api/v1/auth/logout` | Logout user | Yes |
| GET | `/api/v1/auth/profile` | Get user profile | Yes |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/change-password` | Change password | Yes |

### API Key Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/api-keys` | Create API key | Yes |
| GET | `/api/v1/auth/api-keys` | List user's API keys | Yes |
| DELETE | `/api/v1/auth/api-keys/{key_id}` | Delete API key | Yes |

### Admin Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/admin/stats` | Security statistics | Admin |
| GET | `/api/v1/admin/users` | List all users | Admin |
| POST | `/api/v1/admin/users/{user_id}/unlock` | Unlock user account | Admin |

### Protected Application Endpoints

All existing endpoints are now secured with JWT:

- `/api/v1/agents` - List available agents
- `/api/v1/conversations` - Create and manage conversations
- `/api/v1/workflows` - Workflow management
- `/api/v1/analytics` - Analytics and reporting
- `/api/v1/system/*` - System management

## 🔧 Configuration

### JWT Settings (in jwt_auth_service.py)

```python
# Token expiry times
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30 days

# Security settings
PASSWORD_MIN_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 30  # minutes
```

### Rate Limiting

- **Default**: 100 requests per hour per user
- **Admin**: 1000 requests per hour
- **API Keys**: Configurable per key

## 🧪 Testing

### Test Suite

```bash
python test_jwt_auth.py
```

**Tests Include:**

- ✅ Health check
- ✅ User registration (valid/invalid data)
- ✅ User login (valid/invalid credentials)
- ✅ Token validation
- ✅ Protected endpoint access
- ✅ Refresh token flow
- ✅ Role-based access control
- ✅ Admin endpoint security
- ✅ Logout functionality
- ✅ Password change workflow

### Interactive Demo

```bash
python jwt_auth_demo.py
```

**Demo Features:**

- Live API testing
- Authentication workflow demonstration
- Error handling examples
- Security feature validation

## 🛡️ Security Features

### Password Security

- **bcrypt hashing** with 12 salt rounds
- **Minimum 8 characters** with complexity requirements
- **Password history** prevention (last 3 passwords)

### Account Protection

- **Account locking** after 5 failed attempts
- **30-minute lockout** duration
- **IP-based rate limiting**
- **Session invalidation** on logout

### Token Security

- **HS256 algorithm** with secure secret key
- **Short access token** lifetime (60 minutes)
- **Long refresh token** lifetime (30 days)
- **Session tracking** with device fingerprinting

## 📁 File Structure

```
c:\Users\romel\fullstack-ecosystem\
├── src/
│   └── db/
│       ├── schema.py           # Database schema with auth tables
│       └── users_repo.py       # User CRUD operations
├── autogen/
│   ├── advanced_backend.py     # Main FastAPI app with JWT integration
│   ├── jwt_auth_service.py     # Core JWT authentication service
│   └── auth_router.py          # Additional auth endpoints
├── test_jwt_auth.py            # Comprehensive test suite
├── jwt_auth_demo.py            # Interactive demonstration
└── JWT_AUTH_QUICKSTART.md      # This guide
```

## 🐛 Troubleshooting

### Common Issues

**1. "Invalid credentials" error**

- Check username/password spelling
- Verify user account exists and isn't locked
- Check if account needs email verification

**2. "Token expired" error**

- Use refresh token to get new access token
- Re-login if refresh token is also expired

**3. "Access denied" error**

- Check user role permissions
- Verify token is included in Authorization header
- Ensure endpoint allows user's role

**4. Connection refused**

- Make sure backend server is running on port 8011
- Check firewall settings
- Verify server startup logs for errors

### Debug Mode

Set `DEBUG=True` in the backend configuration for detailed error messages.

## 🔄 Next Steps

1. **Run Tests**: Execute `python test_jwt_auth.py` to validate system
2. **Try Demo**: Run `python jwt_auth_demo.py` for interactive testing
3. **Customize**: Adjust token expiry times and security settings
4. **Deploy**: Configure production secrets and database
5. **Monitor**: Set up logging and security monitoring

## 🎉 Success

Your JWT authentication system is now complete with:

- ✅ **Login** - Secure user authentication
- ✅ **Token Issuance** - JWT access and refresh tokens  
- ✅ **Token Expiry** - Automatic expiration handling
- ✅ **Role-Based Access** - Granular permission control
- ✅ **Session Management** - Complete session tracking
- ✅ **Security Features** - Account locking, rate limiting, password hashing

The system is production-ready and includes comprehensive testing and documentation!

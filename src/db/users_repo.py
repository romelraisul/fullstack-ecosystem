"""
Users Repository for JWT Authentication
Handles user CRUD operations, sessions, and API keys
"""

import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from passlib.context import CryptContext


class UsersRepository:
    """Repository for user management and authentication"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
        role: str = "user",
        is_active: bool = True,
    ) -> dict[str, Any] | None:
        """Create a new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Check if username or email already exists
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
                )
                if cursor.fetchone():
                    return None  # User already exists

                # Hash password
                hashed_password = self.pwd_context.hash(password)
                now = datetime.utcnow().isoformat()

                # Insert user
                cursor.execute(
                    """
                    INSERT INTO users (
                        username, email, hashed_password, full_name, role,
                        is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (username, email, hashed_password, full_name, role, int(is_active), now, now),
                )

                user_id = cursor.lastrowid
                conn.commit()

                return self.get_user_by_id(user_id)
        except sqlite3.Error:
            return None

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Get user by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, username, email, hashed_password, full_name, role,
                           is_active, created_at, updated_at, last_login,
                           failed_login_attempts, locked_until
                    FROM users WHERE id = ?
                    """,
                    (user_id,),
                )

                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, username, email, hashed_password, full_name, role,
                           is_active, created_at, updated_at, last_login,
                           failed_login_attempts, locked_until
                    FROM users WHERE username = ?
                    """,
                    (username,),
                )

                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, username, email, hashed_password, full_name, role,
                           is_active, created_at, updated_at, last_login,
                           failed_login_attempts, locked_until
                    FROM users WHERE email = ?
                    """,
                    (email,),
                )

                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                hashed_password = self.pwd_context.hash(new_password)
                now = datetime.utcnow().isoformat()

                cursor.execute(
                    "UPDATE users SET hashed_password = ?, updated_at = ? WHERE id = ?",
                    (hashed_password, now, user_id),
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()

                cursor.execute(
                    "UPDATE users SET last_login = ?, failed_login_attempts = 0 WHERE id = ?",
                    (now, user_id),
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def increment_failed_login(self, user_id: int) -> bool:
        """Increment failed login attempts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = failed_login_attempts + 1,
                        locked_until = CASE
                            WHEN failed_login_attempts >= 4
                            THEN datetime('now', '+15 minutes')
                            ELSE locked_until
                        END
                    WHERE id = ?
                    """,
                    (user_id,),
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def is_user_locked(self, user_id: int) -> bool:
        """Check if user is currently locked"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT locked_until FROM users WHERE id = ?", (user_id,))

                row = cursor.fetchone()
                if not row or not row[0]:
                    return False

                locked_until = datetime.fromisoformat(row[0])
                return datetime.utcnow() < locked_until
        except sqlite3.Error:
            return False

    # JWT Session Management
    def create_session(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Create a new JWT session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                session_id = str(uuid.uuid4())
                now = datetime.utcnow().isoformat()

                cursor.execute(
                    """
                    INSERT INTO jwt_sessions (
                        session_id, user_id, token_hash, expires_at,
                        created_at, last_activity, ip_address, user_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        user_id,
                        token_hash,
                        expires_at.isoformat(),
                        now,
                        now,
                        ip_address,
                        user_agent,
                    ),
                )

                conn.commit()
                return session_id
        except sqlite3.Error:
            return None

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT s.*, u.username, u.role
                    FROM jwt_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_id = ? AND s.is_active = 1
                    """,
                    (session_id,),
                )

                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None

    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()

                cursor.execute(
                    "UPDATE jwt_sessions SET last_activity = ? WHERE session_id = ?",
                    (now, session_id),
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE jwt_sessions SET is_active = 0 WHERE session_id = ?", (session_id,)
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def invalidate_user_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE jwt_sessions SET is_active = 0 WHERE user_id = ?", (user_id,)
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()

                cursor.execute("DELETE FROM jwt_sessions WHERE expires_at < ?", (now,))

                conn.commit()
                return cursor.rowcount
        except sqlite3.Error:
            return 0

    # API Key Management
    def create_api_key(
        self,
        user_id: int,
        name: str,
        permissions: list[str],
        rate_limit: int = 1000,
        expires_at: datetime | None = None,
    ) -> tuple[str, str] | None:
        """Create a new API key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                key_id = str(uuid.uuid4())
                raw_key = secrets.token_urlsafe(32)
                key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
                now = datetime.utcnow().isoformat()

                cursor.execute(
                    """
                    INSERT INTO api_keys (
                        key_id, key_hash, name, user_id, permissions,
                        rate_limit, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key_id,
                        key_hash,
                        name,
                        user_id,
                        json.dumps(permissions),
                        rate_limit,
                        now,
                        expires_at.isoformat() if expires_at else None,
                    ),
                )

                conn.commit()
                return key_id, raw_key
        except sqlite3.Error:
            return None

    def get_api_key_by_hash(self, key_hash: str) -> dict[str, Any] | None:
        """Get API key by hash"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT k.*, u.username
                    FROM api_keys k
                    JOIN users u ON k.user_id = u.id
                    WHERE k.key_hash = ? AND k.is_active = 1
                    """,
                    (key_hash,),
                )

                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["permissions"] = json.loads(result["permissions"])
                    return result
                return None
        except sqlite3.Error:
            return None

    def update_api_key_usage(self, key_id: str) -> bool:
        """Update API key last used timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()

                cursor.execute("UPDATE api_keys SET last_used = ? WHERE key_id = ?", (now, key_id))

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_user_api_keys(self, user_id: int) -> list[dict[str, Any]]:
        """Get all API keys for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT key_id, name, permissions, rate_limit,
                           created_at, expires_at, last_used, is_active
                    FROM api_keys WHERE user_id = ?
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )

                keys = []
                for row in cursor.fetchall():
                    key_data = dict(row)
                    key_data["permissions"] = json.loads(key_data["permissions"])
                    keys.append(key_data)

                return keys
        except sqlite3.Error:
            return []

    def revoke_api_key(self, key_id: str, user_id: int | None = None) -> bool:
        """Revoke an API key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if user_id:
                    # User can only revoke their own keys
                    cursor.execute(
                        "UPDATE api_keys SET is_active = 0 WHERE key_id = ? AND user_id = ?",
                        (key_id, user_id),
                    )
                else:
                    # Admin can revoke any key
                    cursor.execute("UPDATE api_keys SET is_active = 0 WHERE key_id = ?", (key_id,))

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    # User Management
    def list_users(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """List all users (admin function)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, username, email, full_name, role, is_active,
                           created_at, updated_at, last_login
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def update_user(
        self,
        user_id: int,
        email: str | None = None,
        full_name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> bool:
        """Update user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                updates = ["updated_at = ?"]
                values = [datetime.utcnow().isoformat()]

                if email is not None:
                    updates.append("email = ?")
                    values.append(email)
                if full_name is not None:
                    updates.append("full_name = ?")
                    values.append(full_name)
                if role is not None:
                    updates.append("role = ?")
                    values.append(role)
                if is_active is not None:
                    updates.append("is_active = ?")
                    values.append(int(is_active))

                values.append(user_id)

                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all related data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete user (cascades to sessions and API keys)
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    # Admin utilities
    def get_user_stats(self) -> dict[str, Any]:
        """Get user statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Total users
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total_users = cursor.fetchone()["total"]

                # Active users
                cursor.execute("SELECT COUNT(*) as active FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()["active"]

                # Users by role
                cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
                users_by_role = {row["role"]: row["count"] for row in cursor.fetchall()}

                # Active sessions
                cursor.execute("SELECT COUNT(*) as active FROM jwt_sessions WHERE is_active = 1")
                active_sessions = cursor.fetchone()["active"]

                # Active API keys
                cursor.execute("SELECT COUNT(*) as active FROM api_keys WHERE is_active = 1")
                active_api_keys = cursor.fetchone()["active"]

                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "users_by_role": users_by_role,
                    "active_sessions": active_sessions,
                    "active_api_keys": active_api_keys,
                }
        except sqlite3.Error:
            return {}

    def seed_admin_user(self, username: str = "admin", password: str = "admin123") -> bool:
        """Create default admin user if none exists"""
        try:
            # Check if admin user already exists
            if self.get_user_by_username(username):
                return False

            # Create admin user
            admin_user = self.create_user(
                username=username,
                email=f"{username}@example.com",
                password=password,
                full_name="System Administrator",
                role="admin",
                is_active=True,
            )

            return admin_user is not None
        except Exception:
            return False

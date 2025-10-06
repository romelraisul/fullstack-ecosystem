"""SQLite schema definitions and initialization utilities.

Tables:
  agents
  conversations
  conversation_messages
  workflows
  workflow_steps
  workflow_executions
    workflow_execution_steps

Design Notes:
 - Simple INTEGER PRIMARY KEY autoincrement for internal identity.
 - Business identifiers (like agent id from YAML) stored in `agent_key` (unique).
 - Timestamps stored as ISO 8601 text for portability.
 - JSON style columns stored as TEXT (caller serializes/deserializes JSON).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

SCHEMA_STATEMENTS: Iterable[str] = [
    # Users table
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        role TEXT NOT NULL DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_login TEXT,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TEXT,
        password_reset_token TEXT,
        password_reset_expires TEXT,
        email_verified INTEGER DEFAULT 0,
        email_verification_token TEXT
    );
    """,
    # JWT sessions table
    """
    CREATE TABLE IF NOT EXISTS jwt_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_activity TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """,
    # API keys table
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id TEXT NOT NULL UNIQUE,
        key_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        permissions TEXT, -- JSON array string
        rate_limit INTEGER DEFAULT 1000,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        last_used TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """,
    # Agents table
    """
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_key TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        capabilities TEXT, -- JSON array string
        status TEXT,
        version TEXT,
        metadata TEXT, -- JSON object string
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    # Conversations table
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL UNIQUE,
        agent_key TEXT NOT NULL,
        context TEXT, -- JSON object
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(agent_key) REFERENCES agents(agent_key)
    );
    """,
    # Conversation messages
    """
    CREATE TABLE IF NOT EXISTS conversation_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        message_id TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        agent_key TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
    );
    """,
    # Workflows master
    """
    CREATE TABLE IF NOT EXISTS workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        parallel_execution INTEGER DEFAULT 0,
        status TEXT,
        created_at TEXT NOT NULL
    );
    """,
    # Workflow steps
    """
    CREATE TABLE IF NOT EXISTS workflow_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_id TEXT NOT NULL,
        step_name TEXT NOT NULL,
        agent_key TEXT NOT NULL,
        parameters TEXT, -- JSON object
        depends_on TEXT, -- JSON array of step names
        position INTEGER,
        FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id),
        FOREIGN KEY(agent_key) REFERENCES agents(agent_key)
    );
    """,
    # Workflow executions
    """
    CREATE TABLE IF NOT EXISTS workflow_executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        execution_id TEXT NOT NULL UNIQUE,
        workflow_id TEXT NOT NULL,
        status TEXT,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        steps_completed INTEGER DEFAULT 0,
        total_steps INTEGER DEFAULT 0,
        FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id)
    );
    """,
    # Workflow execution step states
    """
    CREATE TABLE IF NOT EXISTS workflow_execution_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        execution_id TEXT NOT NULL,
        step_name TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT,
        completed_at TEXT,
        error TEXT,
        FOREIGN KEY(execution_id) REFERENCES workflow_executions(execution_id)
    );
    """,
]


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for stmt in SCHEMA_STATEMENTS:
            cur.executescript(stmt)
        conn.commit()

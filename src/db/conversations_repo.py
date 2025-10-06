"""Conversation persistence repository."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class ConversationsRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def create_conversation(self, conv: dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO conversations (conversation_id, agent_key, context, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    conv["id"],
                    conv["agent_id"],
                    json.dumps(conv.get("context", {}), ensure_ascii=False),
                    conv.get("status"),
                    conv.get("created_at"),
                    conv.get("last_updated"),
                ),
            )
            for m in conv.get("messages", []):
                self.add_message(conv["id"], m)

    def add_message(self, conversation_id: str, message: dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO conversation_messages (conversation_id, message_id, role, content, agent_key, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    conversation_id,
                    message["id"],
                    message["role"],
                    message["content"],
                    message.get("agent_id"),
                    message["timestamp"],
                ),
            )

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT conversation_id, agent_key, context, status, created_at, updated_at FROM conversations WHERE conversation_id=?",
                (conversation_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            messages_cur = conn.execute(
                "SELECT message_id, role, content, agent_key, created_at FROM conversation_messages WHERE conversation_id=? ORDER BY id",
                (conversation_id,),
            )
            messages = [
                {
                    "id": r[0],
                    "role": r[1],
                    "content": r[2],
                    "agent_id": r[3],
                    "timestamp": r[4],
                }
                for r in messages_cur.fetchall()
            ]
            return {
                "id": row[0],
                "agent_id": row[1],
                "context": json.loads(row[2]) if row[2] else {},
                "status": row[3],
                "created_at": row[4],
                "last_updated": row[5],
                "messages": messages,
            }

    def list_conversations(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT conversation_id FROM conversations ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            ids = [r[0] for r in cur.fetchall()]
        return [self.get_conversation(cid) for cid in ids if cid]

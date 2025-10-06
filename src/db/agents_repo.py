"""Agents repository layer for SQLite backend."""

from __future__ import annotations

import builtins
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AgentRecord:
    agent_key: str
    name: str
    category: str | None
    description: str | None
    capabilities: list[str]
    status: str | None
    version: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str

    @staticmethod
    def from_row(row) -> AgentRecord:
        return AgentRecord(
            agent_key=row[0],
            name=row[1],
            category=row[2],
            description=row[3],
            capabilities=json.loads(row[4]) if row[4] else [],
            status=row[5],
            version=row[6],
            metadata=json.loads(row[7]) if row[7] else {},
            created_at=row[8],
            updated_at=row[9],
        )


class AgentsRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    # CRUD operations -----------------------------------------------------
    def upsert(self, agent: dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        capabilities_json = json.dumps(agent.get("capabilities", []), ensure_ascii=False)
        metadata_json = json.dumps(
            {
                k: v
                for k, v in agent.items()
                if k
                not in {
                    "id",
                    "name",
                    "category",
                    "description",
                    "capabilities",
                    "status",
                    "version",
                }
            },
            ensure_ascii=False,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agents (agent_key, name, category, description, capabilities, status, version, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_key) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    description=excluded.description,
                    capabilities=excluded.capabilities,
                    status=excluded.status,
                    version=excluded.version,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
                """,
                (
                    agent.get("id") or agent.get("agent_key"),
                    agent.get("name"),
                    agent.get("category"),
                    agent.get("description"),
                    capabilities_json,
                    agent.get("status"),
                    agent.get("version"),
                    metadata_json,
                    now,
                    now,
                ),
            )

    def get(self, agent_key: str) -> AgentRecord | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT agent_key, name, category, description, capabilities, status, version, metadata, created_at, updated_at FROM agents WHERE agent_key = ?",
                (agent_key,),
            )
            row = cur.fetchone()
            return AgentRecord.from_row(row) if row else None

    def list(self) -> builtins.list[AgentRecord]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT agent_key, name, category, description, capabilities, status, version, metadata, created_at, updated_at FROM agents ORDER BY name"
            )
            return [AgentRecord.from_row(r) for r in cur.fetchall()]

    def delete(self, agent_key: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM agents WHERE agent_key = ?", (agent_key,))
            return cur.rowcount > 0

    def count(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("SELECT COUNT(1) FROM agents")
            return cur.fetchone()[0]

    # Seeding -------------------------------------------------------------
    def seed_from_yaml_agents(self, agents: dict[str, dict[str, Any]]) -> int:
        inserted = 0
        for agent_id, agent in agents.items():
            existing = self.get(agent_id)
            if existing is None:
                self.upsert(agent)
                inserted += 1
        return inserted

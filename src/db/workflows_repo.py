"""Workflow execution repository layer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class WorkflowsRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Perform lightweight migration for step_order if needed
        try:
            with sqlite3.connect(self.db_path) as conn:  # type: ignore[arg-type]
                cur = conn.execute("PRAGMA table_info(workflow_executions)")
                cols = {r[1] for r in cur.fetchall()}
                if "step_order" not in cols:
                    conn.execute("ALTER TABLE workflow_executions ADD COLUMN step_order TEXT")
                if "replay_of" not in cols:
                    conn.execute("ALTER TABLE workflow_executions ADD COLUMN replay_of TEXT")
                if "input_snapshot" not in cols:
                    conn.execute("ALTER TABLE workflow_executions ADD COLUMN input_snapshot TEXT")
                # Create perf history table if not exists
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS daily_endpoint_perf (
                        date TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        median_ms REAL,
                        p95_ms REAL,
                        samples INT,
                        PRIMARY KEY (date, endpoint)
                    )"""
                )
                # Adaptive latency state persistence
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS adaptive_latency_state (
                        endpoint TEXT PRIMARY KEY,
                        ema_p95_ms REAL,
                        class_ema_shares TEXT,
                        updated_at TEXT,
                        sample_count INTEGER,
                        sample_mean_ms REAL,
                        sample_m2 REAL,
                        tdigest_blob BLOB
                    )"""
                )
                # Add tdigest_blob column if missing (migration)
                cur = conn.execute("PRAGMA table_info(adaptive_latency_state)")
                cols = {r[1] for r in cur.fetchall()}
                if "tdigest_blob" not in cols:
                    conn.execute("ALTER TABLE adaptive_latency_state ADD COLUMN tdigest_blob BLOB")
        except Exception:
            # Ignore migration failures silently (will just not persist order)
            pass

    def _conn(self):  # context manager usage
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------
    # Workflow Definitions (create/list/get + steps)
    # ------------------------------------------------------------------
    def create_workflow(self, wf: dict[str, Any]):
        """Persist a workflow definition and its steps.

        Expects wf structure similar to in-memory version:
          {
            'id': <workflow_id>,
            'name': str,
            'description': str,
            'steps': [ { name, agent_id, parameters, depends_on } ],
            'parallel_execution': bool,
            'status': str,
            'created_at': iso8601
          }
        """
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO workflows (workflow_id, name, description, parallel_execution, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    wf["id"],
                    wf.get("name"),
                    wf.get("description"),
                    1 if wf.get("parallel_execution") else 0,
                    wf.get("status"),
                    wf.get("created_at"),
                ),
            )
            for position, step in enumerate(wf.get("steps", [])):
                conn.execute(
                    """INSERT INTO workflow_steps (workflow_id, step_name, agent_key, parameters, depends_on, position)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        wf["id"],
                        step.get("name"),
                        step.get("agent_id"),
                        json.dumps(step.get("parameters", {}), ensure_ascii=False),
                        json.dumps(step.get("depends_on", []), ensure_ascii=False),
                        position,
                    ),
                )

    def list_workflows(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT workflow_id FROM workflows ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            ids = [r[0] for r in cur.fetchall()]
        return [wf for wf in (self.get_workflow(i) for i in ids) if wf]

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT workflow_id, name, description, parallel_execution, status, created_at FROM workflows WHERE workflow_id=?",
                (workflow_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            steps_cur = conn.execute(
                "SELECT step_name, agent_key, parameters, depends_on FROM workflow_steps WHERE workflow_id=? ORDER BY position",
                (workflow_id,),
            )
            steps = []
            for s in steps_cur.fetchall():
                try:
                    parameters = json.loads(s[2]) if s[2] else {}
                except Exception:
                    parameters = {}
                try:
                    depends_on = json.loads(s[3]) if s[3] else []
                except Exception:
                    depends_on = []
                steps.append(
                    {
                        "name": s[0],
                        "agent_id": s[1],
                        "parameters": parameters,
                        "depends_on": depends_on,
                    }
                )
            return {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "parallel_execution": bool(row[3]),
                "status": row[4],
                "created_at": row[5],
                "steps": steps,
            }

    # Executions ---------------------------------------------------------
    def create_execution(self, execution: dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO workflow_executions (execution_id, workflow_id, status, started_at, completed_at, steps_completed, total_steps, step_order, replay_of, input_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    execution["execution_id"],
                    execution["workflow_id"],
                    execution.get("status"),
                    execution.get("started_at"),
                    execution.get("completed_at"),
                    execution.get("steps_completed", 0),
                    execution.get("total_steps", 0),
                    (
                        json.dumps(execution.get("step_order"))
                        if execution.get("step_order")
                        else None
                    ),
                    execution.get("replay_of"),
                    (
                        json.dumps(execution.get("input_snapshot"))
                        if execution.get("input_snapshot")
                        else None
                    ),
                ),
            )

    def update_execution(self, execution: dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """UPDATE workflow_executions SET status=?, started_at=?, completed_at=?, steps_completed=?, total_steps=?, step_order=?, replay_of=?, input_snapshot=? WHERE execution_id=?""",
                (
                    execution.get("status"),
                    execution.get("started_at"),
                    execution.get("completed_at"),
                    execution.get("steps_completed", 0),
                    execution.get("total_steps", 0),
                    (
                        json.dumps(execution.get("step_order"))
                        if execution.get("step_order")
                        else None
                    ),
                    execution.get("replay_of"),
                    (
                        json.dumps(execution.get("input_snapshot"))
                        if execution.get("input_snapshot")
                        else None
                    ),
                    execution["execution_id"],
                ),
            )

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT execution_id, workflow_id, status, started_at, completed_at, steps_completed, total_steps, step_order, replay_of, input_snapshot FROM workflow_executions WHERE execution_id=?",
                (execution_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            try:
                order = json.loads(row[7]) if row[7] else None
            except Exception:
                order = None
            try:
                snapshot = json.loads(row[9]) if row[9] else None
            except Exception:
                snapshot = None
            return {
                "execution_id": row[0],
                "workflow_id": row[1],
                "status": row[2],
                "started_at": row[3],
                "completed_at": row[4],
                "steps_completed": row[5],
                "total_steps": row[6],
                "step_order": order,
                "replay_of": row[8],
                "input_snapshot": snapshot,
            }

    def list_executions(
        self, workflow_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List executions optionally filtered by workflow_id ordered by started_at desc (NULLs last)."""
        with self._conn() as conn:
            if workflow_id:
                cur = conn.execute(
                    """
                    SELECT execution_id FROM workflow_executions
                    WHERE workflow_id=?
                    ORDER BY (started_at IS NULL) ASC, started_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (workflow_id, limit, offset),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT execution_id FROM workflow_executions
                    ORDER BY (started_at IS NULL) ASC, started_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )
            ids = [r[0] for r in cur.fetchall()]
        out: list[dict[str, Any]] = []
        for eid in ids:
            exe = self.get_execution(eid)
            if exe:
                out.append(exe)
        return out

    def prune_executions(self, max_entries: int = 1000) -> int:
        """Keep only most recent max_entries executions globally. Returns number deleted."""
        if max_entries <= 0:
            return 0
        with self._conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM workflow_executions")
            total = cur.fetchone()[0]
            if total <= max_entries:
                return 0
            # Determine cutoff (ids beyond newest max_entries)
            cur = conn.execute(
                """
                SELECT execution_id FROM workflow_executions
                ORDER BY (started_at IS NULL) ASC, started_at DESC
                LIMIT -1 OFFSET ?
                """,
                (max_entries,),
            )
            to_delete = [r[0] for r in cur.fetchall()]
            if not to_delete:
                return 0
            # Delete step states first (FK not enforced maybe; be explicit)
            conn.executemany(
                "DELETE FROM workflow_execution_steps WHERE execution_id=?",
                [(eid,) for eid in to_delete],
            )
            conn.executemany(
                "DELETE FROM workflow_executions WHERE execution_id=?",
                [(eid,) for eid in to_delete],
            )
            return len(to_delete)

    # Step States --------------------------------------------------------
    def upsert_step_state(self, execution_id: str, step_name: str, state: dict[str, Any]):
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id FROM workflow_execution_steps WHERE execution_id=? AND step_name=?",
                (execution_id, step_name),
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    """UPDATE workflow_execution_steps SET status=?, started_at=?, completed_at=?, error=? WHERE id=?""",
                    (
                        state.get("status"),
                        state.get("started_at"),
                        state.get("completed_at"),
                        state.get("error"),
                        row[0],
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO workflow_execution_steps (execution_id, step_name, status, started_at, completed_at, error)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        execution_id,
                        step_name,
                        state.get("status"),
                        state.get("started_at"),
                        state.get("completed_at"),
                        state.get("error"),
                    ),
                )

    def list_step_states(self, execution_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT step_name, status, started_at, completed_at, error FROM workflow_execution_steps WHERE execution_id=? ORDER BY id",
                (execution_id,),
            )
            return [
                {
                    "step_name": r[0],
                    "status": r[1],
                    "started_at": r[2],
                    "completed_at": r[3],
                    "error": r[4],
                }
                for r in cur.fetchall()
            ]

    # Performance History ----------------------------------------------
    def upsert_daily_perf(
        self, date: str, endpoint: str, median_ms: float | None, p95_ms: float | None, samples: int
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO daily_endpoint_perf(date, endpoint, median_ms, p95_ms, samples)
                VALUES(?,?,?,?,?)
                ON CONFLICT(date, endpoint) DO UPDATE SET median_ms=excluded.median_ms, p95_ms=excluded.p95_ms, samples=excluded.samples""",
                (date, endpoint, median_ms, p95_ms, samples),
            )

    def list_daily_perf(self, from_date: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT date, endpoint, median_ms, p95_ms, samples FROM daily_endpoint_perf WHERE date >= ? ORDER BY date ASC, endpoint ASC",
                (from_date,),
            )
            return [
                {
                    "date": r[0],
                    "endpoint": r[1],
                    "median_ms": r[2],
                    "p95_ms": r[3],
                    "samples": r[4],
                }
                for r in cur.fetchall()
            ]

    # Adaptive Latency State ------------------------------------------
    def upsert_adaptive_latency_state(
        self,
        endpoint: str,
        ema_p95_ms: float | None,
        class_ema_shares: dict[str, float] | None,
        updated_at: str,
        sample_count: int | None,
        sample_mean_ms: float | None,
        sample_m2: float | None,
        tdigest_blob: bytes | None = None,
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO adaptive_latency_state(endpoint, ema_p95_ms, class_ema_shares, updated_at, sample_count, sample_mean_ms, sample_m2, tdigest_blob)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(endpoint) DO UPDATE SET ema_p95_ms=excluded.ema_p95_ms, class_ema_shares=excluded.class_ema_shares, updated_at=excluded.updated_at, sample_count=excluded.sample_count, sample_mean_ms=excluded.sample_mean_ms, sample_m2=excluded.sample_m2, tdigest_blob=excluded.tdigest_blob""",
                (
                    endpoint,
                    ema_p95_ms,
                    json.dumps(class_ema_shares or {}, ensure_ascii=False),
                    updated_at,
                    sample_count,
                    sample_mean_ms,
                    sample_m2,
                    tdigest_blob,
                ),
            )

    def load_adaptive_latency_states(self) -> list[dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT endpoint, ema_p95_ms, class_ema_shares, updated_at, sample_count, sample_mean_ms, sample_m2, tdigest_blob FROM adaptive_latency_state"
            )
            out = []
            for r in cur.fetchall():
                try:
                    shares = json.loads(r[2]) if r[2] else {}
                except Exception:
                    shares = {}
                out.append(
                    {
                        "endpoint": r[0],
                        "ema_p95_ms": r[1],
                        "class_ema_shares": shares,
                        "updated_at": r[3],
                        "sample_count": r[4],
                        "sample_mean_ms": r[5],
                        "sample_m2": r[6],
                        "tdigest_blob": r[7],
                    }
                )
            return out

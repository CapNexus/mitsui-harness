"""harness-db: SQLite store for analysis and implementation runs.

Everything a run needs to resume after a stop or a crash is here: the run row (story,
branch, base ref, target repo, the loop context as JSON), one row per step with its
status and token figures, and every console event. The web app streams the console from
the events table, so a reconnecting browser simply asks for events after the last id.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("HARNESS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "harness.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            TEXT PRIMARY KEY,
    story_id      TEXT NOT NULL,
    kind          TEXT NOT NULL,            -- analysis | implementation
    status        TEXT NOT NULL,            -- queued | running | awaiting_review | completed | failed | stopped | interrupted | rejected
    branch        TEXT,
    base_ref      TEXT,
    target_repo   TEXT,
    scaffold      INTEGER DEFAULT 0,
    confidence    INTEGER,
    override_reason TEXT,
    context_json  TEXT NOT NULL DEFAULT '{}',
    result_json   TEXT,
    error         TEXT,
    commit_sha    TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS runs_story ON runs(story_id, created_at);

CREATE TABLE IF NOT EXISTS steps (
    run_id        TEXT NOT NULL,
    idx           INTEGER NOT NULL,
    name          TEXT NOT NULL,
    kind          TEXT NOT NULL,            -- agent | deterministic | human
    status        TEXT NOT NULL,            -- pending | running | ok | failed | skipped
    detail        TEXT,
    started_at    TEXT,
    ended_at      TEXT,
    input_tokens  INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    tokens_reported INTEGER DEFAULT 0,      -- 1 = from the agent, 0 = estimated from text size
    PRIMARY KEY (run_id, idx)
);

CREATE TABLE IF NOT EXISTS events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id    TEXT NOT NULL,
    ts        TEXT NOT NULL,
    step      TEXT,
    kind      TEXT NOT NULL,                -- phase | step | agent | thought | tool | perm | check | output | info | warn | error
    text      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_run ON events(run_id, id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DB:
    def __init__(self, path: str = DB_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)

    def _q(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, args).fetchall()

    def _x(self, sql: str, args: tuple = ()) -> int:
        with self._lock:
            cur = self._conn.execute(sql, args)
            return cur.lastrowid

    # --- runs ---------------------------------------------------------------------------

    def create_run(self, story_id: str, kind: str, **fields: Any) -> str:
        rid = f"{story_id}-{kind[:4]}-{uuid.uuid4().hex[:6]}"
        cols = {"id": rid, "story_id": story_id, "kind": kind, "status": "queued",
                "created_at": now(), "updated_at": now(), **fields}
        self._x(f"INSERT INTO runs ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                tuple(cols.values()))
        return rid

    def update_run(self, rid: str, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = now()
        self._x(f"UPDATE runs SET {', '.join(f'{k}=?' for k in fields)} WHERE id=?",
                (*fields.values(), rid))

    def run(self, rid: str) -> Optional[dict]:
        rows = self._q("SELECT * FROM runs WHERE id=?", (rid,))
        return _run_dict(rows[0]) if rows else None

    def runs(self, story_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        if story_id:
            rows = self._q("SELECT * FROM runs WHERE story_id=? ORDER BY created_at DESC LIMIT ?",
                           (story_id, limit))
        else:
            rows = self._q("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [_run_dict(r) for r in rows]

    def latest(self, story_id: str, kind: str) -> Optional[dict]:
        rows = self._q("SELECT * FROM runs WHERE story_id=? AND kind=? ORDER BY created_at DESC LIMIT 1",
                       (story_id, kind))
        return _run_dict(rows[0]) if rows else None

    def mark_interrupted(self) -> int:
        """At server start, any run still `running` died with the previous process."""
        rows = self._q("SELECT id FROM runs WHERE status IN ('running','queued')")
        for r in rows:
            self.update_run(r["id"], status="interrupted",
                            error="the server stopped while this run was active; resume it")
            self._x("UPDATE steps SET status='pending' WHERE run_id=? AND status='running'", (r["id"],))
        return len(rows)

    def set_context(self, rid: str, context: Dict[str, Any]) -> None:
        self.update_run(rid, context_json=json.dumps(context, default=str))

    # --- steps --------------------------------------------------------------------------

    def init_steps(self, rid: str, steps: List[dict]) -> None:
        for i, s in enumerate(steps):
            self._x("INSERT OR IGNORE INTO steps (run_id, idx, name, kind, status) VALUES (?,?,?,?,?)",
                    (rid, i, s["name"], s["kind"], "pending"))

    def steps(self, rid: str) -> List[dict]:
        return [dict(r) for r in self._q("SELECT * FROM steps WHERE run_id=? ORDER BY idx", (rid,))]

    def update_step(self, rid: str, idx: int, **fields: Any) -> None:
        self._x(f"UPDATE steps SET {', '.join(f'{k}=?' for k in fields)} WHERE run_id=? AND idx=?",
                (*fields.values(), rid, idx))

    def add_tokens(self, rid: str, idx: int, inp: int, out: int, reported: bool) -> None:
        self._x("UPDATE steps SET input_tokens=input_tokens+?, output_tokens=output_tokens+?, "
                "tokens_reported=MAX(tokens_reported, ?) WHERE run_id=? AND idx=?",
                (inp, out, 1 if reported else 0, rid, idx))

    def token_totals(self, story_id: Optional[str] = None) -> dict:
        sql = ("SELECT r.kind, COALESCE(SUM(s.input_tokens),0) AS i, COALESCE(SUM(s.output_tokens),0) AS o, "
               "COALESCE(MAX(s.tokens_reported),0) AS rep FROM steps s JOIN runs r ON r.id=s.run_id")
        args: tuple = ()
        if story_id:
            sql += " WHERE r.story_id=?"
            args = (story_id,)
        sql += " GROUP BY r.kind"
        out = {"analysis": {"input": 0, "output": 0}, "implementation": {"input": 0, "output": 0},
               "any_reported": False}
        for r in self._q(sql, args):
            out[r["kind"]] = {"input": r["i"], "output": r["o"]}
            out["any_reported"] = out["any_reported"] or bool(r["rep"])
        return out

    # --- events -------------------------------------------------------------------------

    def event(self, rid: str, kind: str, text: str, step: Optional[str] = None) -> int:
        return self._x("INSERT INTO events (run_id, ts, step, kind, text) VALUES (?,?,?,?,?)",
                       (rid, now(), step, kind, text))

    def events(self, rid: str, after: int = 0, limit: int = 500) -> List[dict]:
        return [dict(r) for r in self._q(
            "SELECT * FROM events WHERE run_id=? AND id>? ORDER BY id LIMIT ?", (rid, after, limit))]


def _run_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["context"] = json.loads(d.pop("context_json") or "{}")
    d["result"] = json.loads(d.pop("result_json")) if d.get("result_json") else None
    return d

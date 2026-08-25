"""Read-write repository over queue.db — the operational record of every
case review, persisted so a review is replayable from the store at any
time, during execution or long after it finished (the same discipline
A2's `run_store.py` follows for investigations).

Creates its own schema on first use: like `run_store.py`, this holds
operational state, not build-time data — unlike `cohort_store.py`, which is
read-only over data `data/build_cohort_store.py` builds ahead of time.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from cohort.store.models import ReviewCase, ReviewEvent

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_cases (
    patient_id TEXT PRIMARY KEY,
    risk_score REAL NOT NULL,
    risk_tier TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    decision TEXT,
    override_notes TEXT,
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS review_events (
    patient_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    node TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (patient_id, sequence)
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _case_from_row(row: sqlite3.Row) -> ReviewCase:
    return ReviewCase(
        patient_id=row["patient_id"],
        risk_score=row["risk_score"],
        risk_tier=row["risk_tier"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        decision=row["decision"],
        override_notes=row["override_notes"],
        decided_at=row["decided_at"],
    )


class QueueStore:
    """Persists review cases and their node-by-node events — the single
    source of truth the queue and case-detail API routes read from."""

    def __init__(self, db_path: Path) -> None:
        # check_same_thread=False: FastAPI runs sync-ish request handling and
        # the background review executor from different tasks/threads.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def enqueue_case(self, patient_id: str, risk_score: float, risk_tier: str) -> None:
        now = _now()
        self._conn.execute(
            "INSERT OR IGNORE INTO review_cases "
            "(patient_id, risk_score, risk_tier, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'pending', ?, ?)",
            (patient_id, risk_score, risk_tier, now, now),
        )
        self._conn.commit()

    def get_case(self, patient_id: str) -> ReviewCase | None:
        row = self._conn.execute(
            "SELECT * FROM review_cases WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        return _case_from_row(row) if row else None

    def list_queue(self, status: str | None = None) -> list[ReviewCase]:
        if status is None:
            rows = self._conn.execute(
                "SELECT * FROM review_cases ORDER BY risk_score DESC"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM review_cases WHERE status = ? ORDER BY risk_score DESC",
                (status,),
            ).fetchall()
        return [_case_from_row(row) for row in rows]

    def set_status(self, patient_id: str, status: str) -> None:
        self._conn.execute(
            "UPDATE review_cases SET status = ?, updated_at = ? WHERE patient_id = ?",
            (status, _now(), patient_id),
        )
        self._conn.commit()

    def record_decision(self, patient_id: str, decision: str, override_notes: str | None) -> None:
        now = _now()
        self._conn.execute(
            "UPDATE review_cases SET status = 'decided', decision = ?, override_notes = ?, "
            "decided_at = ?, updated_at = ? WHERE patient_id = ?",
            (decision, override_notes, now, now, patient_id),
        )
        self._conn.commit()

    def append_event(self, patient_id: str, sequence: int, node: str, payload_json: str) -> None:
        self._conn.execute(
            "INSERT INTO review_events (patient_id, sequence, node, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (patient_id, sequence, node, payload_json, _now()),
        )
        self._conn.commit()

    def get_events(self, patient_id: str, after_sequence: int = -1) -> list[ReviewEvent]:
        rows = self._conn.execute(
            "SELECT * FROM review_events WHERE patient_id = ? AND sequence > ? ORDER BY sequence",
            (patient_id, after_sequence),
        ).fetchall()
        return [
            ReviewEvent(
                patient_id=row["patient_id"],
                sequence=row["sequence"],
                node=row["node"],
                payload_json=row["payload_json"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

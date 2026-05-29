from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or settings.database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patient_sessions (
                    id TEXT PRIMARY KEY,
                    patient_json TEXT NOT NULL,
                    transcript TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    clinical_tools_json TEXT NOT NULL DEFAULT '[]',
                    imaging_results_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create(self, patient: dict[str, Any] | None = None) -> dict[str, Any]:
        now = utc_now_iso()
        session_id = str(uuid.uuid4())
        patient_data = patient or {}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO patient_sessions (
                    id, patient_json, transcript, summary, clinical_tools_json,
                    imaging_results_json, created_at, updated_at
                ) VALUES (?, ?, '', '', '[]', '[]', ?, ?)
                """,
                (session_id, json.dumps(patient_data, ensure_ascii=False), now, now),
            )
            conn.commit()
        return self.get(session_id) or {}

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM patient_sessions WHERE id = ?", (session_id,)).fetchone()
        return self._row_to_session(row) if row else None

    def list(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM patient_sessions ORDER BY updated_at DESC").fetchall()
        return [self._row_to_session(row) for row in rows]

    def update(self, session_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get(session_id)
        if not current:
            return None
        updated = {**current, **changes, "updatedAt": utc_now_iso()}
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE patient_sessions
                SET patient_json = ?, transcript = ?, summary = ?, clinical_tools_json = ?,
                    imaging_results_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(updated.get("patient", {}), ensure_ascii=False),
                    updated.get("transcript", ""),
                    updated.get("summary", ""),
                    json.dumps(updated.get("clinicalToolResults", []), ensure_ascii=False),
                    json.dumps(updated.get("imagingResults", []), ensure_ascii=False),
                    updated["updatedAt"],
                    session_id,
                ),
            )
            conn.commit()
        return self.get(session_id)

    def append(self, session_id: str, key: str, value: Any) -> dict[str, Any] | None:
        current = self.get(session_id)
        if not current:
            return None
        items = current.get(key, [])
        if not isinstance(items, list):
            items = []
        items.append(value)
        return self.update(session_id, {key: items})

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "patient": json.loads(row["patient_json"] or "{}"),
            "transcript": row["transcript"],
            "summary": row["summary"],
            "clinicalToolResults": json.loads(row["clinical_tools_json"] or "[]"),
            "imagingResults": json.loads(row["imaging_results_json"] or "[]"),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

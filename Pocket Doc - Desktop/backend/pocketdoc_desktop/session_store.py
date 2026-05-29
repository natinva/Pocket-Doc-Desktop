from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import settings


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class SessionStore:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or settings.database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS patient_sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    patient_json TEXT NOT NULL,
                    transcript TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    doctor_notes TEXT NOT NULL DEFAULT '',
                    clinical_tool_results_json TEXT NOT NULL DEFAULT '[]',
                    imaging_results_json TEXT NOT NULL DEFAULT '[]',
                    warnings_json TEXT NOT NULL DEFAULT '[]',
                    finalized INTEGER NOT NULL DEFAULT 0,
                    archived INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._ensure_column(connection, "archived", "INTEGER NOT NULL DEFAULT 0")
            connection.commit()

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, column_name: str, definition: str) -> None:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(patient_sessions)").fetchall()}
        if column_name not in columns:
            connection.execute(f"ALTER TABLE patient_sessions ADD COLUMN {column_name} {definition}")

    def create(self, patient: dict[str, Any] | None = None) -> dict[str, Any]:
        now = utc_now_iso()
        session = {
            "id": str(uuid4()),
            "createdAt": now,
            "updatedAt": now,
            "patient": patient or {},
            "transcript": "",
            "summary": "",
            "doctorNotes": "",
            "clinicalToolResults": [],
            "imagingResults": [],
            "warnings": [],
            "finalized": False,
            "archived": False,
        }
        self._upsert(session)
        return deepcopy(session)

    def list(
        self,
        query: str | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM patient_sessions ORDER BY updated_at DESC, created_at DESC"
            ).fetchall()
        sessions = [self._row_to_session(row) for row in rows]
        if not include_archived:
            sessions = [session for session in sessions if not session.get("archived")]
        if status:
            status_value = status.lower().strip()
            sessions = [session for session in sessions if _session_status(session) == status_value]
        if query:
            needle = query.lower().strip()
            if needle:
                sessions = [session for session in sessions if _matches_query(session, needle)]
        return sessions

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM patient_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return self._row_to_session(row) if row else None

    def update(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        session = self.get(session_id)
        if not session:
            return None
        session.update(patch)
        session["updatedAt"] = utc_now_iso()
        self._upsert(session)
        return deepcopy(session)

    def append(self, session_id: str, key: str, value: dict[str, Any]) -> dict[str, Any] | None:
        session = self.get(session_id)
        if not session:
            return None
        if key not in session or not isinstance(session[key], list):
            session[key] = []
        session[key].append(value)
        session["updatedAt"] = utc_now_iso()
        self._upsert(session)
        return deepcopy(session)

    def archive(self, session_id: str, archived: bool = True) -> dict[str, Any] | None:
        return self.update(session_id, {"archived": archived})

    def delete(self, session_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM patient_sessions WHERE id = ?", (session_id,))
            connection.commit()
            return cursor.rowcount > 0

    def _upsert(self, session: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO patient_sessions (
                    id, created_at, updated_at, patient_json, transcript, summary,
                    doctor_notes, clinical_tool_results_json, imaging_results_json,
                    warnings_json, finalized, archived
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    patient_json = excluded.patient_json,
                    transcript = excluded.transcript,
                    summary = excluded.summary,
                    doctor_notes = excluded.doctor_notes,
                    clinical_tool_results_json = excluded.clinical_tool_results_json,
                    imaging_results_json = excluded.imaging_results_json,
                    warnings_json = excluded.warnings_json,
                    finalized = excluded.finalized,
                    archived = excluded.archived
                """,
                (
                    session["id"],
                    session.get("createdAt") or utc_now_iso(),
                    session.get("updatedAt") or utc_now_iso(),
                    _dump_json(session.get("patient", {})),
                    session.get("transcript", ""),
                    session.get("summary", ""),
                    session.get("doctorNotes", ""),
                    _dump_json(session.get("clinicalToolResults", [])),
                    _dump_json(session.get("imagingResults", [])),
                    _dump_json(session.get("warnings", [])),
                    1 if session.get("finalized") else 0,
                    1 if session.get("archived") else 0,
                ),
            )
            connection.commit()

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "patient": _load_json(row["patient_json"], {}),
            "transcript": row["transcript"] or "",
            "summary": row["summary"] or "",
            "doctorNotes": row["doctor_notes"] or "",
            "clinicalToolResults": _load_json(row["clinical_tool_results_json"], []),
            "imagingResults": _load_json(row["imaging_results_json"], []),
            "warnings": _load_json(row["warnings_json"], []),
            "finalized": bool(row["finalized"]),
            "archived": bool(row["archived"]),
        }


def _session_status(session: dict[str, Any]) -> str:
    if session.get("archived"):
        return "archived"
    if session.get("finalized"):
        return "final"
    if session.get("summary"):
        return "summary"
    if session.get("transcript"):
        return "transcript"
    return "draft"


def _matches_query(session: dict[str, Any], needle: str) -> bool:
    patient = session.get("patient") or {}
    haystack = " ".join(
        str(value or "")
        for value in [
            session.get("id"),
            patient.get("displayName"),
            patient.get("age"),
            patient.get("sex"),
            patient.get("chiefComplaint"),
            session.get("summary"),
            session.get("doctorNotes"),
            session.get("transcript"),
        ]
    ).lower()
    return needle in haystack


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return deepcopy(fallback)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return deepcopy(fallback)

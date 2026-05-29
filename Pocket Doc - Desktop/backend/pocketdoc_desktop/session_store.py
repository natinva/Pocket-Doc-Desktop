from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def create(self, patient: dict[str, Any] | None = None) -> dict[str, Any]:
        session_id = str(uuid4())
        session = {
            "id": session_id,
            "createdAt": utc_now_iso(),
            "updatedAt": utc_now_iso(),
            "patient": patient or {},
            "transcript": "",
            "summary": "",
            "doctorNotes": "",
            "clinicalToolResults": [],
            "imagingResults": [],
            "warnings": [],
            "finalized": False,
        }
        self._sessions[session_id] = session
        return deepcopy(session)

    def list(self) -> list[dict[str, Any]]:
        return [deepcopy(s) for s in self._sessions.values()]

    def get(self, session_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        return deepcopy(session) if session else None

    def update(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.update(patch)
        session["updatedAt"] = utc_now_iso()
        return deepcopy(session)

    def append(self, session_id: str, key: str, value: dict[str, Any]) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        if key not in session or not isinstance(session[key], list):
            session[key] = []
        session[key].append(value)
        session["updatedAt"] = utc_now_iso()
        return deepcopy(session)

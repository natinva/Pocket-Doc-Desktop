from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .config import settings


SENSITIVE_KEYS = {"pin", "transcript", "summary", "doctorNotes", "patient", "warnings", "inputs"}


def audit_event(action: str, details: dict[str, Any] | None = None) -> None:
    if not settings.audit_log_enabled:
        return
    safe_details = _scrub(details or {})
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "details": safe_details,
    }
    settings.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    with settings.audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        scrubbed: dict[str, Any] = {}
        for key, item in value.items():
            if key in SENSITIVE_KEYS:
                scrubbed[key] = "[redacted]"
            elif key == "session_id" and isinstance(item, str):
                scrubbed[key] = item[:8]
            else:
                scrubbed[key] = _scrub(item)
        return scrubbed
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value

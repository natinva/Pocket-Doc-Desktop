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


def read_audit_events(limit: int = 100) -> list[dict[str, Any]]:
    if not settings.audit_log_path.exists():
        return []
    safe_limit = min(max(limit, 1), 500)
    lines = settings.audit_log_path.read_text(encoding="utf-8").splitlines()[-safe_limit:]
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            events.append({"ts": "", "action": "invalid_log_line", "details": {}})
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    return list(reversed(events))


def audit_summary() -> dict[str, Any]:
    events = read_audit_events(limit=500)
    counts: dict[str, int] = {}
    for event in events:
        action = str(event.get("action") or "unknown")
        counts[action] = counts.get(action, 0) + 1
    return {
        "enabled": settings.audit_log_enabled,
        "path": str(settings.audit_log_path),
        "recentEventCount": len(events),
        "actionCounts": counts,
    }


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

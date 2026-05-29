from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from hmac import compare_digest
from typing import Any

from .config import settings


class AccessTokenManager:
    def __init__(self) -> None:
        self._tokens: dict[str, datetime] = {}

    def issue(self) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.access_token_ttl_seconds)
        self._tokens[token] = expires_at
        self._purge_expired()
        return {"token": token, "expiresAt": expires_at.isoformat()}

    def verify(self, token: str | None) -> bool:
        if not settings.device_pin:
            return True
        if not token:
            return False
        self._purge_expired()
        for known_token, expires_at in self._tokens.items():
            if compare_digest(known_token, token) and expires_at > datetime.now(timezone.utc):
                return True
        return False

    def revoke(self, token: str | None) -> None:
        if token:
            self._tokens.pop(token, None)

    def _purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [token for token, expires_at in self._tokens.items() if expires_at <= now]
        for token in expired:
            self._tokens.pop(token, None)


access_tokens = AccessTokenManager()

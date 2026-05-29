from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from hmac import compare_digest
from typing import Any

from .config import settings


PIN_HASH_PREFIX = "pbkdf2_sha256"


def pin_is_enabled() -> bool:
    return bool(settings.device_pin_hash or settings.device_pin)


def pin_storage_mode() -> str:
    if settings.device_pin_hash:
        return "hashed"
    if settings.device_pin:
        return "legacy_plaintext"
    return "disabled"


def hash_pin(pin: str, salt: bytes | None = None, iterations: int | None = None) -> str:
    salt_bytes = salt or secrets.token_bytes(16)
    rounds = iterations or settings.pin_hash_iterations
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt_bytes, rounds)
    return ":".join(
        [
            PIN_HASH_PREFIX,
            str(rounds),
            base64.urlsafe_b64encode(salt_bytes).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def verify_pin_value(pin: str) -> bool:
    if settings.device_pin_hash:
        return verify_pin_hash(pin, settings.device_pin_hash)
    if settings.device_pin:
        return compare_digest(str(pin), str(settings.device_pin))
    return True


def verify_pin_hash(pin: str, encoded_hash: str) -> bool:
    try:
        algorithm, rounds_text, salt_text, digest_text = encoded_hash.split(":", 3)
        if algorithm != PIN_HASH_PREFIX:
            return False
        rounds = int(rounds_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    except Exception:
        return False
    actual_digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, rounds)
    return compare_digest(actual_digest, expected_digest)


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
        if not pin_is_enabled():
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

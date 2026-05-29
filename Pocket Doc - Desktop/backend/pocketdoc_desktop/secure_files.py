from __future__ import annotations

import base64
import hashlib
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from .config import settings


class SecureFileStore:
    def __init__(self) -> None:
        self.enabled = settings.file_protection_enabled and bool(settings.file_protection_secret)
        self.available = self._fernet_available()
        self.active = self.enabled and self.available

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "available": self.available,
            "active": self.active,
            "mode": "fernet" if self.active else "plain",
        }

    def save_upload(self, content: bytes, filename: str, prefix: str = "upload") -> Path:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".bin"
        if self.active:
            target = settings.upload_dir / f"{prefix}-{uuid4()}{suffix}.pdoc"
            target.write_bytes(self._encrypt(content))
            return target
        target = settings.upload_dir / f"{prefix}-{uuid4()}{suffix}"
        target.write_bytes(content)
        return target

    def read_bytes(self, path: Path) -> bytes:
        content = path.read_bytes()
        if self.active and path.suffix == ".pdoc":
            return self._decrypt(content)
        return content

    @contextmanager
    def readable_path(self, path: Path, suffix: str = ".bin") -> Iterator[Path]:
        if self.active and path.suffix == ".pdoc":
            settings.secure_temp_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.secure_temp_dir) as handle:
                temp_path = Path(handle.name)
                handle.write(self.read_bytes(path))
            try:
                yield temp_path
            finally:
                self.safe_unlink(temp_path, allow_outside_uploads=True)
        else:
            yield path

    def safe_unlink(self, path: Path | str | None, allow_outside_uploads: bool = False) -> bool:
        if not path:
            return False
        candidate = Path(path)
        try:
            resolved = candidate.resolve()
        except OSError:
            return False
        allowed_roots = [settings.upload_dir.resolve()]
        if allow_outside_uploads:
            allowed_roots.append(settings.secure_temp_dir.resolve())
        if not any(_is_relative_to(resolved, root) for root in allowed_roots):
            return False
        if not resolved.exists() or not resolved.is_file():
            return False
        try:
            resolved.unlink()
            return True
        except OSError:
            return False

    def _encrypt(self, content: bytes) -> bytes:
        return self._fernet().encrypt(content)

    def _decrypt(self, content: bytes) -> bytes:
        return self._fernet().decrypt(content)

    def _fernet(self):
        from cryptography.fernet import Fernet

        return Fernet(self._derive_fernet_key())

    @staticmethod
    def _fernet_available() -> bool:
        try:
            import cryptography.fernet  # noqa: F401
        except Exception:
            return False
        return True

    @staticmethod
    def _derive_fernet_key() -> bytes:
        salt = b"pocketdoc-desktop-file-protection-v1"
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            (settings.file_protection_secret or "").encode("utf-8"),
            salt,
            settings.file_protection_iterations,
            dklen=32,
        )
        return base64.urlsafe_b64encode(digest)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


secure_files = SecureFileStore()

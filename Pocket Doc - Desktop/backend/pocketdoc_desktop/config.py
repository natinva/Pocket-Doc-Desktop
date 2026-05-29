from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("POCKETDOC_ENV", "development")
    host: str = os.getenv("POCKETDOC_HOST", "0.0.0.0")
    port: int = int(os.getenv("POCKETDOC_PORT", "8765"))
    model_base_dir: Path = Path(
        os.getenv(
            "POCKETDOC_MODEL_BASE_DIR",
            "/Users/avnitan/PycharmProjects/TestProject/PocketDoc/Modeller",
        )
    )
    inference_backend: str = os.getenv("POCKETDOC_INFERENCE_BACKEND", "mock")
    upload_dir: Path = _path_from_env("POCKETDOC_UPLOAD_DIR", PROJECT_ROOT / "uploads")
    data_dir: Path = _path_from_env("POCKETDOC_DATA_DIR", PROJECT_ROOT / "data")
    reports_dir: Path = _path_from_env("POCKETDOC_REPORTS_DIR", PROJECT_ROOT / "reports")
    database_path: Path = _path_from_env("POCKETDOC_DATABASE_PATH", PROJECT_ROOT / "data" / "pocketdoc.sqlite3")
    audit_log_path: Path = _path_from_env("POCKETDOC_AUDIT_LOG_PATH", PROJECT_ROOT / "data" / "audit.log")
    device_pin: str | None = os.getenv("POCKETDOC_DEVICE_PIN") or None
    device_lock_timeout_seconds: int = int(os.getenv("POCKETDOC_LOCK_TIMEOUT_SECONDS", "900"))
    access_token_ttl_seconds: int = int(os.getenv("POCKETDOC_ACCESS_TOKEN_TTL_SECONDS", "3600"))
    local_only_mode: bool = os.getenv("POCKETDOC_LOCAL_ONLY_MODE", "true").lower() in {"1", "true", "yes", "on"}
    audit_log_enabled: bool = os.getenv("POCKETDOC_AUDIT_LOG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_transcribe_model: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    openai_summary_model: str = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4.1-mini")


def ensure_runtime_dirs(settings: Settings) -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.audit_log_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
ensure_runtime_dirs(settings)

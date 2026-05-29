from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    def __init__(self) -> None:
        self.env = os.getenv("POCKETDOC_ENV", "development")
        self.host = os.getenv("POCKETDOC_HOST", "0.0.0.0")
        self.port = int(os.getenv("POCKETDOC_PORT", "8765"))
        self.database_path = PROJECT_ROOT / os.getenv("POCKETDOC_DATABASE_PATH", "runtime/pocketdoc.sqlite3")
        self.upload_dir = PROJECT_ROOT / os.getenv("POCKETDOC_UPLOAD_DIR", "runtime/uploads")
        self.export_dir = PROJECT_ROOT / os.getenv("POCKETDOC_EXPORT_DIR", "runtime/exports")
        self.inference_backend = os.getenv("POCKETDOC_INFERENCE_BACKEND", "mock")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    def ensure_runtime_dirs(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_runtime_dirs()

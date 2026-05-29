from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    upload_dir: Path = PROJECT_ROOT / "uploads"
    data_dir: Path = PROJECT_ROOT / "data"
    reports_dir: Path = PROJECT_ROOT / "reports"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_transcribe_model: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    openai_summary_model: str = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4.1-mini")


settings = Settings()

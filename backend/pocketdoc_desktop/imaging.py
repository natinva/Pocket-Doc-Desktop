from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .config import settings
from .session_store import utc_now_iso

MODEL_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "ortho-elbow-demo",
        "titleTR": "Pediatrik Dirsek Röntgen Demo Analizi",
        "modality": "xray",
        "bodyRegion": "elbow",
        "status": "mock",
    },
    {
        "id": "skin-lesion-demo",
        "titleTR": "Deri Lezyonu Demo Analizi",
        "modality": "photo",
        "bodyRegion": "skin",
        "status": "mock",
    },
]


def registry_summary() -> dict[str, Any]:
    return {"count": len(MODEL_REGISTRY), "backend": settings.inference_backend}


def flatten_models() -> list[dict[str, Any]]:
    return MODEL_REGISTRY


class ImagingService:
    def save_upload(self, content: bytes, filename: str) -> Path:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".bin"
        path = settings.upload_dir / f"{uuid.uuid4()}{suffix}"
        path.write_bytes(content)
        return path

    def analyze(self, model_id: str, image_path: Path) -> dict[str, Any]:
        model = next((item for item in MODEL_REGISTRY if item["id"] == model_id), None)
        if not model:
            raise KeyError(f"Bilinmeyen model: {model_id}")
        return {
            "modelId": model_id,
            "modelTitleTR": model["titleTR"],
            "status": "mock-result",
            "createdAt": utc_now_iso(),
            "imagePath": str(image_path),
            "findingsTR": "Bu MVP aşamasında gerçek görüntü analizi yapılmadı. Görüntü kaydedildi ve model akışı test edildi.",
            "requiresDoctorApproval": True,
        }

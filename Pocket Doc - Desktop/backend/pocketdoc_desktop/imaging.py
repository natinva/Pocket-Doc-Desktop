from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import settings
from .model_registry import find_model
from .session_store import utc_now_iso


class ImagingService:
    def __init__(self) -> None:
        self.backend = settings.inference_backend

    def save_upload(self, content: bytes, filename: str) -> Path:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".img"
        target = settings.upload_dir / f"{uuid4()}{suffix}"
        target.write_bytes(content)
        return target

    def analyze(self, model_id: str, image_path: Path, source: str = "upload") -> dict[str, Any]:
        model = find_model(model_id)
        if not model:
            raise KeyError(f"Unknown model id: {model_id}")

        if self.backend == "mock":
            return {
                "id": str(uuid4()),
                "modelId": model_id,
                "modelName": model["name"],
                "domain": model["domain"],
                "modality": model.get("modality"),
                "backend": "mock",
                "source": source,
                "imagePath": str(image_path),
                "imageBytes": image_path.stat().st_size if image_path.exists() else None,
                "resultSummaryTR": "Görüntü alındı. Gerçek inference backend'i henüz mock modda.",
                "detections": [],
                "warningsTR": [
                    "Bu sonuç demo/mock çıktıdır.",
                    "Hailo/ONNX/Ultralytics backend bağlandığında gerçek model sonucu burada görünecek.",
                ],
                "generatedAt": utc_now_iso(),
            }

        return {
            "id": str(uuid4()),
            "modelId": model_id,
            "modelName": model["name"],
            "domain": model["domain"],
            "backend": self.backend,
            "source": source,
            "imagePath": str(image_path),
            "resultSummaryTR": f"{self.backend} backend seçili; adapter implementasyonu sıradaki milestone.",
            "detections": [],
            "warningsTR": ["Inference adapter pending."],
            "generatedAt": utc_now_iso(),
        }

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import settings
from .model_registry import find_model
from .secure_files import secure_files
from .session_store import utc_now_iso


class ImagingService:
    def __init__(self) -> None:
        self.backend = settings.inference_backend

    def save_upload(self, content: bytes, filename: str) -> Path:
        return secure_files.save_upload(content, filename, prefix="image")

    def analyze(self, model_id: str, image_path: Path, source: str = "upload") -> dict[str, Any]:
        model = find_model(model_id)
        if not model:
            raise KeyError(f"Unknown model id: {model_id}")

        image_size = image_path.stat().st_size if image_path.exists() else None
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
                "imageBytes": image_size,
                "fileProtected": secure_files.active and image_path.suffix == ".pdoc",
                "resultSummaryTR": "Görüntü alındı. Gerçek inference backend'i henüz mock modda.",
                "detections": [],
                "warningsTR": [
                    "Bu sonuç demo/mock çıktıdır.",
                    "Hailo/ONNX/Ultralytics backend bağlandığında gerçek model sonucu burada görünecek.",
                ],
                "generatedAt": utc_now_iso(),
            }

        with secure_files.readable_path(image_path, suffix=Path(image_path.name.replace(".pdoc", "")).suffix or ".img") as readable_image:
            return {
                "id": str(uuid4()),
                "modelId": model_id,
                "modelName": model["name"],
                "domain": model["domain"],
                "backend": self.backend,
                "source": source,
                "imagePath": str(image_path),
                "runtimeImagePath": str(readable_image),
                "fileProtected": secure_files.active and image_path.suffix == ".pdoc",
                "resultSummaryTR": f"{self.backend} backend seçili; adapter implementasyonu sıradaki milestone.",
                "detections": [],
                "warningsTR": ["Inference adapter pending."],
                "generatedAt": utc_now_iso(),
            }

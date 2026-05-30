from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import settings
from .inference_adapters import get_adapter, normalize_options
from .model_registry import find_model
from .postprocess import run_postprocess
from .secure_files import secure_files
from .session_store import utc_now_iso


class ImagingService:
    def __init__(self) -> None:
        self.backend = settings.inference_backend

    def save_upload(self, content: bytes, filename: str) -> Path:
        return secure_files.save_upload(content, filename, prefix="image")

    def analyze(self, model_id: str, image_path: Path, source: str = "upload", options: dict[str, Any] | None = None) -> dict[str, Any]:
        model = find_model(model_id)
        if not model:
            raise KeyError(f"Unknown model id: {model_id}")
        options = normalize_options(options)

        with secure_files.readable_path(image_path, suffix=Path(image_path.name.replace(".pdoc", "")).suffix or ".img") as readable_image:
            try:
                adapter = get_adapter(self.backend)
                result = adapter.predict(model, readable_image, options=options)
            except Exception as exc:
                result = self._fallback_result(model, image_path, exc, options)

        result["source"] = source
        result["imagePath"] = str(image_path)
        result["fileProtected"] = secure_files.active and image_path.suffix == ".pdoc"
        result.setdefault("detections", [])
        result.setdefault("classifications", [])
        result.setdefault("masks", [])
        result.setdefault("keypoints", [])
        result.setdefault("findings", {})
        result.setdefault("warningsTR", [])
        if result["fileProtected"]:
            result["warningsTR"].append("Yüklenen dosya disk üzerinde korumalı formatta saklandı.")
        if settings.demo_enable_postprocess:
            postprocess_result = run_postprocess(model, result)
            if postprocess_result:
                result["postprocessResult"] = postprocess_result
                if postprocess_result.get("summaryTR"):
                    result["warningsTR"].append(f"Postprocess: {postprocess_result['summaryTR']}")
        return result

    def _fallback_result(self, model: dict[str, Any], image_path: Path, error: Exception, options: dict[str, Any] | None = None) -> dict[str, Any]:
        options = normalize_options(options)
        image_size = image_path.stat().st_size if image_path.exists() else None
        return {
            "id": str(uuid4()),
            "modelId": model["id"],
            "modelName": model["name"],
            "domain": model.get("domain"),
            "modality": model.get("modality"),
            "backend": self.backend,
            "imagePath": str(image_path),
            "modelPath": model.get("path"),
            "modelExists": Path(str(model.get("path", ""))).exists(),
            "imageBytes": image_size,
            "inferenceOptions": options,
            "fileProtected": secure_files.active and image_path.suffix == ".pdoc",
            "resultSummaryTR": "Inference çalıştırılamadı; güvenli fallback sonucu üretildi.",
            "detections": [],
            "classifications": [],
            "masks": [],
            "keypoints": [],
            "findings": {
                "model": model.get("name"),
                "model_id": model.get("id"),
                "modality": model.get("modality"),
                "conf_threshold": float(options["conf"]),
                "iou_threshold": float(options["iou"]),
                "imgsz": int(options["imgsz"]),
                "max_det": int(options["max_det"]),
                "timestamp": utc_now_iso(),
                "detections": [],
                "classification": None,
            },
            "warningsTR": [
                "Model çıktısı üretilemedi.",
                f"Backend: {self.backend}",
                f"Hata: {type(error).__name__}: {error}",
            ],
            "generatedAt": utc_now_iso(),
        }

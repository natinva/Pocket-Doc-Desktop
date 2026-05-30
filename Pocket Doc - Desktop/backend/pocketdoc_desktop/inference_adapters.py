from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from .session_store import utc_now_iso


class InferenceAdapter(Protocol):
    name: str

    def predict(self, model: dict[str, Any], image_path: Path) -> dict[str, Any]:
        ...


class MockAdapter:
    name = "mock"

    def predict(self, model: dict[str, Any], image_path: Path) -> dict[str, Any]:
        return _base_result(model, image_path, self.name) | {
            "resultSummaryTR": "Görüntü alındı. Gerçek inference backend'i henüz mock modda.",
            "detections": [],
            "classifications": [],
            "masks": [],
            "keypoints": [],
            "warningsTR": [
                "Bu sonuç demo/mock çıktıdır.",
                "Gerçek model sonucu için POCKETDOC_INFERENCE_BACKEND=ultralytics veya onnx_runtime seçilmelidir.",
            ],
        }


class UltralyticsAdapter:
    name = "ultralytics"

    def __init__(self) -> None:
        try:
            from ultralytics import YOLO  # noqa: F401
        except Exception as exc:
            raise RuntimeError("Ultralytics package is not installed. Install ultralytics or use mock backend.") from exc

    def predict(self, model: dict[str, Any], image_path: Path) -> dict[str, Any]:
        from ultralytics import YOLO

        model_path = Path(model["path"])
        if not model_path.exists():
            return _missing_model_result(model, image_path, self.name)

        yolo = YOLO(str(model_path))
        task = model.get("force_task")
        raw_results = yolo.predict(str(image_path), verbose=False, task=task) if task else yolo.predict(str(image_path), verbose=False)
        detections: list[dict[str, Any]] = []
        classifications: list[dict[str, Any]] = []
        masks: list[dict[str, Any]] = []
        keypoints: list[dict[str, Any]] = []

        for raw in raw_results:
            names = getattr(raw, "names", {}) or {}
            boxes = getattr(raw, "boxes", None)
            if boxes is not None:
                for box in boxes:
                    cls_idx = int(box.cls[0]) if getattr(box, "cls", None) is not None else -1
                    confidence = float(box.conf[0]) if getattr(box, "conf", None) is not None else None
                    xyxy = box.xyxy[0].tolist() if getattr(box, "xyxy", None) is not None else []
                    detections.append({
                        "label": str(names.get(cls_idx, cls_idx)),
                        "classIndex": cls_idx,
                        "confidence": confidence,
                        "bboxXYXY": [float(value) for value in xyxy],
                    })

            raw_masks = getattr(raw, "masks", None)
            if raw_masks is not None and getattr(raw_masks, "xy", None) is not None:
                for index, polygon in enumerate(raw_masks.xy):
                    related_detection = detections[index] if index < len(detections) else {}
                    points = _points_to_xy_list(polygon)
                    if not points:
                        continue
                    masks.append({
                        "label": related_detection.get("label", f"mask_{index + 1}"),
                        "classIndex": related_detection.get("classIndex"),
                        "confidence": related_detection.get("confidence"),
                        "polygonXY": points,
                    })

            raw_keypoints = getattr(raw, "keypoints", None)
            if raw_keypoints is not None and getattr(raw_keypoints, "xy", None) is not None:
                keypoint_xy = raw_keypoints.xy
                keypoint_conf = getattr(raw_keypoints, "conf", None)
                for item_index, item_points in enumerate(keypoint_xy):
                    points = _points_to_keypoint_list(item_points, keypoint_conf[item_index] if keypoint_conf is not None else None)
                    if not points:
                        continue
                    keypoints.append({
                        "label": f"keypoints_{item_index + 1}",
                        "points": points,
                    })

            probs = getattr(raw, "probs", None)
            if probs is not None and getattr(probs, "top5", None) is not None:
                for cls_idx in probs.top5:
                    confidence = float(probs.data[cls_idx])
                    classifications.append({"label": str(names.get(int(cls_idx), int(cls_idx))), "classIndex": int(cls_idx), "confidence": confidence})

        summary = _summarize_prediction(detections, classifications, masks, keypoints)
        return _base_result(model, image_path, self.name) | {
            "resultSummaryTR": summary,
            "detections": detections,
            "classifications": classifications,
            "masks": masks,
            "keypoints": keypoints,
            "warningsTR": _clinical_warnings(model, detections, classifications, masks, keypoints),
        }


class OnnxRuntimeAdapter:
    name = "onnx_runtime"

    def __init__(self) -> None:
        try:
            import onnxruntime  # noqa: F401
        except Exception as exc:
            raise RuntimeError("onnxruntime package is not installed. Install onnxruntime or use mock backend.") from exc

    def predict(self, model: dict[str, Any], image_path: Path) -> dict[str, Any]:
        model_path = Path(model["path"])
        if not model_path.exists():
            return _missing_model_result(model, image_path, self.name)
        return _base_result(model, image_path, self.name) | {
            "resultSummaryTR": "ONNX Runtime backend hazır; model özel pre/postprocess adapteri henüz tanımlanmadı.",
            "detections": [],
            "classifications": [],
            "masks": [],
            "keypoints": [],
            "warningsTR": [
                "ONNX model bulundu ancak her model için input preprocessing ve output decoding farklı olabilir.",
                "Bu adapter, model özel parser eklendikten sonra gerçek sonuç üretecek.",
            ],
        }


def get_adapter(name: str) -> InferenceAdapter:
    normalized = (name or "mock").strip().lower()
    if normalized == "mock":
        return MockAdapter()
    if normalized in {"ultralytics", "yolo", "yolov8", "yolov11"}:
        return UltralyticsAdapter()
    if normalized in {"onnx", "onnx_runtime", "onnxruntime"}:
        return OnnxRuntimeAdapter()
    raise ValueError(f"Unsupported inference backend: {name}")


def _base_result(model: dict[str, Any], image_path: Path, backend: str) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "modelId": model["id"],
        "modelName": model["name"],
        "domain": model.get("domain"),
        "modality": model.get("modality"),
        "backend": backend,
        "imagePath": str(image_path),
        "modelPath": model.get("path"),
        "modelExists": Path(str(model.get("path", ""))).exists(),
        "imageBytes": image_path.stat().st_size if image_path.exists() else None,
        "generatedAt": utc_now_iso(),
    }


def _missing_model_result(model: dict[str, Any], image_path: Path, backend: str) -> dict[str, Any]:
    return _base_result(model, image_path, backend) | {
        "resultSummaryTR": "Model dosyası bulunamadığı için analiz çalıştırılamadı.",
        "detections": [],
        "classifications": [],
        "masks": [],
        "keypoints": [],
        "warningsTR": [f"Beklenen model yolu bulunamadı: {model.get('path')}"]
    }


def _summarize_prediction(
    detections: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
    masks: list[dict[str, Any]],
    keypoints: list[dict[str, Any]],
) -> str:
    parts: list[str] = []
    if detections:
        labels = ", ".join(sorted({str(item.get("label")) for item in detections if item.get("label")}))
        parts.append(f"{len(detections)} bbox tespiti: {labels}")
    if masks:
        parts.append(f"{len(masks)} segmentasyon maskesi")
    if keypoints:
        point_count = sum(len(item.get("points") or []) for item in keypoints)
        parts.append(f"{len(keypoints)} keypoint grubu / {point_count} nokta")
    if parts:
        return "; ".join(parts) + "."
    if classifications:
        best = max(classifications, key=lambda item: item.get("confidence") or 0)
        percent = round(float(best.get("confidence") or 0) * 100, 1)
        return f"En yüksek sınıf: {best.get('label')} (%{percent})."
    return "Model çalıştı ancak belirgin tespit/sınıflama çıktısı üretmedi."


def _clinical_warnings(
    model: dict[str, Any],
    detections: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
    masks: list[dict[str, Any]],
    keypoints: list[dict[str, Any]],
) -> list[str]:
    warnings = ["Bu çıktı klinik karar yerine geçmez; hekim değerlendirmesi gerekir."]
    if not detections and not classifications and not masks and not keypoints:
        warnings.append("Negatif/boş model çıktısı hastalık yok anlamına gelmez.")
    if model.get("domain") in {"Dermatology", "Medical Aesthetic"}:
        warnings.append("Dermatolojik görüntülerde ışık, odak ve açı model sonucunu ciddi etkileyebilir.")
    if model.get("modality") and "X-ray" in str(model.get("modality")):
        warnings.append("Radyografik sonuçlar klinik muayene ve orijinal DICOM/röntgen kalitesi ile birlikte yorumlanmalıdır.")
    return warnings


def _points_to_xy_list(points: Any) -> list[list[float]]:
    try:
        raw_points = points.tolist() if hasattr(points, "tolist") else points
    except Exception:
        raw_points = points
    normalized: list[list[float]] = []
    for point in raw_points or []:
        if len(point) < 2:
            continue
        x, y = float(point[0]), float(point[1])
        normalized.append([x, y])
    return normalized


def _points_to_keypoint_list(points: Any, confidence_values: Any | None = None) -> list[dict[str, float]]:
    xy_points = _points_to_xy_list(points)
    try:
        conf_list = confidence_values.tolist() if hasattr(confidence_values, "tolist") else confidence_values
    except Exception:
        conf_list = None
    keypoints: list[dict[str, float]] = []
    for index, point in enumerate(xy_points):
        item = {"index": index, "x": point[0], "y": point[1]}
        if conf_list is not None and index < len(conf_list):
            item["confidence"] = float(conf_list[index])
        keypoints.append(item)
    return keypoints

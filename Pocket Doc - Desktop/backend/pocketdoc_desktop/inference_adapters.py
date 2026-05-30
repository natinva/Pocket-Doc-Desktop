from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import cv2

from .config import settings
from .session_store import utc_now_iso


class InferenceAdapter(Protocol):
    name: str

    def predict(self, model: dict[str, Any], image_path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


class MockAdapter:
    name = "mock"

    def predict(self, model: dict[str, Any], image_path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return _base_result(model, image_path, self.name, options) | {
            "resultSummaryTR": "Görüntü alındı. Mock mod aktif olduğu için gerçek model çalıştırılmadı.",
            "detections": [],
            "classifications": [],
            "masks": [],
            "keypoints": [],
            "findings": _empty_findings(model, options),
            "warningsTR": ["Bu sonuç demo/mock çıktıdır."],
        }


class UltralyticsAdapter:
    name = "ultralytics"
    _models_cache: dict[str, Any] = {}

    def __init__(self) -> None:
        try:
            from ultralytics import YOLO  # noqa: F401
        except Exception as exc:
            raise RuntimeError("Ultralytics package is not installed. Install ultralytics or use mock backend.") from exc

    def predict(self, model: dict[str, Any], image_path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        from ultralytics import YOLO

        options = normalize_options(options)
        model_path = Path(model["path"])
        if not model_path.exists():
            return _missing_model_result(model, image_path, self.name, options)

        raw_image = cv2.imread(str(image_path))
        if raw_image is None:
            raise RuntimeError(f"Could not read the image: {image_path}")

        model_id = str(model.get("id") or model_path)
        if model_id not in self._models_cache:
            force_task = model.get("force_task")
            self._models_cache[model_id] = YOLO(str(model_path), task=force_task) if force_task else YOLO(str(model_path))

        yolo_model = self._models_cache[model_id]
        raw_results = yolo_model.predict(
            raw_image,
            conf=float(options["conf"]),
            iou=float(options["iou"]),
            imgsz=int(options["imgsz"]),
            max_det=int(options["max_det"]),
            verbose=False,
        )
        if not raw_results:
            return _base_result(model, image_path, self.name, options) | {
                "resultSummaryTR": "Model sonuç döndürmedi.",
                "detections": [],
                "classifications": [],
                "masks": [],
                "keypoints": [],
                "findings": _empty_findings(model, options),
                "warningsTR": ["Model returned no result."],
            }

        raw = raw_results[0]
        findings = build_demo_findings(model, raw, raw_image, options)
        detections = _detections_from_findings(findings)
        classifications = _classifications_from_findings(findings)
        masks = _masks_from_result(raw, detections)
        keypoints = _keypoints_from_result(raw)
        summary = _summary_from_findings(findings, masks, keypoints)

        return _base_result(model, image_path, self.name, options) | {
            "resultSummaryTR": summary,
            "detections": detections,
            "classifications": classifications,
            "masks": masks,
            "keypoints": keypoints,
            "findings": findings,
            "warningsTR": ["Demo model çıktısıdır; klinik karar yerine geçmez."],
        }


class OnnxRuntimeAdapter:
    name = "onnx_runtime"

    def __init__(self) -> None:
        try:
            import onnxruntime  # noqa: F401
        except Exception as exc:
            raise RuntimeError("onnxruntime package is not installed. Install onnxruntime or use mock backend.") from exc

    def predict(self, model: dict[str, Any], image_path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        model_path = Path(model["path"])
        options = normalize_options(options)
        if not model_path.exists():
            return _missing_model_result(model, image_path, self.name, options)
        return _base_result(model, image_path, self.name, options) | {
            "resultSummaryTR": "ONNX Runtime backend hazır; model özel pre/postprocess adapteri henüz tanımlanmadı.",
            "detections": [],
            "classifications": [],
            "masks": [],
            "keypoints": [],
            "findings": _empty_findings(model, options),
            "warningsTR": ["ONNX için model özel parser gerekir."],
        }


def get_adapter(name: str) -> InferenceAdapter:
    normalized = (name or "ultralytics").strip().lower()
    if normalized == "mock":
        return MockAdapter()
    if normalized in {"ultralytics", "yolo", "yolov8", "yolov11"}:
        return UltralyticsAdapter()
    if normalized in {"onnx", "onnx_runtime", "onnxruntime"}:
        return OnnxRuntimeAdapter()
    raise ValueError(f"Unsupported inference backend: {name}")


def normalize_options(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    return {
        "conf": float(options.get("conf", settings.demo_conf_threshold)),
        "iou": float(options.get("iou", settings.demo_iou_threshold)),
        "imgsz": int(options.get("imgsz", settings.demo_imgsz)),
        "max_det": int(options.get("max_det", settings.demo_max_det)),
    }


def build_demo_findings(model: dict[str, Any], raw: Any, raw_image: Any, options: dict[str, Any]) -> dict[str, Any]:
    payload = _empty_findings(model, options)
    names = getattr(raw, "names", None)

    probs = getattr(raw, "probs", None)
    if probs is not None:
        try:
            top1 = int(probs.top1)
            top1_conf = float(probs.top1conf)
            payload["classification"] = {"top1": _class_name(names, top1), "confidence": top1_conf}
        except Exception:
            pass

    boxes = getattr(raw, "boxes", None)
    if boxes is not None and len(boxes) > 0:
        try:
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy() if hasattr(boxes, "conf") and boxes.conf is not None else None
            clss = boxes.cls.cpu().numpy() if hasattr(boxes, "cls") and boxes.cls is not None else None
            for i in range(len(xyxy)):
                cls_id = int(clss[i]) if clss is not None else 0
                payload["detections"].append({
                    "class_id": cls_id,
                    "class_name": _class_name(names, cls_id),
                    "confidence": float(confs[i]) if confs is not None else None,
                    "box_xyxy": [float(v) for v in xyxy[i].tolist()],
                    "mask_area_px": None,
                    "mask_area_ratio": None,
                })
        except Exception:
            pass

    masks = getattr(raw, "masks", None)
    if masks is not None and hasattr(masks, "data") and payload["detections"] and raw_image is not None:
        try:
            h, w = raw_image.shape[:2]
            mdata = masks.data.cpu().numpy()
            for i in range(min(len(mdata), len(payload["detections"]))):
                m = mdata[i]
                mask_resized = cv2.resize(m, (w, h))
                mask_bin = mask_resized > 0.5
                area_px = int(mask_bin.sum())
                payload["detections"][i]["mask_area_px"] = area_px
                payload["detections"][i]["mask_area_ratio"] = float(area_px) / float(h * w)
        except Exception:
            pass

    return payload


def _empty_findings(model: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = normalize_options(options)
    return {
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
    }


def _detections_from_findings(findings: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "label": item.get("class_name"),
            "classIndex": item.get("class_id"),
            "confidence": item.get("confidence"),
            "bboxXYXY": item.get("box_xyxy") or [],
            "maskAreaPx": item.get("mask_area_px"),
            "maskAreaRatio": item.get("mask_area_ratio"),
        }
        for item in findings.get("detections", [])
    ]


def _classifications_from_findings(findings: dict[str, Any]) -> list[dict[str, Any]]:
    item = findings.get("classification")
    if not item:
        return []
    return [{"label": item.get("top1"), "confidence": item.get("confidence")}]


def _masks_from_result(raw: Any, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    masks: list[dict[str, Any]] = []
    raw_masks = getattr(raw, "masks", None)
    if raw_masks is None or getattr(raw_masks, "xy", None) is None:
        return masks
    for index, polygon in enumerate(raw_masks.xy):
        related_detection = detections[index] if index < len(detections) else {}
        points = _points_to_xy_list(polygon)
        if points:
            masks.append({
                "label": related_detection.get("label", f"mask_{index + 1}"),
                "classIndex": related_detection.get("classIndex"),
                "confidence": related_detection.get("confidence"),
                "polygonXY": points,
            })
    return masks


def _keypoints_from_result(raw: Any) -> list[dict[str, Any]]:
    raw_keypoints = getattr(raw, "keypoints", None)
    if raw_keypoints is None or getattr(raw_keypoints, "xy", None) is None:
        return []
    keypoints: list[dict[str, Any]] = []
    keypoint_xy = raw_keypoints.xy
    keypoint_conf = getattr(raw_keypoints, "conf", None)
    for item_index, item_points in enumerate(keypoint_xy):
        points = _points_to_keypoint_list(item_points, keypoint_conf[item_index] if keypoint_conf is not None else None)
        if points:
            keypoints.append({"label": f"keypoints_{item_index + 1}", "points": points})
    return keypoints


def _summary_from_findings(findings: dict[str, Any], masks: list[dict[str, Any]], keypoints: list[dict[str, Any]]) -> str:
    detections = findings.get("detections", [])
    classification = findings.get("classification")
    if detections:
        confs = [item["confidence"] for item in detections if item.get("confidence") is not None]
        max_conf = max(confs) if confs else 0.0
        return f"Detections: {len(detections)} | Max confidence: {max_conf:.2f} | Masks: {len(masks)} | Keypoint groups: {len(keypoints)}"
    if classification:
        return f"Classification: {classification.get('top1')} ({float(classification.get('confidence') or 0):.2f})"
    return "Model returned neither boxes/masks nor classification probs."


def _base_result(model: dict[str, Any], image_path: Path, backend: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "inferenceOptions": normalize_options(options),
        "generatedAt": utc_now_iso(),
    }


def _missing_model_result(model: dict[str, Any], image_path: Path, backend: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    return _base_result(model, image_path, backend, options) | {
        "resultSummaryTR": f"Model file not found: {model.get('path')}",
        "detections": [],
        "classifications": [],
        "masks": [],
        "keypoints": [],
        "findings": _empty_findings(model, options),
        "warningsTR": [f"Model file not found: {model.get('path')}"],
    }


def _class_name(names: Any, cls_id: int) -> str:
    if isinstance(names, dict):
        return str(names.get(cls_id, cls_id))
    if isinstance(names, (list, tuple)) and cls_id < len(names):
        return str(names[cls_id])
    return str(cls_id)


def _points_to_xy_list(points: Any) -> list[list[float]]:
    try:
        raw_points = points.tolist() if hasattr(points, "tolist") else points
    except Exception:
        raw_points = points
    normalized: list[list[float]] = []
    for point in raw_points or []:
        if len(point) < 2:
            continue
        normalized.append([float(point[0]), float(point[1])])
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

"""Cep Doktorum AI imaging demo reference.

This file preserves the working inference approach from the local Tkinter demo:
- cache YOLO models by model id
- load with optional force_task
- read image with cv2.imread
- call model.predict(raw_image, conf, iou, imgsz, max_det, verbose=False)
- produce a structured findings payload with boxes, classification and mask area

The production web backend mirrors this behavior in pocketdoc_desktop/inference_adapters.py.
Keep this file lightweight and independent so it can be used as a quick sanity check.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


DEFAULT_CONF = 0.25
DEFAULT_IOU = 0.45
DEFAULT_IMGSZ = 640
DEFAULT_MAX_DET = 300


MODELS_CACHE: dict[str, YOLO] = {}


def load_model(model_id: str, model_path: str, force_task: str | None = None) -> YOLO:
    """Load and cache a YOLO model using the same logic as the original demo."""
    if model_id not in MODELS_CACHE:
        if force_task:
            MODELS_CACHE[model_id] = YOLO(model_path, task=force_task)
        else:
            MODELS_CACHE[model_id] = YOLO(model_path)
    return MODELS_CACHE[model_id]


def class_name(names: Any, cls_id: int) -> str:
    if isinstance(names, dict):
        return str(names.get(cls_id, cls_id))
    if isinstance(names, (list, tuple)) and cls_id < len(names):
        return str(names[cls_id])
    return str(cls_id)


def build_findings_payload(
    res: Any,
    *,
    model_name: str,
    model_id: str,
    modality: str | None,
    raw_image: Any,
    conf: float,
    iou: float,
    imgsz: int,
    max_det: int,
) -> dict[str, Any]:
    """Build the same structured output style as the working Tkinter demo."""
    payload: dict[str, Any] = {
        "model": model_name,
        "model_id": model_id,
        "modality": modality,
        "conf_threshold": float(conf),
        "iou_threshold": float(iou),
        "imgsz": int(imgsz),
        "max_det": int(max_det),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "detections": [],
        "classification": None,
    }

    names = getattr(res, "names", None)

    # Classification
    if hasattr(res, "probs") and res.probs is not None:
        try:
            top1 = int(res.probs.top1)
            top1_conf = float(res.probs.top1conf)
            payload["classification"] = {"top1": class_name(names, top1), "confidence": top1_conf}
        except Exception:
            pass

    # Boxes
    boxes = getattr(res, "boxes", None)
    if boxes is not None and len(boxes) > 0:
        try:
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy() if hasattr(boxes, "conf") and boxes.conf is not None else None
            clss = boxes.cls.cpu().numpy() if hasattr(boxes, "cls") and boxes.cls is not None else None

            for i in range(len(xyxy)):
                cls_id = int(clss[i]) if clss is not None else 0
                payload["detections"].append(
                    {
                        "class_id": cls_id,
                        "class_name": class_name(names, cls_id),
                        "confidence": float(confs[i]) if confs is not None else None,
                        "box_xyxy": [float(v) for v in xyxy[i].tolist()],
                        "mask_area_px": None,
                        "mask_area_ratio": None,
                    }
                )
        except Exception:
            pass

    # Masks -> add area
    masks = getattr(res, "masks", None)
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


def run_analysis(
    *,
    model_id: str,
    model_name: str,
    model_path: str,
    image_path: str,
    modality: str | None = None,
    force_task: str | None = None,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
    imgsz: int = DEFAULT_IMGSZ,
    max_det: int = DEFAULT_MAX_DET,
) -> dict[str, Any]:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    raw_image = cv2.imread(image_path)
    if raw_image is None:
        raise RuntimeError(f"Could not read the image: {image_path}")

    model = load_model(model_id, model_path, force_task=force_task)
    results = model.predict(
        raw_image,
        conf=float(conf),
        iou=float(iou),
        imgsz=int(imgsz),
        max_det=int(max_det),
        verbose=False,
    )
    if not results:
        return {
            "model": model_name,
            "model_id": model_id,
            "modality": modality,
            "conf_threshold": float(conf),
            "iou_threshold": float(iou),
            "imgsz": int(imgsz),
            "max_det": int(max_det),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "detections": [],
            "classification": None,
            "note": "Model returned no result.",
        }

    return build_findings_payload(
        results[0],
        model_name=model_name,
        model_id=model_id,
        modality=modality,
        raw_image=raw_image,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        max_det=max_det,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Cep Doktorum YOLO demo inference.")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--modality", default=None)
    parser.add_argument("--force-task", default=None)
    parser.add_argument("--conf", type=float, default=DEFAULT_CONF)
    parser.add_argument("--iou", type=float, default=DEFAULT_IOU)
    parser.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    parser.add_argument("--max-det", type=int, default=DEFAULT_MAX_DET)
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    findings = run_analysis(
        model_id=args.model_id,
        model_name=args.model_name,
        model_path=args.model_path,
        image_path=args.image_path,
        modality=args.modality,
        force_task=args.force_task,
        conf=args.conf,
        iou=args.iou,
        imgsz=args.imgsz,
        max_det=args.max_det,
    )
    text = json.dumps(findings, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()

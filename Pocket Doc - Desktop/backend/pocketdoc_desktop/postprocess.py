from __future__ import annotations

import math
from typing import Any


def run_postprocess(model: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    postprocess_name = model.get("postprocess")
    if not postprocess_name:
        return None
    if postprocess_name == "supracondylar_pin_geometry":
        return supracondylar_pin_geometry(model, result)
    if postprocess_name == "scoliosis_alignment_measurement":
        return scoliosis_alignment_measurement(model, result)
    if postprocess_name == "kellgren_lawrence_grade_summary":
        return kellgren_lawrence_grade_summary(model, result)
    return {
        "name": postprocess_name,
        "status": "pending",
        "summaryTR": "Bu model için postprocess adı tanımlı ancak işlemci henüz uygulanmadı.",
        "measurements": [],
        "warningsTR": ["Postprocess adapter henüz implement edilmedi."],
    }


def supracondylar_pin_geometry(model: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    detections = result.get("detections") or []
    masks = result.get("masks") or []
    labels = _label_counts(detections + masks)
    measurements: list[dict[str, Any]] = [
        {"key": "detection_count", "labelTR": "BBox tespit sayısı", "value": len(detections), "unit": "adet"},
        {"key": "mask_count", "labelTR": "Segmentasyon maskesi sayısı", "value": len(masks), "unit": "adet"},
    ]
    if masks:
        measurements.extend(_mask_area_measurements(masks))
    ready = bool(masks or detections)
    return {
        "name": "supracondylar_pin_geometry",
        "status": "ready_for_geometry" if ready else "insufficient_output",
        "summaryTR": "Suprakondiler humerus geometri postprocess için model çıktısı alındı." if ready else "Geometri ölçümü için yeterli humerus/K-teli çıktısı bulunamadı.",
        "measurements": measurements,
        "labelCounts": labels,
        "warningsTR": [
            "Bu aşama ölçüm hazırlığıdır; K-teli açı ve oran hesapları için sınıf isimlerinin humerus/fossa/epikondil/K-teli olarak doğrulanması gerekir.",
            "Cerrahi karar veya redüksiyon değerlendirmesi için hekim kontrolü zorunludur.",
        ],
    }


def scoliosis_alignment_measurement(model: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    keypoint_groups = result.get("keypoints") or []
    masks = result.get("masks") or []
    point_count = sum(len(group.get("points") or []) for group in keypoint_groups)
    measurements: list[dict[str, Any]] = [
        {"key": "keypoint_group_count", "labelTR": "Keypoint grup sayısı", "value": len(keypoint_groups), "unit": "adet"},
        {"key": "keypoint_count", "labelTR": "Toplam keypoint sayısı", "value": point_count, "unit": "adet"},
        {"key": "mask_count", "labelTR": "Segmentasyon maskesi sayısı", "value": len(masks), "unit": "adet"},
    ]
    if keypoint_groups:
        measurements.extend(_keypoint_span_measurements(keypoint_groups))
    ready = point_count >= 2 or bool(masks)
    return {
        "name": "scoliosis_alignment_measurement",
        "status": "ready_for_alignment" if ready else "insufficient_output",
        "summaryTR": "Skolyoz hizalanma ölçümü için nokta/segmentasyon çıktısı hazır." if ready else "Skolyoz ölçümü için yeterli keypoint veya vertebra segmentasyonu bulunamadı.",
        "measurements": measurements,
        "warningsTR": [
            "Cobb açısı üretimi için vertebra seviye eşleştirme ve uç plak çizgisi postprocess algoritması gerekir.",
            "Hasta pozisyonu, rotasyon ve görüntü kalitesi ölçümü etkiler.",
        ],
    }


def kellgren_lawrence_grade_summary(model: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    classifications = result.get("classifications") or []
    best = max(classifications, key=lambda item: item.get("confidence") or 0, default=None)
    measurements: list[dict[str, Any]] = []
    summary = "Kellgren-Lawrence sınıflaması için sınıflama çıktısı bulunamadı."
    status = "insufficient_output"
    if best:
        confidence = float(best.get("confidence") or 0)
        label = str(best.get("label") or "Bilinmeyen")
        measurements.append({"key": "predicted_grade", "labelTR": "Tahmini KL sınıfı", "value": label, "unit": "sınıf"})
        measurements.append({"key": "confidence", "labelTR": "Model güveni", "value": round(confidence, 4), "unit": "oran"})
        summary = f"En olası Kellgren-Lawrence sınıfı: {label} (%{round(confidence * 100, 1)})."
        status = "ready_for_review"
    return {
        "name": "kellgren_lawrence_grade_summary",
        "status": status,
        "summaryTR": summary,
        "measurements": measurements,
        "warningsTR": [
            "KL evresi hasta semptomları, ayakta basarak grafi ve hekim değerlendirmesi ile birlikte yorumlanmalıdır.",
            "Model sınıflaması tek başına tedavi kararı için kullanılmamalıdır.",
        ],
    }


def _label_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        label = str(item.get("label") or "unknown")
        counts[label] = counts.get(label, 0) + 1
    return counts


def _mask_area_measurements(masks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    measurements: list[dict[str, Any]] = []
    for index, mask in enumerate(masks, start=1):
        polygon = mask.get("polygonXY") or []
        area = _polygon_area(polygon)
        measurements.append({
            "key": f"mask_{index}_area_px2",
            "labelTR": f"Maske {index} yaklaşık alanı",
            "value": round(area, 2),
            "unit": "px²",
        })
    return measurements


def _keypoint_span_measurements(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    measurements: list[dict[str, Any]] = []
    for index, group in enumerate(groups, start=1):
        points = group.get("points") or []
        xs = [float(point["x"]) for point in points if _has_xy(point)]
        ys = [float(point["y"]) for point in points if _has_xy(point)]
        if not xs or not ys:
            continue
        measurements.append({"key": f"keypoint_group_{index}_width_px", "labelTR": f"Keypoint grup {index} genişliği", "value": round(max(xs) - min(xs), 2), "unit": "px"})
        measurements.append({"key": f"keypoint_group_{index}_height_px", "labelTR": f"Keypoint grup {index} yüksekliği", "value": round(max(ys) - min(ys), 2), "unit": "px"})
        if len(xs) >= 2:
            measurements.append({"key": f"keypoint_group_{index}_rough_slope_deg", "labelTR": f"Keypoint grup {index} kaba eğim", "value": round(_rough_slope_degrees(xs, ys), 2), "unit": "derece"})
    return measurements


def _polygon_area(points: list[list[float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        area += float(point[0]) * float(next_point[1])
        area -= float(next_point[0]) * float(point[1])
    return abs(area) / 2.0


def _has_xy(point: dict[str, Any]) -> bool:
    try:
        float(point["x"])
        float(point["y"])
        return True
    except Exception:
        return False


def _rough_slope_degrees(xs: list[float], ys: list[float]) -> float:
    dx = xs[-1] - xs[0]
    dy = ys[-1] - ys[0]
    if dx == 0:
        return 90.0
    return math.degrees(math.atan2(dy, dx))

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import settings


TASK_CLASSIFICATION = "classification"
TASK_DETECTION = "detection"
TASK_SEGMENTATION = "segmentation"
TASK_KEYPOINT = "keypoint"
TASK_UNKNOWN = "unknown"


def _p(*parts: str) -> str:
    return str(settings.model_base_dir.joinpath(*parts))


MODEL_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "Dental": [
        {"name": "Dental Clinical - Pathologies", "id": "dental_clinical", "path": _p("Dental", "Dental Clinical", "DentalClinical.pt"), "modality": "Clinical dental photo"},
        {"name": "Dental X-Ray - Pathologies", "id": "dental_xray_pathologies", "path": _p("Dental", "Dental X-Ray", "Dental X-Ray Pathologies.pt"), "modality": "Dental X-ray"},
    ],
    "Dermatology": [
        {"name": "Eczema Detector", "id": "eczema", "path": _p("Dermatology", "Eczema", "eczema.pt"), "modality": "Clinical skin photo"},
        {"name": "Melanoma Detector", "id": "melanoma", "path": _p("Dermatology", "Melanoma", "melanom.pt"), "modality": "Clinical skin photo"},
        {"name": "Vitiligo Detector", "id": "vitiligo", "path": _p("Dermatology", "Vitiligo", "vitiligo.pt"), "modality": "Clinical skin photo"},
    ],
    "Medical Aesthetic": [
        {"name": "Acne Detector", "id": "acne", "path": _p("Medical Aesthetic", "Acne", "Acne.pt"), "modality": "Facial clinical photo"},
        {"name": "Blackheads Detector", "id": "blackheads", "path": _p("Medical Aesthetic", "Blackheads", "Blackheads.pt"), "modality": "Facial clinical photo"},
        {"name": "Dark Circles Detector", "id": "dark_circles", "path": _p("Medical Aesthetic", "Dark Circles", "Dark Circles.pt"), "modality": "Facial clinical photo"},
        {"name": "Pigmentation Detector", "id": "pigmentation", "path": _p("Medical Aesthetic", "Pigmentation", "Pigmentation.pt"), "modality": "Facial clinical photo"},
        {"name": "Pores Detector", "id": "pores", "path": _p("Medical Aesthetic", "Pores", "pore.pt"), "modality": "Facial clinical photo"},
        {"name": "Redness Detector", "id": "redness", "path": _p("Medical Aesthetic", "Redness", "redness.pt"), "modality": "Facial clinical photo"},
        {"name": "Wrinkles Detector", "id": "wrinkles", "path": _p("Medical Aesthetic", "Wrinkles", "Wrinkles.pt"), "modality": "Facial clinical photo"},
    ],
    "Orthopaedics & Traumatology": [
        {"name": "ACL Detection - Sagittal MRI", "id": "acl", "path": _p("Orthopaedics and Traumatology", "ACL Detection Sagittal MRI", "acl-detector.pt"), "modality": "Sagittal knee MRI"},
        {"name": "BML & Cyst - Sagittal Knee MRI", "id": "bml_cyst", "path": _p("Orthopaedics and Traumatology", "BML & Cyst - Saggital Knee MRI", "BML-Cyst.pt"), "modality": "Sagittal knee MRI"},
        {"name": "Bone CA Detector", "id": "bone_ca", "path": _p("Orthopaedics and Traumatology", "Bone CA", "BoneCA.pt"), "modality": "X-ray / CT"},
        {"name": "Bone-K-wire Cast Detector", "id": "bone_kwire", "path": _p("Orthopaedics and Traumatology", "Bone-Kwire-Cast", "BoneKwire.pt"), "modality": "X-ray"},
        {"name": "Canal Stenosis - Lumbar Sagittal MRI", "id": "canal_stenosis", "path": _p("Orthopaedics and Traumatology", "Canal Stenosis - Lumbar MRI Saggital", "canalstenosis.pt"), "modality": "Lumbar sagittal MRI"},
        {"name": "Canal Stenosis - Lumbar Sagittal MRI (ONNX)", "id": "canal_stenosis_onnx", "path": _p("Orthopaedics and Traumatology", "Canal Stenosis - Lumbar MRI Saggital", "canalstenosis.onnx"), "modality": "Lumbar sagittal MRI", "requiresCustomParser": True},
        {"name": "General Fracture Detector - X-Ray", "id": "fracture_general", "path": _p("Orthopaedics and Traumatology", "Fracture - Xray, General", "fracture.pt"), "modality": "X-ray"},
        {"name": "Gonarthrosis - Kellgren-Lawrence", "id": "knee_oa", "path": _p("Orthopaedics and Traumatology", "Gonarthrosis - Kelgreen Lawrance", "knee.pt"), "modality": "Knee X-ray", "taskType": TASK_CLASSIFICATION, "outputTypes": ["classifications"]},
        {"name": "Hand Bones - AP X-Ray", "id": "hand_bones", "path": _p("Orthopaedics and Traumatology", "Hand Bones - AP Xray", "HandBones.pt"), "modality": "Hand AP X-ray"},
        {"name": "Hand Fractures Detector", "id": "hand_fractures", "path": _p("Orthopaedics and Traumatology", "Hand Fractures", "Hand Fractures.pt"), "modality": "Hand X-ray"},
        {"name": "Hernia - Lumbar Sagittal MRI", "id": "hernia", "path": _p("Orthopaedics and Traumatology", "Hernia - Lumbar Saggital MRI", "hernia.pt"), "modality": "Lumbar sagittal MRI"},
        {"name": "Pelvis Sections Detector", "id": "pelvis_sections", "path": _p("Orthopaedics and Traumatology", "Pelvis", "Pelvis Sections.pt"), "modality": "Pelvis X-ray"},
        {"name": "Proximal Femoral - Pelvis AP", "id": "prox_femur", "path": _p("Orthopaedics and Traumatology", "Proximal Femoral Area - Pelvis AP", "Proximal Femoral Fractures.pt"), "modality": "Pelvis AP X-ray"},
        {"name": "Rotator Cuff Tear Detection - Shoulder MRI", "id": "rotator_cuff_tear", "path": _p("Orthopaedics and Traumatology", "Rotator Cuff Tear - MRI", "RotatorCuff.pt"), "modality": "Shoulder MRI"},
        {"name": "Scoliosis - Basic Vertebrae", "id": "scoliosis_basic", "path": _p("Orthopaedics and Traumatology", "Scoliosis", "Basic Vertebrae", "Basic Vertebrae.pt"), "modality": "Spine X-ray"},
        {"name": "Scoliosis Keypoints", "id": "scoliosis_keypoints", "path": _p("Orthopaedics and Traumatology", "Scoliosis", "Scoliosis Keypoints", "ScoliosisKeypoints.pt"), "modality": "Spine X-ray", "taskType": TASK_KEYPOINT, "outputTypes": ["keypoints"]},
        {"name": "Scoliosis - Back Pose", "id": "scoliosis_backpose", "path": _p("Orthopaedics and Traumatology", "Scoliosis - Back Pose", "BackPose.pt"), "modality": "Back photo", "taskType": TASK_KEYPOINT, "outputTypes": ["keypoints"]},
        {"name": "Shoulder Anatomy - AP X-Ray", "id": "shoulder", "path": _p("Orthopaedics and Traumatology", "Shoulder Anatomy - AP Xray", "Shoulder.pt"), "modality": "Shoulder AP X-ray"},
        {"name": "Subchondral Sclerosis - Coronal Knee MRI", "id": "subchondral_sclerosis", "path": _p("Orthopaedics and Traumatology", "Subcondral Sclerosis - Coronal Knee MRI", "Subcondral Sclerosis.pt"), "modality": "Coronal knee MRI"},
        {"name": "Supracondylar Humerus - AP X-Ray", "id": "supracondylar", "path": _p("Orthopaedics and Traumatology", "Supracondylar Humerus - AP Xray", "k-teli.pt"), "modality": "Elbow AP X-ray", "taskType": TASK_SEGMENTATION, "outputTypes": ["masks", "detections"], "postprocess": "supracondylar_pin_geometry"},
        {"name": "Tibia Fractures Detector", "id": "tibia_fractures", "path": _p("Orthopaedics and Traumatology", "Tibia Fractures", "Tibia Fractures.pt"), "modality": "Tibia X-ray"},
        {"name": "Ulna Fracture - Detailed", "id": "ulna_detailed", "path": _p("Orthopaedics and Traumatology", "Ulna Fracture - Xray", "Detailed", "UlnaFractures.pt"), "modality": "Ulna X-ray"},
        {"name": "Ulna Fracture - Simple", "id": "ulna_simple", "path": _p("Orthopaedics and Traumatology", "Ulna Fracture - Xray", "Simple", "UlnaFracture.pt"), "modality": "Ulna X-ray"},
    ],
    "Others": [
        {"name": "Brain MRI - Tumor Detector", "id": "brain_tumor", "path": _p("Others", "Brain MRI - Tumor", "brain.pt"), "modality": "Brain MRI"},
        {"name": "Chest X-Ray - Detailed Findings", "id": "chest_xray_detailed", "path": _p("Others", "Chest X-Ray Detailed", "ChestXray.pt"), "modality": "Chest X-ray", "force_task": "detect"},
        {"name": "Pneumonia - Chest AP X-Ray", "id": "pneumonia", "path": _p("Others", "Pneumonia - Chest AP Xray", "pneumonia.pt"), "modality": "Chest AP X-ray"},
        {"name": "Spinal Endoscopy - Instrument/Anatomy", "id": "spinal_endoscopy", "path": _p("Others", "Spinal Endoscopy", "SpineEndoscope.pt"), "modality": "Endoscopy image/frame", "force_task": "detect"},
    ],
    "Veterinary": [
        {"name": "Dog Spinal Anomalies", "id": "dog_spinal_anomalies", "path": _p("Veterinary", "Dog Spinal Anomalies", "SpinalAnomalies.pt"), "modality": "Veterinary imaging", "force_task": "detect"},
        {"name": "Dog X-Ray - Pathologies", "id": "dog_xray_pathologies", "path": _p("Veterinary", "Dog X-Ray Pathologies", "DogX-Ray.pt"), "modality": "Veterinary X-ray", "force_task": "detect"},
    ],
}


def flatten_models() -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for domain, items in MODEL_REGISTRY.items():
        for item in items:
            models.append(_enrich_model(domain, item))
    return models


def find_model(model_id: str) -> dict[str, Any] | None:
    for model in flatten_models():
        if model["id"] == model_id:
            return model
    return None


def registry_summary() -> dict[str, Any]:
    models = flatten_models()
    task_counts: dict[str, int] = {}
    output_counts: dict[str, int] = {}
    for model in models:
        task_counts[model["taskType"]] = task_counts.get(model["taskType"], 0) + 1
        for output_type in model.get("outputTypes", []):
            output_counts[output_type] = output_counts.get(output_type, 0) + 1
    return {
        "domains": list(MODEL_REGISTRY.keys()),
        "totalModels": len(models),
        "availableModels": sum(1 for model in models if model["exists"]),
        "missingModels": [model for model in models if not model["exists"]],
        "taskCounts": task_counts,
        "outputCounts": output_counts,
    }


def _enrich_model(domain: str, item: dict[str, Any]) -> dict[str, Any]:
    path = Path(item["path"])
    task_type = item.get("taskType") or _infer_task_type(item)
    output_types = item.get("outputTypes") or _output_types_for_task(task_type)
    return {
        **item,
        "domain": domain,
        "exists": path.exists(),
        "extension": path.suffix.lower(),
        "taskType": task_type,
        "outputTypes": output_types,
        "requiresCustomParser": bool(item.get("requiresCustomParser") or path.suffix.lower() == ".onnx"),
        "postprocess": item.get("postprocess") or _infer_postprocess(item),
        "clinicalUseTR": item.get("clinicalUseTR") or _clinical_use_text(domain, item, task_type),
        "inputRequirementsTR": item.get("inputRequirementsTR") or _input_requirements(item),
        "safetyNoteTR": item.get("safetyNoteTR") or _safety_note(domain, item),
    }


def _infer_task_type(item: dict[str, Any]) -> str:
    text = f"{item.get('id', '')} {item.get('name', '')} {item.get('modality', '')}".lower()
    if "keypoint" in text or "pose" in text:
        return TASK_KEYPOINT
    if any(token in text for token in ["section", "anatomy", "bones", "vertebrae", "supracondylar"]):
        return TASK_SEGMENTATION
    if any(token in text for token in ["gonarthrosis", "kellgren", "classification", "grade"]):
        return TASK_CLASSIFICATION
    if any(token in text for token in ["detector", "detection", "fracture", "patholog", "tumor", "pneumonia", "kwire", "instrument"]):
        return TASK_DETECTION
    return TASK_DETECTION


def _output_types_for_task(task_type: str) -> list[str]:
    if task_type == TASK_CLASSIFICATION:
        return ["classifications"]
    if task_type == TASK_SEGMENTATION:
        return ["masks", "detections"]
    if task_type == TASK_KEYPOINT:
        return ["keypoints"]
    if task_type == TASK_DETECTION:
        return ["detections"]
    return []


def _infer_postprocess(item: dict[str, Any]) -> str | None:
    model_id = str(item.get("id", "")).lower()
    if model_id == "supracondylar":
        return "supracondylar_pin_geometry"
    if "scoliosis" in model_id:
        return "scoliosis_alignment_measurement"
    if model_id == "knee_oa":
        return "kellgren_lawrence_grade_summary"
    return None


def _clinical_use_text(domain: str, item: dict[str, Any], task_type: str) -> str:
    modality = item.get("modality") or "görüntü"
    if task_type == TASK_CLASSIFICATION:
        return f"{modality} üzerinden sınıflama/evreleme desteği sağlar. Tek başına tanı amacıyla kullanılmamalıdır."
    if task_type == TASK_SEGMENTATION:
        return f"{modality} üzerinde anatomik veya patolojik alanları işaretleme/segmentasyon desteği sağlar."
    if task_type == TASK_KEYPOINT:
        return f"{modality} üzerinde anatomik nokta veya poz işaretleme desteği sağlar. Ölçüm üretimi için postprocess gerekebilir."
    return f"{modality} üzerinde olası bulgu veya nesne tespiti için karar destek çıktısı sağlar."


def _input_requirements(item: dict[str, Any]) -> str:
    modality = str(item.get("modality") or "görüntü")
    if "skin" in modality.lower() or "facial" in modality.lower() or "photo" in modality.lower():
        return "İyi ışıkta, odaklı, mümkünse tek bölgeyi içeren klinik fotoğraf kullanılmalıdır."
    if "x-ray" in modality.lower() or "xray" in modality.lower():
        return "Uygun projeksiyonlu, net ve mümkünse kırpılmamış röntgen görüntüsü kullanılmalıdır."
    if "mri" in modality.lower():
        return "Modelin eğitildiği düzleme uygun, net MRI kesiti kullanılmalıdır."
    return "Modelin eğitildiği görüntü tipine uygun, net ve artefaktsız dosya kullanılmalıdır."


def _safety_note(domain: str, item: dict[str, Any]) -> str:
    if domain in {"Dermatology", "Medical Aesthetic"}:
        return "Işık, açı, makyaj/kremler ve kamera kalitesi sonucu etkileyebilir; hekim değerlendirmesi gerekir."
    if "X-ray" in str(item.get("modality", "")) or "MRI" in str(item.get("modality", "")):
        return "Model çıktısı klinik muayene, radyolojik kalite ve uzman hekim yorumu ile birlikte değerlendirilmelidir."
    return "Bu model tıbbi karar destek amaçlıdır; nihai değerlendirme hekime aittir."

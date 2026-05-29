from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import settings


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
        {"name": "Canal Stenosis - Lumbar Sagittal MRI (ONNX)", "id": "canal_stenosis_onnx", "path": _p("Orthopaedics and Traumatology", "Canal Stenosis - Lumbar MRI Saggital", "canalstenosis.onnx"), "modality": "Lumbar sagittal MRI"},
        {"name": "General Fracture Detector - X-Ray", "id": "fracture_general", "path": _p("Orthopaedics and Traumatology", "Fracture - Xray, General", "fracture.pt"), "modality": "X-ray"},
        {"name": "Gonarthrosis - Kellgren-Lawrence", "id": "knee_oa", "path": _p("Orthopaedics and Traumatology", "Gonarthrosis - Kelgreen Lawrance", "knee.pt"), "modality": "Knee X-ray"},
        {"name": "Hand Bones - AP X-Ray", "id": "hand_bones", "path": _p("Orthopaedics and Traumatology", "Hand Bones - AP Xray", "HandBones.pt"), "modality": "Hand AP X-ray"},
        {"name": "Hand Fractures Detector", "id": "hand_fractures", "path": _p("Orthopaedics and Traumatology", "Hand Fractures", "Hand Fractures.pt"), "modality": "Hand X-ray"},
        {"name": "Hernia - Lumbar Sagittal MRI", "id": "hernia", "path": _p("Orthopaedics and Traumatology", "Hernia - Lumbar Saggital MRI", "hernia.pt"), "modality": "Lumbar sagittal MRI"},
        {"name": "Pelvis Sections Detector", "id": "pelvis_sections", "path": _p("Orthopaedics and Traumatology", "Pelvis", "Pelvis Sections.pt"), "modality": "Pelvis X-ray"},
        {"name": "Proximal Femoral - Pelvis AP", "id": "prox_femur", "path": _p("Orthopaedics and Traumatology", "Proximal Femoral Area - Pelvis AP", "Proximal Femoral Fractures.pt"), "modality": "Pelvis AP X-ray"},
        {"name": "Rotator Cuff Tear Detection - Shoulder MRI", "id": "rotator_cuff_tear", "path": _p("Orthopaedics and Traumatology", "Rotator Cuff Tear - MRI", "RotatorCuff.pt"), "modality": "Shoulder MRI"},
        {"name": "Scoliosis - Basic Vertebrae", "id": "scoliosis_basic", "path": _p("Orthopaedics and Traumatology", "Scoliosis", "Basic Vertebrae", "Basic Vertebrae.pt"), "modality": "Spine X-ray"},
        {"name": "Scoliosis Keypoints", "id": "scoliosis_keypoints", "path": _p("Orthopaedics and Traumatology", "Scoliosis", "Scoliosis Keypoints", "ScoliosisKeypoints.pt"), "modality": "Spine X-ray"},
        {"name": "Scoliosis - Back Pose", "id": "scoliosis_backpose", "path": _p("Orthopaedics and Traumatology", "Scoliosis - Back Pose", "BackPose.pt"), "modality": "Back photo"},
        {"name": "Shoulder Anatomy - AP X-Ray", "id": "shoulder", "path": _p("Orthopaedics and Traumatology", "Shoulder Anatomy - AP Xray", "Shoulder.pt"), "modality": "Shoulder AP X-ray"},
        {"name": "Subchondral Sclerosis - Coronal Knee MRI", "id": "subchondral_sclerosis", "path": _p("Orthopaedics and Traumatology", "Subcondral Sclerosis - Coronal Knee MRI", "Subcondral Sclerosis.pt"), "modality": "Coronal knee MRI"},
        {"name": "Supracondylar Humerus - AP X-Ray", "id": "supracondylar", "path": _p("Orthopaedics and Traumatology", "Supracondylar Humerus - AP Xray", "k-teli.pt"), "modality": "Elbow AP X-ray"},
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
            path = Path(item["path"])
            models.append({**item, "domain": domain, "exists": path.exists(), "extension": path.suffix.lower()})
    return models


def find_model(model_id: str) -> dict[str, Any] | None:
    for model in flatten_models():
        if model["id"] == model_id:
            return model
    return None


def registry_summary() -> dict[str, Any]:
    models = flatten_models()
    return {
        "domains": list(MODEL_REGISTRY.keys()),
        "totalModels": len(models),
        "availableModels": sum(1 for model in models if model["exists"]),
        "missingModels": [model for model in models if not model["exists"]],
    }

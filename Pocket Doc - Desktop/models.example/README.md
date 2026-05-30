# Pocket Doc Desktop Model Files

This folder is documentation only. Real model weights should not be committed to the Git repository.

Large files such as `.pt`, `.onnx`, `.pth`, `.engine`, `.hef`, `.tflite`, `.mlmodel`, and `.safetensors` are intentionally ignored by `.gitignore`.

## Recommended setup

Keep model files outside the repository, then point the app to that folder with `POCKETDOC_MODEL_BASE_DIR`.

Example on macOS:

```bash
export POCKETDOC_MODEL_BASE_DIR="/Users/avnitan/PycharmProjects/TestProject/PocketDoc/Modeller"
```

Example on Raspberry Pi:

```bash
export POCKETDOC_MODEL_BASE_DIR="/home/pi/PocketDoc/Modeller"
```

Or set it in `.env`:

```env
POCKETDOC_MODEL_BASE_DIR=/home/pi/PocketDoc/Modeller
POCKETDOC_INFERENCE_BACKEND=ultralytics
```

## Expected folder structure

The model registry expects a folder like this:

```text
Modeller/
├── Dental/
│   ├── Dental Clinical/
│   │   └── DentalClinical.pt
│   └── Dental X-Ray/
│       └── Dental X-Ray Pathologies.pt
├── Dermatology/
│   ├── Eczema/
│   │   └── eczema.pt
│   ├── Melanoma/
│   │   └── melanom.pt
│   └── Vitiligo/
│       └── vitiligo.pt
├── Medical Aesthetic/
│   ├── Acne/
│   │   └── Acne.pt
│   ├── Blackheads/
│   │   └── Blackheads.pt
│   ├── Dark Circles/
│   │   └── Dark Circles.pt
│   ├── Pigmentation/
│   │   └── Pigmentation.pt
│   ├── Pores/
│   │   └── pore.pt
│   ├── Redness/
│   │   └── redness.pt
│   └── Wrinkles/
│       └── Wrinkles.pt
├── Orthopaedics and Traumatology/
│   ├── ACL Detection Sagittal MRI/
│   │   └── acl-detector.pt
│   ├── BML & Cyst - Saggital Knee MRI/
│   │   └── BML-Cyst.pt
│   ├── Bone CA/
│   │   └── BoneCA.pt
│   ├── Bone-Kwire-Cast/
│   │   └── BoneKwire.pt
│   ├── Canal Stenosis - Lumbar MRI Saggital/
│   │   ├── canalstenosis.pt
│   │   └── canalstenosis.onnx
│   ├── Fracture - Xray, General/
│   │   └── fracture.pt
│   ├── Gonarthrosis - Kelgreen Lawrance/
│   │   └── knee.pt
│   ├── Hand Bones - AP Xray/
│   │   └── HandBones.pt
│   ├── Hand Fractures/
│   │   └── Hand Fractures.pt
│   ├── Hernia - Lumbar Saggital MRI/
│   │   └── hernia.pt
│   ├── Pelvis/
│   │   └── Pelvis Sections.pt
│   ├── Proximal Femoral Area - Pelvis AP/
│   │   └── Proximal Femoral Fractures.pt
│   ├── Rotator Cuff Tear - MRI/
│   │   └── RotatorCuff.pt
│   ├── Scoliosis/
│   │   ├── Basic Vertebrae/
│   │   │   └── Basic Vertebrae.pt
│   │   ├── Scoliosis Keypoints/
│   │   │   └── ScoliosisKeypoints.pt
│   │   └── Scoliosis - Back Pose/
│   │       └── BackPose.pt
│   ├── Shoulder Anatomy - AP Xray/
│   │   └── Shoulder.pt
│   ├── Subcondral Sclerosis - Coronal Knee MRI/
│   │   └── Subcondral Sclerosis.pt
│   ├── Supracondylar Humerus - AP Xray/
│   │   └── k-teli.pt
│   ├── Tibia Fractures/
│   │   └── Tibia Fractures.pt
│   └── Ulna Fracture - Xray/
│       ├── Detailed/
│       │   └── UlnaFractures.pt
│       └── Simple/
│           └── UlnaFracture.pt
├── Others/
│   ├── Brain MRI - Tumor/
│   │   └── brain.pt
│   ├── Chest X-Ray Detailed/
│   │   └── ChestXray.pt
│   ├── Pneumonia - Chest AP Xray/
│   │   └── pneumonia.pt
│   └── Spinal Endoscopy/
│       └── SpineEndoscope.pt
└── Veterinary/
    ├── Dog Spinal Anomalies/
    │   └── SpinalAnomalies.pt
    └── Dog X-Ray Pathologies/
        └── DogX-Ray.pt
```

## Optional class preview images

The original demo supports class preview images in each model folder. You can keep these next to the model file:

```text
Classes.png
New Classes.png
Classes.jpg
New Classes.jpg
Classes - 1.png
Classes - 2.png
```

These are small images and may be kept with the external model folder. If they become part of the product UI, serve them through a controlled backend endpoint rather than exposing the whole model directory as static files.

## Distribution options

Recommended options for model files:

1. GitHub Releases: upload a zipped `Modeller/` folder per version.
2. Git LFS: usable for smaller teams, but watch storage and bandwidth quotas.
3. External storage: S3, Google Drive, or Hugging Face, with a download script.

Do not put model weights directly into normal Git history.

## Quick check

After setting `POCKETDOC_MODEL_BASE_DIR`, start the backend and open:

```text
/api/models
```

Each model has an `exists` field. `true` means the file exists at the expected path.

# Pocket Doc - Desktop

Raspberry Pi 5 kiosk application for outpatient clinical work.

Target device:

- Raspberry Pi 5, 16 GB RAM
- Raspberry Pi AI HAT+ 26 TOPS
- Waveshare 4.3 inch HDMI LCD (B), 800x480 capacitive touch
- Pi Camera, optional USB camera, optional file upload
- Internet available in clinic

## Product Shape

Pocket Doc - Desktop is designed as one fullscreen clinical assistant:

- PatientSum: consultation recording, transcription, and clinical summary
- Clinical Tools: calculators, red flags, documentation helpers, terminology adapters
- Imaging AI: model registry, image capture/upload, local or hybrid inference
- Report: doctor-approved visit snapshot with transcript, tools, imaging results, notes

## Architecture

```text
Raspberry Pi
├─ Chromium kiosk frontend
│  └─ 800x480 touch-first UI
├─ Python FastAPI backend
│  ├─ Patient session store
│  ├─ PatientSum service
│  ├─ Clinical tools adapter
│  ├─ Imaging AI adapter
│  └─ Report/export service
└─ Optional accelerators/services
   ├─ Hailo AI HAT+ runtime
   ├─ Ultralytics/ONNX fallback
   └─ Remote inference endpoint
```

## First Run

Create a virtual environment, install dependencies, then start the backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.pocketdoc_desktop.app:app --host 0.0.0.0 --port 8765 --reload
```

Open:

```text
http://localhost:8765
```

On the Raspberry Pi, Chromium should later be launched in kiosk mode against that URL.

## Current Milestone

This repo currently contains the first usable product shell:

- Working 800x480 web UI shell
- Simple doctor-facing home screen with three choices: PatientSum, Clinical Tools, AI Models
- In-memory patient session API
- Clinical tools module embedded from the full `ClinicalTools.py` HTML engine, with 976 calculators visible and working
- AI model registry adapted from the existing Cep Doktorum demo
- Mock imaging analysis endpoint ready to be replaced by local/Hailo/hybrid inference
- PatientSum browser audio recording flow and backend Whisper transcription endpoint
- OpenAI summary endpoint with local fallback when `OPENAI_API_KEY` is not configured

The next milestone is to connect Pi Camera/USB camera capture and selected imaging model inference.

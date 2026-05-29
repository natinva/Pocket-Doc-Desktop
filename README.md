# Pocket Doc Desktop

Pocket Doc Desktop is a Raspberry Pi based kiosk application for outpatient clinical work. The first target device is a Raspberry Pi 5 with a small touch display, optional camera input, and optional AI acceleration.

## Current MVP Goal

This first repository milestone focuses on a stable, runnable product shell:

- FastAPI backend
- 800x480 touch-first kiosk frontend
- SQLite-backed patient session store
- PatientSum placeholder flow: transcript to clinical summary
- Clinical tools placeholder registry
- Imaging AI placeholder registry and mock analysis
- Clear local development commands

## Target Hardware

- Raspberry Pi 5
- Raspberry Pi AI HAT+ 26 TOPS, planned
- Waveshare 4.3 inch HDMI LCD, 800x480 capacitive touch
- Pi Camera or USB camera, planned
- Chromium kiosk mode

## Project Structure

```text
backend/
  pocketdoc_desktop/
    app.py              FastAPI application
    config.py           Runtime settings
    session_store.py    SQLite patient session store
    patientsum.py       Transcript and summary service placeholder
    clinical_tools.py   Clinical tools registry placeholder
    imaging.py          Imaging registry and mock analysis
frontend/
  index.html            Touch-first kiosk UI
scripts/
  run_dev.sh            Local development runner
  run_kiosk.sh          Raspberry Pi Chromium kiosk launcher
runtime/                Local runtime data, ignored by git
```

## First Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.pocketdoc_desktop.app:app --host 0.0.0.0 --port 8765 --reload
```

Open:

```text
http://localhost:8765
```

## Raspberry Pi Kiosk Launch

After the backend is running locally:

```bash
bash scripts/run_kiosk.sh
```

## Product Direction

Pocket Doc Desktop should become a single-purpose clinical assistant device:

1. Start a patient session
2. Record or paste consultation transcript
3. Generate a structured doctor-facing summary
4. Run selected clinical tools
5. Capture or upload images for selected AI models
6. Export a doctor-approved visit snapshot

This repository intentionally starts with safe placeholders for AI and imaging. Real model inference should be added after the device workflow is stable.

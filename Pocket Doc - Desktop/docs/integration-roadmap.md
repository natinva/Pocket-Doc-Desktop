# Integration Roadmap

## Milestone 1: Kiosk Scaffold

- Single app shell
- 800x480 touch UI
- Patient session state
- Clinical tools dynamic forms
- Model registry
- Mock imaging
- PatientSum summary fallback

## Milestone 2: Real PatientSum

- Browser or backend audio recording
- Whisper/OpenAI transcription
- Turkish-first structured summaries
- Doctor correction workflow
- Consent and retention settings

## Milestone 3: Clinical Tools Completion

- Embed and harmonize the full `ClinicalTools.py` set
- Parse all 976 tools into the backend catalog
- Keep `basic/pro/elite` metadata
- Mark licensed/high-risk tools visibly
- Add result provenance and formula versions
- Add automatic tool suggestions from transcript and imaging results

## Milestone 4: Imaging AI

- Fix/validate model paths
- Add active-model-only loading
- Add Ultralytics/ONNX adapter
- Add Pi Camera and USB camera capture
- Benchmark Pi 5 CPU/GPU vs AI HAT+
- Convert selected models to Hailo where useful

## Milestone 5: Clinical Report

- Immutable final snapshot
- PDF export
- Patient education output
- Referral/discharge draft
- Doctor approval state

## Milestone 6: Clinic Hardening

- Offline-safe behavior
- Local SQLite persistence
- Encrypted backups
- Audit trail
- Kiosk auto-start
- Hardware health screen

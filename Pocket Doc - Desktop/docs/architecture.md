# Architecture

Pocket Doc - Desktop is a kiosk-style clinical assistant. The visible product is one app, but the internal modules stay separate so each can be optimized independently.

## Runtime Modules

## Frontend

- Static HTML/CSS/JavaScript
- Designed first for 800x480 touch
- Served by FastAPI
- No build step in the first milestone

## Backend

- FastAPI app
- In-memory session store for first milestone
- Later persistence target: SQLite on Pi, optional encrypted export/sync

## PatientSum

Current boundary:

- `PatientSumService.summarize_text()`
- Local draft fallback when `OPENAI_API_KEY` is not configured

Next:

- Browser or backend microphone capture
- OpenAI audio transcription
- Structured SOAP/plan output
- Consent and retention controls

## Clinical Tools

Current boundary:

- Full `ClinicalTools.py` HTML engine embedded in the product
- 976 visible tools parsed into the backend catalog
- Local backend execution for the small starter registry
- Embedded execution for the full calculator set

Next:

- Attach selected embedded-tool results to patient session records
- Keep licensed/integration-pending tools clearly marked if new external tools are added
- Add validation metadata and versioned formula references

## Imaging AI

Current boundary:

- Model registry adapted from `cepdoktorum_ai_demo.py`
- Upload endpoint
- Mock analysis output attached to patient session

Backend strategy:

- `mock`: development mode
- `ultralytics`: direct `.pt`/`.onnx` fallback
- `hailo`: AI HAT+ compiled model path
- `remote`: clinical workstation/server inference

Pi 5 + AI HAT+ makes local inference realistic, but each model must still be evaluated. Some existing `.pt` models may need ONNX/Hailo conversion.

## Patient Session

All modules write into one visit snapshot:

```text
Session
├─ patient
├─ transcript
├─ summary
├─ doctorNotes
├─ clinicalToolResults
├─ imagingResults
├─ warnings
└─ finalized
```

The final report should always be generated from this snapshot, not from live UI fields.

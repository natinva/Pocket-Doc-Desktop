from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .clinical_tools import clinical_tools_summary, list_clinical_tools, run_tool
from .config import PROJECT_ROOT, settings
from .imaging import flatten_models, registry_summary
from .patientsum import PatientSumService
from .session_store import SessionStore

FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Pocket Doc Desktop", version="0.1.0")
store = SessionStore()
patient_sum = PatientSumService()


class SessionCreateRequest(BaseModel):
    patient: dict[str, Any] = Field(default_factory=dict)


class TranscriptRequest(BaseModel):
    transcript: str


class SummaryRequest(BaseModel):
    language: str = "tr"


class ToolRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    return FileResponse(index_path)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "env": settings.env,
        "inferenceBackend": settings.inference_backend,
        "patientSumEnabled": patient_sum.enabled,
        "modelRegistry": registry_summary(),
        "clinicalTools": clinical_tools_summary(),
    }


@app.post("/api/sessions")
def create_session(body: SessionCreateRequest) -> dict[str, Any]:
    return store.create(body.patient)


@app.get("/api/sessions")
def list_sessions() -> list[dict[str, Any]]:
    return store.list()


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{session_id}/transcript")
def set_transcript(session_id: str, body: TranscriptRequest) -> dict[str, Any]:
    session = store.update(session_id, {"transcript": body.transcript})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{session_id}/summary")
def generate_summary(session_id: str, body: SummaryRequest) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = patient_sum.summarize_text(session.get("transcript", ""), language=body.language)
    updated = store.update(session_id, {"summary": result["summary"]})
    return {"session": updated, "result": result}


@app.get("/api/clinical-tools")
def get_clinical_tools() -> list[dict[str, Any]]:
    return list_clinical_tools()


@app.post("/api/sessions/{session_id}/clinical-tools/{tool_id}")
def run_clinical_tool(session_id: str, tool_id: str, body: ToolRunRequest) -> dict[str, Any]:
    if not store.get(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        result = run_tool(tool_id, body.inputs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session = store.append(session_id, "clinicalToolResults", result)
    return {"session": session, "result": result}


@app.get("/api/models")
def list_models() -> list[dict[str, Any]]:
    return flatten_models()


@app.get("/api/kiosk/config")
def kiosk_config() -> dict[str, Any]:
    return {
        "screen": {"width": 800, "height": 480, "touch": True},
        "recommendedBrowser": "chromium-browser --kiosk http://localhost:8765",
        "pi": {"model": "Raspberry Pi 5", "accelerator": "AI HAT+ 26 TOPS planned"},
    }

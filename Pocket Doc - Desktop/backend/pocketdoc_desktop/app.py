from __future__ import annotations

from hmac import compare_digest
from html import escape
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .clinical_tools import clinical_tools_summary, list_clinical_tools, run_tool
from .config import PROJECT_ROOT, settings
from .imaging import ImagingService
from .model_registry import flatten_models, registry_summary
from .patientsum import PatientSumService
from .session_store import SessionStore


FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Pocket Doc - Desktop", version="0.1.0")
store = SessionStore()
patient_sum = PatientSumService()
imaging = ImagingService()


class SessionCreateRequest(BaseModel):
    patient: dict[str, Any] = Field(default_factory=dict)


class SessionUpdateRequest(BaseModel):
    patient: dict[str, Any] | None = None
    doctorNotes: str | None = None
    warnings: list[str] | None = None
    finalized: bool | None = None
    archived: bool | None = None


class TranscriptRequest(BaseModel):
    transcript: str


class SummaryRequest(BaseModel):
    language: str = "tr"


class ToolRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


class VerifyPinRequest(BaseModel):
    pin: str = ""


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "env": settings.env,
        "inferenceBackend": settings.inference_backend,
        "patientSumEnabled": patient_sum.enabled,
        "modelRegistry": registry_summary(),
        "clinicalTools": clinical_tools_summary(),
        "security": security_status(),
    }


@app.get("/api/security/status")
def get_security_status() -> dict[str, Any]:
    return security_status()


@app.post("/api/security/verify-pin")
def verify_pin(body: VerifyPinRequest) -> dict[str, bool]:
    if not settings.device_pin:
        return {"ok": True}
    is_valid = compare_digest(str(body.pin), str(settings.device_pin))
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return {"ok": True}


@app.post("/api/sessions")
def create_session(body: SessionCreateRequest) -> dict[str, Any]:
    return store.create(body.patient)


@app.get("/api/sessions")
def list_sessions(
    query: str | None = None,
    status: str | None = None,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    return store.list(query=query, status=status, include_archived=include_archived)


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.patch("/api/sessions/{session_id}")
def update_session(session_id: str, body: SessionUpdateRequest) -> dict[str, Any]:
    patch = body.model_dump(exclude_none=True)
    session = store.update(session_id, patch)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{session_id}/archive")
def archive_session(session_id: str) -> dict[str, Any]:
    session = store.archive(session_id, archived=True)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{session_id}/restore")
def restore_session(session_id: str) -> dict[str, Any]:
    session = store.archive(session_id, archived=False)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str) -> dict[str, bool]:
    deleted = store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@app.get("/api/sessions/{session_id}/report-preview")
def report_preview(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": session, "report": build_report_preview(session)}


@app.get("/api/sessions/{session_id}/report.txt", response_class=PlainTextResponse)
def export_report_txt(session_id: str) -> PlainTextResponse:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    filename = f"pocketdoc-report-{session_id[:8]}.txt"
    return PlainTextResponse(
        build_report_preview(session),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/sessions/{session_id}/report.html", response_class=HTMLResponse)
def export_report_html(session_id: str) -> HTMLResponse:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    filename = f"pocketdoc-report-{session_id[:8]}.html"
    return HTMLResponse(
        build_report_html(session),
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


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


@app.post("/api/sessions/{session_id}/audio/transcribe")
async def transcribe_audio(session_id: str, language: str = "tr", file: UploadFile = File(...)) -> dict[str, Any]:
    if not store.get(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    content = await file.read()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    audio_path = settings.upload_dir / f"{session_id}-audio{suffix}"
    audio_path.write_bytes(content)
    result = patient_sum.transcribe_audio(audio_path, language=language)
    if result.get("transcript"):
        session = store.update(session_id, {"transcript": result["transcript"]})
    else:
        session = store.get(session_id)
    return {"session": session, "result": result}


@app.get("/api/clinical-tools")
def list_tools() -> list[dict[str, Any]]:
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


@app.post("/api/sessions/{session_id}/imaging/{model_id}")
async def analyze_image(session_id: str, model_id: str, file: UploadFile = File(...)) -> dict[str, Any]:
    if not store.get(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    content = await file.read()
    image_path = imaging.save_upload(content, file.filename or "image")
    try:
        result = imaging.analyze(model_id, image_path)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session = store.append(session_id, "imagingResults", result)
    return {"session": session, "result": result}


@app.get("/api/kiosk/config")
def kiosk_config() -> dict[str, Any]:
    return {
        "screen": {"width": 800, "height": 480, "touch": True},
        "recommendedBrowser": "chromium --kiosk http://localhost:8765",
        "pi": {"model": "Raspberry Pi 5", "ramGb": 16, "accelerator": "AI HAT+ 26 TOPS"},
        "security": security_status(),
    }


def security_status() -> dict[str, Any]:
    return {
        "pinEnabled": bool(settings.device_pin),
        "lockTimeoutSeconds": settings.device_lock_timeout_seconds,
        "localOnlyMode": settings.local_only_mode,
        "dataStorage": "local-sqlite",
        "noticeTR": "Hasta verisi bu cihazda lokal olarak saklanır. Klinik kullanımda KVKK ve kurum politikaları doğrultusunda hekim sorumluluğunda yönetilmelidir.",
    }


def build_report_preview(session: dict[str, Any]) -> str:
    patient = session.get("patient") or {}
    patient_line = " / ".join(
        item
        for item in [
            patient.get("displayName") or "Hasta adı belirtilmedi",
            patient.get("age") or "Yaş belirtilmedi",
            patient.get("sex") or "Cinsiyet belirtilmedi",
            patient.get("chiefComplaint") or "Ana şikayet belirtilmedi",
        ]
        if item
    )
    tool_count = len(session.get("clinicalToolResults") or [])
    imaging_count = len(session.get("imagingResults") or [])
    finalized = "Evet" if session.get("finalized") else "Hayır"
    archived = "Evet" if session.get("archived") else "Hayır"
    warnings = session.get("warnings") or []
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "Uyarı girilmedi."
    return (
        "POCKET DOC - KLİNİK GÖRÜŞME TASLAĞI\n\n"
        f"Hasta: {patient_line}\n"
        f"Oturum: {session.get('id')}\n"
        f"Final onay: {finalized}\n"
        f"Arşiv: {archived}\n\n"
        "AI / Klinik Özet:\n"
        f"{session.get('summary') or 'Henüz özet oluşturulmadı.'}\n\n"
        "Hekim Notu:\n"
        f"{session.get('doctorNotes') or 'Henüz hekim notu girilmedi.'}\n\n"
        "Uyarılar / Red Flag Notları:\n"
        f"{warning_text}\n\n"
        f"Klinik araç sonucu: {tool_count}\n"
        f"Görüntü analizi sonucu: {imaging_count}\n\n"
        "Not: Bu çıktı hekim tarafından kontrol edilmeden hasta raporu olarak kullanılmamalıdır."
    )


def build_report_html(session: dict[str, Any]) -> str:
    patient = session.get("patient") or {}
    patient_name = patient.get("displayName") or "Hasta adı belirtilmedi"
    patient_items = [
        ("Yaş", patient.get("age") or "Belirtilmedi"),
        ("Cinsiyet", patient.get("sex") or "Belirtilmedi"),
        ("Ana şikayet", patient.get("chiefComplaint") or "Belirtilmedi"),
        ("Oturum", session.get("id") or "-"),
        ("Final onay", "Evet" if session.get("finalized") else "Hayır"),
        ("Arşiv", "Evet" if session.get("archived") else "Hayır"),
    ]
    warnings = session.get("warnings") or []
    warning_html = "".join(f"<li>{escape(str(warning))}</li>" for warning in warnings) or "<li>Uyarı girilmedi.</li>"
    clinical_tools = session.get("clinicalToolResults") or []
    imaging_results = session.get("imagingResults") or []
    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pocket Doc Klinik Görüşme Taslağı</title>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #17211b; background: #ffffff; }}
    .report {{ max-width: 840px; margin: 0 auto; }}
    h1 {{ color: #0f766e; margin-bottom: 4px; }}
    h2 {{ color: #17211b; border-bottom: 1px solid #d9ded6; padding-bottom: 6px; margin-top: 24px; }}
    .muted {{ color: #647067; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }}
    .box {{ border: 1px solid #d9ded6; border-radius: 8px; padding: 12px; background: #fbfcfa; white-space: pre-wrap; }}
    .meta {{ border: 1px solid #d9ded6; border-radius: 8px; padding: 10px; }}
    .label {{ color: #647067; font-size: 12px; display: block; margin-bottom: 4px; }}
    .warning {{ border-left: 4px solid #b7791f; padding-left: 12px; }}
    @media print {{ body {{ margin: 16mm; }} .no-print {{ display: none; }} }}
  </style>
</head>
<body>
  <main class="report">
    <button class="no-print" onclick="window.print()">Yazdır / PDF Kaydet</button>
    <h1>Pocket Doc Klinik Görüşme Taslağı</h1>
    <p class="muted">Bu çıktı hekim tarafından kontrol edilmeden hasta raporu olarak kullanılmamalıdır.</p>
    <h2>{escape(str(patient_name))}</h2>
    <section class="grid">
      {''.join(f'<div class="meta"><span class="label">{escape(label)}</span>{escape(str(value))}</div>' for label, value in patient_items)}
    </section>
    <h2>AI / Klinik Özet</h2>
    <section class="box">{escape(session.get('summary') or 'Henüz özet oluşturulmadı.')}</section>
    <h2>Hekim Notu</h2>
    <section class="box">{escape(session.get('doctorNotes') or 'Henüz hekim notu girilmedi.')}</section>
    <h2>Uyarılar / Red Flag Notları</h2>
    <section class="box warning"><ul>{warning_html}</ul></section>
    <h2>Ek Sonuçlar</h2>
    <section class="grid">
      <div class="meta"><span class="label">Klinik araç sonucu</span>{len(clinical_tools)}</div>
      <div class="meta"><span class="label">Görüntü analizi sonucu</span>{len(imaging_results)}</div>
    </section>
  </main>
</body>
</html>"""

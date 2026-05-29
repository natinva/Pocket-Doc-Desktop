from __future__ import annotations

from pathlib import Path
from typing import Any


class PatientSumService:
    def __init__(self) -> None:
        self.enabled = True

    def summarize_text(self, transcript: str, language: str = "tr") -> dict[str, Any]:
        clean = " ".join((transcript or "").split())
        if not clean:
            summary = "Henüz özet oluşturmak için yeterli görüşme metni yok."
        else:
            preview = clean[:900]
            summary = (
                "Klinik Görüşme Özeti\n\n"
                "Ana görüşme metni kaydedildi. Bu MVP aşamasında özet, güvenli lokal şablon ile oluşturulmaktadır.\n\n"
                f"Görüşme notu: {preview}"
            )
        return {
            "language": language,
            "provider": "local-template",
            "summary": summary,
            "warning": "Bu çıktı klinik kararın yerine geçmez. Son karar hekimindir.",
        }

    def transcribe_audio(self, audio_path: Path, language: str = "tr") -> dict[str, Any]:
        return {
            "language": language,
            "provider": "placeholder",
            "transcript": "",
            "audioPath": str(audio_path),
            "warning": "Ses kaydı alındı. Gerçek Whisper/OpenAI transkripsiyon entegrasyonu sonraki aşamada eklenecek.",
        }

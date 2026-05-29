from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import settings


class PatientSumService:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key)

    def transcribe_audio(self, audio_path: Path, language: str = "tr") -> dict[str, Any]:
        if not self.enabled:
            return {
                "transcript": "",
                "mode": "missing_openai_key",
                "warning": "OPENAI_API_KEY yok; ses kaydı alındı fakat Whisper transkripsiyonu çalıştırılamadı.",
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            with audio_path.open("rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=audio_file,
                    model=settings.openai_transcribe_model,
                    response_format="text",
                    language=language,
                )
            transcript = response.strip() if isinstance(response, str) else str(response).strip()
            return {"transcript": transcript, "mode": "openai_whisper"}
        except Exception as exc:
            return {"transcript": "", "mode": "error", "warning": str(exc)}

    def summarize_text(self, transcript: str, language: str = "tr") -> dict[str, Any]:
        if not transcript.strip():
            return {"summary": "", "mode": "empty"}

        if not self.enabled:
            return {
                "summary": self._local_draft(transcript),
                "mode": "local_draft",
                "warning": "OPENAI_API_KEY yok; gerçek AI özeti yerine yerel taslak üretildi.",
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            system = (
                "Sen poliklinik ortamında çalışan, tıbbi notları yapılandıran yardımcı bir asistansın. "
                "Tanı koydurucu kesin dil kullanma. Türkçe ve kısa cevap ver."
                if language == "tr"
                else "You are a clinical documentation assistant. Keep the answer concise and avoid definitive diagnostic commands."
            )
            prompt = (
                "Aşağıdaki hasta görüşmesini poliklinik notuna dönüştür:\n"
                "1. Ana şikayet\n2. Kısa öykü\n3. Muayene/vital bulgu varsa\n"
                "4. Değerlendirme\n5. Plan/tetkik önerileri\n6. Red flag varsa belirt\n\n"
                f"Transkript:\n{transcript}"
            )
            response = client.chat.completions.create(
                model=settings.openai_summary_model,
                temperature=0.2,
                max_tokens=700,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            )
            return {"summary": response.choices[0].message.content or "", "mode": "openai"}
        except Exception as exc:
            return {"summary": self._local_draft(transcript), "mode": "fallback", "warning": str(exc)}

    def _local_draft(self, transcript: str) -> str:
        clipped = transcript.strip().replace("\n", " ")
        if len(clipped) > 420:
            clipped = clipped[:420].rstrip() + "..."
        return (
            "AI özet servisi yapılandırılmadı.\n\n"
            "Transkript taslağı:\n"
            f"{clipped}\n\n"
            "Doktor notu: Bu alan gerçek OpenAI bağlantısı etkinleşince SOAP/plan formatında otomatik üretilecek."
        )

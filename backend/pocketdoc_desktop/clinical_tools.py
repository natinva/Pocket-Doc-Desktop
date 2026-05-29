from __future__ import annotations

from typing import Any

DISCLAIMER_TR = "Bu çıktı klinik kararın yerine geçmez. Son karar hekimindir."

TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "bmi-bsa",
        "titleTR": "BMI / BSA / İdeal Kilo",
        "category": "calculator",
        "riskLevel": "low",
        "inputs": [
            {"key": "heightCm", "labelTR": "Boy (cm)", "type": "number", "required": True},
            {"key": "weightKg", "labelTR": "Kilo (kg)", "type": "number", "required": True},
        ],
    },
    {
        "id": "red-flags-basic",
        "titleTR": "Temel Klinik Red Flag Kontrolü",
        "category": "red-flag",
        "riskLevel": "moderate",
        "inputs": [
            {"key": "chestPain", "labelTR": "Göğüs ağrısı", "type": "boolean"},
            {"key": "dyspnea", "labelTR": "Nefes darlığı", "type": "boolean"},
            {"key": "neurologicDeficit", "labelTR": "Nörolojik defisit", "type": "boolean"},
            {"key": "highFever", "labelTR": "Yüksek ateş", "type": "boolean"},
        ],
    },
]


def clinical_tools_summary() -> dict[str, Any]:
    return {"count": len(TOOL_REGISTRY), "source": "mvp-registry"}


def list_clinical_tools() -> list[dict[str, Any]]:
    return TOOL_REGISTRY


def run_tool(tool_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    if tool_id == "bmi-bsa":
        height_cm = float(inputs.get("heightCm", 0))
        weight_kg = float(inputs.get("weightKg", 0))
        if height_cm <= 0 or weight_kg <= 0:
            raise ValueError("Boy ve kilo pozitif değer olmalıdır.")
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        bsa = ((height_cm * weight_kg) / 3600) ** 0.5
        return {
            "toolId": tool_id,
            "titleTR": "BMI / BSA / İdeal Kilo",
            "outputs": {"bmi": round(bmi, 2), "bsaMosteller": round(bsa, 2)},
            "interpretationTR": "BMI ve BSA hesaplandı. Klinik bağlam ile birlikte değerlendirilmelidir.",
            "disclaimerTR": DISCLAIMER_TR,
        }

    if tool_id == "red-flags-basic":
        positives = [key for key, value in inputs.items() if bool(value)]
        return {
            "toolId": tool_id,
            "titleTR": "Temel Klinik Red Flag Kontrolü",
            "outputs": {"positiveFlags": positives, "positiveCount": len(positives)},
            "interpretationTR": "Pozitif red flag varsa acil değerlendirme ve yerel protokoller önceliklidir.",
            "disclaimerTR": DISCLAIMER_TR,
        }

    raise KeyError(f"Bilinmeyen klinik araç: {tool_id}")

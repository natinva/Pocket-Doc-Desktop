from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any

from .config import PROJECT_ROOT
from .session_store import utc_now_iso


DISCLAIMER_TR = (
    "Bu çıktı klinik kararın yerine geçmez. Son karar hekimindir; acil/kritik durumda "
    "yerel acil protokoller uygulanmalıdır."
)


TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "bmi-bsa",
        "titleTR": "BMI / BSA / İdeal Kilo",
        "category": "calculator",
        "riskLevel": "low",
        "inputs": [
            {"key": "heightCm", "labelTR": "Boy (cm)", "type": "number", "required": True},
            {"key": "weightKg", "labelTR": "Kilo (kg)", "type": "number", "required": True},
            {"key": "sex", "labelTR": "Cinsiyet", "type": "select", "options": ["female", "male"]},
        ],
    },
    {
        "id": "egfr-crcl",
        "titleTR": "eGFR / Cockcroft-Gault / CrCl",
        "category": "calculator",
        "riskLevel": "moderate",
        "inputs": [
            {"key": "age", "labelTR": "Yaş", "type": "number", "required": True},
            {"key": "sex", "labelTR": "Cinsiyet", "type": "select", "required": True, "options": ["female", "male"]},
            {"key": "weightKg", "labelTR": "Kilo (kg)", "type": "number", "required": True},
            {"key": "creatinineMgDl", "labelTR": "Kreatinin (mg/dL)", "type": "number", "required": True},
        ],
    },
    {
        "id": "cha2ds2-hasbled",
        "titleTR": "CHA2DS2-VASc / HAS-BLED",
        "category": "calculator",
        "riskLevel": "low",
        "inputs": [
            {"key": "age", "labelTR": "Yaş", "type": "number", "required": True},
            {"key": "sex", "labelTR": "Cinsiyet", "type": "select", "required": True, "options": ["female", "male"]},
            {"key": "heartFailure", "labelTR": "Kalp yetmezliği", "type": "boolean"},
            {"key": "hypertension", "labelTR": "Hipertansiyon", "type": "boolean"},
            {"key": "diabetes", "labelTR": "Diyabet", "type": "boolean"},
            {"key": "strokeTia", "labelTR": "İnme/TIA", "type": "boolean"},
            {"key": "vascularDisease", "labelTR": "Vasküler hastalık", "type": "boolean"},
            {"key": "abnormalRenalLiver", "labelTR": "Renal/karaciğer bozukluğu", "type": "boolean"},
            {"key": "bleedingHistory", "labelTR": "Kanama öyküsü", "type": "boolean"},
            {"key": "labileInr", "labelTR": "Labil INR", "type": "boolean"},
            {"key": "drugsAlcohol", "labelTR": "İlaç/alkol riski", "type": "boolean"},
        ],
    },
    {
        "id": "wells-perc-ddimer",
        "titleTR": "Wells / PERC / Yaşa Göre D-dimer",
        "category": "calculator",
        "riskLevel": "low",
        "inputs": [
            {"key": "age", "labelTR": "Yaş", "type": "number", "required": True},
            {"key": "clinicalDvt", "labelTR": "DVT bulguları", "type": "boolean"},
            {"key": "peMostLikely", "labelTR": "PE en olası tanı", "type": "boolean"},
            {"key": "heartRateOver100", "labelTR": "Nabız >100", "type": "boolean"},
            {"key": "immobilizationOrSurgery", "labelTR": "İmmobilizasyon/cerrahi", "type": "boolean"},
            {"key": "previousVte", "labelTR": "Önceki VTE", "type": "boolean"},
            {"key": "hemoptysis", "labelTR": "Hemoptizi", "type": "boolean"},
            {"key": "malignancy", "labelTR": "Malignite", "type": "boolean"},
        ],
    },
    {
        "id": "curb65-crb65",
        "titleTR": "CURB-65 / CRB-65",
        "category": "calculator",
        "riskLevel": "low",
        "inputs": [
            {"key": "age", "labelTR": "Yaş", "type": "number", "required": True},
            {"key": "confusion", "labelTR": "Konfüzyon", "type": "boolean"},
            {"key": "ureaHigh", "labelTR": "Üre yüksek", "type": "boolean"},
            {"key": "rr30", "labelTR": "Solunum sayısı >=30", "type": "boolean"},
            {"key": "lowBp", "labelTR": "Düşük kan basıncı", "type": "boolean"},
        ],
    },
    {
        "id": "news2-qsofa",
        "titleTR": "NEWS2 / qSOFA Akut Kötüleşme",
        "category": "calculator",
        "riskLevel": "moderate",
        "inputs": [
            {"key": "rr", "labelTR": "Solunum sayısı", "type": "number", "required": True},
            {"key": "spo2", "labelTR": "SpO2", "type": "number", "required": True},
            {"key": "temperature", "labelTR": "Ateş", "type": "number", "required": True},
            {"key": "systolicBp", "labelTR": "Sistolik TA", "type": "number", "required": True},
            {"key": "heartRate", "labelTR": "Nabız", "type": "number", "required": True},
            {"key": "alteredMentalStatus", "labelTR": "Bilinç değişikliği", "type": "boolean"},
        ],
    },
    {
        "id": "pregnancy-dating-edd",
        "titleTR": "Gebelik Haftası / EDD",
        "category": "calculator",
        "riskLevel": "low",
        "inputs": [{"key": "lmp", "labelTR": "Son adet tarihi", "type": "date", "required": True}],
    },
    {
        "id": "red-flags",
        "titleTR": "Red Flag / Acil Yönlendirme",
        "category": "guideline",
        "riskLevel": "low",
        "inputs": [
            {"key": "complaint", "labelTR": "Ana şikayet", "type": "string", "required": True},
            {"key": "chestPain", "labelTR": "Göğüs ağrısı", "type": "boolean"},
            {"key": "dyspnea", "labelTR": "Nefes darlığı", "type": "boolean"},
            {"key": "neurologicDeficit", "labelTR": "Nörolojik defisit", "type": "boolean"},
            {"key": "severePain", "labelTR": "Şiddetli ağrı", "type": "boolean"},
            {"key": "syncope", "labelTR": "Senkop", "type": "boolean"},
        ],
    },
    {
        "id": "patient-education",
        "titleTR": "Hasta Bilgilendirme Metni",
        "category": "documentation",
        "riskLevel": "low",
        "inputs": [{"key": "topic", "labelTR": "Konu", "type": "string", "required": True}],
    },
    {
        "id": "referral-discharge-draft",
        "titleTR": "Sevk / Konsültasyon / Epikriz Taslağı",
        "category": "documentation",
        "riskLevel": "low",
        "inputs": [
            {"key": "complaint", "labelTR": "Şikayet", "type": "string", "required": True},
            {"key": "assessment", "labelTR": "Değerlendirme", "type": "string"},
            {"key": "plan", "labelTR": "Plan", "type": "string"},
        ],
    },
]


def _clean_js_string(value: str) -> str:
    return (
        value.replace(r"\"", '"')
        .replace(r"\'", "'")
        .replace(r"\n", " ")
        .replace(r"\\", "\\")
        .strip()
    )


def _extract_js_string(chunk: str, key: str) -> str:
    match = re.search(rf'{key}:"(?P<value>(?:\\.|[^"\\])*)"', chunk, re.DOTALL)
    if not match:
        return ""
    return _clean_js_string(match.group("value"))


def _extract_js_array_strings(chunk: str, key: str) -> list[str]:
    match = re.search(rf"{key}:\[(?P<value>[^\]]*)\]", chunk, re.DOTALL)
    if not match:
        return []
    return [_clean_js_string(item) for item in re.findall(r'"((?:\\.|[^"\\])*)"', match.group("value"))]


def _parse_qprofile_titles(html: str) -> dict[str, str]:
    pattern = re.compile(
        r'"(?P<id>[^"]+)":qProfile\(\{tr:"(?P<title>(?:\\.|[^"\\])*)"',
        re.DOTALL,
    )
    return {match.group("id"): _clean_js_string(match.group("title")) for match in pattern.finditer(html)}


@lru_cache(maxsize=1)
def _parse_full_html_catalog_cached() -> tuple[dict[str, Any], ...]:
    html_path = PROJECT_ROOT / "frontend" / "clinical_tools_full.html"
    if not html_path.exists():
        return tuple()
    html = html_path.read_text(encoding="utf-8")
    qprofile_titles = _parse_qprofile_titles(html)
    id_matches = list(re.finditer(r'\{\s*id:"(?P<id>[^"]+)"\s*,', html))
    seen: set[str] = set()
    catalog: list[dict[str, Any]] = []

    def add_tool(
        tool_id: str,
        title: str,
        description: str,
        category: str,
        tool_type: str,
        tags: list[str] | None = None,
        hot: bool = False,
    ) -> None:
        if tool_id in seen:
            return
        seen.add(tool_id)
        catalog.append(
            {
                "id": tool_id,
                "titleTR": title or qprofile_titles.get(tool_id, tool_id),
                "descriptionTR": description,
                "category": category or "Clinical Tools",
                "type": tool_type or "Araç",
                "tags": tags or [],
                "hot": hot,
                "riskLevel": "low",
                "implementationType": "embedded_html_formula",
                "source": "ClinicalTools.py embedded HTML",
                "inputs": [],
            }
        )

    for index, match in enumerate(id_matches):
        tool_id = match.group("id")
        if tool_id in seen:
            continue
        end = id_matches[index + 1].start() if index + 1 < len(id_matches) else len(html)
        chunk = html[match.start() : end]
        title = _extract_js_string(chunk, "title") or qprofile_titles.get(tool_id, tool_id)
        description = _extract_js_string(chunk, "description")
        category = _extract_js_string(chunk, "category") or "Clinical Tools"
        tool_type = _extract_js_string(chunk, "type") or "Araç"
        tags = _extract_js_array_strings(chunk, "tags")
        add_tool(tool_id, title, description, category, tool_type, tags, hot="hot:true" in chunk[:1200])

    guideline_pattern = re.compile(
        r'guidelineTool\("(?P<id>(?:\\.|[^"\\])*)",\s*"(?P<title>(?:\\.|[^"\\])*)",\s*"(?P<description>(?:\\.|[^"\\])*)",\s*"(?P<category>(?:\\.|[^"\\])*)",\s*\[(?P<tags>[^\]]*)\]',
        re.DOTALL,
    )
    for match in guideline_pattern.finditer(html):
        add_tool(
            _clean_js_string(match.group("id")),
            _clean_js_string(match.group("title")),
            _clean_js_string(match.group("description")),
            _clean_js_string(match.group("category")),
            "Klinik Kural",
            [_clean_js_string(item) for item in re.findall(r'"((?:\\.|[^"\\])*)"', match.group("tags"))],
        )

    rome_pattern = re.compile(
        r'romeDx\("(?P<id>(?:\\.|[^"\\])*)",\s*"(?P<title>(?:\\.|[^"\\])*)",\s*"(?P<description>(?:\\.|[^"\\])*)",\s*"(?P<age_group>(?:\\.|[^"\\])*)"',
        re.DOTALL,
    )
    for match in rome_pattern.finditer(html):
        age_group = _clean_js_string(match.group("age_group"))
        category = "İç Hastalıkları (Dahiliye)" if age_group == "adult" else "Çocuk Sağlığı ve Hastalıkları"
        add_tool(
            _clean_js_string(match.group("id")),
            _clean_js_string(match.group("title")),
            _clean_js_string(match.group("description")),
            category,
            "Tanı Desteği",
            ["Rome kriterleri", "Fonksiyonel GİS"],
        )
    return tuple(catalog)


def _parse_full_html_catalog() -> list[dict[str, Any]]:
    return [dict(tool) for tool in _parse_full_html_catalog_cached()]


def list_clinical_tools() -> list[dict[str, Any]]:
    full_catalog = _parse_full_html_catalog()
    if not full_catalog:
        return TOOL_REGISTRY

    local_by_id = {tool["id"]: tool for tool in TOOL_REGISTRY}
    merged: list[dict[str, Any]] = []
    for tool in full_catalog:
        local = local_by_id.get(tool["id"])
        if local:
            merged.append({**tool, **local, "implementationType": "embedded_html_formula_and_backend"})
        else:
            merged.append(tool)
    return merged


def clinical_tools_summary() -> dict[str, Any]:
    full_catalog = _parse_full_html_catalog()
    return {
        "totalTools": len(full_catalog) if full_catalog else len(TOOL_REGISTRY),
        "source": "ClinicalTools.py" if full_catalog else "Pocket Doc backend registry",
        "backendExecutableTools": len(TOOL_REGISTRY),
        "embeddedExecutableTools": len(full_catalog),
    }


def _num(inputs: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = inputs.get(key, default)
    if value in ("", None):
        return default
    return float(value)


def _bool(inputs: dict[str, Any], key: str) -> bool:
    return bool(inputs.get(key))


def _result(tool_id: str, summary: str, structured: dict[str, Any], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "toolId": tool_id,
        "resultSummaryTR": summary,
        "structuredResult": structured,
        "warningsTR": warnings or [],
        "sourceMetadata": [{"name": "Pocket Doc local rules/formulas", "type": "internal_protocol"}],
        "generatedAt": utc_now_iso(),
        "disclaimerTR": DISCLAIMER_TR,
    }


def run_tool(tool_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    if tool_id == "bmi-bsa":
        height_cm = _num(inputs, "heightCm")
        weight_kg = _num(inputs, "weightKg")
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        bsa = math.sqrt((height_cm * weight_kg) / 3600)
        ideal = None
        if inputs.get("sex") == "male":
            ideal = 50 + 0.9 * (height_cm - 152)
        elif inputs.get("sex") == "female":
            ideal = 45.5 + 0.9 * (height_cm - 152)
        return _result(
            tool_id,
            f"BMI {bmi:.1f} kg/m2, BSA {bsa:.2f} m2.",
            {"bmi": round(bmi, 1), "bsaMosteller": round(bsa, 2), "idealWeightKg": round(ideal, 1) if ideal else None},
        )

    if tool_id == "egfr-crcl":
        age = _num(inputs, "age")
        scr = _num(inputs, "creatinineMgDl")
        weight = _num(inputs, "weightKg")
        female = inputs.get("sex") == "female"
        crcl = ((140 - age) * weight) / (72 * scr)
        if female:
            crcl *= 0.85
        k = 0.7 if female else 0.9
        alpha = -0.241 if female else -0.302
        egfr = 142 * min(scr / k, 1) ** alpha * max(scr / k, 1) ** -1.2 * 0.9938 ** age
        if female:
            egfr *= 1.012
        return _result(
            tool_id,
            f"eGFR yaklaşık {egfr:.0f}, Cockcroft-Gault CrCl yaklaşık {crcl:.0f} mL/dk.",
            {"egfrCkdEpi2021": round(egfr), "crclCockcroftGault": round(crcl)},
            ["İlaç doz kararı için lokal protokol ve ilaç veri tabanı ile doğrulayın."],
        )

    if tool_id == "cha2ds2-hasbled":
        age = _num(inputs, "age")
        cha = 0
        cha += int(_bool(inputs, "heartFailure"))
        cha += int(_bool(inputs, "hypertension"))
        cha += 2 if age >= 75 else int(age >= 65)
        cha += int(_bool(inputs, "diabetes"))
        cha += 2 * int(_bool(inputs, "strokeTia"))
        cha += int(_bool(inputs, "vascularDisease"))
        cha += int(inputs.get("sex") == "female")
        hasbled = 0
        hasbled += int(_bool(inputs, "hypertension"))
        hasbled += int(_bool(inputs, "abnormalRenalLiver"))
        hasbled += int(_bool(inputs, "strokeTia"))
        hasbled += int(_bool(inputs, "bleedingHistory"))
        hasbled += int(_bool(inputs, "labileInr"))
        hasbled += int(age > 65)
        hasbled += int(_bool(inputs, "drugsAlcohol"))
        return _result(tool_id, f"CHA2DS2-VASc {cha}, HAS-BLED {hasbled}.", {"cha2ds2Vasc": cha, "hasBled": hasbled})

    if tool_id == "wells-perc-ddimer":
        age = _num(inputs, "age")
        wells = 0.0
        wells += 3 if _bool(inputs, "clinicalDvt") else 0
        wells += 3 if _bool(inputs, "peMostLikely") else 0
        wells += 1.5 if _bool(inputs, "heartRateOver100") else 0
        wells += 1.5 if _bool(inputs, "immobilizationOrSurgery") else 0
        wells += 1.5 if _bool(inputs, "previousVte") else 0
        wells += 1 if _bool(inputs, "hemoptysis") else 0
        wells += 1 if _bool(inputs, "malignancy") else 0
        adjusted_ddimer = age * 10 if age > 50 else 500
        return _result(
            tool_id,
            f"Wells PE skoru {wells:.1f}. Yaşa göre D-dimer eşiği yaklaşık {adjusted_ddimer:.0f} ng/mL FEU.",
            {"wellsPe": wells, "ageAdjustedDdimerNgMlFeu": adjusted_ddimer, "peLikely": wells > 4},
        )

    if tool_id == "curb65-crb65":
        age = _num(inputs, "age")
        crb = int(age >= 65) + int(_bool(inputs, "confusion")) + int(_bool(inputs, "rr30")) + int(_bool(inputs, "lowBp"))
        curb = crb + int(_bool(inputs, "ureaHigh"))
        return _result(tool_id, f"CRB-65 {crb}, CURB-65 {curb}.", {"crb65": crb, "curb65": curb})

    if tool_id == "news2-qsofa":
        rr = _num(inputs, "rr")
        sbp = _num(inputs, "systolicBp")
        altered = _bool(inputs, "alteredMentalStatus")
        qsofa = int(rr >= 22) + int(sbp <= 100) + int(altered)
        warnings = ["qSOFA 2 veya üzeriyse sepsis riski açısından acil klinik değerlendirme gerekir."] if qsofa >= 2 else []
        return _result(tool_id, f"qSOFA {qsofa}. NEWS2 ayrıntılı skorlama için vital eşik tablosu doğrulaması gerekir.", {"qsofa": qsofa}, warnings)

    if tool_id == "pregnancy-dating-edd":
        lmp_raw = str(inputs.get("lmp"))
        lmp = datetime.strptime(lmp_raw, "%Y-%m-%d").date()
        today = date.today()
        days = (today - lmp).days
        edd = lmp + timedelta(days=280)
        weeks = days // 7
        rem_days = days % 7
        return _result(tool_id, f"Gebelik yaşı yaklaşık {weeks}+{rem_days} hafta. EDD: {edd.isoformat()}.", {"gestationalAgeWeeks": weeks, "gestationalAgeDays": rem_days, "edd": edd.isoformat()})

    if tool_id == "red-flags":
        flags = [
            label
            for key, label in [
                ("chestPain", "göğüs ağrısı"),
                ("dyspnea", "nefes darlığı"),
                ("neurologicDeficit", "nörolojik defisit"),
                ("severePain", "şiddetli ağrı"),
                ("syncope", "senkop"),
            ]
            if _bool(inputs, key)
        ]
        warning = "Acil değerlendirme gerektirebilecek bulgular var." if flags else "Belirgin red flag işaretlenmedi."
        return _result(tool_id, warning, {"complaint": inputs.get("complaint"), "flags": flags}, flags)

    if tool_id == "patient-education":
        topic = str(inputs.get("topic", ""))
        text = f"{topic} hakkında: Şikayetler artarsa, yeni alarm bulgusu gelişirse veya önerilen kontrolde düzelme olmazsa hekime yeniden başvurunuz."
        return _result(tool_id, "Hasta bilgilendirme taslağı oluşturuldu.", {"educationTextTR": text})

    if tool_id == "referral-discharge-draft":
        draft = {
            "complaint": inputs.get("complaint", ""),
            "assessment": inputs.get("assessment", ""),
            "plan": inputs.get("plan", ""),
            "closing": "Bu metin hekim tarafından düzenlenip onaylandıktan sonra kullanılmalıdır.",
        }
        return _result(tool_id, "Sevk/konsültasyon taslağı oluşturuldu.", draft)

    known = next((tool for tool in list_clinical_tools() if tool["id"] == tool_id), None)
    if known:
        return _result(
            tool_id,
            f"{known['titleTR']} gömülü Clinical Tools modülünde çalıştırılabilir.",
            {"executionMode": "embedded_html_formula", "title": known["titleTR"]},
            ["Bu aracın tam hesaplama formülü frontend içindeki ClinicalTools motorundadır."],
        )

    raise KeyError(f"Unknown clinical tool: {tool_id}")

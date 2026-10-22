"""Senariy (script) parser — Gemini yordamida qahramon dialoglarini ajratish.

Foydalanish:
    import script_parser
    result = script_parser.parse_script_to_roles(script_text)
    voiced = script_parser.assign_voices(result.get("characters", []))
"""

import io
import json
import os
import re
import sys
import time

import httpx
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()

GEMINI_API_KEY = os.getenv("MIYYA_API_KEY", "")
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

SYSTEM_PROMPT = """Sen professional senariy tahlilchisisiz. Quyidagi senariyni tahlil qiling va HAR BIR QAHRAMONNING dialoglarini ajrating.

Faqat quyidagi JSON formatda qaytaring (boshqa hech narsa yozmang):
{
  "characters": [
    {
      "name": "Qahramon ismi",
      "gender": "erkak" yoki "ayol" yoki "bola",
      "description": "Qisqa tavsif (10 so'zdan kam)",
      "dialogue": ["birinchi replika", "ikkinchi replika"]
    }
  ],
  "summary": "Senariy haqida bitta jumla"
}"""

VALID_GENDERS = ("erkak", "ayol", "bola")

# ---------- Gemini API ----------

def call_gemini(prompt: str, system_prompt: str = SYSTEM_PROMPT,
                timeout: float = 60.0, retries: int = 3) -> str:
    """Gemini'ga (system + user) prompt yuborib, matn javobini qaytaradi.

    Vaqtinchalik xatolar (429/5xx) uchun `retries` marta qayta urinadi.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("MIYYA_API_KEY topilmadi (.env faylini tekshiring)")

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.post(GEMINI_URL, json=payload, timeout=timeout)
        except httpx.HTTPError as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            last_err = RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:200]}")
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini javobida candidates yo'q: {str(data)[:300]}")
        parts = candidates[0].get("content", {}).get("parts", []) or []
        text = "".join(p.get("text", "") for p in parts)
        if not text.strip():
            raise RuntimeError("Gemini bo'sh javob qaytardi")
        return text
    raise RuntimeError(f"Gemini {retries} marta urinishdan so'ng ham javob bermadi: {last_err}")


def extract_json(text: str) -> dict:
    """Gemini matnidan JSON obyektni ajratib oladi (markdown fences ham bo'lishi mumkin)."""
    text = text.strip()
    # ```json ... ``` fences
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        # Birinchi { dan oxirgi } gacha
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"JSON topilmadi: {text[:200]}")
        text = text[start:end + 1]
    return json.loads(text)


# ---------- Fallback: oddiy qator-qator tahlil ----------

NAME_RE = re.compile(r"^\s*([A-Z'Oʻʼ’][\w'ʻʼ’\-]*(?:\s+[A-Z'Oʻʼ’][\w'ʻʼ’\-]*)*)\s*[:：]\s*(.+)$")
# Narrativ uslub: "Ali ... dedi: 'replika'" (ASCII va typographic qo'shtirnoqlar)
_NARR_QUOTES = "'\"«»‘’“”„"
NARRATIVE_RE = re.compile(
    r"^\s*([A-Z'Oʻʼ’][\w'ʻʼ’\-]*)\b[^:'\"«»‘’“”]*?\b"
    r"(?:dedi|so'radi|soʻradi|javob berdi|qichqirdi)\s*[:：]\s*"
    r"[" + _NARR_QUOTES + r"](.+?)[" + _NARR_QUOTES + r"]\s*$"
)
_STRIP_QUOTES = "'\"«»‘’“”„"


def fallback_simple_parse(script_text: str) -> dict:
    """Gemini ishlamasa, sodda qoidalar bilan tahlil qiladi.

    Qo'llab-quvvatlanadigan formatlar:
      - "Ism: replika" (sahna izohi bilan yoki yo'q)
      - "Ism ... dedi: 'replika'" (narrativ uslub)
    """
    characters: dict[str, dict] = {}

    def add(name: str, text: str) -> None:
        text = re.sub(r"\([^)]*\)", "", text).strip().strip(_STRIP_QUOTES).strip()
        if not text:
            return
        entry = characters.setdefault(name, {
            "name": name,
            "gender": "erkak",
            "description": "",
            "dialogue": [],
        })
        entry["dialogue"].append(text)

    for line in script_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # "Ism (jiddiy): replika" — ismdan keyingi sahna izohini olib tashlash
        line_no_dir = re.sub(r"\([^)]*\)", "", line).strip()
        m = NAME_RE.match(line_no_dir)
        if m:
            add(m.group(1).strip(), m.group(2).strip())
            continue
        m = NARRATIVE_RE.match(line)
        if m:
            add(m.group(1).strip(), m.group(2).strip())
    return {
        "characters": list(characters.values()),
        "summary": "Oddiy qator-qator tahlil (fallback) orqali ajratildi.",
        "fallback": True,
    }


# ---------- Asosiy funksiya ----------

def parse_script_to_roles(script_text: str) -> dict:
    """Senariyni Gemini orqali strukturali qahramonlar ro'yxatiga aylantiradi.

    Xatolikda fallback parser ishlatiladi; u ham ishlamasa {} qaytaradi.
    """
    script_text = (script_text or "").strip()
    if not script_text:
        return {}

    try:
        raw = call_gemini(script_text)
        data = extract_json(raw)

        chars_out = []
        for c in data.get("characters", []) or []:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "")).strip()
            if not name:
                continue
            gender = str(c.get("gender", "")).strip().lower()
            if gender not in VALID_GENDERS:
                gender = "erkak"
            dialogue = c.get("dialogue", []) or []
            if isinstance(dialogue, str):
                dialogue = [dialogue]
            dialogue = [str(d).strip() for d in dialogue if str(d).strip()]
            chars_out.append({
                "name": name,
                "gender": gender,
                "description": str(c.get("description", "")).strip(),
                "dialogue": dialogue,
            })

        if not chars_out:
            raise ValueError("Gemini JSON'da qahramon topilmadi")

        return {
            "characters": chars_out,
            "summary": str(data.get("summary", "")).strip(),
            "fallback": False,
        }
    except Exception as e:
        print(f"[script_parser] Gemini xatosi: {e} -> fallback ishlatilmoqda")
        try:
            fb = fallback_simple_parse(script_text)
            return fb if fb.get("characters") else {}
        except Exception as e2:
            print(f"[script_parser] Fallback ham ishlamadi: {e2}")
            return {}


# ---------- Ovoz biriktirish ----------

VOICE_POOLS = {
    "erkak": ["2ce3de29febb43d7a4a85a63085e1da1", "7d44c98f619c4e98823a84ed60122f9f"],
    "ayol":  ["933563129e564b19a115bedd57b7406a", "e3cd384158934cc9a01029cd7d278634"],
    "bola":  ["4e407b98cb034f74b3863ec33c567c83", "501f126749464eef92d30fa913da1e8e"],
}
DEFAULT_VOICE = VOICE_POOLS["erkak"][0]


def assign_voices(characters: list) -> dict:
    """Har bir qahramonning jinsiga qarab voice ID biriktiradi (har xil ovozlar).

    Qaytariladigan dict: {"QahramonIsmi": {"voice_id": ..., "gender": ...}, ...}
    """
    used: set[str] = set()
    result: dict[str, dict] = {}
    for c in characters or []:
        if not isinstance(c, dict):
            continue
        name = str(c.get("name", "")).strip()
        if not name or name in result:
            continue
        gender = str(c.get("gender", "")).strip().lower()
        pool = VOICE_POOLS.get(gender, VOICE_POOLS["erkak"])
        # Avval ishlatilmagan ovozni tanlaymiz (bir xil ovoz takrorlanmasin)
        voice_id = next((v for v in pool if v not in used), pool[0])
        used.add(voice_id)
        result[name] = {"voice_id": voice_id, "gender": gender or "erkak"}
    return result


def build_voice_plan(script_text: str) -> dict:
    """parse_script_to_roles + assign_voices birlashtirilgan qulay wrapper."""
    parsed = parse_script_to_roles(script_text)
    if not parsed:
        return {}
    return {
        "characters": parsed["characters"],
        "summary": parsed.get("summary", ""),
        "fallback": parsed.get("fallback", False),
        "voices": assign_voices(parsed["characters"]),
    }


if __name__ == "__main__":
    script = (
        "Ali: Assalomu alaykum, qalaysiz?\n"
        "Zulfiya: Yaxshi, rahmat. Sizchi?\n"
        "Ali: Men ham yaxshi. Bugun ob-havo juda chiroyli.\n"
        "Bolacha: Dad, men ochman!\n"
        "Ali: Bo'ladi o'g'lim, hozir ovqat qilamiz.\n"
    )
    print(json.dumps(build_voice_plan(script), ensure_ascii=False, indent=2))

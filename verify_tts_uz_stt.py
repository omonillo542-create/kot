# -*- coding: utf-8 -*-
"""
Fish Audio MP3 larni Gemini STT orqali qayta transkripsiya qilish
(matn qayta tiklanishi = ovoz sifatining obyektiv o'lchovi).
"""
import base64
import io
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
for line in (BASE_DIR / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.strip().partition("=")
        os.environ.setdefault(k, v)

KEY = os.environ.get("MIYYA_API_KEY", "")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
SRC = "Assalomu alaykum! Menga matn kerak. Ovozli xabar yuboring."

import requests


def norm(s: str) -> list[str]:
    s = s.lower().replace("'", "").replace("\u2018", "").replace("\u2019", "")
    s = re.sub(r"[^\w\s]", " ", s)
    return [w for w in s.split() if w]


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, " ".join(norm(a)), " ".join(norm(b))).ratio()


def stt(audio: bytes, mime="audio/mpeg") -> str | None:
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime,
                                 "data": base64.b64encode(audio).decode()}},
                {"text": (
                    "Bu ovozli xabar. Undagi so'zlarni aniq transkripsiya qiling.\n"
                    "- Agar o'zbekcha bo'lsa, o'zbek tilida yozing (o', g', so'm)\n"
                    "- Faqat transkripsiya matnini qaytaring, boshqa hech narsa yozmang"
                )},
            ]
        }]
    }
    r = requests.post(f"{URL}?key={KEY}", json=payload, timeout=90)
    if r.status_code != 200:
        print(f"    STT HTTP {r.status_code}: {r.text[:200]}")
        return None
    for p in r.json().get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "text" in p:
            return p["text"].strip()
    return None


print("Kutilgan matn:", SRC)
print("=" * 70)
files = sorted(BASE_DIR.glob("test_fish_*.mp3"))
if not files:
    print("test_fish_*.mp3 fayllari topilmadi")
for f in files:
    print(f"\n{f.name}  ({f.stat().st_size / 1024:.1f} KB)")
    text = stt(f.read_bytes())
    if text is None:
        print("    STT: FAILED")
        continue
    s = sim(SRC, text)
    print(f"    STT: {text}")
    print(f"    O'xshashlik: {s:.0%}")

"""
intent_detector.py — Telegram bot uchun foydalanuvchi niyatini aniqlash (Uzbek).

Gemini (gemini-3.5-flash-lite) orqali niyat aniqlaydi:
    tts | stt | grandpa | script | help | chat

Gemini ishlamasa (kalit noto'g'ri, tarmoq xatosi, 429/5xx, javob yaroqsiz)
— kalit so'zlar (keyword) asosida fallback ishlatiladi.

Foydalanish:
    from intent_detector import detect_intent, detect_intent_async

    detect_intent("Matnni ovozga aylantir")        # -> "tts"   (sync)
    await detect_intent_async("Salom")             # -> "chat"  (aiogram handlerlar uchun)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from pathlib import Path

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:  # python-dotenv o'rnatilmagan bo'lsa ham ishlaydi
    pass

logger = logging.getLogger(__name__)

# =============================================
# Konfiguratsiya
# =============================================

GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = (
    "Sen Telegram bot yordamchisisiz. Foydalanuvchi xabarini o'qib, niyatini aniqlang.\n"
    "\n"
    "Quyidagi niyatlardan birini tanlang:\n"
    '- "tts" — ovoz yaratmoqchi (matnni ovozga aylantirish)\n'
    '- "stt" — ovozdan matn olish xohlaydi\n'
    '- "grandpa" — keksa odam ovozini xohlaydi\n'
    '- "script" — senariy yubormoqda yoki senariy haqida gapirmoqda\n'
    '- "help" — bot haqida savol bermoqda\n'
    '- "chat" — oddiy suhbat qilmoqda\n'
    "\n"
    "Faqat niyat nomini qaytaring. Boshqa hech narsa yozmang."
)

VALID_INTENTS = ("tts", "stt", "grandpa", "script", "help", "chat")
DEFAULT_INTENT = "chat"

GEMINI_TIMEOUT = 20.0     # soniya — to'liq Gemini testi uchun (jonli botda kamaytiring, quy. tezlik bo'limi)
FAST_GEMINI_TIMEOUT = 2.5 # soniya — "tez rejim" uchun deadline (3s chegaradan past)
GEMINI_RETRIES = 2        # 5xx / tarmoq xatlari uchun qayta urinish
CACHE_MAX = 512           # niyat keshi hajmi (takroriy xabarlar uchun)

# Kalit so'zlarni indekslash (pastga tushirilgan holda qidiriladi)
_KW_GRANDPA = ("grandpa", "keksa", "qariya", "bobo")
_KW_SCRIPT = ("senariy", "skript", "script", "drama")
_KW_HELP = ("yordam", "nima qila", "help")
_KW_STT = ("stt", "transkripsiya", "ovozli xabar", "vozli xabar", "ovozdan matn", "transkript")
_KW_TTS = ("tts", "voice", "audio", "ovozga", "ovoz yarat", "aylantir", "o'qib", "ovoz")

_INTENT_RE = re.compile(r"\b(tts|stt|grandpa|script|help|chat)\b", re.IGNORECASE)


# =============================================
# 1) Kalit so'zlar bilan fallback
# =============================================

def keyword_intent(text: str) -> str:
    """Gemini'siz, kalit so'zlar orqali niyat aniqlash (fallback).

    Muhim: tekshirish tartibi muhim, aks holda ayrim xabarlar noto'g'ri
    tasniflanadi:
      - "Keksa odam ovozida qil" ichida "ovoz" bor → grandpa tekshiruvi
        tts'dan oldin turishi kerak;
      - "Ovozli xabar yuboraman" ichida ham "ovoz" bor → stt tekshiruvi
        tts'dan oldin turishi kerak;
      - "Matnni ovozga aylantir" ichida "matn" bor → tts ("ovozga"/"aylantir")
        matn'dan oldin turishi kerak.
    """
    t = (text or "").lower()

    # 0) Uzun dialog (senariy) — kalit so'zlardan ham oldin, chunki uzun
    #    matnda "ovoz" so'zi uchraydi va u script bo'ladi
    if len(text or "") > 200 and ":" in text:
        return "script"

    # 1) Keksa odam ovozini xohlaydi
    if any(k in t for k in _KW_GRANDPA):
        return "grandpa"

    # 2) Senariy
    if any(k in t for k in _KW_SCRIPT):
        return "script"

    # 3) Yordam / savol
    if any(k in t for k in _KW_HELP):
        return "help"

    # 4) Ovoz → matn (STT)
    if any(k in t for k in _KW_STT):
        return "stt"

    # 5) Matn → ovoz (TTS)
    if any(k in t for k in _KW_TTS):
        return "tts"

    # 6) Oddiy "matn" so'zi (TTS emas, "ovozga aylantir" allaqachon yuqorida)
    if "matn" in t:
        return "stt"

    return DEFAULT_INTENT


# =============================================
# 2) Gemini orqali niyat aniqlash
# =============================================

def _parse_intent(raw: str | None) -> str | None:
    """Gemini javobidan niyat nomini ajratib oladi. Yaroqsiz bo'lsa None."""
    if not raw:
        return None
    m = _INTENT_RE.search(raw.strip().lower())
    if not m:
        return None
    intent = m.group(1).lower()
    return intent if intent in VALID_INTENTS else None


def _gemini_detect(
    text: str,
    api_key: str,
    timeout: float = GEMINI_TIMEOUT,
    retries: int = GEMINI_RETRIES,
) -> str | None:
    """Gemini'ga so'rov yuboradi. Muvaffaqiyatsiz bo'lsa None qaytaradi."""
    if not api_key:
        logger.warning("Gemini API kaliti topilmadi (MIYYA_API_KEY)")
        return None

    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 1024,
            "candidateCount": 1,
        },
    }
    # Esluma: thinkingConfig (thinkingBudget=0) bu modelda 400 INVALID_ARGUMENT
    # beradi — yubormaymiz.
    headers = {"x-goog-api-key": api_key}

    with httpx.Client(timeout=timeout) as client:
        for attempt in range(retries + 1):
            try:
                r = client.post(GEMINI_URL, json=payload, headers=headers)
            except Exception as e:
                logger.warning("Gemini so'rovi amalga oshmadi (%s/%s): %s",
                               attempt + 1, retries + 1, e)
                continue

            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    return None
                parts = candidates[0].get("content", {}).get("parts", []) or []
                raw = "".join(p.get("text", "") for p in parts if "text" in p)
                return _parse_intent(raw)

            if r.status_code == 429 or r.status_code >= 500:
                logger.warning("Gemini HTTP %s (%s/%s)", r.status_code,
                               attempt + 1, retries + 1)
                continue
            # 401/403 (kalit noto'g'ri) — qayta urinishsiz chiqamiz
            logger.error("Gemini API xatosi %s: %s", r.status_code, r.text[:200])
            return None
    return None


# =============================================
# 3) Asosiy funksiya (sync) + kesh + tez rejim
# =============================================

_CACHE: dict[tuple[str, str], str] = {}


def _normalize(text: str) -> str:
    """Kesh kaliti uchun matnni normallashtiradi."""
    return " ".join((text or "").split()).lower()


def _cache_get(key: tuple[str, str]) -> str | None:
    return _CACHE.get(key)


def _cache_put(key: tuple[str, str], value: str) -> None:
    if len(_CACHE) >= CACHE_MAX:
        _CACHE.clear()  # oddiy siyosat: to'lganda tozalaymiz
    _CACHE[key] = value


def detect_intent(
    text: str,
    api_key: str | None = None,
    timeout: float = GEMINI_TIMEOUT,
    use_cache: bool = True,
) -> str:
    """Foydalanuvchi xabaridan niyatni aniqlaydi.

    Avval Gemini'ga so'rov yuboradi; u ishlamasa (tarmoq/429/5xx xatosi),
    javob qaytarmasa yoki yaroqsiz niyat yozsa — kalit so'zlar fallback'i
    ishlatiladi. Natija keshlanadi (takroriy xabarlar uchun 0 ms).

    Qaytadi: "tts" | "stt" | "grandpa" | "script" | "help" | "chat"
    """
    text = text or ""
    key = api_key if api_key is not None else os.getenv("MIYYA_API_KEY", "")
    ck = (key, _normalize(text))
    if use_cache:
        cached = _cache_get(ck)
        if cached:
            return cached

    try:
        intent = _gemini_detect(text, key, timeout=timeout)
    except Exception as e:
        logger.error("detect_intent xatosi: %s", e)
        intent = None
    result = intent if intent else keyword_intent(text)
    if use_cache:
        _cache_put(ck, result)
    return result


def detect_intent_fast(
    text: str,
    api_key: str | None = None,
    timeout: float = FAST_GEMINI_TIMEOUT,
    use_cache: bool = True,
) -> str:
    """Tez variant (jonli bot uchun, ~0-2.5 s chegarada).

    1) Avval kalit so'zlar qoidalari tekshiriladi — aniq moslik topsa,
       Gemini'ga umuman so'rov yuborilmaydi (0 ms).
    2) Moslik topilmasa (masalan "Salom" kabi xabarlar) — Gemini'ga
       qisqa deadline bilan so'rov ketadi; javob kelmasa "chat".
    """
    text = text or ""
    kw = keyword_intent(text)
    # Default ("chat") — qoida tegmadi, Gemini'ga so'raymiz.
    # Qoida tegkan bo'lsa (tts/stt/grandpa/script/help) — shu natija yetarli.
    if kw != DEFAULT_INTENT:
        return kw

    # Default "chat" bo'lsa ham, Gemini orqali tasdiqlashga urinamiz,
    # lekin uzun matn (senariy) yoki bandwidth uchun keshdan foydalanamiz.
    return detect_intent(text, api_key=api_key, timeout=timeout, use_cache=use_cache)


# =============================================
# 4) Async variant (aiogram handlerlar uchun — bloklamaydi)
# =============================================

async def detect_intent_async(
    text: str,
    api_key: str | None = None,
    timeout: float = GEMINI_TIMEOUT,
) -> str:
    """detect_intent'ning async versiyasi — bot.py dagi handlerlar uchun."""
    text = text or ""
    key = api_key if api_key is not None else os.getenv("MIYYA_API_KEY", "")
    intent = None
    if key:
        url = f"{GEMINI_URL}?key={key}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 1024},
        }
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                for attempt in range(GEMINI_RETRIES + 1):
                    try:
                        async with session.post(
                            url, json=payload,
                            timeout=aiohttp.ClientTimeout(total=timeout),
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                candidates = data.get("candidates") or []
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", []) or []
                                    raw = "".join(p.get("text", "") for p in parts if "text" in p)
                                    intent = _parse_intent(raw)
                                break
                            if resp.status == 429 or resp.status >= 500:
                                await asyncio.sleep(0.3 * (attempt + 1))
                                continue
                            logger.error("Gemini API xatosi %s", resp.status)
                            break
                    except Exception as e:
                        logger.warning("Gemini async so'rovi xatosi: %s", e)
                        await asyncio.sleep(0.2)
        except Exception as e:
            logger.error("detect_intent_async xatosi: %s", e)

    return intent if intent else keyword_intent(text)


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for line in sys.argv[1:] or ["Salom"]:
        print(f"{line!r} -> {detect_intent(line)}")

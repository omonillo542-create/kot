# -*- coding: utf-8 -*-
"""
O'zbek tili uchun TTS sifatini tekshirish skripti.

1) gTTS (lang="uz")
2) Fish Audio via OpenRouter (fish-audio/s2.1-pro-free:free) - bir necha ovozlar
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent

# --- .env yuklash ---
env_path = BASE_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

GTTS_TEXT = "Assalomu alaykum! Men ovoz botman. Matnni ovozga aylantiraman."
FISH_TEXT = "Assalomu alaykum! Menga matn kerak. Ovozli xabar yuboring."

TTS_API_URL = "https://openrouter.ai/api/v1/audio/speech"
TTS_MODEL = "fish-audio/s2.1-pro-free:free"

VOICES = [
    ("erkak_rasmiy", "44ad146afad04e4e99a7b98b8f97106f"),
    ("erkak_tabiiy", "fef226d2978a42d5b542e7577134f7b2"),
    ("grandpa_spencer", "245aac5cae7640d88a0e81da89c1e0f3"),
    ("sarah", "933563129e564b19a115bedd57b7406a"),
    ("default", None),  # voice'siz
]

results = []


def human(nbytes: int) -> str:
    if nbytes >= 1024 * 1024:
        return f"{nbytes / (1024 * 1024):.2f} MB"
    return f"{nbytes / 1024:.1f} KB"


def mp3_duration(path: Path) -> float | None:
    """ffmpeg orqali MP3 davomini olish (mavjud bo'lmasa None)."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        out = subprocess.run(
            [exe, "-i", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out.stderr)
        if m:
            h, mi, s = m.groups()
            return int(h) * 3600 + int(mi) * 60 + float(s)
    except Exception:
        return None
    return None


def save(data: bytes, name: str) -> Path:
    p = BASE_DIR / name
    p.write_bytes(data)
    return p


# ============================================================
# 1) gTTS
# ============================================================
def test_gtts():
    print("=" * 64)
    print("1) gTTS  (lang='uz')")
    print("=" * 64)
    t0 = time.time()
    try:
        from gtts import gTTS
        tts = gTTS(text=GTTS_TEXT, lang="uz", slow=False)
        path = BASE_DIR / "test_gtts_uz.mp3"
        tts.save(str(path))
        size = path.stat().st_size
        dur = mp3_duration(path)
        dt = time.time() - t0
        ok = size > 1000
        print(f"  STATUS : {'OK' if ok else 'FAILED (kichik fayl)'}")
        print(f"  Fayl   : {path.name}")
        print(f"  Hajm   : {human(size)} ({size} bayt)")
        if dur:
            print(f"  Davomi  : {dur:.2f} s")
        print(f"  Vaqt   : {dt:.1f} s")
        results.append(("gTTS (uz)", ok, size, dur, ""))
        return ok
    except Exception as e:
        print(f"  STATUS : FAILED - {type(e).__name__}: {e}")
        results.append(("gTTS (uz)", False, 0, None, str(e)[:120]))
        return False


# ============================================================
# 2) Fish Audio via OpenRouter
# ============================================================
def fish_request(voice_id: str | None):
    """Ikkita urinish: to'liq payload -> oddiy payload. (data, qaysi variant)"""
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    full = {
        "model": TTS_MODEL,
        "input": FISH_TEXT,
        "response_format": "mp3",
        "provider": {
            "options": {
                "fish-audio": {
                    "normalize": True,
                    "latency": "normal",
                    "prosody": {"speed": 1.0, "normalize_loudness": True},
                }
            }
        },
    }
    if voice_id:
        full["voice"] = voice_id

    minimal = {"model": TTS_MODEL, "input": FISH_TEXT, "response_format": "mp3"}
    if voice_id:
        minimal["voice"] = voice_id

    last_err = ""
    for variant, payload in (("full", full), ("minimal", minimal)):
        try:
            r = requests.post(TTS_API_URL, headers=headers, json=payload, timeout=180)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue
        ctype = r.headers.get("content-type", "")
        if r.status_code == 200 and "audio" in ctype and len(r.content) > 500:
            return r.content, f"{variant} payload"
        snippet = r.text[:300].replace("\n", " ")
        last_err = f"HTTP {r.status_code} [{variant}] {ctype}: {snippet}"
    return None, last_err


def test_fish():
    print("=" * 64)
    print(f"2) Fish Audio via OpenRouter  ({TTS_MODEL})")
    print("=" * 64)
    if not OPENROUTER_API_KEY:
        print("  OPENROUTER_API_KEY topilmadi!")
        results.append(("Fish Audio", False, 0, None, "no api key"))
        return
    for name, vid in VOICES:
        label = f"fish_{name}"
        shown = vid if vid else "yo'q (default)"
        print(f"\n  -- {name}  voice={shown}")
        t0 = time.time()
        data, info = fish_request(vid)
        dt = time.time() - t0
        if data:
            path = save(data, f"test_fish_{name}.mp3")
            size = path.stat().st_size
            dur = mp3_duration(path)
            print(f"     STATUS : OK ({info})")
            print(f"     Fayl   : {path.name}  Hajm: {human(size)}" +
                  (f"  Davom: {dur:.2f} s" if dur else ""))
            print(f"     Vaqt   : {dt:.1f} s")
            results.append((f"Fish: {name}", True, size, dur, info))
        else:
            print(f"     STATUS : FAILED - {info}")
            results.append((f"Fish: {name}", False, 0, None, info[:160]))


def main():
    print("O'zbek TTS testi boshlandi\n")
    if not OPENROUTER_API_KEY:
        print("Ogohlantirish: OPENROUTER_API_KEY o'rnatilmagan\n")
    test_gtts()
    print()
    test_fish()

    print("\n" + "=" * 64)
    print("3) NATIJALAR")
    print("=" * 64)
    print(f"{'Test':<26} {'Holat':<8} {'Hajm':<12} {'Davom':<8} Izoh")
    print("-" * 64)
    for name, ok, size, dur, note in results:
        st = "OK" if ok else "FAILED"
        h = human(size) if size else "-"
        d = f"{dur:.1f}s" if dur else "-"
        print(f"{name:<26} {st:<8} {h:<12} {d:<8} {note[:40]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

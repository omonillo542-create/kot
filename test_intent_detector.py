"""
test_intent_detector.py — Gemini niyat aniqlashni to'liq sinovdan o'tkazadi.

Bosqichlar:
  1) Gemini bilan 10 ta o'zbekcha test xabari (a–j)
  2) Kalit so'zlar fallback'i — Gemini ishlamayotganda (yaroqli kalit bilan)
  3) Tezlik — Gemini javob vaqti o'lchanadi
"""

import sys, io, time, statistics, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.getLogger("intent_detector").setLevel(logging.CRITICAL)  # log shovqinsini o'chirish

from intent_detector import detect_intent, detect_intent_fast, keyword_intent, _gemini_detect

BAD_KEY = "AQ.this-key-is-invalid-0000000000000000"

LONG_SCRIPT = (
    "Ali: Salom, qalaysiz? Men yaxshiman. Bugun juda qiziq voqea bo'ldi, "
    "do'stlar bilan kinoga bordik.\n"
    "Dilshod: Ha, aytib o'ting keyin. Kechqurun hammani birga uchrashdik.\n"
    "Ali: Zo'r! Ertaga yana uchrashamizmi? Soat oltida maktab yonida kutaman.\n"
    "Dilshod: Albatta, kechikmasam bo'ladi. Hozirgina uyga keldim, dam olay."
)

CASES = [
    ("a", "Salom", "chat"),
    ("b", "Matnni ovozga aylantir", "tts"),
    ("c", "Ovozli xabar yuboraman", "stt"),
    ("d", "Keksa odam ovozida qil", "grandpa"),
    ("e", "Bot nima qila oladi?", "help"),
    ("f", "Quyidagi senariyni tahlil qil: Ali: Salom", "script"),
    ("g", "Yaxshi, qalaysiz?", "chat"),
    ("h", "Ovoz yarat", "tts"),
    ("i", LONG_SCRIPT, "script"),
    ("j", "Menga audio kerak", "tts"),
]

assert len(LONG_SCRIPT) > 200 and ":" in LONG_SCRIPT, "test (i) uzunligi >200 bo'lishi kerak"


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ---------------------------------------------------------
section("1) GEMINI BILAN TEST (a-j)")
# ---------------------------------------------------------
results = []
for name, msg, expected in CASES:
    t0 = time.time()
    try:
        got = detect_intent(msg)
    except Exception as e:
        got = f"EXC:{e}"
    dt = time.time() - t0
    ok = got == expected
    results.append((ok, dt))
    shown = msg if len(msg) <= 60 else msg[:57] + "..."
    print(f"  [{name}] {'OK ' if ok else 'FAIL'} expected={expected:<8} got={got:<8} {dt:6.2f}s  {shown!r}")

gem_ok = sum(1 for ok, _ in results if ok)
print(f"\n  Gemini natija: {gem_ok}/{len(CASES)} to'g'ri")


# ---------------------------------------------------------
section("2) FALLBACK TEST — Gemini ishlamayotganda (yaroqsiz kalit)")
# ---------------------------------------------------------
# avval Gemini haqiqatan ham ishlamayotganini tekshiramiz
probe = _gemini_detect("Salom", BAD_KEY, timeout=5.0, retries=0)
print(f"  _gemini_detect(yaroqsiz kalit) = {probe!r}  (None bo'lishi kerak)")
assert probe is None, "yaroqsiz kalit Gemini'dan niyat qaytarmasligi kerak"

fb = []
for name, msg, expected in CASES:
    t0 = time.time()
    got = detect_intent(msg, api_key=BAD_KEY, timeout=3.0)
    dt = time.time() - t0
    ok = got == expected
    fb.append(ok)
    shown = msg if len(msg) <= 60 else msg[:57] + "..."
    print(f"  [{name}] {'OK ' if ok else 'FAIL'} expected={expected:<8} got={got:<8} {dt:6.2f}s  {shown!r}")

fb_ok = sum(fb)
print(f"\n  Fallback natija: {fb_ok}/{len(CASES)} to'g'ri")

# qo'shimcha: kalit so'z qoidalarining mustaqil tekshiruvi
print("\n  keyword_intent() mustaqil tekshiruvi:")
extra = [
    ("Ovozga aylantir bu matnni", "tts"),
    ("transkripsiya qilib bering", "stt"),
    ("boboning ovozi bo'lsin", "grandpa"),
    ("drama sifatida yoz", "script"),
    ("yordam beraolasizmi?", "help"),
    ("Bugun ob-havo yaxshi ekan", "chat"),
]
for msg, expected in extra:
    got = keyword_intent(msg)
    print(f"  {'OK ' if got == expected else 'FAIL'} {expected:<8} <- {got:<8} {msg!r}")


# ---------------------------------------------------------
section("3) TEZLIK TEST")
# ---------------------------------------------------------
times = []
for i in range(5):
    msg = CASES[i % len(CASES)][1]
    t0 = time.time()
    got = detect_intent(msg, use_cache=False)   # keshsiz — haqiqiy Gemini vaqti
    dt = time.time() - t0
    times.append(dt)
    print(f"  #{i + 1} {dt:6.2f}s -> {got}")

avg = statistics.mean(times)
med = statistics.median(times)
print(f"\n  O'rtacha: {avg:.2f}s | Median: {med:.2f}s | Min: {min(times):.2f}s | Max: {max(times):.2f}s")
print(f"  3s chegarasi: {'UTDI (sekin)' if avg > 3 else 'UTDI (tez)'}")

# fallback tezligi
t0 = time.time()
for _ in range(20):
    keyword_intent("Matnni ovozga aylantir")
fb_speed = (time.time() - t0) / 20 * 1000
print(f"  Fallback (kalit so'z) o'rtacha: {fb_speed:.2f} ms")

# kesh tezligi (takroriy xabar)
detect_intent("Salom", use_cache=False)
t0 = time.time()
for _ in range(20):
    detect_intent("Salom")
cache_speed = (time.time() - t0) / 20 * 1000
print(f"  Keshdan (takroriy xabar) o'rtacha: {cache_speed:.2f} ms")

# tez rejim (kalit so'z yo'qda Gemini, deadline 2.5s)
t0 = time.time()
fast1 = detect_intent_fast("Keksa odam ovozida qil")
fast1_dt = time.time() - t0
t0 = time.time()
fast2 = detect_intent_fast("Salom", timeout=2.5)
fast2_dt = time.time() - t0
print(f"  detect_intent_fast (kalit mosligi): {fast1_dt * 1000:.1f} ms -> {fast1}")
print(f"  detect_intent_fast (Salom, Gemini+deadline): {fast2_dt:.2f}s -> {fast2}")


# ---------------------------------------------------------
section("XULOSA")
# ---------------------------------------------------------
print(f"  Gemini:      {gem_ok}/{len(CASES)}")
print(f"  Fallback:    {fb_ok}/{len(CASES)}")
print(f"  Gemini o'rtacha vaqti: {avg:.2f}s")
all_ok = (gem_ok == len(CASES)) and (fb_ok == len(CASES))
print(f"  UMUMIY: {'HAMMA TEST O\'TDI' if all_ok else 'BAZI TESTLAR YIQILDI'}")
sys.exit(0 if all_ok else 1)

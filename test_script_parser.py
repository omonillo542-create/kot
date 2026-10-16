"""Gemini senariy parser testlari — 4 xil format."""
import json
import sys

import script_parser as sp

SCRIPTS = {
    "a) Oddiy dialog": (
        "Ali: Assalomu alaykum, qalaysiz?\n"
        "Zulfiya: Yaxshi, rahmat. Sizchi?\n"
        "Ali: Men ham yaxshi. Bugun ob-havo juda chiroyli.\n"
        "Bolacha: Dad, men ochman!\n"
        "Ali: Bo'ladi o'g'lim, hozir ovqat qilamiz.\n"
    ),
    "b) Sahna izohi uslubi": (
        "Ali (jiddiy): Assalomu alaykum, qalaysiz?\n"
        "Zulfiya (kulib): Yaxshi, rahmat. Sizchi?\n"
        "Ali (jiddiy): Muhim gap bor, o'tiring.\n"
    ),
    "c) Narrativ uslub": (
        "Ali Zulfiyaga qaradi va dedi: 'Yaxshimisiz?'\n"
        "Zulfiya javob berdi: 'Yaxshi, rahmat. Siz chiroyli ko'rinasiz.'\n"
        "Bolacha dadining yoniga yugurib keldi: 'Dad, men ochman!'\n"
    ),
    "d) O'zbek lotin (o', g', sh, ch)": (
        "G'ulom: Yo'q, men bilmayman.\n"
        "Shahzoda: O'sha joyga borish kerak.\n"
        "O'ktam: Kechirasiz, chaqmoq chaqdi!\n"
        "G'ulom: Tushunarli, rahmat o'zim.\n"
    ),
}

OK = "OK "
FAIL = "XATO: "


def show(title, result):
    print("=" * 70)
    print(f"TEST: {title}")
    print("-" * 70)
    if not result:
        print(f"{FAIL}natija bo'sh dict")
        return False
    if result.get("fallback"):
        print("*** Fallback parser ishlatildi (Gemini emas) ***")
    print(f"Summary: {result.get('summary', '')}")
    voices = result.get("voices") or sp.assign_voices(result.get("characters", []))
    for c in result.get("characters", []):
        v = voices.get(c["name"], {})
        print(f"  [{c['name']}] gender={c['gender']} voice={v.get('voice_id', '?')}")
        print(f"    tavsif: {c.get('description', '')}")
        for d in c.get("dialogue", []):
            print(f"    - {d}")
    return True


def main():
    ok_all = True
    for title, script in SCRIPTS.items():
        try:
            result = sp.build_voice_plan(script)
        except Exception as e:
            print(f"{FAIL}{title} -> {e}")
            ok_all = False
            continue
        ok = show(title, result)
        ok_all = ok_all and ok
        print()

    # Maxsus test: fallback parser (Gemini'siz, API kaliti o'chirilgan holda)
    print("=" * 70)
    print("TEST: e) Fallback parser (API'siz)")
    print("-" * 70)
    fb = sp.fallback_simple_parse(SCRIPTS["a) Oddiy dialog"])
    for c in fb["characters"]:
        print(f"  [{c['name']}] -> {c['dialogue']}")
    ok_all = ok_all and len(fb["characters"]) == 3

    # Maxsus test: noto'g'ri JSON keladigan holat uchun extract_json
    print()
    print("=" * 70)
    print("TEST: f) extract_json (markdown fence bilan)")
    print("-" * 70)
    wrapped = '```json\n{"characters": [{"name": "Ali", "gender": "erkak", "description": "t", "dialogue": ["salom"]}], "summary": "s"}\n```'
    try:
        d = sp.extract_json(wrapped)
        print(f"  OK -> {len(d['characters'])} ta qahramon: {d['characters'][0]['name']}")
    except Exception as e:
        print(f"  XATO: {e}")
        ok_all = False

    print()
    print("JAMI NATIJA:", "BARCHA TESTLAR O'TDI" if ok_all else "BAZI TESTLAR MUVAFFAQIYATSIZ")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

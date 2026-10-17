# 🎙️ AI Ovoz Bot (@mp3speak_bot)

O'zbek tilidagi AI yordamchi Telegram bot: matnni ovozga aylantirish, ovozni matnga aylantirish (STT), senariy bo'yicha qahramonlarga alohida ovoz berish, Grandpa effekti va AI suhbat.

## ✨ Imkoniyatlar

- 🗣 **TTS (matn → ovoz)** — Edge TTS (bepul) asosiy dvigatel; Kokoro, Fish Audio fallback
- 🎤 **STT (ovoz → matn)** — Gemini bilan o'zbekcha transkripsiya
- 🎭 **Senariy** — qahramonlarni ajratib, har biriga alohida ovoz
- 👴 **Grandpa effekti** — FFmpeg bilan keksa odam ovozi
- 💬 **AI suhbat** — Gemini 3.5 Flash Lite
- ⚙️ **Sozlamalar** (`/settings`) — til (uz/ru/en), ovoz (erkak/ayol), tezlik (sekin/normal/tez)
- 📄 **Fayl o'qish** — .txt, .pdf, .docx (10 MB gacha)
- 📚 **Tarix** (`/history`) — oxirgi 10 matn
- 🚀 **Inline rejimi** — har qanday chatda `@mp3speak_bot matn` → ovoz xabari
- 📊 **Kunlik limit** — `DAILY_LIMIT` (.env da sozlanadi, 0 = cheklovsiz)
- 👑 **Admin panel** (`/admin`) — statistika va broadcast (faqat `ADMIN_IDS`)

## 🛠 O'rnatish

```bash
pip install -r requirements.txt
```

Kerakli tashqi dastur: **FFmpeg** (loyihada `imageio-ffmpeg` bilan keladi, alohida o'rnatish shart emas).

## ⚙️ .env sozlash

`.env.example` faylini nusxalab `.env` qiling va qiymatlarni to'ldiring:

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | Telegram bot tokeni (@BotFather dan) |
| `MIYYA_API_KEY` | Gemini API kaliti (chat/STT/intent) |
| `OPENROUTER_API_KEY` | OpenRouter kaliti (Fish Audio fallback) |
| `OPENROUTER_THINKING_KEY` | matnni tayyorlash uchun (ixtiyoriy) |
| `ADMIN_IDS` | Admin ID lari, vergul bilan (masalan `123,456`) |
| `DAILY_LIMIT` | Kunlik so'rovlar (0 = cheklovsiz) |
| `KOKORO_API_URL` | Kokoro TTS endpointi (fallback) |
| `KOKORO_ENABLED` | `true`/`false` — Kokoro ishlatilsinmi |

> ⚠️ `.env` hech qachon Git'ga commit qilinmaydi (`.gitignore` ichida).

## ▶️ Ishga tushirish

```bash
python bot.py
```

Baza (`bot.db`) birinchi ishga tushirishda avtomatik yaratiladi.

## 📦 Loyiha tuzilishi

| Fayl | Vazifasi |
|---|---|
| `bot.py` | Asosiy bot: handlerlar, TTS/STT, AI oqimi |
| `database.py` | SQLite (aiosqlite): sozlamalar, tarix, limitlar |
| `texts.py` | Barcha UI matnlari (o'zbekcha) |
| `requirements.txt` | Python kutubxonalari |

## 🔐 Xavfsizlik

- Barcha kalitlar faqat `.env` da
- SQL so'rovlari parametrlangan (SQL injection yo'q)
- Vaqtinchalik fayllar `tmp/` da uuid bilan, `finally` da o'chiriladi
- Throttling middleware (1.5s) + TTS Semaphore (5 parallel) — serverga yuk kam

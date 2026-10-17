"""texts.py — bot interfeysidagi barcha matnlar (o'zbekcha).

Barcha foydalanuvchi ko'radigan matnlar shu faylda.
"""

# =============================================
# SALOMLASHUV VA YORDAM
# =============================================

GREETING = (
    "Assalomu alaykum! 👋 Men <b>AI Ovoz Bot</b>man.\n\n"
    "Men nima qila olaman:\n"
    "🔊 Matnni ovozga aylantiraman (o'zbek, rus, ingliz)\n"
    "🎤 Ovozli xabaringizni matnga aylantiraman\n"
    "👴 Grandpa (keksa odam) effektini qo'llayman\n"
    "🎭 Senariy bo'yicha har bir qahramonni alohida ovozda ovozlayman\n"
    "💬 Har qanday savolga javob beraman\n\n"
    "Matn yuboring yoki mikrofonni bosing — men o'zim tushunaman. 😊\n\n"
    "⚙️ Sozlamalarni o'zgartirish uchun /settings bosing."
)

HELP = (
    "ℹ️ <b>Yo'riqnoma</b>\n\n"
    "Men AI yordamchiman — oddiygina yozing yoki ovoz yuboring:\n\n"
    "🔊 <b>Matn → Ovoz</b> — 'Salom, bugun ob-havo zo'r' deb yozing\n"
    "🎤 <b>Ovoz → Matn</b> — mikrofon tugmasini bosib gapiring\n"
    "👴 <b>Grandpa effekti</b> — 'Grandpa ovozida aylantir: ...'\n"
    "🎭 <b>Senariy</b> — qahramonlari bilan dialog yuboring\n"
    "💬 <b>Suhbat</b> — har qanday savol bering\n\n"
    "Buyruqlar:\n"
    "/start — qaytadan boshlash\n"
    "/settings — ovoz, til, tezlik sozlamalari\n"
    "/history — oxirgi matnlaringiz\n"
    "/reset — suhbat tarixini tozalash\n\n"
    "⚠️ Maksimal ovoz xabari: 5 daqiqa"
)

RESET_DONE = (
    "🔄 Suhbat tarixi tozalandi. Qaytadan boshlaymiz — yozing yoki "
    "ovoz yuboring! 😊"
)

# =============================================
# SOZLAMALAR (/settings)
# =============================================

SETTINGS_HEADER = (
    "⚙️ <b>Sozlamalar</b>\n\n"
    "Hozirgi sozlamalaringiz:"
)

SETTINGS_SUMMARY = (
    "🌍 Til: <b>{lang}</b>\n"
    "🗣 Ovoz: <b>{voice}</b>\n"
    "⚡ Tezlik: <b>{speed}</b>"
)

CHOOSE_LANG = "🌍 Tilni tanlang:"
CHOOSE_VOICE = "🗣 Ovozni tanlang:"
CHOOSE_SPEED = "⚡ Tezlikni tanlang:"

# Tugma matnlari
BTN_LANG_UZ = "🇺🇿 O'zbek"
BTN_LANG_RU = "🇷🇺 Rus"
BTN_LANG_EN = "🇬🇧 Ingliz"

BTN_VOICE_MALE = "🧔 Erkak"
BTN_VOICE_FEMALE = "👩 Ayol"

BTN_SPEED_SLOW = "🐢 Sekin"
BTN_SPEED_NORMAL = "🚶 Normal"
BTN_SPEED_FAST = "⚡ Tez"

BTN_REFRESH = "🔄 Yangilash"
BTN_CLOSE = "❌ Yopish"

# Sozlamalar yangilandi xabarlari
SETTINGS_LANG_SET = "✅ Til yangilandi: <b>{lang}</b>"
SETTINGS_VOICE_SET = "✅ Ovoz yangilandi: <b>{voice}</b>"
SETTINGS_SPEED_SET = "✅ Tezlik yangilandi: <b>{speed}</b>"

# =============================================
# XATOLIK VA OGOHLANTIRISHLAR
# =============================================

ERR_EMPTY_TEXT = "⚠️ Matn topilmadi. Iltimos, qayta yozing."
ERR_NO_VOICE = "❌ Ovoz yaratib bo'lmadi. Birozdan so'ng qayta urinib ko'ring."
ERR_TTS_FAILED = "❌ Ovoz yaratishda xatolik yuz berdi. Qayta urinib ko'ring."
ERR_TOO_LONG = "⚠️ Matn juda uzun. Maksimal {max} belgi."
ERR_VOICE_TOO_LONG = (
    "⚠️ Ovoz juda uzun ({duration} s). Maksimal {max} soniya."
)
ERR_SCRIPT_PARSE = (
    "❌ Senariy qahramonlarini topa olmadim.\n"
    "Iltimos, senariyni 'Ism: matn' ko'rinishida jo'natib ko'ring."
)
ERR_SCRIPT_EMPTY = "❌ Senariyda hech qanday qahramon topilmadi."
ERR_DAILY_LIMIT = (
    "🚫 Bugungi bepul limit tugadi ({limit} ta so'rov).\n"
    "Ertaga qayta urinib ko'ring yoki premium o'qing."
)
ERR_UNKNOWN = "❌ Kutilmagan xatolik: {error}"
ERR_FILE_TOO_BIG = "⚠️ Fayl juda katta ({size} MB). Maksimal {max} MB."
ERR_FILE_TYPE = "❌ Bu fayl turini o'qiy olmayman. Qo'llab-quvvatlanadi: .txt, .pdf, .docx"
ERR_FILE_READ = "❌ Faylni o'qib bo'lmadi. Iltimos, boshqa fayl yuboring."
ERR_NOT_ADMIN = "🚫 Bu buyruq faqat adminlar uchun."

# =============================================
# PROGRESS VA STATUS
# =============================================

STATUS_TTS = "⏳ Ovoz yaratilmoqda..."
STATUS_SCRIPT_PARSE = "📜 Senariy tahlil qilinmoqda..."
STATUS_VOICE_HEARING = "🎤 Ovoz tinglanmoqda..."
STATUS_TRANSCRIBING = "⏳ Matnga aylantirilmoqda..."
STATUS_FILE_READING = "📄 Fayl o'qilmoqda..."
STATUS_CHUNK = "⏳ Ovoz yaratilmoqda ({current}/{total})..."
STATUS_GRANDPA = "👴 Grandpa effekti qo'llanmoqda..."

# =============================================
# MUVAFFAQIYAT XABARLARI
# =============================================

TTS_DONE = "🔊 {engine} • {lang} • {chars} belgi"
GRANDPA_DONE = "👴 Grandpa effekti • {chars} belgi"
SCRIPT_FOUND = "🎭 {count} ta qahramon topildi:\n{summary}"
SCRIPT_DONE = "✅ Tayyor! {count} ta ovozli xabar yuborildi. 🎉"
TRANSCRIPT = "🗣️ «{text}»\n\n🧠 Davom etilmoqda..."

# =============================================
# TARIX
# =============================================

HISTORY_HEADER = "📚 <b>Oxirgi matnlaringiz</b> (so'nggi {count} ta):\n"
HISTORY_EMPTY = "📚 Hozircha tarix yo'q. Matn yuboring!"

# =============================================
# INLINE REJIM
# =============================================

INLINE_NO_QUERY = "✏️ Matn yozing — ovozga aylantirib beraman."

# =============================================
# ADMIN PANEL
# =============================================

ADMIN_HEADER = "👑 <b>Admin Panel</b>\n"
ADMIN_STATS = (
    "👥 Foydalanuvchilar: <b>{users}</b>\n"
    "📊 Bugungi so'rovlar: <b>{today}</b>\n"
    "📈 Jami so'rovlar: <b>{total}</b>"
)
ADMIN_BROADCAST_PROMPT = (
    "📢 Broadcast rejimi. Yubormoqchi bo'lgan xabaringizni yozing.\n"
    "Bekor qilish uchun /cancel bosing."
)
ADMIN_BROADCAST_START = "📤 Broadcast boshlandi: {count} ta foydalanuvchi..."
ADMIN_BROADCAST_DONE = "✅ Broadcast tugadi. Yuborildi: {sent}/{total}"
ADMIN_CANCELLED = "❌ Broadcast bekor qilindi."

# =============================================
# BOSHQA
# =============================================

NOT_UNDERSTOOD = (
    "😊 Men hozircha <b>matn</b> va <b>ovozli xabar</b>lar bilan ishlayman.\n"
    "Matn yozing yoki mikrofon tugmasini bosib ovoz yuboring!"
)

AI_FALLBACK = (
    "Kechirasiz, AI bilan aloqa vaqtincha uzildi 😔. "
    "Birozdan keyin qayta yozing yoki /start bosing."
)

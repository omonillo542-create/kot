"""Test synthesize_speech() with Kokoro as primary."""
import asyncio
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Import from bot.py
sys.path.insert(0, os.path.dirname(__file__))

# We need to test the function without starting the bot
# So let's replicate the core logic
import aiohttp

KOKORO_API_URL = os.getenv("KOKORO_API_URL", "https://strive33-kokoro-tts-fastapi.hf.space/tts")
KOKORO_DEFAULT_VOICE = os.getenv("KOKORO_DEFAULT_VOICE", "af_heart")
KOKORO_SPEED = float(os.getenv("KOKORO_SPEED", "1.0"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

async def kokoro_tts(text, voice_id=None):
    voice = voice_id or KOKORO_DEFAULT_VOICE
    payload = {"text": text, "voice": voice, "speed": KOKORO_SPEED, "output_format": "wav"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(KOKORO_API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
                return data if len(data) > 100 else None
    except Exception as e:
        print(f"  Kokoro error: {e}")
        return None

async def fish_audio_tts(text, voice_id=None):
    if not OPENROUTER_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "fish-audio/s2.1-pro-free:free", "input": text, "response_format": "mp3"}
    if voice_id and voice_id != "default":
        payload["voice"] = voice_id
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://openrouter.ai/api/v1/audio/speech", headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
                return data if len(data) > 100 else None
    except:
        return None

async def synthesize_speech(text, lang="uz", voice_id=None):
    text = (text or "").strip()
    if not text:
        return None, ""
    order = ["kokoro"]
    if OPENROUTER_API_KEY:
        order.append("fish")
    for engine in order:
        if engine == "kokoro":
            audio = await kokoro_tts(text, voice_id)
            label = "Kokoro TTS"
        else:
            audio = await fish_audio_tts(text, voice_id)
            label = "Fish Audio"
        if audio:
            return audio, label
    return None, ""

async def main():
    print("=== synthesize_speech() Test ===\n")
    
    tests = [
        ("Assalomu alaykum! Bu test xabar.", None),
        ("Bugun juda chiroyli kun. Sayr qilishni maslahat beraman.", "am_michael"),
        ("Rahmat! Yana qo'ng'iroq qiling.", "af_bella"),
        ("Bu bolakay ovozi. Juda shirin.", "am_puck"),
    ]
    
    for text, voice in tests:
        print(f"Text: {text[:50]}...")
        print(f"Voice: {voice or 'default'}")
        audio, engine = await synthesize_speech(text, "uz", voice)
        if audio:
            print(f"  Engine: {engine}, Size: {len(audio)} bytes")
            # Save for listening
            fname = f"test_synth_{voice or 'default'}.wav"
            with open(fname, "wb") as f:
                f.write(audio)
            print(f"  Saved: {fname}")
        else:
            print(f"  FAILED!")
        print()

if __name__ == "__main__":
    asyncio.run(main())

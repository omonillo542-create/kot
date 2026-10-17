"""Kokoro TTS integration test — strive33 Space orqali."""
import asyncio
import aiohttp

KOKORO_API_URL = "https://strive33-kokoro-tts-fastapi.hf.space/tts"
KOKORO_DEFAULT_VOICE = "af_heart"

async def test_kokoro(text: str, voice: str = KOKORO_DEFAULT_VOICE):
    payload = {
        "text": text,
        "voice": voice,
        "speed": 1.0,
        "output_format": "wav",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            KOKORO_API_URL, json=payload,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            if resp.status != 200:
                err = await resp.text()
                print(f"  ERROR {resp.status}: {err[:200]}")
                return False
            data = await resp.read()
            print(f"  OK: {len(data)} bytes, voice={voice}")
            # Save test file
            fname = f"test_kokoro_{voice}.wav"
            with open(fname, "wb") as f:
                f.write(data)
            print(f"  Saved: {fname}")
            return True

async def main():
    print("=== Kokoro TTS Test (strive33 Space) ===\n")
    
    # Test 1: Default voice, Uzbek text
    print("Test 1: Uzbek text, af_heart")
    await test_kokoro("Assalomu alaykum! Menga ovozli xabar yuboring.")
    
    # Test 2: Male voice
    print("\nTest 2: Uzbek text, am_michael")
    await test_kokoro("Bugun havo juda chiroyli. Sayr qilishni maslahat beraman.", "am_michael")
    
    # Test 3: Another voice
    print("\nTest 3: Uzbek text, af_bella")
    await test_kokoro("Rahmat! Yana qo'ng'iroq qiling.", "af_bella")
    
    # Test 4: Health check
    print("\n=== Health Check ===")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://strive33-kokoro-tts-fastapi.hf.space/health",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"  Status: {data}")
            else:
                print(f"  ERROR: {resp.status}")

if __name__ == "__main__":
    asyncio.run(main())

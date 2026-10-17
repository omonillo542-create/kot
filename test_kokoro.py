"""Kokoro TTS serverni tekshirish va ovoz yaratish testi."""
import asyncio
import aiohttp

KOKORO_API_URL = "http://localhost:8880/v1/audio/speech"
KOKORO_VOICES_URL = "http://localhost:8880/v1/audio/voices"


async def check_server():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                KOKORO_VOICES_URL, timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    voices = data.get("voices", [])
                    print(f"Kokoro server RUNNING! {len(voices)} voices available")
                    for v in voices[:8]:
                        print("  -", v.get("id", "unknown"))
                    return True
                print("Server responded with", resp.status)
                return False
    except Exception as e:
        print("Kokoro server NOT running:", type(e).__name__, e)
        return False


async def synth_test():
    """Oddiy ovoz yaratish testi."""
    payload = {
        "model": "kokoro",
        "input": "Assalomu alaykum! Bu Kokoro TTS orqali o'zbekcha ovoz.",
        "voice": "af_heart",
        "response_format": "mp3",
        "speed": 1.0,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                KOKORO_API_URL, json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                print("Synth status:", resp.status)
                if resp.status == 200:
                    data = await resp.read()
                    print(f"Audio size: {len(data)} bytes")
                    with open("test_kokoro_uz.mp3", "wb") as f:
                        f.write(data)
                    print("Saved to test_kokoro_uz.mp3")
                    return True
                else:
                    text = await resp.text()
                    print("Error:", text[:300])
                    return False
    except Exception as e:
        print("Synth error:", type(e).__name__, e)
        return False


async def main():
    print("=== 1. Server check ===")
    running = await check_server()
    if running:
        print("\n=== 2. Uzbek TTS test ===")
        await synth_test()
    else:
        print("\nKokoro server ishlamayapti.")
        print("Ishga tushirish:")
        print("  docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest")
        print("  yoki")
        print("  docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi:latest")


if __name__ == "__main__":
    asyncio.run(main())

import os
import time
import asyncio
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kokoro TTS API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

model = None
pipelines = {}

# Only English pipelines (needed for Uzbek phonemization via espeak-ng fallback)
LANG_CODES = ["a", "b"]

def load_model():
    global model, pipelines
    try:
        from kokoro import KPipeline, KModel
        logger.info("Loading Kokoro model...")
        model = KModel(repo_id="hexgrad/Kokoro-82M").to("cpu").eval()
        for code in LANG_CODES:
            try:
                pipelines[code] = KPipeline(lang_code=code, model=False)
                logger.info(f"Pipeline '{code}' loaded")
            except Exception as e:
                logger.warning(f"Pipeline '{code}' failed: {e}")
        if "a" in pipelines:
            pipelines["a"].g2p.lexicon.golds["kokoro"] = "kˈOkəɹO"
        if "b" in pipelines:
            pipelines["b"].g2p.lexicon.golds["kokoro"] = "kˈQkəɹQ"
        logger.info(f"Model loaded. Pipelines: {list(pipelines.keys())}")
    except Exception as e:
        logger.error(f"Model load failed: {e}")

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model)

# Voice registry (English voices only)
VOICES = {
    # American English female
    "af_heart":   {"lang": "en-US", "gender": "female", "code": "a"},
    "af_bella":   {"lang": "en-US", "gender": "female", "code": "a"},
    "af_nicole":  {"lang": "en-US", "gender": "female", "code": "a"},
    "af_kore":    {"lang": "en-US", "gender": "female", "code": "a"},
    "af_sarah":   {"lang": "en-US", "gender": "female", "code": "a"},
    "af_nova":    {"lang": "en-US", "gender": "female", "code": "a"},
    "af_sky":     {"lang": "en-US", "gender": "female", "code": "a"},
    "af_river":   {"lang": "en-US", "gender": "female", "code": "a"},
    # American English male
    "am_michael": {"lang": "en-US", "gender": "male",   "code": "a"},
    "am_fenrir":  {"lang": "en-US", "gender": "male",   "code": "a"},
    "am_puck":    {"lang": "en-US", "gender": "male",   "code": "a"},
    "am_echo":    {"lang": "en-US", "gender": "male",   "code": "a"},
    "am_eric":    {"lang": "en-US", "gender": "male",   "code": "a"},
    "am_liam":    {"lang": "en-US", "gender": "male",   "code": "a"},
    "am_adam":    {"lang": "en-US", "gender": "male",   "code": "a"},
    # British English
    "bf_emma":     {"lang": "en-GB", "gender": "female", "code": "b"},
    "bf_isabella": {"lang": "en-GB", "gender": "female", "code": "b"},
    "bf_alice":    {"lang": "en-GB", "gender": "female", "code": "b"},
    "bf_lily":     {"lang": "en-GB", "gender": "female", "code": "b"},
    "bm_george":   {"lang": "en-GB", "gender": "male",   "code": "b"},
    "bm_fable":    {"lang": "en-GB", "gender": "male",   "code": "b"},
    "bm_lewis":    {"lang": "en-GB", "gender": "male",   "code": "b"},
    "bm_daniel":   {"lang": "en-GB", "gender": "male",   "code": "b"},
}

DEFAULT_VOICE = "af_heart"


def _synthesize(text: str, voice: str, speed: float) -> tuple[bytes, float]:
    """Generate WAV audio bytes."""
    if model is None:
        raise RuntimeError("Model not loaded")
    info = VOICES.get(voice, VOICES[DEFAULT_VOICE])
    pipeline = pipelines.get(info["code"])
    if not pipeline:
        raise RuntimeError("Pipeline not loaded")
    voice_pack = pipeline.load_voice(voice)
    chunks = []
    for _, ps, _ in pipeline(text, voice, speed, split_pattern=r"\n+"):
        ref_s = voice_pack[len(ps) - 1]
        chunks.append(model(ps, ref_s, speed).cpu().numpy())
    if not chunks:
        raise RuntimeError("No audio generated")
    audio = np.concatenate(chunks)
    duration = len(audio) / 24000
    buf = io.BytesIO()
    sf.write(buf, audio, 24000, format="WAV")
    return buf.getvalue(), duration


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None, "pipelines": list(pipelines.keys())}

@app.get("/v1/audio/voices")
async def list_voices():
    return {"voices": [{"id": k, **v} for k, v in VOICES.items()]}

# ── OpenAI-compatible endpoint ────────────────────────────────────────────────
class OpenAISpeechRequest(BaseModel):
    model: str = "kokoro"
    input: str
    voice: str = DEFAULT_VOICE
    response_format: str = "mp3"
    speed: float = 1.0

@app.post("/v1/audio/speech")
async def openai_speech(req: OpenAISpeechRequest):
    if not req.input.strip():
        raise HTTPException(400, "input cannot be empty")
    if model is None:
        raise HTTPException(503, "Model loading, retry shortly")
    if req.voice not in VOICES:
        req.voice = DEFAULT_VOICE
    speed = max(0.5, min(2.0, req.speed))
    try:
        loop = asyncio.get_event_loop()
        wav_bytes, duration = await loop.run_in_executor(
            None, lambda: _synthesize(req.input, req.voice, speed)
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(500, str(e))

    fmt = req.response_format or "mp3"
    if fmt == "wav":
        return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")
    # Convert WAV to MP3 via ffmpeg (subprocess)
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as inf:
        inf.write(wav_bytes)
        in_path = inf.name
    out_path = in_path.replace(".wav", ".mp3")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-codec:a", "libmp3lame", "-b:a", "128k", out_path],
            check=True, capture_output=True, timeout=30
        )
        with open(out_path, "rb") as f:
            mp3_bytes = f.read()
        return StreamingResponse(io.BytesIO(mp3_bytes), media_type="audio/mpeg")
    finally:
        os.unlink(in_path)
        if os.path.exists(out_path):
            os.unlink(out_path)


# ── Custom /tts endpoint (backward compat) ────────────────────────────────────
class TTSRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE
    speed: float = 1.0
    output_format: str = "wav"

@app.post("/tts")
async def tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(400, "text cannot be empty")
    if model is None:
        raise HTTPException(503, "Model loading")
    if req.voice not in VOICES:
        req.voice = DEFAULT_VOICE
    speed = max(0.5, min(2.0, req.speed))
    try:
        loop = asyncio.get_event_loop()
        wav_bytes, duration = await loop.run_in_executor(
            None, lambda: _synthesize(req.text, req.voice, speed)
        )
    except Exception as e:
        raise HTTPException(500, str(e))
    return StreamingResponse(
        io.BytesIO(wav_bytes),
        media_type="audio/wav" if req.output_format == "wav" else "audio/mpeg",
        headers={"X-Duration-Seconds": str(round(duration, 2))},
    )

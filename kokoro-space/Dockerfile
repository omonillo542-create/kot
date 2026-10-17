FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs curl ffmpeg espeak-ng libsndfile1 build-essential \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

COPY --chown=appuser:appuser main.py .

RUN mkdir -p /app/audio_output && chown -R appuser:appuser /app
USER appuser

# Pre-download model weights
RUN python -c "from kokoro import KModel; KModel(repo_id='hexgrad/Kokoro-82M')" || true

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]

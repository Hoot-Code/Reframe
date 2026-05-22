# ── ReFrame Bot — Dockerfile  |  creator: Hoot-Code ─────────────────────────
FROM python:3.12-slim

# Install FFmpeg + dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Temp dir for processing
RUN mkdir -p temp_media

CMD ["python", "main.py"]

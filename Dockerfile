FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates unzip curl && rm -rf /var/lib/apt/lists/*
# A JS runtime is needed by current yt-dlp YouTube extraction.
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
# Temporary trial: opt into yt-dlp's prerelease channel for YouTube extractor fixes.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --pre --upgrade "yt-dlp[default]"
COPY backend ./backend
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

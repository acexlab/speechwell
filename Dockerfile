FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SPEECHWELL_DATA_DIR=/var/data \
    SPEECHWELL_STORAGE_DIR=/var/data/storage \
    SQLITE_DB_PATH=/var/data/speechwell.db \
    XDG_CACHE_HOME=/var/data/.cache \
    HF_HOME=/var/data/.cache/huggingface \
    TORCH_HOME=/var/data/.cache/torch \
    NUMBA_CACHE_DIR=/tmp/numba-cache \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend ./backend
COPY ml ./ml

RUN mkdir -p /var/data/storage/uploaded_audio \
    /var/data/storage/processed_audio \
    /var/data/storage/reports \
    /var/data/.cache \
    /tmp/numba-cache \
    /tmp/matplotlib

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

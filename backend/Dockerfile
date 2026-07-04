# Pinned to 3.12 for reproducible builds (your local may be 3.14 — that's fine).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# App code
COPY . .

EXPOSE 8000

# Render/Railway inject $PORT; default to 8000 locally.
# Run DB migrations on startup, then launch the server (safe on a single instance).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

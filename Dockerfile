# Multi-stage build: build wheels in builder (python:3.11) then install in slim runtime
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps required for compiling C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libssl-dev libffi-dev pkg-config \
    libtool autoconf automake make file python3-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Build wheels for all requirements to avoid rebuilding on runtime
RUN python -m pip install --upgrade pip wheel setuptools \
    && python -m pip wheel --wheel-dir=/wheels -r /app/requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 procps ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-index --find-links=/wheels -r /app/requirements.txt

# Copy application files
COPY --chown=appuser:appuser . /app

# If no .env exists in the image, create one from .env.example so Settings can load.
# This is a convenience for deployments where env vars are passed via environment
# (Railway) — remove or adjust if you prefer not to bake secrets into the image.
RUN if [ ! -f /app/.env ] && [ -f /app/.env.example ]; then cp /app/.env.example /app/.env; fi

RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD pgrep -f "python -u main.py" > /dev/null || exit 1

ENTRYPOINT ["python", "-u", "main.py"]

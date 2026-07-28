FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install minimal build deps required by some packages (asyncpg / psycopg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage layer caching
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application
COPY . /app

# Create unprivileged user and fix permissions
RUN useradd --create-home app || true \
    && chown -R app:app /app

USER app

CMD ["python", "main.py"]
# syntax=docker/dockerfile:1

# ==================== Build stage ====================
FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==================== Runtime stage ====================
FROM python:3.13-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        procps \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY . .

RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD pgrep -f "python -u main.py" > /dev/null || exit 1

ENTRYPOINT ["python", "-u", "main.py"]

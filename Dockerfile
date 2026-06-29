# ─────────────────────────────────────────────
# Stage 1: Builder
# Sirf dependencies install karo
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies (PostgreSQL client for wait_for_db.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencies pehle copy karo (caching ke liye)
COPY requirements.txt .

# Ek folder mein install karo
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2: Final Image
# Sirf jo chahiye woh lo, baaki chhodo
# ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Builder se sirf installed packages lo
COPY --from=builder /install /usr/local

# Non-root user banao (security)
RUN useradd --create-home --shell /bin/bash appuser

# Application code copy karo
COPY --chown=appuser:appuser . .

# wait_for_db.sh ko executable banao
RUN chmod +x scripts/wait_for_db.sh

# Non-root user switch karo
USER appuser

# Port expose karo
EXPOSE 5000

# Environment variables
ENV FLASK_ENV=production \
    PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Health check — Docker khud check karega
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entry point — DB wait karo, migrations chalaao, phir gunicorn
ENTRYPOINT ["scripts/wait_for_db.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
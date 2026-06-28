#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# TaskFlow API — Wait for PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────
# Blocks until PostgreSQL is accepting connections, then executes the command
# passed as arguments.
#
# DevOps usage (Docker ENTRYPOINT / CMD):
#   ENTRYPOINT ["./scripts/wait_for_db.sh"]
#   CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
#
# This solves the Docker Compose race condition where the app container
# starts before PostgreSQL is ready to accept connections.
#
# Requires: postgresql-client (pg_isready)
# Install in Dockerfile: apt-get install -y postgresql-client
#
# Environment variables used (must match your DATABASE_URL):
#   DB_HOST    (default: localhost)
#   DB_PORT    (default: 5432)
#   DB_USER    (default: taskflow)
#   DB_NAME    (default: taskflow)
#   DB_MAX_WAIT_SECONDS (default: 60)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-taskflow}"
DB_NAME="${DB_NAME:-taskflow}"
MAX_WAIT="${DB_MAX_WAIT_SECONDS:-60}"

ELAPSED=0
INTERVAL=2

echo "⏳ Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} (timeout: ${MAX_WAIT}s)..."

until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -q; do
    if [ "${ELAPSED}" -ge "${MAX_WAIT}" ]; then
        echo "❌ PostgreSQL not ready after ${MAX_WAIT}s. Aborting."
        exit 1
    fi

    echo "   PostgreSQL is unavailable — retrying in ${INTERVAL}s (${ELAPSED}s elapsed)..."
    sleep "${INTERVAL}"
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "✅ PostgreSQL is ready at ${DB_HOST}:${DB_PORT}"
echo ""

# ── Run Database Migrations ────────────────────────────────────────────────────
# Apply any pending migrations before starting the application.
# This makes zero-downtime rolling deploys safe:
#   - Migrations must be backward-compatible (new columns nullable, etc.)
#   - Old app version continues running while new version migrates

echo "📦 Running database migrations..."
flask db upgrade
echo "✅ Migrations complete"
echo ""

# ── Execute the given command ──────────────────────────────────────────────────
# Replace this script process with the app server (exec = no extra PID)
# This ensures signals (SIGTERM) go directly to gunicorn, not to bash.

echo "🚀 Starting: $*"
exec "$@"

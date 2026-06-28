# ─────────────────────────────────────────────────────────────────────────────
# TaskFlow API — Developer Makefile
# Usage: make <target>
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help install dev-install run run-prod test test-cov lint format \
        db-init db-migrate db-upgrade db-downgrade seed clean

# Default target
help:
	@echo ""
	@echo "TaskFlow API — Available Commands"
	@echo "──────────────────────────────────────────"
	@echo "  make install       Install production dependencies"
	@echo "  make dev-install   Install all dependencies (inc. dev/test)"
	@echo "  make run           Start Flask dev server (hot reload)"
	@echo "  make run-prod      Start Gunicorn production server"
	@echo "  make test          Run all tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Check code style (flake8 + isort)"
	@echo "  make format        Auto-format code (black + isort)"
	@echo "  make db-init       Initialise Flask-Migrate (first time only)"
	@echo "  make db-migrate    Generate migration (use: make db-migrate msg='description')"
	@echo "  make db-upgrade    Apply pending migrations"
	@echo "  make db-downgrade  Revert last migration"
	@echo "  make seed          Seed database with sample data"
	@echo "  make clean         Remove cache files and build artifacts"
	@echo ""

# ── Dependencies ──────────────────────────────────────────────────────────────

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt

# ── Running ───────────────────────────────────────────────────────────────────

run:
	FLASK_ENV=development FLASK_APP=wsgi.py flask run --host=0.0.0.0 --port=5000 --debug

run-prod:
	gunicorn -c gunicorn.conf.py wsgi:app

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	FLASK_ENV=testing pytest tests/ -v

test-unit:
	FLASK_ENV=testing pytest tests/unit/ -v

test-integration:
	FLASK_ENV=testing pytest tests/integration/ -v

test-cov:
	FLASK_ENV=testing pytest tests/ -v \
		--cov=app \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-fail-under=70
	@echo "Coverage report: htmlcov/index.html"

# ── Code Quality ──────────────────────────────────────────────────────────────

lint:
	flake8 app/ tests/ --max-line-length=100 --exclude=migrations/
	isort --check-only --diff app/ tests/

format:
	black app/ tests/ scripts/ --line-length=100
	isort app/ tests/ scripts/

# ── Database ──────────────────────────────────────────────────────────────────

db-init:
	FLASK_APP=wsgi.py flask db init

db-migrate:
	FLASK_APP=wsgi.py flask db migrate -m "$(msg)"

db-upgrade:
	FLASK_APP=wsgi.py flask db upgrade

db-downgrade:
	FLASK_APP=wsgi.py flask db downgrade

db-history:
	FLASK_APP=wsgi.py flask db history

seed:
	FLASK_ENV=development python scripts/seed_data.py

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "*.egg-info" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete
	@echo "✅ Cleaned"

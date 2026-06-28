"""
TaskFlow API — Flask Extensions
─────────────────────────────────────────────────────────────────────────────
All extensions are created here WITHOUT an app instance (application factory
pattern). They are bound to the app inside create_app() via .init_app(app).

This prevents circular imports and allows multiple app instances (testing).
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics

# ── Core ───────────────────────────────────────────────────────────────────────
db = SQLAlchemy()
migrate = Migrate()

# ── Authentication ─────────────────────────────────────────────────────────────
jwt = JWTManager()

# ── Rate Limiting ──────────────────────────────────────────────────────────────
# key_func determines who gets rate-limited (by IP address)
# In production behind Nginx, use get_remote_address with proper X-Forwarded-For
limiter = Limiter(key_func=get_remote_address)

# ── CORS ───────────────────────────────────────────────────────────────────────
cors = CORS()

# ── Observability ──────────────────────────────────────────────────────────────
# PrometheusMetrics.for_app_factory() supports the application factory pattern.
# It registers /metrics endpoint automatically.
# DevOps: point your Prometheus scrape config at /metrics
metrics = PrometheusMetrics.for_app_factory()

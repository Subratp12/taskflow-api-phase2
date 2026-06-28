"""
TaskFlow API — API v1 Blueprint
─────────────────────────────────────────────────────────────────────────────
Parent blueprint for all /api/v1/* routes.
Each feature area has its own child blueprint registered here.

Adding a new API group in Phase 3:
    1. Create app/api/v1/feature/__init__.py with Blueprint('feature', ...)
    2. Import and register it here
    3. Done — it inherits /api/v1 prefix automatically
"""

from flask import Blueprint

api_v1_bp = Blueprint('api_v1', __name__)

# ── Register Child Blueprints ──────────────────────────────────────────────────
from .auth import auth_bp          # noqa: E402
from .users import users_bp        # noqa: E402
from .projects import projects_bp  # noqa: E402
from .tasks import tasks_bp        # noqa: E402
from .comments import comments_bp  # noqa: E402

api_v1_bp.register_blueprint(auth_bp)
api_v1_bp.register_blueprint(users_bp)
api_v1_bp.register_blueprint(projects_bp)
api_v1_bp.register_blueprint(tasks_bp)
api_v1_bp.register_blueprint(comments_bp)

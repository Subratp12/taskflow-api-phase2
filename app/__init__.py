"""
TaskFlow API — Application Factory
─────────────────────────────────────────────────────────────────────────────
create_app() is the single entry point for building the Flask application.
Every environment (dev, staging, prod, test) calls this function.

Design decisions:
  - Application factory pattern prevents circular imports
  - Extensions are initialized here, not at module level
  - Error handlers return consistent JSON (never HTML)
  - Graceful shutdown: SIGTERM → Gunicorn drains, Flask closes cleanly
"""

import os
import signal
import logging

from flask import Flask, jsonify, g, request

from .config import config
from .extensions import cors, db, jwt, limiter, metrics, migrate
from .utils.logger import setup_logging


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'staging', 'production', 'testing'.
                     Falls back to FLASK_ENV env var, then 'development'.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, instance_relative_config=False)

    # ── Load Configuration ─────────────────────────────────────────────────────
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)

    # Fail fast in production if secrets are not set
    if config_name == 'production' and hasattr(config_class, 'validate'):
        config_class.validate()

    # ── Structured Logging ─────────────────────────────────────────────────────
    setup_logging(app)
    app.logger.info(
        "Initializing TaskFlow API",
        extra={'env': config_name, 'version': app.config['APP_VERSION']},
    )

    # ── Initialize Extensions ──────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}},
        supports_credentials=True,
    )
    metrics.init_app(app)

    # ── Register Middleware ────────────────────────────────────────────────────
    _register_middleware(app)

    # ── Register Blueprints ────────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Register Error Handlers ────────────────────────────────────────────────
    _register_error_handlers(app)

    # ── Register JWT Callbacks ─────────────────────────────────────────────────
    _register_jwt_callbacks(app)

    # ── Shell Context (flask shell) ────────────────────────────────────────────
    _register_shell_context(app)

    # ── Graceful Shutdown ──────────────────────────────────────────────────────
    _register_shutdown_handlers(app)

    app.logger.info("TaskFlow API ready", extra={'env': config_name})
    return app


# ── Private Setup Functions ────────────────────────────────────────────────────

def _register_middleware(app: Flask) -> None:
    """Register request/response middleware."""
    from .middleware.correlation_id import init_correlation_id
    from .middleware.security_headers import init_security_headers

    init_correlation_id(app)
    init_security_headers(app)


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    # System endpoints (health, ready) — no auth, no /api/v1 prefix
    from .api.v1.system import system_bp
    app.register_blueprint(system_bp)

    # Business logic API — all under /api/v1
    from .api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')


def _register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for all HTTP errors."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'success': False, 'error': {'code': 400, 'message': str(e.description)}}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'success': False, 'error': {'code': 401, 'message': 'Authentication required'}}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'success': False, 'error': {'code': 403, 'message': 'Access denied'}}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'error': {'code': 404, 'message': f'Resource not found: {request.path}'}}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'error': {'code': 405, 'message': f'Method {request.method} not allowed'}}), 405

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({'success': False, 'error': {'code': 409, 'message': str(e.description)}}), 409

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({'success': False, 'error': {'code': 422, 'message': str(e.description)}}), 422

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({'success': False, 'error': {'code': 429, 'message': 'Too many requests. Slow down.'}}), 429

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Internal server error", extra={'error': str(e), 'path': request.path})
        return jsonify({'success': False, 'error': {'code': 500, 'message': 'Internal server error'}}), 500

    @app.errorhandler(503)
    def service_unavailable(e):
        return jsonify({'success': False, 'error': {'code': 503, 'message': 'Service temporarily unavailable'}}), 503


def _register_jwt_callbacks(app: Flask) -> None:
    """
    Register JWT error callbacks.
    All JWT errors return consistent JSON responses.
    """
    from .extensions import jwt as _jwt

    @_jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({'success': False, 'error': {'code': 401, 'message': 'Token has expired'}}), 401

    @_jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'success': False, 'error': {'code': 401, 'message': 'Invalid token'}}), 401

    @_jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'success': False, 'error': {'code': 401, 'message': 'Authorization token required'}}), 401

    @_jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_data):
        return jsonify({'success': False, 'error': {'code': 401, 'message': 'Token has been revoked'}}), 401

    @_jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_data):
        return jsonify({'success': False, 'error': {'code': 401, 'message': 'Fresh token required'}}), 401


def _register_shell_context(app: Flask) -> None:
    """Expose models and db in `flask shell` for debugging."""
    @app.shell_context_processor
    def make_shell_context():
        from .models import User, Project, ProjectMember, Task, Comment, ActivityLog
        return {
            'db': db,
            'User': User,
            'Project': Project,
            'ProjectMember': ProjectMember,
            'Task': Task,
            'Comment': Comment,
            'ActivityLog': ActivityLog,
        }


def _register_shutdown_handlers(app: Flask) -> None:
    """
    Handle SIGTERM gracefully.
    Gunicorn sends SIGTERM when shutting down. This gives us a chance to
    log the shutdown and allow in-flight DB transactions to complete.
    """
    def graceful_shutdown(signum, frame):
        app.logger.info("SIGTERM received — shutting down gracefully")
        # SQLAlchemy connection pool closes automatically when the process ends
        # Gunicorn's graceful_timeout controls the window for in-flight requests

    signal.signal(signal.SIGTERM, graceful_shutdown)

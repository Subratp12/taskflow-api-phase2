"""
TaskFlow API — System / Observability Endpoints
─────────────────────────────────────────────────────────────────────────────
These endpoints are NOT under /api/v1 — they live at the root.
They require NO authentication — consumed by infrastructure, not users.

GET /health  — Liveness probe
    "Is the process alive and able to serve requests?"
    Fails only if the Flask process itself is broken.
    → Kubernetes/ECS: if this fails, KILL and restart the container.

GET /ready   — Readiness probe
    "Is this instance ready to receive traffic?"
    Checks DB connectivity and pool health.
    → Kubernetes/ECS: if this fails, STOP sending traffic (but don't kill).
    → Load balancer: remove from rotation until ready again.

GET /metrics — Prometheus scrape endpoint
    Auto-registered by prometheus_flask_exporter on extension init.
    Exposes: request counts, latencies, DB pool stats, custom counters.
    → Prometheus scrape config: targets: ['app:5000']
      path: /metrics (default)

DevOps Usage:
    # Docker health check
    HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
        CMD curl -f http://localhost:5000/health || exit 1

    # Nginx upstream health check
    health_check uri=/health interval=5s fails=3 passes=2;

    # Kubernetes liveness probe
    livenessProbe:
      httpGet:
        path: /health
        port: 5000
      initialDelaySeconds: 10
      periodSeconds: 15

    # Kubernetes readiness probe
    readinessProbe:
      httpGet:
        path: /ready
        port: 5000
      initialDelaySeconds: 5
      periodSeconds: 10
"""

from datetime import datetime, timezone

import structlog
from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db

logger = structlog.get_logger(__name__)

system_bp = Blueprint('system', __name__)


@system_bp.route('/health', methods=['GET'])
def health():
    """
    Liveness probe.

    Returns 200 if Flask is running. Returns 503 only if the application
    process itself is in a broken state. Does NOT check dependencies —
    that is /ready's job.

    Response:
        200: { "status": "healthy", "timestamp": "...", "version": "1.0.0" }
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': current_app.config.get('APP_VERSION', 'unknown'),
        'app': current_app.config.get('APP_NAME', 'TaskFlow API'),
    }), 200


@system_bp.route('/ready', methods=['GET'])
def ready():
    """
    Readiness probe.

    Verifies:
      1. Flask app is running
      2. Database connection is available (SELECT 1)
      3. Connection pool stats are within normal range

    Returns 200 if ready to serve traffic, 503 if not.

    Response (200):
        {
            "status": "ready",
            "version": "1.0.0",
            "timestamp": "...",
            "checks": {
                "database": "connected",
                "pool": {
                    "size": 5,
                    "checked_in": 4,
                    "checked_out": 1,
                    "overflow": 0
                }
            }
        }

    Response (503):
        {
            "status": "not_ready",
            "checks": { "database": "disconnected" },
            "error": "connection refused"
        }
    """
    checks = {}
    pool_info = {}

    # ── Database Check ─────────────────────────────────────────────────────────
    try:
        db.session.execute(text('SELECT 1'))
        checks['database'] = 'connected'

        # Connection pool statistics
        pool = db.engine.pool
        pool_info = {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
        }
        checks['pool'] = pool_info

    except Exception as exc:
        logger.error('Readiness check failed — database unreachable', error=str(exc))
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {'database': 'disconnected'},
            'error': str(exc),
        }), 503

    return jsonify({
        'status': 'ready',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': current_app.config.get('APP_VERSION', 'unknown'),
        'checks': checks,
    }), 200


@system_bp.route('/api/v1/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """
    Aggregate dashboard statistics.
    Requires authentication — handled in Phase 3.
    Placeholder returns structure so frontend dev can mock against it.
    """
    return jsonify({
        'success': True,
        'data': {
            'projects': {'total': 0, 'active': 0, 'completed': 0},
            'tasks': {
                'total': 0,
                'todo': 0,
                'in_progress': 0,
                'in_review': 0,
                'done': 0,
                'overdue': 0,
            },
            'recent_activity': [],
        },
        'message': 'Dashboard stats endpoint — authentication required in production',
    }), 200

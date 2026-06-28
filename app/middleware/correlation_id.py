"""
TaskFlow API — Correlation ID Middleware
─────────────────────────────────────────────────────────────────────────────
Every HTTP request gets an X-Correlation-ID header. This ID flows through:
    Client → Nginx → Flask → Logs → Response headers

If the client sends X-Correlation-ID, we reuse it (so frontend and backend
logs can be correlated for the same user action).
If not, we generate a new UUID.

DevOps:
    - Nginx should be configured to pass X-Correlation-ID upstream
    - Log aggregators (CloudWatch, Datadog) should index on correlation_id
    - When debugging an incident, search all logs by correlation_id
      to get the full trace of a single request across services
"""

import uuid

import structlog
from flask import Flask, g, request


def init_correlation_id(app: Flask) -> None:
    """Register correlation ID before/after request hooks."""

    @app.before_request
    def set_correlation_id() -> None:
        """
        Extract or generate correlation ID and store in Flask g.
        Also bind it to structlog's context so every log line includes it.
        """
        correlation_id = (
            request.headers.get('X-Correlation-ID')
            or request.headers.get('X-Request-ID')
            or str(uuid.uuid4())
        )
        g.correlation_id = correlation_id

        # Bind to structlog context — persists for the lifetime of this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    @app.after_request
    def add_correlation_id_header(response):
        """Echo the correlation ID back in the response so clients can log it."""
        response.headers['X-Correlation-ID'] = getattr(
            g, 'correlation_id', str(uuid.uuid4())
        )
        return response

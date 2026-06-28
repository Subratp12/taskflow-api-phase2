"""
TaskFlow API — Structured Logging
─────────────────────────────────────────────────────────────────────────────
Configures structlog to emit JSON on stdout.

Why JSON logging?
  - CloudWatch, Datadog, Splunk, Loki — all ingest JSON natively
  - No regex parsing needed
  - Correlation IDs, user IDs, request paths are first-class fields
  - grep + jq work perfectly in local dev

Every log line looks like:
{
    "timestamp": "2024-01-15T10:30:00.123456Z",
    "level": "info",
    "event": "Task created",
    "correlation_id": "abc-123",
    "user_id": "uuid-here",
    "task_id": "uuid-here",
    "logger": "app.api.v1.tasks"
}

Usage in routes/services:
    import structlog
    logger = structlog.get_logger(__name__)
    logger.info("Task created", task_id=str(task.id), user_id=str(user.id))
    logger.warning("Permission denied", user_id=str(user.id), project_id=str(project.id))
    logger.error("Database error", error=str(e), query="...")
"""

import logging
import sys

import structlog
from flask import Flask, g, has_request_context, request


def _add_logger_name(logger, method, event_dict: dict) -> dict:
    """
    Processor: add logger name to event dict.
    Handles both stdlib loggers (have .name) and structlog PrintLogger (don't).
    """
    if hasattr(logger, 'name'):
        event_dict['logger'] = logger.name
    elif hasattr(logger, '_name'):
        event_dict['logger'] = logger._name
    return event_dict


def _add_request_context(logger, method, event_dict: dict) -> dict:
    """
    Processor: inject HTTP request context into every log record.
    Only runs when inside a Flask request context.
    """
    if has_request_context():
        event_dict['correlation_id'] = getattr(g, 'correlation_id', None)
        event_dict['http_method'] = request.method
        event_dict['path'] = request.path
        event_dict['remote_addr'] = request.remote_addr
    return event_dict


def setup_logging(app: Flask) -> None:
    """
    Configure structlog and standard library logging.
    Called once from create_app().
    """
    log_level_name = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # ── Standard Library Logging ───────────────────────────────────────────────
    # Route all stdlib logging through structlog
    logging.basicConfig(
        format='%(message)s',     # structlog renders the full JSON string
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # Suppress noisy libraries in production
    if log_level_name != 'DEBUG':
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # ── structlog Pipeline ─────────────────────────────────────────────────────
    structlog.configure(
        processors=[
            # Merge bound context vars (e.g. bind correlation_id once, use everywhere)
            structlog.contextvars.merge_contextvars,
            # Add log level as a field
            structlog.stdlib.add_log_level,
            # Add logger name (safe for PrintLogger)
            _add_logger_name,
            # Inject request context
            _add_request_context,
            # ISO 8601 timestamp
            structlog.processors.TimeStamper(fmt='iso', utc=True),
            # Render stack traces as strings (not raw objects)
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Final render: JSON string
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # ── Flask App Logger ───────────────────────────────────────────────────────
    # Make Flask's app.logger use our structlog setup
    app.logger.handlers.clear()
    app.logger.propagate = True
    app.logger.setLevel(log_level)

    structlog.get_logger('app').info(
        'Logging initialised',
        level=log_level_name,
        format='json',
    )

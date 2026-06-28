"""
TaskFlow API — Utility Helpers
─────────────────────────────────────────────────────────────────────────────
Shared utilities used across routes and services.
"""

import re
import uuid
from datetime import date, datetime
from typing import Any

from flask import current_app, request


# ── Pagination ─────────────────────────────────────────────────────────────────

def get_pagination_params() -> tuple[int, int]:
    """
    Extract and validate pagination query params from the current request.

    Returns:
        (page, per_page) tuple — both are guaranteed to be positive integers
        within configured limits.

    Usage:
        page, per_page = get_pagination_params()
        tasks = Task.query.paginate(page=page, per_page=per_page)
    """
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(
            max(1, int(request.args.get('per_page', current_app.config['DEFAULT_PAGE_SIZE']))),
            current_app.config['MAX_PAGE_SIZE'],
        )
    except (ValueError, TypeError):
        per_page = current_app.config['DEFAULT_PAGE_SIZE']

    return page, per_page


# ── UUID Validation ────────────────────────────────────────────────────────────

def is_valid_uuid(value: Any) -> bool:
    """Return True if value is a valid UUID string."""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def parse_uuid(value: Any) -> uuid.UUID | None:
    """Parse a UUID string into a UUID object. Returns None if invalid."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return None


# ── Date Helpers ───────────────────────────────────────────────────────────────

def parse_date(value: str | None) -> date | None:
    """
    Parse an ISO 8601 date string (YYYY-MM-DD) into a date object.
    Returns None if value is None or invalid.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def format_date(value: date | None) -> str | None:
    """Format a date object to ISO 8601 string."""
    return value.isoformat() if value else None


# ── String Sanitization ────────────────────────────────────────────────────────

def sanitize_string(value: str | None, max_length: int | None = None) -> str | None:
    """Strip whitespace and optionally truncate a string."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned or None


def is_safe_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


# ── Query Filter Helpers ───────────────────────────────────────────────────────

def get_enum_filter(param_name: str, enum_class) -> Any | None:
    """
    Extract and validate an enum value from query params.

    Usage:
        status = get_enum_filter('status', TaskStatus)
        if status:
            query = query.filter(Task.status == status)
    """
    value = request.args.get(param_name)
    if not value:
        return None
    try:
        return enum_class(value)
    except ValueError:
        return None


# ── Request Helpers ────────────────────────────────────────────────────────────

def get_json_body() -> dict:
    """
    Safely get JSON body from request.
    Returns empty dict if body is missing or invalid JSON.
    """
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}

"""
TaskFlow API — Response Helpers
─────────────────────────────────────────────────────────────────────────────
All API responses use a consistent JSON envelope:

Success:
    {
        "success": true,
        "data": { ... },
        "message": "Optional human-readable message",
        "meta": { "page": 1, "total": 50, ... }   ← pagination only
    }

Error:
    {
        "success": false,
        "error": {
            "code": 400,
            "message": "Human-readable error",
            "details": { ... }   ← validation errors, optional
        }
    }

This consistency means the frontend and monitoring tools can
always trust the shape of every response.
"""

from typing import Any

from flask import jsonify


def success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = 200,
    meta: dict | None = None,
):
    """
    Standard success response.

    Args:
        data:        Payload to return (dict, list, or None)
        message:     Optional human-readable message
        status_code: HTTP status code (default 200)
        meta:        Pagination or other metadata

    Returns:
        Flask JSON response tuple
    """
    body: dict = {'success': True}
    if message:
        body['message'] = message
    if data is not None:
        body['data'] = data
    if meta:
        body['meta'] = meta
    return jsonify(body), status_code


def created_response(data: Any = None, message: str = 'Resource created successfully'):
    """Convenience wrapper for 201 Created."""
    return success_response(data=data, message=message, status_code=201)


def no_content_response():
    """204 No Content — used for successful DELETE requests."""
    return '', 204


def error_response(
    message: str,
    status_code: int = 400,
    details: dict | list | None = None,
):
    """
    Standard error response.

    Args:
        message:     Human-readable error message
        status_code: HTTP status code
        details:     Optional validation errors or extra context

    Returns:
        Flask JSON response tuple
    """
    error: dict = {
        'code': status_code,
        'message': message,
    }
    if details:
        error['details'] = details
    return jsonify({'success': False, 'error': error}), status_code


def validation_error_response(errors: dict):
    """422 Unprocessable Entity — marshmallow validation failed."""
    return error_response(
        message='Validation failed',
        status_code=422,
        details=errors,
    )


def not_found_response(resource: str = 'Resource'):
    """404 Not Found."""
    return error_response(f'{resource} not found', 404)


def forbidden_response(message: str = 'Access denied'):
    """403 Forbidden."""
    return error_response(message, 403)


def paginated_response(
    data: list,
    page: int,
    per_page: int,
    total: int,
    status_code: int = 200,
):
    """
    Paginated list response with metadata.

    Usage:
        return paginated_response(
            data=[task.to_dict() for task in tasks],
            page=page,
            per_page=per_page,
            total=total,
        )
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    meta = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
    }
    return success_response(data=data, meta=meta, status_code=status_code)

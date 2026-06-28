"""
TaskFlow API — Security Headers Middleware
─────────────────────────────────────────────────────────────────────────────
Adds OWASP-recommended HTTP security headers to every response.

These headers harden the API against common web vulnerabilities even when
the app is accessed directly (before Nginx adds its own headers).

DevOps note:
    Nginx should add these headers as well (defence in depth).
    Some of these (HSTS, CSP) are more relevant when serving a frontend.
    For a pure API, they're still best practice.
"""

from flask import Flask


def init_security_headers(app: Flask) -> None:
    """Register security header injection after each request."""

    @app.after_request
    def add_security_headers(response):
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # XSS protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # HTTPS only — Nginx/load balancer enforces TLS, this tells browsers
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )

        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Prevent caching of API responses (contains sensitive data)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'

        # Permissions Policy — disable unused browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )

        # Remove server fingerprint
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)

        # CORS headers are handled by Flask-CORS, not here
        return response

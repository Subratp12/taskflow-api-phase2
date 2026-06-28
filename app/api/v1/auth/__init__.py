"""
TaskFlow API — Auth Blueprint
─────────────────────────────────────────────────────────────────────────────
Routes implemented in Phase 3:
    POST /api/v1/auth/register    Create account
    POST /api/v1/auth/login       Login → access + refresh tokens
    POST /api/v1/auth/refresh     Refresh access token
    POST /api/v1/auth/logout      Revoke refresh token
"""

from flask import Blueprint, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Phase 3 — User registration."""
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@auth_bp.route('/login', methods=['POST'])
def login():
    """Phase 3 — Login and receive JWT tokens."""
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Phase 3 — Refresh access token using refresh token."""
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Phase 3 — Revoke refresh token."""
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501

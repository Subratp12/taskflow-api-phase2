"""
TaskFlow API — Users Blueprint
─────────────────────────────────────────────────────────────────────────────
Routes implemented in Phase 3:
    GET    /api/v1/users          List users (admin only)
    GET    /api/v1/users/me       Get own profile
    PUT    /api/v1/users/me       Update own profile
    GET    /api/v1/users/:id      Get user by ID
    DELETE /api/v1/users/:id      Deactivate user (admin only)
"""

from flask import Blueprint, jsonify

users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('', methods=['GET'])
def list_users():
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@users_bp.route('/me', methods=['GET'])
def get_me():
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@users_bp.route('/me', methods=['PUT'])
def update_me():
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@users_bp.route('/<string:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@users_bp.route('/<string:user_id>', methods=['DELETE'])
def deactivate_user(user_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501

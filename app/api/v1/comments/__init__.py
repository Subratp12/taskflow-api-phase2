"""
TaskFlow API — Comments Blueprint
─────────────────────────────────────────────────────────────────────────────
Routes implemented in Phase 3:
    PUT    /api/v1/comments/:id    Edit own comment
    DELETE /api/v1/comments/:id    Delete comment (own or admin)
"""

from flask import Blueprint, jsonify

comments_bp = Blueprint('comments', __name__, url_prefix='/comments')


@comments_bp.route('/<string:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@comments_bp.route('/<string:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501

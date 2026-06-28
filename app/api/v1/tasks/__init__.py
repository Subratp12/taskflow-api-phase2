"""
TaskFlow API — Tasks Blueprint
─────────────────────────────────────────────────────────────────────────────
Routes implemented in Phase 3:
    GET    /api/v1/tasks/:id              Get task detail
    PUT    /api/v1/tasks/:id              Update task
    DELETE /api/v1/tasks/:id              Delete task
    PATCH  /api/v1/tasks/:id/status       Update status only
    PATCH  /api/v1/tasks/:id/assign       Assign/unassign task
    GET    /api/v1/tasks/:id/comments     List task comments
    POST   /api/v1/tasks/:id/comments     Add comment
"""

from flask import Blueprint, jsonify

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@tasks_bp.route('/<string:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@tasks_bp.route('/<string:task_id>', methods=['PUT'])
def update_task(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@tasks_bp.route('/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@tasks_bp.route('/<string:task_id>/status', methods=['PATCH'])
def update_status(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@tasks_bp.route('/<string:task_id>/assign', methods=['PATCH'])
def assign_task(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@tasks_bp.route('/<string:task_id>/comments', methods=['GET'])
def list_comments(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@tasks_bp.route('/<string:task_id>/comments', methods=['POST'])
def add_comment(task_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501

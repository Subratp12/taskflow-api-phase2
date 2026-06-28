"""
TaskFlow API — Projects Blueprint
─────────────────────────────────────────────────────────────────────────────
Routes implemented in Phase 3:
    GET    /api/v1/projects                     List projects
    POST   /api/v1/projects                     Create project
    GET    /api/v1/projects/:id                 Get project detail
    PUT    /api/v1/projects/:id                 Update project
    DELETE /api/v1/projects/:id                 Delete project
    GET    /api/v1/projects/:id/members         List members
    POST   /api/v1/projects/:id/members         Add member
    DELETE /api/v1/projects/:id/members/:uid    Remove member
    GET    /api/v1/projects/:id/activity        Project activity feed
"""

from flask import Blueprint, jsonify

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('', methods=['GET'])
def list_projects():
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('', methods=['POST'])
def create_project():
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>', methods=['GET'])
def get_project(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>', methods=['PUT'])
def update_project(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>', methods=['DELETE'])
def delete_project(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>/members', methods=['GET'])
def list_members(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>/members', methods=['POST'])
def add_member(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>/members/<string:user_id>', methods=['DELETE'])
def remove_member(project_id, user_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>/activity', methods=['GET'])
def project_activity(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>/tasks', methods=['GET'])
def list_tasks(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501


@projects_bp.route('/<string:project_id>/tasks', methods=['POST'])
def create_task(project_id):
    return jsonify({'message': 'Phase 3 — not yet implemented'}), 501

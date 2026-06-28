"""
TaskFlow API — Project Schemas
─────────────────────────────────────────────────────────────────────────────
Marshmallow schemas for Project and ProjectMember validation and serialization.
"""

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema


class ProjectCreateSchema(Schema):
    """POST /projects — create a new project."""

    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200, error='Project name must be 1–200 characters'),
    )
    description = fields.Str(
        load_default=None,
        validate=validate.Length(max=5000),
    )
    status = fields.Str(
        load_default='planning',
        validate=validate.OneOf(
            ['planning', 'active', 'on_hold', 'completed'],
            error='Status must be: planning, active, on_hold, or completed',
        ),
    )
    start_date = fields.Date(load_default=None, format='%Y-%m-%d')
    due_date = fields.Date(load_default=None, format='%Y-%m-%d')

    @validates_schema
    def validate_dates(self, data: dict, **kwargs) -> None:
        start = data.get('start_date')
        due = data.get('due_date')
        if start and due and due < start:
            raise ValidationError('due_date must be on or after start_date', 'due_date')


class ProjectUpdateSchema(Schema):
    """PUT /projects/:id — all fields optional."""

    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=1, max=200), load_default=None)
    description = fields.Str(validate=validate.Length(max=5000), load_default=None)
    status = fields.Str(
        load_default=None,
        validate=validate.OneOf(['planning', 'active', 'on_hold', 'completed']),
    )
    start_date = fields.Date(load_default=None, format='%Y-%m-%d')
    due_date = fields.Date(load_default=None, format='%Y-%m-%d')

    @validates_schema
    def validate_dates(self, data: dict, **kwargs) -> None:
        start = data.get('start_date')
        due = data.get('due_date')
        if start and due and due < start:
            raise ValidationError('due_date must be on or after start_date', 'due_date')


class AddMemberSchema(Schema):
    """POST /projects/:id/members — add a user to a project."""

    class Meta:
        unknown = EXCLUDE

    user_id = fields.UUID(required=True)
    role = fields.Str(
        load_default='developer',
        validate=validate.OneOf(
            ['manager', 'developer'],
            error='Role must be: manager or developer (owner is set automatically)',
        ),
    )


# ── Response Schemas ───────────────────────────────────────────────────────────

class ProjectMemberResponseSchema(Schema):
    """Embedded in project detail responses."""

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    project_id = fields.UUID(dump_only=True)
    role = fields.Str(dump_only=True)
    joined_at = fields.DateTime(dump_only=True)
    # Nested user info
    user = fields.Method('get_user')

    def get_user(self, obj):
        if obj.user:
            return {
                'id': str(obj.user.id),
                'username': obj.user.username,
                'full_name': obj.user.full_name,
            }
        return None


class ProjectResponseSchema(Schema):
    """Full project response."""

    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    start_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    due_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Computed
    member_count = fields.Method('get_member_count')
    task_count = fields.Method('get_task_count')
    # Nested owner summary
    owner = fields.Method('get_owner')

    def get_member_count(self, obj):
        return obj.member_count

    def get_task_count(self, obj):
        return obj.task_count

    def get_owner(self, obj):
        if obj.owner:
            return {'id': str(obj.owner.id), 'username': obj.owner.username}
        return None


class ProjectListResponseSchema(Schema):
    """Lightweight schema for list views."""

    id = fields.UUID(dump_only=True)
    name = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    due_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    member_count = fields.Method('get_member_count')
    task_count = fields.Method('get_task_count')
    created_at = fields.DateTime(dump_only=True)

    def get_member_count(self, obj):
        return obj.member_count

    def get_task_count(self, obj):
        return obj.task_count


# ── Schema Instances ───────────────────────────────────────────────────────────
project_create_schema = ProjectCreateSchema()
project_update_schema = ProjectUpdateSchema()
add_member_schema = AddMemberSchema()
project_response_schema = ProjectResponseSchema()
projects_list_schema = ProjectListResponseSchema(many=True)
project_member_response_schema = ProjectMemberResponseSchema()
project_members_response_schema = ProjectMemberResponseSchema(many=True)

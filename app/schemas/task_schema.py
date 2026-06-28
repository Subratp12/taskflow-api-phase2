"""
TaskFlow API — Task Schemas
─────────────────────────────────────────────────────────────────────────────
Marshmallow schemas for Task validation and serialization.

Separate schemas for:
  - Full update (PUT) vs status-only patch (PATCH /status)
  - Assign-only patch (PATCH /assign)
  - List vs detail responses (avoid N+1 in lists)
"""

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates


VALID_STATUSES = ['todo', 'in_progress', 'in_review', 'done']
VALID_PRIORITIES = ['low', 'medium', 'high', 'critical']


class TaskCreateSchema(Schema):
    """POST /projects/:id/tasks"""

    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200, error='Title must be 1–200 characters'),
    )
    description = fields.Str(load_default=None, validate=validate.Length(max=10000))
    priority = fields.Str(
        load_default='medium',
        validate=validate.OneOf(VALID_PRIORITIES),
    )
    status = fields.Str(
        load_default='todo',
        validate=validate.OneOf(VALID_STATUSES),
    )
    assignee_id = fields.UUID(load_default=None, allow_none=True)
    due_date = fields.Date(load_default=None, format='%Y-%m-%d')

    @validates('title')
    def validate_title_not_blank(self, value: str) -> None:
        if not value.strip():
            raise ValidationError('Title cannot be blank')


class TaskUpdateSchema(Schema):
    """PUT /tasks/:id — full update, all fields optional."""

    class Meta:
        unknown = EXCLUDE

    title = fields.Str(
        load_default=None,
        validate=validate.Length(min=1, max=200),
    )
    description = fields.Str(load_default=None, validate=validate.Length(max=10000))
    priority = fields.Str(
        load_default=None,
        validate=validate.OneOf(VALID_PRIORITIES),
    )
    status = fields.Str(
        load_default=None,
        validate=validate.OneOf(VALID_STATUSES),
    )
    assignee_id = fields.UUID(load_default=None, allow_none=True)
    due_date = fields.Date(load_default=None, format='%Y-%m-%d', allow_none=True)


class TaskStatusPatchSchema(Schema):
    """PATCH /tasks/:id/status — update status only."""

    class Meta:
        unknown = EXCLUDE

    status = fields.Str(
        required=True,
        validate=validate.OneOf(
            VALID_STATUSES,
            error=f'Status must be one of: {", ".join(VALID_STATUSES)}',
        ),
    )


class TaskAssignPatchSchema(Schema):
    """PATCH /tasks/:id/assign — assign or unassign a task."""

    class Meta:
        unknown = EXCLUDE

    # None = unassign; UUID = assign to this user
    assignee_id = fields.UUID(required=True, allow_none=True)


class TaskFilterSchema(Schema):
    """Query parameters for GET /projects/:id/tasks"""

    class Meta:
        unknown = EXCLUDE

    status = fields.Str(
        load_default=None,
        validate=validate.OneOf(VALID_STATUSES + ['all']),
    )
    priority = fields.Str(
        load_default=None,
        validate=validate.OneOf(VALID_PRIORITIES + ['all']),
    )
    assignee_id = fields.UUID(load_default=None, allow_none=True)
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


# ── Response Schemas ───────────────────────────────────────────────────────────

class TaskResponseSchema(Schema):
    """Full task detail response."""

    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)
    status = fields.Str(dump_only=True)
    priority = fields.Str(dump_only=True)
    project_id = fields.UUID(dump_only=True)
    creator_id = fields.UUID(dump_only=True, allow_none=True)
    assignee_id = fields.UUID(dump_only=True, allow_none=True)
    due_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    completed_at = fields.DateTime(dump_only=True, allow_none=True)
    comment_count = fields.Method('get_comment_count')
    is_overdue = fields.Method('get_is_overdue')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Nested user summaries
    creator = fields.Method('get_creator')
    assignee = fields.Method('get_assignee')

    def get_comment_count(self, obj):
        return obj.comment_count

    def get_is_overdue(self, obj):
        return obj.is_overdue

    def get_creator(self, obj):
        if obj.creator:
            return {'id': str(obj.creator.id), 'username': obj.creator.username}
        return None

    def get_assignee(self, obj):
        if obj.assignee:
            return {
                'id': str(obj.assignee.id),
                'username': obj.assignee.username,
                'full_name': obj.assignee.full_name,
            }
        return None


class TaskListItemSchema(Schema):
    """Lightweight schema for task list views — avoids heavy joins."""

    id = fields.UUID(dump_only=True)
    title = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    priority = fields.Str(dump_only=True)
    assignee_id = fields.UUID(dump_only=True, allow_none=True)
    due_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    is_overdue = fields.Method('get_is_overdue')
    comment_count = fields.Method('get_comment_count')
    created_at = fields.DateTime(dump_only=True)

    def get_is_overdue(self, obj):
        return obj.is_overdue

    def get_comment_count(self, obj):
        return obj.comment_count


# ── Schema Instances ───────────────────────────────────────────────────────────
task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_status_patch_schema = TaskStatusPatchSchema()
task_assign_patch_schema = TaskAssignPatchSchema()
task_filter_schema = TaskFilterSchema()
task_response_schema = TaskResponseSchema()
tasks_list_schema = TaskListItemSchema(many=True)

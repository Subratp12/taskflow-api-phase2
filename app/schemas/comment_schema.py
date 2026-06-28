"""
TaskFlow API — Comment & ActivityLog Schemas
─────────────────────────────────────────────────────────────────────────────
"""

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates


# ── Comment Schemas ────────────────────────────────────────────────────────────

class CommentCreateSchema(Schema):
    """POST /tasks/:id/comments"""

    class Meta:
        unknown = EXCLUDE

    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=10000, error='Comment must be 1–10,000 characters'),
    )

    @validates('content')
    def validate_not_blank(self, value: str) -> None:
        if not value.strip():
            raise ValidationError('Comment content cannot be blank')


class CommentUpdateSchema(Schema):
    """PUT /comments/:id — edit own comment."""

    class Meta:
        unknown = EXCLUDE

    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=10000),
    )

    @validates('content')
    def validate_not_blank(self, value: str) -> None:
        if not value.strip():
            raise ValidationError('Comment content cannot be blank')


class CommentResponseSchema(Schema):
    """Comment response with nested author info."""

    id = fields.UUID(dump_only=True)
    content = fields.Str(dump_only=True)
    is_edited = fields.Bool(dump_only=True)
    task_id = fields.UUID(dump_only=True)
    author_id = fields.UUID(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    author = fields.Method('get_author')

    def get_author(self, obj):
        if obj.author:
            return {
                'id': str(obj.author.id),
                'username': obj.author.username,
                'full_name': obj.author.full_name,
            }
        return {'id': None, 'username': '[deleted user]', 'full_name': '[deleted user]'}


# ── ActivityLog Schemas ────────────────────────────────────────────────────────

class ActivityLogResponseSchema(Schema):
    """Activity log entry response."""

    id = fields.UUID(dump_only=True)
    action = fields.Str(dump_only=True)
    entity_type = fields.Str(dump_only=True)
    entity_id = fields.UUID(dump_only=True, allow_none=True)
    user_id = fields.UUID(dump_only=True, allow_none=True)
    project_id = fields.UUID(dump_only=True, allow_none=True)
    metadata = fields.Method('get_metadata')
    created_at = fields.DateTime(dump_only=True)
    actor = fields.Method('get_actor')

    def get_metadata(self, obj):
        return obj.metadata_ or {}

    def get_actor(self, obj):
        if obj.user:
            return {'id': str(obj.user.id), 'username': obj.user.username}
        return None


# ── Schema Instances ───────────────────────────────────────────────────────────
comment_create_schema = CommentCreateSchema()
comment_update_schema = CommentUpdateSchema()
comment_response_schema = CommentResponseSchema()
comments_response_schema = CommentResponseSchema(many=True)
activity_log_response_schema = ActivityLogResponseSchema()
activity_logs_response_schema = ActivityLogResponseSchema(many=True)

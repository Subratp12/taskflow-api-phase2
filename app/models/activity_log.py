"""
TaskFlow API — ActivityLog Model
─────────────────────────────────────────────────────────────────────────────
Every significant action in the system creates an ActivityLog entry.
This is an append-only audit trail. Records are NEVER updated or deleted.

The metadata JSONB column stores action-specific details:
    task_created:    {'title': 'Build login page', 'priority': 'high'}
    status_changed:  {'from': 'todo', 'to': 'in_progress'}
    member_added:    {'user_id': '...', 'role': 'developer'}
    task_assigned:   {'assignee_id': '...', 'assignee_name': 'Jane'}

DevOps note:
    This table will grow continuously. Plan a retention/archival strategy.
    Index on project_id and created_at is critical for query performance.
"""

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.extensions import db

from .base import BaseModel


class ActivityLog(BaseModel):
    __tablename__ = 'activity_logs'

    # ── What Happened ─────────────────────────────────────────────────────────
    action = db.Column(db.String(100), nullable=False, index=True)
    # e.g. 'task_created', 'task_status_changed', 'member_added', 'project_updated'

    # ── What Was Affected ─────────────────────────────────────────────────────
    entity_type = db.Column(db.String(50), nullable=False)
    # e.g. 'task', 'project', 'comment', 'user'

    entity_id = db.Column(PG_UUID(as_uuid=True), nullable=True)
    # UUID of the affected object (NULL if entity was deleted)

    # ── Context ───────────────────────────────────────────────────────────────
    # Who did it
    user_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    # Which project it happened in
    project_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )

    # ── Extra Data ────────────────────────────────────────────────────────────
    # JSONB — flexible, queryable. Store before/after values, names, etc.
    metadata_ = db.Column('metadata', JSONB, nullable=True, default=dict)

    # ── Relationships ──────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='activity_logs', lazy='joined')
    project = db.relationship('Project', back_populates='activity_logs', lazy='joined')

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # Most common query: "what happened in project X, newest first?"
        db.Index('ix_activity_logs_project_created', 'project_id', 'created_at'),
        # "what did user Y do?"
        db.Index('ix_activity_logs_user_created', 'user_id', 'created_at'),
        # "all task_created events"
        db.Index('ix_activity_logs_action', 'action'),
    )

    # ── Factory Class Method ───────────────────────────────────────────────────

    @classmethod
    def log(
        cls,
        action: str,
        entity_type: str,
        entity_id=None,
        user_id=None,
        project_id=None,
        metadata: dict | None = None,
    ) -> 'ActivityLog':
        """
        Create and persist an activity log entry.

        Usage:
            ActivityLog.log(
                action='task_status_changed',
                entity_type='task',
                entity_id=task.id,
                user_id=current_user.id,
                project_id=task.project_id,
                metadata={'from': 'todo', 'to': 'in_progress'},
            )
        """
        entry = cls(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            project_id=project_id,
            metadata_=metadata or {},
        )
        db.session.add(entry)
        # Note: caller is responsible for db.session.commit()
        # This allows logging to be batched with the main transaction
        return entry

    def __repr__(self) -> str:
        return f"<ActivityLog action={self.action} entity={self.entity_type}:{self.entity_id}>"

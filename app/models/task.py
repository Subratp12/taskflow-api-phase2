"""
TaskFlow API — Task Model
─────────────────────────────────────────────────────────────────────────────
Tasks are the core unit of work in TaskFlow. They belong to a project and
can be assigned to a project member.

Status flow:
    todo → in_progress → in_review → done
                          ↑___________|  (can go back for revision)

Priority levels affect how tasks are surfaced in views and alerts.
"""

import enum

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.extensions import db

from .base import BaseModel


class TaskStatus(str, enum.Enum):
    todo = 'todo'
    in_progress = 'in_progress'
    in_review = 'in_review'
    done = 'done'


class TaskPriority(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'


class Task(BaseModel):
    __tablename__ = 'tasks'

    # ── Core Fields ───────────────────────────────────────────────────────────
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # ── Status & Priority ─────────────────────────────────────────────────────
    status = db.Column(
        db.Enum(TaskStatus, name='task_status', values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskStatus.todo,
        server_default=TaskStatus.todo.value,
        index=True,
    )
    priority = db.Column(
        db.Enum(TaskPriority, name='task_priority', values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskPriority.medium,
        server_default=TaskPriority.medium.value,
        index=True,
    )

    # ── Relationships (Foreign Keys) ───────────────────────────────────────────
    project_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    creator_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,   # Allow creator account deletion without losing tasks
        index=True,
    )
    assignee_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,   # Tasks can be unassigned
        index=True,
    )

    # ── Timeline ──────────────────────────────────────────────────────────────
    due_date = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    project = db.relationship(
        'Project',
        back_populates='tasks',
        lazy='joined',
    )
    creator = db.relationship(
        'User',
        back_populates='created_tasks',
        foreign_keys=[creator_id],
        lazy='joined',
    )
    assignee = db.relationship(
        'User',
        back_populates='assigned_tasks',
        foreign_keys=[assignee_id],
        lazy='joined',
    )
    comments = db.relationship(
        'Comment',
        back_populates='task',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    # ── Table Constraints ─────────────────────────────────────────────────────
    __table_args__ = (
        db.CheckConstraint("length(title) >= 1", name='ck_tasks_title_not_empty'),
        db.Index('ix_tasks_project_status', 'project_id', 'status'),
        db.Index('ix_tasks_project_priority', 'project_id', 'priority'),
        db.Index('ix_tasks_assignee_status', 'assignee_id', 'status'),
    )

    # ── Business Logic Helpers ─────────────────────────────────────────────────

    @property
    def is_overdue(self) -> bool:
        """True if task has a due date in the past and is not done."""
        if not self.due_date or self.status == TaskStatus.done:
            return False
        from datetime import date
        return self.due_date < date.today()

    @property
    def comment_count(self) -> int:
        return self.comments.count()

    def mark_done(self) -> None:
        """Mark task as done and set completed_at timestamp."""
        from datetime import datetime, timezone
        self.status = TaskStatus.done
        self.completed_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<Task '{self.title[:30]}' [{self.status.value}] [{self.priority.value}]>"

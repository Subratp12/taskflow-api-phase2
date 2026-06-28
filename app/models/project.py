"""
TaskFlow API — Project & ProjectMember Models
─────────────────────────────────────────────────────────────────────────────
Project: The top-level entity. Every task belongs to a project.
ProjectMember: Associates users with projects and assigns a project-level role.

A user can have different roles in different projects:
  - owner: created the project, full control
  - manager: can manage tasks and members
  - developer: can update assigned tasks
"""

import enum

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.extensions import db

from .base import BaseModel


class ProjectStatus(str, enum.Enum):
    planning = 'planning'
    active = 'active'
    on_hold = 'on_hold'
    completed = 'completed'


class MemberRole(str, enum.Enum):
    """Role within a specific project (different from system-level UserRole)."""
    owner = 'owner'
    manager = 'manager'
    developer = 'developer'


class Project(BaseModel):
    __tablename__ = 'projects'

    # ── Core Fields ───────────────────────────────────────────────────────────
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(ProjectStatus, name='project_status', values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProjectStatus.planning,
        server_default=ProjectStatus.planning.value,
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    owner_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )

    # ── Timeline ──────────────────────────────────────────────────────────────
    start_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    owner = db.relationship(
        'User',
        back_populates='owned_projects',
        foreign_keys=[owner_id],
        lazy='joined',
    )
    memberships = db.relationship(
        'ProjectMember',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    tasks = db.relationship(
        'Task',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    activity_logs = db.relationship(
        'ActivityLog',
        back_populates='project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    # ── Table Constraints ─────────────────────────────────────────────────────
    __table_args__ = (
        db.CheckConstraint("length(name) >= 1", name='ck_projects_name_not_empty'),
        db.CheckConstraint(
            "due_date IS NULL OR start_date IS NULL OR due_date >= start_date",
            name='ck_projects_date_order',
        ),
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def is_member(self, user_id) -> bool:
        """Check if a user (by ID) is a member of this project."""
        import uuid
        return db.session.query(
            ProjectMember.query.filter_by(
                project_id=self.id,
                user_id=uuid.UUID(str(user_id)),
            ).exists()
        ).scalar()

    def get_member_role(self, user_id) -> 'MemberRole | None':
        """Return the user's role in this project, or None if not a member."""
        import uuid
        membership = ProjectMember.query.filter_by(
            project_id=self.id,
            user_id=uuid.UUID(str(user_id)),
        ).first()
        return membership.role if membership else None

    @property
    def member_count(self) -> int:
        return self.memberships.count()

    @property
    def task_count(self) -> int:
        return self.tasks.count()

    def __repr__(self) -> str:
        return f"<Project '{self.name}' ({self.status.value})>"


class ProjectMember(BaseModel):
    """
    Association model between User and Project.
    Stores the user's role within that specific project.
    """
    __tablename__ = 'project_members'

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    project_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
    )
    user_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # ── Role within this project ───────────────────────────────────────────────
    role = db.Column(
        db.Enum(MemberRole, name='member_role', values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=MemberRole.developer,
        server_default=MemberRole.developer.value,
    )

    joined_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    project = db.relationship('Project', back_populates='memberships', lazy='joined')
    user = db.relationship('User', back_populates='project_memberships', lazy='joined')

    # ── Constraints ───────────────────────────────────────────────────────────
    __table_args__ = (
        # A user can only be a member of a project once
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_members_project_user'),
    )

    def __repr__(self) -> str:
        return f"<ProjectMember project={self.project_id} user={self.user_id} role={self.role.value}>"

"""
TaskFlow API — User Model
─────────────────────────────────────────────────────────────────────────────
Represents a TaskFlow user. Handles its own password hashing (bcrypt).
Roles control what a user can do across the system.
"""

import enum

import bcrypt
from flask import current_app
from sqlalchemy import event

from app.extensions import db

from .base import BaseModel


class UserRole(str, enum.Enum):
    """System-level role. Controls admin access."""
    admin = 'admin'
    manager = 'manager'
    developer = 'developer'


class User(BaseModel):
    __tablename__ = 'users'

    # ── Core Fields ───────────────────────────────────────────────────────────
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # ── Profile ───────────────────────────────────────────────────────────────
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)

    # ── Access Control ────────────────────────────────────────────────────────
    role = db.Column(
        db.Enum(UserRole, name='user_role', values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.developer,
        server_default=UserRole.developer.value,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')

    # ── Activity Tracking ─────────────────────────────────────────────────────
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    # Projects this user owns
    owned_projects = db.relationship(
        'Project',
        back_populates='owner',
        foreign_keys='Project.owner_id',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    # Project memberships (via association table)
    project_memberships = db.relationship(
        'ProjectMember',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    # Tasks assigned to this user
    assigned_tasks = db.relationship(
        'Task',
        back_populates='assignee',
        foreign_keys='Task.assignee_id',
        lazy='dynamic',
    )
    # Tasks created by this user
    created_tasks = db.relationship(
        'Task',
        back_populates='creator',
        foreign_keys='Task.creator_id',
        lazy='dynamic',
    )
    # Comments written by this user
    comments = db.relationship(
        'Comment',
        back_populates='author',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    # Activity log entries for this user
    activity_logs = db.relationship(
        'ActivityLog',
        back_populates='user',
        lazy='dynamic',
    )

    # ── Table Constraints ─────────────────────────────────────────────────────
    __table_args__ = (
        db.CheckConstraint("length(username) >= 3", name='ck_users_username_min_length'),
        db.CheckConstraint("email LIKE '%@%'", name='ck_users_email_format'),
    )

    # ── Password Management ───────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """
        Hash and store the password using bcrypt.
        Cost factor (log_rounds) comes from app config.
        """
        rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12)
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=rounds),
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8'),
        )

    # ── Helper Properties ─────────────────────────────────────────────────────

    @property
    def full_name(self) -> str:
        """Display name — falls back to username if name fields are empty."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.admin

    @property
    def is_manager(self) -> bool:
        return self.role in (UserRole.admin, UserRole.manager)

    # ── Serialization Override ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Exclude password_hash from serialization — never expose it."""
        data = super().to_dict()
        data.pop('password_hash', None)
        data['full_name'] = self.full_name
        return data

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"

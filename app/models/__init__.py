"""
TaskFlow API — Models Package
─────────────────────────────────────────────────────────────────────────────
Import all models here so Flask-Migrate (Alembic) can discover them
when running `flask db migrate`.

Also used by the shell context (flask shell) and seed scripts.
"""

from .activity_log import ActivityLog
from .comment import Comment
from .project import MemberRole, Project, ProjectMember, ProjectStatus
from .task import Task, TaskPriority, TaskStatus
from .user import User, UserRole

__all__ = [
    # Models
    'User',
    'Project',
    'ProjectMember',
    'Task',
    'Comment',
    'ActivityLog',
    # Enums (exported for use in schemas and services)
    'UserRole',
    'ProjectStatus',
    'MemberRole',
    'TaskStatus',
    'TaskPriority',
]

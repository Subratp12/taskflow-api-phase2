"""
TaskFlow API — Comment Model
─────────────────────────────────────────────────────────────────────────────
Users can add comments to tasks. Authors can edit their own comments.
The is_edited flag tracks whether content was modified after creation.
"""

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.extensions import db

from .base import BaseModel


class Comment(BaseModel):
    __tablename__ = 'comments'

    # ── Content ───────────────────────────────────────────────────────────────
    content = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, nullable=False, default=False, server_default='false')

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    task_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    author_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,   # Preserve comments when user account is deleted
        index=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    task = db.relationship('Task', back_populates='comments', lazy='joined')
    author = db.relationship('User', back_populates='comments', lazy='joined')

    # ── Table Constraints ─────────────────────────────────────────────────────
    __table_args__ = (
        db.CheckConstraint("length(content) >= 1", name='ck_comments_content_not_empty'),
        db.CheckConstraint("length(content) <= 10000", name='ck_comments_content_max_length'),
    )

    def edit(self, new_content: str) -> None:
        """Update content and flag as edited."""
        self.content = new_content
        self.is_edited = True

    def __repr__(self) -> str:
        preview = self.content[:30] if self.content else ''
        return f"<Comment '{preview}...' task={self.task_id}>"

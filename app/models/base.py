"""
TaskFlow API — Base Model
─────────────────────────────────────────────────────────────────────────────
All models inherit from BaseModel. This gives every table:
  - UUID primary key (no sequential ID guessing)
  - created_at / updated_at with timezone-aware timestamps
  - save() / delete() convenience methods
  - to_dict() for safe serialization (no raw SQLAlchemy objects in responses)
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.extensions import db


class BaseModel(db.Model):
    """Abstract base model — never creates its own table."""
    __abstract__ = True

    id = db.Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Persistence Helpers ────────────────────────────────────────────────────

    def save(self) -> 'BaseModel':
        """Add to session and commit. Returns self for chaining."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        """Delete from session and commit."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, record_id: str) -> 'BaseModel | None':
        """Fetch by primary key. Returns None if not found."""
        try:
            return db.session.get(cls, uuid.UUID(str(record_id)))
        except (ValueError, AttributeError):
            return None

    # ── Serialization ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Serialize model columns to a plain dict.
        Handles: UUID → str, datetime → ISO string, Enum → .value
        Relationships are NOT included (avoids N+1 queries).
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if value is None:
                result[column.name] = None
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, enum.Enum):
                result[column.name] = value.value
            else:
                result[column.name] = value
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"

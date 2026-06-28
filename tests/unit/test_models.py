"""
TaskFlow API — Model Unit Tests
─────────────────────────────────────────────────────────────────────────────
Tests the database models in isolation (no HTTP layer).

Run: pytest tests/unit/test_models.py -v
"""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models import (
    ActivityLog,
    Comment,
    Project,
    ProjectMember,
    Task,
    User,
)
from app.models.project import MemberRole, ProjectStatus
from app.models.task import TaskPriority, TaskStatus
from app.models.user import UserRole


# ── User Model ─────────────────────────────────────────────────────────────────

class TestUserModel:

    def test_create_user(self, db):
        """User is persisted with correct defaults."""
        user = User(
            username='testuser',
            email='test@example.com',
        )
        user.set_password('SecurePass1!')
        db.session.add(user)
        db.session.flush()

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.role == UserRole.developer    # default
        assert user.is_active is True             # default
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_password_hashing(self, db):
        """Password is hashed — plaintext is never stored."""
        user = User(username='pwtest', email='pw@example.com')
        user.set_password('MyPassword1!')

        assert user.password_hash != 'MyPassword1!'
        assert user.password_hash.startswith('$2b$')  # bcrypt prefix
        assert user.check_password('MyPassword1!') is True
        assert user.check_password('WrongPassword') is False

    def test_password_wrong_returns_false(self, db):
        """Wrong password fails gracefully (no exception)."""
        user = User(username='pwtest2', email='pw2@example.com')
        user.set_password('CorrectPassword1!')
        assert user.check_password('') is False
        assert user.check_password('correctpassword1!') is False  # case-sensitive

    def test_full_name_property(self, db):
        """full_name falls back to username when name fields are empty."""
        u1 = User(username='jdoe', email='jdoe@example.com', first_name='John', last_name='Doe')
        assert u1.full_name == 'John Doe'

        u2 = User(username='janedoe', email='janedoe@example.com', first_name='Jane')
        assert u2.full_name == 'Jane'

        u3 = User(username='noname', email='noname@example.com')
        assert u3.full_name == 'noname'

    def test_is_admin_property(self, db):
        """Role-based convenience properties."""
        admin = User(username='a', email='a@e.com', role=UserRole.admin)
        manager = User(username='m', email='m@e.com', role=UserRole.manager)
        dev = User(username='d', email='d@e.com', role=UserRole.developer)

        assert admin.is_admin is True
        assert manager.is_admin is False
        assert dev.is_admin is False

        assert admin.is_manager is True   # admin inherits manager access
        assert manager.is_manager is True
        assert dev.is_manager is False

    def test_to_dict_excludes_password(self, db):
        """to_dict() never exposes the password hash."""
        user = User(username='safe', email='safe@example.com')
        user.set_password('SafePass1!')
        result = user.to_dict()

        assert 'password_hash' not in result
        assert 'id' in result
        assert 'username' in result
        assert 'email' in result
        assert 'full_name' in result

    def test_uuid_primary_key_is_unique(self, db):
        """Each user gets a different UUID."""
        u1 = User(username='u1', email='u1@example.com')
        u2 = User(username='u2', email='u2@example.com')
        u1.set_password('Pass1!')
        u2.set_password('Pass1!')
        db.session.add_all([u1, u2])
        db.session.flush()

        assert u1.id != u2.id


# ── Project Model ──────────────────────────────────────────────────────────────

class TestProjectModel:

    def test_create_project(self, db, manager_user):
        """Project is created with correct defaults."""
        project = Project(
            name='My New Project',
            owner_id=manager_user.id,
        )
        db.session.add(project)
        db.session.flush()

        assert project.id is not None
        assert project.status == ProjectStatus.planning   # default
        assert project.description is None
        assert project.created_at is not None

    def test_project_status_transitions(self, db, manager_user):
        """Project status can be changed to any valid status."""
        project = Project(name='Status Test', owner_id=manager_user.id)
        db.session.add(project)
        db.session.flush()

        for status in ProjectStatus:
            project.status = status
            db.session.flush()
            assert project.status == status

    def test_project_member_count(self, db, sample_project, dev_user):
        """member_count reflects current memberships."""
        initial_count = sample_project.member_count  # owner already added

        membership = ProjectMember(
            project_id=sample_project.id,
            user_id=dev_user.id,
            role=MemberRole.developer,
        )
        db.session.add(membership)
        db.session.flush()

        assert sample_project.member_count == initial_count + 1

    def test_project_unique_membership(self, db, sample_project, manager_user):
        """A user cannot be added to the same project twice."""
        from sqlalchemy.exc import IntegrityError

        duplicate = ProjectMember(
            project_id=sample_project.id,
            user_id=manager_user.id,   # already a member (owner)
            role=MemberRole.developer,
        )
        db.session.add(duplicate)
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()


# ── Task Model ─────────────────────────────────────────────────────────────────

class TestTaskModel:

    def test_create_task(self, db, sample_project, manager_user):
        """Task is created with correct defaults."""
        task = Task(
            title='Write unit tests',
            project_id=sample_project.id,
            creator_id=manager_user.id,
        )
        db.session.add(task)
        db.session.flush()

        assert task.id is not None
        assert task.status == TaskStatus.todo      # default
        assert task.priority == TaskPriority.medium  # default
        assert task.assignee_id is None
        assert task.completed_at is None

    def test_is_overdue_with_past_due_date(self, db, sample_project, manager_user):
        """is_overdue is True for past due date on non-done tasks."""
        from datetime import timedelta
        past_date = date.today() - timedelta(days=3)

        task = Task(
            title='Overdue task',
            project_id=sample_project.id,
            creator_id=manager_user.id,
            due_date=past_date,
            status=TaskStatus.in_progress,
        )
        db.session.add(task)
        db.session.flush()

        assert task.is_overdue is True

    def test_is_overdue_is_false_when_done(self, db, sample_project, manager_user):
        """Done tasks are never considered overdue."""
        from datetime import timedelta
        past_date = date.today() - timedelta(days=3)

        task = Task(
            title='Done task',
            project_id=sample_project.id,
            creator_id=manager_user.id,
            due_date=past_date,
            status=TaskStatus.done,
        )
        db.session.add(task)
        db.session.flush()

        assert task.is_overdue is False

    def test_mark_done_sets_completed_at(self, db, sample_task):
        """mark_done() updates status and sets completed_at timestamp."""
        assert sample_task.completed_at is None

        sample_task.mark_done()
        db.session.flush()

        assert sample_task.status == TaskStatus.done
        assert sample_task.completed_at is not None
        assert sample_task.completed_at.tzinfo is not None  # timezone-aware

    def test_task_cascade_delete(self, db, sample_project, manager_user):
        """Deleting a task cascades to its comments."""
        task = Task(
            title='Task to delete',
            project_id=sample_project.id,
            creator_id=manager_user.id,
        )
        db.session.add(task)
        db.session.flush()

        comment = Comment(
            content='This comment should vanish',
            task_id=task.id,
            author_id=manager_user.id,
        )
        db.session.add(comment)
        db.session.flush()
        comment_id = comment.id

        db.session.delete(task)
        db.session.flush()

        assert db.session.get(Comment, comment_id) is None


# ── Comment Model ──────────────────────────────────────────────────────────────

class TestCommentModel:

    def test_create_comment(self, db, sample_task, dev_user):
        """Comment is created and linked to task and author."""
        comment = Comment(
            content='This looks good to me!',
            task_id=sample_task.id,
            author_id=dev_user.id,
        )
        db.session.add(comment)
        db.session.flush()

        assert comment.id is not None
        assert comment.is_edited is False

    def test_edit_comment(self, db, sample_comment):
        """edit() updates content and sets is_edited flag."""
        assert sample_comment.is_edited is False

        sample_comment.edit('Updated comment content here.')
        db.session.flush()

        assert sample_comment.content == 'Updated comment content here.'
        assert sample_comment.is_edited is True


# ── ActivityLog Model ──────────────────────────────────────────────────────────

class TestActivityLogModel:

    def test_log_factory_method(self, db, sample_project, manager_user, sample_task):
        """ActivityLog.log() creates a persisted log entry."""
        entry = ActivityLog.log(
            action='task_created',
            entity_type='task',
            entity_id=sample_task.id,
            user_id=manager_user.id,
            project_id=sample_project.id,
            metadata={'title': sample_task.title, 'priority': 'high'},
        )
        db.session.flush()

        assert entry.id is not None
        assert entry.action == 'task_created'
        assert entry.entity_type == 'task'
        assert entry.metadata_['title'] == sample_task.title

    def test_log_without_metadata(self, db, sample_project, manager_user):
        """ActivityLog.log() works with no metadata."""
        entry = ActivityLog.log(
            action='project_updated',
            entity_type='project',
            entity_id=sample_project.id,
            user_id=manager_user.id,
            project_id=sample_project.id,
        )
        db.session.flush()

        assert entry.metadata_ == {}


# ── BaseModel ──────────────────────────────────────────────────────────────────

class TestBaseModel:

    def test_get_by_id(self, db, manager_user):
        """get_by_id() fetches by UUID."""
        fetched = User.get_by_id(str(manager_user.id))
        assert fetched is not None
        assert fetched.id == manager_user.id

    def test_get_by_id_invalid_uuid(self, db):
        """get_by_id() returns None for invalid UUID strings."""
        result = User.get_by_id('not-a-uuid')
        assert result is None

    def test_get_by_id_nonexistent(self, db):
        """get_by_id() returns None for valid but non-existent UUID."""
        result = User.get_by_id(str(uuid.uuid4()))
        assert result is None

    def test_to_dict_serializes_uuid_as_string(self, db, manager_user):
        """to_dict() returns UUID fields as strings (JSON-serializable)."""
        data = manager_user.to_dict()
        assert isinstance(data['id'], str)
        # Should be valid UUID
        uuid.UUID(data['id'])

    def test_to_dict_serializes_datetime_as_iso(self, db, manager_user):
        """to_dict() returns datetime fields as ISO 8601 strings."""
        data = manager_user.to_dict()
        assert isinstance(data['created_at'], str)
        # Should be parseable as ISO datetime
        datetime.fromisoformat(data['created_at'])

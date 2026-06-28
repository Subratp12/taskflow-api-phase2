"""
TaskFlow API — Test Configuration & Fixtures
─────────────────────────────────────────────────────────────────────────────
pytest fixtures shared across all test files.

Fixture scopes:
    session   — created once for the entire test run (app, tables)
    function  — created fresh for every test (client, db_session)

Database strategy:
    Each test gets a fresh transaction that is ROLLED BACK after the test.
    This means tests are isolated without needing to truncate tables.
"""

import pytest

from app import create_app
from app.extensions import db as _db
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


# ── App & Database Setup ───────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """
    Create the Flask test application once per test session.
    Creates all database tables before tests, drops them after.
    """
    test_app = create_app('testing')

    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """
    Provide a database session that is rolled back after each test.
    This ensures complete test isolation without truncating tables.
    """
    with app.app_context():
        # Begin a savepoint so we can roll back after each test
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client — use for HTTP-level integration tests."""
    return app.test_client()


# ── Model Factories ────────────────────────────────────────────────────────────

@pytest.fixture(scope='function')
def admin_user(db):
    """An admin user — used to test admin-only endpoints."""
    user = User(
        username='admin_test',
        email='admin@test.com',
        role=UserRole.admin,
        first_name='Admin',
        last_name='User',
        is_active=True,
    )
    user.set_password('AdminPass1!')
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture(scope='function')
def manager_user(db):
    """A manager user — used to test project/task management."""
    user = User(
        username='manager_test',
        email='manager@test.com',
        role=UserRole.manager,
        first_name='Manager',
        last_name='User',
        is_active=True,
    )
    user.set_password('ManagerPass1!')
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture(scope='function')
def dev_user(db):
    """A developer user — used to test task assignment and updates."""
    user = User(
        username='dev_test',
        email='dev@test.com',
        role=UserRole.developer,
        first_name='Dev',
        last_name='User',
        is_active=True,
    )
    user.set_password('DevPass1!')
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture(scope='function')
def sample_project(db, manager_user):
    """A sample project owned by manager_user."""
    project = Project(
        name='Test Project Alpha',
        description='A test project for unit and integration tests',
        status=ProjectStatus.active,
        owner_id=manager_user.id,
    )
    db.session.add(project)
    db.session.flush()

    # Add owner as a member
    membership = ProjectMember(
        project_id=project.id,
        user_id=manager_user.id,
        role=MemberRole.owner,
    )
    db.session.add(membership)
    db.session.flush()
    return project


@pytest.fixture(scope='function')
def sample_task(db, sample_project, manager_user, dev_user):
    """A sample task inside sample_project, assigned to dev_user."""
    task = Task(
        title='Implement user authentication',
        description='Build JWT-based auth with refresh tokens',
        status=TaskStatus.in_progress,
        priority=TaskPriority.high,
        project_id=sample_project.id,
        creator_id=manager_user.id,
        assignee_id=dev_user.id,
    )
    db.session.add(task)
    db.session.flush()
    return task


@pytest.fixture(scope='function')
def sample_comment(db, sample_task, dev_user):
    """A comment on sample_task written by dev_user."""
    comment = Comment(
        content='Starting work on this. Will use Flask-JWT-Extended.',
        task_id=sample_task.id,
        author_id=dev_user.id,
    )
    db.session.add(comment)
    db.session.flush()
    return comment

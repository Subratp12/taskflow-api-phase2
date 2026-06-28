#!/usr/bin/env python3
"""
TaskFlow API — Database Seed Script
─────────────────────────────────────────────────────────────────────────────
Populates the database with realistic sample data for development and staging.

Usage:
    python scripts/seed_data.py
    FLASK_ENV=staging python scripts/seed_data.py

WARNING: This script TRUNCATES existing data before seeding.
         NEVER run against production.

Creates:
    Users     → 1 admin, 2 managers, 4 developers
    Projects  → 3 projects with members
    Tasks     → ~20 tasks across projects
    Comments  → Comments on selected tasks
    Logs      → Activity log entries
"""

import os
import sys
from datetime import date, timedelta

# Add project root to path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
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


def clear_data() -> None:
    """Truncate all tables in correct order (respect FK constraints)."""
    print("  🗑️  Clearing existing data...")
    db.session.execute(db.text("SET session_replication_role = replica"))  # Disable FK checks
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.execute(db.text("SET session_replication_role = DEFAULT"))
    db.session.commit()


def seed_users() -> dict:
    """Create 7 users across all roles."""
    print("  👤 Creating users...")

    users = {
        'admin': User(
            username='sarah_admin',
            email='sarah@taskflow.dev',
            role=UserRole.admin,
            first_name='Sarah',
            last_name='Chen',
            is_active=True,
        ),
        'manager_1': User(
            username='alex_pm',
            email='alex@taskflow.dev',
            role=UserRole.manager,
            first_name='Alex',
            last_name='Rivera',
            is_active=True,
        ),
        'manager_2': User(
            username='priya_pm',
            email='priya@taskflow.dev',
            role=UserRole.manager,
            first_name='Priya',
            last_name='Sharma',
            is_active=True,
        ),
        'dev_1': User(
            username='james_dev',
            email='james@taskflow.dev',
            role=UserRole.developer,
            first_name='James',
            last_name='Wilson',
            is_active=True,
        ),
        'dev_2': User(
            username='mei_dev',
            email='mei@taskflow.dev',
            role=UserRole.developer,
            first_name='Mei',
            last_name='Tanaka',
            is_active=True,
        ),
        'dev_3': User(
            username='omar_dev',
            email='omar@taskflow.dev',
            role=UserRole.developer,
            first_name='Omar',
            last_name='Hassan',
            is_active=True,
        ),
        'dev_4': User(
            username='emma_dev',
            email='emma@taskflow.dev',
            role=UserRole.developer,
            first_name='Emma',
            last_name='Koch',
            is_active=True,
        ),
    }

    # Set passwords — all use 'TaskFlow2024!' in dev
    for user in users.values():
        user.set_password('TaskFlow2024!')

    db.session.add_all(users.values())
    db.session.commit()

    print(f"     ✅ {len(users)} users created")
    return users


def seed_projects(users: dict) -> dict:
    """Create 3 realistic projects."""
    print("  📁 Creating projects...")

    today = date.today()

    projects = {
        'ecommerce': Project(
            name='E-Commerce Platform Rewrite',
            description=(
                'Complete rewrite of the legacy monolith into a microservices architecture. '
                'This project covers the API gateway, product catalog, order management, '
                'payment integration, and customer notifications.'
            ),
            status=ProjectStatus.active,
            owner_id=users['manager_1'].id,
            start_date=today - timedelta(days=45),
            due_date=today + timedelta(days=90),
        ),
        'mobile': Project(
            name='Mobile App — iOS & Android',
            description=(
                'Native mobile applications for iOS and Android. '
                'React Native codebase targeting feature parity with web app. '
                'Phase 1: Authentication, Dashboard, Task Management.'
            ),
            status=ProjectStatus.active,
            owner_id=users['manager_2'].id,
            start_date=today - timedelta(days=20),
            due_date=today + timedelta(days=120),
        ),
        'infra': Project(
            name='DevOps Infrastructure Uplift',
            description=(
                'Migrate all services to containerized deployments on AWS ECS. '
                'Implement CI/CD pipelines, observability stack (Prometheus + Grafana), '
                'and disaster recovery procedures.'
            ),
            status=ProjectStatus.planning,
            owner_id=users['manager_1'].id,
            start_date=today + timedelta(days=14),
            due_date=today + timedelta(days=180),
        ),
    }

    db.session.add_all(projects.values())
    db.session.commit()

    print(f"     ✅ {len(projects)} projects created")
    return projects


def seed_memberships(users: dict, projects: dict) -> None:
    """Add members to projects with appropriate roles."""
    print("  👥 Creating project memberships...")

    memberships = [
        # E-Commerce Project
        ProjectMember(project_id=projects['ecommerce'].id, user_id=users['manager_1'].id, role=MemberRole.owner),
        ProjectMember(project_id=projects['ecommerce'].id, user_id=users['dev_1'].id, role=MemberRole.developer),
        ProjectMember(project_id=projects['ecommerce'].id, user_id=users['dev_2'].id, role=MemberRole.developer),
        ProjectMember(project_id=projects['ecommerce'].id, user_id=users['dev_3'].id, role=MemberRole.developer),
        ProjectMember(project_id=projects['ecommerce'].id, user_id=users['admin'].id, role=MemberRole.manager),

        # Mobile Project
        ProjectMember(project_id=projects['mobile'].id, user_id=users['manager_2'].id, role=MemberRole.owner),
        ProjectMember(project_id=projects['mobile'].id, user_id=users['dev_2'].id, role=MemberRole.developer),
        ProjectMember(project_id=projects['mobile'].id, user_id=users['dev_4'].id, role=MemberRole.developer),

        # Infra Project
        ProjectMember(project_id=projects['infra'].id, user_id=users['manager_1'].id, role=MemberRole.owner),
        ProjectMember(project_id=projects['infra'].id, user_id=users['dev_1'].id, role=MemberRole.manager),
        ProjectMember(project_id=projects['infra'].id, user_id=users['dev_3'].id, role=MemberRole.developer),
        ProjectMember(project_id=projects['infra'].id, user_id=users['dev_4'].id, role=MemberRole.developer),
    ]

    db.session.add_all(memberships)
    db.session.commit()
    print(f"     ✅ {len(memberships)} memberships created")


def seed_tasks(users: dict, projects: dict) -> list:
    """Create realistic tasks across all projects."""
    print("  ✅ Creating tasks...")

    today = date.today()

    tasks = [
        # ── E-Commerce Project Tasks ───────────────────────────────────────────
        Task(
            title='Set up PostgreSQL schema and migrations',
            description='Design and implement the initial database schema. Products, orders, customers, payments tables. Use Flask-Migrate for version control.',
            status=TaskStatus.done,
            priority=TaskPriority.high,
            project_id=projects['ecommerce'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_1'].id,
            due_date=today - timedelta(days=30),
            completed_at=db.func.now() if False else None,
        ),
        Task(
            title='Implement JWT authentication service',
            description='Build registration, login, refresh token, and logout endpoints. Use bcrypt for password hashing. Implement token blacklisting on logout.',
            status=TaskStatus.in_review,
            priority=TaskPriority.critical,
            project_id=projects['ecommerce'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_1'].id,
            due_date=today + timedelta(days=3),
        ),
        Task(
            title='Product catalog API endpoints',
            description='CRUD endpoints for products. Include filtering by category, price range, availability. Pagination required. Write OpenAPI spec.',
            status=TaskStatus.in_progress,
            priority=TaskPriority.high,
            project_id=projects['ecommerce'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_2'].id,
            due_date=today + timedelta(days=7),
        ),
        Task(
            title='Shopping cart session management',
            description='Implement cart service. Support guest carts (Redis) and logged-in user carts (PostgreSQL). Merge cart on login.',
            status=TaskStatus.todo,
            priority=TaskPriority.medium,
            project_id=projects['ecommerce'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_2'].id,
            due_date=today + timedelta(days=21),
        ),
        Task(
            title='Stripe payment integration',
            description='Integrate Stripe for payment processing. Handle webhooks for payment confirmation. Store payment intents, not raw card data.',
            status=TaskStatus.todo,
            priority=TaskPriority.high,
            project_id=projects['ecommerce'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_3'].id,
            due_date=today + timedelta(days=35),
        ),
        Task(
            title='Write integration tests for auth endpoints',
            description='Minimum 80% coverage on auth module. Test happy path, invalid credentials, expired tokens, revoked tokens.',
            status=TaskStatus.todo,
            priority=TaskPriority.medium,
            project_id=projects['ecommerce'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_1'].id,
            due_date=today + timedelta(days=10),
        ),
        Task(
            title='Add rate limiting to public API endpoints',
            description='Implement per-IP rate limiting on auth endpoints (5 req/min login). Per-user rate limiting on write endpoints. Return 429 with Retry-After header.',
            status=TaskStatus.todo,
            priority=TaskPriority.medium,
            project_id=projects['ecommerce'].id,
            creator_id=users['admin'].id,
            assignee_id=users['dev_3'].id,
            due_date=today - timedelta(days=2),   # This one is overdue
        ),

        # ── Mobile Project Tasks ───────────────────────────────────────────────
        Task(
            title='React Native project setup and navigation',
            description='Bootstrap RN project. Set up React Navigation v6. Implement tab navigator (Dashboard, Projects, Tasks, Profile). Configure environment variables.',
            status=TaskStatus.done,
            priority=TaskPriority.high,
            project_id=projects['mobile'].id,
            creator_id=users['manager_2'].id,
            assignee_id=users['dev_4'].id,
            due_date=today - timedelta(days=15),
        ),
        Task(
            title='Authentication screens — Login & Register',
            description='Build login and registration UI. Form validation. Secure token storage (Keychain/Keystore). Auto-refresh token on 401.',
            status=TaskStatus.in_progress,
            priority=TaskPriority.critical,
            project_id=projects['mobile'].id,
            creator_id=users['manager_2'].id,
            assignee_id=users['dev_4'].id,
            due_date=today + timedelta(days=5),
        ),
        Task(
            title='Task list and detail screens',
            description='List view with swipe actions (complete, delete). Detail view with comments. Pull-to-refresh. Offline support with local SQLite cache.',
            status=TaskStatus.todo,
            priority=TaskPriority.high,
            project_id=projects['mobile'].id,
            creator_id=users['manager_2'].id,
            assignee_id=users['dev_2'].id,
            due_date=today + timedelta(days=30),
        ),
        Task(
            title='Push notifications — Firebase Cloud Messaging',
            description='Integrate FCM for push notifications. Notify on task assignment, comment, due date reminder. Handle foreground and background notifications.',
            status=TaskStatus.todo,
            priority=TaskPriority.medium,
            project_id=projects['mobile'].id,
            creator_id=users['manager_2'].id,
            assignee_id=None,   # Unassigned
            due_date=today + timedelta(days=60),
        ),

        # ── Infra Project Tasks ────────────────────────────────────────────────
        Task(
            title='Dockerise Flask application with multi-stage build',
            description='Write production Dockerfile using multi-stage build. Builder stage installs deps. Final stage uses slim image. Non-root user. HEALTHCHECK instruction.',
            status=TaskStatus.todo,
            priority=TaskPriority.critical,
            project_id=projects['infra'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_3'].id,
            due_date=today + timedelta(days=20),
        ),
        Task(
            title='Write Docker Compose for local development',
            description='Compose file with: app service, PostgreSQL, Redis (for rate limiting). Volume for DB persistence. Health checks. .env support.',
            status=TaskStatus.todo,
            priority=TaskPriority.high,
            project_id=projects['infra'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_3'].id,
            due_date=today + timedelta(days=22),
        ),
        Task(
            title='GitHub Actions CI pipeline',
            description='On push to main/develop: lint (flake8), unit tests (pytest), build Docker image, push to ECR. Fail fast. Cache pip dependencies.',
            status=TaskStatus.todo,
            priority=TaskPriority.high,
            project_id=projects['infra'].id,
            creator_id=users['manager_1'].id,
            assignee_id=users['dev_4'].id,
            due_date=today + timedelta(days=30),
        ),
        Task(
            title='Deploy Prometheus + Grafana observability stack',
            description='Deploy Prometheus scraping /metrics on all app instances. Build Grafana dashboards: request rate, error rate, response time, DB pool utilisation.',
            status=TaskStatus.todo,
            priority=TaskPriority.medium,
            project_id=projects['infra'].id,
            creator_id=users['dev_1'].id,
            assignee_id=users['dev_1'].id,
            due_date=today + timedelta(days=60),
        ),
    ]

    db.session.add_all(tasks)
    db.session.commit()
    print(f"     ✅ {len(tasks)} tasks created")
    return tasks


def seed_comments(users: dict, tasks: list) -> None:
    """Add realistic comments to several tasks."""
    print("  💬 Creating comments...")

    # Find specific tasks by title
    def find_task(title_fragment):
        return next((t for t in tasks if title_fragment in t.title), None)

    auth_task = find_task('JWT authentication')
    catalog_task = find_task('Product catalog')
    docker_task = find_task('Dockerise Flask')

    comments = []
    if auth_task:
        comments += [
            Comment(
                content='I\'ve completed the registration and login endpoints. Starting on refresh token logic now. Should have a PR up by EOD.',
                task_id=auth_task.id,
                author_id=users['dev_1'].id,
            ),
            Comment(
                content='Nice work. Make sure the refresh token is stored hashed in the DB, not plaintext. Also add the `jti` claim so we can blacklist tokens on logout.',
                task_id=auth_task.id,
                author_id=users['manager_1'].id,
            ),
            Comment(
                content='Good call on the jti. I\'ll add a `revoked_tokens` table. Should I use Redis or PostgreSQL for the blacklist?',
                task_id=auth_task.id,
                author_id=users['dev_1'].id,
            ),
            Comment(
                content='PostgreSQL is fine for now — we can migrate to Redis if logout volume becomes a problem. Keep it simple.',
                task_id=auth_task.id,
                author_id=users['manager_1'].id,
            ),
        ]

    if catalog_task:
        comments += [
            Comment(
                content='Starting on the product catalog endpoints. Question: should filtering be query params or request body? I\'ll go with query params unless there\'s a reason not to.',
                task_id=catalog_task.id,
                author_id=users['dev_2'].id,
            ),
            Comment(
                content='Query params are correct for GET requests — they\'re cacheable and bookmarkable. Make sure you validate all filter values via marshmallow schema.',
                task_id=catalog_task.id,
                author_id=users['admin'].id,
            ),
        ]

    if docker_task:
        comments += [
            Comment(
                content='Starting on the Dockerfile. Plan: use python:3.11-slim-bullseye as base, multi-stage build to keep final image lean. Will run as non-root user `appuser`.',
                task_id=docker_task.id,
                author_id=users['dev_3'].id,
            ),
        ]

    if comments:
        db.session.add_all(comments)
        db.session.commit()
    print(f"     ✅ {len(comments)} comments created")


def seed_activity_logs(users: dict, projects: dict, tasks: list) -> None:
    """Create sample activity log entries."""
    print("  📋 Creating activity logs...")

    logs = [
        ActivityLog.log('project_created', 'project', projects['ecommerce'].id, users['manager_1'].id, projects['ecommerce'].id, {'name': 'E-Commerce Platform Rewrite'}),
        ActivityLog.log('project_created', 'project', projects['mobile'].id, users['manager_2'].id, projects['mobile'].id, {'name': 'Mobile App — iOS & Android'}),
        ActivityLog.log('project_created', 'project', projects['infra'].id, users['manager_1'].id, projects['infra'].id, {'name': 'DevOps Infrastructure Uplift'}),
        ActivityLog.log('member_added', 'project_member', projects['ecommerce'].id, users['manager_1'].id, projects['ecommerce'].id, {'user': 'james_dev', 'role': 'developer'}),
        ActivityLog.log('member_added', 'project_member', projects['ecommerce'].id, users['manager_1'].id, projects['ecommerce'].id, {'user': 'mei_dev', 'role': 'developer'}),
        ActivityLog.log('task_status_changed', 'task', tasks[0].id, users['dev_1'].id, projects['ecommerce'].id, {'from': 'in_progress', 'to': 'done', 'title': tasks[0].title}),
        ActivityLog.log('task_status_changed', 'task', tasks[7].id, users['dev_4'].id, projects['mobile'].id, {'from': 'in_progress', 'to': 'done', 'title': tasks[7].title}),
        ActivityLog.log('task_assigned', 'task', tasks[1].id, users['manager_1'].id, projects['ecommerce'].id, {'assignee': 'james_dev', 'title': tasks[1].title}),
        ActivityLog.log('comment_added', 'comment', tasks[1].id, users['dev_1'].id, projects['ecommerce'].id, {'task_title': tasks[1].title}),
    ]

    db.session.commit()
    print(f"     ✅ {len(logs)} activity log entries created")


def print_summary(users: dict) -> None:
    """Print login credentials summary."""
    print()
    print("─" * 60)
    print("  🌱 SEED COMPLETE — Login Credentials")
    print("─" * 60)
    print("  All users share the password: TaskFlow2024!")
    print()
    print("  Role       | Username       | Email")
    print("  -----------|----------------|------------------------")
    creds = [
        ('admin', 'sarah_admin', 'sarah@taskflow.dev'),
        ('manager', 'alex_pm', 'alex@taskflow.dev'),
        ('manager', 'priya_pm', 'priya@taskflow.dev'),
        ('developer', 'james_dev', 'james@taskflow.dev'),
        ('developer', 'mei_dev', 'mei@taskflow.dev'),
        ('developer', 'omar_dev', 'omar@taskflow.dev'),
        ('developer', 'emma_dev', 'emma@taskflow.dev'),
    ]
    for role, username, email in creds:
        print(f"  {role:<10} | {username:<14} | {email}")
    print("─" * 60)
    print()


def seed():
    """Run the full seed sequence."""
    env = os.environ.get('FLASK_ENV', 'development')

    if env == 'production':
        print("❌ REFUSING to seed production database. Set FLASK_ENV to development or staging.")
        sys.exit(1)

    print()
    print(f"🌱 Seeding TaskFlow database [{env}]...")
    print()

    app = create_app(env)
    with app.app_context():
        clear_data()
        users = seed_users()
        projects = seed_projects(users)
        seed_memberships(users, projects)
        tasks = seed_tasks(users, projects)
        seed_comments(users, tasks)
        seed_activity_logs(users, projects, tasks)
        print_summary(users)


if __name__ == '__main__':
    seed()

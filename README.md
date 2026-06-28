# TaskFlow API

A production-grade RESTful project and task management backend. Built with Python 3.11, Flask, and PostgreSQL.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11 |
| Framework | Flask 2.3 |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 + Flask-Migrate |
| Auth | Flask-JWT-Extended (RS256 JWTs) |
| Validation | Marshmallow 3.x |
| Rate Limiting | Flask-Limiter |
| WSGI Server | Gunicorn |
| Observability | Prometheus + structlog (JSON) |

---

## For the DevOps Engineer

This application is designed with container-first deployment in mind. Key facts:

**It is completely stateless.** JWT tokens are verified on every request. No server-side sessions. Safe to kill/restart/scale any instance at any time.

**All config comes from environment variables.** Copy `.env.example` → `.env`. No config is hardcoded.

**Three endpoints you care about before anything else:**

```
GET /health   → Liveness probe  (200 = process is alive)
GET /ready    → Readiness probe (200 = DB connected, ready for traffic)
GET /metrics  → Prometheus scrape endpoint
```

**Migration is handled by the app.** `scripts/wait_for_db.sh` runs `flask db upgrade` before gunicorn starts. Your rolling deploy is safe as long as migrations are backward-compatible (which they are — new columns are always nullable).

**The app runs on port 5000 by default.** Override with `PORT` env var.

---

## Prerequisites (Local Development)

- Python 3.11+
- PostgreSQL 15+
- `pg_isready` (postgresql-client, for `wait_for_db.sh`)

---

## Local Setup

### 1. Clone and install

```bash
git clone https://github.com/yourorg/taskflow-api.git
cd taskflow-api

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements-dev.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
```

Minimum required in `.env`:

```env
FLASK_ENV=development
DATABASE_URL=postgresql://taskflow:taskflow_pass@localhost:5432/taskflow
SECRET_KEY=any-random-string-for-local-dev
JWT_SECRET_KEY=another-random-string-for-local-dev
```

### 3. Create the database

```sql
-- Run in psql
CREATE USER taskflow WITH PASSWORD 'taskflow_pass';
CREATE DATABASE taskflow OWNER taskflow;
CREATE DATABASE taskflow_test OWNER taskflow;
```

### 4. Run migrations

```bash
# First time only — initialise Alembic
make db-init

# Generate initial migration from models
make db-migrate msg="initial schema"

# Apply migrations
make db-upgrade
```

### 5. Seed sample data

```bash
make seed
```

This creates 7 users, 3 projects, 15 tasks, and sample comments. See output for login credentials.

### 6. Start the server

```bash
make run           # Flask dev server with hot-reload
# OR
make run-prod      # Gunicorn (production mode locally)
```

Server starts at `http://localhost:5000`

---

## Testing

```bash
make test          # All tests
make test-unit     # Unit tests only (no DB required for schema tests)
make test-cov      # Tests + coverage report
```

Tests use a separate `taskflow_test` database and roll back after each test.

---

## API Overview

All business endpoints are under `/api/v1/`. Authentication required on all except `/auth/*`.

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout

GET    /api/v1/users/me
PUT    /api/v1/users/me

GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/:id
PUT    /api/v1/projects/:id
DELETE /api/v1/projects/:id
POST   /api/v1/projects/:id/members

GET    /api/v1/projects/:id/tasks
POST   /api/v1/projects/:id/tasks
GET    /api/v1/tasks/:id
PUT    /api/v1/tasks/:id
PATCH  /api/v1/tasks/:id/status
PATCH  /api/v1/tasks/:id/assign

GET    /api/v1/tasks/:id/comments
POST   /api/v1/tasks/:id/comments
PUT    /api/v1/comments/:id
DELETE /api/v1/comments/:id
```

Full API implementation is delivered in Phase 3.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `FLASK_ENV` | Yes | `development` | `development`, `staging`, `production` |
| `SECRET_KEY` | Yes (prod) | — | Flask secret key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes (prod) | — | JWT signing secret |
| `APP_VERSION` | No | `1.0.0` | Match to Docker image tag |
| `PORT` | No | `5000` | Application port |
| `LOG_LEVEL` | No | `INFO` | Log verbosity |
| `DB_POOL_SIZE` | No | `5` | SQLAlchemy pool size |
| `DB_MAX_OVERFLOW` | No | `10` | Max extra connections |
| `JWT_ACCESS_TOKEN_MINUTES` | No | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_DAYS` | No | `7` | Refresh token lifetime |
| `REDIS_URL` | No | `memory://` | Rate limit storage |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins (comma-separated) |
| `GUNICORN_WORKERS` | No | `(2×CPU)+1` | Gunicorn worker count |
| `BCRYPT_LOG_ROUNDS` | No | `12` | Password hash cost factor |

---

## Project Structure

```
taskflow-api/
├── app/
│   ├── __init__.py          Application factory (create_app)
│   ├── config.py            Environment-based configuration
│   ├── extensions.py        Flask extensions (db, jwt, limiter...)
│   ├── models/              SQLAlchemy models
│   │   ├── base.py          BaseModel (UUID PK, timestamps)
│   │   ├── user.py          User + UserRole
│   │   ├── project.py       Project + ProjectMember
│   │   ├── task.py          Task + TaskStatus + TaskPriority
│   │   ├── comment.py       Comment
│   │   └── activity_log.py  ActivityLog (audit trail)
│   ├── api/v1/              Route blueprints
│   │   ├── system.py        /health, /ready
│   │   ├── auth/            POST /auth/* (Phase 3)
│   │   ├── users/           GET/PUT /users/* (Phase 3)
│   │   ├── projects/        CRUD /projects/* (Phase 3)
│   │   ├── tasks/           CRUD /tasks/* (Phase 3)
│   │   └── comments/        CRUD /comments/* (Phase 3)
│   ├── schemas/             Marshmallow validation schemas
│   ├── middleware/          Correlation ID, security headers
│   └── utils/               Response helpers, pagination, logging
├── migrations/              Alembic migration files
├── tests/
│   ├── conftest.py          Shared pytest fixtures
│   ├── unit/                Model unit tests
│   └── integration/         HTTP endpoint tests
├── scripts/
│   ├── seed_data.py         Sample data for dev/staging
│   └── wait_for_db.sh       Docker entrypoint — waits for DB + runs migrations
├── .env.example             All supported environment variables
├── gunicorn.conf.py         Production WSGI config
├── wsgi.py                  Application entry point
├── Makefile                 Developer workflow commands
└── requirements.txt         Production dependencies
```

---

## Database Schema

```
users              → UUID PK, username, email, password_hash, role, is_active
projects           → UUID PK, name, description, status, owner_id (FK→users)
project_members    → UUID PK, project_id (FK), user_id (FK), role
tasks              → UUID PK, title, description, status, priority, project_id (FK),
                     creator_id (FK), assignee_id (FK), due_date, completed_at
comments           → UUID PK, content, task_id (FK), author_id (FK), is_edited
activity_logs      → UUID PK, action, entity_type, entity_id, user_id (FK),
                     project_id (FK), metadata (JSONB)
```

All tables use UUID primary keys and include `created_at` / `updated_at` timestamps.

---

## Observability

**Logs** — All logs are JSON on stdout. Feed into CloudWatch, Datadog, or Loki.

```json
{"timestamp":"2024-01-15T10:30:00Z","level":"info","event":"Task created",
 "correlation_id":"abc-123","task_id":"uuid","user_id":"uuid"}
```

**Metrics** — Prometheus endpoint at `/metrics`. Includes:
- HTTP request count by method, path, status
- Request latency histograms
- DB connection pool statistics

**Tracing** — Every request gets `X-Correlation-ID`. Set by client or auto-generated. Returned in response headers and included in every log line.

---

## Deployment Notes (for DevOps)

- **Entrypoint**: Use `scripts/wait_for_db.sh gunicorn -c gunicorn.conf.py wsgi:app`
- **Migrations**: Run automatically by `wait_for_db.sh` before each deploy
- **Health Check**: `GET /health` → 200 within 5s
- **Readiness**: `GET /ready` → 200 = safe to send traffic
- **Graceful Shutdown**: SIGTERM → Gunicorn drains in-flight requests (30s window)
- **Scaling**: Stateless — run as many replicas as needed. Watch `DB_POOL_SIZE × replicas < PostgreSQL max_connections`

---

*Phase 3 delivers: complete implementation of all API routes, services layer, and full test suite.*

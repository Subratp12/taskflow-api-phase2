"""
Gunicorn Production Configuration — TaskFlow API
─────────────────────────────────────────────────
This file is used by gunicorn when running in production.
Command: gunicorn -c gunicorn.conf.py wsgi:app

DevOps note:
  - GUNICORN_WORKERS env var controls worker count
  - stdout/stderr logs feed directly into your log aggregator
  - On SIGTERM, gunicorn finishes in-flight requests before shutdown
    (graceful_timeout controls the window)
"""

import multiprocessing
import os

# ── Binding ────────────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# ── Workers ────────────────────────────────────────────────────────────────────
# Formula: (2 × CPU cores) + 1
# Override via GUNICORN_WORKERS env var for container deployments
workers = int(
    os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1)
)
worker_class = 'sync'       # sync works well with PostgreSQL + SQLAlchemy
worker_connections = 1000
threads = 1

# ── Timeouts ───────────────────────────────────────────────────────────────────
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '30'))
graceful_timeout = 30       # Seconds to finish in-flight requests on SIGTERM
keepalive = 5

# ── Process Naming ─────────────────────────────────────────────────────────────
proc_name = 'taskflow-api'
default_proc_name = 'taskflow-api'

# ── Logging (JSON to stdout for log aggregation) ───────────────────────────────
accesslog = '-'             # stdout
errorlog = '-'              # stdout
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()
capture_output = True
enable_stdio_inheritance = True

# Log format: timestamp, method, path, status, response-time (microseconds)
access_log_format = (
    '{"time":"%(t)s","remote_addr":"%(h)s","method":"%(m)s",'
    '"path":"%(U)s","status":%(s)s,"response_bytes":%(b)s,'
    '"duration_us":%(D)s,"referer":"%(f)s","user_agent":"%(a)s"}'
)

# ── Security ───────────────────────────────────────────────────────────────────
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
forwarded_allow_ips = os.environ.get('FORWARDED_ALLOW_IPS', '127.0.0.1')

# ── Server Hooks (Lifecycle Logging) ───────────────────────────────────────────
def on_starting(server):
    server.log.info(
        f"TaskFlow API starting | workers={workers} | bind={bind}"
    )


def on_exit(server):
    server.log.info("TaskFlow API shutting down — goodbye")


def pre_fork(server, worker):
    pass


def post_fork(server, worker):
    server.log.debug(f"Worker forked | pid={worker.pid}")


def worker_exit(server, worker):
    server.log.info(f"Worker exited | pid={worker.pid}")


def worker_abort(worker):
    worker.log.error(f"Worker aborted | pid={worker.pid}")

"""
TaskFlow API — Configuration
─────────────────────────────────────────────────────────────────────────────
All values come from environment variables. No hardcoded secrets.

Usage:
    from app.config import config
    app.config.from_object(config['production'])
"""

import os
from datetime import timedelta


class Config:
    """Base configuration — shared across all environments."""

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = 'TaskFlow API'
    APP_VERSION: str = os.environ.get('APP_VERSION', '1.0.0')
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO').upper()

    # ── Database ───────────────────────────────────────────────────────────────
    _raw_db_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://taskflow:taskflow_pass@localhost:5432/taskflow',
    )
    # Heroku/Railway use postgres:// — SQLAlchemy 2.x requires postgresql://
    SQLALCHEMY_DATABASE_URI: str = (
        _raw_db_url.replace('postgres://', 'postgresql://', 1)
        if _raw_db_url.startswith('postgres://')
        else _raw_db_url
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_RECORD_QUERIES: bool = False

    # Connection Pool — critical for horizontal scaling
    # DevOps: POOL_SIZE × container_count must stay under PostgreSQL max_connections
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800)),
        'pool_pre_ping': True,   # Detect stale connections — essential for long-running containers
    }

    # ── JWT ────────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        minutes=int(os.environ.get('JWT_ACCESS_TOKEN_MINUTES', 30))
    )
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(
        days=int(os.environ.get('JWT_REFRESH_TOKEN_DAYS', 7))
    )
    JWT_ALGORITHM: str = 'HS256'
    JWT_TOKEN_LOCATION: list = ['headers']
    JWT_HEADER_NAME: str = 'Authorization'
    JWT_HEADER_TYPE: str = 'Bearer'
    JWT_ERROR_MESSAGE_KEY: str = 'message'

    # ── Rate Limiting ──────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT: str = os.environ.get('RATELIMIT_DEFAULT', '100 per minute')
    RATELIMIT_STORAGE_URL: str = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_HEADERS_ENABLED: bool = True
    RATELIMIT_SWALLOW_ERRORS: bool = False

    # ── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_SUPPORTS_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 600

    # ── Pagination ─────────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = int(os.environ.get('DEFAULT_PAGE_SIZE', 20))
    MAX_PAGE_SIZE: int = int(os.environ.get('MAX_PAGE_SIZE', 100))

    # ── Password Hashing ───────────────────────────────────────────────────────
    BCRYPT_LOG_ROUNDS: int = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))


class DevelopmentConfig(Config):
    """
    Local development — verbose, fast, relaxed security.
    """
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False       # Set True to log SQL queries
    BCRYPT_LOG_ROUNDS: int = 4          # Faster hashing during local dev
    RATELIMIT_ENABLED: bool = False     # No rate limits in dev


class StagingConfig(Config):
    """
    Staging environment — mirrors production behaviour.
    Used for integration tests and pre-release validation.
    """
    DEBUG: bool = False
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = False


class ProductionConfig(Config):
    """
    Production — hardened, secrets must be set in environment.
    """
    DEBUG: bool = False
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = False
    BCRYPT_LOG_ROUNDS: int = 13         # Stronger hashing in production

    @classmethod
    def validate(cls) -> None:
        """
        Fail fast if required secrets are missing.
        Called by create_app() when FLASK_ENV=production.
        """
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise EnvironmentError(
                f"FATAL: Missing required environment variables: {missing}\n"
                f"Check your secrets management configuration."
            )
        # Warn if default dev secrets are used in production
        if os.environ.get('SECRET_KEY') == 'dev-secret-change-in-production':
            raise EnvironmentError("FATAL: Default SECRET_KEY must not be used in production.")
        if os.environ.get('JWT_SECRET_KEY') == 'jwt-dev-secret-change-in-production':
            raise EnvironmentError("FATAL: Default JWT_SECRET_KEY must not be used in production.")


class TestingConfig(Config):
    """
    Test environment — in-memory rate limiting, fast bcrypt, isolated DB.
    """
    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'TEST_DATABASE_URL',
        'postgresql://taskflow:taskflow_pass@localhost:5432/taskflow_test',
    )
    SQLALCHEMY_ECHO: bool = False
    BCRYPT_LOG_ROUNDS: int = 4
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=5)
    RATELIMIT_ENABLED: bool = False
    WTF_CSRF_ENABLED: bool = False


# ── Config Selector ────────────────────────────────────────────────────────────
config: dict = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}

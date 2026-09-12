"""
Central configuration. Everything that could change between dev/demo/prod
lives here and is pulled from environment variables (see .env.example).

DO NOT hardcode secrets elsewhere in the codebase — import `settings` instead.
"""
import logging
import warnings

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEFAULT_JWT_SECRET = "metroscan_legal_metrology_jwt_secure_secret_key_2026_sih"


class Settings(BaseSettings):
    APP_NAME: str = "METROSCAN AI - Compliance Intelligence Platform"

    # --- Database ---
    # Defaults to a local SQLite file so the backend runs standalone on day 1,
    # even before Dev5's PostgreSQL schema / server is ready.
    # Swap to Postgres by setting DATABASE_URL in .env, e.g.:
    # postgresql://user:password@localhost:5432/metroscan
    DATABASE_URL: str = "sqlite:///./metroscan.db"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours - long enough for a demo day

    # --- Bootstrap admin seed ---
    # POST /auth/promote requires an *existing* admin token, so there is no
    # self-service way to create the very first admin.  These credentials are
    # auto-created (or promoted) on every startup by seed_admin() in db/session.py.
    # Override both values in .env before any real deployment.
    ADMIN_EMAIL: str = "admin@metroscan.local"
    ADMIN_PASSWORD: str = "CHANGE_ME_ADMIN_PASSWORD"

    # --- File uploads ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 15

    # --- CORS (frontend runs on a different port) ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "*",  # loosen for hackathon demo; tighten before anything real
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# ---------------------------------------------------------------------------
# Startup safety check — warn loudly if the JWT secret is still the default.
# This is intentionally a warning (not an exception) so demos can still run
# in a pinch, but the message will be visible in the server log.
# ---------------------------------------------------------------------------
if settings.JWT_SECRET_KEY in ("CHANGE_ME_BEFORE_DEMO", "changeme", "secret"):
    _msg = (
        "\n"
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║  ⚠️  SECURITY WARNING — METROSCAN AI                         ║\n"
        "║  JWT_SECRET_KEY is still the default placeholder value.     ║\n"
        "║  Anyone can forge tokens with this secret!                  ║\n"
        "║  Set a real random value in your .env before the demo.      ║\n"
        "║  e.g.: openssl rand -hex 32                                 ║\n"
        "╚══════════════════════════════════════════════════════════════╝"
    )
    warnings.warn(_msg, stacklevel=1)
    logger.warning(_msg)

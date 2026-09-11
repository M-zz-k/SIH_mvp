from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.db_models import Base

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)


def seed_admin():
    """Ensure the bootstrap admin account exists.

    POST /auth/promote requires an existing admin token, so without this
    seeder there would be no way to ever create the first admin — every
    self-registered user is forced to 'inspector'.

    Imports are done locally to avoid circular imports: this module is
    imported very early (before all models are fully wired up).

    Safe to call on every app startup, not just the first time.
    """
    # Local imports to prevent circular dependency at module load time.
    from app.core.config import settings
    from app.core.security import hash_password
    from app.models.db_models import User, UserRoleDB

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if user is None:
            # First run — create the admin account from scratch.
            db.add(User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role=UserRoleDB.admin,
            ))
            db.commit()
        elif user.role != UserRoleDB.admin:
            # Account exists but was somehow demoted — re-promote it.
            user.role = UserRoleDB.admin
            db.commit()
        # If already admin, nothing to do.
    finally:
        db.close()


def get_db():
    """FastAPI dependency — yields a DB session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

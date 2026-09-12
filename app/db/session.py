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
        # Default accounts to seed for demonstration & evaluation
        default_accounts = [
            (settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, UserRoleDB.admin),
            ("inspector@doca.gov.in", "doca2026", UserRoleDB.inspector),
            ("supervisor@doca.gov.in", "doca2026", UserRoleDB.supervisor),
            ("admin@doca.gov.in", "doca2026", UserRoleDB.admin),
        ]

        for email, password, role in default_accounts:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                db.add(User(
                    email=email,
                    hashed_password=hash_password(password),
                    role=role,
                ))
                db.commit()
            elif role == UserRoleDB.admin and user.role != UserRoleDB.admin:
                user.role = UserRoleDB.admin
                db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI dependency — yields a DB session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

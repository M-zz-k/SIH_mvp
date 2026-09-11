"""
database.py
Shared DB engine + session for the whole team.

Usage (any teammate's file):
    from database import get_session
    from models import Inspection

    with get_session() as session:
        session.add(Inspection(...))
        session.commit()
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your "
        "Supabase connection string."
    )

# echo=False keeps the console quiet; flip to True if you need to debug SQL.
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


def init_db() -> None:
    """
    Creates all tables defined in models.py if they don't already exist.
    Quick path for hackathon speed — no migration history.
    Safe to call multiple times; it won't touch existing tables/data.
    """
    # Import models here (not at top) so init_db() always sees every
    # table class registered on SQLModel.metadata, even if models.py
    # is edited after this file.
    import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    """
    Context-manager session for safe read/write with automatic cleanup.

        with get_session() as session:
            session.add(obj)
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

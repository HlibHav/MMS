"""
<<<<<<< HEAD
Session helpers for SQLAlchemy.
"""

from functools import lru_cache
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@lru_cache(maxsize=1)
def get_engine():
    """
    Return a configured SQLAlchemy engine.

    Defaults to SQLite file `tmp/mms_data.db` if DATABASE_URL is not set to reduce
    dialect-specific DDL differences while mirroring the documented schema.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        os.makedirs("tmp", exist_ok=True)
        url = "sqlite:///tmp/mms_data.db"
    return create_engine(url, future=True)


def get_session():
    """Yield a new SQLAlchemy session bound to the shared engine."""
    engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
=======
Database session utilities.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoSuchModuleError

from db.base import ensure_metadata_column

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mms.db")

# Use future engine for SQLAlchemy 2 style
engine = create_engine(DATABASE_URL, future=True)

# Backward-compatibility migration: rename legacy 'metadata' column if present.
ensure_metadata_column(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_session():
    """FastAPI dependency to provide a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
>>>>>>> dbf51a57d90587fa2ae6397ac9a6c322b870fe89

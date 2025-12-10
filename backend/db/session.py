"""
Database session utilities.
"""

import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@lru_cache(maxsize=1)
def get_engine():
    """
    Return a configured SQLAlchemy engine.

    Defaults to SQLite file `tmp/mms_data.db` if DATABASE_URL is not set to keep
    local dev simple while matching documented schema types.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        os.makedirs("tmp", exist_ok=True)
        url = "sqlite:///tmp/mms_data.db"
    return create_engine(url, future=True)


def get_session():
    """FastAPI dependency to provide a DB session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

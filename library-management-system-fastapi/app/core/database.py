"""
Database engine & session setup.

This is the ONLY place the SQLAlchemy engine is created. Repositories
and services never touch `create_engine` directly - they receive a
`Session` through dependency injection (see app/dependencies/database.py).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # verifies connections are alive before using them
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class that all ORM models inherit from."""
    pass

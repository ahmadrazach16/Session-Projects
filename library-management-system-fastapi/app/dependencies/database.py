"""
Database session dependency.

FastAPI's `Depends(get_db)` pattern: a fresh Session is created per
request and always closed afterward, regardless of success/failure.
"""
from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

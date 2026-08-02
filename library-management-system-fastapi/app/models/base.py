"""
Shared base mixin for ORM models.

Using a mixin for id/timestamps avoids repeating the same columns in
every model (DRY) and demonstrates Inheritance: every model gains
these fields "for free" by inheriting from TimestampMixin.
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    """Adds created_at / updated_at columns to any model that inherits it."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

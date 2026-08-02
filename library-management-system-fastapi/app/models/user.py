"""
User model.

Represents an authenticated user of the system. The `role` field
drives role-based authorization (see app/dependencies/auth.py).
"""
import enum

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    """
    Roles supported by the system.

    - ADMIN: full access (manage books, users, issue/return on behalf of anyone)
    - LIBRARIAN: manage books, issue/return books
    - MEMBER: search books, borrow/return own books, view own history
    """
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    MEMBER = "MEMBER"


class User(Base, TimestampMixin):
    """
    User ORM entity.

    Note: this class only describes DATA and its persistence mapping.
    All password hashing / validation logic lives in the service layer
    and app.core.security - keeping this class focused on one
    responsibility (SRP).
    """
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        ENUM(
            UserRole,
            name="user_role",
            create_type=False,
        ),
        default=UserRole.MEMBER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # One user can have many loans
    loans: Mapped[list["Loan"]] = relationship(
        "Loan",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
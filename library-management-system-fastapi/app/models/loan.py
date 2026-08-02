"""
Loan model.

Represents the transaction of a book being issued to a member,
and (eventually) returned. Owns the status/fine bookkeeping columns.
"""
import enum

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class LoanStatus(str, enum.Enum):
    ISSUED = "ISSUED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class Loan(Base, TimestampMixin):
    __tablename__ = "loans"

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    issue_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )

    due_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )

    return_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
    )

    fine_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    status: Mapped[LoanStatus] = mapped_column(
        ENUM(
            LoanStatus,
            name="loan_status",
            create_type=False,
        ),
        default=LoanStatus.ISSUED,
        nullable=False,
    )

    book: Mapped["Book"] = relationship(
        "Book",
        back_populates="loans",
    )

    member: Mapped["User"] = relationship(
        "User",
        back_populates="loans",
    )

    def __repr__(self) -> str:
        return (
            f"<Loan id={self.id} "
            f"book_id={self.book_id} "
            f"member_id={self.member_id} "
            f"status={self.status}>"
        )
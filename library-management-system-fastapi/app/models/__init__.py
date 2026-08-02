"""
Import every ORM model here so that `Base.metadata` is fully populated
when Alembic (or `Base.metadata.create_all`) inspects it.
"""
from app.models.user import User, UserRole  # noqa: F401
from app.models.book import Book  # noqa: F401
from app.models.loan import Loan, LoanStatus  # noqa: F401

__all__ = ["User", "UserRole", "Book", "Loan", "LoanStatus"]

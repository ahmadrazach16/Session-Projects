"""
Loan repository interface.
"""
from abc import abstractmethod

from app.models.loan import Loan
from app.repositories.interfaces.base_repository import IBaseRepository


class ILoanRepository(IBaseRepository[Loan]):

    @abstractmethod
    def get_active_loan(self, book_id: int, member_id: int) -> Loan | None:
        """Return the currently ISSUED loan for this book+member combination, if any."""
        ...

    @abstractmethod
    def count_active_loans_by_member(self, member_id: int) -> int:
        ...

    @abstractmethod
    def get_loans_by_member(self, member_id: int) -> list[Loan]:
        ...

    @abstractmethod
    def get_overdue_loans(self) -> list[Loan]:
        ...

    @abstractmethod
    def get_all_filtered(
        self,
        member_id: int | None = None,
        book_id: int | None = None,
        status: str | None = None,
    ) -> list[Loan]:
        ...

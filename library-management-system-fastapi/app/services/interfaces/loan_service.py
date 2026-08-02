"""
Loan service interface.
"""
from abc import ABC, abstractmethod

from app.models.loan import Loan


class ILoanService(ABC):

    @abstractmethod
    def issue_book(self, book_id: int, member_id: int) -> Loan:
        ...

    @abstractmethod
    def return_book(self, book_id: int, member_id: int) -> tuple[Loan, float]:
        ...

    @abstractmethod
    def get_member_history(self, member_id: int) -> list[Loan]:
        ...

    @abstractmethod
    def get_overdue_loans(self) -> list[Loan]:
        ...

    @abstractmethod
    def list_loans(
        self, member_id: int | None, book_id: int | None, status: str | None
    ) -> list[Loan]:
        ...

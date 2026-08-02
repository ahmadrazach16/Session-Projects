"""
LoanService - the heart of the Library Management System.

Orchestrates Book, User and Loan repositories to implement the
"issue book" and "return book" use cases, including business rules
around availability, borrowing limits and fine calculation.

Depends only on repository ABSTRACTIONS (Dependency Inversion
Principle) - the concrete Postgres implementations are injected via
the constructor and wired in app/dependencies/services.py.
"""
import logging
from datetime import date, timedelta

from app.core.config import settings
from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.models.loan import Loan, LoanStatus
from app.repositories.interfaces.book_repository import IBookRepository
from app.repositories.interfaces.loan_repository import ILoanRepository
from app.repositories.interfaces.user_repository import IUserRepository
from app.services.interfaces.loan_service import ILoanService

logger = logging.getLogger(__name__)


class LoanService(ILoanService):

    def __init__(
        self,
        book_repository: IBookRepository,
        user_repository: IUserRepository,
        loan_repository: ILoanRepository,
    ):
        self.book_repository = book_repository
        self.user_repository = user_repository
        self.loan_repository = loan_repository

    def issue_book(self, book_id: int, member_id: int) -> Loan:
        """
        Feature: Issue a book to a member.

        Business rules enforced:
        - Book must exist and have available copies.
        - Member must exist.
        - Member cannot exceed MAX_ACTIVE_LOANS_PER_MEMBER.
        """
        book = self.book_repository.get_by_id(book_id)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")

        member = self.user_repository.get_by_id(member_id)
        if not member:
            raise NotFoundError(f"Member with id {member_id} not found")

        if book.available_copies <= 0:
            raise BusinessRuleViolation(f"'{book.title}' has no available copies right now")

        active_loans = self.loan_repository.count_active_loans_by_member(member_id)
        if active_loans >= settings.MAX_ACTIVE_LOANS_PER_MEMBER:
            raise BusinessRuleViolation(
                f"Member has reached the maximum limit of "
                f"{settings.MAX_ACTIVE_LOANS_PER_MEMBER} active loans"
            )

        # Mutate book availability
        book.available_copies -= 1
        self.book_repository.update(book)

        issue_date = date.today()
        due_date = issue_date + timedelta(days=settings.LOAN_PERIOD_DAYS)

        loan = Loan(
            book_id=book_id,
            member_id=member_id,
            issue_date=issue_date,
            due_date=due_date,
            status=LoanStatus.ISSUED,
        )
        created = self.loan_repository.create(loan)
        logger.info(
            "Book issued: book_id=%s member_id=%s due_date=%s", book_id, member_id, due_date
        )
        return created

    def return_book(self, book_id: int, member_id: int) -> tuple[Loan, float]:
        """
        Feature: Return a borrowed book, calculating any late fine.
        Fine = FINE_PER_DAY * number of days late (0 if returned on time).
        """
        active_loan = self.loan_repository.get_active_loan(book_id, member_id)
        if not active_loan:
            raise NotFoundError("No active loan found for this book and member")

        book = self.book_repository.get_by_id(book_id)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")

        return_date = date.today()
        fine = self._calculate_fine(active_loan.due_date, return_date)

        active_loan.return_date = return_date
        active_loan.fine_amount = fine
        active_loan.status = LoanStatus.RETURNED
        self.loan_repository.update(active_loan)

        # Mutate book availability
        book.available_copies += 1
        self.book_repository.update(book)

        logger.info(
            "Book returned: book_id=%s member_id=%s fine=%s", book_id, member_id, fine
        )
        return active_loan, fine

    @staticmethod
    def _calculate_fine(due_date: date, return_date: date) -> float:
        days_late = (return_date - due_date).days
        return round(days_late * settings.FINE_PER_DAY, 2) if days_late > 0 else 0.0

    def get_member_history(self, member_id: int) -> list[Loan]:
        member = self.user_repository.get_by_id(member_id)
        if not member:
            raise NotFoundError(f"Member with id {member_id} not found")
        return self.loan_repository.get_loans_by_member(member_id)

    def get_overdue_loans(self) -> list[Loan]:
        return self.loan_repository.get_overdue_loans()

    def list_loans(
        self,
        member_id: int | None = None,
        book_id: int | None = None,
        status: str | None = None,
    ) -> list[Loan]:
        return self.loan_repository.get_all_filtered(
            member_id=member_id, book_id=book_id, status=status
        )

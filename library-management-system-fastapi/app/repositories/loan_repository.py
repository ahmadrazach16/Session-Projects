"""
SQLAlchemy implementation of ILoanRepository.
"""
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.repositories.interfaces.loan_repository import ILoanRepository


class LoanRepository(ILoanRepository):
    """Concrete Postgres/SQLAlchemy repository for Loan entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, entity_id: int) -> Loan | None:
        return self.db.query(Loan).filter(Loan.id == entity_id).first()

    def get_active_loan(self, book_id: int, member_id: int) -> Loan | None:
        return (
            self.db.query(Loan)
            .filter(
                Loan.book_id == book_id,
                Loan.member_id == member_id,
                Loan.status != LoanStatus.RETURNED,
            )
            .order_by(Loan.id.desc())
            .first()
        )

    def count_active_loans_by_member(self, member_id: int) -> int:
        return (
            self.db.query(Loan)
            .filter(Loan.member_id == member_id, Loan.status != LoanStatus.RETURNED)
            .count()
        )

    def get_loans_by_member(self, member_id: int) -> list[Loan]:
        return (
            self.db.query(Loan)
            .filter(Loan.member_id == member_id)
            .order_by(Loan.id.desc())
            .all()
        )

    def get_overdue_loans(self) -> list[Loan]:
        from datetime import date

        return (
            self.db.query(Loan)
            .filter(Loan.status == LoanStatus.ISSUED, Loan.due_date < date.today())
            .order_by(Loan.due_date.asc())
            .all()
        )

    def get_all_filtered(
        self,
        member_id: int | None = None,
        book_id: int | None = None,
        status: str | None = None,
    ) -> list[Loan]:
        query = self.db.query(Loan)
        if member_id is not None:
            query = query.filter(Loan.member_id == member_id)
        if book_id is not None:
            query = query.filter(Loan.book_id == book_id)
        if status is not None:
            query = query.filter(Loan.status == status)
        return query.order_by(Loan.id.desc()).all()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Loan]:
        return self.db.query(Loan).offset(skip).limit(limit).all()

    def create(self, entity: Loan) -> Loan:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Loan) -> Loan:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity_id: int) -> bool:
        loan = self.get_by_id(entity_id)
        if not loan:
            return False
        self.db.delete(loan)
        self.db.commit()
        return True

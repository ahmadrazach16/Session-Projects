"""
Loan API routes.

Issue/Return are restricted to ADMIN and LIBRARIAN roles (a librarian
performs the physical hand-over of the book). Members can view their
own loan history.
"""
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import (
    get_current_active_user,
    require_librarian_or_admin,
)
from app.dependencies.services import get_loan_service
from app.models.user import User
from app.schemas.loan import (
    LoanIssueRequest,
    LoanResponse,
    LoanReturnRequest,
    LoanReturnResponse,
)
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/issue", response_model=LoanResponse, dependencies=[Depends(require_librarian_or_admin)])
def issue_book(
    request: LoanIssueRequest,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Issue a book to a member. Requires LIBRARIAN or ADMIN role."""
    return loan_service.issue_book(request.book_id, request.member_id)


@router.post("/return", response_model=LoanReturnResponse, dependencies=[Depends(require_librarian_or_admin)])
def return_book(
    request: LoanReturnRequest,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Return a borrowed book, calculating any late fine. Requires LIBRARIAN or ADMIN role."""
    loan, fine = loan_service.return_book(request.book_id, request.member_id)
    return LoanReturnResponse(loan=loan, fine_charged=fine)


@router.get("", response_model=list[LoanResponse], dependencies=[Depends(require_librarian_or_admin)])
def list_loans(
    member_id: int | None = Query(default=None),
    book_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    loan_service: LoanService = Depends(get_loan_service),
):
    """List/filter all loans. Requires LIBRARIAN or ADMIN role."""
    return loan_service.list_loans(member_id=member_id, book_id=book_id, status=status)


@router.get("/overdue", response_model=list[LoanResponse], dependencies=[Depends(require_librarian_or_admin)])
def get_overdue_loans(loan_service: LoanService = Depends(get_loan_service)):
    """Overdue books report. Requires LIBRARIAN or ADMIN role."""
    return loan_service.get_overdue_loans()


@router.get("/my-history", response_model=list[LoanResponse])
def get_my_loan_history(
    current_user: User = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service),
):
    """Any authenticated member can view their OWN loan history."""
    return loan_service.get_member_history(current_user.id)


@router.get("/member/{member_id}", response_model=list[LoanResponse], dependencies=[Depends(require_librarian_or_admin)])
def get_member_loan_history(
    member_id: int,
    loan_service: LoanService = Depends(get_loan_service),
):
    """Librarian/Admin view of any member's loan history."""
    return loan_service.get_member_history(member_id)

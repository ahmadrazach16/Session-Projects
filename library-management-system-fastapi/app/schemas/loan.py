"""
Pydantic schemas for Loan (issue/return) requests/responses.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.loan import LoanStatus


class LoanIssueRequest(BaseModel):
    book_id: int
    member_id: int


class LoanReturnRequest(BaseModel):
    book_id: int
    member_id: int


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    issue_date: date
    due_date: date
    return_date: date | None
    fine_amount: float
    status: LoanStatus
    created_at: datetime


class LoanReturnResponse(BaseModel):
    loan: LoanResponse
    fine_charged: float

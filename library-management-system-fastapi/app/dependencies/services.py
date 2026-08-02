"""
Service factory dependencies.

This module is the application's Composition Root: the ONLY place
where concrete repository classes are instantiated and injected into
concrete service classes. API route handlers depend on the service
INTERFACES (return type hints) and never construct services or
repositories themselves.

To swap PostgreSQL for another database, only the repository imports
below would need to change - services, routes and business logic stay
untouched.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.repositories.book_repository import BookRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.book_service import BookService
from app.services.loan_service import LoanService


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    return AuthService(user_repository)


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    book_repository = BookRepository(db)
    return BookService(book_repository)


def get_loan_service(db: Session = Depends(get_db)) -> LoanService:
    book_repository = BookRepository(db)
    user_repository = UserRepository(db)
    loan_repository = LoanRepository(db)
    return LoanService(book_repository, user_repository, loan_repository)

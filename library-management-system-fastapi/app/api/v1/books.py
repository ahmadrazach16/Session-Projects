"""
Book API routes.

Add/Update/Delete are restricted to ADMIN and LIBRARIAN roles.
Search/List/Get are available to any authenticated user.
"""
from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_active_user, require_librarian_or_admin
from app.dependencies.services import get_book_service
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_librarian_or_admin)],
)
def add_book(
    book_data: BookCreate,
    book_service: BookService = Depends(get_book_service),
):
    """Add a new book to the catalogue. Requires LIBRARIAN or ADMIN role."""
    return book_service.add_book(book_data)


@router.get("", response_model=list[BookResponse], dependencies=[Depends(get_current_active_user)])
def search_books(
    title: str | None = Query(default=None, description="Filter by title (partial match)"),
    author: str | None = Query(default=None, description="Filter by author (partial match)"),
    category: str | None = Query(default=None, description="Filter by category (partial match)"),
    book_service: BookService = Depends(get_book_service),
):
    """Search / list books. Any authenticated user can search the catalogue."""
    return book_service.search_books(title=title, author=author, category=category)


@router.get("/{book_id}", response_model=BookResponse, dependencies=[Depends(get_current_active_user)])
def get_book(
    book_id: int,
    book_service: BookService = Depends(get_book_service),
):
    """Get a single book by id."""
    return book_service.get_book(book_id)


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    dependencies=[Depends(require_librarian_or_admin)],
)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    book_service: BookService = Depends(get_book_service),
):
    """Update a book. Requires LIBRARIAN or ADMIN role."""
    return book_service.update_book(book_id, book_data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_librarian_or_admin)],
)
def delete_book(
    book_id: int,
    book_service: BookService = Depends(get_book_service),
):
    """Delete a book. Requires LIBRARIAN or ADMIN role."""
    book_service.delete_book(book_id)

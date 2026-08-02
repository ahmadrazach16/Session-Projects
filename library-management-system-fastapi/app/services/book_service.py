"""
BookService - business logic for book management use cases.

Depends only on IBookRepository (abstraction) - Dependency Inversion
Principle. Contains no HTTP or SQLAlchemy specific code (framework
independence, a core Clean Architecture rule).
"""
import logging

from app.core.exceptions import ConflictError, NotFoundError
from app.models.book import Book
from app.repositories.interfaces.book_repository import IBookRepository
from app.schemas.book import BookCreate, BookUpdate
from app.services.interfaces.book_service import IBookService

logger = logging.getLogger(__name__)


class BookService(IBookService):

    def __init__(self, book_repository: IBookRepository):
        self.book_repository = book_repository

    def add_book(self, book_data: BookCreate) -> Book:
        if self.book_repository.get_by_isbn(book_data.isbn):
            raise ConflictError(f"A book with ISBN '{book_data.isbn}' already exists")

        book = Book(
            title=book_data.title,
            author=book_data.author,
            isbn=book_data.isbn,
            category=book_data.category,
            total_copies=book_data.total_copies,
            available_copies=book_data.total_copies,
        )
        created = self.book_repository.create(book)
        logger.info("Book added: %s (id=%s)", created.title, created.id)
        return created

    def get_book(self, book_id: int) -> Book:
        book = self.book_repository.get_by_id(book_id)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")
        return book

    def search_books(
        self, title: str | None = None, author: str | None = None, category: str | None = None
    ) -> list[Book]:
        return self.book_repository.search(title=title, author=author, category=category)

    def update_book(self, book_id: int, book_data: BookUpdate) -> Book:
        book = self.get_book(book_id)  # raises NotFoundError if missing

        update_fields = book_data.model_dump(exclude_unset=True)

        # Business rule: total_copies can never drop below the number of copies
        # currently on loan (i.e. below (total - available) already borrowed).
        if "total_copies" in update_fields:
            currently_borrowed = book.total_copies - book.available_copies
            new_total = update_fields["total_copies"]
            if new_total < currently_borrowed:
                raise ConflictError(
                    f"Cannot set total_copies to {new_total}: "
                    f"{currently_borrowed} copies are currently borrowed"
                )
            # Keep available_copies consistent with the new total
            book.available_copies = new_total - currently_borrowed

        for field, value in update_fields.items():
            setattr(book, field, value)

        updated = self.book_repository.update(book)
        logger.info("Book updated: id=%s", book_id)
        return updated

    def delete_book(self, book_id: int) -> None:
        self.get_book(book_id)  # raises NotFoundError if missing
        self.book_repository.delete(book_id)
        logger.info("Book deleted: id=%s", book_id)

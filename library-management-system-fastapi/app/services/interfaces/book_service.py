"""
Book service interface.
"""
from abc import ABC, abstractmethod

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class IBookService(ABC):

    @abstractmethod
    def add_book(self, book_data: BookCreate) -> Book:
        ...

    @abstractmethod
    def get_book(self, book_id: int) -> Book:
        ...

    @abstractmethod
    def search_books(
        self, title: str | None, author: str | None, category: str | None
    ) -> list[Book]:
        ...

    @abstractmethod
    def update_book(self, book_id: int, book_data: BookUpdate) -> Book:
        ...

    @abstractmethod
    def delete_book(self, book_id: int) -> None:
        ...

"""
Book repository interface.
"""
from abc import abstractmethod

from app.models.book import Book
from app.repositories.interfaces.base_repository import IBaseRepository


class IBookRepository(IBaseRepository[Book]):

    @abstractmethod
    def get_by_isbn(self, isbn: str) -> Book | None:
        ...

    @abstractmethod
    def search(
        self,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Book]:
        ...

"""
SQLAlchemy implementation of IBookRepository.
"""
from sqlalchemy.orm import Session

from app.models.book import Book
from app.repositories.interfaces.book_repository import IBookRepository


class BookRepository(IBookRepository):
    """Concrete Postgres/SQLAlchemy repository for Book entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, entity_id: int) -> Book | None:
        return self.db.query(Book).filter(Book.id == entity_id).first()

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.db.query(Book).filter(Book.isbn == isbn).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Book]:
        return self.db.query(Book).offset(skip).limit(limit).all()

    def search(
        self,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Book]:
        query = self.db.query(Book)
        if title:
            query = query.filter(Book.title.ilike(f"%{title}%"))
        if author:
            query = query.filter(Book.author.ilike(f"%{author}%"))
        if category:
            query = query.filter(Book.category.ilike(f"%{category}%"))
        return query.offset(skip).limit(limit).all()

    def create(self, entity: Book) -> Book:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Book) -> Book:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity_id: int) -> bool:
        book = self.get_by_id(entity_id)
        if not book:
            return False
        self.db.delete(book)
        self.db.commit()
        return True

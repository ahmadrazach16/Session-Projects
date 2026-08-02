"""
SQLAlchemy implementation of IUserRepository.

This is the ONLY class in the whole application that runs SQLAlchemy
queries against the `users` table. Swapping databases or ORMs later
means changing only this file - services and API layers are untouched
(Open/Closed Principle in action).
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.interfaces.user_repository import IUserRepository


class UserRepository(IUserRepository):
    """Concrete Postgres/SQLAlchemy repository for User entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, entity_id: int) -> User | None:
        return self.db.query(User).filter(User.id == entity_id).first()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, entity: User) -> User:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: User) -> User:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity_id: int) -> bool:
        user = self.get_by_id(entity_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

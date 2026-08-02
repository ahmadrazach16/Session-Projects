"""
User repository interface.

Extends the generic contract with user-specific lookups. Kept as its
own interface (rather than bloating IBaseRepository) in line with the
Interface Segregation Principle - callers that only need book
operations should never be forced to depend on user-lookup methods.
"""
from abc import abstractmethod

from app.models.user import User
from app.repositories.interfaces.base_repository import IBaseRepository


class IUserRepository(IBaseRepository[User]):

    @abstractmethod
    def get_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        ...

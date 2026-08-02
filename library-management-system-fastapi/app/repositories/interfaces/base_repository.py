"""
Generic repository interface.

This ABC defines the contract that ANY repository implementation must
satisfy, regardless of the underlying storage technology. Services
depend on these abstractions, never on concrete SQLAlchemy classes
(Dependency Inversion Principle).

Using Python's `abc` module + generics demonstrates Abstraction and
enables Liskov Substitution: any concrete subclass can be swapped in
without breaking callers.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ModelType = TypeVar("ModelType")


class IBaseRepository(ABC, Generic[ModelType]):
    """Abstract CRUD contract shared by all repositories."""

    @abstractmethod
    def get_by_id(self, entity_id: int) -> ModelType | None:
        ...

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        ...

    @abstractmethod
    def create(self, entity: ModelType) -> ModelType:
        ...

    @abstractmethod
    def update(self, entity: ModelType) -> ModelType:
        ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        ...

"""
Auth service interface.
"""
from abc import ABC, abstractmethod

from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate


class IAuthService(ABC):

    @abstractmethod
    def register(self, user_data: UserCreate) -> User:
        ...

    @abstractmethod
    def authenticate(self, username: str, password: str) -> User:
        ...

    @abstractmethod
    def login(self, username: str, password: str) -> Token:
        ...

    @abstractmethod
    def get_current_user(self, token: str) -> User:
        ...

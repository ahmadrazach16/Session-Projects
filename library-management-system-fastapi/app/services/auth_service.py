"""
AuthService - handles registration, login and current-user resolution.

Depends ONLY on IUserRepository (an abstraction), never on the
concrete UserRepository/SQLAlchemy class directly - Dependency
Inversion Principle. The concrete repository is injected via the
constructor (Dependency Injection), which is wired up in
app/dependencies/services.py.
"""
import logging

from app.core.exceptions import ConflictError, InvalidCredentialsError, NotFoundError
from app.core.security import JWTHandler, PasswordHasher
from app.models.user import User, UserRole
from app.repositories.interfaces.user_repository import IUserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.services.interfaces.auth_service import IAuthService

logger = logging.getLogger(__name__)


class AuthService(IAuthService):

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def register(self, user_data: UserCreate) -> User:
        """Registers a new user. Self-registration always creates a MEMBER."""
        if self.user_repository.get_by_username(user_data.username):
            raise ConflictError(f"Username '{user_data.username}' is already taken")
        if self.user_repository.get_by_email(user_data.email):
            raise ConflictError(f"Email '{user_data.email}' is already registered")

        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=PasswordHasher.hash(user_data.password),
            role=UserRole.MEMBER,
        )
        created = self.user_repository.create(user)
        logger.info("New user registered: %s (id=%s)", created.username, created.id)
        return created

    def authenticate(self, username: str, password: str) -> User:
        """Verifies credentials and returns the User if valid."""
        user = self.user_repository.get_by_username(username)
        if not user or not PasswordHasher.verify(password, user.hashed_password):
            logger.warning("Failed login attempt for username=%s", username)
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InvalidCredentialsError("This account has been deactivated")
        return user

    def login(self, username: str, password: str) -> Token:
        user = self.authenticate(username, password)
        access_token = JWTHandler.create_access_token(
            subject=str(user.id), extra_claims={"role": user.role.value, "username": user.username}
        )
        refresh_token = JWTHandler.create_refresh_token(subject=str(user.id))
        logger.info("User logged in: %s (id=%s)", user.username, user.id)
        return Token(access_token=access_token, refresh_token=refresh_token)

    def get_current_user(self, token: str) -> User:
        """Decodes a JWT access token and resolves the corresponding User."""
        payload = JWTHandler.decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise NotFoundError("User not found")

        user = self.user_repository.get_by_id(int(user_id))
        if not user:
            raise NotFoundError("User not found")
        if not user.is_active:
            raise InvalidCredentialsError("This account has been deactivated")
        return user

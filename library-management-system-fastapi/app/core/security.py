"""
Security utilities.

Encapsulates ALL password hashing and JWT logic in one place
(Single Responsibility Principle). No other module should import
jose/passlib directly - they depend on this abstraction instead.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

# bcrypt is the industry-standard adaptive hashing algorithm for passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """
    Encapsulates password hashing behaviour.
    Kept as its own class so hashing strategy can be swapped later
    (e.g. argon2) without touching any calling code (Open/Closed Principle).
    """

    @staticmethod
    def hash(plain_password: str) -> str:
        return pwd_context.hash(plain_password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)


class JWTHandler:
    """
    Encapsulates JWT creation and decoding.
    Only this class knows about the `jose` library and the secret key.
    """

    @staticmethod
    def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
        if extra_claims:
            to_encode.update(extra_claims)
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode = {"sub": subject, "exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as exc:
            raise InvalidTokenError("Could not validate credentials") from exc

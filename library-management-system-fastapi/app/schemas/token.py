"""
Pydantic schemas for authentication tokens.
"""
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: str | None = None
    type: str | None = None
    exp: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str

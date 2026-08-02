"""
Pydantic schemas for User-related requests/responses.

These are pure DTOs (Data Transfer Objects) - they define the API
"contract" and are completely separate from the SQLAlchemy ORM model
(separation of concerns between the persistence layer and the API layer).
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for user self-registration. Role defaults to MEMBER (see service)."""
    password: str = Field(..., min_length=8, max_length=128)


class UserCreateByAdmin(UserCreate):
    """Schema allowing an ADMIN to create a user with an explicit role."""
    role: UserRole = UserRole.MEMBER


class UserUpdate(BaseModel):
    """Partial update - all fields optional."""
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class UserResponse(UserBase):
    """Public-facing user representation. NEVER includes the password hash."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

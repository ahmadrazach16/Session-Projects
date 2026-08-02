"""
Pydantic schemas for Book-related requests/responses.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    category: str = Field(default="General", max_length=100)


class BookCreate(BookBase):
    total_copies: int = Field(..., ge=1)


class BookUpdate(BaseModel):
    """Partial update - all fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    total_copies: int | None = Field(default=None, ge=0)


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_copies: int
    available_copies: int
    created_at: datetime


class BookSearchParams(BaseModel):
    """Query parameters for GET /books search endpoint."""
    title: str | None = None
    author: str | None = None
    category: str | None = None

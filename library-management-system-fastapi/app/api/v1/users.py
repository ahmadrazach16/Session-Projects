"""
User management API routes (admin-facing).

Listing/viewing all users is restricted to ADMIN - regular members
only ever see their own profile via /auth/me.
"""
from fastapi import APIRouter, Depends

from app.core.exceptions import NotFoundError
from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    """List all registered users. Requires ADMIN role."""
    return UserRepository(db).get_all()


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a single user by id. Requires ADMIN role."""
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User with id {user_id} not found")
    return user

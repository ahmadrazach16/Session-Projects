"""
Auth API routes.

Thin HTTP layer: parses the request, delegates to AuthService, formats
the response. Contains NO business logic itself.
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies.auth import get_current_active_user
from app.dependencies.services import get_auth_service
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user. New users are always created with the MEMBER role."""
    return auth_service.register(user_data)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    OAuth2-compatible login endpoint (form-encoded username/password).
    Using OAuth2PasswordRequestForm makes this compatible with the
    "Authorize" button in FastAPI's auto-generated Swagger UI.
    """
    return auth_service.login(form_data.username, form_data.password)


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user

"""
Authentication & role-based authorization dependencies.

`get_current_user` resolves the JWT bearer token into a User.
`RoleChecker` is a small callable class (Polymorphism via __call__)
that can be parametrized per-route with the roles allowed to access
it, e.g. `Depends(RoleChecker([UserRole.ADMIN, UserRole.LIBRARIAN]))`.
"""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import ForbiddenError
from app.dependencies.services import get_auth_service
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Resolves the currently authenticated user from the bearer token."""
    return auth_service.get_current_user(token)


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


class RoleChecker:
    """
    Callable dependency that restricts a route to a specific set of roles.

    Usage:
        @router.post("/books", dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.LIBRARIAN]))])

    Implemented as a class with __call__ so FastAPI can use it as a
    dependency while still letting us parametrize allowed_roles per route
    (a small but real demonstration of encapsulated, reusable behaviour).
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(
                f"Role '{current_user.role.value}' is not permitted to perform this action"
            )
        return current_user


# Pre-built role checkers for common cases, reused across routers
require_admin = RoleChecker([UserRole.ADMIN])
require_librarian_or_admin = RoleChecker([UserRole.ADMIN, UserRole.LIBRARIAN])
require_any_role = RoleChecker([UserRole.ADMIN, UserRole.LIBRARIAN, UserRole.MEMBER])

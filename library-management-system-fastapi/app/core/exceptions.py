"""
Custom exception hierarchy.

Domain/service layers raise these instead of HTTPException directly -
this keeps business logic framework-agnostic (a core Clean Architecture
rule: inner layers must not depend on FastAPI). The API layer's
exception handlers (see app/main.py) translate these into proper
HTTP responses.
"""


class AppException(Exception):
    """Base class for all application-specific exceptions."""

    status_code: int = 500
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    message = "Resource not found"


class ValidationError(AppException):
    status_code = 400
    message = "Validation failed"


class ConflictError(AppException):
    status_code = 409
    message = "Resource already exists"


class BusinessRuleViolation(AppException):
    status_code = 422
    message = "Business rule violated"


class UnauthorizedError(AppException):
    status_code = 401
    message = "Authentication required"


class InvalidTokenError(UnauthorizedError):
    message = "Invalid or expired token"


class ForbiddenError(AppException):
    status_code = 403
    message = "You do not have permission to perform this action"


class InvalidCredentialsError(UnauthorizedError):
    message = "Incorrect username or password"

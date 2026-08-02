"""
FastAPI application entry point.

Responsible ONLY for:
- creating the FastAPI app instance
- registering middleware
- registering global exception handlers (translating AppException -> HTTP)
- mounting routers

No business logic lives here (Single Responsibility Principle).
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A Library Management System built with FastAPI, Clean Architecture and SOLID principles.",
    debug=settings.DEBUG,
)

# --- CORS ---
origins = (
    ["*"] if settings.ALLOWED_ORIGINS == "*" else settings.ALLOWED_ORIGINS.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global exception handler ---
# Every custom AppException (and its subclasses: NotFoundError,
# ConflictError, BusinessRuleViolation, ForbiddenError, etc.) is caught
# here ONCE and translated into a consistent JSON error response.
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("AppException handled: %s - %s", exc.__class__.__name__, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.__class__.__name__, "message": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
        },
    )


# --- Routers ---
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Simple liveness/readiness probe used by Docker/Kubernetes."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.on_event("startup")
async def on_startup():
    logger.info("%s v%s starting up (env=%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("%s shutting down", settings.APP_NAME)

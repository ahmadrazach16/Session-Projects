"""
Application configuration.

Uses pydantic-settings to load configuration from environment variables
(and a local .env file during development). Centralizing config here
means no other module ever reads os.environ directly - Single
Responsibility Principle applied to configuration management.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    APP_NAME: str = "Library Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/library_db"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # --- JWT / Security ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Business rules ---
    LOAN_PERIOD_DAYS: int = 14
    FINE_PER_DAY: float = 10.0
    MAX_ACTIVE_LOANS_PER_MEMBER: int = 3

    # --- CORS ---
    ALLOWED_ORIGINS: str = "*"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings factory.
    lru_cache ensures the .env file is parsed only once per process,
    and the same Settings instance is reused everywhere (singleton-like).
    """
    return Settings()


settings = get_settings()

# app/config.py
import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Application
    APP_NAME: str = Field(default="Code Intelligence Backend", env="APP_NAME")
    APP_ENV: str = Field(default="development", env="APP_ENV")  # development, staging, production
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    RELOAD: bool = Field(default=True, env="RELOAD")  # Only for development

    # CORS
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        env="ALLOWED_ORIGINS"
    )

    # Database - Qdrant
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = Field(default="code_chunks", env="QDRANT_COLLECTION_NAME")

    # Embeddings
    EMBEDDING_MODEL: str = Field(default="microsoft/codebert-base", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSION: int = Field(default=768, env="EMBEDDING_DIMENSION")
    EMBEDDING_DEVICE: str = Field(default="cpu", env="EMBEDDING_DEVICE")  # cpu, cuda, mps

    # Search Configuration
    DEFAULT_TOP_K: int = Field(default=10, env="DEFAULT_TOP_K")
    MAX_TOP_K: int = Field(default=100, env="MAX_TOP_K")
    MIN_SCORE: float = Field(default=0.3, env="MIN_SCORE")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=False, env="RATE_LIMIT_ENABLED")  # Enable in production
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")  # Per minute
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # Seconds

    # Authentication
    AUTH_ENABLED: bool = Field(default=False, env="AUTH_ENABLED")  # Enable in production
    API_KEYS: dict = Field(default={}, env="API_KEYS")  # JSON: {"key": "secret"}
    JWT_SECRET: Optional[str] = Field(default=None, env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # Caching (Redis/In-Memory)
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")  # Enable caching
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")  # Use Redis backend
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Cache TTLs (in seconds)
    CACHE_TTL_SEARCH: int = Field(default=3600, env="CACHE_TTL_SEARCH")  # 1 hour
    CACHE_TTL_INDEX: int = Field(default=300, env="CACHE_TTL_INDEX")  # 5 minutes
    CACHE_TTL_GENERAL: int = Field(default=1800, env="CACHE_TTL_GENERAL")  # 30 minutes

    # Celery (optional, for async tasks)
    CELERY_ENABLED: bool = Field(default=False, env="CELERY_ENABLED")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")

    # Monitoring & Logging
    SENTRY_ENABLED: bool = Field(default=False, env="SENTRY_ENABLED")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    PROMETHEUS_ENABLED: bool = Field(default=False, env="PROMETHEUS_ENABLED")

    # File Upload
    MAX_REPO_SIZE_MB: int = Field(default=500, env="MAX_REPO_SIZE_MB")
    TEMP_DIR: str = Field(default="/tmp", env="TEMP_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# For quick access
settings = get_settings()

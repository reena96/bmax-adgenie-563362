"""
Configuration management using Pydantic Settings.

This module handles environment-based configuration for the FastAPI application.
All settings are loaded from environment variables with validation.
"""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have defaults for development and can be overridden
    via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="DEBUG",
        description="Logging level"
    )
    app_name: str = Field(
        default="Zapcut Ad Generation API",
        description="Application name"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version"
    )

    # Database Settings
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/zapcut_db_dev",
        description="PostgreSQL connection URL"
    )
    db_pool_size: int = Field(
        default=20,
        description="Database connection pool size"
    )
    db_max_overflow: int = Field(
        default=40,
        description="Maximum overflow connections for database pool"
    )

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for queue and caching"
    )

    # JWT/Authentication Settings
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expiry_minutes: int = Field(
        default=30,
        description="Access token expiry time in minutes"
    )

    # AWS/S3 Settings
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID"
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS secret access key"
    )
    s3_bucket_name: str | None = Field(
        default=None,
        description="S3 bucket name for asset storage"
    )

    # External API Keys (for future use)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key"
    )
    replicate_api_token: str | None = Field(
        default=None,
        description="Replicate API token"
    )

    # CORS Settings
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS configuration"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that database URL is a PostgreSQL URL."""
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate that Redis URL is properly formatted."""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with redis://")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def get_database_url(self, async_driver: bool = False) -> str:
        """
        Get database URL with optional async driver.

        Args:
            async_driver: If True, returns URL for async SQLAlchemy driver

        Returns:
            Database connection URL
        """
        if async_driver:
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url.replace("postgresql://", "postgresql+psycopg2://")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency for FastAPI routes to access settings.

    Returns:
        Application settings instance
    """
    return settings

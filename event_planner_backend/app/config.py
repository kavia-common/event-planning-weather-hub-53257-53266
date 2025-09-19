"""Application configuration and environment variable handling for the Event Planner backend."""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Base configuration loaded from environment variables.

    Notes:
        Do not hardcode secrets. Ensure the corresponding environment variables are set
        by deployment/orchestrator. Provide .env.example separately for guidance.
    """
    # Flask config
    DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    TESTING: bool = os.getenv("FLASK_TESTING", "false").lower() in ("1", "true", "yes")
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

    # Database
    # Prefer DATABASE_URL if present, fallback to individual components for convenience
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    DB_DIALECT: str = os.getenv("DB_DIALECT", "sqlite")
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "")

    # OpenWeather
    OPENWEATHER_API_KEY: str | None = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_BASE_URL: str = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")

    # CORS
    CORS_ALLOW_ORIGINS: str = os.getenv("CORS_ALLOW_ORIGINS", "*")

    # API Metadata
    API_TITLE: str = os.getenv("API_TITLE", "Event Planner API")
    API_VERSION: str = os.getenv("API_VERSION", "v1")

    # Pagination default
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))

    def build_sqlalchemy_uri(self) -> str:
        """Build a SQLAlchemy-compatible URI from environment variables.

        Supports:
        - DATABASE_URL directly if provided
        - sqlite (default): sqlite:///events.db
        - Postgres: postgresql+psycopg2://user:pass@host:port/db
        - MySQL: mysql+pymysql://user:pass@host:port/db
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        dialect = (self.DB_DIALECT or "sqlite").lower()
        if dialect == "sqlite":
            # Local file fallback
            db_path = self.DB_NAME or "events.db"
            return f"sqlite:///{db_path}"

        user_part = self.DB_USER or ""
        if self.DB_PASSWORD:
            user_part += f":{self.DB_PASSWORD}"
        if user_part:
            user_part += "@"

        host_part = self.DB_HOST or "localhost"
        if self.DB_PORT:
            host_part += f":{self.DB_PORT}"

        dbname = self.DB_NAME or "events"
        if dialect in ("postgres", "postgresql"):
            return f"postgresql+psycopg2://{user_part}{host_part}/{dbname}"
        if dialect in ("mysql", "mariadb"):
            return f"mysql+pymysql://{user_part}{host_part}/{dbname}"
        # Fallback to sqlite if unknown
        return f"sqlite:///{dbname}.db"

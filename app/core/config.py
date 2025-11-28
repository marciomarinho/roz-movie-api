"""Application configuration management."""
import logging
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Movie API"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api"

    # PostgreSQL Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = "mysecretpassword"

    # Authentication
    api_key: Optional[str] = None

    # Keycloak/OAuth2 Configuration
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "movie-realm"
    keycloak_client_id: str = "movie-api-client"
    keycloak_client_secret: Optional[str] = None
    
    # Enable/disable authentication (for dev/test)
    auth_enabled: bool = True

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application configuration instance.
    """
    return Settings()

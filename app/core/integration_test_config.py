"""Configuration for integration tests."""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class IntegrationTestSettings(BaseSettings):
    """Settings for integration tests using testcontainers."""

    # PostgreSQL Container Configuration
    postgres_image: str = "postgres:15-alpine"
    postgres_user: str = "testuser"
    postgres_password: str = "testpassword"
    postgres_db: str = "movies_test"
    # NOTE: postgres_port is NOT set here - testcontainers will dynamically assign it!
    # This prevents port conflicts with existing PostgreSQL instances
    
    # Container startup timeout (seconds)
    container_startup_timeout: int = 60
    
    # Path to CSV file for loading test data
    test_data_csv: str = "data/movies_small.csv"
    
    # Application configuration for tests
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    
    # API configuration
    api_key_enabled: bool = False
    api_key: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        env_file = ".env.test"
        env_prefix = "INTEGRATION_TEST_"
        case_sensitive = False


def get_integration_test_settings() -> IntegrationTestSettings:
    """Get integration test settings.

    Returns:
        IntegrationTestSettings: Loaded settings.
    """
    return IntegrationTestSettings()

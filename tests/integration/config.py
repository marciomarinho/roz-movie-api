"""Configuration for integration tests."""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class IntegrationTestSettings(BaseSettings):

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
    
    # Keycloak configuration for tests
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "movie-realm"
    keycloak_client_id: str = "movie-api-client"
    keycloak_client_secret: Optional[str] = None
    keycloak_test_user: str = "movieuser"
    keycloak_test_password: str = "moviepassword"
    
    class Config:
        """Pydantic config."""
        env_file = ".env.test"
        env_prefix = "INTEGRATION_TEST_"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.keycloak_client_secret and os.path.exists(".env.keycloak"):
            try:
                with open(".env.keycloak", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("CLIENT_SECRET="):
                            self.keycloak_client_secret = line.split("=", 1)[1].strip('"\'')
                            break
            except Exception:
                pass


def get_integration_test_settings() -> IntegrationTestSettings:
    return IntegrationTestSettings()

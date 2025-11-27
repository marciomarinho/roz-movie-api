"""Pytest configuration and fixtures for integration tests."""
import asyncio
import os
from urllib.parse import urlparse

import pytest
import psycopg2
from fastapi import FastAPI
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer

from app.core.config import Settings
from app.core.database import DatabasePool
from app.core.integration_test_config import IntegrationTestSettings
from scripts.init_db import initialize_database

# Create container instance at module level
postgres = PostgresContainer("postgres:15-alpine")


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    """
    Setup fixture to start PostgreSQL container and initialize database.
    Uses module scope so it runs once for all tests in the module.
    Uses finalizer for cleanup to ensure teardown runs even if setup fails.
    """
    settings = IntegrationTestSettings()
    
    print("\n" + "="*60)
    print("[*] Starting PostgreSQL container...")
    print("="*60)
    
    # Start container
    postgres.start()
    print(f"[✓] Container started")
    
    # Get connection details
    db_url = postgres.get_connection_url()
    host = postgres.get_container_host_ip()
    port = postgres.get_exposed_port(5432)
    
    print("db_url" + db_url)
    print("host" + host)
    print("port" + port)

    print(f"    Connection URL: postgresql://{settings.postgres_user}:***@{host}:{port}/{settings.postgres_db}")
    print(f"[✓] Database is ready!")
    
    # Initialize database (create tables and load data)
    print("\n[*] Creating tables and loading test data...")
    parsed = urlparse(db_url)
    initialize_database(
        host=parsed.hostname,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        csv_file_path=settings.test_data_csv,
    )
    print("[✓] Database initialized")
    print("="*60 + "\n")
    
    # Store connection details in environment for other fixtures
    os.environ["DB_CONN"] = db_url
    os.environ["DB_HOST"] = host
    os.environ["DB_PORT"] = str(port)
    os.environ["DB_USERNAME"] = settings.postgres_user
    os.environ["DB_PASSWORD"] = settings.postgres_password
    os.environ["DB_NAME"] = settings.postgres_db
    
    # Define cleanup function
    def cleanup():
        print("\n" + "="*60)
        print("[*] Stopping PostgreSQL container...")
        print("="*60)
        try:
            postgres.stop()
            print("[✓] Container stopped")
        except Exception as e:
            print(f"[!] Error stopping container: {e}")
        print("="*60 + "\n")
    
    # Register cleanup to run after all tests
    request.addfinalizer(cleanup)


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get database connection URL.
    
    Returns:
        str: Database connection URL.
    """
    settings = IntegrationTestSettings()
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    return f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{host}:{port}/{settings.postgres_db}"


@pytest.fixture(scope="function")
def test_settings() -> Settings:
    """Create Settings with test database connection.
    
    Returns:
        Settings: Configured for test database.
    """
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USERNAME")
    db_password = os.environ.get("DB_PASSWORD")
    
    if not all([host, port, db_name, db_user, db_password]):
        raise RuntimeError(
            f"Database environment variables not set. "
            f"Host={host}, Port={port}, Name={db_name}, User={db_user}, Pass={bool(db_password)}"
        )
    
    return Settings(
        db_host=host,
        db_port=int(port),
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        api_key="test-api-key-123",
    )


@pytest.fixture(scope="function")
def app(test_settings: Settings):
    """
    Create and configure FastAPI application for testing.
    
    Args:
        test_settings: Test database settings.
        
    Yields:
        FastAPI: The configured application.
    """
    print("\n[*] Starting FastAPI application...")
    
    # Override get_settings before importing app.main
    from app.core import config as config_module
    original_get_settings = config_module.get_settings
    config_module.get_settings = lambda: test_settings
    
    try:
        # Import create_app AFTER overriding get_settings
        from app.main import create_app
        
        application = create_app()
        print("[✓] Application started")
        
        yield application
    finally:
        print("[*] Stopping FastAPI application...")
        # Restore original settings
        config_module.get_settings = original_get_settings
        
        # Close database connections
        try:
            if DatabasePool.is_initialized():
                DatabasePool.close()
                print("[✓] Database pool closed")
        except Exception as e:
            print(f"[!] Error closing pool: {e}")


@pytest.fixture(scope="function")
def client(app: FastAPI) -> TestClient:
    """Create TestClient for the application.
    
    Args:
        app: The FastAPI application.
        
    Returns:
        TestClient: HTTP test client.
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def db_connection(test_db_url: str):
    """Create direct database connection for raw SQL operations.
    
    Args:
        test_db_url: The test database connection URL.
        
    Yields:
        psycopg2 connection object.
    """
    parsed = urlparse(test_db_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
    )
    
    try:
        yield conn
    finally:
        conn.close()


def pytest_configure(config):
    """Configure pytest - handle Windows asyncio."""
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

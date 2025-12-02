"""Pytest configuration and fixtures for integration tests."""
import asyncio
import os
from urllib.parse import urlparse
import time
import subprocess
import json

import pytest
import psycopg2
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import DatabasePool
from tests.integration.config import IntegrationTestSettings
from scripts.init_db import initialize_database


@pytest.fixture(scope="session")
def postgres_container():
    settings = IntegrationTestSettings()

    print("\n" + "=" * 60)
    print("[*] Starting PostgreSQL container...")
    print("=" * 60)

    container_id = None
    host_port = None
    
    try:
        # Start PostgreSQL container directly with Docker CLI
        cmd = [
            "docker", "run", "-d",
            "-e", f"POSTGRES_USER={settings.postgres_user}",
            "-e", f"POSTGRES_PASSWORD={settings.postgres_password}",
            "-e", f"POSTGRES_DB={settings.postgres_db}",
            "-p", "0:5432",  # Bind to random host port
            "postgres:15-alpine"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()
        print(f"[✓] Container started: {container_id[:12]}")
        
        # Get the mapped port
        inspect_cmd = ["docker", "port", container_id, "5432"]
        port_result = subprocess.run(inspect_cmd, capture_output=True, text=True, check=True)
        port_mapping = port_result.stdout.strip()  # e.g., "127.0.0.1:32768"
        host_port = int(port_mapping.split(":")[-1])
        container_host = "127.0.0.1"
        
        print(f"    Host: {container_host}")
        print(f"    Port: {host_port}")

        # Manually check if connection is ready
        print("\n[*] Waiting for PostgreSQL to be ready...")
        max_retries = 30
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                test_conn = psycopg2.connect(
                    host=container_host,
                    port=host_port,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                    database=settings.postgres_db,
                    connect_timeout=3,
                )
                test_conn.close()
                print(f"[✓] PostgreSQL is ready!")
                break
            except psycopg2.OperationalError as e:
                if attempt < max_retries - 1:
                    print(f"    Attempt {attempt + 1}/{max_retries}: Connection failed, retrying...")
                    time.sleep(retry_delay)
                else:
                    print(f"[!] PostgreSQL failed to start after {max_retries} attempts")
                    raise

        # Initialize schema & data
        print("\n[*] Creating tables and loading test data...")

        initialize_database(
            host=container_host,
            port=host_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            csv_file_path=settings.test_data_csv,
        )
        print("[✓] Database initialized")
        print("=" * 60 + "\n")

        # Expose connection details via env for other fixtures
        os.environ["DB_HOST"] = container_host
        os.environ["DB_PORT"] = str(host_port)
        os.environ["DB_USERNAME"] = settings.postgres_user
        os.environ["DB_PASSWORD"] = settings.postgres_password
        os.environ["DB_NAME"] = settings.postgres_db

        yield {
            "host": container_host,
            "port": host_port,
            "user": settings.postgres_user,
            "password": settings.postgres_password,
            "database": settings.postgres_db,
            "container_id": container_id,
        }

    finally:
        print("\n" + "=" * 60)
        print("[*] Stopping PostgreSQL container...")
        print("=" * 60)
        if container_id:
            try:
                stop_cmd = ["docker", "stop", container_id]
                subprocess.run(stop_cmd, capture_output=True, check=True)
                
                rm_cmd = ["docker", "rm", container_id]
                subprocess.run(rm_cmd, capture_output=True, check=True)
                print("[✓] Container stopped and removed")
            except Exception as e:
                print(f"[!] Error stopping container: {e}")
        print("=" * 60 + "\n")


@pytest.fixture(scope="session")
def test_db_url(postgres_container) -> str:
    # We rely on env vars set in postgres_container fixture
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    user = os.environ["DB_USERNAME"]
    password = os.environ["DB_PASSWORD"]
    db_name = os.environ["DB_NAME"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


@pytest.fixture(scope="function")
def test_settings(postgres_container) -> Settings:
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USERNAME")
    db_password = os.environ.get("DB_PASSWORD")

    if not all([host, port, db_name, db_user, db_password]):
        raise RuntimeError(
            f"Database environment variables not set. "
            f"Host={host}, Port={port}, Name={db_name}, "
            f"User={db_user}, Pass={bool(db_password)}"
        )

    settings = IntegrationTestSettings()
    
    return Settings(
        db_host=host,
        db_port=int(port),
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        api_key="test-api-key-123",
        keycloak_url=settings.keycloak_url,
        keycloak_realm=settings.keycloak_realm,
        keycloak_client_id=settings.keycloak_client_id,
        keycloak_client_secret=settings.keycloak_client_secret,
        auth_enabled=True,
    )


@pytest.fixture(scope="function")
def app(test_settings: Settings):
    print("\n[*] Starting FastAPI application...")

    from app.core import config as config_module
    original_get_settings = config_module.get_settings
    config_module.get_settings = lambda: test_settings

    try:
        # Import and manually initialize dependencies
        from app.main import create_app
        import app.main as main_module
        from app.core.database import DatabasePool
        from app.repositories.movies_repository import MoviesRepository
        from app.services.movies_service import MoviesService
        
        # Initialize database pool with test settings
        DatabasePool.initialize(
            host=test_settings.db_host,
            port=test_settings.db_port,
            dbname=test_settings.db_name,
            user=test_settings.db_user,
            password=test_settings.db_password,
        )
        
        # Initialize movies service
        repository = MoviesRepository()
        main_module.movies_service = MoviesService(repository)
        
        # Create app (lifespan will try to reinitialize but that's okay, it will just update)
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
    return TestClient(app)




@pytest.fixture(scope="function")
def bearer_token() -> str:
    settings = IntegrationTestSettings()
    
    try:
        from tests.integration.keycloak_client import KeycloakTestClient
        
        keycloak_client = KeycloakTestClient(
            keycloak_url=settings.keycloak_url,
            realm=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            client_secret=settings.keycloak_client_secret,
            username=settings.keycloak_test_user,
            password=settings.keycloak_test_password,
        )
        
        token = keycloak_client.get_token()
        print(f"Obtained bearer token: {token}")
        return token
    except Exception as e:
        print(f"[!] Failed to obtain bearer token from Keycloak: {e}")
        # For local testing, return a mock token that will fail but allow tests to structure properly
        # In CI/Docker, Keycloak will be running
        raise


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, bearer_token: str) -> TestClient:
    # Store the original request method
    original_request = client.request
    
    def request_with_auth(method, url, **kwargs):
        # Add Authorization header if not already present
        if "headers" not in kwargs or kwargs["headers"] is None:
            kwargs["headers"] = {}
        
        # Check if authorization header is already present (case-insensitive)
        has_auth = any(k.lower() == "authorization" for k in kwargs["headers"].keys())
        
        if not has_auth:
            kwargs["headers"]["Authorization"] = f"Bearer {bearer_token}"
        
        return original_request(method, url, **kwargs)
    
    # Monkey-patch the request method
    client.request = request_with_auth
    return client


@pytest.fixture(scope="function")
def db_connection(test_db_url: str):
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
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

"""Pytest configuration and fixtures for unit tests."""
import os
from unittest.mock import MagicMock, patch

import pytest

from app.models.movie import Movie, MovieRead, PaginatedMovies


@pytest.fixture(autouse=True)
def clear_lru_cache():
    """Clear LRU cache before each test to avoid test pollution."""
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sample_movies() -> list[Movie]:
    """Create sample movies for testing.

    Returns:
        list[Movie]: List of sample movies.
    """
    return [
        Movie(movie_id=1, title="Toy Story (1995)", year=1995, genres=["Adventure", "Animation", "Children", "Comedy", "Fantasy"]),
        Movie(movie_id=2, title="Jumanji (1995)", year=1995, genres=["Adventure", "Children", "Fantasy"]),
        Movie(movie_id=3, title="Grumpier Old Men (1995)", year=1995, genres=["Comedy", "Romance"]),
        Movie(movie_id=4, title="Heat (1995)", year=1995, genres=["Action", "Crime", "Thriller"]),
        Movie(movie_id=5, title="The Matrix (1999)", year=1999, genres=["Action", "Sci-Fi"]),
        Movie(movie_id=6, title="Inception (2010)", year=2010, genres=["Action", "Sci-Fi", "Thriller"]),
    ]


@pytest.fixture
def mock_settings():
    """Create mock settings for testing.

    Returns:
        MagicMock: Mock settings object.
    """
    settings = MagicMock()
    settings.app_name = "Movie API"
    settings.app_version = "1.0.0"
    settings.api_v1_prefix = "/api"
    settings.api_key = None
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def mock_movies_repository(sample_movies):
    """Create a mock MoviesRepository.

    Args:
        sample_movies: List of sample movies.

    Returns:
        MagicMock: Mock repository.
    """
    repo = MagicMock()
    repo.get_movie_by_id = MagicMock(side_effect=lambda movie_id: next((m for m in sample_movies if m.movie_id == movie_id), None))
    repo.list_movies = MagicMock(return_value=(sample_movies[:3], 3))
    repo.search_movies = MagicMock(return_value=(sample_movies[:2], 2))
    return repo


@pytest.fixture
def mock_movies_service(mock_movies_repository):
    """Create a mock MoviesService.

    Args:
        mock_movies_repository: Mock repository.

    Returns:
        MagicMock: Mock service.
    """
    service = MagicMock()
    service.get_movies = MagicMock(
        return_value=PaginatedMovies(
            items=[MovieRead.from_orm(m) for m in [mock_movies_repository.get_movie_by_id(1), mock_movies_repository.get_movie_by_id(2)]],
            page=1,
            page_size=2,
            total_items=6,
            total_pages=3
        )
    )
    service.search_movies = MagicMock(
        return_value=PaginatedMovies(
            items=[MovieRead.from_orm(m) for m in [mock_movies_repository.get_movie_by_id(1)]],
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1
        )
    )
    service.get_movie = MagicMock(return_value=MovieRead.from_orm(mock_movies_repository.get_movie_by_id(1)))
    return service


@pytest.fixture
def env_no_api_key(monkeypatch):
    """Set environment with no API key.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.
    """
    monkeypatch.setenv("API_KEY", "")
    monkeypatch.delenv("API_KEY", raising=False)


@pytest.fixture
def env_with_api_key(monkeypatch):
    """Set environment with API key.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.
    """
    monkeypatch.setenv("API_KEY", "test-key-12345")


@pytest.fixture
def env_with_custom_settings(monkeypatch):
    """Set environment with custom settings.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.
    """
    monkeypatch.setenv("APP_NAME", "Test Movie API")
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

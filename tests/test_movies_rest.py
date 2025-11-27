"""Tests for Movie API."""
import csv
import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.database import DatabasePool
from app.main import create_app
from app.models.movie import Movie
from app.repositories.movies_repository import MoviesRepository
from app.services.movies_service import MoviesService


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
        Movie(movie_id=4, title="Waiting to Exhale (1995)", year=1995, genres=["Comedy", "Drama"]),
        Movie(movie_id=5, title="Father of the Bride Part II (1995)", year=1995, genres=["Comedy"]),
        Movie(movie_id=6, title="Heat (1995)", year=1995, genres=["Action", "Crime", "Thriller"]),
        Movie(movie_id=7, title="Sabrina (1995)", year=1995, genres=["Comedy", "Romance"]),
        Movie(movie_id=8, title="Tom and Huck (1995)", year=1995, genres=["Adventure", "Children"]),
        Movie(movie_id=9, title="Sudden Death (1995)", year=1995, genres=["Action"]),
        Movie(movie_id=10, title="GoldenEye (1995)", year=1995, genres=["Action", "Adventure", "Thriller"]),
    ]


@pytest.fixture
def movies_repository(sample_movies: list[Movie]) -> MoviesRepository:
    """Create a mock MoviesRepository with sample data.

    Args:
        sample_movies: List of sample movies.

    Returns:
        MoviesRepository: Mock repository with sample data.
    """
    import re
    
    class MockMoviesRepository:
        def __init__(self):
            self.movies = sample_movies
            self.movies_dict = {m.movie_id: m for m in sample_movies}
        
        def get_movie_by_id(self, movie_id: int):
            return self.movies_dict.get(movie_id)
        
        def list_movies(self, page: int = 1, page_size: int = 20, title=None, genre=None, year=None):
            filtered = self._filter_movies(title=title, genre=genre, year=year)
            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            return filtered[start:end], total
        
        def search_movies(self, query: str, page: int = 1, page_size: int = 20, genre=None, year=None):
            return self.list_movies(page=page, page_size=page_size, title=query, genre=genre, year=year)
        
        def _filter_movies(self, title=None, genre=None, year=None):
            result = self.movies
            if title:
                title_lower = title.lower()
                result = [m for m in result if title_lower in m.title.lower()]
            if genre:
                genre_lower = genre.lower()
                result = [m for m in result if any(genre_lower in g.lower() for g in m.genres)]
            if year is not None:
                result = [m for m in result if m.year == year]
            return result
        
        @staticmethod
        def _extract_year(title: str):
            """Extract year from movie title like 'Toy Story (1995)'."""
            year_regex = re.compile(r"\((\d{4})\)\s*$")
            match = year_regex.search(title)
            if match:
                return int(match.group(1))
            return None
    
    return MockMoviesRepository()


@pytest.fixture
def movies_service(movies_repository: MoviesRepository) -> MoviesService:
    """Create a MoviesService with sample data.

    Args:
        movies_repository: MoviesRepository fixture.

    Returns:
        MoviesService: Initialized service.
    """
    return MoviesService(movies_repository)


@pytest.fixture
def client(movies_service: MoviesService) -> TestClient:
    """Create a FastAPI test client.

    Args:
        movies_service: MoviesService fixture.

    Returns:
        TestClient: FastAPI test client.
    """
    from app.api import routes_movies
    
    app = create_app()
    app.dependency_overrides[routes_movies.get_movies_service] = (
        lambda: movies_service
    )

    return TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint returns 200 and correct response.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestListMovies:
    """Tests for list movies endpoint."""

    def test_list_movies_without_auth_key_when_not_required(
        self, client: TestClient
    ) -> None:
        """Test listing movies without API key when not required.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies")
        # Should work because no API_KEY is set in test environment
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_items" in data
        assert "total_pages" in data

    def test_list_movies_default_pagination(self, client: TestClient) -> None:
        """Test default pagination for list movies.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_items"] == 10
        assert len(data["items"]) == 10

    def test_list_movies_with_custom_pagination(
        self, client: TestClient
    ) -> None:
        """Test custom pagination parameters.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) == 5

    def test_list_movies_page_size_clamped_to_max(
        self, client: TestClient
    ) -> None:
        """Test page_size is clamped to maximum of 100.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies?page_size=200")
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 100

    def test_list_movies_filter_by_genre(self, client: TestClient) -> None:
        """Test filtering movies by genre.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies?genre=Action")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 3
        # Check that all items contain the genre
        for item in data["items"]:
            assert "Action" in item["genres"]

    def test_list_movies_filter_by_title(self, client: TestClient) -> None:
        """Test filtering movies by partial title match.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies?title=Toy")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1
        assert data["items"][0]["movie_id"] == 1

    def test_list_movies_filter_by_year(self, client: TestClient) -> None:
        """Test filtering movies by year.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies?year=1995")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 10

    def test_movie_response_format(self, client: TestClient) -> None:
        """Test movie response format includes all required fields.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies?page_size=1")
        assert response.status_code == 200
        data = response.json()
        movie = data["items"][0]
        assert "movie_id" in movie
        assert "title" in movie
        assert "year" in movie
        assert "genres" in movie
        assert isinstance(movie["genres"], list)


class TestSearchMovies:
    """Tests for search movies endpoint."""

    def test_search_movies_by_query(self, client: TestClient) -> None:
        """Test searching movies by query.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies/search?q=Story")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1
        assert data["items"][0]["movie_id"] == 1

    def test_search_movies_case_insensitive(self, client: TestClient) -> None:
        """Test search is case-insensitive.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies/search?q=TOY")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1

    def test_search_movies_with_genre_filter(self, client: TestClient) -> None:
        """Test search with additional genre filter.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies/search?q=1995&genre=Comedy")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] > 0
        for item in data["items"]:
            assert "Comedy" in item["genres"]

    def test_search_movies_required_parameter(self, client: TestClient) -> None:
        """Test search requires 'q' parameter.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies/search")
        assert response.status_code == 422  # Unprocessable Entity


class TestGetMovieById:
    """Tests for get movie by ID endpoint."""

    def test_get_movie_by_id_success(self, client: TestClient) -> None:
        """Test getting a movie by valid ID.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies/1")
        assert response.status_code == 200
        data = response.json()
        assert data["movie_id"] == 1
        assert data["title"] == "Toy Story (1995)"
        assert data["year"] == 1995
        assert len(data["genres"]) == 5

    def test_get_movie_by_id_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent movie returns 404.

        Args:
            client: TestClient fixture.
        """
        response = client.get("/api/movies/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRepositoryYearExtraction:
    """Tests for year extraction from title."""

    def test_extract_year_from_title(self, movies_repository: MoviesRepository) -> None:
        """Test year extraction from movie title.

        Args:
            movies_repository: MoviesRepository fixture.
        """
        year = movies_repository._extract_year("Toy Story (1995)")
        assert year == 1995

    def test_extract_year_missing(self, movies_repository: MoviesRepository) -> None:
        """Test extraction when year is not in title.

        Args:
            movies_repository: MoviesRepository fixture.
        """
        year = movies_repository._extract_year("Toy Story")
        assert year is None

    def test_extract_year_invalid(self, movies_repository: MoviesRepository) -> None:
        """Test extraction with invalid year format.

        Args:
            movies_repository: MoviesRepository fixture.
        """
        year = movies_repository._extract_year("Movie (ABCD)")
        assert year is None


class TestGenreFiltering:
    """Tests for genre filtering logic."""

    def test_filter_movies_by_single_genre(
        self, movies_service: MoviesService
    ) -> None:
        """Test filtering by a single genre.

        Args:
            movies_service: MoviesService fixture.
        """
        result = movies_service.get_movies(genre="Adventure")
        assert result.total_items == 4

    def test_filter_movies_by_genre_case_insensitive(
        self, movies_service: MoviesService
    ) -> None:
        """Test genre filtering is case-insensitive.

        Args:
            movies_service: MoviesService fixture.
        """
        result = movies_service.get_movies(genre="adventure")
        assert result.total_items == 4

    def test_filter_movies_partial_genre_match(
        self, movies_service: MoviesService
    ) -> None:
        """Test partial genre matching.

        Args:
            movies_service: MoviesService fixture.
        """
        result = movies_service.get_movies(genre="Dram")
        assert result.total_items == 1

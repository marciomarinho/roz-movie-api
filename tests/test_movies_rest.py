"""Tests for Movie API."""
import csv
import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.movies_repository import MoviesRepository
from app.services.movies_service import MoviesService


@pytest.fixture
def sample_csv_data() -> str:
    """Create sample CSV data for testing.

    Returns:
        str: Sample CSV content.
    """
    return """movieId,title,genres
1,Toy Story (1995),Adventure|Animation|Children|Comedy|Fantasy
2,Jumanji (1995),Adventure|Children|Fantasy
3,Grumpier Old Men (1995),Comedy|Romance
4,Waiting to Exhale (1995),Comedy|Drama
5,Father of the Bride Part II (1995),Comedy
6,Heat (1995),Action|Crime|Thriller
7,Sabrina (1995),Comedy|Romance
8,Tom and Huck (1995),Adventure|Children
9,Sudden Death (1995),Action
10,GoldenEye (1995),Action|Adventure|Thriller
"""


@pytest.fixture
def temp_csv_file(sample_csv_data: str) -> str:
    """Create a temporary CSV file with sample data.

    Args:
        sample_csv_data: Sample CSV content.

    Yields:
        str: Path to temporary CSV file.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    ) as f:
        f.write(sample_csv_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def movies_repository(temp_csv_file: str) -> MoviesRepository:
    """Create a MoviesRepository with sample data.

    Args:
        temp_csv_file: Path to temporary CSV file.

    Returns:
        MoviesRepository: Initialized repository.
    """
    return MoviesRepository(temp_csv_file)


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
    app = create_app()
    app.dependency_overrides[app.get("routes_movies").get_movies_service] = (
        lambda: movies_service
    )

    # Override the dependency directly from the router
    from app.api import routes_movies

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
        assert data["total_items"] == 2
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

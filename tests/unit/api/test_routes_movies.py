"""Unit tests for movie API routes."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from app.api.routes_movies import router
from app.models.movie import Movie, MovieRead, PaginatedMovies


@pytest.fixture
def mock_service():
    service = MagicMock()
    
    # Sample data
    movies = [
        Movie(movie_id=1, title="Toy Story", year=1995, genres=["Animation"]),
        Movie(movie_id=2, title="Inception", year=2010, genres=["Sci-Fi"]),
        Movie(movie_id=3, title="Heat", year=1995, genres=["Action"]),
    ]
    
    movie_reads = [
        MovieRead(movie_id=m.movie_id, title=m.title, year=m.year, genres=m.genres)
        for m in movies
    ]
    
    # Setup return values
    service.get_movies.return_value = PaginatedMovies(
        items=movie_reads,
        page=1,
        page_size=20,
        total_items=len(movies),
        total_pages=1
    )
    
    service.search_movies.return_value = PaginatedMovies(
        items=movie_reads[:1],
        page=1,
        page_size=20,
        total_items=1,
        total_pages=1
    )
    
    service.get_movie.return_value = movie_reads[0]
    
    return service


@pytest.fixture
def app(mock_service):
    app = FastAPI()
    
    # Override dependencies
    async def override_get_movies_service():
        return mock_service
    
    async def override_verify_api_key():
        # Skip API key verification in tests
        return None
    
    async def override_verify_bearer_token():
        # Skip bearer token verification in unit tests
        return {}
    
    app.include_router(router)
    
    # Apply overrides
    from app.api.routes_movies import get_movies_service
    from app.deps.auth import verify_api_key, verify_bearer_token
    
    app.dependency_overrides[get_movies_service] = override_get_movies_service
    app.dependency_overrides[verify_api_key] = override_verify_api_key
    app.dependency_overrides[verify_bearer_token] = override_verify_bearer_token
    
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestListMoviesRoute:

    def test_list_movies_default_pagination(self, client, mock_service):
        response = client.get("/api/movies")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_movies_custom_page(self, client, mock_service):
 
        mock_service.get_movies.return_value = PaginatedMovies(
            items=[],
            page=2,
            page_size=20,
            total_items=100,
            total_pages=5
        )
        
        response = client.get("/api/movies?page=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2

    def test_list_movies_custom_page_size(self, client, mock_service):

        mock_service.get_movies.return_value = PaginatedMovies(
            items=[],
            page=1,
            page_size=50,
            total_items=100,
            total_pages=2
        )
        
        response = client.get("/api/movies?page_size=50")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 50

    def test_list_movies_with_title_filter(self, client, mock_service):
        response = client.get("/api/movies?title=Toy")
        
        assert response.status_code == 200
        mock_service.get_movies.assert_called()

    def test_list_movies_with_genre_filter(self, client, mock_service):
        response = client.get("/api/movies?genre=Action")
        
        assert response.status_code == 200

    def test_list_movies_with_year_filter(self, client, mock_service):
        response = client.get("/api/movies?year=1995")
        
        assert response.status_code == 200

    def test_list_movies_invalid_page_zero(self, client, mock_service):
        response = client.get("/api/movies?page=0")
        
        # FastAPI validation should reject page=0
        assert response.status_code == 422

    def test_list_movies_invalid_page_negative(self, client, mock_service):
        response = client.get("/api/movies?page=-1")
        
        assert response.status_code == 422

    def test_list_movies_invalid_page_size_zero(self, client, mock_service):
        response = client.get("/api/movies?page_size=0")
        
        assert response.status_code == 422

    def test_list_movies_invalid_page_size_exceeds_max(self, client, mock_service):
        response = client.get("/api/movies?page_size=101")
        
        assert response.status_code == 422
        data = response.json()
        assert "page_size" in str(data).lower()

    def test_list_movies_page_size_at_max_boundary(self, client, mock_service):
        response = client.get("/api/movies?page_size=100")
        
        assert response.status_code == 200
        mock_service.get_movies.assert_called_once()
        call_args = mock_service.get_movies.call_args
        assert call_args[1]["page_size"] == 100

    def test_list_movies_title_too_long(self, client, mock_service):
        long_title = "x" * 101  # Exceeds 100 char limit
        response = client.get(f"/api/movies?title={long_title}")
        
        assert response.status_code == 422
        data = response.json()
        assert "title" in str(data).lower()

    def test_list_movies_genre_too_long(self, client, mock_service):
        long_genre = "x" * 51  # Exceeds 50 char limit
        response = client.get(f"/api/movies?genre={long_genre}")
        
        assert response.status_code == 422
        data = response.json()
        assert "genre" in str(data).lower()

    def test_list_movies_year_out_of_range_low(self, client, mock_service):
        response = client.get("/api/movies?year=1899")
        
        assert response.status_code == 422
        data = response.json()
        assert "year" in str(data).lower()

    def test_list_movies_year_out_of_range_high(self, client, mock_service):
        response = client.get("/api/movies?year=2101")
        
        assert response.status_code == 422
        data = response.json()
        assert "year" in str(data).lower()

    def test_list_movies_year_at_valid_range(self, client, mock_service):
        response = client.get("/api/movies?year=2000")
        
        assert response.status_code == 200
        mock_service.get_movies.assert_called_once()
        call_args = mock_service.get_movies.call_args
        assert call_args[1]["year"] == 2000

    def test_list_movies_response_structure(self, client, mock_service):
        response = client.get("/api/movies")
        
        data = response.json()
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_items" in data
        assert "total_pages" in data

    def test_list_movies_empty_result(self, client, mock_service):
        mock_service.get_movies.return_value = PaginatedMovies(
            items=[],
            page=1,
            page_size=20,
            total_items=0,
            total_pages=0
        )
        
        response = client.get("/api/movies")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total_items"] == 0


class TestSearchMoviesRoute:

    def test_search_movies_basic(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total_items"] >= 0

    def test_search_movies_required_query(self, client, mock_service):
        response = client.get("/api/movies/search")
        
        # Query parameter is required
        assert response.status_code == 422

    def test_search_movies_query_too_long(self, client, mock_service):
        long_query = "x" * 101  # Exceeds 100 char limit
        response = client.get(f"/api/movies/search?q={long_query}")
        
        assert response.status_code == 422
        data = response.json()
        assert "q" in str(data).lower()

    def test_search_movies_page_size_exceeds_max(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy&page_size=101")
        
        assert response.status_code == 422
        data = response.json()
        assert "page_size" in str(data).lower()

    def test_search_movies_page_size_at_max_boundary(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy&page_size=100")
        
        assert response.status_code == 200
        mock_service.search_movies.assert_called_once()
        call_args = mock_service.search_movies.call_args
        assert call_args[1]["page_size"] == 100

    def test_search_movies_genre_too_long(self, client, mock_service):
        long_genre = "x" * 51  # Exceeds 50 char limit
        response = client.get(f"/api/movies/search?q=Toy&genre={long_genre}")
        
        assert response.status_code == 422
        data = response.json()
        assert "genre" in str(data).lower()

    def test_search_movies_year_out_of_range(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy&year=1899")
        
        assert response.status_code == 422
        data = response.json()
        assert "year" in str(data).lower()

    def test_search_movies_with_pagination(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy&page=2&page_size=10")
        
        assert response.status_code == 200

    def test_search_movies_with_genre_filter(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy&genre=Animation")
        
        assert response.status_code == 200

    def test_search_movies_with_year_filter(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy&year=1995")
        
        assert response.status_code == 200

    def test_search_movies_combined_filters(self, client, mock_service):
        response = client.get(
            "/api/movies/search?q=Toy&genre=Animation&year=1995&page=1&page_size=20"
        )
        
        assert response.status_code == 200

    def test_search_movies_no_results(self, client, mock_service):
        mock_service.search_movies.return_value = PaginatedMovies(
            items=[],
            page=1,
            page_size=20,
            total_items=0,
            total_pages=0
        )
        
        response = client.get("/api/movies/search?q=NonExistent")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    def test_search_movies_case_insensitive(self, client, mock_service):
        response = client.get("/api/movies/search?q=TOY")
        
        assert response.status_code == 200

    def test_search_movies_special_characters(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy%20Story%202")
        
        assert response.status_code == 200

    def test_search_movies_response_structure(self, client, mock_service):
        response = client.get("/api/movies/search?q=Toy")
        
        data = response.json()
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_items" in data
        assert "total_pages" in data


class TestGetMovieRoute:

    def test_get_movie_by_id_found(self, client, mock_service):
        response = client.get("/api/movies/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "movie_id" in data
        assert "title" in data
        assert "year" in data
        assert "genres" in data

    def test_get_movie_by_id_not_found(self, client, mock_service):
        mock_service.get_movie.return_value = None
        
        response = client.get("/api/movies/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "999" in data["detail"]

    def test_get_movie_response_structure(self, client, mock_service):
        response = client.get("/api/movies/1")
        
        data = response.json()
        assert "movie_id" in data
        assert "title" in data
        assert "year" in data
        assert "genres" in data
        assert isinstance(data["genres"], list)

    def test_get_movie_with_invalid_id_format(self, client, mock_service):
        response = client.get("/api/movies/invalid")
        
        # Should return validation error
        assert response.status_code == 422

    def test_get_movie_with_negative_id(self, client, mock_service):
        mock_service.get_movie.return_value = None
        
        response = client.get("/api/movies/-1")
        
        # Negative IDs are allowed by FastAPI, but service returns None
        assert response.status_code == 404

    def test_get_movie_with_zero_id(self, client, mock_service):
        mock_service.get_movie.return_value = None
        
        response = client.get("/api/movies/0")
        
        assert response.status_code == 404

    def test_get_movie_with_large_id(self, client, mock_service):
        mock_service.get_movie.return_value = None
        
        response = client.get("/api/movies/999999999")
        
        assert response.status_code == 404

    def test_get_movie_response_includes_all_fields(self, client, mock_service):
        movie_read = MovieRead(
            movie_id=1,
            title="Test Movie",
            year=2020,
            genres=["Action", "Drama"]
        )
        mock_service.get_movie.return_value = movie_read
        
        response = client.get("/api/movies/1")
        
        data = response.json()
        assert data["movie_id"] == 1
        assert data["title"] == "Test Movie"
        assert data["year"] == 2020
        assert data["genres"] == ["Action", "Drama"]

    def test_get_movie_with_none_year(self, client, mock_service):
        movie_read = MovieRead(movie_id=1, title="Unknown Year", year=None)
        mock_service.get_movie.return_value = movie_read
        
        response = client.get("/api/movies/1")
        
        data = response.json()
        assert data["year"] is None

    def test_get_movie_with_empty_genres(self, client, mock_service):
        movie_read = MovieRead(movie_id=1, title="No Genres", genres=[])
        mock_service.get_movie.return_value = movie_read
        
        response = client.get("/api/movies/1")
        
        data = response.json()
        assert data["genres"] == []


class TestMovieRoutesIntegration:

    def test_routes_return_json_content_type(self, client, mock_service):
        responses = [
            client.get("/api/movies"),
            client.get("/api/movies/search?q=test"),
            client.get("/api/movies/1"),
        ]
        
        for response in responses:
            if response.status_code in (200, 404):
                assert "application/json" in response.headers.get("content-type", "")

    def test_multiple_sequential_requests(self, client, mock_service):
        response1 = client.get("/api/movies")
        response2 = client.get("/api/movies/search?q=test")
        response3 = client.get("/api/movies/1")
        
        assert all(r.status_code in (200, 404) for r in [response1, response2, response3])

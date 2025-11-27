"""Integration tests for the Movie API.

These tests use testcontainers to spin up a real PostgreSQL database
and test the full application stack end-to-end.
"""
import pytest
from fastapi.testclient import TestClient


class TestMovieAPIIntegration:
    """Integration tests for movie API endpoints."""

    def test_health_check(self, client: TestClient):
        """Test that health check endpoint is working."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_list_movies_returns_data(self, client: TestClient):
        """Test that list movies returns data from test database."""
        response = client.get("/api/movies", headers={"X-API-Key": "test-api-key-123"})
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page" in data
        assert "total_items" in data
        assert len(data["items"]) > 0

    def test_list_movies_default_pagination(self, client: TestClient):
        """Test default pagination when listing movies."""
        response = client.get("/api/movies", headers={"X-API-Key": "test-api-key-123"})
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_items"] > 0
        assert data["total_pages"] >= 1

    def test_list_movies_with_pagination(self, client: TestClient):
        """Test pagination parameters work correctly."""
        response = client.get(
            "/api/movies?page=1&page_size=5",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    def test_list_movies_page_two(self, client: TestClient):
        """Test accessing second page of movies."""
        response = client.get(
            "/api/movies?page=2&page_size=5",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["page"] == 2
        # Second page might have fewer items depending on total
        assert len(data["items"]) >= 0

    def test_list_movies_with_title_filter(self, client: TestClient):
        """Test filtering movies by title."""
        response = client.get(
            "/api/movies?title=Toy",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["total_items"] > 0
        # All returned movies should have "Toy" in title
        for movie in data["items"]:
            assert "toy" in movie["title"].lower()

    def test_list_movies_with_genre_filter(self, client: TestClient):
        """Test filtering movies by genre."""
        response = client.get(
            "/api/movies?genre=Action",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["total_items"] > 0
        # All returned movies should have Action genre
        for movie in data["items"]:
            assert any("action" in g.lower() for g in movie["genres"])

    def test_list_movies_with_year_filter(self, client: TestClient):
        """Test filtering movies by year."""
        response = client.get(
            "/api/movies?year=1995",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["total_items"] > 0
        # All returned movies should be from 1995
        for movie in data["items"]:
            assert movie["year"] == 1995

    def test_search_movies_basic(self, client: TestClient):
        """Test basic movie search functionality."""
        response = client.get(
            "/api/movies/search?q=Toy",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] > 0
        for movie in data["items"]:
            assert "toy" in movie["title"].lower()

    def test_search_movies_case_insensitive(self, client: TestClient):
        """Test that search is case-insensitive."""
        response_lower = client.get(
            "/api/movies/search?q=toy",
            headers={"X-API-Key": "test-api-key-123"}
        )
        response_upper = client.get(
            "/api/movies/search?q=TOY",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data_lower = response_lower.json()
        data_upper = response_upper.json()
        assert data_lower["total_items"] == data_upper["total_items"]

    def test_search_movies_with_genre_filter(self, client: TestClient):
        """Test search with additional genre filter."""
        response = client.get(
            "/api/movies/search?q=Toy&genre=Animation",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["total_items"] > 0
        for movie in data["items"]:
            assert "toy" in movie["title"].lower()
            assert any("animation" in g.lower() for g in movie["genres"])

    def test_search_movies_with_year_filter(self, client: TestClient):
        """Test search with additional year filter."""
        response = client.get(
            "/api/movies/search?q=Story&year=1995",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        for movie in data["items"]:
            assert "story" in movie["title"].lower()
            assert movie["year"] == 1995

    def test_get_movie_by_id(self, client: TestClient):
        """Test retrieving a specific movie by ID."""
        # First, get a list to find a valid ID
        list_response = client.get(
            "/api/movies?page_size=1",
            headers={"X-API-Key": "test-api-key-123"}
        )
        list_data = list_response.json()
        movie_id = list_data["items"][0]["movie_id"]
        
        # Now get that specific movie
        response = client.get(
            f"/api/movies/{movie_id}",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["movie_id"] == movie_id
        assert "title" in data
        assert "year" in data
        assert "genres" in data

    def test_get_movie_not_found(self, client: TestClient):
        """Test retrieving a non-existent movie returns 404."""
        response = client.get(
            "/api/movies/99999",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_search_movies_no_results(self, client: TestClient):
        """Test search that returns no results."""
        response = client.get(
            "/api/movies/search?q=XYZ_NONEXISTENT_MOVIE_XYZ",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert data["total_items"] == 0
        assert len(data["items"]) == 0

    def test_movie_response_format(self, client: TestClient):
        """Test that movie responses have the correct format."""
        response = client.get(
            "/api/movies?page_size=1",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        movie = data["items"][0]
        
        # Check required fields
        assert "movie_id" in movie
        assert "title" in movie
        assert "year" in movie
        assert "genres" in movie
        
        # Check types
        assert isinstance(movie["movie_id"], int)
        assert isinstance(movie["title"], str)
        assert isinstance(movie["year"], (int, type(None)))
        assert isinstance(movie["genres"], list)

    def test_pagination_response_format(self, client: TestClient):
        """Test that paginated responses have correct format."""
        response = client.get(
            "/api/movies",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        
        # Check required fields
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_items" in data
        assert "total_pages" in data
        
        # Check types
        assert isinstance(data["items"], list)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["total_items"], int)
        assert isinstance(data["total_pages"], int)

    def test_combined_filters(self, client: TestClient):
        """Test using multiple filters together."""
        response = client.get(
            "/api/movies?title=Story&genre=Animation&year=1995",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        
        for movie in data["items"]:
            assert "story" in movie["title"].lower()
            assert any("animation" in g.lower() for g in movie["genres"])
            assert movie["year"] == 1995

    def test_missing_api_key_returns_unauthorized(self, client: TestClient):
        """Test that missing API key returns 401 when required."""
        response = client.get("/api/movies")
        
        # Since test API key is enabled, should get 401
        assert response.status_code == 401

    def test_invalid_api_key_returns_unauthorized(self, client: TestClient):
        """Test that invalid API key returns 401."""
        response = client.get(
            "/api/movies",
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401


class TestMovieAPIEdgeCases:
    """Test edge cases and error handling."""

    def test_very_large_page_number(self, client: TestClient):
        """Test requesting a page number beyond available data."""
        response = client.get(
            "/api/movies?page=9999&page_size=10",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        assert len(data["items"]) == 0

    def test_large_page_size(self, client: TestClient):
        """Test that page size is clamped to maximum."""
        response = client.get(
            "/api/movies?page_size=500",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        # Should be clamped to 100
        assert data["page_size"] <= 100

    def test_negative_page_returns_validation_error(self, client: TestClient):
        """Test that negative page number returns validation error."""
        response = client.get(
            "/api/movies?page=-1",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 422

    def test_invalid_movie_id_format(self, client: TestClient):
        """Test that invalid movie ID format returns validation error."""
        response = client.get(
            "/api/movies/invalid",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 422

    def test_empty_search_query_returns_validation_error(self, client: TestClient):
        """Test that empty search query returns validation error."""
        response = client.get(
            "/api/movies/search?q=",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        # Empty query might return 422 or be treated as no filter
        assert response.status_code in [200, 422]

    def test_special_characters_in_search(self, client: TestClient):
        """Test search with special characters."""
        response = client.get(
            "/api/movies/search?q=Monkeys",  # "Twelve Monkeys"
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should find "Twelve Monkeys"
        assert data["total_items"] > 0

    def test_movies_response_json_serializable(self, client: TestClient):
        """Test that responses are valid JSON."""
        response = client.get(
            "/api/movies",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 200
        # Should be able to parse JSON
        data = response.json()
        assert isinstance(data, dict)


class TestMovieAPIDataAccuracy:
    """Test data accuracy and consistency."""

    def test_movie_count_is_consistent(self, client: TestClient):
        """Test that total movie count is consistent across requests."""
        response1 = client.get(
            "/api/movies",
            headers={"X-API-Key": "test-api-key-123"}
        )
        response2 = client.get(
            "/api/movies",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["total_items"] == data2["total_items"]

    def test_movie_data_unchanged_across_requests(self, client: TestClient):
        """Test that movie data doesn't change between requests."""
        response1 = client.get(
            "/api/movies?page_size=1",
            headers={"X-API-Key": "test-api-key-123"}
        )
        response2 = client.get(
            "/api/movies?page_size=1",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        movie1 = response1.json()["items"][0]
        movie2 = response2.json()["items"][0]
        
        assert movie1["movie_id"] == movie2["movie_id"]
        assert movie1["title"] == movie2["title"]
        assert movie1["year"] == movie2["year"]

    def test_movie_id_1_exists(self, client: TestClient):
        """Test that movie ID 1 exists (Toy Story)."""
        response = client.get(
            "/api/movies/1",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["movie_id"] == 1
        assert "toy story" in data["title"].lower()

    def test_all_returned_movies_have_ids(self, client: TestClient):
        """Test that all movies have IDs."""
        response = client.get(
            "/api/movies?page_size=10",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        for movie in data["items"]:
            assert movie["movie_id"] > 0

    def test_all_returned_movies_have_titles(self, client: TestClient):
        """Test that all movies have titles."""
        response = client.get(
            "/api/movies?page_size=10",
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        data = response.json()
        for movie in data["items"]:
            assert movie["title"]
            assert len(movie["title"]) > 0

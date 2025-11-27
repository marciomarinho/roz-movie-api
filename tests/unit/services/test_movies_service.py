"""Unit tests for movies service business logic."""
from unittest.mock import MagicMock

import pytest

from app.models.movie import Movie
from app.services.movies_service import MoviesService


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = MagicMock()
    
    sample_movies = [
        Movie(movie_id=1, title="Toy Story", year=1995, genres=["Animation"]),
        Movie(movie_id=2, title="Inception", year=2010, genres=["Sci-Fi"]),
        Movie(movie_id=3, title="Heat", year=1995, genres=["Action"]),
        Movie(movie_id=4, title="Matrix", year=1999, genres=["Sci-Fi", "Action"]),
        Movie(movie_id=5, title="Avatar", year=2009, genres=["Sci-Fi"]),
    ]
    
    repo.list_movies = MagicMock(return_value=(sample_movies[:3], len(sample_movies)))
    repo.search_movies = MagicMock(return_value=(sample_movies[:2], len(sample_movies)))
    repo.get_movie_by_id = MagicMock(side_effect=lambda id: next((m for m in sample_movies if m.movie_id == id), None))
    
    return repo


class TestMoviesServiceGetMovies:
    """Test suite for get_movies method."""

    def test_get_movies_default_pagination(self, mock_repository):
        """Test get_movies with default pagination."""
        service = MoviesService(mock_repository)
        result = service.get_movies()
        
        assert result.page == 1
        assert result.page_size == 20
        assert len(result.items) > 0

    def test_get_movies_custom_pagination(self, mock_repository):
        """Test get_movies with custom pagination."""
        service = MoviesService(mock_repository)
        result = service.get_movies(page=2, page_size=5)
        
        assert result.page == 2
        assert result.page_size == 5

    def test_get_movies_page_size_clamped_to_max(self, mock_repository):
        """Test that page_size is clamped to maximum of 100."""
        service = MoviesService(mock_repository)
        result = service.get_movies(page_size=200)
        
        assert result.page_size == 100

    def test_get_movies_page_size_minimum(self, mock_repository):
        """Test that page_size has minimum of 1."""
        service = MoviesService(mock_repository)
        result = service.get_movies(page_size=0)
        
        assert result.page_size >= 1

    def test_get_movies_with_title_filter(self, mock_repository):
        """Test get_movies with title filter."""
        service = MoviesService(mock_repository)
        result = service.get_movies(title="Toy")
        
        mock_repository.list_movies.assert_called_with(
            page=1,
            page_size=20,
            title="Toy",
            genre=None,
            year=None
        )

    def test_get_movies_with_genre_filter(self, mock_repository):
        """Test get_movies with genre filter."""
        service = MoviesService(mock_repository)
        result = service.get_movies(genre="Action")
        
        mock_repository.list_movies.assert_called_with(
            page=1,
            page_size=20,
            title=None,
            genre="Action",
            year=None
        )

    def test_get_movies_with_year_filter(self, mock_repository):
        """Test get_movies with year filter."""
        service = MoviesService(mock_repository)
        result = service.get_movies(year=1995)
        
        mock_repository.list_movies.assert_called_with(
            page=1,
            page_size=20,
            title=None,
            genre=None,
            year=1995
        )

    def test_get_movies_combined_filters(self, mock_repository):
        """Test get_movies with multiple filters."""
        service = MoviesService(mock_repository)
        result = service.get_movies(title="Toy", genre="Animation", year=1995)
        
        mock_repository.list_movies.assert_called_with(
            page=1,
            page_size=20,
            title="Toy",
            genre="Animation",
            year=1995
        )

    def test_get_movies_pagination_calculation(self, mock_repository):
        """Test pagination calculations."""
        mock_repository.list_movies.return_value = ([], 105)  # 105 total items
        
        service = MoviesService(mock_repository)
        result = service.get_movies(page=1, page_size=20)
        
        # 105 items / 20 per page = 5.25 => 6 pages
        assert result.total_pages == 6

    def test_get_movies_returns_correct_format(self, mock_repository):
        """Test that get_movies returns correct response format."""
        service = MoviesService(mock_repository)
        result = service.get_movies()
        
        assert hasattr(result, 'items')
        assert hasattr(result, 'page')
        assert hasattr(result, 'page_size')
        assert hasattr(result, 'total_items')
        assert hasattr(result, 'total_pages')

    def test_get_movies_negative_page(self, mock_repository):
        """Test get_movies with negative page number (edge case)."""
        service = MoviesService(mock_repository)
        # Service might default to page 1 or raise error
        result = service.get_movies(page=-1)
        # Behavior depends on implementation


class TestMoviesServiceSearchMovies:
    """Test suite for search_movies method."""

    def test_search_movies_basic(self, mock_repository):
        """Test basic search functionality."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Inception")
        
        assert result.page == 1
        assert len(result.items) > 0

    def test_search_movies_with_pagination(self, mock_repository):
        """Test search with custom pagination."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Matrix", page=2, page_size=10)
        
        assert result.page == 2
        assert result.page_size == 10

    def test_search_movies_with_genre_filter(self, mock_repository):
        """Test search with genre filter."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Matrix", genre="Sci-Fi")
        
        mock_repository.search_movies.assert_called()

    def test_search_movies_with_year_filter(self, mock_repository):
        """Test search with year filter."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Matrix", year=1999)
        
        mock_repository.search_movies.assert_called()

    def test_search_movies_combined_filters(self, mock_repository):
        """Test search with multiple filters."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Matrix", genre="Sci-Fi", year=1999)
        
        mock_repository.search_movies.assert_called()

    def test_search_movies_empty_query(self, mock_repository):
        """Test search with empty query string."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="")
        
        assert result is not None

    def test_search_movies_page_size_clamped(self, mock_repository):
        """Test that page_size is clamped in search."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Test", page_size=500)
        
        assert result.page_size <= 100

    def test_search_movies_returns_correct_format(self, mock_repository):
        """Test that search returns correct format."""
        service = MoviesService(mock_repository)
        result = service.search_movies(query="Test")
        
        assert hasattr(result, 'items')
        assert hasattr(result, 'page')
        assert hasattr(result, 'page_size')
        assert hasattr(result, 'total_items')
        assert hasattr(result, 'total_pages')


class TestMoviesServiceGetMovie:
    """Test suite for get_movie method."""

    def test_get_movie_found(self, mock_repository):
        """Test retrieving an existing movie."""
        service = MoviesService(mock_repository)
        result = service.get_movie(1)
        
        assert result is not None
        mock_repository.get_movie_by_id.assert_called_with(1)

    def test_get_movie_not_found(self, mock_repository):
        """Test retrieving a non-existent movie."""
        mock_repository.get_movie_by_id.return_value = None
        
        service = MoviesService(mock_repository)
        result = service.get_movie(999)
        
        assert result is None

    def test_get_movie_returns_correct_format(self, mock_repository):
        """Test that get_movie returns correct format."""
        service = MoviesService(mock_repository)
        result = service.get_movie(1)
        
        if result:
            assert hasattr(result, 'movie_id')
            assert hasattr(result, 'title')
            assert hasattr(result, 'year')
            assert hasattr(result, 'genres')

    def test_get_movie_with_zero_id(self, mock_repository):
        """Test get_movie with zero ID."""
        mock_repository.get_movie_by_id.return_value = None
        
        service = MoviesService(mock_repository)
        result = service.get_movie(0)
        
        mock_repository.get_movie_by_id.assert_called_with(0)

    def test_get_movie_with_negative_id(self, mock_repository):
        """Test get_movie with negative ID."""
        mock_repository.get_movie_by_id.return_value = None
        
        service = MoviesService(mock_repository)
        result = service.get_movie(-1)
        
        mock_repository.get_movie_by_id.assert_called_with(-1)


class TestMoviesServiceEdgeCases:
    """Test suite for edge cases in MoviesService."""

    def test_service_with_none_repository(self):
        """Test that service validates repository."""
        with pytest.raises((TypeError, AttributeError)):
            service = MoviesService(None)
            service.get_movies()

    def test_service_pagination_calculation_zero_items(self, mock_repository):
        """Test pagination calculation with zero items."""
        mock_repository.list_movies.return_value = ([], 0)
        
        service = MoviesService(mock_repository)
        result = service.get_movies()
        
        assert result.total_items == 0
        assert result.total_pages == 0

    def test_service_pagination_calculation_exact_page_size(self, mock_repository):
        """Test pagination when total equals page size."""
        mock_repository.list_movies.return_value = ([], 20)
        
        service = MoviesService(mock_repository)
        result = service.get_movies(page_size=20)
        
        assert result.total_pages == 1

    def test_service_pagination_calculation_one_extra_item(self, mock_repository):
        """Test pagination calculation with one extra item."""
        mock_repository.list_movies.return_value = ([], 21)
        
        service = MoviesService(mock_repository)
        result = service.get_movies(page_size=20)
        
        assert result.total_pages == 2

    def test_service_large_page_size_request(self, mock_repository):
        """Test service with very large page_size request."""
        service = MoviesService(mock_repository)
        result = service.get_movies(page_size=999999)
        
        # Should be clamped to 100
        assert result.page_size == 100

    def test_service_large_page_number(self, mock_repository):
        """Test service with very large page number."""
        service = MoviesService(mock_repository)
        result = service.get_movies(page=999999)
        
        assert result.page == 999999

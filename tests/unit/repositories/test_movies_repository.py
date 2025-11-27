"""Unit tests for movies repository."""
from unittest.mock import MagicMock, patch

import pytest

from app.models.movie import Movie
from app.repositories.movies_repository import MoviesRepository


class TestMoviesRepositoryInit:
    """Test suite for MoviesRepository initialization."""

    def test_repository_init_pool_not_initialized(self):
        """Test that repository raises error when pool not initialized."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = False
            
            with pytest.raises(RuntimeError) as exc_info:
                MoviesRepository()
            
            assert "DatabasePool not initialized" in str(exc_info.value)

    def test_repository_init_success(self):
        """Test successful repository initialization."""
        sample_movies = [
            {"movie_id": 1, "title": "Movie 1", "year": 2020, "genres": ["Action"]},
            {"movie_id": 2, "title": "Movie 2", "year": 2021, "genres": ["Drama"]},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            
            assert len(repo.movies) == 2
            assert len(repo.movies_dict) == 2


class TestGetMovieById:
    """Test suite for get_movie_by_id method."""

    def test_get_movie_by_id_found(self):
        """Test retrieving an existing movie by ID."""
        movie = Movie(movie_id=1, title="Test Movie", year=2020, genres=["Action"])
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                {"movie_id": 1, "title": "Test Movie", "year": 2020, "genres": ["Action"]}
            ]
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(1)
            
            assert result is not None
            assert result.movie_id == 1
            assert result.title == "Test Movie"

    def test_get_movie_by_id_not_found(self):
        """Test retrieving a non-existent movie by ID."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(999)
            
            assert result is None

    def test_get_movie_by_id_negative_id(self):
        """Test get_movie_by_id with negative ID."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(-1)
            
            assert result is None

    def test_get_movie_by_id_zero(self):
        """Test get_movie_by_id with zero ID."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(0)
            
            assert result is None


class TestListMovies:
    """Test suite for list_movies method."""

    def test_list_movies_default_pagination(self):
        """Test listing movies with default pagination."""
        sample_movies = [
            {"movie_id": i, "title": f"Movie {i}", "year": 2020, "genres": []}
            for i in range(1, 11)
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=1, page_size=5)
            
            assert len(movies) == 5
            assert total == 10

    def test_list_movies_different_page(self):
        """Test listing movies with different page number."""
        sample_movies = [
            {"movie_id": i, "title": f"Movie {i}", "year": 2020, "genres": []}
            for i in range(1, 11)
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=2, page_size=5)
            
            assert len(movies) == 5
            assert total == 10
            assert movies[0].movie_id == 6

    def test_list_movies_with_title_filter(self):
        """Test listing movies with title filter."""
        sample_movies = [
            {"movie_id": 1, "title": "Toy Story", "year": 1995, "genres": []},
            {"movie_id": 2, "title": "Toy Soldiers", "year": 1991, "genres": []},
            {"movie_id": 3, "title": "Inception", "year": 2010, "genres": []},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(title="Toy")
            
            assert total == 2
            assert all("Toy" in m.title for m in movies)

    def test_list_movies_with_genre_filter(self):
        """Test listing movies with genre filter."""
        sample_movies = [
            {"movie_id": 1, "title": "Action Movie", "year": 2020, "genres": ["Action", "Thriller"]},
            {"movie_id": 2, "title": "Drama Film", "year": 2020, "genres": ["Drama"]},
            {"movie_id": 3, "title": "Action Comedy", "year": 2020, "genres": ["Action", "Comedy"]},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(genre="Action")
            
            assert total == 2
            assert all(any("Action" in g for g in m.genres) for m in movies)

    def test_list_movies_with_year_filter(self):
        """Test listing movies with year filter."""
        sample_movies = [
            {"movie_id": 1, "title": "Movie 2020 A", "year": 2020, "genres": []},
            {"movie_id": 2, "title": "Movie 2020 B", "year": 2020, "genres": []},
            {"movie_id": 3, "title": "Movie 2021", "year": 2021, "genres": []},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(year=2020)
            
            assert total == 2
            assert all(m.year == 2020 for m in movies)

    def test_list_movies_combined_filters(self):
        """Test listing movies with multiple filters combined."""
        sample_movies = [
            {"movie_id": 1, "title": "Action 2020", "year": 2020, "genres": ["Action"]},
            {"movie_id": 2, "title": "Drama 2020", "year": 2020, "genres": ["Drama"]},
            {"movie_id": 3, "title": "Action 2021", "year": 2021, "genres": ["Action"]},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(genre="Action", year=2020)
            
            assert total == 1
            assert movies[0].movie_id == 1

    def test_list_movies_empty_result(self):
        """Test listing movies with no results."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies()
            
            assert len(movies) == 0
            assert total == 0

    def test_list_movies_page_out_of_range(self):
        """Test listing movies with page number out of range."""
        sample_movies = [
            {"movie_id": 1, "title": "Movie 1", "year": 2020, "genres": []}
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=100, page_size=20)
            
            assert len(movies) == 0  # Page out of range
            assert total == 1  # But total remains


class TestSearchMovies:
    """Test suite for search_movies method."""

    def test_search_movies_basic(self):
        """Test basic movie search."""
        sample_movies = [
            {"movie_id": 1, "title": "Toy Story", "year": 1995, "genres": []},
            {"movie_id": 2, "title": "Toy Soldiers", "year": 1991, "genres": []},
            {"movie_id": 3, "title": "Inception", "year": 2010, "genres": []},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.search_movies(query="Toy")
            
            assert total == 2
            assert all("Toy" in m.title for m in movies)

    def test_search_movies_case_insensitive(self):
        """Test that movie search is case-insensitive."""
        sample_movies = [
            {"movie_id": 1, "title": "Toy Story", "year": 1995, "genres": []},
            {"movie_id": 2, "title": "TOY SOLDIERS", "year": 1991, "genres": []},
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.search_movies(query="toy")
            
            assert total == 2

    def test_search_movies_no_results(self):
        """Test search with no results."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.search_movies(query="NonExistentMovie")
            
            assert len(movies) == 0
            assert total == 0

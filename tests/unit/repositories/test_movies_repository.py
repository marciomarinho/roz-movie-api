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
        """Test successful repository initialization without loading data."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            
            # Repository should not load any data on init
            repo = MoviesRepository()
            
            # Verify DatabasePool was checked
            mock_pool.is_initialized.assert_called_once()


class TestGetMovieById:
    """Test suite for get_movie_by_id method."""

    def test_get_movie_by_id_found(self):
        """Test retrieving an existing movie by ID from database."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            # Mock the fetchone result
            mock_cursor.fetchone.return_value = {
                "movie_id": 1,
                "title": "Test Movie",
                "year": 2020,
                "genres": ["Action", "Adventure"],
            }
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(1)
            
            assert result is not None
            assert result.movie_id == 1
            assert result.title == "Test Movie"
            assert result.year == 2020
            assert result.genres == ["Action", "Adventure"]
            
            # Verify SQL was executed
            mock_cursor.execute.assert_called_once()
            args = mock_cursor.execute.call_args
            assert "WHERE movie_id = %s" in args[0][0]

    def test_get_movie_by_id_not_found(self):
        """Test retrieving a non-existent movie by ID."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(999)
            
            assert result is None
            mock_cursor.execute.assert_called_once()

    def test_get_movie_by_id_with_null_genres(self):
        """Test get_movie_by_id handles null genres."""
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                "movie_id": 1,
                "title": "Test Movie",
                "year": 2020,
                "genres": None,
            }
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            result = repo.get_movie_by_id(1)
            
            assert result is not None
            assert result.genres == []


class TestListMovies:
    """Test suite for list_movies method."""

    def test_list_movies_no_filters(self):
        """Test listing movies without filters (database query)."""
        sample_movies = [
            {
                "movie_id": i,
                "title": f"Movie {i}",
                "year": 2020 + i,
                "genres": ["Action"],
            }
            for i in range(1, 6)
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            # First call: count query
            # Second call: fetch query
            mock_cursor.fetchone.side_effect = [{"total": 5}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=1, page_size=5)
            
            assert len(movies) == 5
            assert total == 5
            assert movies[0].title == "Movie 1"
            
            # Verify SQL was executed with LIMIT/OFFSET
            calls = mock_cursor.execute.call_args_list
            assert len(calls) >= 2
            # Check that LIMIT and OFFSET are in the query
            final_query = calls[-1][0][0]
            assert "LIMIT" in final_query
            assert "OFFSET" in final_query

    def test_list_movies_with_title_filter(self):
        """Test listing movies with title filter (SQL WHERE clause)."""
        sample_movies = [
            {
                "movie_id": 1,
                "title": "Toy Story",
                "year": 1995,
                "genres": ["Animation"],
            }
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 1}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=1, page_size=20, title="Toy")
            
            assert len(movies) == 1
            assert total == 1
            assert movies[0].title == "Toy Story"
            
            # Verify WHERE clause includes title ILIKE
            calls = mock_cursor.execute.call_args_list
            query_with_title = calls[-1][0][0]
            assert "title ILIKE" in query_with_title or "ILIKE" in query_with_title

    def test_list_movies_with_genre_filter(self):
        """Test listing movies with genre filter (array contains)."""
        sample_movies = [
            {
                "movie_id": 1,
                "title": "Toy Story",
                "year": 1995,
                "genres": ["Animation", "Adventure"],
            }
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 1}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=1, page_size=20, genre="Adventure")
            
            assert len(movies) == 1
            assert "Adventure" in movies[0].genres
            
            # Verify WHERE clause includes ANY array check
            calls = mock_cursor.execute.call_args_list
            query_with_genre = calls[-1][0][0]
            assert "ANY" in query_with_genre

    def test_list_movies_with_year_filter(self):
        """Test listing movies with year filter."""
        sample_movies = [
            {
                "movie_id": 1,
                "title": "Toy Story",
                "year": 1995,
                "genres": ["Animation"],
            }
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 1}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=1, page_size=20, year=1995)
            
            assert len(movies) == 1
            assert movies[0].year == 1995
            
            # Verify WHERE clause includes year filter
            calls = mock_cursor.execute.call_args_list
            query_with_year = calls[-1][0][0]
            assert "year" in query_with_year.lower()

    def test_list_movies_with_combined_filters(self):
        """Test listing movies with multiple filters."""
        sample_movies = [
            {
                "movie_id": 1,
                "title": "Toy Story",
                "year": 1995,
                "genres": ["Animation", "Adventure"],
            }
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 1}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(
                page=1, page_size=20, title="Toy", genre="Adventure", year=1995
            )
            
            assert len(movies) == 1
            assert movies[0].title == "Toy Story"
            
            # Verify all filters are in WHERE clause
            calls = mock_cursor.execute.call_args_list
            query = calls[-1][0][0]
            assert "ILIKE" in query or "title" in query.lower()
            assert "ANY" in query
            assert "year" in query.lower()

    def test_list_movies_pagination_second_page(self):
        """Test pagination to second page uses correct OFFSET."""
        sample_movies = [
            {
                "movie_id": 21,
                "title": "Movie 21",
                "year": 2020,
                "genres": ["Action"],
            },
            {
                "movie_id": 22,
                "title": "Movie 22",
                "year": 2020,
                "genres": ["Action"],
            },
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 100}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.list_movies(page=2, page_size=20)
            
            assert len(movies) == 2
            assert total == 100
            
            # Verify OFFSET = (page - 1) * page_size = 20
            calls = mock_cursor.execute.call_args_list
            last_query = calls[-1][0][0]
            params = calls[-1][0][1]
            assert "OFFSET" in last_query
            # OFFSET value should be 20 (page 2, offset = (2-1)*20)
            assert 20 in params


class TestSearchMovies:
    """Test suite for search_movies method."""

    def test_search_movies_delegates_to_list_movies(self):
        """Test that search_movies delegates to list_movies with query as title."""
        sample_movies = [
            {
                "movie_id": 1,
                "title": "Toy Story",
                "year": 1995,
                "genres": ["Animation"],
            }
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 1}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.search_movies(query="Toy", page=1, page_size=20)
            
            assert len(movies) == 1
            assert movies[0].title == "Toy Story"
            
            # Verify query parameter is used as title filter
            calls = mock_cursor.execute.call_args_list
            query_string = calls[-1][0][0]
            assert "ILIKE" in query_string or "title" in query_string.lower()

    def test_search_movies_with_additional_filters(self):
        """Test search_movies with query and additional genre/year filters."""
        sample_movies = [
            {
                "movie_id": 1,
                "title": "Toy Story",
                "year": 1995,
                "genres": ["Animation", "Adventure"],
            }
        ]
        
        with patch("app.repositories.movies_repository.DatabasePool") as mock_pool:
            mock_pool.is_initialized.return_value = True
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_cursor.fetchone.side_effect = [{"total": 1}]
            mock_cursor.fetchall.return_value = sample_movies
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.__exit__.return_value = False
            mock_conn.cursor.return_value = mock_cursor
            mock_pool.get_connection.return_value = mock_conn
            
            repo = MoviesRepository()
            movies, total = repo.search_movies(
                query="Toy", page=1, page_size=20, genre="Adventure", year=1995
            )
            
            assert len(movies) == 1
            assert movies[0].title == "Toy Story"
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

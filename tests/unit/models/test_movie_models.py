"""Unit tests for Pydantic models."""
import pytest
from pydantic import ValidationError

from app.models.movie import Movie, MovieRead, PaginatedMovies


class TestMovieModel:
    """Test suite for Movie domain model."""

    def test_movie_creation_valid(self):
        """Test creating a valid Movie."""
        movie = Movie(
            movie_id=1,
            title="Toy Story",
            year=1995,
            genres=["Animation", "Comedy"]
        )
        assert movie.movie_id == 1
        assert movie.title == "Toy Story"
        assert movie.year == 1995
        assert movie.genres == ["Animation", "Comedy"]

    def test_movie_with_multiple_genres(self):
        """Test Movie with many genres."""
        genres = ["Action", "Adventure", "Sci-Fi", "Thriller"]
        movie = Movie(
            movie_id=10,
            title="Inception",
            year=2010,
            genres=genres
        )
        assert len(movie.genres) == 4
        assert movie.genres == genres

    def test_movie_with_empty_genres(self):
        """Test Movie with empty genres list."""
        movie = Movie(
            movie_id=1,
            title="Unknown Movie",
            year=2020,
            genres=[]
        )
        assert movie.genres == []

    def test_movie_missing_required_fields(self):
        """Test that Movie requires only movie_id and title."""
        # year and genres are optional, so only movie_id and title are required
        movie = Movie(movie_id=1, title="Test")  # This should work
        assert movie.movie_id == 1
        assert movie.title == "Test"
        assert movie.year is None
        assert movie.genres == []
        
        # But movie_id and title are still required
        with pytest.raises(ValidationError):
            Movie(title="Test Only")  # Missing movie_id

    def test_movie_invalid_year_type(self):
        """Test Movie with invalid year type."""
        with pytest.raises(ValidationError):
            Movie(
                movie_id=1,
                title="Test",
                year="not-a-year",
                genres=[]
            )

    def test_movie_negative_id(self):
        """Test Movie with negative ID (allowed)."""
        movie = Movie(
            movie_id=-1,
            title="Test",
            year=2020,
            genres=[]
        )
        assert movie.movie_id == -1

    def test_movie_zero_year(self):
        """Test Movie with zero year (allowed)."""
        movie = Movie(
            movie_id=1,
            title="Ancient",
            year=0,
            genres=[]
        )
        assert movie.year == 0

    def test_movie_very_large_year(self):
        """Test Movie with large year."""
        movie = Movie(
            movie_id=1,
            title="Future",
            year=9999,
            genres=[]
        )
        assert movie.year == 9999


class TestMovieReadModel:
    """Test suite for MovieRead API response model."""

    def test_movie_read_creation_from_movie(self):
        """Test creating MovieRead from Movie."""
        movie = Movie(
            movie_id=1,
            title="Toy Story",
            year=1995,
            genres=["Animation", "Comedy"]
        )
        movie_read = MovieRead.from_orm(movie)
        assert movie_read.movie_id == 1
        assert movie_read.title == "Toy Story"
        assert movie_read.year == 1995
        assert movie_read.genres == ["Animation", "Comedy"]

    def test_movie_read_dict_serialization(self):
        """Test MovieRead serialization to dict."""
        movie = Movie(
            movie_id=1,
            title="Toy Story",
            year=1995,
            genres=["Animation"]
        )
        movie_read = MovieRead.from_orm(movie)
        movie_dict = movie_read.dict()
        
        assert movie_dict["movie_id"] == 1
        assert movie_dict["title"] == "Toy Story"
        assert movie_dict["year"] == 1995
        assert movie_dict["genres"] == ["Animation"]

    def test_movie_read_json_serialization(self):
        """Test MovieRead JSON serialization."""
        movie = Movie(
            movie_id=2,
            title="Inception",
            year=2010,
            genres=["Sci-Fi", "Thriller"]
        )
        movie_read = MovieRead.from_orm(movie)
        json_str = movie_read.json()
        
        assert "Inception" in json_str
        assert "2010" in json_str


class TestPaginatedMoviesModel:
    """Test suite for PaginatedMovies response model."""

    def test_paginated_movies_creation(self):
        """Test creating PaginatedMovies response."""
        movies = [
            MovieRead(movie_id=1, title="Movie 1", year=2020, genres=[]),
            MovieRead(movie_id=2, title="Movie 2", year=2021, genres=[])
        ]
        paginated = PaginatedMovies(
            items=movies,
            page=1,
            page_size=20,
            total_items=100,
            total_pages=5
        )
        
        assert len(paginated.items) == 2
        assert paginated.page == 1
        assert paginated.page_size == 20
        assert paginated.total_items == 100
        assert paginated.total_pages == 5

    def test_paginated_movies_empty_items(self):
        """Test PaginatedMovies with empty items."""
        paginated = PaginatedMovies(
            items=[],
            page=2,
            page_size=20,
            total_items=0,
            total_pages=0
        )
        
        assert len(paginated.items) == 0
        assert paginated.total_items == 0

    def test_paginated_movies_single_page(self):
        """Test PaginatedMovies for single page result."""
        movies = [MovieRead(movie_id=i, title=f"Movie {i}", year=2020, genres=[]) for i in range(1, 6)]
        paginated = PaginatedMovies(
            items=movies,
            page=1,
            page_size=20,
            total_items=5,
            total_pages=1
        )
        
        assert paginated.total_pages == 1
        assert len(paginated.items) == 5

    def test_paginated_movies_last_page(self):
        """Test PaginatedMovies for last page with partial results."""
        movies = [MovieRead(movie_id=i, title=f"Movie {i}", year=2020, genres=[]) for i in range(1, 6)]
        paginated = PaginatedMovies(
            items=movies,
            page=5,
            page_size=20,
            total_items=85,
            total_pages=5
        )
        
        assert paginated.page == 5
        assert paginated.total_pages == 5
        assert len(paginated.items) == 5

    def test_paginated_movies_dict_serialization(self):
        """Test PaginatedMovies serialization."""
        movies = [MovieRead(movie_id=1, title="Test", year=2020, genres=["Test"])]
        paginated = PaginatedMovies(
            items=movies,
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1
        )
        
        data = paginated.dict()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_items"] == 1
        assert data["total_pages"] == 1
        assert len(data["items"]) == 1

    def test_paginated_movies_large_page_numbers(self):
        """Test PaginatedMovies with large page numbers."""
        paginated = PaginatedMovies(
            items=[],
            page=1000,
            page_size=100,
            total_items=100000,
            total_pages=1000
        )
        
        assert paginated.page == 1000
        assert paginated.total_items == 100000
        assert paginated.total_pages == 1000

    def test_paginated_movies_missing_required_fields(self):
        """Test that PaginatedMovies requires all fields."""
        with pytest.raises(ValidationError):
            PaginatedMovies(
                items=[],
                page=1
                # Missing: page_size, total_items, total_pages
            )

    def test_paginated_movies_invalid_page_type(self):
        """Test PaginatedMovies with invalid page type."""
        with pytest.raises(ValidationError):
            PaginatedMovies(
                items=[],
                page="not-a-number",
                page_size=20,
                total_items=0,
                total_pages=0
            )

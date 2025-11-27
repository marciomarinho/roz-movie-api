"""Movies service for business logic."""
import logging
from typing import Optional

from app.models.movie import MovieRead, PaginatedMovies
from app.repositories.movies_repository import MoviesRepository

logger = logging.getLogger(__name__)


class MoviesService:
    """Service layer for movies business logic."""

    def __init__(self, repository: MoviesRepository) -> None:
        """Initialize the service with a repository.

        Args:
            repository: MoviesRepository instance.
        """
        self.repository = repository

    def get_movies(
        self,
        page: int = 1,
        page_size: int = 20,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> PaginatedMovies:
        """Get a paginated list of movies with optional filters.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page (max 100).
            title: Filter by partial title match (case-insensitive).
            genre: Filter by genre (case-insensitive).
            year: Filter by year.

        Returns:
            PaginatedMovies: Paginated response with movies.
        """
        # Validate and clamp page_size
        page_size = min(page_size, 100)
        page_size = max(page_size, 1)
        page = max(page, 1)

        movies, total_items = self.repository.list_movies(
            page=page, page_size=page_size, title=title, genre=genre, year=year
        )

        total_pages = (total_items + page_size - 1) // page_size

        items = [
            MovieRead(
                movie_id=m.movie_id,
                title=m.title,
                year=m.year,
                genres=m.genres,
            )
            for m in movies
        ]

        return PaginatedMovies(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def search_movies(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> PaginatedMovies:
        """Search movies by query with optional additional filters.

        Args:
            query: Search query for title (case-insensitive, partial match).
            page: Page number (1-indexed).
            page_size: Number of items per page (max 100).
            genre: Additional genre filter (case-insensitive).
            year: Additional year filter.

        Returns:
            PaginatedMovies: Search results with pagination.
        """
        # Validate and clamp page_size
        page_size = min(page_size, 100)
        page_size = max(page_size, 1)
        page = max(page, 1)

        movies, total_items = self.repository.search_movies(
            query=query, page=page, page_size=page_size, genre=genre, year=year
        )

        total_pages = (total_items + page_size - 1) // page_size

        items = [
            MovieRead(
                movie_id=m.movie_id,
                title=m.title,
                year=m.year,
                genres=m.genres,
            )
            for m in movies
        ]

        return PaginatedMovies(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def get_movie(self, movie_id: int) -> Optional[MovieRead]:
        """Get a single movie by ID.

        Args:
            movie_id: The movie ID to retrieve.

        Returns:
            Optional[MovieRead]: The movie if found, None otherwise.
        """
        movie = self.repository.get_movie_by_id(movie_id)
        if movie:
            return MovieRead(
                movie_id=movie.movie_id,
                title=movie.title,
                year=movie.year,
                genres=movie.genres,
            )
        return None

"""Movies repository for PostgreSQL data access."""
import logging
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.database import DatabasePool
from app.models.movie import Movie

logger = logging.getLogger(__name__)


class MoviesRepository:
    """Repository for managing movie data from PostgreSQL database.
    
    Uses a shared connection pool managed by DatabasePool for efficient
    resource utilization across all repositories.
    """

    def __init__(self) -> None:
        """Initialize the repository.

        The repository uses a shared connection pool. Ensure DatabasePool
        has been initialized before creating repository instances.

        Raises:
            RuntimeError: If DatabasePool is not initialized.
        """
        if not DatabasePool.is_initialized():
            raise RuntimeError(
                "DatabasePool not initialized. Call DatabasePool.initialize() first."
            )
        
        self.movies: List[Movie] = []
        self.movies_dict: dict[int, Movie] = {}

        self._load_movies()

    def _load_movies(self) -> None:
        """Load all movies from PostgreSQL database.

        Gets a connection from the shared pool and fetches all movies 
        from the movies table.
        """
        conn = None
        try:
            # Get connection from shared pool
            conn = DatabasePool.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT movie_id, title, year, genres FROM movies ORDER BY movie_id")
                rows = cur.fetchall()

                for row in rows:
                    movie = Movie(
                        movie_id=row["movie_id"],
                        title=row["title"],
                        year=row["year"],
                        genres=list(row["genres"]) if row["genres"] else [],
                    )

                    self.movies.append(movie)
                    self.movies_dict[row["movie_id"]] = movie

            logger.info(f"Loaded {len(self.movies)} movies from PostgreSQL")
        except psycopg2.Error as e:
            logger.error(f"Error loading movies from PostgreSQL: {e}")
            raise
        finally:
            # Return connection to shared pool
            if conn:
                DatabasePool.return_connection(conn)

    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """Get a movie by its ID.

        Args:
            movie_id: The movie ID to retrieve.

        Returns:
            Optional[Movie]: The movie if found, None otherwise.
        """
        return self.movies_dict.get(movie_id)

    def list_movies(
        self,
        page: int = 1,
        page_size: int = 20,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Tuple[List[Movie], int]:
        """List movies with optional filtering and pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            title: Filter by partial title match (case-insensitive).
            genre: Filter by genre (case-insensitive).
            year: Filter by year.

        Returns:
            Tuple[List[Movie], int]: Filtered movies for the page and total count.
        """
        filtered = self._filter_movies(title=title, genre=genre, year=year)
        total_items = len(filtered)

        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        items = filtered[start_idx:end_idx]
        return items, total_items

    def search_movies(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Tuple[List[Movie], int]:
        """Search movies by query with optional additional filters.

        Args:
            query: Search query for title (case-insensitive, partial match).
            page: Page number (1-indexed).
            page_size: Number of items per page.
            genre: Additional genre filter (case-insensitive).
            year: Additional year filter.

        Returns:
            Tuple[List[Movie], int]: Search results and total count.
        """
        return self.list_movies(
            page=page, page_size=page_size, title=query, genre=genre, year=year
        )

    def _filter_movies(
        self,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[Movie]:
        """Filter movies by optional criteria.

        Args:
            title: Partial title match (case-insensitive).
            genre: Genre match (case-insensitive).
            year: Year match.

        Returns:
            List[Movie]: Filtered list of movies.
        """
        result = self.movies

        if title:
            title_lower = title.lower()
            result = [m for m in result if title_lower in m.title.lower()]

        if genre:
            genre_lower = genre.lower()
            result = [
                m
                for m in result
                if any(genre_lower in g.lower() for g in m.genres)
            ]

        if year is not None:
            result = [m for m in result if m.year == year]

        return result


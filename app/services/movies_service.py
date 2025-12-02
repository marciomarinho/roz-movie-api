import logging
from typing import Optional

from app.models.movie import MovieRead, PaginatedMovies
from app.repositories.movies_repository import MoviesRepository

logger = logging.getLogger(__name__)


class MoviesService:
    def __init__(self, repository: MoviesRepository) -> None:
        self.repository = repository

    def get_movies(
        self,
        page: int = 1,
        page_size: int = 20,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> PaginatedMovies:
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
        movie = self.repository.get_movie_by_id(movie_id)
        if movie:
            return MovieRead(
                movie_id=movie.movie_id,
                title=movie.title,
                year=movie.year,
                genres=movie.genres,
            )
        return None

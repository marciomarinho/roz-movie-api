"""Movie API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps.auth import verify_bearer_token
from app.models.movie import MovieRead, PaginatedMovies
from app.services.movies_service import MoviesService

router = APIRouter(prefix="/api", tags=["movies"], dependencies=[Depends(verify_bearer_token)])


def get_movies_service() -> MoviesService:
    """Get movies service instance.

    This is a placeholder that will be injected by FastAPI.
    The actual service is provided in main.py.

    Returns:
        MoviesService: The service instance.
    """
    # This will be overridden in main.py
    raise NotImplementedError("Movies service not initialized")


@router.get("/movies", response_model=PaginatedMovies)
async def list_movies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    title: Optional[str] = Query(None, max_length=100),
    genre: Optional[str] = Query(None, max_length=50),
    year: Optional[int] = Query(None, ge=1900, le=2100),
    service: MoviesService = Depends(get_movies_service),
) -> PaginatedMovies:
    """List movies with optional filtering and pagination.

    Args:
        page: Page number (1-indexed, default 1).
        page_size: Number of items per page (default 20, max 100).
        title: Filter by partial title match (case-insensitive, max 100 chars).
        genre: Filter by genre (case-insensitive, max 50 chars).
        year: Filter by year (1900-2100).
        service: Injected MoviesService.

    Returns:
        PaginatedMovies: Paginated list of movies.
    """
    return service.get_movies(
        page=page, page_size=page_size, title=title, genre=genre, year=year
    )


@router.get("/movies/search", response_model=PaginatedMovies)
async def search_movies(
    q: str = Query(..., description="Search query for movie title", max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: Optional[str] = Query(None, max_length=50),
    year: Optional[int] = Query(None, ge=1900, le=2100),
    service: MoviesService = Depends(get_movies_service),
) -> PaginatedMovies:
    """Search movies by query with optional additional filters.

    Args:
        q: Search query for title (case-insensitive, partial match, max 100 chars).
        page: Page number (1-indexed, default 1).
        page_size: Number of items per page (default 20, max 100).
        genre: Filter by genre (case-insensitive, max 50 chars).
        year: Filter by year (1900-2100).
        service: Injected MoviesService.

    Returns:
        PaginatedMovies: Search results with pagination.
    """
    return service.search_movies(query=q, page=page, page_size=page_size, genre=genre, year=year)


@router.get("/movies/{movie_id}", response_model=MovieRead)
async def get_movie(
    movie_id: int,
    service: MoviesService = Depends(get_movies_service),
) -> MovieRead:
    """Get a single movie by ID.

    Args:
        movie_id: The movie ID to retrieve.
        service: Injected MoviesService.

    Returns:
        MovieRead: The movie details.

    Raises:
        HTTPException: 404 if movie not found.
    """
    movie = service.get_movie(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found",
        )
    return movie

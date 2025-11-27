"""Movie models and schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field


class Movie(BaseModel):
    """Domain model for a movie."""

    movie_id: int
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""
        from_attributes = True


class MovieRead(BaseModel):
    """Schema for movie API responses."""

    movie_id: int
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""
        from_attributes = True


class PaginatedMovies(BaseModel):
    """Schema for paginated movie responses."""

    items: List[MovieRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int

    class Config:
        """Pydantic config."""
        populate_by_name = True

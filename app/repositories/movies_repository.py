import logging
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.database import DatabasePool
from app.models.movie import Movie

logger = logging.getLogger(__name__)

class MoviesRepository:

    def __init__(self) -> None:
        if not DatabasePool.is_initialized():
            raise RuntimeError(
                "DatabasePool not initialized. Call DatabasePool.initialize() first."
            )

    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        conn = None
        try:
            conn = DatabasePool.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT movie_id, title, year, genres FROM movies WHERE movie_id = %s",
                    (movie_id,)
                )
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return Movie(
                    movie_id=row["movie_id"],
                    title=row["title"],
                    year=row["year"],
                    genres=list(row["genres"]) if row["genres"] else [],
                )
        except psycopg2.Error as e:
            logger.error(f"Error fetching movie {movie_id}: {e}")
            raise
        finally:
            if conn:
                DatabasePool.return_connection(conn)

    def list_movies(
        self,
        page: int = 1,
        page_size: int = 20,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Tuple[List[Movie], int]:
        conn = None
        try:
            conn = DatabasePool.get_connection()
            
            # Build WHERE clause dynamically
            where_clauses = []
            params = []
            
            if title:
                where_clauses.append("title ILIKE %s")
                params.append(f"%{title}%")
            
            if genre:
                where_clauses.append("%s = ANY(genres)")
                params.append(genre)
            
            if year is not None:
                where_clauses.append("year = %s")
                params.append(year)
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count with filters
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                count_query = f"SELECT COUNT(*) as total FROM movies WHERE {where_clause}"
                cur.execute(count_query, params)
                total_items = cur.fetchone()["total"]
            
            # Get paginated results with filters
            offset = (page - 1) * page_size
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT movie_id, title, year, genres 
                    FROM movies 
                    WHERE {where_clause}
                    ORDER BY movie_id
                    LIMIT %s OFFSET %s
                """
                params.extend([page_size, offset])
                cur.execute(query, params)
                rows = cur.fetchall()
                
                movies = [
                    Movie(
                        movie_id=row["movie_id"],
                        title=row["title"],
                        year=row["year"],
                        genres=list(row["genres"]) if row["genres"] else [],
                    )
                    for row in rows
                ]
                
                return movies, total_items
        except psycopg2.Error as e:
            logger.error(f"Error listing movies: {e}")
            raise
        finally:
            if conn:
                DatabasePool.return_connection(conn)

    def search_movies(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        genre: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Tuple[List[Movie], int]:
        return self.list_movies(
            page=page, page_size=page_size, title=query, genre=genre, year=year
        )
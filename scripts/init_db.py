"""Database initialization script for testing and setup."""
import csv
import logging
import os
from typing import Optional

import psycopg2
from psycopg2 import sql

logger = logging.getLogger(__name__)


def create_tables(connection) -> None:
    """Create database tables.

    Args:
        connection: PostgreSQL database connection.
    """
    cursor = connection.cursor()
    try:
        # Create movies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                movie_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                year INTEGER,
                genres TEXT[] DEFAULT ARRAY[]::TEXT[]
            );
        """)
        
        # Create index on title for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_title 
            ON movies USING btree (title);
        """)
        
        connection.commit()
        logger.info("Tables created successfully")
    except Exception as e:
        connection.rollback()
        logger.error(f"Error creating tables: {e}")
        raise
    finally:
        cursor.close()


def load_movies_from_csv(
    connection,
    csv_file_path: str,
    clear_existing: bool = True
) -> int:
    """Load movies from CSV file into database.

    Args:
        connection: PostgreSQL database connection.
        csv_file_path: Path to the CSV file.
        clear_existing: Whether to clear existing data first.

    Returns:
        int: Number of movies loaded.
    """
    cursor = connection.cursor()
    try:
        if clear_existing:
            cursor.execute("DELETE FROM movies;")
            logger.info("Cleared existing movies")
        
        movies_loaded = 0
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract year from title if present (e.g., "Toy Story (1995)")
                title = row['title'].strip()
                year = extract_year_from_title(title)
                
                # Parse genres
                genres = []
                if row.get('genres'):
                    genres = [g.strip() for g in row['genres'].split('|')]
                
                # Insert movie
                cursor.execute(
                    sql.SQL("""
                        INSERT INTO movies (title, year, genres)
                        VALUES (%s, %s, %s)
                    """),
                    (title, year, genres)
                )
                movies_loaded += 1
        
        connection.commit()
        logger.info(f"Loaded {movies_loaded} movies from {csv_file_path}")
        return movies_loaded
    except Exception as e:
        connection.rollback()
        logger.error(f"Error loading movies: {e}")
        raise
    finally:
        cursor.close()


def extract_year_from_title(title: str) -> Optional[int]:
    """Extract year from movie title (e.g., "Toy Story (1995)" -> 1995).

    Args:
        title: Movie title string.

    Returns:
        Optional[int]: The extracted year or None.
    """
    import re
    match = re.search(r'\((\d{4})\)\s*$', title)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def initialize_database(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    csv_file_path: Optional[str] = None,
) -> None:
    """Initialize database with schema and optional data.

    Args:
        host: Database host.
        port: Database port.
        user: Database user.
        password: Database password.
        database: Database name.
        csv_file_path: Optional path to CSV file to load.
    """
    connection = None
    try:
        # Connect to database
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
        logger.info(f"Connected to database at {host}:{port}")
        
        # Create tables
        create_tables(connection)
        
        # Load data if CSV provided
        if csv_file_path and os.path.exists(csv_file_path):
            load_movies_from_csv(connection, csv_file_path)
        else:
            logger.warning(f"CSV file not found: {csv_file_path}")
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get arguments from command line or environment
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '5432'))
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgres')
    database = os.getenv('DB_NAME', 'movies')
    csv_file = os.getenv('CSV_FILE', 'data/movies_small.csv')
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    initialize_database(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        csv_file_path=csv_file,
    )
    
    logger.info("Database initialization complete!")

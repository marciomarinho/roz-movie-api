"""Database connection pool management."""
import logging
from typing import Optional

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DatabasePool:
    """Singleton database connection pool manager.
    
    Manages a single connection pool shared across the entire application
    and all repositories. This ensures efficient resource usage and
    prevents connection pool duplication.
    """

    _instance: Optional["DatabasePool"] = None
    _pool: Optional[pool.SimpleConnectionPool] = None

    def __new__(cls) -> "DatabasePool":
        """Implement singleton pattern.
        
        Returns:
            DatabasePool: The single instance of this class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(
        cls,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "postgres",
        user: str = "postgres",
        password: str = "mysecretpassword",
        min_connections: int = 2,
        max_connections: int = 10,
    ) -> None:
        """Initialize the database connection pool.
        
        Should be called once during application startup.
        Subsequent calls will be ignored if pool already exists.

        Args:
            host: PostgreSQL host (default: localhost)
            port: PostgreSQL port (default: 5432)
            dbname: PostgreSQL database name (default: postgres)
            user: PostgreSQL user (default: postgres)
            password: PostgreSQL password
            min_connections: Minimum connections in pool (default: 2)
            max_connections: Maximum connections in pool (default: 10)

        Raises:
            psycopg2.Error: If pool creation fails.
            RuntimeError: If pool is already initialized.
        """
        if cls._pool is not None:
            logger.warning("Connection pool already initialized, skipping initialization")
            return

        try:
            conn_params = {
                "host": host,
                "port": port,
                "dbname": dbname,
                "user": user,
                "password": password,
            }
            cls._pool = pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                **conn_params,
            )
            logger.info(
                f"Initialized database connection pool ({min_connections}-{max_connections} connections)"
            )
        except psycopg2.Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    @classmethod
    def get_connection(cls) -> psycopg2.extensions.connection:
        """Get a connection from the pool.

        Returns:
            psycopg2.extensions.connection: A database connection from the pool.

        Raises:
            RuntimeError: If pool is not initialized.
            psycopg2.pool.PoolError: If no connections available.
        """
        if cls._pool is None:
            raise RuntimeError(
                "Connection pool not initialized. Call DatabasePool.initialize() first."
            )
        return cls._pool.getconn()

    @classmethod
    def return_connection(cls, conn: psycopg2.extensions.connection) -> None:
        """Return a connection to the pool.

        Args:
            conn: The connection to return to the pool.

        Raises:
            RuntimeError: If pool is not initialized.
        """
        if cls._pool is None:
            raise RuntimeError("Connection pool not initialized")
        cls._pool.putconn(conn)

    @classmethod
    def close(cls) -> None:
        """Close all connections in the pool.
        
        Should be called during application shutdown.
        After calling this, the pool must be re-initialized with initialize()
        before it can be used again.
        """
        if cls._pool is not None:
            try:
                cls._pool.closeall()
                logger.info("Closed database connection pool")
                cls._pool = None
            except psycopg2.Error as e:
                logger.error(f"Error closing connection pool: {e}")

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the pool is initialized.
        
        Returns:
            bool: True if pool is initialized and ready, False otherwise.
        """
        return cls._pool is not None

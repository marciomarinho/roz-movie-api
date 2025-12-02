"""Database connection pool management."""
import logging
from typing import Optional

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DatabasePool:

    _instance: Optional["DatabasePool"] = None
    _pool: Optional[pool.SimpleConnectionPool] = None

    def __new__(cls) -> "DatabasePool":
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
        if cls._pool is None:
            raise RuntimeError(
                "Connection pool not initialized. Call DatabasePool.initialize() first."
            )
        return cls._pool.getconn()

    @classmethod
    def return_connection(cls, conn: psycopg2.extensions.connection) -> None:
        if cls._pool is None:
            raise RuntimeError("Connection pool not initialized")
        cls._pool.putconn(conn)

    @classmethod
    def close(cls) -> None:
        if cls._pool is not None:
            try:
                cls._pool.closeall()
                logger.info("Closed database connection pool")
                cls._pool = None
            except psycopg2.Error as e:
                logger.error(f"Error closing connection pool: {e}")

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._pool is not None

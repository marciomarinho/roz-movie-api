import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_health, routes_movies
from app.core.config import get_settings
from app.core.database import DatabasePool
from app.core.logging_config import configure_logging
from app.repositories.movies_repository import MoviesRepository
from app.services.movies_service import MoviesService

# Configure logging at module load time
configure_logging()
logger = logging.getLogger(__name__)

# Global service instance
movies_service: MoviesService = None


def get_movies_service() -> MoviesService:
    if movies_service is None:
        raise RuntimeError("Movies service not initialized")
    return movies_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global movies_service
    settings = get_settings()
    logger.info(
        f"Connecting to PostgreSQL at {settings.db_host}:{settings.db_port}/{settings.db_name}"
    )

    try:
        # Initialize shared connection pool
        DatabasePool.initialize(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )
        
        # Create repository (uses the initialized pool)
        repository = MoviesRepository()
        movies_service = MoviesService(repository)
        logger.info("Application started successfully - ready to serve movie data")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Application shutting down")
    DatabasePool.close()
    logger.info("Database connection pool closed")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="REST API for MovieLens movies database",
        lifespan=lifespan,
    )

    # Add CORS middleware (allow all origins for demo purposes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(routes_health.router)
    app.include_router(routes_movies.router)

    # Override the dependency injection for get_movies_service
    app.dependency_overrides[routes_movies.get_movies_service] = get_movies_service

    return app


# Create the app instance
app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to Movie API",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )

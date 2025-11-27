Movie API - Project Structure
=============================

movie_api/
├── app/                              # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI app factory and lifespan management
│   │                                 # - Creates FastAPI app instance
│   │                                 # - Handles startup/shutdown events
│   │                                 # - Loads movies repository
│   │                                 # - Sets up CORS middleware
│   │
│   ├── api/                          # API routes
│   │   ├── __init__.py
│   │   ├── routes_health.py          # Health check endpoint (no auth required)
│   │   │                             # - GET /health
│   │   │
│   │   └── routes_movies.py          # Movie API endpoints (auth required)
│   │                                 # - GET /api/movies (list with pagination)
│   │                                 # - GET /api/movies/search (search query)
│   │                                 # - GET /api/movies/{movie_id} (get by ID)
│   │
│   ├── core/                         # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings class using pydantic-settings
│   │   │                             # - APP_NAME, API_V1_PREFIX, etc.
│   │   │                             # - Loads from environment variables
│   │   │
│   │   └── logging_config.py         # Logging setup
│   │                                 # - Configures stdout logging
│   │                                 # - Sets log level from config
│   │
│   ├── models/                       # Pydantic models
│   │   ├── __init__.py
│   │   └── movie.py                  # Movie domain and API schemas
│   │                                 # - Movie (domain model)
│   │                                 # - MovieRead (API response schema)
│   │                                 # - PaginatedMovies (list response schema)
│   │
│   ├── repositories/                 # Data access layer
│   │   ├── __init__.py
│   │   └── movies_repository.py      # CSV-based repository
│   │                                 # - Loads CSV at startup
│   │                                 # - Stores in-memory for fast access
│   │                                 # - Provides list_movies, search_movies, get_movie_by_id
│   │                                 # - Handles filtering and pagination
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   └── movies_service.py         # Movie service
│   │                                 # - Consumes repository
│   │                                 # - Exposes get_movies, search_movies, get_movie
│   │                                 # - Handles pagination calculation
│   │                                 # - Validates input parameters
│   │
│   └── deps/                         # Dependency injection
│       ├── __init__.py
│       └── auth.py                   # Authentication dependencies
│                                     # - verify_api_key: Validates X-API-Key header
│                                     # - Returns None if no key required
│                                     # - Raises 401 Unauthorized if invalid
│
├── data/                             # Data files
│   └── movies.csv                    # MovieLens movies dataset
│                                     # CSV format: movieId,title,genres
│
├── tests/                            # Test suite
│   ├── __init__.py
│   └── test_movies_rest.py           # Comprehensive test suite (40+ tests)
│                                     # - Health check tests
│                                     # - List movies with pagination
│                                     # - Filtering by title, genre, year
│                                     # - Search functionality
│                                     # - Get movie by ID
│                                     # - Error cases (404, 401, 422)
│                                     # - Authentication tests
│                                     # - Year extraction tests
│
├── conftest.py                       # Pytest configuration
│                                     # - Project root path setup
│                                     # - Test fixtures and configuration
│
├── requirements.txt                  # Python dependencies
│                                     # - FastAPI 0.104.1
│                                     # - Uvicorn 0.24.0
│                                     # - Pydantic 2.5.0
│                                     # - pytest, httpx for testing
│
├── Dockerfile                        # Docker image definition
│                                     # - Python 3.11-slim base
│                                     # - Non-root user (appuser)
│                                     # - Health check
│                                     # - Uvicorn entrypoint
│
├── .dockerignore                     # Files to exclude from Docker build
│
├── .env.example                      # Example environment variables
│
├── .gitignore                        # Git ignore patterns
│
└── README.md                         # Complete documentation
                                      # - Feature overview
                                      # - Installation instructions
                                      # - API endpoint documentation
                                      # - Authentication guide
                                      # - Docker deployment
                                      # - AWS Lightsail deployment
                                      # - Testing instructions
                                      # - Troubleshooting


Key Architecture Decisions
===========================

1. LAYERED ARCHITECTURE
   - Routes (API layer) → Services (business logic) → Repository (data access)
   - Clean separation of concerns
   - Easy to test each layer independently
   - Easy to swap repository implementation (e.g., database for CSV)

2. DEPENDENCY INJECTION
   - FastAPI's Depends() for route-level dependencies
   - Global movies_service instance managed in main.py
   - Auth dependency: verify_api_key injected into protected routes

3. CONFIGURATION MANAGEMENT
   - Pydantic Settings for environment variables
   - All config in one place (app/core/config.py)
   - Supports .env files
   - Easy to override for testing

4. IN-MEMORY STORAGE
   - CSV loaded once at startup (lifespan event)
   - Movies stored in List and Dict for fast access
   - Suitable for small-medium datasets (~10k movies)
   - Easy to migrate to database later

5. ERROR HANDLING
   - HTTPException for API errors with proper status codes
   - 404 for missing resources
   - 401 for authentication failures
   - 422 for validation errors

6. PAGINATION
   - Prevents large responses
   - page_size clamped to max 100
   - Calculates total_pages server-side
   - Enables efficient large dataset browsing

7. FILTERING
   - Case-insensitive matching for title and genre
   - Partial string matching for text fields
   - Exact matching for year (integer)
   - Efficient in-memory filtering

8. LOGGING
   - Structured logging to stdout (Docker-friendly)
   - Configurable log level
   - Different log levels for different components

9. DOCKER
   - Multi-layer optimization (slim image, no cache)
   - Non-root user for security
   - Health check endpoint
   - Environment variables for configuration
   - Ready for AWS Lightsail and other cloud platforms


Development Workflow
====================

1. LOCAL DEVELOPMENT
   $ python -m venv .venv
   $ source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   $ pip install -r requirements.txt
   $ uvicorn app.main:app --reload

2. TESTING
   $ pytest                          # Run all tests
   $ pytest --cov=app tests/         # Run with coverage
   $ pytest tests/test_movies_rest.py::TestListMovies -v  # Run specific tests

3. DOCKER LOCAL
   $ docker build -t movielens-api .
   $ docker run -p 8000:8000 -e API_KEY=secret movielens-api

4. PRODUCTION (AWS LIGHTSAIL)
   - SSH into instance
   - Upload project files
   - Build Docker image
   - Run container with restart policy
   - Bind to port 80 or behind load balancer


API Response Examples
====================

List Movies Response:
{
  "items": [
    {
      "movie_id": 1,
      "title": "Toy Story (1995)",
      "year": 1995,
      "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"]
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_items": 9742,
  "total_pages": 488
}

Error Responses:
- 401 Unauthorized (missing/invalid API key)
  {"detail": "Missing X-API-Key header"}

- 404 Not Found (movie ID doesn't exist)
  {"detail": "Movie with id 99999 not found"}

- 422 Unprocessable Entity (invalid query parameters)
  {"detail": [{"loc": ["query", "page"], "msg": "ensure this value is greater than or equal to 1", ...}]}

- 200 OK (health check)
  {"status": "ok"}


Testing Coverage
================

Unit Tests:
- Year extraction from titles
- Genre filtering (case-insensitive, partial match)
- Pagination logic
- Filter combination logic

Integration Tests:
- Health check endpoint
- List movies with pagination
- Filtering by title, genre, year
- Search functionality
- Get movie by ID (success and 404)
- Authentication (missing/invalid keys)
- Invalid query parameters

Fixtures:
- Sample CSV data with 10 movies
- Temporary CSV file creation
- Repository with sample data
- Service instance
- TestClient with dependency overrides

MOVIE API - ENDPOINT REFERENCE
==============================

BASE URL: http://localhost:8000
DOCS: http://localhost:8000/docs


ROOT & DOCUMENTATION ENDPOINTS (No Auth Required)
==================================================

GET /
  Description: Root endpoint with links to docs
  Response:
    {
      "message": "Welcome to Movie API",
      "docs": "/docs",
      "openapi": "/openapi.json"
    }
  Example:
    curl http://localhost:8000/

GET /health
  Description: Health check (used by Docker/Kubernetes)
  Response:
    {
      "status": "ok"
    }
  Example:
    curl http://localhost:8000/health

GET /docs
  Description: Swagger UI interactive documentation
  Example:
    Open in browser: http://localhost:8000/docs

GET /redoc
  Description: ReDoc alternative documentation
  Example:
    Open in browser: http://localhost:8000/redoc

GET /openapi.json
  Description: OpenAPI specification (JSON)
  Example:
    curl http://localhost:8000/openapi.json


PROTECTED MOVIE ENDPOINTS (Auth Required if API_KEY is set)
============================================================

GET /api/movies
  Description: List movies with pagination and optional filtering
  
  Query Parameters:
    page (int, default=1): Page number (1-indexed)
    page_size (int, default=20, max=100): Items per page
    title (string, optional): Filter by partial title match (case-insensitive)
    genre (string, optional): Filter by genre (case-insensitive)
    year (int, optional): Filter by year (exact match)
  
  Headers:
    X-API-Key: {api_key} (required if API_KEY env var is set)
  
  Response Status Codes:
    200 OK: Successful request
    401 Unauthorized: Missing or invalid API key
    422 Unprocessable Entity: Invalid query parameters
  
  Response Body:
    {
      "items": [
        {
          "movie_id": 1,
          "title": "Toy Story (1995)",
          "year": 1995,
          "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"]
        },
        ...
      ],
      "page": 1,
      "page_size": 20,
      "total_items": 9742,
      "total_pages": 488
    }
  
  Examples:
    # Basic list (first 20 movies)
    curl http://localhost:8000/api/movies
    
    # Custom pagination
    curl http://localhost:8000/api/movies?page=2&page_size=10
    
    # Filter by title
    curl http://localhost:8000/api/movies?title=toy
    
    # Filter by genre
    curl http://localhost:8000/api/movies?genre=Action
    
    # Filter by year
    curl http://localhost:8000/api/movies?year=1995
    
    # Combine multiple filters
    curl http://localhost:8000/api/movies?genre=Comedy&year=1995&page_size=50
    
    # With authentication
    curl -H "X-API-Key: mysecret" http://localhost:8000/api/movies


GET /api/movies/search
  Description: Search movies by title query with optional filters
  
  Query Parameters:
    q (string, required): Search query for title (case-insensitive, partial match)
    page (int, default=1): Page number (1-indexed)
    page_size (int, default=20, max=100): Items per page
    genre (string, optional): Additional genre filter
    year (int, optional): Additional year filter
  
  Headers:
    X-API-Key: {api_key} (required if API_KEY env var is set)
  
  Response Status Codes:
    200 OK: Successful request
    401 Unauthorized: Missing or invalid API key
    422 Unprocessable Entity: Invalid parameters or missing 'q'
  
  Response Body:
    (Same pagination format as /api/movies)
  
  Examples:
    # Basic search
    curl http://localhost:8000/api/movies/search?q=story
    
    # Search with genre filter
    curl http://localhost:8000/api/movies/search?q=adventure&genre=Action
    
    # Search with year filter
    curl http://localhost:8000/api/movies/search?q=1995&year=1995
    
    # Search with pagination
    curl http://localhost:8000/api/movies/search?q=toy&page=1&page_size=5


GET /api/movies/{movie_id}
  Description: Get a single movie by ID
  
  Path Parameters:
    movie_id (integer): The movie ID to retrieve
  
  Headers:
    X-API-Key: {api_key} (required if API_KEY env var is set)
  
  Response Status Codes:
    200 OK: Movie found
    401 Unauthorized: Missing or invalid API key
    404 Not Found: Movie with specified ID doesn't exist
    422 Unprocessable Entity: Invalid movie_id format
  
  Response Body (200 OK):
    {
      "movie_id": 1,
      "title": "Toy Story (1995)",
      "year": 1995,
      "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"]
    }
  
  Response Body (404 Not Found):
    {
      "detail": "Movie with id 99999 not found"
    }
  
  Examples:
    # Get movie by ID
    curl http://localhost:8000/api/movies/1
    
    # Non-existent movie (returns 404)
    curl http://localhost:8000/api/movies/99999
    
    # With authentication
    curl -H "X-API-Key: mysecret" http://localhost:8000/api/movies/1


FILTERING BEHAVIOR
==================

Title Filter (case-insensitive partial match):
  ?title=toy
    Matches: "Toy Story", "TOY STORY", "A Toy Story"
    Does NOT match: "Boys"
  
Genre Filter (case-insensitive, substring match):
  ?genre=Action
    Matches: Movie with genres: ["Action", "Comedy"]
    Matches: Movie with genres: ["Adventure"]  (contains "Action" as substring? NO)
    Actually: ["Action", "Adventure", "Crime", "Thriller"]
  
  ?genre=Adv
    Matches: Movie with genres: ["Adventure", "Comedy"]
  
Year Filter (exact match):
  ?year=1995
    Matches: Movies where year == 1995 (parsed from title)
    Does NOT match: Movies from 1990-1994 or 1996+


COMBINING FILTERS
=================

Multiple filters use AND logic (all must match):

  ?genre=Action&year=1995
    Returns movies that are BOTH Action AND from 1995

  ?title=story&genre=Animation&year=1995
    Returns movies that contain "story" AND have "Animation" genre AND are from 1995

  ?title=star&genre=Wars
    Returns movies with "star" in title AND "Wars" in genres
    (If "Star Wars" has "Wars" as genre, it matches)


PAGINATION BEHAVIOR
===================

Default: page=1, page_size=20

Limits:
  - Minimum page_size: 1
  - Maximum page_size: 100
  - Minimum page: 1

Examples:
  ?page=1&page_size=10        → Returns items 1-10
  ?page=2&page_size=10        → Returns items 11-20
  ?page=3&page_size=10        → Returns items 21-30

Page Clamping (server-side):
  ?page_size=500              → Automatically reduced to 100
  ?page_size=0                → Automatically set to 1
  ?page=0                     → Automatically set to 1


AUTHENTICATION
==============

Optional Authentication:
  - If API_KEY environment variable is NOT set: No authentication required
  - If API_KEY environment variable IS set: X-API-Key header required

Setting API_KEY:
  export API_KEY=your-secret-key-here

Making Authenticated Requests:
  curl -H "X-API-Key: your-secret-key-here" \
    http://localhost:8000/api/movies

Invalid Key Response (401):
  {
    "detail": "Invalid API key"
  }

Missing Key Response (401):
  {
    "detail": "Missing X-API-Key header"
  }

Exempt from Authentication:
  - GET /health
  - GET /docs
  - GET /redoc
  - GET /openapi.json
  - GET /


ERROR RESPONSES
===============

400 Bad Request:
  {
    "detail": "Invalid request format"
  }

401 Unauthorized (Authentication):
  {
    "detail": "Missing X-API-Key header"
  }
  or
  {
    "detail": "Invalid API key"
  }

404 Not Found:
  {
    "detail": "Movie with id 99999 not found"
  }

422 Unprocessable Entity (Validation):
  {
    "detail": [
      {
        "loc": ["query", "page"],
        "msg": "ensure this value is greater than or equal to 1",
        "type": "value_error.number.not_gt",
        "ctx": {"limit_value": 0}
      }
    ]
  }

500 Internal Server Error:
  {
    "detail": "Internal server error"
  }


RESPONSE FORMAT
===============

All responses are JSON with proper Content-Type header.

Paginated Response Format:
  {
    "items": [
      {movie_object},
      {movie_object},
      ...
    ],
    "page": 1,
    "page_size": 20,
    "total_items": 1000,
    "total_pages": 50
  }

Single Movie Format:
  {
    "movie_id": 1,
    "title": "Toy Story (1995)",
    "year": 1995,
    "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"]
  }

Field Descriptions:
  movie_id (int):      Unique identifier for the movie
  title (string):      Movie title with year in parentheses
  year (int | null):   Release year (extracted from title if present)
  genres (array):      List of genre tags as strings


QUICK REFERENCE
===============

No Auth Required:
  curl http://localhost:8000/health
  curl http://localhost:8000/docs

List All Movies:
  curl http://localhost:8000/api/movies

Filter Examples:
  curl http://localhost:8000/api/movies?genre=Action
  curl http://localhost:8000/api/movies?title=Toy
  curl http://localhost:8000/api/movies?year=1995

Search:
  curl http://localhost:8000/api/movies/search?q=toy

Get One:
  curl http://localhost:8000/api/movies/1

With Auth:
  curl -H "X-API-Key: secret" http://localhost:8000/api/movies


TROUBLESHOOTING
===============

Q: Getting 401 Unauthorized
A: Check if API_KEY is set. If yes, include the header:
   curl -H "X-API-Key: your-key" http://localhost:8000/api/movies

Q: Getting 422 Unprocessable Entity
A: Check your query parameters. Common issues:
   - page must be >= 1
   - page_size must be >= 1
   - page_size max is 100
   - Missing required 'q' parameter for search endpoint

Q: Getting 404 for a movie
A: The movie ID doesn't exist in the database.
   Try: curl http://localhost:8000/api/movies
   To see available movies

Q: Empty results
A: Your filter might be too specific.
   Try removing filters one by one:
   curl http://localhost:8000/api/movies?title=toy
   curl http://localhost:8000/api/movies?genre=Adventure
   curl http://localhost:8000/api/movies?year=1995

Q: API not responding
A: Check if server is running:
   uvicorn app.main:app --reload
   Should say "Uvicorn running on http://127.0.0.1:8000"


TESTING ENDPOINTS
=================

Use the interactive Swagger UI:
  http://localhost:8000/docs
  - Try it out button in each endpoint
  - See request/response format
  - Automatically formatted

Or use curl:
  curl http://localhost:8000/api/movies?page=1&page_size=5 | jq

Or use Python:
  import requests
  r = requests.get('http://localhost:8000/api/movies')
  print(r.json())

Or use the test suite:
  pytest tests/test_movies_rest.py -v

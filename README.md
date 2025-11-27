# Movie API - REST Backend

A production-ready REST API for the MovieLens movies database, built with FastAPI, designed to run locally and in Docker.

## Features

- **REST API** with paginated movie listings
- **Filtering** by title, genre, and year
- **Search** endpoint for free-text queries
- **Single movie lookup** by ID
- **API Key authentication** (optional)
- **Health check** endpoint
- **Auto-generated API documentation** (Swagger UI, ReDoc)
- **Production-ready Docker** setup
- **Comprehensive test suite** with pytest

## Project Structure

```
movie_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory and setup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_health.py    # Health check routes
│   │   └── routes_movies.py    # Movie API routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration management
│   │   └── logging_config.py   # Logging setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── movie.py            # Pydantic models
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── movies_repository.py # Data access layer
│   ├── services/
│   │   ├── __init__.py
│   │   └── movies_service.py   # Business logic
│   └── deps/
│       ├── __init__.py
│       └── auth.py             # Auth dependencies
├── data/
│   └── movies.csv              # MovieLens data file
├── tests/
│   ├── __init__.py
│   └── test_movies_rest.py     # Test suite
├── conftest.py                 # Pytest configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
└── README.md                   # This file
```

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- MovieLens movies.csv file (download from https://grouplens.org/datasets/movielens/)

## Installation & Local Development

### 1. Clone/Setup the Project

```bash
cd movie_api
```

### 2. Create Virtual Environment

```bash
# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# On Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare Data

Download the MovieLens movies dataset and place it at `./data/movies.csv`.

**Expected CSV format:**
```
movieId,title,genres
1,Toy Story (1995),Adventure|Animation|Children|Comedy|Fantasy
2,Jumanji (1995),Adventure|Children|Fantasy
...
```

### 5. Run Locally

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- **API Docs (Swagger UI):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## API Endpoints

### Health Check (No Authentication)

```
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### List Movies

```
GET /api/movies?page=1&page_size=20&title=toy&genre=Adventure&year=1995
```

**Query Parameters:**
- `page` (int, default 1): Page number
- `page_size` (int, default 20, max 100): Items per page
- `title` (string, optional): Filter by partial title match (case-insensitive)
- `genre` (string, optional): Filter by genre (case-insensitive)
- `year` (int, optional): Filter by release year

**Response:**
```json
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
```

**Requires:** `X-API-Key` header (if `API_KEY` env var is set)

### Search Movies

```
GET /api/movies/search?q=story&genre=Animation&page=1&page_size=20
```

**Query Parameters:**
- `q` (string, required): Search query for title
- `page` (int, default 1): Page number
- `page_size` (int, default 20, max 100): Items per page
- `genre` (string, optional): Additional genre filter
- `year` (int, optional): Additional year filter

**Response:** Same as list movies

**Requires:** `X-API-Key` header (if `API_KEY` env var is set)

### Get Movie by ID

```
GET /api/movies/{movie_id}
```

**Response:**
```json
{
  "movie_id": 1,
  "title": "Toy Story (1995)",
  "year": 1995,
  "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"]
}
```

**Status Codes:**
- `200`: Movie found
- `404`: Movie not found

**Requires:** `X-API-Key` header (if `API_KEY` env var is set)

## Authentication

The API supports optional API Key authentication. To enable it:

### 1. Set API_KEY Environment Variable

```bash
export API_KEY=your-secret-key-here
```

### 2. Include Header in Requests

```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8000/api/movies
```

### Exempt Endpoints

The following endpoints **do not** require authentication:
- `/health`
- `/docs` (Swagger UI)
- `/redoc` (ReDoc)
- `/openapi.json`
- `/`

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app tests/
```

### Run Specific Test File

```bash
pytest tests/test_movies_rest.py
```

### Run Specific Test Class

```bash
pytest tests/test_movies_rest.py::TestListMovies
```

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t movielens-api:latest .
```

### 2. Run Container Locally

```bash
docker run --rm -p 8000:8000 \
  -e API_KEY=supersecret \
  -e DATA_FILE_PATH=/app/data/movies.csv \
  -e LOG_LEVEL=INFO \
  movielens-api:latest
```

### 3. Docker Compose (Optional)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      API_KEY: supersecret
      DATA_FILE_PATH: /app/data/movies.csv
      LOG_LEVEL: INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

Then run:

```bash
docker-compose up
```

## AWS Lightsail Deployment

### 1. Prepare Your Lightsail Instance

```bash
# SSH into your Lightsail instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. Upload Project

```bash
# From your local machine
scp -i your-key.pem -r ./movie_api/* ubuntu@your-instance-ip:/home/ubuntu/movie_api/
```

### 3. Build and Run on Lightsail

```bash
cd /home/ubuntu/movie_api

# Build the image
sudo docker build -t movielens-api .

# Run the container
sudo docker run -d --restart always \
  -p 80:8000 \
  -e API_KEY=your-production-key \
  -e DATA_FILE_PATH=/app/data/movies.csv \
  -e LOG_LEVEL=INFO \
  movielens-api
```

### 4. Access the API

Your API will be available at `http://your-instance-ip/api/movies`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Movie API | Application name |
| `API_V1_PREFIX` | /api | API prefix for routes |
| `DATA_FILE_PATH` | ./data/movies.csv | Path to movies CSV file |
| `API_KEY` | None | Required API key (optional) |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Code Quality & Architecture

### Design Patterns

- **Dependency Injection:** Used for service and repository injection
- **Repository Pattern:** Data access layer abstraction
- **Service Layer:** Business logic separated from routes
- **Factory Pattern:** FastAPI app creation in `main.py`

### Best Practices

- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Pydantic models for validation
- ✅ Proper error handling and status codes
- ✅ Logging throughout the application
- ✅ Clean separation of concerns
- ✅ Configurable via environment variables
- ✅ Security: Non-root Docker user, API key auth

### Testing

- Unit tests for repositories, services, and models
- Integration tests for API endpoints
- Test fixtures for sample data
- 40+ test cases covering all endpoints and filters

## Performance Considerations

- **In-Memory Storage:** Movies loaded at startup for fast read access
- **Pagination:** Prevents large response payloads
- **Filtering:** Done in-memory (efficient for typical dataset sizes)
- **Future:** Easy to replace CSV with database for larger scales

## Future Enhancements

- [ ] GraphQL API option
- [ ] Caching layer (Redis)
- [ ] Database backend (PostgreSQL)
- [ ] User ratings and reviews
- [ ] Advanced search with full-text indexing
- [ ] Rate limiting
- [ ] JWT authentication
- [ ] Multi-language support

## Troubleshooting

### CSV File Not Found

Ensure `data/movies.csv` exists. You can download from: https://grouplens.org/datasets/movielens/

### Port 8000 Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Or use a different port
uvicorn app.main:app --port 8001
```

### Authentication Error

If you get a 401 Unauthorized error, make sure:
1. The `X-API-Key` header is included
2. The value matches the `API_KEY` environment variable
3. You're accessing a protected endpoint (not `/health`)

### Docker Build Issues

```bash
# Clean build (no cache)
docker build --no-cache -t movielens-api .

# Check logs
docker logs <container-id>
```

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions, please refer to the code documentation and inline comments for detailed implementation information.

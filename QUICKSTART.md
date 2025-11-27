QUICK START GUIDE
=================

This is a production-ready REST API backend for the MovieLens movies dataset,
built with FastAPI, Docker-ready, and deployable to AWS Lightsail.


OPTION 1: RUN LOCALLY (Development)
====================================

1. Navigate to project directory:
   $ cd movie_api

2. Create virtual environment:
   $ python -m venv .venv
   
   On Windows:
   $ .venv\Scripts\activate
   
   On macOS/Linux:
   $ source .venv/bin/activate

3. Install dependencies:
   $ pip install -r requirements.txt

4. Ensure movies.csv is in ./data/ directory:
   - Download from https://grouplens.org/datasets/movielens/
   - Place at: ./data/movies.csv

5. Run the server:
   $ uvicorn app.main:app --reload

6. Access the API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

7. Try some endpoints:
   $ curl http://localhost:8000/api/movies
   $ curl http://localhost:8000/api/movies?genre=Action
   $ curl http://localhost:8000/api/movies/1
   $ curl http://localhost:8000/api/movies/search?q=toy


OPTION 2: RUN IN DOCKER (Local Testing)
========================================

1. Build the image:
   $ docker build -t movielens-api:latest .

2. Run the container:
   $ docker run --rm -p 8000:8000 \
     -e API_KEY=mysecretkey \
     -e LOG_LEVEL=INFO \
     movielens-api:latest

3. Access the API (same URLs as above):
   - API: http://localhost:8000/api/movies
   - Health: http://localhost:8000/health

4. With authentication:
   $ curl -H "X-API-Key: mysecretkey" http://localhost:8000/api/movies


OPTION 3: DEPLOY TO AWS LIGHTSAIL
==================================

1. Launch Lightsail instance:
   - OS: Ubuntu 22.04
   - Size: At least 2GB RAM

2. SSH into instance:
   $ ssh -i key.pem ubuntu@your-instance-ip

3. Install Docker:
   $ curl -fsSL https://get.docker.com -o get-docker.sh
   $ sudo sh get-docker.sh

4. Upload project:
   $ scp -i key.pem -r ./movie_api ubuntu@instance-ip:/home/ubuntu/

5. On the instance, build and run:
   $ cd /home/ubuntu/movie_api
   $ sudo docker build -t movielens-api .
   $ sudo docker run -d --restart always \
     -p 80:8000 \
     -e API_KEY=your-prod-key \
     movielens-api

6. Access your API:
   http://your-instance-ip/api/movies
   http://your-instance-ip/health


RUN TESTS
=========

Run all tests:
  $ pytest

Run specific test file:
  $ pytest tests/test_movies_rest.py

Run with coverage:
  $ pytest --cov=app tests/

Run specific test class:
  $ pytest tests/test_movies_rest.py::TestListMovies -v


KEY ENDPOINTS
=============

Health Check (no auth needed):
  GET /health
  → {"status": "ok"}

List Movies:
  GET /api/movies
  GET /api/movies?page=1&page_size=20
  GET /api/movies?title=toy
  GET /api/movies?genre=Action
  GET /api/movies?year=1995
  → Paginated list of movies

Search Movies:
  GET /api/movies/search?q=story
  GET /api/movies/search?q=story&genre=Animation
  → Search results with pagination

Get Single Movie:
  GET /api/movies/1
  → Single movie object or 404

API Documentation:
  GET /docs (Swagger UI)
  GET /redoc (ReDoc)


AUTHENTICATION (Optional)
==========================

Set API_KEY environment variable to enable:
  $ export API_KEY=your-secret-key

Then include header in requests:
  $ curl -H "X-API-Key: your-secret-key" http://localhost:8000/api/movies

Exempt endpoints (no auth needed):
  - /health
  - /docs
  - /redoc
  - /openapi.json
  - /


CONFIGURATION
==============

Environment variables:

APP_NAME                 Application name (default: Movie API)
API_V1_PREFIX           API prefix (default: /api)
DATA_FILE_PATH          Path to CSV (default: ./data/movies.csv)
API_KEY                 API key for auth (optional)
LOG_LEVEL               Log level (default: INFO)


PROJECT FILES
=============

Key files to understand:

app/main.py                    - FastAPI app setup and startup
app/api/routes_movies.py       - Movie API endpoints
app/services/movies_service.py - Business logic
app/repositories/movies_repository.py - CSV data loading
app/models/movie.py            - Data models
app/deps/auth.py               - Authentication
tests/test_movies_rest.py      - Comprehensive tests


TROUBLESHOOTING
===============

Q: Module 'app' not found
A: Make sure you're in the movie_api directory, and the virtual environment is activated

Q: Port 8000 already in use
A: Use different port: uvicorn app.main:app --port 8001

Q: CSV file not found
A: Download from https://grouplens.org/datasets/movielens/
   Place it at ./data/movies.csv

Q: Docker build fails
A: Try: docker build --no-cache -t movielens-api .

Q: 401 Unauthorized errors
A: If API_KEY is set, include header: -H "X-API-Key: your-key"
   Or disable by not setting API_KEY environment variable


NEXT STEPS
==========

1. Customize the code:
   - Add more filters
   - Add ratings data if available
   - Modify response schemas
   - Add caching
   - Add database backend

2. Deploy:
   - Push to Docker Hub/ECR
   - Deploy to Lightsail/ECS/EKS
   - Set up monitoring/logging

3. Extend:
   - Add GraphQL endpoint
   - Add user authentication (JWT)
   - Add user ratings/reviews
   - Add recommendation engine


FOR MORE DETAILS, SEE:
======================

README.md             - Complete documentation
PROJECT_STRUCTURE.md  - Architecture and design decisions
requirements.txt      - Dependencies
Dockerfile            - Container definition

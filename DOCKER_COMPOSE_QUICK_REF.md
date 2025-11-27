# Docker Compose Quick Reference

## TL;DR - Getting Started in 30 Seconds

```bash
# Start everything
docker-compose up --build

# In another terminal, wait ~20 seconds, then get a token:
curl -X POST "http://localhost:8081/realms/movie-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=movie-api-client" \
  -d "client_secret=<COPY_FROM_LOGS_BELOW>" \
  -d "grant_type=password" \
  -d "username=movieuser" \
  -d "password=moviepassword"

# Find the client secret in the logs:
docker-compose logs keycloak-setup | grep "Client Secret"
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| FastAPI | http://localhost:8000 | Your API |
| Keycloak | http://localhost:8081/admin | Admin console |
| PostgreSQL | localhost:5432 | Database |
| Token Endpoint | http://localhost:8081/realms/movie-realm/protocol/openid-connect/token | Get access tokens |

## Default Credentials

| Component | Username | Password |
|-----------|----------|----------|
| Keycloak Admin | admin | admin |
| Test User | movieuser | moviepassword |
| PostgreSQL | movie_api_user | movie_api_password |

## Useful Commands

```bash
# Start everything
docker-compose up --build

# Stop everything (keep data)
docker-compose stop

# Stop and remove everything (keep data)
docker-compose down

# Stop and remove everything INCLUDING data
docker-compose down -v

# View all service statuses
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app
docker-compose logs -f keycloak
docker-compose logs -f db

# Access FastAPI container shell
docker-compose exec app bash

# Access PostgreSQL CLI
docker-compose exec db psql -U movie_api_user -d movie_api_db

# Rebuild without restarting
docker-compose build

# Rebuild and restart single service
docker-compose up --build app
```

## Common Workflows

### Get an Access Token

```bash
# 1. Ensure services are running
docker-compose ps

# 2. Get the client secret from logs
CLIENT_SECRET=$(docker-compose logs keycloak-setup | grep "Client Secret" | grep -o "[a-zA-Z0-9]*$")

# 3. Request a token
curl -X POST "http://localhost:8081/realms/movie-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=movie-api-client" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "grant_type=password" \
  -d "username=movieuser" \
  -d "password=moviepassword"

# 4. Save the access_token value
```

### Call Your API

```bash
# With the token from above:
TOKEN="<paste_access_token_here>"

# Call an endpoint
curl -X GET "http://localhost:8000/health" \
  -H "Authorization: Bearer $TOKEN"

# Or call a protected endpoint
curl -X GET "http://localhost:8000/api/movies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: test-api-key-123"
```

### Access Keycloak Admin Console

1. Open http://localhost:8081/admin
2. Login with admin / admin
3. Navigate to "movie-realm" realm
4. Manage clients, users, roles, etc.

### Access PostgreSQL

```bash
# Option 1: Inside container
docker-compose exec db psql -U movie_api_user -d movie_api_db

# Option 2: From your machine (requires psql installed)
psql -h localhost -U movie_api_user -d movie_api_db
# Password: movie_api_password

# Common queries:
SELECT datname FROM pg_database;  -- List databases
\dt                               -- List tables
SELECT * FROM information_schema.tables;
```

## Checking Service Health

```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose exec db pg_isready -U movie_api_user -d movie_api_db
docker-compose exec keycloak curl -f http://localhost:8080/realms/master
docker-compose exec app curl http://localhost:8000/health
```

## Cleaning Up

```bash
# Remove all containers but keep volumes
docker-compose down

# Remove all containers AND volumes (fresh start)
docker-compose down -v

# Remove unused Docker images
docker image prune

# Remove unused volumes
docker volume prune
```

## Ports Reference

- **5432**: PostgreSQL (internal and external)
- **8000**: FastAPI (external only)
- **8081**: Keycloak (external, internal is 8080)

## Environment in Containers

Inside containers, services communicate using:
- Database: `db:5432` (not localhost!)
- Keycloak: `keycloak:8080` (not localhost!)
- FastAPI: `app:8000` (not localhost!)

From your machine:
- Database: `localhost:5432`
- Keycloak: `localhost:8081`
- FastAPI: `localhost:8000`

## Files Modified

```
.
├── docker-compose.yml           # NEW: Service definitions
├── scripts/
│   └── keycloak-setup.sh        # NEW: Keycloak configuration
├── Dockerfile                   # (existing, used by docker-compose)
├── app/
│   └── main.py                  # (existing, entrypoint)
└── requirements.txt             # (existing, dependencies)
```

## Next Steps

1. Run `docker-compose up --build`
2. Wait for services to initialize (~20-30 seconds)
3. Get a token using the commands above
4. Call your API endpoints
5. Access Keycloak admin console to explore configuration

For detailed information, see `DOCKER_COMPOSE_GUIDE.md`

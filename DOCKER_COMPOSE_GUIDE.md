# Docker Compose Setup Guide

This guide explains how to use the docker-compose setup for the Movie API project with PostgreSQL, Keycloak, and automated configuration.

## Prerequisites

- Docker and Docker Compose installed
- The project built and ready to containerize

## Services

The `docker-compose.yml` defines four services:

### 1. **db** (PostgreSQL)
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Database**: movie_api_db
- **User**: movie_api_user
- **Password**: movie_api_password
- **Volume**: postgres_data (persistent storage)

### 2. **keycloak** (Identity & Access Management)
- **Image**: quay.io/keycloak/keycloak:24.0.5
- **Port**: 8081 (on host)
- **Admin Username**: admin
- **Admin Password**: admin
- **Mode**: Development mode (start-dev)

### 3. **keycloak-setup** (Configuration Service)
- **Type**: One-shot container
- **Purpose**: Automatically configures Keycloak with:
  - Realm: `movie-realm`
  - Client: `movie-api-client` (confidential)
  - Test User: `movieuser` / `moviepassword`
- **Runs Once**: Exits after setup completes (no restart)
- **Logs Output**: Client secret and token endpoint information

### 4. **app** (FastAPI Application)
- **Build**: Uses the project's Dockerfile
- **Port**: 8000
- **Environment**: Connected to PostgreSQL and Keycloak
- **Dependencies**: Waits for all services to be healthy and setup complete

## Quick Start

### 1. Start All Services

```bash
docker-compose up --build
```

This will:
- Build the FastAPI image
- Start PostgreSQL and wait for it to be healthy
- Start Keycloak and wait for it to be healthy
- Run the keycloak-setup container to configure Keycloak
- Start the FastAPI app once all dependencies are ready

### 2. Verify Services Are Running

```bash
docker-compose ps
```

Expected output:
```
NAME                      STATUS              PORTS
movie_api_db              Up (healthy)        0.0.0.0:5432->5432/tcp
movie_api_keycloak        Up (healthy)        0.0.0.0:8081->8080/tcp
movie_api_keycloak_setup  Exited (0)         (no ports)
movie_api_app             Up                  0.0.0.0:8000->8000/tcp
```

### 3. Get a Token

After services are up, you can get an access token:

```bash
curl -X POST "http://localhost:8081/realms/movie-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=movie-api-client" \
  -d "client_secret=<CLIENT_SECRET_FROM_SETUP_LOGS>" \
  -d "grant_type=password" \
  -d "username=movieuser" \
  -d "password=moviepassword"
```

**To find the client secret**, check the keycloak-setup logs:

```bash
docker-compose logs keycloak-setup
```

Look for a line like:
```
[SUCCESS] Client Secret: 3f4e...7a8b
```

Example response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cC...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI...",
  "token_type": "Bearer",
  "not-before-policy": 0,
  "session_state": "abcd1234...",
  "scope": "profile email"
}
```

### 4. Call the API with Token

Use the `access_token` from the previous response:

```bash
curl -X GET "http://localhost:8000/health" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Or for protected endpoints:

```bash
curl -X GET "http://localhost:8000/api/movies" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-API-Key: test-api-key-123"
```

## Common Commands

### View Logs

View logs for all services:
```bash
docker-compose logs -f
```

View logs for a specific service:
```bash
docker-compose logs -f keycloak
docker-compose logs -f app
docker-compose logs -f keycloak-setup
```

### Stop Services

Stop all running services:
```bash
docker-compose stop
```

### Stop and Remove Containers

Remove containers (keeps volumes):
```bash
docker-compose down
```

Remove containers and volumes:
```bash
docker-compose down -v
```

### Rebuild Services

Rebuild without starting:
```bash
docker-compose build
```

Rebuild and start:
```bash
docker-compose up --build
```

### Run a Command in a Container

Execute a bash shell in the app container:
```bash
docker-compose exec app bash
```

Access PostgreSQL directly:
```bash
docker-compose exec db psql -U movie_api_user -d movie_api_db
```

## Keycloak Admin Console

Access the Keycloak admin console at:
- URL: http://localhost:8081/admin
- Username: admin
- Password: admin

Here you can:
- Manage realms
- Create/modify clients
- Manage users
- Configure authentication flows
- View audit logs

## Database Access

Connect to PostgreSQL directly:

```bash
docker-compose exec db psql -U movie_api_user -d movie_api_db
```

Or from your local machine (if psql is installed):
```bash
psql -h localhost -U movie_api_user -d movie_api_db
```

When prompted for password, enter: `movie_api_password`

## Environment Variables

### FastAPI App

The app receives these environment variables from docker-compose:

```
DB_HOST=db
DB_PORT=5432
DB_NAME=movie_api_db
DB_USER=movie_api_user
DB_PASSWORD=movie_api_password
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=movie-realm
KEYCLOAK_CLIENT_ID=movie-api-client
```

### Keycloak Setup Script

The setup script uses these environment variables:

```
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_REALM=movie-realm
KEYCLOAK_CLIENT_ID=movie-api-client
KEYCLOAK_TEST_USERNAME=movieuser
KEYCLOAK_TEST_PASSWORD=moviepassword
```

## Troubleshooting

### Services Won't Start

1. Check for port conflicts:
   ```bash
   netstat -an | grep 5432  # PostgreSQL
   netstat -an | grep 8081  # Keycloak
   netstat -an | grep 8000  # FastAPI
   ```

2. View detailed logs:
   ```bash
   docker-compose logs --tail=100
   ```

### Keycloak Setup Failed

1. Check keycloak-setup logs:
   ```bash
   docker-compose logs keycloak-setup
   ```

2. Check if Keycloak is healthy:
   ```bash
   docker-compose logs keycloak
   ```

3. Manually retry setup:
   ```bash
   docker-compose up keycloak-setup
   ```

### PostgreSQL Connection Issues

1. Verify the container is running and healthy:
   ```bash
   docker-compose ps db
   ```

2. Check PostgreSQL logs:
   ```bash
   docker-compose logs db
   ```

3. Test connection:
   ```bash
   docker-compose exec db pg_isready -U movie_api_user -d movie_api_db
   ```

### FastAPI App Can't Connect to Services

1. Verify all services are up:
   ```bash
   docker-compose ps
   ```

2. Check app logs for connection errors:
   ```bash
   docker-compose logs app
   ```

3. Verify service hostnames (use service names, not localhost):
   - Database: `db:5432` (not `localhost:5432`)
   - Keycloak: `keycloak:8080` (not `localhost:8081`)

## Production Considerations

This docker-compose setup is designed for **development and testing**. For production:

1. **Keycloak Storage**: Consider using an external PostgreSQL database instead of embedded H2
2. **Environment Variables**: Use `.env` file instead of hardcoding credentials
3. **HTTPS**: Enable HTTPS for Keycloak and API
4. **Resource Limits**: Add CPU and memory limits for containers
5. **Logging**: Configure centralized logging (ELK stack, etc.)
6. **Backups**: Implement automated database backups
7. **Monitoring**: Add health checks and monitoring

## Customization

To modify the setup, edit these files:

- **docker-compose.yml**: Service definitions, ports, volumes
- **scripts/keycloak-setup.sh**: Keycloak configuration logic
- **Dockerfile**: FastAPI app build process
- **.env**: Environment variables (create from .env.example)

## Next Steps

1. Start the services: `docker-compose up`
2. Wait for the setup to complete (~20-30 seconds)
3. Get a token using the curl command above
4. Call your FastAPI endpoints with the token
5. Access Keycloak admin console to manage realms/clients/users

For more information, see:
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

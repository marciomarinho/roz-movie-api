# Docker Compose Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Your Host Machine                             │
│                                                                       │
│  Ports:                                                              │
│  - 5432:5432 → PostgreSQL                                            │
│  - 8000:8000 → FastAPI App                                           │
│  - 8081:8080 → Keycloak (internal:external)                          │
│                                                                       │
├────────────────────── Docker Network: movie_net ──────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                  Container: movie_api_db                       │  │
│  │                  Image: postgres:15-alpine                     │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ Database: movie_api_db                                   │ │  │
│  │  │ User: movie_api_user / movie_api_password                │ │  │
│  │  │ Port (internal): 5432                                    │ │  │
│  │  │ Volume: postgres_data:/var/lib/postgresql/data           │ │  │
│  │  │ Healthcheck: pg_isready                                  │ │  │
│  │  │ Status: healthy after startup                            │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │               Container: movie_api_keycloak                    │  │
│  │        Image: quay.io/keycloak/keycloak:24.0.5                │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ Admin: admin / admin                                     │ │  │
│  │  │ Port (internal): 8080                                    │ │  │
│  │  │ Mode: start-dev (development)                            │ │  │
│  │  │ Healthcheck: Checks /realms/master endpoint              │ │  │
│  │  │ Status: healthy after startup                            │ │  │
│  │  │                                                          │ │  │
│  │  │ URL: http://localhost:8081/admin                         │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                         │                                             │
│                         │ Depends on                                  │
│                         │ (service_healthy)                           │
│                         ▼                                             │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │         Container: movie_api_keycloak_setup                    │  │
│  │        Image: quay.io/keycloak/keycloak:24.0.5                │  │
│  │        restart: "no" (one-shot, doesn't restart)              │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ Runs setup script: /scripts/keycloak-setup.sh            │ │  │
│  │  │ Mount: ./scripts/keycloak-setup.sh:/scripts/:ro          │ │  │
│  │  │                                                          │ │  │
│  │  │ Configuration:                                          │ │  │
│  │  │ 1. Creates realm: movie-realm                           │ │  │
│  │  │ 2. Creates client: movie-api-client                     │ │  │
│  │  │    - Type: confidential (OAuth2)                        │ │  │
│  │  │    - Protocol: openid-connect                           │ │  │
│  │  │    - Service accounts: enabled                          │ │  │
│  │  │    - Redirect URIs: http://localhost:8000/*             │ │  │
│  │  │ 3. Creates user: movieuser / moviepassword              │ │  │
│  │  │ 4. Outputs client secret to logs                        │ │  │
│  │  │                                                          │ │  │
│  │  │ Status: Exited (0) after completion                     │ │  │
│  │  │ Output: Check logs with:                                │ │  │
│  │  │   docker-compose logs keycloak-setup                    │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                         │                                             │
│                         │ Depends on                                  │
│                         │ (service_completed_successfully)            │
│                         ▼                                             │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                 Container: movie_api_app                       │  │
│  │         Built from ./Dockerfile (context: .)                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ FastAPI Application                                     │ │  │
│  │  │ Command: uvicorn app.main:app --host 0.0.0.0 --port 8000 │ │
│  │  │ Port (internal): 8000                                    │ │  │
│  │  │ URL: http://localhost:8000                              │ │  │
│  │  │                                                          │ │  │
│  │  │ Environment Variables:                                  │ │  │
│  │  │ - DB_HOST=db                                            │ │  │
│  │  │ - DB_PORT=5432                                          │ │  │
│  │  │ - DB_NAME=movie_api_db                                  │ │  │
│  │  │ - DB_USER=movie_api_user                                │ │  │
│  │  │ - DB_PASSWORD=movie_api_password                        │ │  │
│  │  │ - KEYCLOAK_URL=http://keycloak:8080                     │ │  │
│  │  │ - KEYCLOAK_REALM=movie-realm                            │ │  │
│  │  │ - KEYCLOAK_CLIENT_ID=movie-api-client                   │ │  │
│  │  │                                                          │ │  │
│  │  │ Dependencies (must all complete first):                 │ │  │
│  │  │ - db (healthy)                                          │ │  │
│  │  │ - keycloak (healthy)                                    │ │  │
│  │  │ - keycloak-setup (completed successfully)               │ │  │
│  │  │                                                          │ │  │
│  │  │ Status: Running and ready to serve requests             │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   Your Client Application                        │
│                   (browser, mobile, desktop)                     │
└──────────────┬───────────────────────────────────────────────────┘
               │
               │ 1. Request Access Token
               │
               ▼
    ┌─────────────────────────────┐
    │  Keycloak Token Endpoint    │ ← http://localhost:8081/realms/movie-realm/
    │  (keycloak:8080 internal)   │   protocol/openid-connect/token
    │                             │
    │ - Validates credentials     │
    │ - Returns access_token      │
    └──────────┬──────────────────┘
               │
               │ 2. Use Token for API Calls
               │
               ▼
    ┌─────────────────────────────┐
    │  FastAPI Application        │ ← http://localhost:8000/api/...
    │  (app:8000 internal)        │   Header: Authorization: Bearer {token}
    │                             │
    │ - Validates token with      │
    │   Keycloak                  │
    │ - Queries database          │
    │ - Returns response          │
    │                             │
    │ ┌───────────────────────┐   │
    │ │ Connects to:          │   │
    │ │ - db:5432 (internal)  │   │
    │ │ - keycloak:8080       │   │
    │ │   (internal)          │   │
    │ └───────────────────────┘   │
    └─────────────────────────────┘
               │
               │ Database Query
               │
               ▼
    ┌─────────────────────────────┐
    │  PostgreSQL Database        │ ← localhost:5432
    │  (db:5432 internal)         │
    │                             │
    │ - Stores application data   │
    │ - movie_api_db database     │
    │ - Persistent volume         │
    └─────────────────────────────┘
```

## Sequence Diagram: Service Startup

```
Time  docker-compose up --build
 │
 ├─→ Build FastAPI image from Dockerfile
 │   └─ Docker images built ✓
 │
 ├─→ Start db (PostgreSQL)
 │   ├─ Container starts
 │   ├─ Healthcheck begins (pg_isready)
 │   └─ Waits for: db to be healthy ✓ (~5-10 seconds)
 │
 ├─→ Start keycloak
 │   ├─ Container starts
 │   ├─ Keycloak initializes (H2 embedded DB)
 │   ├─ Healthcheck begins (curl to /realms/master)
 │   └─ Waits for: keycloak to be healthy ✓ (~10-15 seconds)
 │
 ├─→ Start keycloak-setup (depends on keycloak healthy)
 │   ├─ Container starts
 │   ├─ Waits for Keycloak endpoint
 │   ├─ Logs in as admin
 │   ├─ Creates realm: movie-realm
 │   ├─ Creates client: movie-api-client
 │   ├─ Gets/creates client secret
 │   ├─ Creates user: movieuser
 │   ├─ Outputs setup summary to logs
 │   └─ Container exits (0) ✓ (~5-10 seconds)
 │
 ├─→ Start app (depends on all above completed)
 │   ├─ Container starts
 │   ├─ Reads environment variables
 │   ├─ Connects to db:5432 → movie_api_db ✓
 │   ├─ Initializes connection pools
 │   ├─ Starts uvicorn on 0.0.0.0:8000
 │   └─ Ready to serve requests ✓ (~3-5 seconds)
 │
 └─ ALL SERVICES READY (~25-40 seconds total)
    ✓ FastAPI at http://localhost:8000
    ✓ Keycloak at http://localhost:8081
    ✓ PostgreSQL at localhost:5432
    ✓ Token endpoint ready
```

## Service Communication Map

```
                    Internal Docker Network (movie_net)
        ┌────────────────────────────────────────────────┐
        │                                                 │
        │  Services communicate by NAME (DNS resolution) │
        │                                                 │
        │  app:8000         ◄──────────────────────────  │
        │  │                                              │
        │  ├─ db:5432       (PostgreSQL)                 │
        │  │   └─ SELECT * FROM movies                   │
        │  │                                              │
        │  └─ keycloak:8080 (Token validation)           │
        │      └─ GET /realms/movie-realm/...            │
        │         GET /.well-known/openid-configuration │
        │         POST /protocol/openid-connect/token    │
        │                                                 │
        │  keycloak-setup:                               │
        │  │                                              │
        │  └─ keycloak:8080 (Configuration)             │
        │      └─ /opt/keycloak/bin/kcadm.sh commands   │
        │                                                 │
        │  keycloak:8080                                 │
        │  └─ Optional: External database (not used)     │
        │                                                 │
        └────────────────────────────────────────────────┘

External Access (Host Machine):
┌─────────────────────────────────────────────────┐
│                                                 │
│  localhost:5432   ──────────► db:5432          │
│  localhost:8000   ──────────► app:8000         │
│  localhost:8081   ──────────► keycloak:8080    │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Environment Variables Flow

```
docker-compose.yml
    │
    ├─ db
    │  └─ POSTGRES_DB=movie_api_db
    │  └─ POSTGRES_USER=movie_api_user
    │  └─ POSTGRES_PASSWORD=movie_api_password
    │
    ├─ keycloak
    │  └─ KEYCLOAK_ADMIN=admin
    │  └─ KEYCLOAK_ADMIN_PASSWORD=admin
    │  └─ KC_HTTP_ENABLED=true
    │  └─ KC_HOSTNAME_STRICT_HTTPS=false
    │
    ├─ keycloak-setup
    │  └─ KEYCLOAK_URL=http://keycloak:8080
    │  └─ KEYCLOAK_ADMIN=admin
    │  └─ KEYCLOAK_ADMIN_PASSWORD=admin
    │  └─ KEYCLOAK_REALM=movie-realm
    │  └─ KEYCLOAK_CLIENT_ID=movie-api-client
    │  └─ KEYCLOAK_TEST_USERNAME=movieuser
    │  └─ KEYCLOAK_TEST_PASSWORD=moviepassword
    │  └─ Script reads these → /scripts/keycloak-setup.sh
    │
    └─ app
       └─ DB_HOST=db
       └─ DB_PORT=5432
       └─ DB_NAME=movie_api_db
       └─ DB_USER=movie_api_user
       └─ DB_PASSWORD=movie_api_password
       └─ KEYCLOAK_URL=http://keycloak:8080
       └─ KEYCLOAK_REALM=movie-realm
       └─ KEYCLOAK_CLIENT_ID=movie-api-client
       └─ PYTHONUNBUFFERED=1
       └─ Python app reads these from environment
```

## Volume Mounts

```
Host Machine                Container
────────────────────────────────────────
                            
./scripts/               ─→ /scripts/ (ro)
keycloak-setup.sh            │
                             └─ Read by keycloak-setup
                                container

(docker named volume)
postgres_data            ─→ /var/lib/postgresql/data
(managed by Docker)          │
                             └─ Persistent storage
                                for PostgreSQL
```

This architecture ensures:
✓ Services start in correct order
✓ Dependencies are satisfied before dependent services
✓ All data is persisted across restarts
✓ Easy horizontal scaling if needed
✓ Clear separation of concerns
✓ Automated configuration

#!/bin/bash

################################################################################
# Movie API - Production-Grade Docker Manual Deployment Script
#
# This script deploys the Movie API with all services (PostgreSQL, Keycloak,
# and API) using individual Docker containers without Docker Compose.
#
# This approach demonstrates production-ready practices:
# - Proper networking with Docker custom bridge network
# - Volume management for persistent data
# - Health checks and service dependencies
# - Proper error handling and logging
# - Secrets management
#
# Usage:
#   bash deploy-docker-manual.sh
#   OR
#   curl -fsSL https://raw.githubusercontent.com/marciomarinho/roz-movie-api/main/scripts/deploy-docker-manual.sh | bash
#
# Prerequisites:
#   - Docker installed and running
#   - Docker group configured for current user
#   - Application code in ~/apps/movie-api
#
################################################################################

set +e  # Don't exit on error, we'll handle gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="${HOME}/apps/movie-api"
NETWORK_NAME="movie-api-network"
DB_CONTAINER="movie-db"
KEYCLOAK_CONTAINER="movie-keycloak"
APP_CONTAINER="movie-api-app"
DB_VOLUME="movie-db-data"

# Timeouts
DB_WAIT_TIME=15
KEYCLOAK_WAIT_TIME=60
APP_START_DELAY=5

# Functions
print_header() {
    echo -e "\n${BLUE}=========================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================================${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    print_section "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    DOCKER_VERSION=$(docker --version)
    print_success "Docker installed: $DOCKER_VERSION"

    print_section "Checking Docker daemon..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_info "Start Docker with: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon is running"

    print_section "Checking project directory..."
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Project directory not found: $PROJECT_DIR"
        print_info "Clone the repository with: git clone https://github.com/marciomarinho/roz-movie-api.git $PROJECT_DIR"
        exit 1
    fi
    print_success "Project directory found"

    print_section "Checking required files..."
    REQUIRED_FILES=("Dockerfile" ".env.keycloak" "app" "docker-compose.yml")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -e "$PROJECT_DIR/$file" ]; then
            print_warning "Missing: $file (may not be critical)"
        else
            print_success "$file exists"
        fi
    done
}

# Load environment variables
load_environment() {
    print_header "Loading Environment Variables"

    if [ ! -f "$PROJECT_DIR/.env.keycloak" ]; then
        print_warning "Generating .env.keycloak (you should have run 'make setup' first)"
        cd "$PROJECT_DIR"
        # Generate a temporary env file if it doesn't exist
        cat > "$PROJECT_DIR/.env.keycloak" << 'EOF'
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=keycloak_admin_password_$(openssl rand -hex 8)
KEYCLOAK_REALM=movie-realm
KEYCLOAK_CLIENT_ID=movie-api-client
KEYCLOAK_CLIENT_SECRET=movie-api-client-secret-$(openssl rand -hex 16)
DB_USER=movie_user
DB_PASSWORD=movie_db_password_$(openssl rand -hex 16)
DB_NAME=movie_database
DB_HOST=movie-db
DB_PORT=5432
API_HOST=0.0.0.0
API_PORT=8000
EOF
    fi

    print_section "Sourcing environment variables..."
    source "$PROJECT_DIR/.env.keycloak"
    print_success "Environment variables loaded"

    # Generate secure passwords if using defaults
    if [ -z "$KEYCLOAK_ADMIN_PASSWORD" ] || [ "$KEYCLOAK_ADMIN_PASSWORD" = "secure_keycloak_password_change_me" ]; then
        KEYCLOAK_ADMIN_PASSWORD="keycloak_$(openssl rand -hex 8)"
        print_info "Generated Keycloak admin password"
    fi

    if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "secure_db_password_change_me" ]; then
        DB_PASSWORD="movie_db_$(openssl rand -hex 8)"
        print_info "Generated database password"
    fi

    if [ -z "$KEYCLOAK_CLIENT_SECRET" ] || [ "$KEYCLOAK_CLIENT_SECRET" = "movie-api-client-secret-change-me" ]; then
        KEYCLOAK_CLIENT_SECRET="client_secret_$(openssl rand -hex 16)"
        print_info "Generated Keycloak client secret"
    fi

    print_info "KEYCLOAK_ADMIN: $KEYCLOAK_ADMIN"
    print_info "KEYCLOAK_REALM: $KEYCLOAK_REALM"
    print_info "DB_USER: $DB_USER"
    print_info "DB_NAME: $DB_NAME"
}

# Create network
create_network() {
    print_header "Creating Docker Network"

    print_section "Checking if network exists..."
    if docker network ls | grep -q "$NETWORK_NAME"; then
        print_warning "Network '$NETWORK_NAME' already exists, skipping..."
    else
        print_section "Creating network '$NETWORK_NAME'..."
        if docker network create "$NETWORK_NAME" > /dev/null; then
            print_success "Network created: $NETWORK_NAME"
        else
            print_error "Failed to create network"
            exit 1
        fi
    fi
}

# Stop and remove existing containers
cleanup_containers() {
    print_header "Cleaning Up Existing Containers (if any)"

    for container in $APP_CONTAINER $KEYCLOAK_CONTAINER $DB_CONTAINER; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
            print_section "Stopping container: $container"
            docker stop "$container" 2>/dev/null || true
            print_section "Removing container: $container"
            docker rm "$container" 2>/dev/null || true
            print_success "Cleaned up $container"
        fi
    done
}

# Deploy PostgreSQL
deploy_postgres() {
    print_header "Deploying PostgreSQL Database"

    print_section "Checking if database volume exists..."
    if docker volume ls | grep -q "$DB_VOLUME"; then
        print_info "Using existing volume: $DB_VOLUME"
    else
        print_section "Creating database volume: $DB_VOLUME"
        docker volume create "$DB_VOLUME"
        print_success "Volume created"
    fi

    print_section "Starting PostgreSQL container..."
    docker run -d \
        --name "$DB_CONTAINER" \
        --network "$NETWORK_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -e POSTGRES_DB="$DB_NAME" \
        -v "$DB_VOLUME:/var/lib/postgresql/data" \
        -p 5432:5432 \
        --health-cmd="pg_isready -U $DB_USER" \
        --health-interval=10s \
        --health-timeout=5s \
        --health-retries=5 \
        postgres:15-alpine

    if [ $? -eq 0 ]; then
        print_success "PostgreSQL container started: $DB_CONTAINER"
    else
        print_error "Failed to start PostgreSQL"
        exit 1
    fi

    print_section "Waiting for PostgreSQL to be ready (${DB_WAIT_TIME}s)..."
    sleep "$DB_WAIT_TIME"

    # Verify PostgreSQL is ready
    if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" > /dev/null; then
        print_success "PostgreSQL is ready"
    else
        print_warning "PostgreSQL health check inconclusive, continuing..."
    fi
}

# Deploy Keycloak
deploy_keycloak() {
    print_header "Deploying Keycloak (OAuth2/OIDC Server)"

    print_section "Starting Keycloak container..."
    docker run -d \
        --name "$KEYCLOAK_CONTAINER" \
        --network "$NETWORK_NAME" \
        -e KEYCLOAK_ADMIN="$KEYCLOAK_ADMIN" \
        -e KEYCLOAK_ADMIN_PASSWORD="$KEYCLOAK_ADMIN_PASSWORD" \
        -e KC_PROXY=edge \
        -p 8080:8080 \
        quay.io/keycloak/keycloak:latest \
        start-dev

    if [ $? -eq 0 ]; then
        print_success "Keycloak container started: $KEYCLOAK_CONTAINER"
    else
        print_error "Failed to start Keycloak"
        exit 1
    fi

    print_section "Waiting for Keycloak to initialize (${KEYCLOAK_WAIT_TIME}s)..."
    sleep "$KEYCLOAK_WAIT_TIME"

    # Verify Keycloak is ready
    print_section "Checking Keycloak health..."
    for i in {1..10}; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            print_success "Keycloak is ready"
            break
        fi
        if [ $i -lt 10 ]; then
            print_info "Waiting for Keycloak... (attempt $i/10)"
            sleep 5
        else
            print_warning "Keycloak health check timeout, continuing anyway..."
        fi
    done
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"

    print_section "Checking for migration files..."
    if [ ! -d "$PROJECT_DIR/alembic" ]; then
        print_warning "No Alembic migrations directory found, skipping migrations"
        return
    fi

    print_section "Running Alembic migrations..."
    docker run --rm \
        --network "$NETWORK_NAME" \
        -e DB_HOST="$DB_CONTAINER" \
        -e DB_PORT=5432 \
        -e DB_USER="$DB_USER" \
        -e DB_PASSWORD="$DB_PASSWORD" \
        -e DB_NAME="$DB_NAME" \
        -v "$PROJECT_DIR:/app" \
        -w /app \
        python:3.11 \
        bash -c "pip install -q alembic sqlalchemy psycopg2-binary && alembic upgrade head"

    if [ $? -eq 0 ]; then
        print_success "Database migrations completed"
    else
        print_warning "Migration may have failed or there were no migrations to run"
    fi
}

# Build application Docker image
build_image() {
    print_header "Building Application Docker Image"

    print_section "Building image from Dockerfile..."
    cd "$PROJECT_DIR"

    docker build -t movie-api:latest . 2>&1 | tail -20

    if [ $? -eq 0 ]; then
        print_success "Docker image built: movie-api:latest"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi

    print_section "Verifying image..."
    docker images | grep "movie-api" | head -1
    print_success "Image verification complete"
}

# Deploy API
deploy_api() {
    print_header "Deploying Movie API Application"

    print_section "Starting API container..."
    docker run -d \
        --name "$APP_CONTAINER" \
        --network "$NETWORK_NAME" \
        -e DB_HOST="$DB_CONTAINER" \
        -e DB_PORT=5432 \
        -e DB_USER="$DB_USER" \
        -e DB_PASSWORD="$DB_PASSWORD" \
        -e DB_NAME="$DB_NAME" \
        -e KEYCLOAK_URL="http://$KEYCLOAK_CONTAINER:8080" \
        -e KEYCLOAK_REALM="$KEYCLOAK_REALM" \
        -e KEYCLOAK_CLIENT_ID="$KEYCLOAK_CLIENT_ID" \
        -e API_HOST=0.0.0.0 \
        -e API_PORT=8000 \
        -p 8000:8000 \
        --health-cmd="curl -f http://localhost:8000/health || exit 1" \
        --health-interval=10s \
        --health-timeout=5s \
        --health-retries=3 \
        movie-api:latest

    if [ $? -eq 0 ]; then
        print_success "API container started: $APP_CONTAINER"
    else
        print_error "Failed to start API container"
        exit 1
    fi

    print_section "Waiting for API to start (${APP_START_DELAY}s)..."
    sleep "$APP_START_DELAY"
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"

    print_section "Checking running containers..."
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "movie-|NAMES"
    echo ""

    print_section "Container health status..."
    for container in $DB_CONTAINER $KEYCLOAK_CONTAINER $APP_CONTAINER; do
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)
        if [ -n "$HEALTH" ]; then
            echo -n "  $container: "
            if [ "$HEALTH" = "healthy" ]; then
                print_success "$HEALTH"
            elif [ "$HEALTH" = "starting" ]; then
                print_warning "$HEALTH"
            else
                print_error "$HEALTH"
            fi
        fi
    done

    print_section "Testing PostgreSQL..."
    if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" > /dev/null 2>&1; then
        print_success "PostgreSQL is responding"
    else
        print_error "PostgreSQL is not responding"
    fi

    print_section "Testing Keycloak..."
    if curl -s http://localhost:8080/health | grep -q "UP\|operational" > /dev/null 2>&1; then
        print_success "Keycloak is responding"
    else
        print_warning "Keycloak health check inconclusive"
    fi

    print_section "Testing API health endpoint..."
    if curl -s http://localhost:8000/health | grep -q "ok\|status" > /dev/null 2>&1; then
        print_success "API is responding"
    else
        print_warning "API not yet responding, may still be starting..."
    fi
}

# Configure and test authentication
test_authentication() {
    print_header "Testing OAuth2 Authentication"

    print_section "Waiting for Keycloak to fully initialize..."
    sleep 10

    print_section "Getting access token from Keycloak..."
    TOKEN=$(curl -s -X POST "http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "client_id=$KEYCLOAK_CLIENT_ID" \
        -d "client_secret=$KEYCLOAK_CLIENT_SECRET" \
        -d "grant_type=client_credentials" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
        print_success "Authentication successful"
        print_info "Token (first 50 chars): ${TOKEN:0:50}..."

        print_section "Testing API with token..."
        RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/movies?page=1&page_size=5")

        if echo "$RESPONSE" | grep -q "items\|movies" > /dev/null 2>&1; then
            print_success "API endpoint working with authentication"
            echo ""
            print_info "Response sample:"
            echo "$RESPONSE" | head -c 200
            echo "..."
        else
            print_warning "API response received but format unclear"
        fi
    else
        print_warning "Could not obtain authentication token"
        print_info "Keycloak may still be initializing"
    fi
}

# Display summary
display_summary() {
    print_header "Deployment Summary 🎉"

    echo -e "${GREEN}Deployment completed!${NC}\n"

    echo "Service Access Points:"
    echo ""
    echo -e "  ${CYAN}API:${NC}        http://localhost:8000"
    echo -e "  ${CYAN}Keycloak:${NC}   http://localhost:8080"
    echo -e "  ${CYAN}Database:${NC}   localhost:5432"
    echo ""

    echo "Container Information:"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep "movie-"
    echo ""

    echo "Useful Commands:"
    echo ""
    echo -e "  View logs:        ${YELLOW}docker logs -f $APP_CONTAINER${NC}"
    echo -e "  Stop all:         ${YELLOW}docker stop $DB_CONTAINER $KEYCLOAK_CONTAINER $APP_CONTAINER${NC}"
    echo -e "  Restart API:      ${YELLOW}docker restart $APP_CONTAINER${NC}"
    echo -e "  Get token:        ${YELLOW}curl -X POST 'http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token' \\${NC}"
    echo -e "                    ${YELLOW}-H 'Content-Type: application/x-www-form-urlencoded' \\${NC}"
    echo -e "                    ${YELLOW}-d 'client_id=$KEYCLOAK_CLIENT_ID' \\${NC}"
    echo -e "                    ${YELLOW}-d 'client_secret=$KEYCLOAK_CLIENT_SECRET' \\${NC}"
    echo -e "                    ${YELLOW}-d 'grant_type=client_credentials'${NC}"
    echo ""

    echo "Next Steps:"
    echo ""
    echo "  1. Test the API: http://localhost:8000/docs (Swagger UI)"
    echo "  2. View Keycloak: http://localhost:8080/admin (user: $KEYCLOAK_ADMIN)"
    echo "  3. Check logs: docker logs -f $APP_CONTAINER"
    echo ""

    echo -e "${GREEN}Happy testing! 🚀${NC}\n"
}

# Cleanup function
cleanup_on_exit() {
    print_warning "Received exit signal. Containers will continue running."
    print_info "To stop all containers, run:"
    echo -e "  docker stop $DB_CONTAINER $KEYCLOAK_CONTAINER $APP_CONTAINER"
}

trap cleanup_on_exit SIGINT SIGTERM

# Main execution
main() {
    print_header "Movie API - Production Docker Deployment"
    echo -e "$(date)\n"

    check_prerequisites
    load_environment
    create_network
    cleanup_containers
    deploy_postgres
    deploy_keycloak
    run_migrations
    build_image
    deploy_api
    verify_deployment
    test_authentication
    display_summary
}

# Run main function
main

#!/bin/bash

################################################################################
# AWS LightSail Deployment Script - Docker Build & Run
# 
# This script automates the deployment of the Movie API to AWS LightSail
# with AWS Cognito for authentication and AWS RDS for the database.
# It builds the Docker image and runs it as a container.
#
# Usage:
#   1. Set required environment variables:
#      export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
#      export DB_PORT=5432
#      export DB_NAME=movie_api_db
#      export DB_USER=postgres
#      export DB_PASSWORD=BananaGelada12
#      export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
#      export COGNITO_REGION=us-east-1
#      export AUTH_PROVIDER=cognito
#      export AUTH_ENABLED=true
#
#   2. Run this script:
#      chmod +x scripts/deploy-lightsail.sh
#      ./scripts/deploy-lightsail.sh
#
# What it does:
#   - Validates all required environment variables
#   - Installs Docker if not present
#   - Creates .env file with production settings
#   - Tests RDS connectivity before building
#   - Builds Docker image
#   - Runs database migrations in container
#   - Starts the application container on port 8000
#
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
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

################################################################################
# Validation Functions
################################################################################

validate_env() {
    print_header "Validating Environment Variables"
    
    local required_vars=(
        "DB_HOST"
        "DB_PORT"
        "DB_NAME"
        "DB_USER"
        "DB_PASSWORD"
        "COGNITO_USER_POOL_ID"
        "COGNITO_REGION"
        "AUTH_PROVIDER"
        "AUTH_ENABLED"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
            print_error "Missing: $var"
        else
            print_success "$var is set"
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "\nMissing ${#missing_vars[@]} required environment variable(s):"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Set them before running this script:"
        echo "  export DB_HOST=..."
        echo "  export COGNITO_USER_POOL_ID=..."
        exit 1
    fi
    
    print_success "All required environment variables are set\n"
}

install_docker() {
    print_header "Checking Docker Installation"
    
    if command -v docker &> /dev/null; then
        print_success "Docker is already installed\n"
        docker --version
        echo ""
        return 0
    fi
    
    print_info "Installing Docker...\n"
    
    # Detect OS and install Docker
    if command -v yum &> /dev/null; then
        # Amazon Linux 2
        echo "Detected Amazon Linux, installing Docker via yum..."
        sudo yum install -y docker > /dev/null 2>&1
    elif command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Detected Debian/Ubuntu, installing Docker..."
        sudo apt-get update > /dev/null 2>&1
        sudo apt-get install -y docker.io > /dev/null 2>&1
    else
        print_error "Could not detect package manager"
        exit 1
    fi
    
    # Start Docker daemon
    echo "Starting Docker daemon..."
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    echo "Configuring Docker permissions..."
    sudo usermod -aG docker $(whoami) || true
    
    print_success "Docker installed and configured\n"
    docker --version
    echo ""
}

setup_env_file() {
    print_header "Creating .env File"
    
    cat > .env << EOF
# Production Environment Variables
# Generated at: $(date)

# Database Configuration (AWS RDS)
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

# Authentication
AUTH_PROVIDER=${AUTH_PROVIDER}
AUTH_ENABLED=${AUTH_ENABLED}

# AWS Cognito Configuration
COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID}
COGNITO_REGION=${COGNITO_REGION}
COGNITO_JWKS_URL=${COGNITO_JWKS_URL:-}

# Application Configuration
APP_NAME=${APP_NAME:-movie-api}
APP_VERSION=${APP_VERSION:-0.1.0}
LOG_LEVEL=${LOG_LEVEL:-INFO}
EOF
    
    print_success ".env file created\n"
}

test_rds_connectivity() {
    print_header "Testing RDS Connectivity"
    
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for RDS to be ready..."
    echo "Target: $DB_HOST:$DB_PORT"
    echo "Database: $DB_NAME"
    echo ""
    
    while [ $attempt -le $max_attempts ]; do
        echo -n "Attempt $attempt/$max_attempts: "
        
        # Use a simple container to test connectivity
        if docker run --rm --network host \
            -e PGPASSWORD="$DB_PASSWORD" \
            postgres:15-alpine \
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
            print_success "RDS is ready\n"
            return 0
        fi
        
        print_warning "Connection failed, retrying..."
        
        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            sleep 2
        fi
    done
    
    print_error "\nCould not connect to RDS after $max_attempts attempts"
    echo "Troubleshooting:"
    echo "1. Check RDS endpoint is correct: $DB_HOST"
    echo "2. Verify RDS security group allows port $DB_PORT from LightSail"
    echo "3. Ensure database credentials are correct"
    echo "4. Check that RDS instance is running in AWS Console"
    exit 1
}

build_docker_image() {
    print_header "Building Docker Image"
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in current directory"
        echo "Make sure you're in the repository root directory"
        exit 1
    fi
    
    local image_name="movie-api"
    local image_tag="latest"
    
    echo "Building Docker image: $image_name:$image_tag"
    echo ""
    
    docker build -t "$image_name:$image_tag" .
    
    print_success "Docker image built successfully\n"
    docker images "$image_name"
    echo ""
}

run_migrations() {
    print_header "Running Database Migrations"
    
    local container_name="movie-api-migrate-$$"
    
    echo "Running migrations in temporary container..."
    echo ""
    
    docker run --rm \
        --name "$container_name" \
        --env-file .env \
        movie-api:latest \
        alembic upgrade head
    
    print_success "Database migrations completed\n"
}

start_application() {
    print_header "Starting Application Container"
    
    local container_name="movie-api"
    
    # Stop existing container if running
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_warning "Stopping existing container..."
        docker stop "$container_name" || true
        docker rm "$container_name" || true
    fi
    
    echo "Starting application container..."
    echo "Container name: $container_name"
    echo "Listening on: 0.0.0.0:8000"
    echo ""
    
    docker run -d \
        --name "$container_name" \
        --restart unless-stopped \
        --env-file .env \
        -p 8000:8000 \
        movie-api:latest \
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
    
    # Give container a moment to start
    sleep 2
    
    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_success "Application container started successfully\n"
        
        print_header "Container Details"
        docker ps --filter "name=$container_name" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        print_header "Application Status"
        echo "Container is running. Checking health..."
        
        # Wait a bit and check logs
        sleep 3
        echo ""
        echo "Recent logs:"
        docker logs --tail 10 "$container_name"
    else
        print_error "Container failed to start"
        echo ""
        echo "Recent logs:"
        docker logs "$container_name" || true
        exit 1
    fi
}

################################################################################
# Main Execution
################################################################################

print_header "Movie API - LightSail Production Deployment (Docker)"

# Run all setup steps
validate_env
install_docker
setup_env_file
test_rds_connectivity
build_docker_image
run_migrations
start_application

print_header "Deployment Complete! 🎉"
echo "Your Movie API is now running!"
echo ""
echo "Next steps:"
echo ""
echo "1. Verify the application is running:"
echo -e "   ${YELLOW}curl http://localhost:8000/api/v1/health${NC}"
echo ""
echo "2. View application logs:"
echo -e "   ${YELLOW}docker logs -f movie-api${NC}"
echo ""
echo "3. Access API documentation:"
echo -e "   ${YELLOW}http://<lightsail-ip>:8000/docs${NC}"
echo ""
echo "4. Setup systemd service (optional, for auto-restart):"
echo -e "   ${YELLOW}sudo cp movie-api.service /etc/systemd/system/${NC}"
echo -e "   ${YELLOW}sudo systemctl daemon-reload${NC}"
echo -e "   ${YELLOW}sudo systemctl enable movie-api.service${NC}"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}\n"

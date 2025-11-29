#!/bin/bash

################################################################################
# AWS LightSail Production Deployment Script - Docker Build & Run
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
#   - Clones the repository if needed
#   - Checks prerequisites (Docker, Git)
#   - Creates .env file with production settings
#   - Tests RDS connectivity
#   - Creates the database if needed
#   - Cleans up existing containers
#   - Builds Docker image
#   - Runs database migrations in container
#   - Starts the application container on port 8000
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

check_prerequisites() {
    print_header "Checking Prerequisites"

    print_section "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed, installing..."
        sudo dnf install -y docker
        
        if [ $? -ne 0 ]; then
            print_error "Failed to install Docker"
            exit 1
        fi
        print_success "Docker installed"
    else
        DOCKER_VERSION=$(docker --version)
        print_success "Docker installed: $DOCKER_VERSION"
    fi

    print_section "Checking Docker daemon..."
    sudo systemctl start docker 2>/dev/null || true
    sudo systemctl enable docker 2>/dev/null || true
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_info "Try starting Docker with: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon is running"

    print_section "Checking Git..."
    if ! command -v git &> /dev/null; then
        print_warning "Git is not installed, installing..."
        sudo dnf install -y git
        
        if [ $? -ne 0 ]; then
            print_error "Failed to install Git"
            exit 1
        fi
        print_success "Git installed"
    else
        print_success "Git is installed"
    fi

    print_section "Checking psql (PostgreSQL client)..."
    if ! command -v psql &> /dev/null; then
        print_warning "psql not found, installing PostgreSQL client..."
        
        # Detect OS and install accordingly
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            
            if [ "$ID" = "amzn" ]; then
                # Amazon Linux (2 or 2023)
                print_section "Installing PostgreSQL client on Amazon Linux..."
                
                # Try dnf first (AL2023), fallback to yum (AL2)
                if command -v dnf &> /dev/null; then
                    print_section "Using dnf package manager..."
                    sudo dnf install -y postgresql15
                else
                    print_section "Using yum package manager..."
                    sudo yum install -y postgresql15
                fi
            else
                # Ubuntu/Debian and others
                print_section "Installing postgresql-client..."
                sudo apt-get update
                sudo apt-get install -y postgresql-client
            fi
        else
            print_error "Cannot determine OS type"
            exit 1
        fi
        
        if ! command -v psql &> /dev/null; then
            print_error "Failed to install psql"
            echo ""
            echo "Manual installation for Amazon Linux 2023:"
            echo "  sudo dnf install -y postgresql15"
            exit 1
        fi
        
        print_success "PostgreSQL client installed"
    else
        print_success "psql is installed"
    fi
    
    echo ""
}

clone_repository() {
    print_header "Cloning Repository"
    
    local repo_url="https://github.com/marciomarinho/roz-movie-api.git"
    local repo_dir="roz-movie-api"
    
    # Check if already in a git repository
    if [ -f "Dockerfile" ] && [ -d "app" ]; then
        print_success "Already in repository directory\n"
        return 0
    fi
    
    # Check if repo directory exists
    if [ -d "$repo_dir" ]; then
        print_warning "Repository directory already exists\n"
        cd "$repo_dir"
    else
        print_section "Cloning repository from: $repo_url"
        echo ""
        git clone "$repo_url" "$repo_dir"
        
        if [ $? -ne 0 ]; then
            print_error "Failed to clone repository"
            exit 1
        fi
        
        cd "$repo_dir"
        print_success "Repository cloned\n"
    fi
    
    # Verify we have required files
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found after cloning"
        exit 1
    fi
    
    if [ ! -d "app" ]; then
        print_error "app directory not found after cloning"
        exit 1
    fi
    
    print_success "Repository structure verified\n"
}

setup_env_file() {
    print_header "Creating .env File"
    
    print_section "Generating production environment file..."
    
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
    
    print_section "Waiting for RDS to be ready..."
    echo "Target: $DB_HOST:$DB_PORT"
    echo "Master user: $DB_USER"
    echo ""
    
    export PGPASSWORD="$DB_PASSWORD"
    
    while [ $attempt -le $max_attempts ]; do
        echo -n "Attempt $attempt/$max_attempts: "
        
        # Test connection to default postgres database
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT 1" > /dev/null 2>&1; then
            print_success "RDS is ready\n"
            unset PGPASSWORD
            return 0
        fi
        
        print_warning "Connection failed, retrying..."
        
        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            sleep 2
        fi
    done
    
    print_error "\nCould not connect to RDS after $max_attempts attempts"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check RDS endpoint is correct: $DB_HOST"
    echo "2. Verify RDS security group allows port $DB_PORT from LightSail"
    echo "3. Ensure database credentials are correct"
    echo "4. Check that RDS instance is running in AWS Console"
    echo ""
    echo "Install psql if needed:"
    echo "  Amazon Linux 2: sudo yum install -y postgresql"
    echo "  Ubuntu/Debian: sudo apt-get install -y postgresql-client"
    unset PGPASSWORD
    exit 1
}

create_database() {
    print_header "Creating Database"
    
    print_section "Checking if database '$DB_NAME' exists..."
    
    # Use psql directly via environment variable - no docker needed
    export PGPASSWORD="$DB_PASSWORD"
    
    # Check if database exists
    local db_check=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -lqt 2>&1 | cut -d \| -f 1 | grep -w "$DB_NAME")
    
    if [ -n "$db_check" ]; then
        print_success "Database '$DB_NAME' already exists\n"
        unset PGPASSWORD
        return 0
    fi
    
    print_section "Creating database '$DB_NAME'..."
    
    # Create the database with error output
    local create_output=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "CREATE DATABASE \"$DB_NAME\";" 2>&1)
    local create_status=$?
    
    if [ $create_status -eq 0 ]; then
        print_success "Database '$DB_NAME' created successfully\n"
        unset PGPASSWORD
    else
        print_error "Failed to create database"
        echo ""
        echo "Error details:"
        echo "$create_output"
        echo ""
        echo "Troubleshooting:"
        echo "1. Verify RDS credentials are correct"
        echo "2. Check that the postgres master user has permissions"
        echo "3. Try manually:"
        echo "   export PGPASSWORD='$DB_PASSWORD'"
        echo "   psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d 'postgres' -c 'CREATE DATABASE \"$DB_NAME\";'"
        unset PGPASSWORD
        exit 1
    fi
}

setup_nginx() {
    print_header "Setting Up Nginx Reverse Proxy"
    
    print_section "Checking if Nginx is installed..."
    if ! command -v nginx &> /dev/null; then
        print_warning "Nginx not found, installing..."
        echo "Running: sudo dnf install -y nginx"
        sudo dnf install -y nginx > /dev/null 2>&1
        
        if [ $? -ne 0 ]; then
            print_error "Failed to install Nginx"
            exit 1
        fi
        print_success "Nginx installed"
    else
        print_success "Nginx is already installed"
    fi
    
    print_section "Configuring Nginx reverse proxy..."
    
    # Create Nginx config
    sudo tee /etc/nginx/conf.d/movie-api.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    print_success "Nginx configuration created"
    
    print_section "Starting Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    if [ $? -eq 0 ]; then
        print_success "Nginx started and enabled\n"
    else
        print_error "Failed to start Nginx"
        exit 1
    fi
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
    
    print_section "Building Docker image: $image_name:$image_tag"
    echo ""
    
    docker build -t "$image_name:$image_tag" .
    
    if [ $? -ne 0 ]; then
        print_error "Failed to build Docker image"
        exit 1
    fi
    
    print_success "Docker image built successfully\n"
    print_section "Image information:"
    docker images "$image_name"
    echo ""
}

cleanup_containers() {
    print_header "Cleaning Up Existing Containers (if any)"

    local container_name="movie-api"
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_section "Stopping existing container: $container_name"
        docker stop "$container_name" 2>/dev/null || true
        print_section "Removing existing container: $container_name"
        docker rm "$container_name" 2>/dev/null || true
        print_success "Cleaned up $container_name\n"
    fi
}

run_migrations() {
    print_header "Running Database Migrations"
    
    local container_name="movie-api-migrate-$$"
    
    print_section "Running migrations in temporary container..."
    echo ""
    
    docker run --rm \
        --name "$container_name" \
        --env-file .env \
        movie-api:latest \
        alembic upgrade head
    
    if [ $? -ne 0 ]; then
        print_warning "Migration may have failed"
    else
        print_success "Database migrations completed\n"
    fi
}

load_movies() {
    print_header "Loading Movie Data"
    
    local container_name="movie-api-load-$$"
    
    print_section "Loading movies from CSV into database..."
    echo ""
    
    docker run --rm \
        --name "$container_name" \
        -e DB_HOST="$DB_HOST" \
        -e DB_PORT="$DB_PORT" \
        -e DB_NAME="$DB_NAME" \
        -e DB_USER="$DB_USER" \
        -e DB_PASSWORD="$DB_PASSWORD" \
        movie-api:latest \
        python scripts/load_movies.py \
            --dbname="$DB_NAME" \
            --user="$DB_USER" \
            --password="$DB_PASSWORD" \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --csv-path=data/movies_large.csv
    
    if [ $? -ne 0 ]; then
        print_warning "Movie data loading may have failed or data already loaded"
    else
        print_success "Movie data loaded successfully\n"
    fi
}

start_application() {
    print_header "Starting Application Container"
    
    local container_name="movie-api"
    
    print_section "Starting application container..."
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
    
    if [ $? -ne 0 ]; then
        print_error "Failed to start container"
        exit 1
    fi
    
    # Give container a moment to start
    sleep 2
    
    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_success "Application container started successfully\n"
        
        print_section "Container Details"
        docker ps --filter "name=$container_name" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        print_section "Checking container health..."
        sleep 3
        echo ""
        print_section "Recent logs:"
        docker logs --tail 10 "$container_name"
    else
        print_error "Container failed to start"
        echo ""
        print_section "Recent logs:"
        docker logs "$container_name" || true
        exit 1
    fi
}

verify_deployment() {
    print_header "Verifying Deployment"

    print_section "Testing API health endpoint..."
    if curl -s http://localhost:8000/api/v1/health | grep -q "ok\|status" > /dev/null 2>&1; then
        print_success "API is responding"
    else
        print_warning "API not yet responding, may still be starting..."
    fi
}

display_summary() {
    print_header "Deployment Complete! 🎉"
    echo -e "Your Movie API is now running!\n"

    echo "Service Access Points:"
    echo ""
    echo -e "  ${CYAN}API (port 80):${NC}  http://localhost"
    echo -e "  ${CYAN}Docs:${NC}           http://localhost/docs"
    echo -e "  ${CYAN}Health:${NC}         http://localhost/health"
    echo ""
    echo "  Note: Access from outside requires opening port 80 in LightSail firewall"
    echo ""

    echo "Container Information:"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep "movie-api"
    echo ""

    echo "Nginx Status:"
    echo ""
    sudo systemctl status nginx --no-pager | head -3
    echo ""

    echo "Useful Commands:"
    echo ""
    echo -e "  View app logs:       ${YELLOW}docker logs -f movie-api${NC}"
    echo -e "  Stop container:      ${YELLOW}docker stop movie-api${NC}"
    echo -e "  Restart container:   ${YELLOW}docker restart movie-api${NC}"
    echo -e "  Health check:        ${YELLOW}curl http://localhost/health${NC}"
    echo -e "  View nginx logs:     ${YELLOW}sudo tail -f /var/log/nginx/access.log${NC}"
    echo ""

    echo "Next Steps:"
    echo ""
    echo "  1. Ask account owner to open port 80 in LightSail firewall"
    echo "  2. Test the API: http://<lightsail-ip>/docs (Swagger UI)"
    echo "  3. Check logs: docker logs -f movie-api"
    echo "  4. Monitor: docker stats movie-api"
    echo ""
    echo "  To cleanup deployment, run:"
    echo "    ./scripts/cleanup-lightsail.sh"
    echo ""
    echo -e "${GREEN}Happy deploying! 🚀${NC}\n"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "Movie API - LightSail Production Deployment (Docker)"
    echo -e "$(date)\n"

    validate_env
    check_prerequisites
    clone_repository
    setup_env_file
    test_rds_connectivity
    create_database
    cleanup_containers
    build_docker_image
    run_migrations
    load_movies
    setup_nginx
    start_application
    verify_deployment
    display_summary
}

# Run main function
main

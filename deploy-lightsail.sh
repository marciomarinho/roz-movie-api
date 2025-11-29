#!/bin/bash
"""
LightSail Production Deployment Script

This script deploys the Movie API to AWS LightSail with AWS Cognito and RDS.
It handles environment variable setup, database migrations, and application startup.

Usage:
    ./deploy-lightsail.sh

Environment Variables (required for production):
    DB_HOST              - RDS PostgreSQL endpoint
    DB_PORT              - RDS PostgreSQL port (default: 5432)
    DB_NAME              - Database name
    DB_USER              - Database master username
    DB_PASSWORD          - Database master password
    
    COGNITO_USER_POOL_ID - AWS Cognito User Pool ID
    COGNITO_REGION       - AWS region for Cognito (default: us-east-1)
    
    AUTH_PROVIDER        - 'cognito' for production
    AUTH_ENABLED         - 'true' to enable authentication

Example:
    export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
    export DB_PORT=5432
    export DB_NAME=movie_api
    export DB_USER=postgres
    export DB_PASSWORD=BananaGelada12
    export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
    export COGNITO_REGION=us-east-1
    export AUTH_PROVIDER=cognito
    export AUTH_ENABLED=true
    ./deploy-lightsail.sh
"""

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Movie API - LightSail Deployment${NC}"
echo -e "${BLUE}================================${NC}\n"

# Validate required environment variables
validate_env() {
    local required_vars=("DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD" "COGNITO_USER_POOL_ID" "COGNITO_REGION")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}✗ Error: $var environment variable not set${NC}"
            echo -e "${YELLOW}Please set all required environment variables before deploying.${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✓ All required environment variables are set${NC}\n"
}

# Create .env file with production settings
setup_env_file() {
    echo -e "${BLUE}Creating .env file with production settings...${NC}"
    
    cat > .env <<EOF
# Application
APP_NAME=Movie API
APP_VERSION=1.0.0

# Database (AWS RDS)
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

# Authentication - Cognito
AUTH_PROVIDER=${AUTH_PROVIDER:-cognito}
AUTH_ENABLED=${AUTH_ENABLED:-true}

# AWS Cognito Configuration
COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID}
COGNITO_REGION=${COGNITO_REGION:-us-east-1}

# Logging
LOG_LEVEL=${LOG_LEVEL:-INFO}
EOF
    
    echo -e "${GREEN}✓ .env file created${NC}\n"
}

# Install Python dependencies
install_dependencies() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    
    echo -e "${GREEN}✓ Dependencies installed${NC}\n"
}

# Run database migrations
run_migrations() {
    echo -e "${BLUE}Running database migrations...${NC}"
    
    source venv/bin/activate
    
    # Wait for RDS to be ready
    echo -e "${YELLOW}Waiting for RDS connection...${NC}"
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python3 -c "import psycopg2; psycopg2.connect(host='${DB_HOST}', port=${DB_PORT}, database='${DB_NAME}', user='${DB_USER}', password='${DB_PASSWORD}')" 2>/dev/null; then
            echo -e "${GREEN}✓ RDS is ready${NC}"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo -e "${RED}✗ Failed to connect to RDS after $max_attempts attempts${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: Waiting for RDS...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    # Run Alembic migrations
    alembic upgrade head
    
    echo -e "${GREEN}✓ Database migrations completed${NC}\n"
}

# Start the application
start_application() {
    echo -e "${BLUE}Starting FastAPI application...${NC}"
    
    source venv/bin/activate
    
    echo -e "${GREEN}✓ Application configuration:${NC}"
    echo -e "  Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    echo -e "  Auth Provider: ${AUTH_PROVIDER:-cognito}"
    echo -e "  Cognito Pool: ${COGNITO_USER_POOL_ID}"
    echo -e ""
    
    # Start Uvicorn server
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level ${LOG_LEVEL:-info}
}

# Main execution
main() {
    validate_env
    setup_env_file
    install_dependencies
    run_migrations
    start_application
}

# Run main function
main

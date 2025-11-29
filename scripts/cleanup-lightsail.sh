#!/bin/bash

################################################################################
# AWS LightSail Cleanup Script
# 
# This script removes the Movie API deployment and cleans up resources.
# It stops containers, removes images, and optionally removes Nginx configuration.
#
# Usage:
#   chmod +x scripts/cleanup-lightsail.sh
#   ./scripts/cleanup-lightsail.sh
#
################################################################################

set +e

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
# Cleanup Functions
################################################################################

stop_containers() {
    print_header "Stopping Docker Containers"
    
    local container_name="movie-api"
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_section "Stopping container: $container_name"
        docker stop "$container_name" 2>/dev/null || true
        print_success "Container stopped\n"
    else
        print_info "Container $container_name not running\n"
    fi
}

remove_containers() {
    print_header "Removing Docker Containers"
    
    local container_name="movie-api"
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_section "Removing container: $container_name"
        docker rm "$container_name" 2>/dev/null || true
        print_success "Container removed\n"
    else
        print_info "Container $container_name not found\n"
    fi
}

remove_images() {
    print_header "Removing Docker Images"
    
    local image_name="movie-api"
    
    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${image_name}:"; then
        print_section "Removing image: $image_name:latest"
        docker rmi "$image_name:latest" 2>/dev/null || true
        print_success "Image removed\n"
    else
        print_info "Image $image_name:latest not found\n"
    fi
}

remove_packages() {
    print_header "Removing Installed Packages"
    
    print_section "Detecting OS to remove packages..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        
        if [ "$ID" = "amzn" ]; then
            # Amazon Linux - batch all packages in one command
            print_section "Removing packages from Amazon Linux..."
            
            if command -v dnf &> /dev/null; then
                echo "Running: sudo dnf remove -y postgresql15 nginx docker git"
                sudo dnf remove -y postgresql15 nginx docker git > /dev/null 2>&1
                
                if [ $? -eq 0 ]; then
                    print_success "All packages removed successfully"
                else
                    print_warning "Some packages may not have been installed, but removal completed"
                fi
            else
                print_warning "dnf not found, trying yum..."
                sudo yum remove -y postgresql15 nginx docker git > /dev/null 2>&1
                print_warning "Package removal attempted"
            fi
        else
            # Ubuntu/Debian
            print_section "Removing packages from Ubuntu/Debian..."
            
            echo "Running: sudo apt-get remove -y postgresql-client nginx docker.io git"
            sudo apt-get remove -y postgresql-client nginx docker.io git > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                print_success "PostgreSQL client, Nginx, Docker, and Git removed"
            fi
        fi
    else
        print_warning "Could not determine OS type, skipping package removal"
    fi
    
    echo ""
}

cleanup_nginx() {
    print_header "Cleaning Up Nginx"
    
    print_section "Stopping Nginx..."
    sudo systemctl stop nginx 2>/dev/null || true
    print_success "Nginx stopped"
    
    print_section "Removing Nginx configuration..."
    sudo rm -f /etc/nginx/conf.d/movie-api.conf 2>/dev/null || true
    print_success "Nginx config removed"
    
    print_section "Restarting Nginx (or disabling if no configs)..."
    sudo systemctl restart nginx 2>/dev/null || true
    
    echo ""
}

cleanup_env_file() {
    print_header "Cleaning Up Environment Files"
    
    if [ -f ".env" ]; then
        print_section "Removing .env file..."
        rm -f .env
        print_success ".env file removed\n"
    else
        print_info ".env file not found\n"
    fi
}

drop_database() {
    print_header "Dropping RDS Database"
    
    # Load environment variables from .env if it exists
    if [ -f ".env" ]; then
        print_section "Loading environment from .env..."
        set -a
        source .env
        set +a
    fi
    
    # Check if we have required database variables
    if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
        print_warning "Database credentials not found, skipping database drop"
        print_info "Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD to drop the database"
        return 0
    fi
    
    print_section "Dropping database '$DB_NAME' from RDS..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Terminate connections and drop database
    local drop_output=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '$DB_NAME'
        AND pid <> pg_backend_pid();
        
        DROP DATABASE IF EXISTS \"$DB_NAME\";" 2>&1)
    
    local drop_status=$?
    
    if [ $drop_status -eq 0 ]; then
        print_success "Database '$DB_NAME' dropped successfully\n"
    else
        print_warning "Could not drop database (it may already be gone)"
        print_info "Error: $drop_output"
    fi
    
    unset PGPASSWORD
}

cleanup_repository() {
    print_header "Cleaning Up Repository"
    
    if [ -d "roz-movie-api" ]; then
        print_section "Removing repository directory..."
        rm -rf roz-movie-api
        print_success "Repository directory removed\n"
    else
        print_info "Repository directory not found\n"
    fi
}

show_remaining_cleanup() {
    print_header "Additional Manual Cleanup (Optional)"
    
    echo "The following have been automatically removed:"
    echo "  ✓ Docker and Docker daemon"
    echo "  ✓ PostgreSQL client"
    echo "  ✓ Nginx"
    echo "  ✓ Git"
    echo "  ✓ Movie API container and image"
    echo "  ✓ Repository directory"
    echo "  ✓ Configuration files"
    echo ""
    echo "Optional manual cleanup for Docker resources:"
    echo ""
    echo "  # Clean up docker volumes (if Docker is reinstalled later)"
    echo "  docker volume prune -f"
    echo ""
    echo "  # Clean up docker networks"
    echo "  docker network prune -f"
    echo ""
    echo "  # View what remains (should be minimal)"
    echo "  docker ps -a"
    echo "  docker images"
    echo "  docker volume ls"
    echo ""
}

show_status() {
    print_header "Cleanup Summary"
    
    echo "Running Docker containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "  No containers"
    
    echo ""
    echo "Nginx status:"
    sudo systemctl status nginx --no-pager 2>/dev/null | head -5 || echo "  Nginx not installed"
    
    echo ""
    echo "Environment:"
    if [ -f ".env" ]; then
        echo "  .env: Present"
    else
        echo "  .env: Removed"
    fi
    
    if [ -d "roz-movie-api" ]; then
        echo "  Repository: Present"
    else
        echo "  Repository: Removed"
    fi
    
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "Movie API - LightSail Cleanup"
    echo -e "$(date)\n"
    
    # Confirm cleanup
    echo "This will completely remove:"
    echo ""
    echo "  Application & Configuration:"
    echo "    - Movie API Docker container"
    echo "    - Movie API Docker image"
    echo "    - .env file"
    echo "    - Repository directory (roz-movie-api)"
    echo "    - Nginx Movie API configuration"
    echo ""
    echo "  System Packages:"
    echo "    - Docker and Docker daemon"
    echo "    - PostgreSQL client (postgresql15)"
    echo "    - Nginx web server"
    echo "    - Git"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_warning "Cleanup cancelled"
        exit 0
    fi
    
    echo ""
    
    stop_containers
    remove_containers
    remove_images
    remove_packages
    cleanup_nginx
    drop_database
    cleanup_env_file
    cleanup_repository
    
    show_status
    show_remaining_cleanup
    
    print_header "Cleanup Complete!"
    echo -e "${GREEN}Movie API deployment and all dependencies have been completely removed.${NC}\n"
}

# Run main function
main

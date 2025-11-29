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
            # Amazon Linux
            print_section "Removing packages from Amazon Linux..."
            
            # Remove PostgreSQL client
            if command -v dnf &> /dev/null; then
                echo "Running: sudo dnf remove -y postgresql15"
                sudo dnf remove -y postgresql15 > /dev/null 2>&1
                if [ $? -eq 0 ]; then
                    print_success "PostgreSQL client removed"
                fi
            fi
            
            # Remove Nginx
            if command -v dnf &> /dev/null; then
                echo "Running: sudo dnf remove -y nginx"
                sudo dnf remove -y nginx > /dev/null 2>&1
                if [ $? -eq 0 ]; then
                    print_success "Nginx removed"
                fi
            fi
        else
            # Ubuntu/Debian
            print_section "Removing packages from Ubuntu/Debian..."
            
            echo "Running: sudo apt-get remove -y postgresql-client nginx"
            sudo apt-get remove -y postgresql-client nginx > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                print_success "PostgreSQL client and Nginx removed"
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
    
    echo "All major dependencies have been removed. Additional optional cleanup:"
    echo ""
    echo "  # Clean up docker volumes"
    echo "  docker volume prune -f"
    echo ""
    echo "  # Clean up dangling docker images"
    echo "  docker image prune -f"
    echo ""
    echo "  # Remove all stopped containers"
    echo "  docker container prune -f"
    echo ""
    echo "  # View remaining docker resources"
    echo "  docker ps -a"
    echo "  docker images"
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
    echo "This will remove:"
    echo "  - Movie API Docker container"
    echo "  - Movie API Docker image"
    echo "  - .env file"
    echo "  - Repository directory (roz-movie-api)"
    echo "  - Nginx Movie API configuration"
    echo "  - PostgreSQL client (postgresql15)"
    echo "  - Nginx web server"
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
    cleanup_env_file
    cleanup_repository
    
    show_status
    show_remaining_cleanup
    
    print_header "Cleanup Complete!"
    echo -e "${GREEN}Movie API deployment has been completely cleaned up.${NC}\n"
}

# Run main function
main

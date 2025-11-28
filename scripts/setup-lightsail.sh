#!/bin/bash

################################################################################
# AWS LightSail Setup Script
# 
# This script automates the setup of an AWS LightSail instance (Amazon Linux 2)
# for deploying the Movie API application.
#
# Usage: 
#   curl -fsSL https://raw.githubusercontent.com/marciomarinho/roz-movie-api/main/scripts/setup-lightsail.sh | bash
#   OR
#   bash setup-lightsail.sh
#
# What it does:
#   - Updates system packages
#   - Installs essential development tools
#   - Installs Docker
#   - Installs Docker Compose
#   - Configures Docker permissions
#   - Clones the repository
#   - Displays next steps
#
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}\n"
}

print_error() {
    echo -e "${RED}✗ Error: $1${NC}\n"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}\n"
}

# Check if running as ec2-user
if [ "$USER" != "ec2-user" ] && [ "$USER" != "root" ]; then
    print_warning "This script should be run as ec2-user or root"
fi

# Start setup
print_header "AWS LightSail Setup - Movie API"

# Step 1: Update system
print_header "Step 1: Updating System Packages"
echo "Running: sudo yum update -y"
sudo yum update -y > /dev/null 2>&1 || print_error "Failed to update system"
print_success "System packages updated"

# Step 2: Install development tools
print_header "Step 2: Installing Development Tools"
echo "Installing: git curl wget gcc make python3 python3-pip python3-devel"

PACKAGES="git curl wget gcc make python3 python3-pip python3-devel"
for pkg in $PACKAGES; do
    echo -n "  Installing $pkg... "
    sudo yum install -y $pkg > /dev/null 2>&1 || print_error "Failed to install $pkg"
    echo -e "${GREEN}done${NC}"
done

print_success "All development tools installed"

# Verify installations
print_header "Step 3: Verifying Installations"

echo "Checking versions:"
echo -n "  Git: "
git --version
echo -n "  Python: "
python3 --version
echo -n "  pip: "
pip3 --version
echo -n "  Make: "
make --version
echo ""
print_success "All tools verified"

# Step 3: Install Docker
print_header "Step 4: Installing Docker"
echo "Installing Docker from amazon-linux-extras..."
sudo amazon-linux-extras install -y docker > /dev/null 2>&1 || print_error "Failed to install Docker"

# Start Docker daemon
echo "Starting Docker daemon..."
sudo systemctl start docker > /dev/null 2>&1 || print_error "Failed to start Docker"
echo "Enabling Docker to start on boot..."
sudo systemctl enable docker > /dev/null 2>&1 || print_error "Failed to enable Docker"

# Add user to docker group
echo "Adding ec2-user to docker group..."
sudo usermod -aG docker ec2-user > /dev/null 2>&1 || print_error "Failed to add user to docker group"

print_success "Docker installed and configured"

# Verify Docker
print_header "Step 5: Verifying Docker"
echo "Docker version:"
sudo docker --version || print_error "Docker verification failed"

# Note about group changes
print_warning "You need to log out and log back in for docker group permissions to take effect"
print_info "Run: exit"
print_info "Then reconnect: ssh -i ~/marcio.pem ec2-user@52.62.14.166"

# Step 4: Install Docker Compose
print_header "Step 6: Installing Docker Compose"
echo "Downloading Docker Compose..."

DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)"
echo "URL: $DOCKER_COMPOSE_URL"

sudo curl -L "$DOCKER_COMPOSE_URL" -o /usr/local/bin/docker-compose > /dev/null 2>&1 || print_error "Failed to download Docker Compose"

echo "Setting permissions..."
sudo chmod +x /usr/local/bin/docker-compose || print_error "Failed to set permissions"

print_success "Docker Compose installed"

# Verify Docker Compose
print_header "Step 7: Verifying Docker Compose"
echo "Docker Compose version:"
/usr/local/bin/docker-compose --version || print_error "Docker Compose verification failed"

# Clone repository
print_header "Step 8: Cloning Repository"

REPO_URL="${1:-https://github.com/marciomarinho/roz-movie-api.git}"
REPO_DIR="${HOME}/apps/movie-api"

echo "Repository URL: $REPO_URL"
echo "Target directory: $REPO_DIR"

mkdir -p ~/apps || print_error "Failed to create ~/apps directory"
cd ~/apps

if [ -d "movie-api" ]; then
    print_warning "movie-api directory already exists, skipping clone"
else
    echo "Cloning repository..."
    git clone "$REPO_URL" movie-api > /dev/null 2>&1 || print_error "Failed to clone repository"
    print_success "Repository cloned to $REPO_DIR"
fi

# Verify repository structure
print_header "Step 9: Verifying Repository Structure"

cd "$REPO_DIR"

echo "Checking required files:"
REQUIRED_FILES=("docker-compose.yml" "Dockerfile" "Makefile" "app" "tests")

for file in "${REQUIRED_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        print_warning "Missing: $file"
    fi
done

print_success "Repository structure verified"

# Summary
print_header "Setup Complete! 🎉"

echo "You are now ready to deploy the Movie API!"
echo ""
echo "Next steps:"
echo ""
echo "1. Log out and back in for Docker group permissions:"
echo -e "   ${YELLOW}exit${NC}"
echo ""
echo "2. Reconnect to your instance:"
echo -e "   ${YELLOW}ssh -i ~/marcio.pem ec2-user@52.62.14.166${NC}"
echo ""
echo "3. Navigate to the project directory:"
echo -e "   ${YELLOW}cd ~/apps/movie-api${NC}"
echo ""
echo "4. Choose your deployment method:"
echo ""
echo -e "   ${BLUE}Option A: Using Docker Compose (Recommended)${NC}"
echo -e "   ${YELLOW}make setup${NC}"
echo ""
echo -e "   ${BLUE}Option B: Manual Docker Container Management${NC}"
echo -e "   See DEPLOYMENT_LIGHTSAIL.md for 'Alternative' section"
echo ""
echo "5. Verify the deployment:"
echo -e "   ${YELLOW}docker-compose ps${NC} (for Option A)"
echo -e "   ${YELLOW}docker ps${NC} (for Option B)"
echo ""
echo "6. Test the API:"
echo -e "   ${YELLOW}curl http://localhost:8000/health${NC}"
echo ""
echo "For detailed instructions, see: DEPLOYMENT_LIGHTSAIL.md"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}\n"

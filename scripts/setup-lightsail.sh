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

set +e  # Don't exit on error

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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Start setup
print_header "AWS LightSail Setup - Movie API"

# Step 1: Update system
print_header "Step 1: Updating System Packages"
echo "Running: sudo yum update -y"
sudo yum update -y 2>&1 | tail -5
print_success "System packages updated\n"

# Step 2: Install development tools
print_header "Step 2: Installing Development Tools"
echo "Installing required packages..."
echo "Packages: git, wget, gcc, make, python3, python3-pip, python3-devel"
echo ""

# Use --allowerasing to resolve curl conflicts on AL2023
sudo yum install -y --allowerasing git wget gcc make python3 python3-pip python3-devel 2>&1 | tail -10

print_success "Package installation completed\n"

# Step 3: Verify critical packages
print_header "Step 3: Verifying Critical Packages"

echo "Checking installed packages:"
git --version && echo "" || print_warning "git not found"
python3 --version && echo "" || print_warning "python3 not found"
which make > /dev/null && echo "✓ make is available" || print_warning "make not found"

print_success "Package verification completed\n"

# Step 4: Install Docker
print_header "Step 4: Installing Docker"
echo "Installing Docker..."

# For Amazon Linux 2023, use dnf
if command -v dnf &> /dev/null; then
    echo "Using dnf to install Docker..."
    sudo dnf install -y docker 2>&1 | tail -10
else
    # Fallback to yum
    echo "Using yum to install Docker..."
    sudo yum install -y docker 2>&1 | tail -10
fi

echo "Starting Docker daemon..."
sudo systemctl start docker 2>&1 | tail -2
sudo systemctl enable docker 2>&1 | tail -2

echo "Adding ec2-user to docker group..."
sudo usermod -aG docker ec2-user

print_success "Docker installed and configured\n"

# Step 5: Verify Docker
print_header "Step 5: Verifying Docker"
docker --version || sudo docker --version
print_warning "You need to log out and log back in for docker group permissions\n"

# Step 6: Install Docker Compose
print_header "Step 6: Installing Docker Compose"
echo "Downloading Docker Compose..."

DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)"
sudo curl -L "$DOCKER_COMPOSE_URL" -o /usr/local/bin/docker-compose 2>&1 | grep -E "100|^\s*$" || true

if [ -f /usr/local/bin/docker-compose ]; then
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed\n"
else
    print_warning "Docker Compose installation may have failed\n"
fi

# Step 7: Verify Docker Compose
print_header "Step 7: Verifying Docker Compose"
/usr/local/bin/docker-compose --version 2>/dev/null || docker-compose --version 2>/dev/null || print_warning "Docker Compose not yet available\n"

# Step 8: Clone repository
print_header "Step 8: Cloning Repository"

REPO_URL="${1:-https://github.com/marciomarinho/roz-movie-api.git}"
REPO_DIR="${HOME}/apps/movie-api"

echo "Repository URL: $REPO_URL"
echo "Target directory: $REPO_DIR"
echo ""

mkdir -p ~/apps
cd ~/apps

if [ -d "movie-api" ]; then
    print_warning "movie-api directory already exists\n"
else
    echo "Cloning repository..."
    git clone "$REPO_URL" movie-api 2>&1 | tail -5
    print_success "Repository cloned\n"
fi

# Step 9: Verify repository
print_header "Step 9: Verifying Repository Structure"

cd "$REPO_DIR" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Checking required files:"
    for file in docker-compose.yml Dockerfile Makefile app tests; do
        if [ -e "$file" ]; then
            echo "  ✓ $file"
        else
            echo "  ✗ $file (missing)"
        fi
    done
    echo ""
    print_success "Repository verified\n"
else
    print_warning "Could not verify repository\n"
fi

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
echo "5. For detailed instructions, see: DEPLOYMENT_LIGHTSAIL.md"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}\n"


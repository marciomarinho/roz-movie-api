#!/bin/bash

################################################################################
# RDS Connectivity Test
# 
# This script tests if you can connect to your AWS RDS instance
# It doesn't require psql to be installed - uses Docker PostgreSQL image
#
# Usage:
#   chmod +x scripts/test-rds.sh
#   ./scripts/test-rds.sh
#
################################################################################

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

print_header "RDS Connectivity Test"

# Check if environment variables are set
if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    print_error "Missing required environment variables!"
    echo ""
    echo "Set them before running this script:"
    echo "  export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com"
    echo "  export DB_PORT=5432"
    echo "  export DB_USER=postgres"
    echo "  export DB_PASSWORD=your-password"
    exit 1
fi

# Set defaults
DB_PORT=${DB_PORT:-5432}

print_info "Testing connection to RDS..."
echo ""
echo "Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo ""

# First, test DNS resolution
print_info "Testing DNS resolution..."
if docker run --rm alpine nslookup "$DB_HOST" > /dev/null 2>&1; then
    print_success "DNS resolved successfully"
else
    print_warning "DNS resolution failed (may still work)"
fi

# Test basic connectivity with netcat
print_info "Testing basic port connectivity...\n"
if docker run --rm alpine sh -c "nc -zv -w 3 $DB_HOST $DB_PORT 2>&1 | grep -q 'open\|succeeded'" 2>/dev/null; then
    print_success "Port $DB_PORT is reachable\n"
else
    print_warning "Port $DB_PORT may not be reachable - checking security groups...\n"
fi

echo ""

# Method 1: Try using Docker (most reliable)
if command -v docker &> /dev/null; then
    print_info "Docker found, using docker for connection test...\n"
    
    if docker run --rm --network host \
        -e PGPASSWORD="$DB_PASSWORD" \
        postgres:15-alpine \
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT version();" 2>&1; then
        
        print_success "Connected to RDS successfully!\n"
        
        print_header "Server Information"
        docker run --rm --network host \
            -e PGPASSWORD="$DB_PASSWORD" \
            postgres:15-alpine \
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT version();"
        
        echo ""
        
        print_header "Listing Databases"
        docker run --rm --network host \
            -e PGPASSWORD="$DB_PASSWORD" \
            postgres:15-alpine \
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -l
        
        echo ""
        exit 0
    else
        print_error "Failed to connect to RDS\n"
        
        print_header "Troubleshooting"
        echo "The connection was refused. This is usually caused by:"
        echo ""
        echo "1. Security Group Issue (MOST COMMON):"
        echo "   - Go to AWS Console → RDS → database-1"
        echo "   - Click 'Security group rules' tab"
        echo "   - Verify there's an inbound rule for PostgreSQL (port 5432)"
        echo "   - Source should include your IP: $(curl -s https://checkip.amazonaws.com 2>/dev/null || echo 'YOUR_IP')"
        echo ""
        echo "2. RDS Not Running:"
        echo "   - Go to AWS Console → RDS → database-1"
        echo "   - Check Status column - should say 'available'"
        echo ""
        echo "3. Wrong Endpoint:"
        echo "   - Verify: $DB_HOST"
        echo "   - Check AWS Console for correct endpoint"
        echo ""
        echo "4. RDS Not Publicly Accessible:"
        echo "   - Go to AWS Console → RDS → database-1 → Connectivity & security"
        echo "   - 'Publicly accessible' should be 'Yes'"
        echo ""
        echo "ACTION NEEDED:"
        echo "  1. Go to AWS Console"
        echo "  2. RDS → Databases → database-1"
        echo "  3. Scroll to 'Security' section"
        echo "  4. Click the security group: sg-0105f1b2cfd95b805"
        echo "  5. Add/edit inbound rule:"
        echo "     Type: PostgreSQL (5432)"
        echo "     Source: Your IP ($(curl -s https://checkip.amazonaws.com 2>/dev/null || echo 'YOUR_IP'))"
        echo ""
        exit 1
    fi
fi

# Method 2: Try using psql directly if installed
if command -v psql &> /dev/null; then
    print_info "psql found, using psql for connection test...\n"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT version();"; then
        print_success "Connected to RDS successfully!\n"
        
        print_header "Listing Databases"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -l
        
        echo ""
        unset PGPASSWORD
        exit 0
    else
        print_error "Failed to connect to RDS\n"
        unset PGPASSWORD
        exit 1
    fi
fi

# Method 3: Try using nc/telnet to just test connectivity
print_warning "Neither docker nor psql found. Attempting basic network test...\n"

if command -v nc &> /dev/null; then
    if nc -zv -w 5 "$DB_HOST" "$DB_PORT" 2>&1 | grep -q "succeeded\|open"; then
        print_success "Port $DB_PORT on $DB_HOST is reachable\n"
        echo "However, full database connection test requires psql or Docker."
        echo "Install either:"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        echo "  - PostgreSQL client: brew install postgresql (Mac) or sudo apt-get install postgresql-client (Ubuntu)"
        exit 0
    else
        print_error "Cannot reach $DB_HOST:$DB_PORT\n"
        exit 1
    fi
fi

print_error "Cannot find docker, psql, or nc to test connectivity"
echo ""
echo "Install one of the following:"
echo "  - Docker: https://docs.docker.com/get-docker/"
echo "  - PostgreSQL client: brew install postgresql (Mac) or sudo apt-get install postgresql-client (Ubuntu)"
exit 1

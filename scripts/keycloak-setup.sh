#!/bin/bash
################################################################################
# Keycloak Setup Script (Simplified)
# 
# This script configures Keycloak with:
# - A realm (movie-realm)
# - A confidential client (movie-api-client)
# - A test user (movieuser)
#
# Uses direct HTTP requests (no kcadm.sh dependency)
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-movie-realm}"
KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-movie-api-client}"
KEYCLOAK_TEST_USERNAME="${KEYCLOAK_TEST_USERNAME:-movieuser}"
KEYCLOAK_TEST_PASSWORD="${KEYCLOAK_TEST_PASSWORD:-moviepassword}"

# Logging functions
log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1"
}

# Get admin access token
get_admin_token() {
    log_info "Getting admin access token..."
    
    local response=$(curl -s -X POST \
        "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "client_id=admin-cli" \
        -d "username=${KEYCLOAK_ADMIN}" \
        -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
        -d "grant_type=password")
    
    local token=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 || true)
    
    if [ -z "$token" ]; then
        log_error "Failed to get admin token"
        echo "$response"
        return 1
    fi
    
    echo "$token"
    return 0
}

# Wait for Keycloak to be ready
wait_for_keycloak() {
    log_info "Waiting for Keycloak to be ready at ${KEYCLOAK_URL}..."
    
    local max_attempts=120
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Try to get token to verify Keycloak is actually ready
        local response=$(curl -s -X POST \
            "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "client_id=admin-cli" \
            -d "username=admin" \
            -d "password=admin" \
            -d "grant_type=password" 2>&1)
        
        if echo "$response" | grep -q "access_token"; then
            log_success "Keycloak is ready!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts..."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "Keycloak did not become ready after $max_attempts attempts"
    log_error "Last response: $response"
    return 1
}

# Create realm
create_realm() {
    local admin_token="$1"
    
    log_info "Creating realm: ${KEYCLOAK_REALM}..."
    
    local response=$(curl -s -X POST \
        "${KEYCLOAK_URL}/admin/realms" \
        -H "Authorization: Bearer ${admin_token}" \
        -H "Content-Type: application/json" \
        -d "{\"realm\":\"${KEYCLOAK_REALM}\",\"enabled\":true}")
    
    # Check if realm was created or already exists
    if echo "$response" | grep -q "Conflict"; then
        log_warning "Realm ${KEYCLOAK_REALM} already exists"
        return 0
    fi
    
    if echo "$response" | grep -q "error"; then
        log_error "Failed to create realm: $response"
        return 1
    fi
    
    log_success "Realm ${KEYCLOAK_REALM} created"
    return 0
}

# Create client
create_client() {
    local admin_token="$1"
    
    log_info "Creating confidential client: ${KEYCLOAK_CLIENT_ID}..."
    
    # Create client
    local create_response=$(curl -s -X POST \
        "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients" \
        -H "Authorization: Bearer ${admin_token}" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\":\"${KEYCLOAK_CLIENT_ID}\",
            \"protocol\":\"openid-connect\",
            \"publicClient\":false,
            \"serviceAccountsEnabled\":true,
            \"standardFlowEnabled\":true,
            \"directAccessGrantsEnabled\":true,
            \"redirectUris\":[\"http://localhost:8000/*\",\"http://app:8000/*\"]
        }")
    
    # Check if client was created
    if echo "$create_response" | grep -q "error"; then
        # Try to get existing client
        log_warning "Client may already exist, attempting to retrieve..."
        local client_list=$(curl -s -X GET \
            "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients?clientId=${KEYCLOAK_CLIENT_ID}" \
            -H "Authorization: Bearer ${admin_token}")
        
        local client_id=$(echo "$client_list" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
        if [ -z "$client_id" ]; then
            log_error "Failed to create client: $create_response"
            return 1
        fi
        echo "$client_id"
        return 0
    fi
    
    # Extract client ID from response
    local client_id=$(echo "$create_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
    
    if [ -z "$client_id" ]; then
        log_error "Failed to extract client ID from response"
        return 1
    fi
    
    log_success "Client ${KEYCLOAK_CLIENT_ID} created with ID: ${client_id}"
    echo "$client_id"
}

# Get client secret
get_client_secret() {
    local admin_token="$1"
    local client_id="$2"
    
    log_info "Getting client secret..."
    
    local response=$(curl -s -X GET \
        "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients/${client_id}/client-secret" \
        -H "Authorization: Bearer ${admin_token}")
    
    local secret=$(echo "$response" | grep -o '"value":"[^"]*"' | cut -d'"' -f4 || true)
    
    if [ -z "$secret" ]; then
        log_error "Failed to get client secret: $response"
        return 1
    fi
    
    log_success "Client secret retrieved"
    echo "$secret"
}

# Create test user
create_test_user() {
    local admin_token="$1"
    
    log_info "Creating test user: ${KEYCLOAK_TEST_USERNAME}..."
    
    # Create user
    local create_response=$(curl -s -X POST \
        "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users" \
        -H "Authorization: Bearer ${admin_token}" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\":\"${KEYCLOAK_TEST_USERNAME}\",
            \"enabled\":true,
            \"credentials\":[{\"type\":\"password\",\"value\":\"${KEYCLOAK_TEST_PASSWORD}\",\"temporary\":false}]
        }")
    
    # Check response
    if echo "$create_response" | grep -q "Conflict"; then
        log_warning "User ${KEYCLOAK_TEST_USERNAME} already exists"
        return 0
    fi
    
    if echo "$create_response" | grep -q "error"; then
        log_error "Failed to create user: $create_response"
        return 1
    fi
    
    log_success "User ${KEYCLOAK_TEST_USERNAME} created"
    return 0
}

# Main execution
main() {
    log_info "=========================================="
    log_info "  Keycloak Setup Script"
    log_info "=========================================="
    log_info ""
    log_info "Configuration:"
    log_info "  Keycloak URL: ${KEYCLOAK_URL}"
    log_info "  Realm: ${KEYCLOAK_REALM}"
    log_info "  Client ID: ${KEYCLOAK_CLIENT_ID}"
    log_info "  Test User: ${KEYCLOAK_TEST_USERNAME}"
    log_info ""
    
    # Execute setup steps
    wait_for_keycloak || exit 1
    local admin_token=$(get_admin_token) || exit 1
    create_realm "$admin_token" || exit 1
    local client_id=$(create_client "$admin_token") || exit 1
    local client_secret=$(get_client_secret "$admin_token" "$client_id") || exit 1
    create_test_user "$admin_token" || exit 1
    
    # Print summary
    log_info ""
    log_success "=========================================="
    log_success "  Keycloak Setup Complete!"
    log_success "=========================================="
    log_success ""
    log_info "Configuration Summary:"
    log_info "  Realm: ${KEYCLOAK_REALM}"
    log_info "  Client ID: ${KEYCLOAK_CLIENT_ID}"
    log_info "  Client Secret: ${client_secret}"
    log_info "  Test User: ${KEYCLOAK_TEST_USERNAME}"
    log_info "  Test Password: ${KEYCLOAK_TEST_PASSWORD}"
    log_info ""
    log_info "Token Endpoint:"
    log_info "  ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token"
    log_info ""
    log_info "To get a token, run:"
    log_info "  curl -X POST \"${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token\" \\"
    log_info "    -H \"Content-Type: application/x-www-form-urlencoded\" \\"
    log_info "    -d \"client_id=${KEYCLOAK_CLIENT_ID}\" \\"
    log_info "    -d \"client_secret=${client_secret}\" \\"
    log_info "    -d \"grant_type=password\" \\"
    log_info "    -d \"username=${KEYCLOAK_TEST_USERNAME}\" \\"
    log_info "    -d \"password=${KEYCLOAK_TEST_PASSWORD}\""
    log_info ""
}

# Run main function
main
#!/usr/bin/env python3
"""
Keycloak Setup Script - Configure realm, client, and user
"""

import requests
import time
import sys
import os

# Configuration from environment variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_ADMIN = os.getenv("KEYCLOAK_ADMIN", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "movie-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "movie-api-client")
KEYCLOAK_TEST_USERNAME = os.getenv("KEYCLOAK_TEST_USERNAME", "movieuser")
KEYCLOAK_TEST_PASSWORD = os.getenv("KEYCLOAK_TEST_PASSWORD", "moviepassword")

# Colors
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def log_info(msg):
    print(f"{BLUE}[INFO]{RESET} {msg}")


def log_success(msg):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")


def log_warning(msg):
    print(f"{YELLOW}[WARNING]{RESET} {msg}")


def log_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}")


def wait_for_keycloak():
    """Wait for Keycloak to be ready"""
    log_info(f"Waiting for Keycloak to be ready at {KEYCLOAK_URL}...")
    max_attempts = 180
    for attempt in range(1, max_attempts + 1):
        try:
            # Try to get admin token endpoint which indicates Keycloak is ready
            response = requests.post(
                f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": "admin-cli",
                    "username": KEYCLOAK_ADMIN,
                    "password": KEYCLOAK_ADMIN_PASSWORD,
                    "grant_type": "password"
                },
                timeout=5
            )
            # If we get any response from token endpoint, Keycloak is ready
            if response.status_code in [200, 400, 401, 403]:
                log_success("Keycloak is ready!")
                return True
        except Exception as e:
            pass
        
        if attempt % 10 == 0:
            log_info(f"Attempt {attempt}/{max_attempts}...")
        time.sleep(1)
    
    log_error(f"Keycloak did not become ready after {max_attempts} attempts")
    return False


def get_admin_token():
    """Get admin access token"""
    log_info("Getting admin access token...")
    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": "admin-cli",
                "username": KEYCLOAK_ADMIN,
                "password": KEYCLOAK_ADMIN_PASSWORD,
                "grant_type": "password"
            }
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            log_success("Got admin token")
            return token
        else:
            log_error(f"Failed to get token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        log_error(f"Error getting token: {e}")
        return None


def create_realm(token):
    """Create realm"""
    log_info(f"Creating realm: {KEYCLOAK_REALM}...")
    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/admin/realms",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "realm": KEYCLOAK_REALM,
                "enabled": True
            }
        )
        if response.status_code in [201, 409]:  # 201 = created, 409 = conflict (already exists)
            log_success(f"Realm {KEYCLOAK_REALM} created/exists")
            return True
        else:
            log_error(f"Failed to create realm: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_error(f"Error creating realm: {e}")
        return False


def create_client(token):
    """Create confidential OAuth client"""
    log_info(f"Creating client: {KEYCLOAK_CLIENT_ID}...")
    try:
        # First, check if client already exists
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            clients = response.json()
            for client in clients:
                if client.get("clientId") == KEYCLOAK_CLIENT_ID:
                    client_id = client.get("id")
                    log_warning(f"Client {KEYCLOAK_CLIENT_ID} already exists with ID: {client_id}")
                    return client_id
        
        # Client doesn't exist, create new one
        response = requests.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "clientId": KEYCLOAK_CLIENT_ID,
                "protocol": "openid-connect",
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": True,
                "redirectUris": [
                    "http://localhost:8000/*",
                    "http://app:8000/*"
                ]
            }
        )
        
        if response.status_code == 201:
            client_data = response.json()
            client_id = client_data.get("id")
            log_success(f"Client {KEYCLOAK_CLIENT_ID} created with ID: {client_id}")
            return client_id
        else:
            log_error(f"Failed to create client: {response.status_code}")
            if response.text:
                log_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        log_error(f"Error creating client: {e}")
        return None


def get_client_secret(token, client_id):
    """Get client secret"""
    log_info("Getting client secret...")
    try:
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_id}/client-secret",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            secret_data = response.json()
            secret = secret_data.get("value")
            log_success("Client secret retrieved")
            return secret
        else:
            log_error(f"Failed to get secret: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        log_error(f"Error getting secret: {e}")
        return None


def create_test_user(token):
    """Create test user with all required attributes"""
    log_info(f"Creating test user: {KEYCLOAK_TEST_USERNAME}...")
    try:
        # First, try to create the user with full attributes
        response = requests.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "username": KEYCLOAK_TEST_USERNAME,
                "email": f"{KEYCLOAK_TEST_USERNAME}@example.com",
                "emailVerified": True,
                "enabled": True,
                "firstName": "Test",
                "lastName": "User",
                "credentials": [
                    {
                        "type": "password",
                        "value": KEYCLOAK_TEST_PASSWORD,
                        "temporary": False
                    }
                ],
                "requiredActions": []
            }
        )
        
        user_id = None
        
        if response.status_code == 201:
            log_success(f"User {KEYCLOAK_TEST_USERNAME} created")
            # Extract user ID from Location header
            location = response.headers.get("Location", "")
            if location:
                user_id = location.split("/")[-1]
            else:
                # Fallback: retrieve the user
                response = requests.get(
                    f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    users = response.json()
                    user = next((u for u in users if u["username"] == KEYCLOAK_TEST_USERNAME), None)
                    if user:
                        user_id = user["id"]
        elif response.status_code == 409:
            log_warning(f"User {KEYCLOAK_TEST_USERNAME} already exists, retrieving...")
            # Get existing user
            response = requests.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                users = response.json()
                user = next((u for u in users if u["username"] == KEYCLOAK_TEST_USERNAME), None)
                if user:
                    user_id = user["id"]
                    log_success(f"Found existing user: {KEYCLOAK_TEST_USERNAME}")
                    # Update user to ensure all attributes are set
                    log_info("Updating user attributes...")
                    response = requests.put(
                        f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "email": f"{KEYCLOAK_TEST_USERNAME}@example.com",
                            "emailVerified": True,
                            "enabled": True,
                            "firstName": "Test",
                            "lastName": "User",
                            "requiredActions": []
                        }
                    )
                    if response.status_code == 204:
                        log_success("User attributes updated")
                    # Reset password for existing user
                    log_info("Resetting password...")
                    response = requests.put(
                        f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/reset-password",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "type": "password",
                            "value": KEYCLOAK_TEST_PASSWORD,
                            "temporary": False
                        }
                    )
                    if response.status_code == 204:
                        log_success(f"Password reset for {KEYCLOAK_TEST_USERNAME}")
                        return True
                    else:
                        log_error(f"Failed to reset password: {response.status_code}")
                        return False
        else:
            log_error(f"Failed to create user: {response.status_code} - {response.text}")
            return False
        
        if not user_id:
            log_error("Could not determine user ID")
            return False
        
        # For newly created user, verify all attributes are set
        log_info("Verifying user is fully set up...")
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            user = response.json()
            log_success(f"User {KEYCLOAK_TEST_USERNAME} fully initialized:")
            log_info(f"  - Username: {user.get('username')}")
            log_info(f"  - Email: {user.get('email')}")
            log_info(f"  - First Name: {user.get('firstName')}")
            log_info(f"  - Last Name: {user.get('lastName')}")
            log_info(f"  - Email Verified: {user.get('emailVerified')}")
            log_info(f"  - Enabled: {user.get('enabled')}")
            log_info(f"  - Required Actions: {user.get('requiredActions', [])}")
            return True
        else:
            log_error(f"Failed to verify user: {response.status_code}")
            return False
            
    except Exception as e:
        log_error(f"Error creating user: {e}")
        return False


def main():
    print(f"{BLUE}=========================================={RESET}")
    print(f"{BLUE}  Keycloak Setup Script{RESET}")
    print(f"{BLUE}=========================================={RESET}")
    print()
    log_info("Configuration:")
    log_info(f"  Keycloak URL: {KEYCLOAK_URL}")
    log_info(f"  Realm: {KEYCLOAK_REALM}")
    log_info(f"  Client ID: {KEYCLOAK_CLIENT_ID}")
    log_info(f"  Test User: {KEYCLOAK_TEST_USERNAME}")
    print()
    
    # Wait for Keycloak
    if not wait_for_keycloak():
        sys.exit(1)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        sys.exit(1)
    
    # Create realm
    if not create_realm(token):
        sys.exit(1)
    
    # Create client
    client_id = create_client(token)
    if not client_id:
        sys.exit(1)
    
    # Get client secret
    secret = get_client_secret(token, client_id)
    if not secret:
        sys.exit(1)
    
    # Create test user
    if not create_test_user(token):
        sys.exit(1)
    
    # Print summary
    print()
    print(f"{GREEN}=========================================={RESET}")
    print(f"{GREEN}  Keycloak Setup Complete!{RESET}")
    print(f"{GREEN}=========================================={RESET}")
    print()
    log_info("Configuration Summary:")
    log_info(f"  Realm: {KEYCLOAK_REALM}")
    log_info(f"  Client ID: {KEYCLOAK_CLIENT_ID}")
    log_info(f"  Client Secret: {secret}")
    log_info(f"  Test User: {KEYCLOAK_TEST_USERNAME}")
    log_info(f"  Test Password: {KEYCLOAK_TEST_PASSWORD}")
    print()
    log_info("Token Endpoint:")
    log_info(f"  {KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token")
    print()
    log_info("To get a token, run:")
    log_info(f'  curl -X POST "{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token" \\')
    log_info('    -H "Content-Type: application/x-www-form-urlencoded" \\')
    log_info(f'    -d "client_id={KEYCLOAK_CLIENT_ID}" \\')
    log_info(f'    -d "client_secret={secret}" \\')
    log_info('    -d "grant_type=password" \\')
    log_info(f'    -d "username={KEYCLOAK_TEST_USERNAME}" \\')
    log_info(f'    -d "password={KEYCLOAK_TEST_PASSWORD}"')
    print()


if __name__ == "__main__":
    main()

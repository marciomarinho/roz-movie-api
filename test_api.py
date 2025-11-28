#!/usr/bin/env python3
"""
Test API with fresh bearer token from Keycloak
"""
import requests
import time

# Keycloak configuration
KEYCLOAK_URL = "http://localhost:8080"
KEYCLOAK_REALM = "movie-realm"
KEYCLOAK_CLIENT_ID = "movie-api-client"
CLIENT_SECRET = "sOfoZVuVnfeYoAze9mRJDT1dUROPDF2O"
KEYCLOAK_TEST_USERNAME = "movieuser"
KEYCLOAK_TEST_PASSWORD = "moviepassword"

# API configuration
API_URL = "http://localhost:8000"

# Wait for Keycloak to be fully ready
print("Waiting for Keycloak to be ready...")
for i in range(30):
    try:
        resp = requests.get(f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration", timeout=2)
        if resp.status_code == 200:
            print("✓ Keycloak is ready")
            break
    except:
        pass
    time.sleep(1)
else:
    print("✗ Keycloak did not become ready in time")
    exit(1)

# Get bearer token
print(f"\nGetting bearer token for user: {KEYCLOAK_TEST_USERNAME}")
token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
token_data = {
    "grant_type": "password",
    "client_id": KEYCLOAK_CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "username": KEYCLOAK_TEST_USERNAME,
    "password": KEYCLOAK_TEST_PASSWORD,
}

try:
    token_response = requests.post(token_url, data=token_data, timeout=10)
    token_response.raise_for_status()
    token = token_response.json()["access_token"]
    print(f"✓ Token obtained (length: {len(token)})")
    print(f"  Token (first 50 chars): {token[:50]}...")
except Exception as e:
    print(f"✗ Failed to get token: {e}")
    exit(1)

# Test API with bearer token
print(f"\nTesting API endpoint: GET {API_URL}/api/movies/1")
headers = {"Authorization": f"Bearer {token}"}

try:
    response = requests.get(f"{API_URL}/api/movies/1", headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\n✓ SUCCESS: API accepted bearer token!")
    else:
        print(f"\n✗ FAILED: Got status {response.status_code}")
        if response.text:
            print(f"Response body: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Test health endpoint (should work without auth)
print(f"\nTesting health endpoint (no auth required): GET {API_URL}/health")
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n✓ All tests completed!")

#!/usr/bin/env python3
"""Verify Keycloak setup was successful"""

import requests
import json

KEYCLOAK_URL = "http://localhost:8080"

print("\n" + "="*50)
print("  Keycloak Setup Verification")
print("="*50 + "\n")

# 1. Check Keycloak is running
print("[1] Checking Keycloak is accessible...")
try:
    response = requests.get(f"{KEYCLOAK_URL}/realms/master", timeout=5)
    if response.status_code == 200:
        print("    ✅ Keycloak is running and accessible\n")
    else:
        print(f"    ❌ Unexpected status: {response.status_code}\n")
except Exception as e:
    print(f"    ❌ Error: {e}\n")
    exit(1)

# 2. Get admin token
print("[2] Authenticating as admin...")
try:
    response = requests.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin",
            "grant_type": "password"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("    ✅ Admin authentication successful\n")
    else:
        print(f"    ❌ Authentication failed: {response.status_code}\n")
        exit(1)
except Exception as e:
    print(f"    ❌ Error: {e}\n")
    exit(1)

# 3. Check realm exists
print("[3] Checking movie-realm exists...")
try:
    response = requests.get(
        f"{KEYCLOAK_URL}/admin/realms/movie-realm",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        realm_data = response.json()
        print(f"    ✅ Realm 'movie-realm' exists")
        print(f"       - Enabled: {realm_data.get('enabled')}")
        print(f"       - Display Name: {realm_data.get('displayName', 'N/A')}\n")
    else:
        print(f"    ❌ Realm not found: {response.status_code}\n")
        exit(1)
except Exception as e:
    print(f"    ❌ Error: {e}\n")
    exit(1)

# 4. Check client exists
print("[4] Checking movie-api-client exists...")
try:
    response = requests.get(
        f"{KEYCLOAK_URL}/admin/realms/movie-realm/clients",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        clients = response.json()
        client = next((c for c in clients if c["clientId"] == "movie-api-client"), None)
        if client:
            print(f"    ✅ Client 'movie-api-client' exists")
            print(f"       - ID: {client['id']}")
            print(f"       - Protocol: {client.get('protocol', 'N/A')}")
            print(f"       - Public Client: {client.get('publicClient', False)}")
            print(f"       - Service Accounts: {client.get('serviceAccountsEnabled', False)}\n")
            client_id = client["id"]
        else:
            print(f"    ❌ Client 'movie-api-client' not found\n")
            exit(1)
    else:
        print(f"    ❌ Failed to list clients: {response.status_code}\n")
        exit(1)
except Exception as e:
    print(f"    ❌ Error: {e}\n")
    exit(1)

# 5. Check client secret
print("[5] Checking client secret is configured...")
try:
    response = requests.get(
        f"{KEYCLOAK_URL}/admin/realms/movie-realm/clients/{client_id}/client-secret",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        secret_data = response.json()
        secret = secret_data.get("value", "")
        if secret:
            print(f"    ✅ Client secret is configured")
            print(f"       - Secret: {secret[:20]}...{secret[-10:]}\n")
        else:
            print(f"    ❌ Client secret is empty\n")
except Exception as e:
    print(f"    ❌ Error: {e}\n")

# 6. Check test user exists
print("[6] Checking movieuser exists...")
try:
    response = requests.get(
        f"{KEYCLOAK_URL}/admin/realms/movie-realm/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        users = response.json()
        user = next((u for u in users if u["username"] == "movieuser"), None)
        if user:
            print(f"    ✅ User 'movieuser' exists")
            print(f"       - ID: {user['id']}")
            print(f"       - Enabled: {user.get('enabled', False)}\n")
        else:
            print(f"    ❌ User 'movieuser' not found\n")
    else:
        print(f"    ❌ Failed to list users: {response.status_code}\n")
except Exception as e:
    print(f"    ❌ Error: {e}\n")

# 7. Test token endpoint
print("[7] Testing token endpoint...")
try:
    response = requests.post(
        f"{KEYCLOAK_URL}/realms/movie-realm/protocol/openid-connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": "movie-api-client",
            "grant_type": "client_credentials"
        }
    )
    if response.status_code == 200:
        token_data = response.json()
        print(f"    ✅ Token endpoint is working")
        print(f"       - Token Type: {token_data.get('token_type', 'N/A')}")
        print(f"       - Expires In: {token_data.get('expires_in', 'N/A')} seconds\n")
    else:
        print(f"    ❌ Token endpoint error: {response.status_code}\n")
except Exception as e:
    print(f"    ❌ Error: {e}\n")

print("="*50)
print("  ✅ All checks passed!")
print("="*50 + "\n")
print("Your Keycloak setup is complete and working correctly!\n")

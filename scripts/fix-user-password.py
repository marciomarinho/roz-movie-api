#!/usr/bin/env python3
"""Fix user password setup in Keycloak"""

import requests

KEYCLOAK_URL = 'http://localhost:8080'

# Get admin token
print("[1] Getting admin token...")
response = requests.post(
    f'{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={
        'client_id': 'admin-cli',
        'username': 'admin',
        'password': 'admin',
        'grant_type': 'password'
    }
)
token = response.json()['access_token']
print("✅ Got admin token")

# Get user ID
print("\n[2] Getting user details...")
response = requests.get(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm/users?username=movieuser',
    headers={'Authorization': f'Bearer {token}'}
)
users = response.json()
user_id = users[0]['id']
print(f"✅ Found user ID: {user_id}")

# Get credentials
print("\n[3] Checking existing credentials...")
response = requests.get(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm/users/{user_id}/credentials',
    headers={'Authorization': f'Bearer {token}'}
)
credentials = response.json()
print(f"   Found {len(credentials)} credentials:")
for cred in credentials:
    print(f"     - {cred.get('type')} (ID: {cred.get('id')})")
    
    # Delete password credentials
    if cred.get('type') == 'password':
        resp = requests.delete(
            f"{KEYCLOAK_URL}/admin/realms/movie-realm/users/{user_id}/credentials/{cred['id']}",
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"     ✅ Deleted old password: {resp.status_code}")

# Set new password
print("\n[4] Setting new password...")
response = requests.put(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm/users/{user_id}/reset-password',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json={
        'type': 'password',
        'value': 'moviepassword',
        'temporary': False
    }
)
if response.status_code == 204:
    print("✅ Password set successfully!")
else:
    print(f"❌ Error: {response.status_code} - {response.text}")

# Test token
print("\n[5] Testing token endpoint...")
response = requests.post(
    f'{KEYCLOAK_URL}/realms/movie-realm/protocol/openid-connect/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={
        'client_id': 'movie-api-client',
        'client_secret': 'z3q2k04C4Vtw2iqC2eqXSyNdlZePpi5G',
        'grant_type': 'password',
        'username': 'movieuser',
        'password': 'moviepassword'
    }
)
if response.status_code == 200:
    data = response.json()
    print("✅ SUCCESS! Token obtained!")
    print(f"   Token type: {data.get('token_type')}")
    print(f"   Expires in: {data.get('expires_in')} seconds")
    print(f"   Access token: {data.get('access_token')[:50]}...")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"   Response: {response.json()}")

#!/usr/bin/env python3
"""Test different authentication flows"""

import requests
import os
import json

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "movie-realm")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "movie-api-client")

# Try to load client secret from .env.keycloak file
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
if not CLIENT_SECRET:
    # Try to read from keycloak secrets file
    try:
        with open(".env.keycloak", "r") as f:
            for line in f:
                if line.startswith("CLIENT_SECRET="):
                    CLIENT_SECRET = line.split("=", 1)[1].strip()
                    break
    except FileNotFoundError:
        pass

if not CLIENT_SECRET:
    print("ERROR: CLIENT_SECRET not found in environment or .env.keycloak file")
    print("Please run: make keycloak-setup")
    exit(1)

print('='*60)
print('Testing Different Keycloak Token Grant Types')
print('='*60)
print(f'Keycloak URL: {KEYCLOAK_URL}')
print(f'Realm: {KEYCLOAK_REALM}')
print(f'Client ID: {CLIENT_ID}')
print()

# Test 1: Client Credentials
print('[1] CLIENT CREDENTIALS Flow (Service Account):')
response = requests.post(
    f'{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
)
if response.status_code == 200:
    data = response.json()
    token = data.get('access_token')
    print(f'  ✅ SUCCESS!')
    print(f'     Token type: {data.get("token_type")}')
    print(f'     Expires: {data.get("expires_in")} seconds')
    print(f'     Token: {token[:50]}...')
else:
    print(f'  ❌ Failed: {response.status_code}')
    try:
        error_desc = response.json().get("error_description")
    except:
        error_desc = response.text
    print(f'     Error: {error_desc}')

# Test 2: Resource Owner Password Credentials
print('\n[2] RESOURCE OWNER PASSWORD CREDENTIALS Flow:')
response = requests.post(
    f'{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'password',
        'username': 'movieuser',
        'password': 'moviepassword'
    }
)
if response.status_code == 200:
    data = response.json()
    token = data.get('access_token')
    print(f'  ✅ SUCCESS!')
    print(f'     Token type: {data.get("token_type")}')
    print(f'     Expires: {data.get("expires_in")} seconds')
    print(f'     Token: {token[:50]}...')
else:
    print(f'  ❌ Failed: {response.status_code}')
    try:
        error_desc = response.json().get('error_description', 'Unknown error')
    except:
        error_desc = response.text
    print(f'     Error: {error_desc}')
    if 'not fully set up' in error_desc:
        print(f'\n     ⚠️  The user account has required actions pending.')
        print(f'         This usually means email verification or other setup is needed.')

print('\n' + '='*60)
print('Summary:')
print('='*60)
print(f'If [1] works: Use client_credentials for server-to-server auth')
print(f'If [2] works: Use password grant for user login')
print(f'Client Credentials is more secure for service-to-service communication.')
print('='*60)

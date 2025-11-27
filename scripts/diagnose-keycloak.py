#!/usr/bin/env python3
"""Diagnose Keycloak configuration"""

import requests
import json

KEYCLOAK_URL = 'http://localhost:8080'

# Get admin token
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

# Check client config
print('CLIENT CONFIGURATION:')
response = requests.get(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm/clients/ee903ea5-8ce9-4981-86b0-4a6b5257d225',
    headers={'Authorization': f'Bearer {token}'}
)
client = response.json()
print(f'  directAccessGrantsEnabled: {client.get("directAccessGrantsEnabled")}')
print(f'  standardFlowEnabled: {client.get("standardFlowEnabled")}')
print(f'  implicitFlowEnabled: {client.get("implicitFlowEnabled")}')
print(f'  publicClient: {client.get("publicClient")}')
print(f'  serviceAccountsEnabled: {client.get("serviceAccountsEnabled")}')

print('\nREALM PASSWORD POLICY:')
response = requests.get(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm',
    headers={'Authorization': f'Bearer {token}'}
)
realm = response.json()
print(f'  passwordPolicy: {realm.get("passwordPolicy", "None")}')

print('\nUSER CREDENTIALS:')
response = requests.get(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm/users/2f1dae6a-6f69-4b40-87d7-01818fab3076/credentials',
    headers={'Authorization': f'Bearer {token}'}
)
creds = response.json()
for cred in creds:
    print(f'  - Type: {cred.get("type")}')
    print(f'    UserLabel: {cred.get("userLabel")}')
    print(f'    CreatedDate: {cred.get("createdDate")}')
    print()

print('CHECKING AUTH FLOW SETTINGS:')
response = requests.get(
    f'{KEYCLOAK_URL}/admin/realms/movie-realm/authentication/flows',
    headers={'Authorization': f'Bearer {token}'}
)
flows = response.json()
for flow in flows:
    alias = flow.get('alias', 'Unknown')
    if 'direct' in alias.lower() or 'password' in alias.lower() or 'user' in alias.lower():
        print(f'  - {alias}: {flow.get("providerId")}')

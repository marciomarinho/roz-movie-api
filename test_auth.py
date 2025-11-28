#!/usr/bin/env python
"""Quick script to get a token and test the API."""
import requests

# Read client secret from .env.keycloak
client_secret = None
try:
    with open(".env.keycloak", "r") as f:
        for line in f:
            if line.startswith("CLIENT_SECRET="):
                client_secret = line.split("=", 1)[1].strip()
                break
except FileNotFoundError:
    print("✗ .env.keycloak not found")
    exit(1)

if not client_secret:
    print("✗ CLIENT_SECRET not found in .env.keycloak")
    exit(1)

# Get token using password grant WITH client secret
resp = requests.post(
    "http://localhost:8080/realms/movie-realm/protocol/openid-connect/token",
    data={
        "client_id": "movie-api-client",
        "client_secret": client_secret,
        "grant_type": "password",
        "username": "movieuser",
        "password": "moviepassword"
    }
)

data = resp.json()
if "access_token" in data:
    token = data["access_token"]
    print(f"✓ Got token: {token[:50]}...")
    
    # Test API with token
    headers = {"Authorization": f"Bearer {token}"}
    api_resp = requests.get("http://localhost:8000/api/movies", headers=headers)
    
    if api_resp.status_code == 200:
        movies = api_resp.json()
        print(f"✓ API works! Got {movies['total_items']} movies")
    else:
        print(f"✗ API returned {api_resp.status_code}: {api_resp.text}")
else:
    print(f"✗ Error: {data}")

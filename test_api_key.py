"""Test script to verify API key validation."""
import requests

BASE_URL = "http://127.0.0.1:8000"
VALID_API_KEY = "test-api-key-12345"

print("=" * 60)
print("API Key Validation Tests")
print("=" * 60)

# Test 1: Request without API key
print("\n[Test 1] Request WITHOUT X-API-Key header (should fail):")
try:
    response = requests.get(f"{BASE_URL}/api/movies")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Request with invalid API key
print("\n[Test 2] Request with INVALID X-API-Key header (should fail):")
try:
    response = requests.get(
        f"{BASE_URL}/api/movies",
        headers={"X-API-Key": "wrong-key"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Request with valid API key
print("\n[Test 3] Request with VALID X-API-Key header (should succeed):")
try:
    response = requests.get(
        f"{BASE_URL}/api/movies",
        headers={"X-API-Key": VALID_API_KEY}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Success! Got {data.get('total_items')} movies")
    print(f"Sample: {data.get('items')[0] if data.get('items') else 'No items'}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Search with valid API key
print("\n[Test 4] Search endpoint with valid X-API-Key (should succeed):")
try:
    response = requests.get(
        f"{BASE_URL}/api/movies/search?q=Toy",
        headers={"X-API-Key": VALID_API_KEY}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Success! Found {data.get('total_items')} movies matching 'Toy'")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Tests complete!")
print("=" * 60)

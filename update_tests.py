#!/usr/bin/env python
"""Update test file to use bearer token authentication."""
import re

with open("tests/integration/test_movies_api.py", "r") as f:
    content = f.read()

# Replace client with authenticated_client in method signatures
content = re.sub(
    r'def (test_\w+)\(self, client: TestClient\):',
    r'def \1(self, authenticated_client: TestClient):',
    content
)

# Replace client.get with authenticated_client.get
content = content.replace('client.get(', 'authenticated_client.get(')
content = content.replace('response_lower = authenticated_client.get(', 'response_lower = authenticated_client.get(')
content = content.replace('response_upper = authenticated_client.get(', 'response_upper = authenticated_client.get(')
content = content.replace('list_response = authenticated_client.get(', 'list_response = authenticated_client.get(')

# Remove X-API-Key headers
content = re.sub(r',\s*headers=\{"X-API-Key": "test-api-key-123"\}', '', content)

with open("tests/integration/test_movies_api.py", "w") as f:
    f.write(content)

print("[✓] Updated test file")

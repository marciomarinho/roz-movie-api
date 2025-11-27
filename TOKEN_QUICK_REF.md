# 🚀 Quick Start - Get a Token NOW!

## One-Line Token Request

```bash
curl -X POST "http://localhost:8080/realms/movie-realm/protocol/openid-connect/token" -H "Content-Type: application/x-www-form-urlencoded" -d "client_id=movie-api-client&client_secret=z3q2k04C4Vtw2iqC2eqXSyNdlZePpi5G&grant_type=client_credentials"
```

## Save Token to Variable

```bash
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/movie-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=movie-api-client&client_secret=bpVkX1pLFt92huj8isf7NJk9qa9n2KGZ&grant_type=password" \
  -d "username=movieuser&password=moviepassword" | jq -r '.access_token')

echo $TOKEN
```

## Use Token to Call Your API

```bash
curl -X GET "http://localhost:8000/api/movies" \
  -H "Authorization: Bearer $TOKEN"
```

## Check Token Details

```bash
# Decode token (visit https://jwt.io and paste it)
echo $TOKEN

# Or decode with Python
python -c "import base64, json; t='''$TOKEN'''; p=base64.b64decode(t.split('.')[1]+'=='); print(json.dumps(json.loads(p), indent=2))"
```

## Status Check

```bash
# Are services running?
docker-compose ps

# Can you reach Keycloak?
curl http://localhost:8080/realms/movie-realm

# Can you get a token?
curl -s -X POST "http://localhost:8080/realms/movie-realm/protocol/openid-connect/token" \
  -d "client_id=movie-api-client&client_secret=z3q2k04C4Vtw2iqC2eqXSyNdlZePpi5G&grant_type=client_credentials" | jq
```

## Admin Console

- URL: **http://localhost:8081/admin/master/console/**
- User: **admin**
- Password: **admin**

## Credentials Reference

| What | Value |
|------|-------|
| Client ID | movie-api-client |
| Client Secret | bpVkX1pLFt92huj8isf7NJk9qa9n2KGZ |
| Test User | movieuser |
| Test Password | moviepassword |
| Realm | movie-realm |
| Token Endpoint | http://localhost:8080/realms/movie-realm/protocol/openid-connect/token |

## Scripts

```bash
# Full setup
python scripts/keycloak-setup.py

# Verify everything
python scripts/verify-keycloak.py

# Test all auth flows
python scripts/test-auth-flows.py
```

## Troubleshooting

```bash
# View Keycloak logs
docker-compose logs keycloak | tail -50

# View database logs  
docker-compose logs db

# Restart everything
docker-compose restart

# Full rebuild
docker-compose down -v && docker-compose up --build
```

---

**Everything is working!** Use the token in your API calls. 🎉

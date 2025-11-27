# 🚀 Quick Start - Keycloak Ready to Use!

## Get Token (Copy & Paste)
```bash
curl -X POST "http://localhost:8080/realms/movie-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=movie-api-client" \
  -d "client_secret=z3q2k04C4Vtw2iqC2eqXSyNdlZePpi5G" \
  -d "grant_type=password" \
  -d "username=movieuser" \
  -d "password=moviepassword"
```

## Admin Console
- URL: http://localhost:8081/admin/master/console/
- User: admin / admin
- Realm to view: movie-realm

## Docker Status
```bash
docker-compose ps
```

Expected:
- ✅ movie_api_db (healthy)
- ✅ movie_api_keycloak (running)

## Setup Scripts

**Run setup:**
```bash
python scripts/keycloak-setup.py
```

**Verify setup:**
```bash
python scripts/verify-keycloak.py
```

## Credentials

| Type | Value |
|------|-------|
| Realm | movie-realm |
| Client | movie-api-client |
| Secret | z3q2k04C4Vtw2iqC2eqXSyNdlZePpi5G |
| User | movieuser |
| Password | moviepassword |

## Key URLs

| Service | URL |
|---------|-----|
| Keycloak | http://localhost:8080 |
| Admin Console | http://localhost:8081 |
| Token Endpoint | http://localhost:8080/realms/movie-realm/protocol/openid-connect/token |
| PostgreSQL | localhost:5432 |

## What's Running

✅ PostgreSQL 15 - Database  
✅ Keycloak 24.0.5 - Identity server  
✅ Realm "movie-realm" - Created  
✅ Client "movie-api-client" - Created  
✅ User "movieuser" - Created  

## Next: Connect Your FastAPI App

1. Uncomment the `app` service in `docker-compose.yml`
2. Add token validation to your FastAPI endpoints
3. Run: `docker-compose up --build`
4. Get token using curl above
5. Call your API with `Authorization: Bearer <token>`

**Done!** Everything works. Start using Keycloak. 🎉

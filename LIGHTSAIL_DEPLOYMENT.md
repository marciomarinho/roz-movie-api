# Movie API - Production Deployment Guide

This guide explains how to deploy the Movie API to AWS LightSail with AWS Cognito for authentication and AWS RDS for the database.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AWS LightSail Instance                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Nginx Reverse Proxy (Port 80)               │   │
│  │  - Forwards HTTP requests to FastAPI on Port 8000           │   │
│  │  - Provides external access point                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│           │                                                           │
│           ↓ (Port 8000 - Internal)                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              FastAPI Application (Docker Container)          │   │
│  │  - Movie Management API                                     │   │
│  │  - Health Checks & Metrics                                  │   │
│  │  - OAuth2 Bearer Token Verification (Cognito)               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
          │                               │
          │ OAuth2 Token Validation       │ Database Queries
          ↓                               ↓
    ┌──────────────────┐        ┌──────────────────┐
    │ AWS Cognito      │        │ AWS RDS          │
    │ (User Pool)      │        │ PostgreSQL       │
    │ - JWKS Endpoint  │        │ - movie_api_db   │
    │ - Token Verify   │        │ - Movies Table   │
    └──────────────────┘        └──────────────────┘
    (External Service)        (External Service)
```

## Prerequisites

1. **AWS Account** with permissions to:
   - Create/manage LightSail instances
   - Access existing RDS PostgreSQL instance
   - Access existing Cognito User Pool

2. **LightSail Instance** running:
   - Amazon Linux 2023 or Ubuntu 20.04+
   - Docker installed (or will be auto-installed by script)
   - Git installed (or will be auto-installed by script)

3. **External Dependencies** already provisioned:
   - AWS RDS PostgreSQL instance (connection details below)
   - AWS Cognito User Pool (User Pool ID below)
   - **Security Group**: RDS security group must allow inbound traffic on port 5432 from the LightSail instance IP

4. **AWS LightSail Firewall**:
   - Port 80 must be open (configured in AWS LightSail console)
   - Port 8000 is internal only (handled by Docker)

## Environment Variables

Before deployment, set these environment variables with your actual values:

```bash
# Database (AWS RDS)
export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=movie_api_db
export DB_USER=postgres
export DB_PASSWORD=<your-password>

# Cognito (AWS)
export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
export COGNITO_REGION=us-east-1

# Authentication
export AUTH_PROVIDER=cognito
export AUTH_ENABLED=true

# Logging (Optional)
export LOG_LEVEL=INFO
```

## Automated Deployment (Recommended)

### Quick Start - One Command Deployment

```bash
# Set environment variables first
export DB_HOST=...
export DB_PORT=5432
export DB_NAME=movie_api_db
export DB_USER=postgres
export DB_PASSWORD=...
export COGNITO_USER_POOL_ID=...
export COGNITO_REGION=us-east-1
export AUTH_PROVIDER=cognito
export AUTH_ENABLED=true

# Run automated deployment script
bash <(curl -fsSL https://raw.githubusercontent.com/marciomarinho/roz-movie-api/main/scripts/deploy-lightsail.sh)
```

The deployment script will automatically:
- ✓ Validate all required environment variables
- ✓ Install Docker, Git, PostgreSQL client, and Nginx (if not present)
- ✓ Clone the repository
- ✓ Create `.env` file with production settings
- ✓ Test RDS connectivity
- ✓ Create the database
- ✓ Configure Nginx as reverse proxy (port 80 → 8000)
- ✓ Build Docker image
- ✓ Run database migrations
- ✓ Load movie data from CSV
- ✓ Start the FastAPI application container
- ✓ Verify deployment health

### Script Details

The deployment script (`scripts/deploy-lightsail.sh`) performs these phases:

1. **Environment Validation** - Checks all required environment variables
2. **Dependency Installation** - Installs Docker, Git, psql, Nginx
3. **Repository Setup** - Clones repository and creates configuration
4. **RDS Connectivity** - Tests connection to RDS database
5. **Database Creation** - Creates database using `psql` CLI
6. **Nginx Configuration** - Sets up reverse proxy on port 80
7. **Container Cleanup** - Removes any existing containers
8. **Docker Build** - Builds optimized Docker image
9. **Database Migrations** - Runs Alembic migrations
10. **Movie Data Loading** - Populates movies from CSV
11. **Application Start** - Starts FastAPI container on port 8000
12. **Health Verification** - Verifies API is responding

## Manual Deployment (If Script Fails)

### 1. SSH into LightSail Instance

```bash
# Using AWS Console: Click "Connect" on the instance
# Or using SSH directly
ssh ec2-user@<lightsail-public-ip>
```

### 2. Install Prerequisites

```bash
# Amazon Linux 2023
sudo dnf install -y docker git postgresql15 nginx

# Or Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io git postgresql-client nginx

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. Clone Repository

```bash
cd /home/ec2-user  # or /home/ubuntu on Ubuntu
git clone https://github.com/marciomarinho/roz-movie-api.git
cd roz-movie-api
```

### 4. Set Environment Variables

```bash
export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=movie_api_db
export DB_USER=postgres
export DB_PASSWORD=<your-password>
export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
export COGNITO_REGION=us-east-1
export AUTH_PROVIDER=cognito
export AUTH_ENABLED=true
```

### 5. Test RDS Connectivity

```bash
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT 1"
unset PGPASSWORD
```

### 6. Create Database

```bash
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c \
    "CREATE DATABASE IF NOT EXISTS \"$DB_NAME\""
unset PGPASSWORD
```

### 7. Configure Nginx

Create `/etc/nginx/conf.d/movie-api.conf`:

```bash
sudo tee /etc/nginx/conf.d/movie-api.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

sudo systemctl restart nginx
```

### 8. Build Docker Image

```bash
docker build -t movie-api:latest .
```

### 9. Run Migrations

```bash
docker run --rm \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  movie-api:latest \
  alembic upgrade head
```

### 10. Load Movie Data

```bash
docker run --rm \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  movie-api:latest \
  python scripts/load_movies.py \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --dbname="$DB_NAME" \
    --user="$DB_USER" \
    --password="$DB_PASSWORD" \
    --csv-path=data/movies_large.csv
```

### 11. Start Application Container

```bash
docker run -d \
  --name movie-api \
  -p 8000:8000 \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e COGNITO_USER_POOL_ID="$COGNITO_USER_POOL_ID" \
  -e COGNITO_REGION="$COGNITO_REGION" \
  -e AUTH_PROVIDER="$AUTH_PROVIDER" \
  -e AUTH_ENABLED="$AUTH_ENABLED" \
  movie-api:latest
```

## Verification

### Test Local Health Check

```bash
curl http://localhost/health
# Expected: {"status":"ok"}
```

### Test Movies API

```bash
curl http://localhost/api/movies
# Expected: JSON list of movies
```

### View Logs

```bash
docker logs -f movie-api
```

## Important Discoveries

### Nginx Reverse Proxy (Port 80 → 8000)

**Issue**: AWS LightSail only exposes port 80 for inbound traffic. The FastAPI application runs on port 8000 by default.

**Solution**: Configure Nginx as a reverse proxy to forward all requests from port 80 to the internal Docker container on port 8000.

**Why this matters**:
- External clients connect to `http://<lightsail-ip>/`
- Nginx intercepts this on port 80
- Nginx forwards to `localhost:8000` internally
- The Docker container never exposes port 8000 to the internet

This is a common production pattern and ensures only port 80 needs to be open in the firewall.

### Docker Image Must Include Scripts Directory

**Issue**: The deployment script failed with `python: can't open file '/app/scripts/load_movies.py': [Errno 2] No such file or directory`

**Root Cause**: The `Dockerfile` was not copying the `scripts/` directory into the image.

**Solution**: Updated `Dockerfile` to include:
```dockerfile
COPY scripts/ ./scripts/
```

**Why this matters**: The `load_movies.py` script is needed inside the container to load movie data from the CSV file into the database.

### RDS Security Group Configuration

**Issue**: Connection attempts from LightSail to RDS were failing.

**Solution**: Add inbound rule to RDS security group:
- **Type**: PostgreSQL
- **Port**: 5432
- **Source**: Security group of LightSail instance (or specific LightSail IP)

**Important**: This must be done in AWS Console under the RDS security group settings.

### Package Manager Compatibility

**Issue**: Amazon Linux 2023 uses `dnf` instead of `yum`, and PostgreSQL package is named `postgresql15` (not `postgresql15-client`)

**Solution**: The deployment script auto-detects the OS and uses the correct package manager and package names.

## Cleanup

If you need to completely remove the deployment and all resources:

```bash
cd roz-movie-api
./scripts/cleanup-lightsail.sh
```

This will:
- Stop and remove Docker containers
- Remove Docker images
- Remove installed packages (Docker, Git, psql, Nginx)
- Remove configuration files
- Drop the RDS database
- Remove the repository directory

## API Usage

### Health Check

```bash
curl http://<lightsail-ip>/health
```

### Get Movies

```bash
curl http://<lightsail-ip>/api/movies
```

### Get All Movies (Paginated)

```bash
curl "http://<lightsail-ip>/api/movies?page=1&page_size=20"
```

### Interactive API Documentation

- **Swagger UI**: http://<lightsail-ip>/docs
- **ReDoc**: http://<lightsail-ip>/redoc

## Troubleshooting

### Deployment script hangs on package installation

**Issue**: `dnf` or `apt-get` waiting for lock from another process

**Solution**:
1. Wait a few minutes (background updates might be running)
2. If it persists, kill the hanging process and retry
3. Run script again - it will retry the installation

```bash
# Check for hanging processes
ps aux | grep dnf
ps aux | grep apt-get

# Kill if necessary (careful!)
sudo kill -9 <pid>
```

### Movies endpoint returns empty list

**Issue**: `GET /api/movies` returns `{"items": [], "total_items": 0}`

**Cause**: Movie data wasn't loaded into the database

**Solution**:
1. Verify database exists and is accessible
2. Manually run movie loading:
```bash
docker run --rm \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  movie-api:latest \
  python scripts/load_movies.py \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --dbname="$DB_NAME" \
    --user="$DB_USER" \
    --password="$DB_PASSWORD" \
    --csv-path=data/movies_large.csv
```
3. Check for errors in the output

### Application won't start - "DB connection refused"

**Issue**: Docker container can't connect to RDS

**Solutions**:
1. Verify RDS security group allows inbound on port 5432 from LightSail IP
2. Test connectivity manually from LightSail:
```bash
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1"
unset PGPASSWORD
```
3. Check that RDS instance is running in AWS Console

### Port 80 not accessible from internet

**Issue**: Can't reach `http://<lightsail-ip>/` from outside

**Solutions**:
1. Verify port 80 is open in AWS LightSail console (Networking tab)
2. Check Nginx is running: `sudo systemctl status nginx`
3. Test locally: `curl http://localhost/health`
4. Check firewall within LightSail: `sudo iptables -L`

### Cognito authentication failing

**Issue**: API returns 401 Unauthorized for authenticated endpoints

**Solutions**:
1. Verify Cognito User Pool ID and Region are correct
2. Check JWKS endpoint is accessible:
```bash
curl https://cognito-idp.${COGNITO_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}/.well-known/jwks.json
```
3. Verify token in Authorization header is valid and not expired

## Monitoring and Logs

### View Application Logs

```bash
# Last 100 lines
docker logs -n 100 movie-api

# Follow logs in real-time
docker logs -f movie-api

# Logs with timestamps
docker logs -t movie-api
```

### Check Container Status

```bash
# Running containers
docker ps

# All containers (including stopped)
docker ps -a

# Container details
docker inspect movie-api
```

### Monitor RDS

Use AWS Console to monitor:
- CPU utilization
- Storage space
- Connection count
- Query performance

## Performance Considerations

1. **Docker Image Size**: The image is optimized with `python:3.11-slim`
2. **Database Indexes**: Movies table has indexes on commonly searched fields
3. **Pagination**: API uses pagination to prevent memory issues with large datasets
4. **Nginx Buffering**: Configured for optimal reverse proxy performance

## Security Considerations

1. **Environment Variables**: Never commit `.env` to Git
   - Use `.gitignore` to exclude
   - Consider AWS Secrets Manager for sensitive data

2. **RDS Security Group**: Only allow connections from LightSail
   - Monitor failed connection attempts
   - Use security group IDs, not IP addresses when possible

3. **API Authentication**: All endpoints (except `/health`) require Cognito JWT
   - Tokens have expiration times
   - Implement token refresh logic in clients

4. **Network Security**: 
   - Only port 80 is open externally
   - Port 8000 is internal only (Docker network)
   - RDS is not directly accessible from internet

5. **Container Security**:
   - Application runs as non-root user (`appuser`)
   - Regular image updates for security patches

## Rollback Procedures

### If deployment fails

```bash
# Stop the application
docker stop movie-api
docker rm movie-api

# Restore previous version
git checkout <previous-commit>

# Rebuild and redeploy
docker build -t movie-api:latest .
./scripts/deploy-lightsail.sh
```

### Database migration rollback

```bash
docker run --rm \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  movie-api:latest \
  alembic downgrade -1
```

## Next Steps

1. Set up CloudWatch monitoring and alerts
2. Configure auto-scaling if needed
3. Implement CI/CD pipeline for automated deployments
4. Set up RDS automated backups
5. Regular load testing to validate performance
6. Plan disaster recovery procedures

## Support

For issues or questions:
- Check application logs with `docker logs -f movie-api`
- Review AWS Console for service health
- Verify all environment variables are set: `env | grep DB_`
- Test RDS connectivity manually
- Ensure all prerequisites are installed


# Movie API - Production Deployment Guide

This guide explains how to deploy the Movie API to AWS LightSail with AWS Cognito for authentication and AWS RDS for the database.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS LightSail Instance                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application (Port 8000)              │  │
│  │  - Movie Management API                                  │  │
│  │  - Health Checks & Metrics                               │  │
│  │  - OAuth2 Bearer Token Verification (Cognito)            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
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
   - Ubuntu 20.04 or later
   - Python 3.11+
   - Git

3. **External Dependencies** already provisioned:
   - AWS RDS PostgreSQL instance (connection details below)
   - AWS Cognito User Pool (User Pool ID below)

## Environment Variables

Before deployment, set these environment variables with your actual values:

```bash
# Database (AWS RDS)
export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=movie_api_db
export DB_USER=postgres
export DB_PASSWORD=BananaGelada12

# Cognito (AWS)
export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
export COGNITO_REGION=us-east-1

# Authentication
export AUTH_PROVIDER=cognito
export AUTH_ENABLED=true

# Logging
export LOG_LEVEL=INFO
```

## Deployment Steps

### 1. SSH into LightSail Instance

```bash
# Using AWS CLI
aws lightsail connect-ssh --instance-name movie-api --region us-east-1

# Or using SSH directly (get the IP from AWS Console)
ssh ubuntu@<lightsail-public-ip>
```

### 2. Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/marciomarinho/roz-movie-api.git
cd roz-movie-api
```

### 3. Set Environment Variables

Create and export environment variables:

```bash
# Copy the template
cp .env.production.template .env

# Edit with your actual values
nano .env

# Source the environment
source .env
```

Or set them directly in the terminal:

```bash
export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=movie_api_db
export DB_USER=postgres
export DB_PASSWORD=BananaGelada12
export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
export COGNITO_REGION=us-east-1
export AUTH_PROVIDER=cognito
export AUTH_ENABLED=true
```

### 4. Run Deployment Script

```bash
chmod +x deploy-lightsail.sh
./deploy-lightsail.sh
```

The script will:
- ✓ Validate all required environment variables
- ✓ Create `.env` file with production settings
- ✓ Install Python dependencies
- ✓ Wait for RDS to be ready
- ✓ Run database migrations
- ✓ Start the FastAPI application

### 5. Verify Deployment

```bash
# Check if application is running
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"ok"}

# View API documentation
# Open in browser: http://<lightsail-ip>:8000/docs
```

### 6. (Optional) Set Up Systemd Service

For automatic restart and management:

```bash
# Copy service file
sudo cp movie-api.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable movie-api
sudo systemctl start movie-api

# Check status
sudo systemctl status movie-api

# View logs
sudo journalctl -u movie-api -f
```

## API Usage

### Health Check

```bash
curl http://<lightsail-ip>:8000/api/v1/health
```

### Get Movies (with Cognito Authentication)

```bash
# Get access token from Cognito
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id <your-client-id> \
  --auth-flow CLIENT_CREDENTIALS_AUTH \
  --auth-parameters SCOPES="default-m2m-resource-server-b4pkvO/read" \
  --region us-east-1 \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# Call API with token
curl -H "Authorization: Bearer $TOKEN" \
  http://<lightsail-ip>:8000/api/v1/movies
```

### Interactive API Documentation

- **Swagger UI**: http://<lightsail-ip>:8000/docs
- **ReDoc**: http://<lightsail-ip>:8000/redoc

## Troubleshooting

### Application won't start

**Check logs:**
```bash
# If using systemd
sudo journalctl -u movie-api -n 50

# Or check the deployment script output
cat deploy.log
```

**Common issues:**
- `DB connection refused`: RDS security group doesn't allow LightSail IP
- `Cognito JWKS fetch failed`: Check network connectivity, Cognito region
- `Missing environment variables`: Ensure all required vars are set

### Database connection issues

```bash
# Test RDS connection from LightSail
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='$DB_HOST',
    port=$DB_PORT,
    database='$DB_NAME',
    user='$DB_USER',
    password='$DB_PASSWORD'
)
print('Connected successfully')
"
```

### Cognito token verification fails

```bash
# Check Cognito JWKS endpoint
curl https://cognito-idp.${COGNITO_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}/.well-known/jwks.json
```

## Logs and Monitoring

### View Application Logs

If using systemd:
```bash
sudo journalctl -u movie-api -f
```

If running directly:
```bash
# Logs output to stdout
# Redirect to file if needed
./deploy-lightsail.sh > deployment.log 2>&1 &
tail -f deployment.log
```

### RDS Monitoring

Use AWS Console to monitor:
- Connection count
- CPU utilization
- Storage space
- Query performance

## Security Considerations

1. **Environment Variables**: Never commit `.env` file to Git
   - Use `.gitignore` to exclude it
   - Use AWS Secrets Manager for sensitive data in production

2. **RDS Security Group**: Ensure it only allows connections from LightSail
   - Restrict to LightSail private IP if possible
   - Monitor failed connection attempts

3. **Cognito**: Enable MFA and use strong client credentials
   - Rotate credentials regularly
   - Monitor token usage

4. **Network**: Use HTTPS/SSL
   - Set up AWS Certificate Manager
   - Use Application Load Balancer (ALB) if needed

## Rollback Procedures

### If deployment fails

```bash
# Stop the application
sudo systemctl stop movie-api

# Restore previous version
git checkout <previous-commit>

# Re-run deployment
./deploy-lightsail.sh
```

### Database migration rollback

```bash
# Downgrade to previous migration
alembic downgrade -1

# Or downgrade to specific revision
alembic downgrade <revision>
```

## Next Steps

1. Set up monitoring and alerts (CloudWatch)
2. Configure auto-scaling if needed
3. Set up CI/CD pipeline for automated deployments
4. Regular backups for RDS
5. Load testing to validate performance

## Support

For issues or questions:
- Check application logs
- Review AWS console for service health
- Verify environment variables are set correctly
- Ensure RDS and Cognito are accessible from LightSail

# Deployment Guide: AWS LightSail

This guide walks through deploying the Movie API to an AWS LightSail instance from scratch.

## Prerequisites

- AWS LightSail instance (Amazon Linux 2 OR Amazon Linux 2023)
- SSH access via key pair
- Application code ready to deploy

## Step 1: Connect to Your LightSail Instance

```bash
ssh -i ~/marcio.pem ec2-user@52.62.14.166
```

You should now be in an empty Linux environment.

## Step 2: Update System and Install Dependencies

First, update the package manager and install essential tools:

### Option A: Automated Setup (Recommended)

Use the provided setup script to automate all installations:

```bash
# Method 1: Direct download and run (freshest version)
curl -fsSL https://raw.githubusercontent.com/marciomarinho/roz-movie-api/main/scripts/setup-lightsail.sh -o /tmp/setup.sh && bash /tmp/setup.sh

# Method 2: If Method 1 doesn't work, add cache bust
curl -fsSL "https://raw.githubusercontent.com/marciomarinho/roz-movie-api/main/scripts/setup-lightsail.sh?$(date +%s)" -o /tmp/setup.sh && bash /tmp/setup.sh

# Method 3: Download and review before running
wget https://raw.githubusercontent.com/marciomarinho/roz-movie-api/main/scripts/setup-lightsail.sh -O setup.sh
bash setup.sh
```

The script will:
- ✅ Update system packages
- ✅ Install git, wget, gcc, make, python3, pip3
- ✅ Install Docker and Docker Compose (works on AL2 and AL2023)
- ✅ Configure Docker permissions
- ✅ Clone the repository
- ✅ Display next steps

After the script completes, follow the on-screen instructions to log out and back in.

### Option B: Manual Installation

If you prefer to install manually:

```bash
# Update system packages
sudo yum update -y

# Install development tools
sudo yum install -y git curl wget gcc make python3 python3-pip python3-devel
```

**What this does:**
- `git`: For cloning your application code from GitHub
- `curl`, `wget`: For downloading files
- `gcc`, `python3-devel`: For compiling Python packages
- `python3-pip`: Python package manager
- `make`: For running Makefile commands

Verify installations:

```bash
git --version
python3 --version
pip3 --version
make --version
```

## Step 3: Install Docker and Docker Compose

Docker is required to run your containerized application:

```bash
# Install Docker
sudo amazon-linux-extras install -y docker

# Start Docker daemon
sudo systemctl start docker
sudo systemctl enable docker

# Add ec2-user to docker group (allows running docker without sudo)
sudo usermod -aG docker ec2-user

# Log out and back in for group changes to take effect
exit
```

Reconnect:

```bash
ssh -i ~/marcio.pem ec2-user@52.62.14.166
```

Verify Docker is working:

```bash
docker --version
docker run hello-world
```

Install Docker Compose:

```bash
# Download latest Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

## Step 4: Clone Your Application Repository

```bash
# Create a directory for your application
mkdir -p ~/apps
cd ~/apps

# Clone your repository
git clone <YOUR_GITHUB_REPO_URL> movie-api
cd movie-api
```

If your repository is private, you'll need to set up SSH keys:

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Display public key (add this to GitHub Deploy Keys)
cat ~/.ssh/id_rsa.pub
```

Then try cloning again with the SSH URL:

```bash
git clone git@github.com:marciomarinho/roz-movie-api.git
```

## Step 5: Verify Application Structure

Once cloned, verify the key files are present:

```bash
cd movie-api
ls -la

# Should see:
# - docker-compose.yml
# - Dockerfile
# - Makefile
# - app/ (application code)
# - tests/ (test suite)
# - .env.keycloak (or create from template)
```

## Step 6: Initialize Application

Use the Makefile to automatically set up and configure everything:

```bash
# Run setup (creates .env.keycloak with auto-generated secrets)
make setup
```

This single command will:
- ✅ Create `.env.keycloak` with auto-generated secure passwords
- ✅ Set up PostgreSQL database with migrations
- ✅ Initialize Keycloak with the movie-realm
- ✅ Create client credentials
- ✅ Start all services (database, Keycloak, API)

If you need to customize environment variables after setup:

```bash
# Edit the generated environment file
nano .env.keycloak

# Restart services to apply changes
docker-compose down
docker-compose up -d
```

---

## Alternative: Build and Run Docker Containers Locally (Without Docker Compose)

If you prefer to build Docker images locally on the EC2 instance and manage containers directly:

### Step 6A: Load Environment Variables

```bash
# Source the environment file
source .env.keycloak

# Verify environment variables are loaded
echo $KEYCLOAK_ADMIN_PASSWORD
echo $DB_PASSWORD
```

### Step 6B: Create Docker Network

```bash
# Create a custom Docker network for container communication
docker network create movie-api-network
```

### Step 6C: Start PostgreSQL Container

```bash
# Run PostgreSQL database
docker run -d \
  --name movie-db \
  --network movie-api-network \
  -e POSTGRES_USER=$DB_USER \
  -e POSTGRES_PASSWORD=$DB_PASSWORD \
  -e POSTGRES_DB=$DB_NAME \
  -v movie-db-data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine
```

Wait for database to be ready:

```bash
sleep 10
# Verify it's running
docker ps | grep movie-db
```

### Step 6D: Run Database Migrations

```bash
# Build and run migrations
docker run --rm \
  --network movie-api-network \
  -e DB_HOST=movie-db \
  -e DB_PORT=5432 \
  -e DB_USER=$DB_USER \
  -e DB_PASSWORD=$DB_PASSWORD \
  -e DB_NAME=$DB_NAME \
  -v $(pwd):/app \
  -w /app \
  python:3.11 \
  bash -c "pip install -q alembic sqlalchemy psycopg2-binary && alembic upgrade head"
```

### Step 6E: Start Keycloak Container

```bash
# Run Keycloak
docker run -d \
  --name movie-keycloak \
  --network movie-api-network \
  -e KEYCLOAK_ADMIN=$KEYCLOAK_ADMIN \
  -e KEYCLOAK_ADMIN_PASSWORD=$KEYCLOAK_ADMIN_PASSWORD \
  -e KC_PROXY=edge \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:latest \
  start-dev

# Wait for Keycloak to initialize (~30-60 seconds)
sleep 30

# Verify it's running
curl http://localhost:8080/health
```

### Step 6F: Initialize Keycloak Realm (Optional - Already Done by Setup)

If you haven't run `make setup`, you can initialize Keycloak manually:

```bash
# This is usually done by the setup script, but can be done manually
# The setup process creates the realm and client automatically
```

### Step 6G: Build Application Docker Image

```bash
# Build the Movie API Docker image
docker build -t movie-api:latest .

# Verify the image was built
docker images | grep movie-api
```

### Step 6H: Run Application Container

```bash
# Run the Movie API
docker run -d \
  --name movie-api-app \
  --network movie-api-network \
  -e DB_HOST=movie-db \
  -e DB_PORT=5432 \
  -e DB_USER=$DB_USER \
  -e DB_PASSWORD=$DB_PASSWORD \
  -e DB_NAME=$DB_NAME \
  -e KEYCLOAK_URL=http://movie-keycloak:8080 \
  -e KEYCLOAK_REALM=$KEYCLOAK_REALM \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -p 8000:8000 \
  movie-api:latest

# Verify it's running
docker ps | grep movie-api-app
```

### Step 6I: Verify All Containers Are Running

```bash
# List all running containers
docker ps

# Check logs of each service
docker logs movie-db
docker logs movie-keycloak
docker logs movie-api-app

# Follow logs in real-time
docker logs -f movie-api-app
```

### Step 6J: Test the API

```bash
# Get a token from Keycloak
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$KEYCLOAK_CLIENT_ID" \
  -d "client_secret=$KEYCLOAK_CLIENT_SECRET" \
  -d "grant_type=client_credentials" \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# Access the API
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/movies?page=1&page_size=10"

# Test health endpoint
curl http://localhost:8000/health
```

### Useful Commands for Manual Docker Management

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs
docker logs movie-api-app
docker logs -f movie-api-app    # Follow logs
docker logs --tail 100 movie-api-app   # Last 100 lines

# Stop containers
docker stop movie-api-app
docker stop movie-keycloak
docker stop movie-db

# Start containers
docker start movie-api-app
docker start movie-keycloak
docker start movie-db

# Restart containers
docker restart movie-api-app

# Remove containers (must be stopped first)
docker stop movie-api-app
docker rm movie-api-app

# View container resource usage
docker stats

# Inspect container details
docker inspect movie-api-app

# Access container shell
docker exec -it movie-api-app /bin/bash

# View container environment variables
docker exec movie-api-app env
```

### Cleanup: Remove All Containers and Network

```bash
# Stop all containers
docker stop movie-api-app movie-keycloak movie-db

# Remove all containers
docker rm movie-api-app movie-keycloak movie-db

# Remove the network
docker network rm movie-api-network

# Remove the image
docker rmi movie-api:latest

# Remove database volume (optional - deletes data!)
docker volume rm movie-db-data
```

### Systemd Service for Auto-Start on Reboot

If you want containers to restart automatically on system reboot:

```bash
# Create a startup script
cat > ~/start-movie-api.sh << 'EOF'
#!/bin/bash
source /home/ec2-user/apps/movie-api/.env.keycloak

# Create network if it doesn't exist
docker network create movie-api-network 2>/dev/null || true

# Start containers
docker start movie-db 2>/dev/null || docker run -d \
  --name movie-db \
  --network movie-api-network \
  -e POSTGRES_USER=$DB_USER \
  -e POSTGRES_PASSWORD=$DB_PASSWORD \
  -e POSTGRES_DB=$DB_NAME \
  -v movie-db-data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine

sleep 10

docker start movie-keycloak 2>/dev/null || docker run -d \
  --name movie-keycloak \
  --network movie-api-network \
  -e KEYCLOAK_ADMIN=$KEYCLOAK_ADMIN \
  -e KEYCLOAK_ADMIN_PASSWORD=$KEYCLOAK_ADMIN_PASSWORD \
  -e KC_PROXY=edge \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:latest \
  start-dev

sleep 30

docker start movie-api-app 2>/dev/null || docker run -d \
  --name movie-api-app \
  --network movie-api-network \
  -e DB_HOST=movie-db \
  -e DB_PORT=5432 \
  -e DB_USER=$DB_USER \
  -e DB_PASSWORD=$DB_PASSWORD \
  -e DB_NAME=$DB_NAME \
  -e KEYCLOAK_URL=http://movie-keycloak:8080 \
  -e KEYCLOAK_REALM=$KEYCLOAK_REALM \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -p 8000:8000 \
  movie-api:latest
EOF

chmod +x ~/start-movie-api.sh
```

Create systemd service:

```bash
sudo tee /etc/systemd/system/movie-api.service > /dev/null << 'EOF'
[Unit]
Description=Movie API Docker Services
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/ec2-user/start-movie-api.sh
ExecStop=/usr/bin/bash -c 'docker stop movie-api-app movie-keycloak movie-db; docker network rm movie-api-network'
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable movie-api
sudo systemctl start movie-api
```

---

## Step 7: Verify Deployment

After `make setup` completes, verify everything is running:

```bash
# Check if services are running
docker-compose ps
```

Wait for Keycloak to fully initialize (~30-60 seconds):

```bash
# Check Keycloak health
curl http://localhost:8080/health
```

Test the API:

```bash
# Get a token from Keycloak
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/movie-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=movie-api-client" \
  -d "client_secret=$(grep KEYCLOAK_CLIENT_SECRET .env.keycloak | cut -d'=' -f2)" \
  -d "grant_type=client_credentials" \
  | jq -r '.access_token')

# Access the API
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/movies?page=1&page_size=10"
```

## Step 8: Configure Networking and Security Groups

Your LightSail instance needs to allow traffic on the required ports. In the AWS Console:

1. **Go to Networking tab** for your LightSail instance
2. **Add port rules:**
   - HTTP (80) - for web traffic
   - HTTPS (443) - for secure traffic
   - 8000 - for API (optional, if not behind reverse proxy)

**Example ports to allow:**
```
Protocol | Port | Source
---------|------|--------
TCP      | 80   | 0.0.0.0/0
TCP      | 443  | 0.0.0.0/0
TCP      | 8000 | 0.0.0.0/0 (API)
```

## Step 9: Set Up Reverse Proxy (Nginx)

For production, use Nginx as a reverse proxy:

```bash
# Install Nginx
sudo yum install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create Nginx configuration
sudo tee /etc/nginx/conf.d/movie-api.conf > /dev/null << 'EOF'
upstream movie_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name 52.62.14.166;

    location / {
        proxy_pass http://movie_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://movie_api;
    }
}
EOF
```

Reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Now access your API through Nginx:

```bash
curl "http://52.62.14.166/api/movies"
```

## Step 10: Enable HTTPS with Let's Encrypt (Optional but Recommended)

Install Certbot:

```bash
sudo yum install -y certbot certbot-nginx

# Request certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is enabled by default
```

## Step 11: Set Up Monitoring and Logs

### View Application Logs

```bash
# Real-time logs
docker-compose logs -f app

# Keycloak logs
docker-compose logs -f keycloak

# Database logs
docker-compose logs -f db
```

### Set Up Log Rotation

```bash
# Create log rotation configuration
sudo tee /etc/logrotate.d/movie-api > /dev/null << 'EOF'
/home/ec2-user/apps/movie-api/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ec2-user ec2-user
}
EOF
```

### Monitor Disk Usage

```bash
# Check disk usage
df -h

# Check Docker storage usage
docker system df
```

Clean up old Docker images if needed:

```bash
# Remove unused images and volumes
docker system prune -a -f
```

## Step 12: Backup Strategy

### Backup PostgreSQL Database

```bash
# Create backup script
cat > ~/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ec2-user/backups"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U movie_user movie_database | \
  gzip > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz"

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x ~/backup-db.sh
```

### Automate Backup with Cron

```bash
# Add to crontab
crontab -e

# Add this line to run backup daily at 2 AM
0 2 * * * /home/ec2-user/backup-db.sh
```

## Step 13: Maintenance Tasks

### Update Application Code

```bash
cd ~/apps/movie-api

# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Monitor Application Health

```bash
# Check if services are running
docker-compose ps

# Check API health
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/health"
```

### View Resource Usage

```bash
# CPU and memory usage
docker stats

# Disk usage
du -sh ~/apps/movie-api
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# View detailed logs
docker-compose logs -f

# Restart Docker
sudo systemctl restart docker
```

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process if needed
sudo kill -9 <PID>
```

### Database Connection Issues

```bash
# Check if database container is running
docker-compose ps db

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a -f

# Remove old backups
rm ~/backups/backup_*.sql.gz (keep recent ones)
```

## Security Hardening (Production)

1. **Update SSH Configuration:**
   ```bash
   sudo nano /etc/ssh/sshd_config
   
   # Disable password authentication
   PasswordAuthentication no
   
   # Change default SSH port
   Port 2222
   ```

2. **Enable UFW (Firewall):**
   ```bash
   sudo yum install -y ufw
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Set Up Fail2Ban (Intrusion Detection):**
   ```bash
   sudo yum install -y fail2ban
   sudo systemctl start fail2ban
   sudo systemctl enable fail2ban
   ```

4. **Use AWS Secrets Manager:**
   Instead of `.env` files, store secrets in AWS:
   ```bash
   # Create secret in AWS
   aws secretsmanager create-secret \
     --name movie-api/keycloak \
     --secret-string '{"password":"secure-password"}'
   
   # Retrieve in application
   aws secretsmanager get-secret-value --secret-id movie-api/keycloak
   ```

## Quick Reference Commands

```bash
# SSH into instance
ssh -i ~/marcio.pem ec2-user@52.62.14.166

# Start/Stop services
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose restart app    # Restart app only

# Check status
docker-compose ps             # Running containers
docker-compose logs -f        # Follow logs
docker stats                  # Resource usage

# Manage systemd service
sudo systemctl start movie-api
sudo systemctl stop movie-api
sudo systemctl status movie-api

# Update application
cd ~/apps/movie-api
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Next Steps

1. Configure a domain name (Route53 or external DNS)
2. Set up HTTPS with Let's Encrypt
3. Enable automated backups to S3
4. Set up CloudWatch monitoring
5. Configure email notifications for alerts
6. Create disaster recovery procedures

---

**Your Movie API is now deployed on AWS LightSail!** 🚀

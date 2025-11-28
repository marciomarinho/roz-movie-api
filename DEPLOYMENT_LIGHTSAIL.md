# Deployment Guide: AWS LightSail

This guide walks through deploying the Movie API to an AWS LightSail instance from scratch.

## Prerequisites

- AWS LightSail instance (Amazon Linux 2)
- SSH access via key pair
- Application code ready to deploy

## Step 1: Connect to Your LightSail Instance

```bash
ssh -i ~/marcio.pem ec2-user@52.62.14.166
```

You should now be in an empty Linux environment.

## Step 2: Update System and Install Dependencies

First, update the package manager and install essential tools:

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

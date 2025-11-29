#!/bin/bash
"""
LightSail Deployment Guide

This guide explains how to deploy the Movie API to AWS LightSail with:
- AWS RDS PostgreSQL (external dependency)
- AWS Cognito (external dependency)
- FastAPI application (running in LightSail)
"""

# Step 1: SSH into LightSail instance
# aws lightsail connect-ssh --instance-name movie-api

# Step 2: Clone the repository
git clone <your-repo-url>
cd movie_api

# Step 3: Set environment variables for production
# These should be set before running the deployment script
export DB_HOST=database-1.cypq86uaqfw3.us-east-1.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=movie_api_db
export DB_USER=postgres
export DB_PASSWORD=BananaGelada12

export COGNITO_USER_POOL_ID=us-east-1_voK1rTJtK
export COGNITO_REGION=us-east-1

export AUTH_PROVIDER=cognito
export AUTH_ENABLED=true

# Step 4: Run the deployment script
chmod +x deploy-lightsail.sh
./deploy-lightsail.sh

# The application will be running at: http://<lightsail-ip>:8000

# Step 5: (Optional) Set up systemd service for auto-restart
# Create /etc/systemd/system/movie-api.service with the content below

# Step 6: Access the application
# - API: http://<lightsail-ip>:8000
# - API Docs: http://<lightsail-ip>:8000/docs
# - ReDoc: http://<lightsail-ip>:8000/redoc

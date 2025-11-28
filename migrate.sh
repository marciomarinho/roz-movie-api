#!/bin/bash
cd /app
echo "Starting database migrations..."
python -m alembic upgrade head
echo "Migrations complete"

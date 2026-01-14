#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Applying database migrations..."
cd /app/game-service/app
uv run alembic upgrade head

echo "Starting game-service..."
cd ..
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 5002


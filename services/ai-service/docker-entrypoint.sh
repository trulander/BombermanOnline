#!/bin/bash
set -e

echo "Starting ai-service..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 5004


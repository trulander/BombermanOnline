#!/bin/bash
set -e

export INFISICAL_TOKEN=$(infisical login --method=universal-auth --client-id=$INFISICAL_MACHINE_CLIENT_ID --client-secret=$INFISICAL_MACHINE_CLIENT_SECRET --plain --silent)

echo "Starting webapi-service..."
exec infisical run --token $INFISICAL_TOKEN --path $INFISICAL_PATH --projectId $INFISICAL_PROJECT_ID --env $INFISICAL_SECRET_ENV --domain $INFISICAL_API_URL -- uv run uvicorn app.main:app --host 0.0.0.0 --port 5001


#!/bin/bash
set -e

echo "Starting auth-service..."

echo "Getting infisical token..."
export INFISICAL_TOKEN=$(infisical login --method=universal-auth --client-id=$INFISICAL_MACHINE_CLIENT_ID --client-secret=$INFISICAL_MACHINE_CLIENT_SECRET --plain --silent)


if [ "$PYCHARM_DEBUG" = "1" ]; then
  echo "Detected pycharm debug mode"

  exec infisical run --token $INFISICAL_TOKEN --path $INFISICAL_PATH --projectId $INFISICAL_PROJECT_ID --env $INFISICAL_SECRET_ENV --domain $INFISICAL_API_URL -- "$@"

#  echo "Export env. from infisical"
#  infisical export --token $INFISICAL_TOKEN --path $INFISICAL_PATH --projectId $INFISICAL_PROJECT_ID --env $INFISICAL_SECRET_ENV --domain $INFISICAL_API_URL > .env.infisical
#
#  echo "Waiting for PyCharm to start python process..."
#  echo "Gotten command: $@"
#  exec "$@"
else
  echo "Waiting for PostgreSQL to be ready..."
  sleep 5

  echo "Applying database migrations..."
  cd /app/auth-service/app
  infisical run --token $INFISICAL_TOKEN --path $INFISICAL_PATH --projectId $INFISICAL_PROJECT_ID --env $INFISICAL_SECRET_ENV --domain $INFISICAL_API_URL -- uv run alembic upgrade head
  cd ..

  exec infisical run --token $INFISICAL_TOKEN --path $INFISICAL_PATH --projectId $INFISICAL_PROJECT_ID --env $INFISICAL_SECRET_ENV --domain $INFISICAL_API_URL -- "$@"

fi

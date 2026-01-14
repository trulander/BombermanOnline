#!/bin/bash
set -e

echo "Ожидание запуска PostgreSQL..."
sleep 5  # Простая задержка для ожидания запуска PostgreSQL

echo "Применяем миграции..."
cd /app/auth-service/app
uv run alembic upgrade head


echo "Запускаем приложение..."
cd ..
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 5003
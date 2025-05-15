#!/bin/bash
set -e

echo "Ожидание запуска PostgreSQL..."
sleep 5  # Простая задержка для ожидания запуска PostgreSQL

echo "Применяем миграции..."
uv run alembic upgrade head

echo "Запускаем приложение..."
exec uv run uvicorn auth-service.app.main:app --host 0.0.0.0 --port 5003 
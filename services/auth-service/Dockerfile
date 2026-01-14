FROM python:3.12-slim

# Установка рабочей директории
WORKDIR /app

# Установка UV
RUN pip install --no-cache-dir uv

# Копирование файлов зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv sync

## Копирование кода приложения
#COPY app/ ./app/

## Создание директорий для приложения
RUN mkdir -p ./app/templates ./app/static

## Копирование файлов для миграций
#COPY migrations/script.py.mako ./migrations/
#COPY alembic.ini ./

# Порт, который будет слушать приложение
#EXPOSE 5003

#CMD ["uv", "run", "uvicorn", "auth-service.app.main:app", "--host", "0.0.0.0", "--port", "5003"]

WORKDIR /app/auth-service

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
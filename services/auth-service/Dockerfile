FROM python:3.12-slim

# Установка рабочей директории
WORKDIR /app

# Установка UV
RUN pip install --no-cache-dir uv

# Копирование файлов зависимостей
COPY pyproject.toml ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv sync

## Копирование кода приложения
#COPY app/ ./app/

# Создание директорий для приложения
RUN mkdir -p ./app/templates ./app/static ./migrations/versions ./scripts

# Копирование файлов для миграций
COPY migrations/script.py.mako ./migrations/
COPY alembic.ini ./

# Порт, который будет слушать приложение
EXPOSE 5003

# Скрипт запуска с применением миграций
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Запуск приложения с применением миграций
CMD ["./docker-entrypoint.sh"]
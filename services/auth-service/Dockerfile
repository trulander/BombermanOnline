FROM python:3.12-slim

# Установка рабочей директории
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && curl -1sLf https://artifacts-cli.infisical.com/setup.deb.sh | bash \
    && apt-get update \
    && apt-get install -y infisical \
#    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/*

# Установка UV
RUN pip install --no-cache-dir uv

# Копирование файлов зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv pip install --no-cache-dir --system -e .
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

RUN groupadd -g 1000 appuser && useradd -m -u 1000 -g 1000 appuser
USER appuser

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5003"]
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        curl \
        ca-certificates \
    && curl -1sLf https://artifacts-cli.infisical.com/setup.deb.sh | bash \
    && apt-get update \
    && apt-get install -y infisical \
#    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/*


# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Установка зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv pip install --no-cache-dir --system -e .
RUN uv sync

# Создаем директорию для логов
RUN mkdir -p /app/logs

WORKDIR /app/game-service

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
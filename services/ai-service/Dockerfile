FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        swig \
        build-essential \
        cmake \
        curl \
        ca-certificates \
    && curl -1sLf https://artifacts-cli.infisical.com/setup.deb.sh | bash \
    && apt-get update \
    && apt-get install -y infisical \
#    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/*


RUN pip install uv

# Копируем pyproject.toml и uv.lock для установки зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync

# Копируем остальной код приложения
COPY app ./app

# Открываем порт, если ai-service будет иметь HTTP API (опционально, если только NATS)
# EXPOSE 5004

# Команда для запуска приложения
#CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5004"]

WORKDIR /app/ai-service

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
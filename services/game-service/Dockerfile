FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей для PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Установка зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv pip install --no-cache-dir --system -e .
RUN uv sync
## Копируем исходный код
#COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

WORKDIR /app/game-service
# Запускаем приложение
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]
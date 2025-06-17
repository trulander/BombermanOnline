FROM python:3.9-slim

WORKDIR /app

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Установка зависимостей
COPY pyproject.toml ./

# Устанавливаем зависимости через uv (с флагом --system)
#RUN uv pip install --no-cache-dir --system -e .
RUN uv sync


CMD ["uv", "run", "game-allocator-service/app/main.py"]
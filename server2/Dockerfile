FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
COPY ../pyproject.toml ../uv.lock /app/
RUN pip install --no-cache-dir uv && \
    uv pip install --system

# Копирование исходного кода
COPY . /app/server2
WORKDIR /app/server2

# Запуск сервера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"] 
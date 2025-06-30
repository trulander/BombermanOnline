FROM python:3.12-slim-bookworm

WORKDIR /app

# Устанавливаем uv
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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5004"] 
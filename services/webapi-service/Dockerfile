FROM python:3.12-slim

WORKDIR /app

# Устанавливаем uv
RUN pip install --no-cache-dir uv

## Установка зависимостей
COPY pyproject.toml ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv pip install --no-cache-dir --system -e .
RUN uv sync
## Сделаем приложение доступным для запуска как дев-сервер
#VOLUME ["/app"]

## Запуск сервера
CMD ["uv", "run", "uvicorn", "webapi-service.app.main:app", "--host", "0.0.0.0", "--port", "5001"]
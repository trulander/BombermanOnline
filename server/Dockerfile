FROM python:3.12-slim

WORKDIR /app

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Копируем pyproject.toml и другие необходимые файлы
COPY ./pyproject.toml ./
COPY ./README.md ./

# Устанавливаем зависимости через uv (с флагом --system)
RUN uv pip install --no-cache-dir --system -e .

# Копируем остальные файлы сервера
COPY ./server ./server

EXPOSE 5000

CMD ["uv", "run", "server/app.py"]

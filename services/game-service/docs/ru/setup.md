[![English](https://img.shields.io/badge/lang-English-blue)](../en/setup.md)

# Установка и запуск Game Service

В этом разделе описаны шаги для установки зависимостей, настройки окружения и запуска Game Service.

## Требования

-   Python 3.12
-   UV (менеджер пакетов Python)
-   Docker (для запуска в контейнере или для зависимостей)
-   Доступ к экземплярам PostgreSQL, Redis, NATS.

## Установка зависимостей

Для установки зависимостей используется менеджер пакетов `uv`.

1.  **Установка UV (если не установлен):**
    ```bash
    pip install uv
    ```

2.  **Создание и активация виртуального окружения (рекомендуется):**
    В корневой директории `services/game-service`:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # для Linux/macOS
    # .venv\Scripts\activate    # для Windows
    ```

3.  **Установка зависимостей проекта:**
    Находясь в директории `services/game-service` (с активированным `.venv`):
    ```bash
    uv sync .
    ```
    Эта команда установит все зависимости, указанные в `pyproject.toml`.

## Настройка окружения

Сервис настраивается с помощью переменных окружения. 

1.  Скопируйте файл-пример `.env-example` в новый файл `.env` в директории `services/game-service`:
    ```bash
    cp .env-example .env
    ```
2.  Отредактируйте файл `.env`, указав актуальные параметры подключения к PostgreSQL, Redis, NATS и другие необходимые настройки.

    **Ключевые переменные:**
    -   `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
    -   `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`
    -   `NATS_URL`
    -   `PORT` (порт, на котором будет запущен сервис, по умолчанию 5002)
    -   `LOG_LEVEL`, `LOG_FORMAT`

    Полный список переменных и их значения по умолчанию можно найти в `app/config.py`.

    Секреты также можно хранить в Infisical. Файл `.env-example` можно импортировать в Infisical как базовую конфигурацию. Для запуска в Docker передайте переменные `INFISICAL_*` и укажите `INFISICAL_PATH` для сервиса.

## Миграции базы данных

Перед первым запуском приложения или после изменений моделей базы данных необходимо применить миграции Alembic.

Из директории `services/game-service`:
```bash
uv run python app/manage.py migrate
```

Для создания новых миграций после изменения моделей `MapTemplateORM`, `MapGroupORM`, `MapChainORM` в `app/models/map_models.py`:
```bash
uv run python app/manage.py makemigrations "<название_миграции>"
```

## Запуск сервиса

### Для разработки (локально)

1.  Убедитесь, что все зависимые сервисы (PostgreSQL, Redis, NATS) запущены и доступны согласно настройкам в `.env`.
2.  Примените миграции (см. выше).
3.  Запустите приложение с помощью Uvicorn для автоматической перезагрузки при изменениях кода:
    Из директории `services/game-service`:
    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5002} --reload
    ```
    (где `${PORT:-5002}` использует значение из `.env` или 5002 по умолчанию).

    Сервис будет доступен по адресу `http://localhost:<PORT>`. API документация (Swagger UI) будет по адресу `http://localhost:<PORT>/games/docs`.

### С использованием Docker

Подробные инструкции по сборке и запуску Docker-образа приведены в основном [README.md](../../README_RU.md) сервиса.

**Основные шаги:**

1.  **Сборка образа:**
    В директории `services/game-service`:
    ```bash
    docker build -t bomberman-game-service .
    ```

2.  **Запуск контейнера:**
    Необходимо передать переменные окружения, например, через `--env-file` или индивидуально через `-e`. В Docker-режиме секреты подставляются через Infisical, поэтому передайте переменные `INFISICAL_*` и укажите `INFISICAL_PATH`.
    ```bash
    docker run -p 5002:5002 --env-file .env bomberman-game-service
    ```
    Убедитесь, что Docker-контейнер имеет доступ к PostgreSQL, Redis и NATS (например, они находятся в одной Docker-сети, и хосты в `.env` указаны соответственно).

### C использованием Docker Compose (Рекомендуется для комплексного запуска)

Для управления всеми сервисами проекта (включая Game Service, базы данных, NATS и т.д.) рекомендуется использовать `docker-compose.yml` из корневой директории проекта `BombermanOnline`. Это упрощает запуск и управление межсервисными зависимостями.

Если `docker-compose.yml` настроен правильно, вы можете запустить все сервисы командой:
```bash
docker-compose up -d
```
Чтобы запустить только game-service (если он определен как сервис в `docker-compose.yml`):
```bash
docker-compose up -d game-service
```
Конфигурация для Game Service в `docker-compose.yml` должна включать сборку из его `Dockerfile` и передачу необходимых переменных окружения, а также настройку сети.
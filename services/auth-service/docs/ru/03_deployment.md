# 3. Развертывание и запуск

[![English](https://img.shields.io/badge/lang-English-blue)](../en/03_deployment.md)

Сервис может быть запущен как в Docker-контейнере, так и локально для разработки.

## Запуск с использованием Docker (рекомендуемый способ)

Сборка и запуск сервиса в Docker является предпочтительным способом для production и staging окружений.

1.  **Сборка Docker-образа:**

    Находясь в корневой директории сервиса (`auth-service`), выполните команду:

    ```bash
    docker build -t auth-service .
    ```

2.  **Запуск контейнера:**

    Запустите контейнер, пробросив порт `5003` и передав необходимые переменные окружения.

    ```bash
    docker run -p 5003:5003 \
      -e POSTGRES_HOST=your_postgres_host \
      -e POSTGRES_USER=your_user \
      -e POSTGRES_PASSWORD=your_password \
      -e SECRET_KEY=your_super_secret_key \
      auth-service
    ```

    В Docker-режиме секреты подставляются через Infisical. Передайте переменные доступа к Infisical и укажите `INFISICAL_PATH` для сервиса. Файл `services/auth-service/.env-example` можно импортировать в Infisical как базовую конфигурацию.

    Необходимые переменные:
    - `INFISICAL_MACHINE_CLIENT_ID`
    - `INFISICAL_MACHINE_CLIENT_SECRET`
    - `INFISICAL_PROJECT_ID`
    - `INFISICAL_SECRET_ENV`
    - `INFISICAL_API_URL`
    - `INFISICAL_PATH`

    > **Примечание:** Полный список переменных окружения смотрите в разделе [Конфигурация](./04_configuration.md).

## Локальный запуск для разработки

Для разработки и отладки сервис можно запустить локально.

1.  **Установка зависимостей:**

    Рекомендуется использовать `uv` для создания виртуального окружения и установки пакетов.

    ```bash
    # Создать и активировать виртуальное окружение
    python -m venv .venv
    source .venv/bin/activate

    # Установить зависимости
    # Установить зависимости из pyproject.toml
    uv pip install -e .
    ```

2.  **Настройка переменных окружения:**

    Создайте файл `.env` в корневой директории проекта и укажите в нем необходимые переменные (см. [Конфигурация](./04_configuration.md)) или используйте Infisical, передав переменные `INFISICAL_*`.

3.  **Применение миграций:**

    Перед первым запуском необходимо применить миграции к базе данных.

    ```bash
    alembic upgrade head
    ```

4.  **Запуск приложения:**

    Выполните команду из корневой директории проекта:

    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 5003 --reload
    ```

    Флаг `--reload` автоматически перезапустит сервер при изменении кода.
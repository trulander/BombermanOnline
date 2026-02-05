# Auth Service - Bomberman Online

[![English](https://img.shields.io/badge/lang-English-blue)](README.md)

Сервис авторизации и управления пользователями для игры Bomberman Online.

Это основной сервис, отвечающий за регистрацию, аутентификацию, управление профилями и ролями пользователей.

## Подробная документация

Вся подробная документация по архитектуре, API, развертыванию и настройке была перенесена в директорию `docs/ru`. 


- [1. Обзор сервиса](./docs/ru/01_overview.md)
- [2. Используемые технологии](./docs/ru/02_technologies.md)
- [3. Развертывание и запуск](./docs/ru/03_deployment.md)
- [4. Конфигурация](./docs/ru/04_configuration.md)
- [5. API и Frontend Эндпоинты](./docs/ru/05_api_endpoints.md)
- [6. Модели Базы Данных](./docs/ru/06_database.md)
- [7. Управление миграциями](./docs/ru/07_migrations.md)
- [8. Архитектура и логика работы](./docs/ru/08_architecture.md)

## Управление секретами

Секреты хранятся в Infisical. Файл `.env-example` содержит все доступные переменные и может быть импортирован в Infisical как базовая конфигурация. Docker entrypoint входит в Infisical и запускает сервис с подставленными переменными окружения.

## Используемые технологии

- **Python 3.12**
- **FastAPI**
- **PostgreSQL (SQLAlchemy & Alembic)**
- **Redis**
- **JWT (python-jose)**
- **OAuth 2.0**
- **Jinja2 Templates**
- **Docker**
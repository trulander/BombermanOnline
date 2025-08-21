# PostgreSQL
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/postgres/index.md)

## Назначение в проекте

**PostgreSQL** — это основная реляционная база данных в проекте, используемая для **постоянного хранения данных**.

-   **`auth-service`**: хранит данные пользователей, ролей, сессий.
-   **`game-service`**: хранит информацию о завершенных играх, статистику игроков, шаблоны карт и т.д.

## Конфигурация

Сервис `postgres` определен в `infra/docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-bomberman}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-bomberman}
      - POSTGRES_DB=${POSTGRES_DB:-bomberman}
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

-   **`image`**: `postgres:15-alpine`.
-   **`ports`**: `5432:5432` - стандартный порт PostgreSQL.
-   **`environment`**: Задают имя пользователя, пароль и имя базы данных по умолчанию.
-   **`volumes`**: `postgres_data` - том для сохранения данных между перезапусками.

## Доступ

-   Прямой доступ к базе данных возможен по порту `5432` с хост-машины. Через Traefik не маршрутизируется.

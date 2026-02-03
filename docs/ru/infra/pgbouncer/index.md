# PgBouncer
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/pgbouncer/index.md)

## Назначение в проекте

**PgBouncer** — это легковесный пул соединений для **PostgreSQL**. Он располагается между сервисами и базой данных, чтобы **уменьшить накладные расходы на соединения** и **стабилизировать нагрузку на БД**.

## Конфигурация

Сервис `pgbouncer` определен в `infra/docker-compose.yml`:

```yaml
services:
  pgbouncer:
    container_name: pgbouncer
    image: edoburu/pgbouncer:v1.25.1-p0
    environment:
      - DB_USER=${POSTGRES_USER:-bomberman}
      - DB_PASSWORD=${POSTGRES_PASSWORD:-bomberman}
      - DB_HOST=postgres
      - POOL_MODE=transaction
      - MAX_CLIENT_CONN=1000
      - DEFAULT_POOL_SIZE=25
      - RESERVE_POOL_SIZE=5
      - SERVER_IDLE_TIMEOUT=60
      - AUTH_TYPE=scram-sha-256
      - ADMIN_USERS=bomberman,postgres,dbuser
    ports:
      - "5432:5432"
    depends_on:
      - postgres
```

-   **`image`**: `edoburu/pgbouncer:v1.25.1-p0`.
-   **`ports`**: `5432:5432` - входной порт для подключений к базе данных.
-   **`environment`**: учетные данные, параметры пула и режим аутентификации.

## Взаимодействие с другими сервисами

-   Сервисы приложений должны подключаться к базе данных через хост `pgbouncer` и порт `5432`.
-   PgBouncer подключается к PostgreSQL через хост `postgres` и порт `5432`.

## Доступ

-   Прямой доступ с хоста осуществляется через порт `5432` и обслуживается PgBouncer.
-   PostgreSQL напрямую не экспонируется.

## Схема

См. `docs/ru/examples/infra-postgres-pgbouncer.md`.


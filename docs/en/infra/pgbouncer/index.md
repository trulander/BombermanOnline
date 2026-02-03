# PgBouncer
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/pgbouncer/index.md)

## Purpose in the Project

**PgBouncer** is a lightweight connection pooler for **PostgreSQL**. It sits between the services and the database to **reduce connection overhead** and **stabilize database load**.

## Configuration

The `pgbouncer` service is defined in `infra/docker-compose.yml`:

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
-   **`ports`**: `5432:5432` - the entry port for database connections.
-   **`environment`**: database credentials, pool settings, and authentication mode.

## Interaction with Other Services

-   Application services should connect to the database via host `pgbouncer` and port `5432`.
-   PgBouncer connects to PostgreSQL via host `postgres` and port `5432`.

## Access

-   Direct access from the host is available on port `5432` and is handled by PgBouncer.
-   PostgreSQL itself is not exposed directly.

## Diagram

See `docs/en/examples/infra-postgres-pgbouncer.md`.


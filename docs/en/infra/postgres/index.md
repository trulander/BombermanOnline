# PostgreSQL
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/postgres/index.md)

## Purpose in the Project

**PostgreSQL** is the primary relational database in the project, used for **persistent data storage**. Database connections are handled through **PgBouncer**, which sits in front of PostgreSQL.

-   **`auth-service`**: stores user data, roles, and sessions.
-   **`game-service`**: stores information about completed games, player statistics, map templates, etc.

## Configuration

The `postgres` service is defined in `infra/docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-bomberman}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-bomberman}
      - POSTGRES_DB=${POSTGRES_DB:-bomberman}
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

-   **`image`**: `postgres:15-alpine`.
-   **`environment`**: Define the default username, password, and database name.
-   **`volumes`**: `postgres_data` - a volume to persist data across restarts.

## Connection Flow

-   Application services connect to PgBouncer.
-   PgBouncer forwards pooled connections to PostgreSQL.

## Access

-   Direct access from the host is available on port `5432` through PgBouncer.
-   PostgreSQL itself is not exposed directly.

## Diagram

See `docs/en/examples/infra-postgres-pgbouncer.md`.

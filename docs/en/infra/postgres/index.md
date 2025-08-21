# PostgreSQL
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/postgres/index.md)

## Purpose in the Project

**PostgreSQL** is the primary relational database in the project, used for **persistent data storage**.

-   **`auth-service`**: stores user data, roles, and sessions.
-   **`game-service`**: stores information about completed games, player statistics, map templates, etc.

## Configuration

The `postgres` service is defined in `infra/docker-compose.yml`:

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
-   **`ports`**: `5432:5432` - the standard PostgreSQL port.
-   **`environment`**: Define the default username, password, and database name.
-   **`volumes`**: `postgres_data` - a volume to persist data across restarts.

## Access

-   Direct access to the database is available on port `5432` from the host machine. It is not routed through Traefik.

# Infisical
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/infisical/index.md)

## Purpose in the Project

**Infisical** is the central secrets manager for the project. All services fetch secrets at startup using the Infisical CLI and run with the injected environment variables.

Each service includes a `.env-example` file that lists all available environment variables. These files can be imported into Infisical to create the base configuration for a service.

## Configuration from docker-compose.yml

```yaml
services:
  infisical:
    image: infisical/infisical:v0.158.0
    depends_on:
      - pgbouncer
      - redis
    expose:
      - "8080"
    environment:
      - NODE_ENV=development
      - ENCRYPTION_KEY=<your_key>
      - AUTH_SECRET=<your_secret>
      - DB_CONNECTION_URI=postgresql://<user>:<password>@pgbouncer:5432/infisical
      - REDIS_URL=redis://redis:6379
      - SITE_URL=http://infisical.localhost:3000
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.infisical.loadbalancer.server.port=8080"
      - "traefik.http.routers.infisical.rule=Host(`infisical.localhost`)"
```

## Required Variables for Service Startup

Each service is started via an entrypoint script that calls Infisical. The following variables are required:

- `INFISICAL_MACHINE_CLIENT_ID`
- `INFISICAL_MACHINE_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_SECRET_ENV`
- `INFISICAL_API_URL`
- `INFISICAL_PATH`

`INFISICAL_PATH` points to the folder inside a service path from which secrets are loaded in that case when the secrest sorted by dirrectories. (for example, `/auth-service`).

## Access

- **Infisical UI**: `http://infisical.localhost:3000`
- **Internal API**: `http://infisical:8080`


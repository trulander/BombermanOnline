# Infisical
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/infisical/index.md)

## Назначение в проекте

**Infisical** используется как централизованное хранилище секретов. Все сервисы получают секреты при запуске через Infisical CLI и работают с переданными переменными окружения.

В каждом сервисе есть файл `.env-example` со списком всех доступных переменных окружения. Эти файлы можно импортировать в Infisical, чтобы создать базовую конфигурацию для сервиса.

## Конфигурация из docker-compose.yml

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

## Переменные, необходимые для запуска сервисов

Каждый сервис стартует через entrypoint-скрипт, который вызывает Infisical. Для этого требуются:

- `INFISICAL_MACHINE_CLIENT_ID`
- `INFISICAL_MACHINE_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_SECRET_ENV`
- `INFISICAL_API_URL`
- `INFISICAL_PATH`

`INFISICAL_PATH` указывает папку внутри пути сервиса, из которой берутся секреты в том случае если секреты сортируются по папкам. (например, `/auth-service`).

## Доступ

- **Infisical UI**: `http://infisical.localhost:3000`
- **Внутренний API**: `http://infisical:8080`


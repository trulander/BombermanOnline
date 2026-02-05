# Traefik
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/traefik/index.md)

## Назначение в проекте

**Traefik** — это API Gateway и обратный прокси, который служит единой точкой входа для всех HTTP-запросов в систему. Он отвечает за маршрутизацию запросов к соответствующим микросервисам, управление SSL-сертификатами (в production) и применение middleware.

## Конфигурация из docker-compose.yml

```yaml
services:
  traefik:
    image: traefik:3.6.6
    ports:
      - "3000:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml
      - ./traefik/middlewares.yml:/etc/traefik/middlewares.yml
      - ./traefik/routers.yml:/etc/traefik/routers.yml
      - ./traefik/logs:/var/log/traefik
      - ./traefik/traefik_plugins:/plugins-storage
      - ./traefik/local-plugins:/plugins-local/src
    command:
      - "--configFile=/etc/traefik/traefik.yml"
    labels:
      - "traefik.enable=true"
```

-   **`image`**: `traefik:3.6.6` - Используемый образ Traefik.
-   **`ports`**: Пробрасываются порты `3000` (для HTTP-трафика) и `8080` (для дашборда) на хост-машину.
-   **`volumes`**:
    -   `/var/run/docker.sock`: Позволяет Traefik автоматически обнаруживать другие контейнеры.
    -   `./traefik/...`: Монтируются все необходимые конфигурационные файлы (основной, middleware, роутеры) и директории для логов и плагинов.
-   **`command`**: Указывает Traefik использовать основной конфигурационный файл `traefik.yml`.
-   **`labels`**: `traefik.enable=true` включает обработку самого Traefik для доступа к его дашборду.

## Взаимодействие с другими сервисами

-   **Providers**: Traefik использует три провайдера для обнаружения маршрутов: `docker` (для сервисов с лейблами), `file` (для чтения `routers.yml` и `middlewares.yml`) и `consulCatalog` (для сервисов, зарегистрированных в Consul).
-   **Auth Service**: Использует `auth-service` через middleware `auth-check` для защиты эндпоинтов. Traefik перенаправляет запрос на `auth-service`, и если тот возвращает статус `200 OK`, запрос пропускается дальше.
-   **Локальный плагин `extractCookie`**: Используется для авторизации WebSocket-соединений. Он извлекает токен из cookie `ws_auth_token` и помещает его в заголовок `Authorization`.
-   **Микросервисы**: Маршрутизирует запросы ко всем публичным сервисам (`web-frontend`, `webapi-service`, `auth-service` и др.) согласно правилам в `routers.yml`.
-   **Infisical**: Маршрутизирует UI Infisical по правилу хоста `infisical.localhost`.

## Маршрутизируемые сервисы (Traefik)

Следующие маршруты настроены в `infra/traefik/routers.yml`:

-   **Web Frontend**: `/`
-   **WebAPI REST**: `/webapi`
-   **WebAPI WebSocket**: `/webapi/socket.io`
-   **WebAPI Docs**: `/webapi/docs`
-   **Auth Service**: `/auth`
-   **Auth Docs**: `/auth/docs`
-   **Game Service REST**: `/games`
-   **Game Service Docs**: `/games/docs`
-   **Game Service gRPC**: `/games/grpc`
-   **AI Service gRPC**: `/ai/grpc`
-   **Сбор логов**: `/logs` (Fluent Bit logger API)
-   **Grafana**: `/grafana`
-   **pgAdmin**: `/pgadmin`
-   **Traefik Dashboard**: `traefik.localhost`
-   **Infisical UI**: `infisical.localhost`

Следующие маршруты настроены через Docker labels в `infra/docker-compose.yml`:

-   **Prometheus**: `prometheus.localhost`

## Доступ

-   **Основной сайт**: `http://localhost/`
-   **WebAPI**: `http://localhost/webapi/`
-   **WebAPI Docs**: `http://localhost/webapi/docs`
-   **Auth**: `http://localhost/auth/`
-   **Auth Docs**: `http://localhost/auth/docs`
-   **Game Service**: `http://localhost/games/`
-   **Game Service Docs**: `http://localhost/games/docs`
-   **Grafana**: `http://localhost/grafana`
-   **pgAdmin**: `http://localhost/pgadmin`
-   **Prometheus**: `http://prometheus.localhost`
-   **Logs**: `http://localhost/logs`
-   **Infisical UI**: `http://infisical.localhost:3000`
-   **Дашборд Traefik**: `http://traefik.localhost` (также доступен по `http://localhost:8080`).

# Traefik
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/traefik/index.md)

## Назначение в проекте

**Traefik** — это современный **API Gateway** и **обратный прокси (Reverse Proxy)**, который служит единой точкой входа для всех HTTP-запросов в систему.

Ключевые функции в проекте:
1.  **Маршрутизация запросов**: Traefik автоматически обнаруживает запущенные сервисы и направляет входящие запросы на нужный контейнер на основе правил, определенных в `infra/traefik/routers.yml`.
2.  **Интеграция с Consul**: Использует `consulCatalog` для обнаружения сервисов, зарегистрированных в Consul.
3.  **Middleware**: Применяет к запросам промежуточные обработчики, настроенные в `infra/traefik/middlewares.yml`. Это включает в себя добавление заголовков безопасности, сжатие, а также проверку аутентификации.
4.  **Проверка аутентификации**: С помощью middleware `auth-check` перенаправляет запросы на `auth-service` для проверки JWT-токена перед доступом к защищенным ресурсам.
5.  **Авторизация WebSocket**: Использует локальный плагин `extractCookie` для извлечения `ws_auth_token` из cookie и передачи его в заголовке `Authorization` для аутентификации WebSocket-соединений.

## Конфигурация

Основная конфигурация Traefik разделена на несколько файлов в директории `infra/traefik/`:

-   **`traefik.yml`**: Основной статический конфигурационный файл. Определяет точки входа (`web`), провайдеры (`docker`, `file`, `consulCatalog`), настройки логов и включает дашборд.
-   **`routers.yml`**: Динамическая конфигурация, определяющая правила маршрутизации (`rule`) для каждого эндпоинта, используемые `entryPoints` и цепочки `middlewares`.
-   **`middlewares.yml`**: Определяет все используемые middleware.

### Основные маршруты (`routers.yml`)

-   `/auth/**`: Маршруты к `auth-service`.
-   `/webapi/**`: Маршруты к `webapi-service` (защищены `auth-check`).
-   `/webapi/socket.io`: Маршрут для WebSocket, использует `extract-cookie-ws_auth_token` и `auth-check`.
-   `/games/**`: Маршруты к `game-service` (защищены `auth-check`).
-   `/logs`: Маршрут для приема логов от фронтенда, перенаправляется на `fluent-bit`.
-   `/`: Все остальные запросы направляются на `web-frontend`.

### Ключевые Middlewares (`middlewares.yml`)

-   `security-headers`: Добавляет стандартные заголовки безопасности.
-   `compress`: Включает GZIP-сжатие.
-   `auth-check`: `forwardAuth` на эндпоинт `http://auth-service:5003/auth/api/v1/auth/check` для валидации токена.
-   `extract-cookie-ws_auth_token`: Локальный плагин, который берет cookie `ws_auth_token` и преобразует его в заголовок `Authorization: Bearer <token>`.

## Доступ через Traefik

-   **Основной сайт**: `http://localhost/`
-   **API сервисы**: `http://localhost/auth/`, `http://localhost/webapi/`, `http://localhost/games/`
-   **Дашборд Traefik**: `http://traefik.localhost` (согласно `routers.yml`, также доступен по `http://localhost:8080` из `docker-compose.yml`).

# Consul
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/consul/index.md)

## Назначение в проекте

**Consul** используется в проекте как ключевой компонент для **обнаружения сервисов (Service Discovery)**.

Микросервисы (`webapi-service`, `game-service`, `auth-service`, `game-allocator-service`, `ai-service` и др.) при запуске регистрируются в Consul. Это позволяет им находить друг друга по имени сервиса (например, `auth-service`) вместо жестко прописанных IP-адресов, что критически важно для распределенной системы. Traefik также использует Consul (`consulCatalog` provider) для динамического обнаружения бэкендов.

Все сервисы регистрируются в Consul с HTTP healthcheck endpoints (например, `/health`), что позволяет Consul автоматически проверять работоспособность инстансов и исключать неработающие из доступных.

## Конфигурация

Сервис `consul` определен в файле `infra/docker-compose.yml`:

```yaml
services:
  consul:
    image: hashicorp/consul:1.21
    ports:
      - "8500:8500"      # HTTP UI и API
      - "8600:8600/udp"  # DNS-интерфейс
    command: "agent -server -bootstrap-expect=1 -ui -client=0.0.0.0"
```

-   **`image`**: `hashicorp/consul:1.21`.
-   **`ports`**:
    -   `8500:8500`: Веб-интерфейс и HTTP API.
    -   `8600:8600/udp`: DNS-порт для разрешения имен сервисов.
-   **`command`**: Запускает Consul в режиме одиночного сервера с включенным UI.

## Доступ

-   **Веб-интерфейс Consul**: `http://localhost:8500`
-   Сервис не выставляется наружу через Traefik, так как является внутренним компонентом.

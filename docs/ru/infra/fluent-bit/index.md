# Fluent Bit
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/fluent-bit/index.md)

## Назначение

**Fluent Bit** — это легковесный и высокопроизводительный сборщик и пересыльщик логов. Он собирает логи из всех контейнеров, парсит их и отправляет в Loki.

## Конфигурация из docker-compose.yml

```yaml
services:
  fluent-bit:
    image: grafana/fluent-bit-plugin-loki:latest
    volumes:
      - ./fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
      - ./fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    ports:
      - "24224:24224"
      - "24224:24224/udp"
      - "2020:2020"
      - "8888:8888"
    environment:
      - LOKI_URL=http://loki.internal:3100/loki/api/v1/push
```

-   **`image`**: `grafana/fluent-bit-plugin-loki:latest` - образ с плагином для Loki.
-   **`volumes`**: Монтируются файлы конфигурации (`fluent-bit.conf`, `parsers.conf`) и сокет Docker для сбора метаданных контейнеров.
-   **`ports`**:
    -   `24224`: Принимает логи от Docker-контейнеров по протоколу `forward`.
    -   `8888`: Принимает логи от `web-frontend` по HTTP.
    -   `2020`: HTTP-сервер для мониторинга самого Fluent Bit.
-   **`environment.LOKI_URL`**: Указывает адрес Loki для отправки логов, используя внутреннее сетевое имя `loki.internal`.

## Взаимодействие с другими сервисами

-   **Docker**: Все микросервисы в `docker-compose.yml` имеют настройку `logging.driver: "fluentd"`, которая направляет их `stdout` и `stderr` в Fluent Bit.
-   **Loki**: Является единственным получателем (`output`) обработанных логов от Fluent Bit.
-   **Web Frontend**: Отправляет свои логи на порт `8888`.

## Доступ

-   Сервис является внутренним и не имеет прямого доступа через Traefik.

# Документация Docker Compose для Bomberman Online

Этот документ описывает сервисы, определенные в файле `infra/docker-compose.yml`, который управляет инфраструктурными компонентами и микросервисами проекта Bomberman Online.

## Содержание

- [Консул](#consul)
- [Сервис-аллокатор игр](#game-allocator-service)
- [Сервис WebAPI](#webapi-service)
- [Игровой сервис](#game-service)
- [Сервис аутентификации](#auth-service)
- [Веб-фронтенд](#web-frontend)
- [PostgreSQL](#postgresql)
- [Redis](#redis)
- [Экспортер Redis](#redis-exporter)
- [NATS](#nats)
- [Экспортер NATS для Prometheus](#prometheus-nats-exporter)
- [Traefik](#traefik)
- [Prometheus](#prometheus)
- [Node Exporter](#node-exporter)
- [cAdvisor](#cadvisor)
- [Loki](#loki)
- [Fluent Bit](#fluent-bit)
- [Grafana](#grafana)
- [Тома данных](#volumes)

---

<a name="consul"></a>
### Consul

**Описание:** Consul используется для обнаружения сервисов и хранения конфигурации.
**Образ:** `hashicorp/consul:1.21`
**Порты:**
- `8500:8500` (HTTP UI)
- `8600:8600/udp` (DNS)
**Команда запуска:** `agent -server -bootstrap-expect=1 -ui -client=0.0.0.0`
**Тома:** (закомментировано)
- `consul_data:/consul/data`

<a name="game-allocator-service"></a>
### Сервис-аллокатор игр (Game Allocator Service)

**Описание:** Микросервис, отвечающий за аллокацию игровых ресурсов.
**Сборка:** Из `../services/game-allocator-service`
**Переменные окружения:**
- `PYTHONUNBUFFERED=1`: Отключает буферизацию вывода Python.
- `REDIS_HOST=redis`: Хост Redis.
- `CONSUL_HTTP_ADDR=consul:8500`: Адрес HTTP API Consul.
- `PROMETHEUS_URL=http://prometheus:9090`: URL сервера Prometheus.
- `NATS_URL=nats://nats:4222`: URL сервера NATS.
- `CONSUL_HOST=consul`: Хост Consul для обнаружения сервисов.
- `LOG_LEVEL=DEBUG`: Уровень логирования.
- `LOG_FORMAT=json`: Формат логов.
**Тома:**
- `../services/game-allocator-service/app:/app/game-allocator-service/app`: Связывает локальную папку `app` сервиса с папкой в контейнере.
**Метки Traefik:**
- `traefik.enable=true`: Включает Traefik для этого сервиса.
**Логирование:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.game-allocator-service`

<a name="webapi-service"></a>
### Сервис WebAPI (WebAPI Service)

**Описание:** Основной API-сервис для взаимодействия с клиентом.
**Сборка:** Из `../services/webapi-service`
**Переменные окружения:**
- `PYTHONUNBUFFERED=1`: Отключает буферизацию вывода Python.
- `REDIS_HOST=redis`: Хост Redis.
- `NATS_URL=nats://nats:4222`: URL сервера NATS.
- `AUTH_SERVICE_URL=http://auth-service:5003`: URL сервиса аутентификации.
- `CONSUL_HOST=consul`: Хост Consul.
**Тома:**
- `../services/webapi-service/app:/app/webapi-service/app`: Связывает локальную папку `app` сервиса с папкой в контейнере.
- `webapi_logs:/var/log/webapi-service`: Том для логов сервиса.
**Порты:** (закомментировано)
- `5001:5001`
**Expose:**
- `5001`: Открывает порт внутри сети Docker.
**Метки Traefik:**
- `traefik.enable=true`: Включает Traefik для этого сервиса.
**Логирование:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.webapi-service`

<a name="game-service"></a>
### Игровой сервис (Game Service)

**Описание:** Сервис, управляющий игровой логикой.
**Сборка:** Из `../services/game-service`
**Переменные окружения:**
- `LOG_LEVEL=INFO`: Уровень логирования.
- `PYTHONUNBUFFERED=1`: Отключает буферизацию вывода Python.
- `REDIS_HOST=redis`: Хост Redis.
- `NATS_URL=nats://nats:4222`: URL сервера NATS.
- `AUTH_SERVICE_URL=http://auth-service:5003`: URL сервиса аутентификации.
- `POSTGRES_HOST=postgres`: Хост PostgreSQL.
- `POSTGRES_PORT=5432`: Порт PostgreSQL.
- `POSTGRES_DB=game_service`: Имя базы данных PostgreSQL.
- `POSTGRES_USER=bomberman`: Пользователь PostgreSQL.
- `POSTGRES_PASSWORD=bomberman`: Пароль PostgreSQL.
- `LOG_FORMAT=json`: Формат логов.
- `CONSUL_HOST=consul`: Хост Consul.
**Тома:**
- `../services/game-service/app:/app/game-service/app`: Связывает локальную папку `app` сервиса с папкой в контейнере.
- `game_logs:/var/log/game-service`: Том для логов сервиса.
**Порты:** (закомментировано)
- `5002:5002`
**Expose:**
- `5002`: Открывает порт внутри сети Docker.
**Метки Traefik:**
- `traefik.enable=true`: Включает Traefik для этого сервиса.
**Логирование:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.game-service`

<a name="auth-service"></a>
### Сервис аутентификации (Auth Service)

**Описание:** Сервис для управления пользователями и аутентификацией.
**Сборка:** Из `../services/auth-service`
**Переменные окружения:**
- `PYTHONUNBUFFERED=1`: Отключает буферизацию вывода Python.
- `REDIS_HOST=redis`: Хост Redis.
- `POSTGRES_HOST=postgres`: Хост PostgreSQL.
- `POSTGRES_PORT=5432`: Порт PostgreSQL.
- `POSTGRES_DB=auth_service`: Имя базы данных PostgreSQL.
- `POSTGRES_USER=bomberman`: Пользователь PostgreSQL.
- `POSTGRES_PASSWORD=bomberman`: Пароль PostgreSQL.
- `SECRET_KEY=${AUTH_SECRET_KEY:-your_secret_key_here}`: Секретный ключ для JWT. Значение по умолчанию используется, если переменная не задана.
- `CONSUL_HOST=consul`: Хост Consul.
**Тома:**
- `../services/auth-service/app:/app/auth-service/app`: Связывает локальную папку `app` сервиса с папкой в контейнере.
- `auth_logs:/var/log/auth-service`: Том для логов сервиса.
**Порты:** (закомментировано)
- `5003:5003`
**Expose:**
- `5003`: Открывает порт внутри сети Docker.
**Метки Traefik:**
- `traefik.enable=true`: Включает Traefik для этого сервиса.
**Логирование:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.auth-service`

<a name="web-frontend"></a>
### Веб-фронтенд (Web Frontend)

**Описание:** Клиентское веб-приложение.
**Сборка:** Из `../services/web-frontend`
**Порты:**
- `3000:3000`: Маппинг порта контейнера на хост.
**Тома:**
- `../services/web-frontend/public:/app/public`: Связывает локальную папку `public` с папкой в контейнере.
- `../services/web-frontend/src:/app/src`: Связывает локальную папку `src` с папкой в контейнере.
**Переменные окружения:**
- `NODE_ENV=production`: Режим окружения Node.js.
- `REACT_APP_LOGS_ENDPOINT=/logs`: Эндпоинт для отправки логов.
- `REACT_APP_SERVICE_NAME=web-frontend`: Имя сервиса для логирования.
- `REACT_APP_SOCKET_URL=http://localhost`: URL для WebSocket-соединений.
- `REACT_APP_SOCKET_PATH=/webapi/socket.io`: Путь для WebSocket-соединений.
- `PORT=3000`: Порт, на котором работает приложение в контейнере.
- `REACT_APP_LOGS_BATCH_SIZE=10`: Размер пачки логов для отправки.
- `AUTH_URL=/auth`: Базовый URL для аутентификации.
**Метки Traefik:**
- `traefik.enable=true`: Включает Traefik для этого сервиса.

<a name="postgresql"></a>
### PostgreSQL

**Описание:** База данных PostgreSQL для хранения постоянных данных.
**Образ:** `postgres:15-alpine`
**Порты:**
- `5432:5432`: Маппинг порта базы данных.
**Переменные окружения:**
- `POSTGRES_USER=${POSTGRES_USER:-bomberman}`: Имя пользователя для базы данных.
- `POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-bomberman}`: Пароль пользователя для базы данных.
- `POSTGRES_DB=${POSTGRES_DB:-bomberman}`: Имя базы данных по умолчанию.
**Тома:**
- `postgres_data:/var/lib/postgresql/data`: Том для хранения данных базы данных.

<a name="redis"></a>
### Redis

**Описание:** In-memory хранилище данных, используемое для кэширования и временных состояний.
**Образ:** `redis:7.2`
**Порты:**
- `6379:6379`: Маппинг порта Redis.
**Тома:**
- `redis_data:/data`: Том для хранения данных Redis.

<a name="redis-exporter"></a>
### Экспортер Redis (Redis Exporter)

**Описание:** Экспортер метрик Redis для Prometheus.
**Образ:** `oliver006/redis_exporter:v1.55.0`
**Переменные окружения:**
- `REDIS_ADDR: redis://redis:6379`: Адрес Redis.
**Порты:**
- `9121:9121`: Порт, на котором экспортер предоставляет метрики.

<a name="nats"></a>
### NATS

**Описание:** Распределенная система обмена сообщениями, используемая для межсервисной коммуникации.
**Образ:** `nats:2.10`
**Порты:**
- `4222:4222` (клиентский порт)
- `8222:8222` (мониторинг)
**Тома:**
- `nats_data:/data`: Том для хранения данных NATS.

<a name="prometheus-nats-exporter"></a>
### Экспортер NATS для Prometheus (Prometheus NATS Exporter)

**Описание:** Экспортер метрик NATS для Prometheus.
**Образ:** `natsio/prometheus-nats-exporter:latest`
**Команда запуска:** `-varz -connz -subz -routez -gatewayz -healthz -accstatz -leafz -jsz=all http://nats:8222`
**Порты:**
- `7777:7777`: Порт, на котором экспортер предоставляет метрики.

<a name="traefik"></a>
### Traefik

**Описание:** API Gateway и балансировщик нагрузки.
**Образ:** `traefik:3.4.0`
**Порты:**
- `80:80` (HTTP)
- `8080:8080` (Веб-интерфейс Traefik Dashboard)
**Тома:**
- `/var/run/docker.sock:/var/run/docker.sock:ro`: Для обнаружения сервисов Docker.
- `./traefik/traefik.yml:/etc/traefik/traefik.yml`: Конфигурационный файл Traefik.
- `./traefik/middlewares.yml:/etc/traefik/middlewares.yml`: Конфигурация промежуточного ПО.
- `./traefik/routers.yml:/etc/traefik/routers.yml`: Конфигурация маршрутизаторов.
- `./traefik/logs:/var/log/traefik`: Том для логов Traefik.
- `./traefik/traefik_plugins:/plugins-storage`: Для плагинов Traefik.
- `./traefik/local-plugins:/plugins-local/src`: Для локальных плагинов разработки.
**Команда запуска:** `--configFile=/etc/traefik/traefik.yml`
**Метки Traefik:**
- `traefik.enable=true`: Включает Traefik для самого Traefik Dashboard.

<a name="prometheus"></a>
### Prometheus

**Описание:** Система мониторинга и сбора метрик.
**Образ:** `prom/prometheus:v2.49.1`
**Порты:**
- `9090:9090`
**Метки Traefik:**
- `traefik.enable=true`
- `traefik.http.routers.prometheus.rule=Host(`prometheus.localhost`)`
- `traefik.http.services.prometheus.loadbalancer.server.port=9090`
**Тома:**
- `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml`
- `prometheus_data:/prometheus`
**Команда запуска:**
- `--config.file=/etc/prometheus/prometheus.yml`
- `--storage.tsdb.path=/prometheus`
- `--web.console.libraries=/etc/prometheus/console_libraries`
- `--web.console.templates=/etc/prometheus/consoles`
- `--web.enable-lifecycle`

<a name="node-exporter"></a>
### Node Exporter

**Описание:** Экспортер метрик системы (CPU, RAM, дисковое пространство) для Prometheus.
**Образ:** `prom/node-exporter:v1.7.0`
**Порты:**
- `9100:9100`
**Тома:**
- `/proc:/host/proc:ro`
- `/sys:/host/sys:ro`
- `/:/rootfs:ro`
**Команда запуска:**
- `--path.procfs=/host/proc`
- `--path.rootfs=/rootfs`
- `--path.sysfs=/host/sys`
- `--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)$`

<a name="cadvisor"></a>
### cAdvisor

**Описание:** Агент для сбора метрик использования ресурсов контейнеров.
**Образ:** `gcr.io/cadvisor/cadvisor:v0.47.2`
**Порты:**
- `8081:8080`
**Тома:**
- `/:/rootfs:ro`
- `/var/run:/var/run:ro`
- `/sys:/sys:ro`
- `/var/lib/docker/:/var/lib/docker:ro`
- `/dev/disk/:/dev/disk:ro`

<a name="loki"></a>
### Loki

**Описание:** Горизонтально масштабируемая, высокодоступная, мультиарендная система агрегации логов, вдохновленная Prometheus.
**Образ:** `grafana/loki:3.5.0`
**Порты:**
- `3100:3100`
**Тома:**
- `./loki/loki-config.yml:/etc/loki/local-config.yaml`
- `loki_data:/loki`
**Команда запуска:** `-config.file=/etc/loki/local-config.yaml -target=all -log.level=info`
**Сети:**
- `default: aliases: - loki.internal`

<a name="fluent-bit"></a>
### Fluent Bit

**Описание:** Легкий и высокопроизводительный процессор и форвардер логов, метрик и трассировок. Используется для отправки логов Docker-контейнеров в Loki.
**Образ:** `grafana/fluent-bit-plugin-loki:latest`
**Порты:**
- `24224:24224`
- `24224:24224/udp`
- `2020:2020`
- `8888:8888`
**Тома:**
- `./fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf`
- `./fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf`
- `/var/run/docker.sock:/var/run/docker.sock`
- `/var/lib/docker/containers:/var/lib/docker/containers:ro`
**Переменные окружения:**
- `LOKI_URL=http://loki.internal:3100/loki/api/v1/push`
**Сети:**
- `default`

<a name="grafana"></a>
### Grafana

**Описание:** Платформа для аналитики и интерактивных дашбордов, используемая для визуализации метрик (из Prometheus) и логов (из Loki).
**Образ:** `grafana/grafana:12.0.0`
**Порты:**
- `3001:3001`
**Переменные окружения:**
- `GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}`
- `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}`
- `GF_SERVER_ROOT_URL=http://localhost:3001`
- `GF_USERS_ALLOW_SIGN_UP=false`
- `GF_SERVER_HTTP_PORT=3001`
- `GF_DASHBOARDS_MIN_REFRESH_INTERVAL=5s`
- `GF_AUTH_ANONYMOUS_ENABLED=true`
- `GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer`
**Тома:**
- `grafana_data:/var/lib/grafana`
- `./grafana/provisioning:/etc/grafana/provisioning`
- `./grafana/dashboards:/var/lib/grafana/dashboards`
**Метки Traefik:**
- `traefik.enable=true`
- `traefik.http.routers.grafana.rule=Host(`grafana.localhost`)`
- `traefik.http.services.grafana.loadbalancer.server.port=3001`

<a name="volumes"></a>
## Тома данных

**Описание:** Определенные тома для сохранения постоянных данных различных сервисов.
- `postgres_data`: Для PostgreSQL.
- `redis_data`: Для Redis.
- `nats_data`: Для NATS.
- `prometheus_data`: Для Prometheus.
- `loki_data`: Для Loki.
- `grafana_data`: Для Grafana.
- `webapi_logs`: Для логов WebAPI Service.
- `game_logs`: Для логов Game Service.
- `auth_logs`: Для логов Auth Service.
- `consul_data`: Для данных Consul. 
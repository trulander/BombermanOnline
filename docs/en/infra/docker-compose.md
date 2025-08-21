# Docker Compose Documentation for Bomberman Online

This document describes the services defined in the `infra/docker-compose.yml` file, which manages the infrastructure components and microservices of the Bomberman Online project.

## Contents

- [Consul](#consul)
- [Game Allocator Service](#game-allocator-service)
- [WebAPI Service](#webapi-service)
- [Game Service](#game-service)
- [Auth Service](#auth-service)
- [Web Frontend](#web-frontend)
- [PostgreSQL](#postgresql)
- [Redis](#redis)
- [Redis Exporter](#redis-exporter)
- [NATS](#nats)
- [Prometheus NATS Exporter](#prometheus-nats-exporter)
- [Traefik](#traefik)
- [Prometheus](#prometheus)
- [Node Exporter](#node-exporter)
- [cAdvisor](#cadvisor)
- [Loki](#loki)
- [Fluent Bit](#fluent-bit)
- [Grafana](#grafana)
- [Data Volumes](#volumes)

---

<a name="consul"></a>
### Consul

**Description:** Consul is used for service discovery and configuration storage.
**Image:** `hashicorp/consul:1.21`
**Ports:**
- `8500:8500` (HTTP UI)
- `8600:8600/udp` (DNS)
**Startup Command:** `agent -server -bootstrap-expect=1 -ui -client=0.0.0.0`
**Volumes:** (commented out)
- `consul_data:/consul/data`

<a name="game-allocator-service"></a>
### Game Allocator Service

**Description:** Microservice responsible for allocating game resources.
**Build:** From `../services/game-allocator-service`
**Environment Variables:**
- `PYTHONUNBUFFERED=1`: Disables Python output buffering.
- `REDIS_HOST=redis`: Redis host.
- `CONSUL_HTTP_ADDR=consul:8500`: Consul HTTP API address.
- `PROMETHEUS_URL=http://prometheus:9090`: Prometheus server URL.
- `NATS_URL=nats://nats:4222`: NATS server URL.
- `CONSUL_HOST=consul`: Consul host for service discovery.
- `LOG_LEVEL=DEBUG`: Logging level.
- `LOG_FORMAT=json`: Log format.
**Volumes:**
- `../services/game-allocator-service/app:/app/game-allocator-service/app`: Binds the local `app` folder of the service to the folder in the container.
**Traefik Labels:**
- `traefik.enable=true`: Enables Traefik for this service.
**Logging:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.game-allocator-service`

<a name="webapi-service"></a>
### WebAPI Service

**Description:** Main API service for client interaction.
**Build:** From `../services/webapi-service`
**Environment Variables:**
- `PYTHONUNBUFFERED=1`: Disables Python output buffering.
- `REDIS_HOST=redis`: Redis host.
- `NATS_URL=nats://nats:4222`: NATS server URL.
- `AUTH_SERVICE_URL=http://auth-service:5003`: Authentication service URL.
- `CONSUL_HOST=consul`: Consul host.
**Volumes:**
- `../services/webapi-service/app:/app/webapi-service/app`: Binds the local `app` folder of the service to the folder in the container.
- `webapi_logs:/var/log/webapi-service`: Volume for service logs.
**Ports:** (commented out)
- `5001:5001`
**Expose:**
- `5001`: Exposes port inside the Docker network.
**Traefik Labels:**
- `traefik.enable=true`: Enables Traefik for this service.
**Logging:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.webapi-service`

<a name="game-service"></a>
### Game Service

**Description:** Service managing game logic.
**Build:** From `../services/game-service`
**Environment Variables:**
- `LOG_LEVEL=INFO`: Logging level.
- `PYTHONUNBUFFERED=1`: Disables Python output buffering.
- `REDIS_HOST=redis`: Redis host.
- `NATS_URL=nats://nats:4222`: NATS server URL.
- `AUTH_SERVICE_URL=http://auth-service:5003`: Authentication service URL.
- `POSTGRES_HOST=postgres`: PostgreSQL host.
- `POSTGRES_PORT=5432`: PostgreSQL port.
- `POSTGRES_DB=game_service`: PostgreSQL database name.
- `POSTGRES_USER=bomberman`: PostgreSQL user.
- `POSTGRES_PASSWORD=bomberman`: PostgreSQL password.
- `LOG_FORMAT=json`: Log format.
- `CONSUL_HOST=consul`: Consul host.
**Volumes:**
- `../services/game-service/app:/app/game-service/app`: Binds the local `app` folder of the service to the folder in the container.
- `game_logs:/var/log/game-service`: Volume for service logs.
**Ports:** (commented out)
- `5002:5002`
**Expose:**
- `5002`: Exposes port inside the Docker network.
**Traefik Labels:**
- `traefik.enable=true`: Enables Traefik for this service.
**Logging:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.game-service`

<a name="auth-service"></a>
### Auth Service

**Description:** Service for user management and authentication.
**Build:** From `../services/auth-service`
**Environment Variables:**
- `PYTHONUNBUFFERED=1`: Disables Python output buffering.
- `REDIS_HOST=redis`: Redis host.
- `POSTGRES_HOST=postgres`: PostgreSQL host.
- `POSTGRES_PORT=5432`: PostgreSQL port.
- `POSTGRES_DB=auth_service`: PostgreSQL database name.
- `POSTGRES_USER=bomberman`: PostgreSQL user.
- `POSTGRES_PASSWORD=bomberman`: PostgreSQL password.
- `SECRET_KEY=${AUTH_SECRET_KEY:-your_secret_key_here}`: Secret key for JWT. Default value used if variable not set.
- `CONSUL_HOST=consul`: Consul host.
**Volumes:**
- `../services/auth-service/app:/app/auth-service/app`: Binds the local `app` folder of the service to the folder in the container.
- `auth_logs:/var/log/auth-service`: Volume for service logs.
**Ports:** (commented out)
- `5003:5003`
**Expose:**
- `5003`: Exposes port inside the Docker network.
**Traefik Labels:**
- `traefik.enable=true`: Enables Traefik for this service.
**Logging:**
- `driver: fluentd`
- `options.fluentd-address: localhost:24224`
- `options.tag: docker.auth-service`

<a name="web-frontend"></a>
### Web Frontend

**Description:** Client-side web application.
**Build:** From `../services/web-frontend`
**Ports:**
- `3000:3000`: Container port mapping to host.
**Volumes:**
- `../services/web-frontend/public:/app/public`: Binds the local `public` folder to the folder in the container.
- `../services/web-frontend/src:/app/src`: Binds the local `src` folder to the folder in the container.
**Environment Variables:**
- `NODE_ENV=production`: Node.js environment mode.
- `REACT_APP_LOGS_ENDPOINT=/logs`: Endpoint for sending logs.
- `REACT_APP_SERVICE_NAME=web-frontend`: Service name for logging.
- `REACT_APP_SOCKET_URL=http://localhost`: URL for WebSocket connections.
- `REACT_APP_SOCKET_PATH=/webapi/socket.io`: Path for WebSocket connections.
- `PORT=3000`: Port on which the application runs in the container.
- `REACT_APP_LOGS_BATCH_SIZE=10`: Log batch size for sending.
- `AUTH_URL=/auth`: Base URL for authentication.
**Traefik Labels:**
- `traefik.enable=true`: Enables Traefik for this service.

<a name="postgresql"></a>
### PostgreSQL

**Description:** PostgreSQL database for persistent data storage.
**Image:** `postgres:15-alpine`
**Ports:**
- `5432:5432`: Database port mapping.
**Environment Variables:**
- `POSTGRES_USER=${POSTGRES_USER:-bomberman}`: Database user name.
- `POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-bomberman}`: Database user password.
- `POSTGRES_DB=${POSTGRES_DB:-bomberman}`: Default database name.
**Volumes:**
- `postgres_data:/var/lib/postgresql/data`: Volume for storing database data.

<a name="redis"></a>
### Redis

**Description:** In-memory data store used for caching and temporary states.
**Image:** `redis:7.2`
**Ports:**
- `6379:6379`: Redis port mapping.
**Volumes:**
- `redis_data:/data`: Volume for storing Redis data.

<a name="redis-exporter"></a>
### Redis Exporter

**Description:** Redis metrics exporter for Prometheus.
**Image:** `oliver006/redis_exporter:v1.55.0`
**Environment Variables:**
- `REDIS_ADDR: redis://redis:6379`: Redis address.
**Ports:**
- `9121:9121`: Port on which the exporter provides metrics.

<a name="nats"></a>
### NATS

**Description:** Distributed messaging system used for inter-service communication.
**Image:** `nats:2.10`
**Ports:**
- `4222:4222` (client port)
- `8222:8222` (monitoring)
**Volumes:**
- `nats_data:/data`: Volume for storing NATS data.

<a name="prometheus-nats-exporter"></a>
### Prometheus NATS Exporter

**Description:** NATS metrics exporter for Prometheus.
**Image:** `natsio/prometheus-nats-exporter:latest`
**Startup Command:** `-varz -connz -subz -routez -gatewayz -healthz -accstatz -leafz -jsz=all http://nats:8222`
**Ports:**
- `7777:7777`: Port on which the exporter provides metrics.

<a name="traefik"></a>
### Traefik

**Description:** API Gateway and load balancer.
**Image:** `traefik:3.4.0`
**Ports:**
- `80:80` (HTTP)
- `8080:8080` (Traefik Dashboard web interface)
**Volumes:**
- `/var/run/docker.sock:/var/run/docker.sock:ro`: For Docker service discovery.
- `./traefik/traefik.yml:/etc/traefik/traefik.yml`: Traefik configuration file.
- `./traefik/middlewares.yml:/etc/traefik/middlewares.yml`: Middleware configuration.
- `./traefik/routers.yml:/etc/traefik/routers.yml`: Routers configuration.
- `./traefik/logs:/var/log/traefik`: Volume for Traefik logs.
- `./traefik/traefik_plugins:/plugins-storage`: For Traefik plugins.
- `./traefik/local-plugins:/plugins-local/src`: For local development plugins.
**Startup Command:** `--configFile=/etc/traefik/traefik.yml`
**Traefik Labels:**
- `traefik.enable=true`: Enables Traefik for the Traefik Dashboard itself.

<a name="prometheus"></a>
### Prometheus

**Description:** Monitoring and metrics collection system.
**Image:** `prom/prometheus:v2.49.1`
**Ports:**
- `9090:9090`
**Traefik Labels:**
- `traefik.enable=true`
- `traefik.http.routers.prometheus.rule=Host(`prometheus.localhost`)`
- `traefik.http.services.prometheus.loadbalancer.server.port=9090`
**Volumes:**
- `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml`
- `prometheus_data:/prometheus`
**Startup Command:**
- `--config.file=/etc/prometheus/prometheus.yml`
- `--storage.tsdb.path=/prometheus`
- `--web.console.libraries=/etc/prometheus/console_libraries`
- `--web.console.templates=/etc/prometheus/consoles`
- `--web.enable-lifecycle`

<a name="node-exporter"></a>
### Node Exporter

**Description:** System metrics exporter (CPU, RAM, disk space) for Prometheus.
**Image:** `prom/node-exporter:v1.7.0`
**Ports:**
- `9100:9100`
**Volumes:**
- `/proc:/host/proc:ro`
- `/sys:/host/sys:ro`
- `/:/rootfs:ro`
**Startup Command:**
- `--path.procfs=/host/proc`
- `--path.rootfs=/rootfs`
- `--path.sysfs=/host/sys`
- `--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)$`

<a name="cadvisor"></a>
### cAdvisor

**Description:** Agent for collecting container resource usage metrics.
**Image:** `gcr.io/cadvisor/cadvisor:v0.47.2`
**Ports:**
- `8081:8080`
**Volumes:**
- `/:/rootfs:ro`
- `/var/run:/var/run:ro`
- `/sys:/sys:ro`
- `/var/lib/docker/:/var/lib/docker:ro`
- `/dev/disk/:/dev/disk:ro`

<a name="loki"></a>
### Loki

**Description:** Horizontally scalable, highly available, multi-tenant log aggregation system, inspired by Prometheus.
**Image:** `grafana/loki:3.5.0`
**Ports:**
- `3100:3100`
**Volumes:**
- `./loki/loki-config.yml:/etc/loki/local-config.yaml`
- `loki_data:/loki`
**Startup Command:** `-config.file=/etc/loki/local-config.yaml -target=all -log.level=info`
**Networks:**
- `default: aliases: - loki.internal`

<a name="fluent-bit"></a>
### Fluent Bit

**Description:** Lightweight and high-performance log processor and forwarder for logs, metrics, and traces. Used to send Docker container logs to Loki.
**Image:** `grafana/fluent-bit-plugin-loki:latest`
**Ports:**
- `24224:24224`
- `24224:24224/udp`
- `2020:2020`
- `8888:8888`
**Volumes:**
- `./fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf`
- `./fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf`
- `/var/run/docker.sock:/var/run/docker.sock`
- `/var/lib/docker/containers:/var/lib/docker/containers:ro`
**Environment Variables:**
- `LOKI_URL=http://loki.internal:3100/loki/api/v1/push`
**Networks:**
- `default`

<a name="grafana"></a>
### Grafana

**Description:** Analytics and interactive dashboards platform used for visualizing metrics (from Prometheus) and logs (from Loki).
**Image:** `grafana/grafana:12.0.0`
**Ports:**
- `3001:3001`
**Environment Variables:**
- `GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}`
- `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}`
- `GF_SERVER_ROOT_URL=http://localhost:3001`
- `GF_USERS_ALLOW_SIGN_UP=false`
- `GF_SERVER_HTTP_PORT=3001`
- `GF_DASHBOARDS_MIN_REFRESH_INTERVAL=5s`
- `GF_AUTH_ANONYMOUS_ENABLED=true`
- `GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer`
**Volumes:**
- `grafana_data:/var/lib/grafana`
- `./grafana/provisioning:/etc/grafana/provisioning`
- `./grafana/dashboards:/var/lib/grafana/dashboards`
**Traefik Labels:**
- `traefik.enable=true`
- `traefik.http.routers.grafana.rule=Host(`grafana.localhost`)`
- `traefik.http.services.grafana.loadbalancer.server.port=3001`

<a name="volumes"></a>
## Data Volumes

**Description:** Defined volumes for persistent data storage of various services.
- `postgres_data`: For PostgreSQL.
- `redis_data`: For Redis.
- `nats_data`: For NATS.
- `prometheus_data`: For Prometheus.
- `loki_data`: For Loki.
- `grafana_data`: For Grafana.
- `webapi_logs`: For WebAPI Service logs.
- `game_logs`: For Game Service logs.
- `auth_logs`: For Auth Service logs.
- `consul_data`: For Consul data.

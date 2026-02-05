# Configuration
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/configuration.md)

The `WebAPI Service` is configured using environment variables. For development convenience, you can use an `.env` file in the service's root directory. The `.env-example` file provides a template for all necessary variables.

## Secrets Management (Infisical)

When running in Docker, secrets are injected by Infisical. Provide the following variables for the entrypoint:

- `INFISICAL_MACHINE_CLIENT_ID`
- `INFISICAL_MACHINE_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_SECRET_ENV`
- `INFISICAL_API_URL`
- `INFISICAL_PATH`

You can import `services/webapi-service/.env-example` into Infisical to bootstrap the configuration.

## Main Variables

| Variable                | Description                                                           | Default Value (`config.py`)      |
| :---------------------- | :-------------------------------------------------------------------- | :------------------------------- |
| `SERVICE_NAME`          | The name of the service used for registration in Consul.              | `webapi-service`                 |
| `API_V1_STR`            | The URL prefix for all API v1 endpoints.                              | `/webapi/api/v1`                 |
| `APP_TITLE`             | The application title displayed in the Swagger UI.                    | `Bomberman WebAPI Service`       |
| `HOST`                  | The host on which the FastAPI application runs.                       | `0.0.0.0`                        |
| `PORT`                  | The port on which the FastAPI application runs.                       | `5001`                           |
| `DEBUG`                 | Enables/disables FastAPI debug mode.                                  | `True`                           |
| `RELOAD`                | Enables/disables automatic Uvicorn reload on code changes.            | `True`                           |
| `SWAGGER_URL`           | The URL to access the Swagger UI documentation.                       | `/webapi/docs`                   |
| `HOSTNAME`              | The hostname used for internal communications.                        | `localhost`                      |

## CORS Settings

| Variable                | Description                                                           | Default Value (`config.py`)      |
| :---------------------- | :-------------------------------------------------------------------- | :------------------------------- |
| `CORS_ORIGINS`          | A list of allowed origins for CORS.                                   | `*` (all origins)                |
| `CORS_CREDENTIALS`      | Whether CORS allows credentials (e.g., cookies) to be sent.           | `True`                           |
| `CORS_METHODS`          | A list of allowed HTTP methods for CORS.                              | `["*"]` (all methods)            |
| `CORS_HEADERS`          | A list of allowed HTTP headers for CORS.                              | `["*"]` (all headers)            |

## Connection Settings

### Redis

| Variable                | Description                                                           | Default Value (`config.py`)      |
| :---------------------- | :-------------------------------------------------------------------- | :------------------------------- |
| `REDIS_HOST`            | The host of the Redis server.                                         | `localhost`                      |
| `REDIS_PORT`            | The port of the Redis server.                                         | `6379`                           |
| `REDIS_DB`              | The Redis database number.                                            | `0`                              |
| `REDIS_PASSWORD`        | The password for connecting to Redis (if required).                   | `None`                           |

### NATS

| Variable                | Description                                                           | Default Value (`config.py`)      |
| :---------------------- | :-------------------------------------------------------------------- | :------------------------------- |
| `NATS_URL`              | The URL for connecting to the NATS server.                            | `nats://localhost:4222`          |

### Consul

| Variable                | Description                                                           | Default Value (`config.py`)      |
| :---------------------- | :-------------------------------------------------------------------- | :------------------------------- |
| `CONSUL_HOST`           | The Consul host for service discovery.                                | `localhost`                      |

## Logging Settings

| Variable                | Description                                                           | Default Value (`config.py`)      |
| :---------------------- | :-------------------------------------------------------------------- | :------------------------------- |
| `LOG_LEVEL`             | The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).            | `INFO`                           |
| `LOG_FORMAT`            | The log format (`text` or `json`).                                    | `text`                           |
| `TRACE_CALLER`          | Whether to include file and line number information in JSON logs.     | `True`                           |

# Configuration
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/configuration.md)

The service is configured via environment variables. The `app/config.py` file uses `pydantic-settings` to read and validate them.

| Variable            | Description                                                         | Default Value (`app/config.py`)        |
| :------------------ | :------------------------------------------------------------------ | :------------------------------------- |
| `SERVICE_NAME`      | The name of the service, used for registration in Consul.           | `ai-service`                           |
| `HOST`              | The host on which the FastAPI application runs.                     | `0.0.0.0`                              |
| `PORT`              | The port on which the FastAPI application runs.                     | `5004`                                 |
| `DEBUG`             | Enables FastAPI debug mode.                                         | `True`                                 |
| `RELOAD`            | Enables automatic reloading of Uvicorn when code changes.           | `True`                                 |
| `REDIS_HOST`        | Host for connecting to Redis.                                       | `localhost`                            |
| `REDIS_PORT`        | Port for connecting to Redis.                                       | `6379`                                 |
| `REDIS_DB`          | Redis database number.                                              | `0`                                    |
| `REDIS_PASSWORD`    | Password for connecting to Redis (if required).                     | `None`                                 |
| `NATS_URL`          | URL for connecting to the NATS server.                              | `nats://localhost:4222`                |
| `CONSUL_HOST`       | Host for connecting to Consul.                                      | `localhost`                            |
| `CONSUL_PORT`       | Port for connecting to Consul.                                      | `8500`                                 |
| `LOG_LEVEL`         | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).              | `INFO`                                 |
| `LOG_FORMAT`        | Log format (`text` or `json`).                                      | `json`                                 |
| `TRACE_CALLER`      | Enables adding caller function information to JSON logs.            | `True`                                 |
| `MODELS_PATH`       | Path to the directory for saving and loading AI models.             | `/app/ai_models`                       |
| `LOGS_PATH`         | Path to the directory for saving TensorBoard logs.                  | `/app/ai_logs`                         |

# 4. Configuration

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/04_configuration.md)

The service is configured using environment variables. They can be loaded from a `.env` file or passed directly at startup.

### Core Settings

- `API_V1_STR`: Prefix for all API routes. (Default: `/auth/api/v1`)
- `APP_TITLE`: Application title (used in OpenAPI). (Default: `Bomberman Auth Service`)
- `HOST`: Host on which the application runs. (Default: `0.0.0.0`)
- `PORT`: Port on which the application runs. (Default: `5003`)
- `DEBUG`: Enables debug mode. (Default: `True`)
- `RELOAD`: Enables automatic server reload on changes. (Default: `True`)
- `SWAGGER_URL`: URL to access OpenAPI (Swagger) documentation. (Default: `/auth/docs`)

### Service Discovery Settings

- `SERVICE_NAME`: Service name for registration in Consul. (Default: `auth-service`)
- `CONSUL_HOST`: Consul host. (Default: `localhost`)

### CORS Settings

- `CORS_ORIGINS`: List of allowed origins. (Default: `["*"]`)
- `CORS_CREDENTIALS`: Allow credentials to be sent. (Default: `True`)
- `CORS_METHODS`: List of allowed HTTP methods. (Default: `["*"]`)
- `CORS_HEADERS`: List of allowed HTTP headers. (Default: `["*"]`)

### PostgreSQL Settings

- `POSTGRES_HOST`: Database host. (Default: `localhost`)
- `POSTGRES_PORT`: Database port. (Default: `5432`)
- `POSTGRES_DB`: Database name. (Default: `auth_service`)
- `POSTGRES_USER`: Username. (Default: `bomberman`)
- `POSTGRES_PASSWORD`: Password. (Default: `bomberman`)

### Redis Settings

- `REDIS_HOST`: Redis host. (Default: `localhost`)
- `REDIS_PORT`: Redis port. (Default: `6379`)
- `REDIS_DB`: Redis database number. (Default: `1`)
- `REDIS_PASSWORD`: Password for Redis. (Default: `None`)

### JWT Settings

- `SECRET_KEY`: **(Required)** Secret key for signing JWTs. **Must be changed for production!**
- `ALGORITHM`: JWT signing algorithm. (Default: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime in minutes. (Default: `3000`)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token lifetime in days. (Default: `7`)

### OAuth2 (Google) Settings

- `OAUTH2_PROVIDERS__GOOGLE__CLIENT_ID`: Client ID of your Google OAuth application.
- `OAUTH2_PROVIDERS__GOOGLE__CLIENT_SECRET`: Client Secret of your Google OAuth application.

> To set nested environment variables like `OAUTH2_PROVIDERS`, use a double underscore `__` as a separator.

### Logging Settings

- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). (Default: `DEBUG`)
- `LOG_FORMAT`: Log format (`json` or `text`). (Default: `json`)
- `TRACE_CALLER`: Enables call tracing in logs. (Default: `True`)

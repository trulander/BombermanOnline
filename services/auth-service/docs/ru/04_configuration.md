# 4. Конфигурация

[![English](https://img.shields.io/badge/lang-English-blue)](../en/04_configuration.md)

Сервис настраивается с помощью переменных окружения. Они могут быть загружены из `.env` файла или переданы напрямую при запуске. В Docker-режиме секреты также подставляются через Infisical.

### Управление секретами (Infisical)

- `INFISICAL_MACHINE_CLIENT_ID`
- `INFISICAL_MACHINE_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_SECRET_ENV`
- `INFISICAL_API_URL`
- `INFISICAL_PATH`

Файл `services/auth-service/.env-example` можно импортировать в Infisical для базовой конфигурации.

### Основные настройки

- `API_V1_STR`: Префикс для всех API маршрутов. (По умолчанию: `/auth/api/v1`)
- `APP_TITLE`: Заголовок приложения (используется в OpenAPI). (По умолчанию: `Bomberman Auth Service`)
- `HOST`: Хост, на котором запускается приложение. (По умолчанию: `0.0.0.0`)
- `PORT`: Порт, на котором запускается приложение. (По умолчанию: `5003`)
- `DEBUG`: Включает режим отладки. (По умолчанию: `True`)
- `RELOAD`: Включает автоматическую перезагрузку сервера при изменениях. (По умолчанию: `True`)
- `SWAGGER_URL`: URL для доступа к OpenAPI (Swagger) документации. (По умолчанию: `/auth/docs`)

### Настройки Service Discovery

- `SERVICE_NAME`: Имя сервиса для регистрации в Consul. (По умолчанию: `auth-service`)
- `CONSUL_HOST`: Хост Consul. (По умолчанию: `localhost`)

### Настройки CORS

- `CORS_ORIGINS`: Список разрешенных источников (origins). (По умолчанию: `["*"]`)
- `CORS_CREDENTIALS`: Разрешить передачу credentials. (По умолчанию: `True`)
- `CORS_METHODS`: Список разрешенных HTTP-методов. (По умолчанию: `["*"]`)
- `CORS_HEADERS`: Список разрешенных HTTP-заголовков. (По умолчанию: `["*"]`)

### Настройки PostgreSQL

- `POSTGRES_HOST`: Хост базы данных. (По умолчанию: `localhost`)
- `POSTGRES_PORT`: Порт базы данных. (По умолчанию: `5432`)
- `POSTGRES_DB`: Имя базы данных. (По умолчанию: `auth_service`)
- `POSTGRES_USER`: Имя пользователя. (По умолчанию: `bomberman`)
- `POSTGRES_PASSWORD`: Пароль. (По умолчанию: `bomberman`)

### Настройки Redis

- `REDIS_HOST`: Хост Redis. (По умолчанию: `localhost`)
- `REDIS_PORT`: Порт Redis. (По умолчанию: `6379`)
- `REDIS_DB`: Номер базы данных Redis. (По умолчанию: `1`)
- `REDIS_PASSWORD`: Пароль для Redis. (По умолчанию: `None`)

### Настройки JWT

- `SECRET_KEY`: **(Обязательно)** Секретный ключ для подписи JWT. **Должен быть изменен для production!**
- `ALGORITHM`: Алгоритм подписи JWT. (По умолчанию: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Время жизни access-токена в минутах. (По умолчанию: `3000`)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Время жизни refresh-токена в днях. (По умолчанию: `7`)

### Настройки OAuth2 (Google)

- `OAUTH2_PROVIDERS__GOOGLE__CLIENT_ID`: Client ID вашего Google OAuth приложения.
- `OAUTH2_PROVIDERS__GOOGLE__CLIENT_SECRET`: Client Secret вашего Google OAuth приложения.

> Для установки вложенных переменных окружения, таких как `OAUTH2_PROVIDERS`, используется двойное подчеркивание `__` в качестве разделителя.

### Настройки логирования

- `LOG_LEVEL`: Уровень логирования (`DEBUG`, `INFO`, `WARNING`, `ERROR`). (По умолчанию: `DEBUG`)
- `LOG_FORMAT`: Формат логов (`json` или `text`). (По умолчанию: `json`)
- `TRACE_CALLER`: Включает трассировку вызовов в логах. (По умолчанию: `True`)
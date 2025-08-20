# Развертывание и запуск
[![English](https://img.shields.io/badge/lang-English-blue)](../en/deployment.md)

Этот раздел содержит инструкции по запуску `WebAPI Service` для разработки и в производственной среде.

## Локальный запуск для разработки

Этот способ рекомендуется для разработки и отладки.

### Требования
*   Python 3.12+
*   [uv](https://github.com/astral-sh/uv) для управления зависимостями.
*   Доступные экземпляры **Redis** и **NATS**.

### Шаги

1.  **Клонируйте репозиторий** (если еще не сделали):
```bash
git clone <your-repo-url>
cd services/webapi-service
```

2.  **Установите зависимости**:
*   `uv` создаст виртуальное окружение и установит в него пакеты из `pyproject.toml`.
```bash
uv sync
```

3.  **Настройте переменные окружения**:
*   Скопируйте файл `.env-example` в `.env`:
```bash
cp .env-example .env
```
*   Отредактируйте `.env`, указав правильные адреса для `REDIS_HOST`, `NATS_URL` и `CONSUL_HOST`.

4.  **Запустите сервер**:
*   `uv` запустит Uvicorn в контексте созданного виртуального окружения.
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

5.  **Проверка**:
*   Откройте в браузере `http://localhost:5001`. Вы должны увидеть приветственную страницу.
*   Документация Swagger UI будет доступна по адресу `http://localhost:5001/webapi/docs` (или по URL, указанному в `SWAGGER_URL`).

## Запуск с использованием Docker

Этот способ подходит для создания изолированного окружения и подготовки к производственному развертыванию.

### Требования
*   [Docker](https://www.docker.com/)
*   [Docker Compose](https://docs.docker.com/compose/) (рекомендуется для управления несколькими сервисами)

### Сборка Docker-образа

Находясь в директории `services/webapi-service`, выполните команду:

```bash
docker build -t bomberman-webapi-service .
```

### Запуск Docker-контейнера

Вы можете запустить сервис в контейнере, передав все необходимые переменные окружения через флаг `-e`.

```bash
docker run -p 5001:5001 \
    -e NATS_URL=nats://<nats_host>:4222 \
    -e REDIS_HOST=<redis_host> \
    -e CONSUL_HOST=<consul_host> \
    --name webapi_service \
    bomberman-webapi-service
```

*   Замените `<nats_host>`, `<redis_host>`, `<consul_host>` на реальные адреса ваших зависимостей. Если они запущены на той же машине, вы можете использовать `host.docker.internal`.

### Использование Docker Compose (Рекомендуемый способ)

Для комплексного развертывания всей системы (включая `WebAPI`, `Game Service`, `NATS`, `Redis` и т.д.) рекомендуется использовать `docker-compose.yml` из корневой директории проекта.

1.  **Настройте `docker-compose.yml`**:
*   Убедитесь, что сервис `webapi-service` определен в файле `docker-compose.yml`.
*   Проверьте, что все переменные окружения для сервиса установлены правильно в секции `environment`.

2.  **Запустите все сервисы**:
*   Эта команда соберет образы (если необходимо) и запустит все сервисы в фоновом режиме.
```bash
docker-compose up -d
```

3.  **Просмотр логов**:
*   Для просмотра логов конкретного сервиса используйте:
```bash
docker-compose logs -f webapi-service
```

4.  **Остановка**:
*   Для остановки всех запущенных сервисов:
```bash
docker-compose down
```
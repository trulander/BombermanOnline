# Auth Service - Bomberman Online

Сервис авторизации и управления пользователями для игры Bomberman Online.

## Возможности

- Регистрация и аутентификация пользователей
- OAuth 2.0 авторизация через внешних провайдеров (Google)
- JWT токены для авторизации
- Управление ролями пользователей (user, admin, moderator, developer)
- Защита API через Traefik Forward Auth
- Веб-интерфейс для авторизации и регистрации

## Технологии

- Python 3.12
- FastAPI
- PostgreSQL (SQLAlchemy)
- Redis
- JWT (jose)
- OAuth 2.0
- Jinja2 Templates
- Alembic (миграции базы данных)

## Структура проекта

```
auth-service/
├── app/
│   ├── models/           # Модели данных (Pydantic и SQLAlchemy)
│   ├── routes/           # Маршруты API и веб-интерфейса
│   ├── services/         # Бизнес-логика
│   ├── templates/        # HTML шаблоны
│   ├── static/           # Статические файлы (CSS, JS)
│   ├── config.py         # Конфигурация
│   ├── database.py       # Работа с базой данных
│   ├── dependencies.py   # Зависимости FastAPI
│   ├── logging_config.py # Настройка логирования
│   ├── redis_client.py   # Клиент Redis
│   └── main.py           # Точка входа приложения
├── migrations/           # Миграции базы данных (Alembic)
│   ├── versions/         # Версии миграций
│   ├── env.py            # Настройки окружения Alembic
│   └── script.py.mako    # Шаблон для файлов миграций
├── scripts/              # Вспомогательные скрипты
│   ├── create_migration.py  # Скрипт для создания миграций
│   ├── apply_migrations.py  # Скрипт для применения миграций
│   ├── rollback_migrations.py  # Скрипт для отката миграций
│   └── show_migrations.py  # Скрипт для просмотра истории миграций
├── alembic.ini           # Конфигурация Alembic
├── Dockerfile            # Dockerfile для контейнеризации
└── pyproject.toml        # Зависимости проекта
```

## API Endpoints

### Аутентификация

- `POST /api/v1/auth/login` - Вход в систему
- `POST /api/v1/auth/refresh` - Обновление токена
- `POST /api/v1/auth/logout` - Выход из системы
- `GET /api/v1/auth/check` - Проверка токена (для Traefik)
- `GET /api/v1/auth/oauth/{provider}` - Начало OAuth авторизации
- `GET /api/v1/auth/oauth/{provider}/callback` - Callback OAuth авторизации

### Пользователи

- `POST /api/v1/users` - Создание пользователя
- `GET /api/v1/users/me` - Получение информации о текущем пользователе
- `PUT /api/v1/users/me` - Обновление информации о текущем пользователе
- `GET /api/v1/users/{user_id}` - Получение информации о пользователе
- `PUT /api/v1/users/{user_id}/role` - Обновление роли пользователя (только для админов)
- `GET /api/v1/users` - Поиск пользователей

### Веб-интерфейс

- `GET /ui/login` - Страница входа
- `GET /ui/register` - Страница регистрации
- `GET /ui/reset-password` - Страница сброса пароля
- `GET /ui/dashboard` - Личный кабинет пользователя

### Другие маршруты

- `GET /auth/login` - Страница входа (HTML форма)
- `GET /auth/register` - Страница регистрации (HTML форма)
- `POST /auth/register` - Обработка формы регистрации
- `GET /auth/reset-password` - Страница сброса пароля
- `POST /auth/reset-password` - Обработка формы сброса пароля
- `GET /auth/verify-email` - Подтверждение email

## Запуск

### Через Docker

```bash
docker build -t auth-service .
docker run -p 5003:5003 auth-service
```

### Локально

```bash
# Установка зависимостей
uv pip install -e .

# Запуск
uvicorn app.main:app --host 0.0.0.0 --port 5003 --reload
```

## Управление миграциями

### Создание новой миграции

```bash
# Автоматическое создание миграции на основе изменений в моделях
python scripts/create_migration.py "Название миграции"

# или с использованием Alembic напрямую
alembic revision --autogenerate -m "Название миграции"
```

### Применение миграций

```bash
# Применение всех миграций до последней версии
python scripts/apply_migrations.py

# или с использованием Alembic напрямую
alembic upgrade head

# Применение миграций до определенной версии
python scripts/apply_migrations.py <revision>
alembic upgrade <revision>

# Применение следующей миграции
alembic upgrade +1
```

### Откат миграций

```bash
# Откат на одну миграцию назад
python scripts/rollback_migrations.py

# или с использованием Alembic напрямую
alembic downgrade -1

# Откат до определенной версии
python scripts/rollback_migrations.py <revision>
alembic downgrade <revision>

# Откат всех миграций
python scripts/rollback_migrations.py base
alembic downgrade base
```

### Просмотр истории миграций

```bash
# Просмотр истории миграций и текущей ревизии
python scripts/show_migrations.py

# или с использованием Alembic напрямую
alembic history --verbose
alembic current
```

## Переменные окружения

- `POSTGRES_HOST` - Хост PostgreSQL (по умолчанию: localhost)
- `POSTGRES_PORT` - Порт PostgreSQL (по умолчанию: 5432)
- `POSTGRES_DB` - Имя базы данных PostgreSQL (по умолчанию: bomberman)
- `POSTGRES_USER` - Пользователь PostgreSQL (по умолчанию: bomberman)
- `POSTGRES_PASSWORD` - Пароль PostgreSQL (по умолчанию: bomberman)
- `REDIS_HOST` - Хост Redis (по умолчанию: localhost)
- `REDIS_PORT` - Порт Redis (по умолчанию: 6379)
- `SECRET_KEY` - Секретный ключ для JWT токенов
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Время жизни access токена в минутах (по умолчанию: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Время жизни refresh токена в днях (по умолчанию: 7)

## Интеграция с Traefik

Сервис настроен для работы с Traefik Forward Auth middleware для защиты API и веб-интерфейса. В конфигурации Traefik используются следующие middleware:

- `auth-check` - Проверка JWT токена для защиты API
- `auth-redirect` - Проверка JWT токена с редиректом на страницу авторизации для веб-интерфейса 
# Bomberman Online

Многопользовательская игра Bomberman с онлайн-режимом.

## Архитектура

Проект состоит из следующих компонентов:

1. **Web Frontend** - клиентское веб-приложение на TypeScript
2. **WebAPI Service** - API сервис на FastAPI для обработки запросов от клиента
3. **Game Service** - сервис для управления игровой логикой на FastAPI
4. **Auth Service** - сервис авторизации и управления пользователями на FastAPI
5. **Инфраструктурные компоненты**:
   - PostgreSQL - база данных
   - Redis - кэширование и хранение состояний
   - NATS - очередь сообщений для коммуникации между сервисами
   - Traefik - API Gateway и балансировщик нагрузки
   - Prometheus, Grafana - мониторинг
   - Loki, Fluent Bit - логирование

## Сервисы

### Web Frontend

Frontend приложение, написанное на TypeScript с использованием:
- Canvas API для отрисовки игрового поля
- Socket.IO для коммуникации с сервером в реальном времени

### WebAPI Service

REST API сервис для обработки запросов от клиента:
- Регистрация и получение игровых комнат
- Управление игровыми сессиями
- Обработка WebSocket соединений

### Game Service

Сервис для управления игровой логикой:
- Создание и управление игровыми сессиями
- Обработка игровых событий
- Расчет игровой физики и логики

### Auth Service

Сервис авторизации и управления пользователями:
- Регистрация и аутентификация пользователей
- Управление JWT токенами
- OAuth 2.0 авторизация через внешние провайдеры
- Управление ролями пользователей
- Защита API через Traefik Forward Auth

## Запуск проекта

### Требования

- Docker и Docker Compose
- Make (опционально)

### Запуск

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/BombermanOnline.git
cd BombermanOnline

# Запуск всех сервисов
docker-compose -f infra/docker-compose.yml up -d
```

### Доступ к сервисам

После запуска сервисы доступны по следующим адресам:

- **Игра**: http://localhost/
- **API**: http://localhost/api/
- **Авторизация**: http://localhost/ui/login
- **Документация API**: http://localhost/api/docs
- **Grafana**: http://grafana.localhost/ (admin/admin)
- **Prometheus**: http://prometheus.localhost/
- **Traefik Dashboard**: http://traefik.localhost/

## Разработка

### Структура проекта

```
BombermanOnline/
├── services/                  # Сервисы
│   ├── web-frontend/          # Web Frontend
│   ├── webapi-service/        # WebAPI Service
│   ├── game-service/          # Game Service
│   └── auth-service/          # Auth Service
├── infra/                     # Инфраструктура
│   ├── docker-compose.yml     # Docker Compose файл
│   ├── traefik/               # Конфигурация Traefik
│   ├── prometheus/            # Конфигурация Prometheus
│   ├── grafana/               # Конфигурация Grafana
│   ├── loki/                  # Конфигурация Loki
│   └── fluent-bit/            # Конфигурация Fluent Bit
└── README.md                  # Документация
```

### Локальная разработка

Для локальной разработки можно использовать Docker Compose:

```bash
# Запуск всех сервисов
docker-compose -f infra/docker-compose.yml up -d

# Запуск отдельного сервиса
docker-compose -f infra/docker-compose.yml up -d webapi-service

# Остановка всех сервисов
docker-compose -f infra/docker-compose.yml down
```

## Роли пользователей

В системе предусмотрены следующие роли пользователей:

1. **user** - обычный пользователь, может играть в игры
2. **admin** - администратор, имеет полный доступ ко всем функциям
3. **moderator** - модератор, может управлять игровыми комнатами и пользователями
4. **developer** - разработчик, имеет доступ к техническим функциям

## Лицензия

MIT

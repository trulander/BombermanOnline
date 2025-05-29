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
- React + Material-UI для пользовательского интерфейса
- Canvas API для отрисовки игрового поля
- Socket.IO для коммуникации с сервером в реальном времени (с авторизацией через JWT токены)
- Axios для HTTP запросов с автоматическим обновлением токенов

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

## Маршрутизация

### Пользовательские маршруты

- **/** - главная страница с описанием игры
- **/account/login** - страница входа в систему
- **/account/register** - страница регистрации
- **/account/reset-password** - сброс пароля
- **/account/confirm-reset-password** - подтверждение сброса пароля
- **/account/verify-email** - подтверждение email
- **/account/dashboard** - личный кабинет пользователя
- **/account/profile** - редактирование профиля
- **/account/stats** - игровая статистика пользователя
- **/account/game** - игровая страница

### API маршруты

- **/auth/api/v1/auth/** - эндпоинты авторизации
- **/auth/api/v1/users/** - управление пользователями
- **/auth/api/v1/games/** - игровые эндпоинты

## Безопасность

### Система авторизации
- **JWT токены** для HTTP API и WebSocket соединений
- **Refresh токены** для автоматического обновления сессий
- **Ролевая модель** (администраторы, игроки)
- **Cookie-based авторизация** для WebSocket соединений

### WebSocket авторизация
Приложение использует **HTTP cookies** для авторизации WebSocket соединений:
- При логине создается cookie `ws_auth_token` с path `/socket.io/`
- Cookie автоматически отправляется при WebSocket handshake
- Безопасная передача токенов без использования query parameters
- Подробности в [WEBSOCKET_AUTH_ARCHITECTURE.md](services/web-frontend/WEBSOCKET_AUTH_ARCHITECTURE.md)

### Архитектура маршрутизации
- **Защищенные маршруты** для авторизованных пользователей (`/account/*`)
- **Публичные маршруты** для неавторизованных (`/login`, `/register`)
- **Централизованный контроль доступа** через `ProtectedRoute` и `PublicRoute`
- Подробности в [ROUTING_ARCHITECTURE.md](services/web-frontend/ROUTING_ARCHITECTURE.md)

### Управление токенами
- **Централизованный TokenService** для всех операций с токенами
- **Отсутствие дублирования** логики между компонентами
- **Автоматическое управление cookies** для WebSocket
- Подробности в [TOKEN_MANAGEMENT_ARCHITECTURE.md](services/web-frontend/TOKEN_MANAGEMENT_ARCHITECTURE.md)

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

- **Игра**: http://localhost/game
- **Личный кабинет**: http://localhost/account/dashboard
- **API**: http://localhost/api/
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
│   │   ├── src/
│   │   │   ├── components/    # React компоненты
│   │   │   ├── pages/         # Страницы приложения
│   │   │   ├── context/       # React контексты
│   │   │   ├── services/      # Сервисы (API, InputHandler)
│   │   │   ├── types/         # TypeScript типы
│   │   │   └── utils/         # Утилиты (Logger)
│   │   ├── public/            # Статические файлы
│   │   └── Dockerfile
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

### Разработка Frontend

```bash
cd services/web-frontend

# Установка зависимостей
npm install

# Запуск в режиме разработки
npm start

# Сборка для продакшена
npm run build
```

## Функциональность

### Игровые возможности

- Создание и присоединение к игровым комнатам
- Многопользовательская игра в реальном времени
- Система статистики игроков
- Профили пользователей с настройками

### Особенности реализации

- Плавная камера с "мертвой зоной" для отслеживания игрока
- Оптимизированная передача изменений карты вместо полного состояния
- Автоматическое переподключение при проблемах с сетью
- Система логирования с отправкой на сервер

## Роли пользователей

В системе предусмотрены следующие роли пользователей:

1. **user** - обычный пользователь, может играть в игры
2. **admin** - администратор, имеет полный доступ ко всем функциям
3. **moderator** - модератор, может управлять игровыми комнатами и пользователями
4. **developer** - разработчик, имеет доступ к техническим функциям

## Технологии

### Frontend
- React 18 + TypeScript
- Material-UI для компонентов интерфейса
- Socket.IO Client для реального времени
- Canvas API для игровой графики
- Axios для HTTP запросов
- Formik + Yup для форм и валидации

### Backend
- FastAPI для API сервисов
- Socket.IO для WebSocket соединений
- PostgreSQL для основной базы данных
- Redis для кэширования и состояний
- NATS для межсервисной коммуникации

### DevOps
- Docker + Docker Compose
- Traefik как API Gateway
- Prometheus + Grafana для мониторинга
- Loki + Fluent Bit для логирования

## Лицензия

MIT

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

## Документация

Здесь вы найдете подробную документацию по различным компонентам проекта Bomberman Online:

### Инфраструктура

*   [Docker Compose Конфигурация](docs/infra/docker-compose.md)

### Сервисы

*   [AI Service](services/ai-service/README.md)
*   [Auth Service](services/auth-service/README.md)
*   [Game Allocator Service](services/game-allocator-service/README.md)
*   [Game Service](services/game-service/README.md)
    *   [API Эндпоинты](services/game-service/docs/api_endpoints.md)
    *   [Архитектура Сущностей](services/game-service/docs/architecture/entities.md)
    *   [Архитектура Моделей](services/game-service/docs/architecture/models.md)
    *   [Обзор Архитектуры](services/game-service/docs/architecture/overview.md)
    *   [Архитектура Репозиториев](services/game-service/docs/architecture/repositories.md)
    *   [Архитектура Сервисов](services/game-service/docs/architecture/services.md)
    *   [Конфигурация](services/game-service/docs/configuration.md)
    *   [Введение](services/game-service/docs/introduction.md)
    *   [События NATS](services/game-service/docs/nats_events.md)
    *   [Команды и Действия Игроков](services/game-service/docs/player_commands_and_actions.md)
    *   [Настройка](services/game-service/docs/setup.md)
    *   [Логика Команд](services/game-service/docs/teams_logic.md)
*   [Web Frontend](services/web-frontend/README.md)
*   [WebAPI Service](services/webapi-service/README.md)

## Сервисы

### AI Service


### Web Frontend

Frontend приложение, написанное на TypeScript с использованием:
- React + Material-UI для пользовательского интерфейса
- Canvas API для отрисовки игрового поля
- Axios для HTTP запросов с автоматическим обновлением токенов
- **REST API** для создания и управления играми (взамен Socket.IO)

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
- Предоставление REST API для создания, управления и получения информации об играх, командах, сущностях и картах.

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
- **/account/games/create** - страница создания новой игры
- **/account/games/:gameId/manage** - страница управления созданной игрой
- **/account/maps/editor** - страница редактора карт
- **/account/game/:gameId** - игровая страница (для присоединения к активной игре)

### API маршруты

- **/auth/api/v1/auth/** - эндпоинты авторизации
- **/auth/api/v1/users/** - управление пользователями
- **/auth/api/v1/games/** - игровые эндпоинты (для управления играми)
- **/auth/api/v1/teams/** - эндпоинты для управления командами
- **/auth/api/v1/maps/** - эндпоинты для управления картами
- **/auth/api/v1/entities/** - эндпоинты для получения информации о сущностях

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

### Архитектура маршрутизации
- **Защищенные маршруты** для авторизованных пользователей (`/account/*`)
- **Публичные маршруты** для неавторизованных (`/login`, `/register`)
- **Централизованный контроль доступа** через `ProtectedRoute` и `PublicRoute`

### Управление токенами
- **Централизованный TokenService** для всех операций с токенами
- **Отсутствие дублирования** логики между компонентами
- **Автоматическое управление cookies** для WebSocket

## Запуск проекта

### Требования

- Docker и Docker Compose

### Запуск

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/BombermanOnline.git
cd BombermanOnline

# Запуск всех сервисов (включая фронтенд)
docker-compose up -d
```

### Установка зависимостей

```bash
# Установка зависимостей для всех Python сервисов с помощью uv
uv sync

# Установка зависимостей для Web Frontend
cd services/web-frontend
npm install
cd ../..
```

### Запуск отдельных сервисов (для разработки)

Для запуска отдельных сервисов можно использовать следующий подход:

1.  **Запуск инфраструктурных компонентов**:

    ```bash
    docker-compose -f infra/docker-compose.yml up -d postgres redis nats
    ```

2.  **Запуск конкретного сервиса (например, game-service)**:

    ```bash
    # Убедитесь, что вы находитесь в корне проекта BombermanOnline
    # Запустите сервис с перезагрузкой для отслеживания изменений кода
    uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
    ```

    Повторите для `auth-service` и `webapi-service`, изменив порт и путь к `app.main:app` соответственно.

3.  **Запуск Web Frontend в режиме разработки**:

    ```bash
    cd services/web-frontend
    npm start
    cd ../..
    ```

### Доступ к сервисам

После запуска сервисы доступны по следующим адресам:

- **Игра**: http://localhost/game/:gameId
- **Создание игры**: http://localhost/account/games/create
- **Управление игрой**: http://localhost/account/games/:gameId/manage
- **Редактор карт**: http://localhost/account/maps/editor
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
│   ├── docker-compose.yml     # Docker Compose файл инфраструктуры
│   ├── traefik/               # Конфигурация Traefik
│   ├── prometheus/            # Конфигурация Prometheus
│   ├── grafana/               # Конфигурация Grafana
│   ├── loki/                  # Конфигурация Loki
│   └── fluent-bit/            # Конфигурация Fluent Bit
└── README.md                  # Документация
└── docker-compose.yml         # Основной Docker Compose файл
```

### Локальная разработка

Для локальной разработки можно использовать Docker Compose:

```bash
# Запуск всех сервисов (включая фронтенд в режиме разработки)
docker-compose up -d

# Запуск отдельного сервиса (пример: только фронтенд в режиме разработки)
docker-compose up -d web-frontend

# Остановка всех сервисов
docker-compose down
```

### Разработка Frontend

```bash
# Для запуска в режиме разработки через Docker Compose, используйте команду выше `docker-compose up -d web-frontend`
# Если вы хотите запустить фронтенд без Docker Compose:
cd services/web-frontend

# Установка зависимостей (если еще не установлены)
npm install

# Запуск в режиме разработки
npm start

# Сборка для продакшена
npm run build
```

## Функциональность

### Игровые возможности

- Создание и присоединение к игровым комнатам через REST API
- Управление созданными игровыми сессиями (старт, пауза, возобновление, удаление, управление игроками и командами)
- Многопользовательская игра в реальном времени
- Система статистики игроков
- Профили пользователей с настройками
- Редактор карт для создания и управления шаблонами карт

### Особенности реализации

- Плавная камера с "мертвой зоной" для отслеживания игрока
- Оптимизированная передача изменений карты вместо полного состояния
- Автоматическое переподключение при проблемах с сетью
- Система логирования с отправкой на сервер
- Переход от Socket.IO к REST API для управления играми

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
- Socket.IO Client для реального времени (только для игрового процесса)
- Axios для HTTP запросов с автоматическим обновлением токенов
- Canvas API для игровой графики

### Backend
- FastAPI для API сервисов
- Socket.IO для WebSocket соединений
- PostgreSQL для основной базы данных
- Redis для кэширования и состояний
- NATS для межсервисной коммуникации
- `uv` для управления зависимостями Python

### DevOps
- Docker + Docker Compose
- Traefik как API Gateway
- Prometheus + Grafana для мониторинга
- Loki + Fluent Bit для логирования
- Dockerfile для каждого сервиса

## Лицензия


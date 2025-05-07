# Bomberman Online

Многопользовательская игра Bomberman, работающая на микросервисной архитектуре.

## Архитектура

Проект разделен на следующие микросервисы:

1. **webapi-service** - REST API и Socket.IO интерфейс для клиентов
2. **game-service** - Игровая логика и механика 
3. **web-frontend** - Клиентский интерфейс на TypeScript

Для коммуникации между сервисами используется NATS.

## Технологии

- **Backend**: Python 3.12, FastAPI, Socket.IO, NATS
- **Frontend**: TypeScript, HTML5 Canvas
- **Database**: PostgreSQL, Redis
- **Infrastructure**: Docker, Docker Compose

## Запуск проекта

### С использованием Docker

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-repo/BombermanOnline.git
   cd BombermanOnline
   ```

2. Создайте файлы .env на основе .env-example:
   ```bash
   cp services/webapi-service/.env-example services/webapi-service/.env
   cp services/game-service/.env-example services/game-service/.env
   ```

3. Запустите сервисы:
   ```bash
   docker-compose up
   ```

4. Игра будет доступна по адресу: http://localhost:3000

### Локальная разработка

1. Установите Python 3.12 и Node.js

2. Установите зависимости Python:
   ```bash
   pip install uv
   uv pip install -e .
   ```

3. Установите зависимости Node.js:
   ```bash
   cd frontend
   npm install
   ```

4. Запустите сервисы в отдельных терминалах:
   ```bash
   # WebAPI сервис
   uvicorn services.webapi-service.app.main:app --host 0.0.0.0 --port 5001 --reload
   
   # Game сервис
   uvicorn services.game-service.app.main:app --host 0.0.0.0 --port 5002 --reload
   
   # Frontend
   cd frontend
   npm run dev
   ```

## Управление

- **Движение**: Стрелки или WASD
- **Установка бомбы**: Пробел
- **Перезапуск**: R (когда игра окончена)

## Мультиплеер

Игра поддерживает до 4-х игроков. Для подключения других игроков:
1. Первый игрок создает игру и получает ID игры
2. Другие игроки присоединяются, вводя этот ID

## Структура проекта

```
BombermanOnline/
├── services/
│   ├── webapi-service/   # REST API и Socket.IO сервис
│   ├── game-service/     # Игровая логика
│   └── web-frontend/     # Клиентский интерфейс
├── docker-compose.yml    # Конфигурация Docker Compose
└── pyproject.toml        # Зависимости Python
```

## Диаграмма архитектуры

```mermaid
graph TD
    A[Клиент] -->|Socket.IO| B[webapi-service]
    B -->|NATS| C[game-service]
    
    subgraph WebAPI Service
        B --> D[REST API]
        D --> E[Socket.IO]
        E --> F[NATS Client]
    end
    
    subgraph Game Service
        C --> G[Game Logic]
        G --> H[NATS Server]
    end
    
    F -->|Request/Response| H
    H -->|Publish/Subscribe| F
    F -->|Socket.IO| A
```

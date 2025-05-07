import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .services.nats_service import NatsService

app = FastAPI(
    title=settings.APP_TITLE,
    debug=settings.DEBUG,
)

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Инициализируем NATS сервис
nats_service = NatsService()

# Запускаем подключение к NATS и игровой цикл при старте приложения
@app.on_event("startup")
async def startup_event() -> None:
    await nats_service.connect()
    asyncio.create_task(nats_service.start_game_loop())

# Закрываем соединение с NATS при завершении работы
@app.on_event("shutdown")
async def shutdown_event() -> None:
    await nats_service.disconnect()

# Простой эндпоинт для проверки статуса сервиса
@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "game-service"}

# Запуск приложения, если файл запущен напрямую
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    ) 
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from .config import settings
from .services.socketio_service import SocketIOService
from .dependencies import nats_service, game_service, redis_repository
from .routes.root import root_router
from .routes.api import api_router

# Инициализация FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
)

# Инициализация Socket.IO
socketio_service = SocketIOService(
    game_service=game_service
)
socket_app = socketio_service.get_app()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Подключаем маршруты
app.include_router(root_router)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Монтируем Socket.IO
app.mount("/socket.io", socket_app)

# Обработчики событий для подключения/отключения сервисов
@app.on_event("startup")
async def startup_event() -> None:
    """Действия при запуске приложения"""
    from .dependencies import redis_repository
    await redis_repository.connect()
    await nats_service.connect()

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Действия при завершении работы приложения"""
    from .dependencies import redis_repository
    await redis_repository.disconnect()
    await nats_service.disconnect()

# Запуск приложения, если файл запущен напрямую
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    ) 
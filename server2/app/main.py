import asyncio
import os

import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.api import router
from config import settings

from services.game_service import GameService

# Создаем FastAPI приложение
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

# Инициализируем игровой сервис
game_service = GameService()

# Создаем приложение Socket.IO
socket_app = socketio.ASGIApp(game_service.sio)

# Монтируем Socket.IO приложение под путь "/socket.io/"
app.mount("/socket.io", socket_app)

# Подключаем маршруты
app.include_router(router)

# Если есть статические файлы, монтируем их
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Запускаем игровой цикл при старте приложения
@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(game_service.start_game_loop())
    # await game_service.start_game_loop()


# Запуск приложения, если файл запущен напрямую
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )


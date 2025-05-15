import asyncio
import logging
import uvicorn
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi.responses import JSONResponse

from .services.game_service import GameService
from .config import settings
from .logging_config import configure_logging
from .services.nats_service import NatsService
from .coordinators.game_coorditanor import GameCoordinator
from .auth import get_current_user, get_current_admin

# Настройка логирования
configure_logging()
logger = logging.getLogger(__name__)

try:
    app = FastAPI(
        title=settings.APP_TITLE,
        debug=settings.DEBUG,
    )
    
    # Добавляем Prometheus метрики
    app.add_middleware(
        PrometheusMiddleware,
        app_name="game_service",
        group_paths=True,
        filter_unhandled_paths=False,
    )
    app.add_route("/metrics", handle_metrics)
    
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
    game_coordinator = GameCoordinator(notification_service=nats_service)
    
    # Добавляем middleware для авторизации
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Извлекаем заголовки X-User-* из запроса (установленные Traefik после проверки токена)
        user_id = request.headers.get("X-User-ID")
        user_role = request.headers.get("X-User-Role")
        user_email = request.headers.get("X-User-Email")
        user_name = request.headers.get("X-User-Name")
        
        # Если заголовки присутствуют, добавляем информацию о пользователе в state запроса
        if user_id and user_role:
            request.state.user = {
                "id": user_id,
                "role": user_role,
                "email": user_email,
                "username": user_name
            }
            logger.info(f"User {user_name} ({user_role}) authenticated")
        else:
            request.state.user = None
        
        # Продолжаем обработку запроса
        return await call_next(request)
    
    # Глобальный обработчик исключений
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    # Запускаем подключение к NATS и игровой цикл при старте приложения
    @app.on_event("startup")
    async def startup_event() -> None:
        try:
            logger.info("Starting Game service")
            await game_coordinator.initialize_handlers()
            asyncio.create_task(game_coordinator.start_game_loop())
            logger.info("Game service started successfully")
        except Exception as e:
            logger.critical(f"Failed to start Game service: {e}", exc_info=True)
            # В продакшене здесь можно было бы добавить metrics.inc({'event': 'startup_failure'})
            # и возможно system exit(1)
    
    # Закрываем соединение с NATS при завершении работы
    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        try:
            logger.info("Shutting down Game service")
            await nats_service.disconnect()
            logger.info("Game service stopped successfully")
        except Exception as e:
            logger.error(f"Error during Game service shutdown: {e}", exc_info=True)
    
    # Простой эндпоинт для проверки статуса сервиса
    @app.get("/health")
    async def health_check() -> dict:
        try:
            # В реальном приложении здесь можно было бы проверить подключение к NATS
            # и вернуть соответствующий статус
            return {"status": "ok", "service": "game-service"}
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {"status": "error", "service": "game-service", "message": str(e)}

except Exception as e:
    logger.critical(f"Failed to initialize application: {str(e)}\n{traceback.format_exc()}")
    raise

# Запуск приложения, если файл запущен напрямую
if __name__ == "__main__":
    try:
        logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            log_level=settings.LOG_LEVEL.lower(),
        )
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True) 
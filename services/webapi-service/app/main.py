import os
import socket

import consul
import uvicorn
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aioprometheus import MetricsMiddleware
from aioprometheus.asgi.starlette import metrics
from fastapi.responses import JSONResponse

from .config import settings
from .logging_config import configure_logging
from .services.socketio_service import SocketIOService
from .dependencies import nats_service, game_service, redis_repository
from .routes.root import root_router
from .routes.api import api_router
from .auth import get_current_user, get_current_admin

# Настройка логирования
configure_logging()
logger = logging.getLogger(__name__)

def register_service():
    logger.info(f"registering in the consul service")
    service_name = settings.SERVICE_NAME
    c = consul.Consul(host=settings.CONSUL_HOST, port=8500)
    service_id = f"{service_name}-{settings.HOSTNAME}"
    c.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=settings.HOSTNAME,  # Имя сервиса в Docker сети
        port=settings.PORT,
        tags=["traefik"],
        check=consul.Check.http(
            url=f"http://{settings.HOSTNAME}:{settings.PORT}/health",
            interval="10s",
            timeout="1s",
            deregister="60s"
        )
    )

try:
    # Инициализация FastAPI
    app = FastAPI(
        title=settings.APP_TITLE,
        docs_url=settings.SWAGGER_URL,
        openapi_url=f"{settings.SWAGGER_URL}/openapi.json",
        debug=settings.DEBUG,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
    
    # Добавляем Prometheus метрики с помощью aioprometheus
    app.add_middleware(
        MetricsMiddleware,
        # app_name="webapi_service"
    )
    app.add_route("/metrics", metrics)
    
    # Глобальный обработчик исключений
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    

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

    # Инициализация Socket.IO
    try:
        socketio_service = SocketIOService(
            game_service=game_service
        )
        socket_app = socketio_service.get_app()
        logger.info("SocketIO service initialized")
    except Exception as e:
        logger.error(f"Error initializing SocketIO service: {e}", exc_info=True)
        raise

    # Монтируем Socket.IO (на frontend мы работаем с /webapi/socket.io - маршрутизируется через api gateway)
    app.mount("/socket.io", socket_app)

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
    
    # Обработчики событий для подключения/отключения сервисов
    @app.on_event("startup")
    async def startup_event() -> None:
        """Действия при запуске приложения"""
        try:
            logger.info("Starting WebAPI service")
            logger.info(f"Hostname: {settings.HOSTNAME}")
            register_service()
            await redis_repository.connect()
            logger.info("Connected to Redis successfully")
            # await nats_service.connect()
            # logger.info("Connected to NATS successfully")
            logger.info("WebAPI service started successfully")
        except Exception as e:
            logger.critical(f"Failed to start WebAPI service: {e}", exc_info=True)
            # В продакшене здесь можно было бы добавить metrics.inc({'event': 'startup_failure'})
            # и возможно system exit(1)
    
    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Действия при остановке приложения"""
        try:
            logger.info("Shutting down WebAPI service")
            await redis_repository.disconnect()
            logger.info("Disconnected from Redis")
            await nats_service.disconnect()
            logger.info("Disconnected from NATS")
            logger.info("WebAPI service stopped successfully")
        except Exception as e:
            logger.error(f"Error during WebAPI service shutdown: {e}", exc_info=True)


    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

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
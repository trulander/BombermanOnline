import uvicorn
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aioprometheus import MetricsMiddleware
from aioprometheus.asgi.starlette import metrics
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError

from .config import settings
from .logging_config import configure_logging
from .routes.root import root_router
from .routes.api import api_router
from .routes.auth import auth_router
from .routes.frontend import frontend_router
from .dependencies import db, redis_client

# Настройка логирования
configure_logging()
logger = logging.getLogger(__name__)

try:
    # Инициализация FastAPI
    app = FastAPI(
        title=settings.APP_TITLE,
        docs_url=settings.SWAGGER_URL,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        debug=settings.DEBUG,
    )
    
    # Добавляем Prometheus метрики с помощью aioprometheus
    app.add_middleware(
        MetricsMiddleware,
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
    
    # Обработчик ошибок валидации
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc):
        logger.error(exc)
        current_user = getattr(request.state, "user", None)

        status_code = 400 if isinstance(exc, (RequestValidationError)) else 500
        message = getattr(exc, "message", str(exc))
        return JSONResponse(
            status_code=getattr(exc, "status_code", status_code),
            content={
                "detail": message
            }
        )
    
    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )
    
    # Подключаем статические файлы
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # Подключаем маршруты
    app.include_router(root_router)
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(auth_router, prefix="/auth")
    app.include_router(frontend_router)
    
    # Обработчики событий для подключения/отключения сервисов
    @app.on_event("startup")
    async def startup_event() -> None:
        """Действия при запуске приложения"""
        try:
            logger.info("Starting Auth service")
            await db.connect()
            logger.info("Connected to PostgreSQL successfully")
            await redis_client.connect()
            logger.info("Connected to Redis successfully")
            logger.info("Auth service started successfully")
        except Exception as e:
            logger.critical(f"Failed to start Auth service: {e}", exc_info=True)
            # В продакшене здесь можно было бы добавить metrics.inc({'event': 'startup_failure'})
    
    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Действия при остановке приложения"""
        try:
            logger.info("Shutting down Auth service")
            await db.disconnect()
            logger.info("Disconnected from PostgreSQL")
            await redis_client.disconnect()
            logger.info("Disconnected from Redis")
            logger.info("Auth service stopped successfully")
        except Exception as e:
            logger.error(f"Error during Auth service shutdown: {e}", exc_info=True)

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
import socket

import consul
import uvicorn
import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from aioprometheus import MetricsMiddleware
from aioprometheus.asgi.starlette import metrics
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings
from .logging_config import configure_logging
from .routes.root import root_router
from .routes.api import api_router
from .routes.frontend import frontend_router, templates
from .dependencies import db, redis_client

# Настройка логирования
configure_logging()
logger = logging.getLogger(__name__)


def register_service():
    logger.info(f"registering in the consul service")
    service_name = settings.SERVICE_NAME
    c = consul.Consul(host=settings.CONSUL_HOST, port=8500)
    service_id = f"{service_name}-{socket.gethostname()}"
    c.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=socket.gethostname(),  # Имя сервиса в Docker сети
        port=settings.PORT,
        tags=["traefik"],
        check=consul.Check.http(
            url=f"http://{socket.gethostname()}:{settings.PORT}/health",
            interval="10s",
            timeout="1s",
            deregister="60s"
        )
    )

# try:
# Инициализация FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    docs_url=settings.SWAGGER_URL,
    openapi_url=f"{settings.SWAGGER_URL}/openapi.json",
    debug=settings.DEBUG,
)

# Добавляем Prometheus метрики с помощью aioprometheus
app.add_middleware(
    MetricsMiddleware,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


app.add_route("/metrics", metrics)
# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
# Подключаем маршруты
app.include_router(root_router)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(frontend_router)


def unhandled_exception_handler(
    request: Request,
    exception: Exception,
):
    logger.error(f"Unhandled exception: {exception}", exc_info=True)
    status_code = status.HTTP_400_BAD_REQUEST if isinstance(exception, (
        RequestValidationError)) else status.HTTP_500_INTERNAL_SERVER_ERROR
    if request.url.path.startswith("/ui/"):
        # Для UI-маршрутов используем Jinja2 шаблоны
        return Jinja2Templates(directory=settings.TEMPLATES_DIR).TemplateResponse(
            "error.html",
            {
                "request": request, "message": str(exception)
            },
            status_code=status_code,
        )
    else:
        return JSONResponse(
            status_code=status_code,
            content={"detail": "Произошла непредвиденная ошибка на сервере", "error": str(exception)}
        )

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return unhandled_exception_handler(request=request, exception=exc)

app.add_middleware(ErrorHandlingMiddleware)

# Глобальный обработчик исключений
@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
@app.exception_handler(RequestValidationError)
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return unhandled_exception_handler(request=request, exception=exc)


# Обработчики событий для подключения/отключения сервисов
@app.on_event("startup")
async def startup_event() -> None:
    """Действия при запуске приложения"""
    try:
        logger.info("Starting Auth service")
        register_service()
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



# except Exception as e:
#     logger.critical(f"Failed to initialize application: {str(e)}\n{traceback.format_exc()}")
#     raise

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
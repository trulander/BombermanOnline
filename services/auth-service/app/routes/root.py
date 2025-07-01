from fastapi import APIRouter, Response
import logging

from ..config import settings
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import status

logger = logging.getLogger(__name__)

root_router = APIRouter()


# Корневой маршрут
@root_router.get("/", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND)
async def root():
    return "/ui/login"

# @root_router.get("/")
# async def root() -> dict:
#     """Корневой маршрут для проверки состояния сервиса"""
#     return {
#         "service": "auth-service",
#         "version": "1.0.0",
#         "status": "running"
#     }

@root_router.get("/health")
async def health_check() -> dict:
    """Маршрут для проверки работоспособности сервиса"""
    return {
        "status": "healthy",
        "service": "auth-service"
    }

@root_router.get("/ping")
async def ping() -> Response:
    """Простой пинг для проверки доступности"""
    return Response(content="pong", media_type="text/plain")
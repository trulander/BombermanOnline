from fastapi import APIRouter, Response
import logging

from ..config import settings

logger = logging.getLogger(__name__)

root_router = APIRouter()

@root_router.get("/")
async def root() -> dict:
    """Корневой маршрут для проверки состояния сервиса"""
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "status": "running"
    }

@root_router.get("/health")
async def health_check() -> dict:
    """Маршрут для проверки работоспособности сервиса"""
    return {
        "status": "ok",
        "service": "auth-service"
    }

@root_router.get("/ping")
async def ping() -> Response:
    """Простой пинг для проверки доступности"""
    return Response(content="pong", media_type="text/plain")
from fastapi import APIRouter

from .api_v1 import game_routes

api_router = APIRouter()

# Регистрация маршрутов API v1
api_router.include_router(
    game_routes.router,
    prefix="/games",
    tags=["games"]
) 
from fastapi import APIRouter

from app.config import settings
from app.routes.api_v1.game_routes import game_router
from app.routes.root import root_router

router = APIRouter()
router.include_router(game_router, prefix=settings.API_V1_STR)
router.include_router(root_router)

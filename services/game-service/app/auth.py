from fastapi import Request, HTTPException, status
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Dict[str, str]:
    """Получить текущего пользователя из состояния запроса"""
    user = getattr(request.state, 'user', None)
    if not user:
        logger.warning("Unauthenticated request attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin(request: Request) -> Dict[str, str]:
    """Получить текущего администратора из состояния запроса"""
    user = await get_current_user(request)
    
    if user.get("role") != "admin":
        logger.warning(f"User {user.get('id')} attempted admin action without permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permissions required"
        )
    
    return user


def get_optional_user(request: Request) -> Optional[Dict[str, str]]:
    """Получить пользователя если он аутентифицирован, иначе None"""
    return getattr(request.state, 'user', None) 
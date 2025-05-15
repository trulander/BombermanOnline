from fastapi import Depends, HTTPException, status, Request
import logging

logger = logging.getLogger(__name__)

async def get_current_user(request: Request):
    """Получает текущего пользователя из state запроса"""
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user

async def get_current_admin(request: Request):
    """Получает текущего администратора из state запроса"""
    user = await get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return user 
from typing import Optional

from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from jose import jwt
from ..dependencies import get_db
from ..config import settings
from ..models.user import User

from ..services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

async def get_current_user(
    request: Request,
    token: str = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Получение текущего пользователя по JWT токену из cookie
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        # Проверяем Authorization заголовок для совместимости с API клиентами
        auth_header = request.headers.get("Authorization")
        if auth_header:
            scheme, _, token_value = auth_header.partition(" ")
            if scheme.lower() == "bearer":
                token = token_value
        
        if not token:
            raise credentials_exception
    
    # Если токен из cookie начинается с "Bearer ", удаляем этот префикс
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_user_optional(
    request: Request,
    token: str = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Получение текущего пользователя, если он авторизован
    """
    try:
        return await get_current_user(request, token, db)
    except HTTPException:
        return None 
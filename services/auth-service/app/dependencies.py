from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from typing import Annotated
import logging
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .database import db
from .redis_client import redis_client
from .config import settings
from .models.token import TokenPayload
from .models.user import User, UserRole
from .services.user_service import UserService

logger = logging.getLogger(__name__)

# Определяем OAuth2 схему
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scopes={
        "user": "Базовый доступ пользователя",
        "admin": "Административный доступ",
        "moderator": "Доступ модератора",
        "developer": "Доступ разработчика",
    },
)

# Зависимость для получения текущего пользователя
async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Проверяем, что токен не в черном списке
        if await redis_client.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен недействителен",
                headers={"WWW-Authenticate": authenticate_value},
            )
        
        # Декодируем токен
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Извлекаем данные пользователя из токена
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
        
        # Проверяем срок действия токена
        if token_data.exp is None:
            raise credentials_exception
        
        # Проверяем роль пользователя и требуемые разрешения
        if security_scopes.scopes and token_data.role not in security_scopes.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этому ресурсу",
                headers={"WWW-Authenticate": authenticate_value},
            )
        
        # Получаем пользователя из базы данных
        async with db.get_session() as session:
            user_service = UserService(session)
            user = await user_service.get_by_id(token_data.sub)
            
            if user is None:
                raise credentials_exception
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Пользователь деактивирован",
                )
            
            return user
            
    except (JWTError, ValueError):
        raise credentials_exception

# Зависимость для получения текущего пользователя с ролью admin
async def get_admin_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["admin"])],
) -> User:
    return current_user

# Зависимость для получения текущего пользователя с ролью модератора
async def get_moderator_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["moderator", "admin"])],
) -> User:
    return current_user

# Зависимость для получения текущего пользователя с ролью разработчика
async def get_developer_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["developer", "admin"])],
) -> User:
    return current_user

# Зависимость для получения сессии базы данных
async def get_db() -> AsyncSession:
    async with db.get_session() as session:
        yield session 
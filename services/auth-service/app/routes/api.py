from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Response, Header, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import logging
from datetime import datetime, UTC
from jose import jwt, JWTError

from ..dependencies import get_db, get_current_user, get_admin_user
from ..models.user import User, UserCreate, UserResponse, UserUpdate, UserSearchResponse, UserRole
from ..models.token import Token, RefreshTokenRequest, LoginForm, TokenPayload
from ..services.user_service import UserService
from ..services.token_service import TokenService
from ..services.oauth_service import OAuthService
from ..config import settings
from ..redis_client import redis_client

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Маршруты для аутентификации
@api_router.post("/auth/login", response_model=Token)
async def login(
    form_data: Annotated[LoginForm, Body(...)],
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Аутентификация пользователя и получение токенов"""
    user_service = UserService(db)
    token_service = TokenService(db)
    
    user = await user_service.authenticate(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )
    
    logger.info(f"User {user.username} logged in successfully")
    
    # Получаем IP адрес и User-Agent клиента
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    # Создаем токены
    return await token_service.create_tokens_for_user(
        user=user,
        remember_me=form_data.remember_me,
        ip_address=ip_address,
        user_agent=user_agent
    )

@api_router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    refresh_data: Annotated[RefreshTokenRequest, Body(...)],
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Обновление токенов"""
    token_service = TokenService(db)
    
    # Получаем IP адрес и User-Agent клиента
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    tokens = await token_service.refresh_tokens(
        refresh_token=refresh_data.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not tokens:
        logger.warning(f"Failed token refresh attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Tokens refreshed successfully")
    return tokens

@api_router.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    token: str = Depends(get_current_user.dependencies[0]),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Выход из системы и отзыв токена"""
    token_service = TokenService(db)
    
    # Отзываем токен
    success = await token_service.revoke_token(token)
    
    # Очищаем куки если они есть
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    if success:
        logger.info(f"User logged out successfully")
        return {"message": "Выход выполнен успешно"}
    else:
        logger.warning(f"Logout failed")
        return {"message": "Выход не выполнен"}

# Маршруты для пользователей
@api_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: Annotated[UserCreate, Body(...)],
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Создание нового пользователя"""
    user_service = UserService(db)
    
    # Проверяем, что пользователь с таким email не существует
    existing_user = await user_service.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    
    # Проверяем, что пользователь с таким username не существует
    existing_user = await user_service.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем пользователя уже существует",
        )
    
    # Создаем пользователя
    user = await user_service.create(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать пользователя",
        )
    
    logger.info(f"User {user.username} created successfully")
    
    # Преобразуем SQLAlchemy модель в Pydantic
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        profile_image=user.profile_image,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )

@api_router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Получение информации о текущем пользователе"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        profile_image=current_user.profile_image,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )

@api_router.put("/users/me", response_model=UserResponse)
async def update_current_user(
    user_data: Annotated[UserUpdate, Body(...)],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Обновление информации о текущем пользователе"""
    user_service = UserService(db)
    
    # Обновляем пользователя
    user = await user_service.update(current_user.id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить пользователя",
        )
    
    logger.info(f"User {user.username} updated their profile")
    
    # Преобразуем SQLAlchemy модель в Pydantic
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        profile_image=user.profile_image,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),  # Только авторизованные пользователи
) -> UserResponse:
    """Получение информации о пользователе по ID"""
    user_service = UserService(db)
    
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    # Преобразуем SQLAlchemy модель в Pydantic
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        profile_image=user.profile_image,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )

@api_router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role: Annotated[str, Body(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # Только админы могут менять роли
) -> UserResponse:
    """Обновление роли пользователя"""
    user_service = UserService(db)
    
    # Проверяем, что роль корректная
    if role not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некорректная роль. Допустимые роли: {', '.join([r.value for r in UserRole])}",
        )
    
    # Обновляем роль пользователя
    user = await user_service.update_role(user_id, role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    
    logger.info(f"User {user.username} role updated to {role} by admin {current_user.username}")
    
    # Преобразуем SQLAlchemy модель в Pydantic
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        profile_image=user.profile_image,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )

@api_router.get("/users", response_model=UserSearchResponse)
async def search_users(
    query: str = None,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),  # Только авторизованные пользователи
) -> UserSearchResponse:
    """Поиск пользователей"""
    user_service = UserService(db)
    
    # Проверка параметров пагинации
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 10
    
    # Поиск пользователей
    return await user_service.search(query, page, size)

# OAuth маршруты для авторизации через внешних провайдеров
@api_router.get("/auth/oauth/{provider}")
async def oauth_login(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Начало процесса OAuth авторизации"""
    oauth_service = OAuthService(db)
    
    # Проверяем, что провайдер поддерживается
    if provider not in ["google"]:  # Список поддерживаемых провайдеров
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый OAuth провайдер",
        )
    
    # Генерируем state для защиты от CSRF
    state = oauth_service.generate_oauth_state()
    
    # Сохраняем state в сессии (в реальном приложении)
    # request.session["oauth_state"] = state
    
    # Генерируем URL для редиректа
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    authorize_url = oauth_service.get_provider_authorize_url(provider, redirect_uri, state)
    
    if not authorize_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать URL авторизации",
        )
    
    return {"authorize_url": authorize_url}

@api_router.get("/auth/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Обработка callback от OAuth провайдера"""
    oauth_service = OAuthService(db)
    
    # Проверяем, что провайдер поддерживается
    if provider not in ["google"]:  # Список поддерживаемых провайдеров
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый OAuth провайдер",
        )
    
    # В реальном приложении здесь нужно проверить state из сессии
    # stored_state = request.session.get("oauth_state")
    # if not stored_state or stored_state != state:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Недействительный state",
    #     )
    
    # Обмениваем код на токен
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    oauth_response = await oauth_service.exchange_code_for_token(provider, code, redirect_uri)
    
    if not oauth_response or not oauth_response.access_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить токен",
        )
    
    # Получаем информацию о пользователе
    user_info = await oauth_service.get_user_info(provider, oauth_response.access_token)
    
    if not user_info or not user_info.email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить информацию о пользователе",
        )
    
    # Получаем IP адрес и User-Agent клиента
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    # Аутентифицируем пользователя в нашей системе
    result = await oauth_service.authenticate_oauth_user(
        provider=provider,
        user_info=user_info,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Ошибка аутентификации"),
        )
    
    # В реальном приложении здесь можно сохранить токены в куки или сессии
    
    return {
        "message": "OAuth аутентификация успешна",
        "user": result["user"],
        "tokens": result["tokens"]
    }

# Новый обработчик для проверки токена (используется в Traefik)
@api_router.get("/auth/check")
async def check_auth(
    request: Request,
    redirect: bool = Query(False),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Проверка JWT токена для использования в Traefik Forward Auth middleware"""
    try:
        token_service = TokenService(db)
        
        # Проверяем наличие токена в заголовке Authorization
        if not authorization or not authorization.startswith("Bearer "):
            if redirect:
                # Если требуется редирект и токен отсутствует или невалиден,
                # перенаправляем на страницу авторизации
                return RedirectResponse(url="/ui/login")
            else:
                # Если токен отсутствует или невалиден, возвращаем 401
                return Response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        # Извлекаем токен из заголовка
        token = authorization.replace("Bearer ", "")
        
        # Проверяем, что токен не в черном списке
        if await redis_client.is_token_blacklisted(token):
            if redirect:
                return RedirectResponse(url="/ui/login")
            else:
                return Response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
        # Декодируем токен
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Извлекаем данные пользователя из токена
            token_data = TokenPayload(**payload)
            
            # Проверяем срок действия токена
            if token_data.exp is None or datetime.now(UTC).timestamp() > token_data.exp:
                if redirect:
                    return RedirectResponse(url="/ui/login")
                else:
                    return Response(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            # Получаем пользователя из базы данных
            user_service = UserService(db)
            user = await user_service.get_by_id(token_data.sub)
            
            if not user or not user.is_active:
                if redirect:
                    return RedirectResponse(url="/ui/login")
                else:
                    return Response(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            # Возвращаем успешный ответ с информацией о пользователе в заголовках
            return Response(
                status_code=status.HTTP_200_OK,
                headers={
                    "X-User-ID": str(user.id),
                    "X-User-Role": user.role,
                    "X-User-Email": user.email,
                    "X-User-Name": user.username
                }
            )
            
        except (JWTError, ValueError):
            if redirect:
                return RedirectResponse(url="/ui/login")
            else:
                return Response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
    except Exception as e:
        logger.error(f"Error checking auth: {e}", exc_info=True)
        if redirect:
            return RedirectResponse(url="/ui/login")
        else:
            return Response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) 
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import logging
from datetime import datetime, UTC

from ..dependencies import get_db
from ..models.token import LoginForm, RefreshTokenRequest, PasswordResetRequest, PasswordReset
from ..services.user_service import UserService
from ..services.token_service import TokenService
from ..services.oauth_service import OAuthService

logger = logging.getLogger(__name__)

auth_router = APIRouter()

@auth_router.get("/login")
async def login_page(request: Request):
    """Страница авторизации"""
    # В реальном приложении здесь будет отображение страницы авторизации через шаблон
    # return templates.TemplateResponse("login.html", {"request": request})
    logger.info("Страница логина")
    # Временно возвращаем информацию о странице
    return {"message": "Страница авторизации"}

@auth_router.get("/register")
async def register_page(request: Request):
    """Страница регистрации"""
    # В реальном приложении здесь будет отображение страницы регистрации через шаблон
    # return templates.TemplateResponse("register.html", {"request": request})

    # Временно возвращаем информацию о странице
    return {"message": "Страница регистрации"}

@auth_router.post("/register")
async def register(
    email: Annotated[str, Form()],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    full_name: Annotated[str, Form()] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Обработка формы регистрации"""
    user_service = UserService(db)
    
    # Проверяем, что пользователь с таким email не существует
    existing_user = await user_service.get_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    
    # Проверяем, что пользователь с таким username не существует
    existing_user = await user_service.get_by_username(username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем пользователя уже существует",
        )
    
    # Создаем пользователя
    from ..models.user import UserCreate
    user_data = UserCreate(
        email=email,
        username=username,
        password=password,
        full_name=full_name
    )
    
    user = await user_service.create(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать пользователя",
        )
    
    logger.info(f"User {user.username} registered successfully")
    
    # Перенаправляем на страницу авторизации
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

@auth_router.get("/reset-password")
async def reset_password_page(request: Request):
    """Страница сброса пароля"""
    # В реальном приложении здесь будет отображение страницы сброса пароля через шаблон
    # return templates.TemplateResponse("reset_password.html", {"request": request})
    
    # Временно возвращаем информацию о странице
    return {"message": "Страница сброса пароля"}

@auth_router.post("/reset-password")
async def reset_password(
    reset_data: Annotated[PasswordResetRequest, Form()],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Обработка запроса на сброс пароля"""
    user_service = UserService(db)
    
    # Проверяем, существует ли пользователь с таким email
    user = await user_service.get_by_email(reset_data.email)
    if not user:
        # В целях безопасности не сообщаем, что пользователь не найден
        logger.warning(f"Password reset attempt for non-existent email: {reset_data.email}")
        return {"message": "Если пользователь с таким email существует, на него отправлена инструкция по сбросу пароля"}
    
    # Генерируем новый токен верификации
    token = await user_service.regenerate_verification_token(user.id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать токен сброса пароля",
        )
    
    # В реальном приложении здесь будет отправка email с ссылкой для сброса пароля
    # Например: f"{request.base_url}auth/confirm-reset-password?token={token}"
    
    logger.info(f"Password reset token generated for user {user.id}")
    
    # Возвращаем сообщение об успешной отправке
    return {"message": "Инструкция по сбросу пароля отправлена на указанный email"}

@auth_router.get("/confirm-reset-password")
async def confirm_reset_password_page(token: str, request: Request):
    """Страница подтверждения сброса пароля"""
    # В реальном приложении здесь будет отображение страницы для ввода нового пароля
    # return templates.TemplateResponse("confirm_reset_password.html", {"request": request, "token": token})
    
    # Временно возвращаем информацию о странице
    return {"message": "Страница подтверждения сброса пароля", "token": token}

@auth_router.post("/confirm-reset-password")
async def confirm_reset_password(
    reset_data: Annotated[PasswordReset, Form()],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Обработка формы сброса пароля"""
    user_service = UserService(db)
    
    # Находим пользователя по токену
    result = await user_service.db.execute(
        "SELECT id FROM users WHERE verification_token = :token",
        {"token": reset_data.token}
    )
    user_id = result.scalar()
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный токен сброса пароля",
        )
    
    # Обновляем пароль
    success = await user_service.update_password(user_id, reset_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить пароль",
        )
    
    # Сбрасываем токен верификации
    user = await user_service.get_by_id(user_id)
    user.verification_token = None
    await user_service.db.commit()
    
    logger.info(f"Password reset completed for user {user_id}")
    
    # Перенаправляем на страницу авторизации
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

@auth_router.get("/verify-email")
async def verify_email(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Подтверждение email пользователя"""
    user_service = UserService(db)
    
    # Подтверждаем email
    success = await user_service.verify_email(token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный токен подтверждения email",
        )
    
    logger.info(f"Email verified with token {token}")
    
    # Перенаправляем на страницу авторизации
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER) 
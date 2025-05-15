from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import os
from pathlib import Path

from ..config import settings


from ..services.auth import get_current_user_optional
from ..models.user import User

logger = logging.getLogger(__name__)

# Создаем директорию для шаблонов и проверяем ее существование
templates_dir = Path(settings.TEMPLATES_DIR)
if not templates_dir.exists():
    os.makedirs(templates_dir, exist_ok=True)

# Инициализируем шаблонизатор
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

frontend_router = APIRouter(prefix="/ui", tags=["frontend"])

@frontend_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/ui/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request})

@frontend_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/ui/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("register.html", {"request": request})

@frontend_router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/ui/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("reset_password.html", {"request": request})

@frontend_router.get("/confirm-reset-password", response_class=HTMLResponse)
async def confirm_reset_password_page(request: Request, token: str = None, user: User = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/ui/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    if not token:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Не указан токен для сброса пароля."})
    return templates.TemplateResponse("confirm_reset_password.html", {"request": request, "token": token})

@frontend_router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, token: str = None, user: User = Depends(get_current_user_optional)):
    if not token:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Не указан токен для подтверждения электронной почты."})
    return templates.TemplateResponse("verify_email.html", {"request": request, "token": token})

@frontend_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@frontend_router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: User = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@frontend_router.get("/ui", response_class=HTMLResponse)
async def ui_root(request: Request):
    """Корневой маршрут для UI - перенаправляет на страницу авторизации или дашборд"""
    try:
        return RedirectResponse(url="/ui/login")
    except Exception as e:
        logger.error(f"Error in ui_root: {e}", exc_info=True)
        return RedirectResponse(url="/ui/login") 
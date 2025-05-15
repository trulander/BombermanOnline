from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import os
from pathlib import Path

from ..config import settings
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

# Создаем директорию для шаблонов и проверяем ее существование
templates_dir = Path(settings.TEMPLATES_DIR)
if not templates_dir.exists():
    os.makedirs(templates_dir, exist_ok=True)

# Инициализируем шаблонизатор
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

frontend_router = APIRouter()

@frontend_router.get("/ui/login", response_class=HTMLResponse)
async def login_ui(request: Request):
    """Страница авторизации"""
    # В реальном приложении здесь должен быть шаблон для отрисовки
    try:
        # return templates.TemplateResponse("login.html", {"request": request})
        
        # Временная заглушка пока нет шаблонов
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Авторизация - Bomberman Online</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .container {
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 30px;
                    width: 350px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    color: #555;
                }
                input[type="text"], input[type="password"], input[type="email"] {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #45a049;
                }
                .links {
                    text-align: center;
                    margin-top: 20px;
                }
                .links a {
                    color: #2196F3;
                    text-decoration: none;
                    margin: 0 10px;
                }
                .oauth-container {
                    margin-top: 20px;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                    text-align: center;
                }
                .oauth-button {
                    background-color: #fff;
                    border: 1px solid #ddd;
                    padding: 10px;
                    border-radius: 4px;
                    display: inline-flex;
                    align-items: center;
                    margin: 5px;
                    cursor: pointer;
                }
                .oauth-button img {
                    margin-right: 10px;
                    width: 20px;
                    height: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Авторизация</h1>
                <form action="/api/v1/auth/login" method="post">
                    <div class="form-group">
                        <label for="username">Имя пользователя или Email</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Пароль</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <input type="checkbox" id="remember_me" name="remember_me" value="true">
                        <label for="remember_me" style="display: inline;">Запомнить меня</label>
                    </div>
                    <button type="submit">Войти</button>
                </form>
                <div class="links">
                    <a href="/ui/register">Регистрация</a>
                    <a href="/ui/reset-password">Забыли пароль?</a>
                </div>
                <div class="oauth-container">
                    <p>Или войдите через:</p>
                    <a href="/api/v1/auth/oauth/google" class="oauth-button">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" alt="Google">
                        Google
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering login page: {e}", exc_info=True)
        return HTMLResponse(content="<h1>Ошибка загрузки страницы</h1>")

@frontend_router.get("/ui/register", response_class=HTMLResponse)
async def register_ui(request: Request):
    """Страница регистрации"""
    # В реальном приложении здесь должен быть шаблон для отрисовки
    try:
        # return templates.TemplateResponse("register.html", {"request": request})
        
        # Временная заглушка пока нет шаблонов
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Регистрация - Bomberman Online</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .container {
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 30px;
                    width: 350px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    color: #555;
                }
                input[type="text"], input[type="password"], input[type="email"] {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #45a049;
                }
                .links {
                    text-align: center;
                    margin-top: 20px;
                }
                .links a {
                    color: #2196F3;
                    text-decoration: none;
                    margin: 0 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Регистрация</h1>
                <form action="/auth/register" method="post">
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="username">Имя пользователя</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Пароль</label>
                        <input type="password" id="password" name="password" 
                               pattern="(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}" 
                               title="Пароль должен содержать минимум 8 символов, включая буквы и цифры" required>
                    </div>
                    <div class="form-group">
                        <label for="full_name">Полное имя (опционально)</label>
                        <input type="text" id="full_name" name="full_name">
                    </div>
                    <button type="submit">Зарегистрироваться</button>
                </form>
                <div class="links">
                    <a href="/ui/login">Уже есть аккаунт? Войти</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering registration page: {e}", exc_info=True)
        return HTMLResponse(content="<h1>Ошибка загрузки страницы</h1>")

@frontend_router.get("/ui/reset-password", response_class=HTMLResponse)
async def reset_password_ui(request: Request):
    """Страница сброса пароля"""
    # В реальном приложении здесь должен быть шаблон для отрисовки
    try:
        # return templates.TemplateResponse("reset_password.html", {"request": request})
        
        # Временная заглушка пока нет шаблонов
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Сброс пароля - Bomberman Online</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .container {
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 30px;
                    width: 350px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    color: #555;
                }
                input[type="email"] {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #45a049;
                }
                .links {
                    text-align: center;
                    margin-top: 20px;
                }
                .links a {
                    color: #2196F3;
                    text-decoration: none;
                    margin: 0 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Сброс пароля</h1>
                <form action="/auth/reset-password" method="post">
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <button type="submit">Отправить инструкции</button>
                </form>
                <div class="links">
                    <a href="/ui/login">Вернуться к авторизации</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering reset password page: {e}", exc_info=True)
        return HTMLResponse(content="<h1>Ошибка загрузки страницы</h1>")

@frontend_router.get("/ui/dashboard", response_class=HTMLResponse)
async def dashboard_ui(request: Request, current_user = Depends(get_current_user)):
    """Dashboard пользователя (только для авторизованных)"""
    # В реальном приложении здесь должен быть шаблон для отрисовки
    try:
        # return templates.TemplateResponse("dashboard.html", {
        #     "request": request, 
        #     "user": current_user
        # })
        
        # Временная заглушка пока нет шаблонов
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Личный кабинет - Bomberman Online</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 30px;
                    max-width: 800px;
                    margin: 40px auto;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
                .user-info {{
                    margin-bottom: 30px;
                }}
                .user-info p {{
                    margin: 5px 0;
                }}
                .user-info .label {{
                    font-weight: bold;
                    display: inline-block;
                    width: 150px;
                }}
                .actions {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                }}
                .btn {{
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin-right: 10px;
                }}
                .btn-danger {{
                    background-color: #f44336;
                }}
                .btn:hover {{
                    opacity: 0.9;
                }}
                .role-badge {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 15px;
                    background-color: #2196F3;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    margin-left: 10px;
                }}
                .role-admin {{
                    background-color: #f44336;
                }}
                .role-moderator {{
                    background-color: #ff9800;
                }}
                .role-developer {{
                    background-color: #9c27b0;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Личный кабинет</h1>
                    <span class="role-badge role-{current_user.role}">{current_user.role.upper()}</span>
                </div>
                <div class="user-info">
                    <p><span class="label">Имя пользователя:</span> {current_user.username}</p>
                    <p><span class="label">Email:</span> {current_user.email}</p>
                    <p><span class="label">Полное имя:</span> {current_user.full_name or 'Не указано'}</p>
                    <p><span class="label">Email подтвержден:</span> {'Да' if current_user.is_verified else 'Нет'}</p>
                    <p><span class="label">Дата регистрации:</span> {current_user.created_at.strftime('%d.%m.%Y %H:%M')}</p>
                </div>
                <div class="actions">
                    <a href="/ui/profile/edit" class="btn">Редактировать профиль</a>
                    <a href="/ui/play" class="btn">Играть</a>
                    <a href="/api/v1/auth/logout" class="btn btn-danger">Выйти</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering dashboard page: {e}", exc_info=True)
        return HTMLResponse(content="<h1>Ошибка загрузки страницы</h1>")

@frontend_router.get("/ui", response_class=HTMLResponse)
async def ui_root(request: Request):
    """Корневой маршрут для UI - перенаправляет на страницу авторизации или дашборд"""
    try:
        # Проверяем есть ли токен в кукисах или сессии
        # В реальном приложении здесь будет проверка токена
        # token = request.cookies.get("access_token") or request.session.get("access_token")
        # if token:
        #     # Проверяем валидность токена
        #     # Если токен валиден, перенаправляем на дашборд
        #     return RedirectResponse(url="/ui/dashboard")
        # else:
        #     # Если нет токена или он невалиден, перенаправляем на страницу авторизации
        return RedirectResponse(url="/ui/login")
    except Exception as e:
        logger.error(f"Error in ui_root: {e}", exc_info=True)
        return RedirectResponse(url="/ui/login") 
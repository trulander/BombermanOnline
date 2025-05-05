from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

root_router = APIRouter()


@root_router.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Обработчик корневого маршрута - отдает фронтенд"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bomberman Online</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #333; }
            p { max-width: 600px; margin: 20px auto; }
        </style>
    </head>
    <body>
        <h1>Bomberman Online</h1>
        <p>Сервер игры работает. Используйте клиентское приложение для подключения.</p>
        <center><a href="http://localhost:3000/">http://localhost:3000/</a></center>
    </body>
    </html>
    """)

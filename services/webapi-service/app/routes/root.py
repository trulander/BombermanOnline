from fastapi import APIRouter
from fastapi.responses import HTMLResponse


root_router = APIRouter()

@root_router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """
    Корневой эндпоинт приложения.
    Просто отображает ссылку на клиента.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Bomberman Online - API Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 30px;
                    background-color: #f4f4f4;
                }
                
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                
                h1 {
                    color: #333;
                }
                
                a {
                    display: inline-block;
                    margin-top: 15px;
                    padding: 10px 15px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                
                a:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Bomberman Online - API Server</h1>
                <p>Добро пожаловать на сервер API Bomberman Online!</p>
                <p>Запустите клиент для игры:</p>
                <a href="/docs">API Documentation</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content) 
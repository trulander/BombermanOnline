import os
import uuid
import asyncio
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

import socketio
from socketio import AsyncServer

from game.game import Game
from game.player import Player

# Создаем FastAPI приложение
app = FastAPI(title="Bomberman Online")

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем сервер Socket.IO
sio: AsyncServer = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

# Создаем приложение Socket.IO
socket_app = socketio.ASGIApp(sio)

# Монтируем Socket.IO приложение под путь "/socket.io/"
app.mount("/socket.io", socket_app)

# Если есть статические файлы, монтируем их
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Создаем словарь для хранения активных игр
games: Dict[str, Game] = {}

# Словарь для хранения соответствия между сессией и идентификатором игры
session_game_map: Dict[str, str] = {}

# Функция для обновления игрового состояния
async def game_loop() -> None:
    """Фоновая задача для обновления игрового состояния и отправки обновлений клиентам"""
    while True:
        for game_id, game in list(games.items()):
            if game.is_active():
                updated_state = game.update()
                await sio.emit("game_update", updated_state, room=game_id)
            else:
                # Игра окончена, отправляем уведомление всем игрокам и удаляем игру
                for player_id in game.players:
                    await sio.emit("game_over", room=player_id)
                del games[game_id]

        # Обновляем примерно 30 раз в секунду
        await asyncio.sleep(0.023)

# Запускаем игровой цикл при старте приложения
@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(game_loop())

# Обработчики Socket.IO событий
@sio.event
async def connect(sid: str, environ: Dict[str, Any]) -> None:
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")
    
    # Удаляем игрока из игры, если он был в какой-то игре
    game_id = session_game_map.get(sid)
    if game_id and game_id in games:
        game = games[game_id]
        game.remove_player(sid)

        # Если игра пуста, удаляем ее
        if len(game.players) == 0:
            del games[game_id]
        else:
            # Уведомляем других игроков
            await sio.emit('player_disconnected', {'player_id': sid}, room=game_id)
        
        # Удаляем из словаря соответствия
        del session_game_map[sid]

@sio.event
async def create_game(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Создать новую игру"""
    game_id = str(uuid.uuid4())
    games[game_id] = Game()
    return {'game_id': game_id}

@sio.event
async def join_game(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Присоединиться к существующей игре"""
    game_id = data['game_id']
    if game_id not in games:
        return {'success': False, 'message': 'Game not found'}
    
    player = Player(sid)
    success = games[game_id].add_player(player)
    
    if success:
        # Присоединить игрока к комнате
        await sio.enter_room(sid, game_id)
        
        # Сохраняем соответствие между сессией и игрой
        session_game_map[sid] = game_id
        
        # Отправляем начальное состояние игры
        game_state = games[game_id].get_state()
        return {
            'success': True, 
            'player_id': sid,
            'game_state': game_state
        }
    else:
        return {'success': False, 'message': 'Game is full'}

@sio.event
async def input(sid: str, data: Dict[str, Any]) -> None:
    """Обработать ввод игрока"""
    game_id = data.get('game_id')
    inputs = data.get('inputs')
    
    if game_id in games:
        game = games[game_id]
        player = game.get_player(sid)
        
        if player:
            player.set_inputs(inputs)

@sio.event
async def place_bomb(sid: str, data: Dict[str, Any]) -> None:
    """Разместить бомбу"""
    game_id = data.get('game_id')
    
    if game_id in games:
        game = games[game_id]
        player = game.get_player(sid)
        
        if player:
            success = game.place_bomb(player)
            if success:
                # Отправляем обновленное состояние игры
                updated_state = game.get_state()
                await sio.emit('game_update', updated_state, room=game_id)

# Маршруты FastAPI
@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Обработчик корневого маршрута - отдает фронтенд"""
    # Если есть статические файлы, они будут обслуживаться через StaticFiles
    # Если нет, возвращаем простую HTML страницу
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
    </body>
    </html>
    """)

# Запуск приложения, если файл запущен напрямую
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True) 
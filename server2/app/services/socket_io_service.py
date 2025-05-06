import uuid
import asyncio
from typing import Dict, Any

import socketio
from socketio import AsyncServer

from app.config import settings
from app.repositories.redis_repository import RedisRepository
from app.repositories.postgres_repository import PostgresRepository

from app.entities.player import Player
from app.services.game_service import GameService


class SocketIOService:
    def __init__(self) -> None:
        self.sio: AsyncServer = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*"
        )
        self.games: Dict[str, GameService] = {}
        self.session_game_map: Dict[str, str] = {}
        self.redis_repo = RedisRepository()
        self.postgres_repo = PostgresRepository()
        
        # Регистрируем обработчики событий Socket.IO
        self.register_handlers()
    
    def register_handlers(self) -> None:
        """Регистрация обработчиков событий Socket.IO"""
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)
        self.sio.on("create_game", self.handle_create_game)
        self.sio.on("join_game", self.handle_join_game)
        self.sio.on("input", self.handle_input)
        self.sio.on("place_bomb", self.handle_place_bomb)
        self.sio.on("get_game_state", self.handle_get_game_state)
    
    async def start_game_loop(self) -> None:
        """Запуск игрового цикла"""
        while True:
            for game_id, game in list(self.games.items()):
                if game.is_active():
                    updated_state = game.update()
                    await self.sio.emit("game_update", updated_state, room=game_id)
                else:
                    # Игра окончена, отправляем уведомление всем игрокам
                    for player_id in game.players:
                        await self.sio.emit("game_over", room=player_id)
                    del self.games[game_id]
            
            await asyncio.sleep(settings.GAME_UPDATE_RATE)
    
    async def handle_connect(self, sid: str, environ: Dict[str, Any]) -> None:
        """Обработка подключения клиента"""
        print(f"Client connected: {sid}")
    
    async def handle_disconnect(self, sid: str) -> None:
        """Обработка отключения клиента"""
        print(f"Client disconnected: {sid}")
        
        game_id = self.session_game_map.get(sid)
        if game_id and game_id in self.games:
            game = self.games[game_id]
            game.remove_player(sid)
            
            if len(game.players) == 0:
                del self.games[game_id]
            else:
                await self.sio.emit('player_disconnected', {'player_id': sid}, room=game_id)
            
            del self.session_game_map[sid]
    
    async def handle_create_game(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание новой игры"""
        game_id = str(uuid.uuid4())
        self.games[game_id] = GameService()
        return {'game_id': game_id}
    
    async def handle_join_game(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Присоединение к существующей игре"""
        game_id = data['game_id']
        if game_id not in self.games:
            return {'success': False, 'message': 'Game not found'}
        
        player = Player(sid)
        success = self.games[game_id].add_player(player)
        
        if success:
            await self.sio.enter_room(sid, game_id)
            self.session_game_map[sid] = game_id
            
            # Получаем начальное состояние игры с данными для текущего игрока
            game_state = self.games[game_id].get_state()
            
            return {
                'success': True,
                'player_id': sid,
                'game_state': game_state
            }
        else:
            return {'success': False, 'message': 'Game is full'}
    
    async def handle_get_game_state(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Получение текущего состояния игры"""
        game_id = data.get('game_id')
        
        if game_id in self.games:
            # Получаем состояние игры (только с изменениями карты)
            game_state = self.games[game_id].get_state()
            
            # Дополнительно получаем полную карту
            full_map = self.games[game_id].map.get_map()
            
            return {
                'success': True, 
                'game_state': game_state,
                'full_map': full_map  # Всегда отправляем полную карту в отдельном поле
            }
        
        return {'success': False, 'message': 'Game not found'}
    
    async def handle_input(self, sid: str, data: Dict[str, Any]) -> None:
        """Обработка ввода игрока"""
        game_id = data.get('game_id')
        inputs = data.get('inputs')
        
        if game_id in self.games:
            game = self.games[game_id]
            player = game.get_player(sid)
            
            if player:
                player.set_inputs(inputs)
    
    async def handle_place_bomb(self, sid: str, data: Dict[str, Any]) -> None:
        """Размещение бомбы"""
        game_id = data.get('game_id')
        
        if game_id in self.games:
            game = self.games[game_id]
            player = game.get_player(sid)
            
            if player:
                success = game.place_bomb(player)
                if success:
                    # Обновляем состояние игры для всех игроков
                    game_state = game.get_state()
                    await self.sio.emit('game_update', game_state, room=game_id)
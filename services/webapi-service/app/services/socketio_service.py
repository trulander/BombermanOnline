import asyncio
import uuid
from typing import Dict, Any, List, Set

import socketio
from redis.asyncio import Redis
from socketio import AsyncRedisManager

from ..config import settings
from .nats_service import NatsService

class SocketIOService:
    def __init__(self, nats_service: NatsService) -> None:
        """Initialize Socket.IO server"""
        # Используем Redis для управления комнатами и состоянием Socket.IO
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        if settings.REDIS_PASSWORD:
            redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            client_manager=AsyncRedisManager(redis_url),
            cors_allowed_origins='*'
        )
        
        # Маппинг sid -> player_id и player_id -> sid
        self.sid_to_player: Dict[str, str] = {}
        self.player_to_sid: Dict[str, str] = {}
        
        # Маппинг sid -> game_id и game_id -> set(sid)
        self.sid_to_game: Dict[str, str] = {}
        self.game_to_sids: Dict[str, Set[str]] = {}
        
        # Нам нужен nats_service для коммуникации с game-service
        self.nats_service = nats_service
        
        # Регистрируем обработчики событий
        self.register_handlers()

    def register_handlers(self) -> None:
        """Register Socket.IO event handlers"""
        @self.sio.event
        async def connect(sid: str, environ: Dict[str, Any]) -> None:
            """Handle client connection"""
            print(f"Client connected: {sid}")

        @self.sio.event
        async def disconnect(sid: str) -> None:
            """Handle client disconnection"""
            print(f"Client disconnected: {sid}")

            # Если игрок был в игре, удаляем его из игры
            await self.handle_disconnect(sid)

            # Удаляем обработчики событий
            self.nats_service.unregister_socket_handler(sid)

            # Удаляем привязки
            if sid in self.sid_to_player:
                player_id = self.sid_to_player[sid]
                del self.sid_to_player[sid]

                if player_id in self.player_to_sid:
                    del self.player_to_sid[player_id]

            if sid in self.sid_to_game:
                game_id = self.sid_to_game[sid]
                del self.sid_to_game[sid]

                if game_id in self.game_to_sids and sid in self.game_to_sids[game_id]:
                    self.game_to_sids[game_id].remove(sid)

                    # Если в игре не осталось игроков, удаляем игру
                    if not self.game_to_sids[game_id]:
                        del self.game_to_sids[game_id]

        @self.sio.event
        async def create_game(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """Create a new game"""
            try:
                response = await self.nats_service.create_game()
                return response
            except Exception as e:
                print(f"Error creating game: {e}")
                return {"success": False, "message": str(e)}

        @self.sio.event
        async def join_game(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """Join an existing game"""
            try:
                game_id = data.get('game_id')
                if not game_id:
                    return {"success": False, "message": "Missing game_id"}

                # Генерируем уникальный ID для игрока
                player_id = str(uuid.uuid4())

                # Присоединяемся к игре через NATS
                response = await self.nats_service.join_game(game_id, player_id)

                if response.get('success'):
                    # Сохраняем привязки
                    self.sid_to_player[sid] = player_id
                    self.player_to_sid[player_id] = sid
                    self.sid_to_game[sid] = game_id

                    if game_id not in self.game_to_sids:
                        self.game_to_sids[game_id] = set()

                    self.game_to_sids[game_id].add(sid)

                    # Присоединяемся к комнате для этой игры
                    await self.sio.enter_room(sid, f"game_{game_id}")

                    # Регистрируем обработчики событий обновления игры
                    self.nats_service.register_socket_handler(sid, 'game_update', self.handle_game_update)
                    self.nats_service.register_socket_handler(sid, 'game_over', self.handle_game_over)
                    self.nats_service.register_socket_handler(sid, 'player_disconnected', self.handle_player_disconnected)

                return response
            except Exception as e:
                print(f"Error joining game: {e}")
                return {"success": False, "message": str(e)}

        @self.sio.event
        async def input(sid: str, data: Dict[str, Any]) -> None:
            """Handle player input"""
            try:
                game_id = data.get('game_id')
                inputs = data.get('inputs')

                if not game_id or not inputs or sid not in self.sid_to_player:
                    return

                player_id = self.sid_to_player[sid]

                # Отправляем ввод игрока в game-service через NATS
                await self.nats_service.send_input(game_id, player_id, inputs)
            except Exception as e:
                print(f"Error handling input: {e}")

        @self.sio.event
        async def place_bomb(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle bomb placement"""
            try:
                game_id = data.get('game_id')

                if not game_id or sid not in self.sid_to_player:
                    return {"success": False, "message": "Invalid request"}

                player_id = self.sid_to_player[sid]

                # Отправляем запрос на установку бомбы в game-service через NATS
                response = await self.nats_service.place_bomb(game_id, player_id)
                return response
            except Exception as e:
                print(f"Error placing bomb: {e}")
                return {"success": False, "message": str(e)}

        @self.sio.event
        async def get_game_state(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """Get current game state"""
            try:
                game_id = data.get('game_id')

                if not game_id:
                    return {"success": False, "message": "Missing game_id"}

                # Получаем состояние игры из game-service через NATS
                response = await self.nats_service.get_game_state(game_id)
                return response
            except Exception as e:
                print(f"Error getting game state: {e}")
                return {"success": False, "message": str(e)}
    
    async def handle_disconnect(self, sid: str) -> None:
        """Handle socket disconnection and clean up game state"""
        if sid in self.sid_to_player and sid in self.sid_to_game:
            player_id = self.sid_to_player[sid]
            game_id = self.sid_to_game[sid]
            
            # Уведомляем game-service об отключении игрока
            await self.nats_service.disconnect_player(game_id, player_id)
    
    async def handle_game_update(self, sid: str, game_id: str, game_state: Dict[str, Any]) -> None:
        """Handle game state update from game service"""
        try:
            await self.sio.emit('game_update', game_state, room=sid)
        except Exception as e:
            print(f"Error in handle_game_update: {e}")
    
    async def handle_game_over(self, sid: str, game_id: str) -> None:
        """Handle game over notification from game service"""
        try:
            await self.sio.emit('game_over', {}, room=sid)
        except Exception as e:
            print(f"Error in handle_game_over: {e}")
    
    async def handle_player_disconnected(self, sid: str, game_id: str, data: Dict[str, Any]) -> None:
        """Handle player disconnection notification from game service"""
        try:
            await self.sio.emit('player_disconnected', data, room=sid)
        except Exception as e:
            print(f"Error in handle_player_disconnected: {e}")
    
    # Получаем Socket.IO приложение для подключения к FastAPI
    def get_app(self) -> Any:
        """Get Socket.IO application for ASGI integration"""
        return socketio.ASGIApp(self.sio)
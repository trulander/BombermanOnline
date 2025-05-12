import asyncio
import uuid
import logging
from typing import Dict, Any, List, Set
import socketio
from redis.asyncio import Redis

from .game_service import GameService
from socketio import AsyncRedisManager
from ..config import settings

# Импортировать наш новый класс
from .metrics_socket_server import MetricsSocketServer

logger = logging.getLogger(__name__)

class SocketIOService:
    def __init__(
            self,
            game_service: GameService
    ) -> None:
        """Initialize Socket.IO server"""
        # Используем Redis для управления комнатами и состоянием Socket.IO
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        if settings.REDIS_PASSWORD:
            redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        
        # Используем наш класс с метриками вместо стандартного AsyncServer
        self.sio = MetricsSocketServer(
            async_mode='asgi',
            client_manager=AsyncRedisManager(redis_url),
            cors_allowed_origins='*'
        )

        self.game_service = game_service

        # Регистрируем обработчики событий
        self.register_handlers()

    def register_handlers(self) -> None:
        """Register Socket.IO event handlers"""
        self.sio.on("connect", self.io_handle_connect)
        self.sio.on("disconnect", self.io_handle_disconnect)
        self.sio.on("create_game", self.io_handle_create_game)
        self.sio.on("join_game", self.io_handle_join_game)
        self.sio.on("input", self.io_handle_input)
        self.sio.on("place_bomb", self.io_handle_place_bomb)
        self.sio.on("get_game_state", self.io_handle_get_game_state)

    async def io_handle_connect(self, sid: str, environ: Dict[str, Any]) -> None:
        """Handle client connection"""
        logger.info(f"Client connected: {sid}")

    async def io_handle_disconnect(self, sid_user_id: str) -> None:
        """Handle client disconnection"""
        # Только логирование и уведомление game-service
        logger.info(f"Handling application-level disconnect for: {sid_user_id}")
        
        # Уведомляем game-service об отключении игрока
        await self.game_service.disconnect_player(sid_user_id=sid_user_id)

    async def io_handle_create_game(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new game"""
        try:
            response = await self.game_service.create_game()
            if response.get('success'):
                # Инкрементируем счетчик игр
                self.sio.increment_games()
            return response
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            return {"success": False, "message": str(e)}

    async def io_handle_join_game(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Join an existing game"""
        try:
            game_id = data.get('game_id')
            if not game_id:
                return {"success": False, "message": "Missing game_id"}

            response = await self.game_service.join_game(sid_user_id=sid, game_id=game_id)

            if response.get('success'):
                # Присоединяемся к комнате для этой игры
                await self.sio.enter_room(sid, f"game_{game_id}")

                # Регистрируем обработчики событий обновления игры
                await self.game_service.register_socket_handler(f"game_{game_id}", 'game_update', self.handle_game_update)
                await self.game_service.register_socket_handler(f"game_{game_id}", 'game_over', self.handle_game_over)
                await self.game_service.register_socket_handler(f"game_{game_id}", 'player_disconnected', self.handle_player_disconnected)

            return response
        except Exception as e:
            logger.error(f"Error joining game: {e}")
            return {"success": False, "message": str(e)}

    async def io_handle_input(self, sid_user_id: str, data: Dict[str, Any]) -> None:
        """Handle player input"""
        try:
            game_id = data.get('game_id')
            inputs = data.get('inputs')

            # Отправляем ввод игрока в game-service через NATS
            await self.game_service.send_input(game_id=game_id, sid_user_id=sid_user_id, inputs=inputs)
        except Exception as e:
            logger.error(f"Error handling input: {e}")

    async def io_handle_place_bomb(self, sid_user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bomb placement"""
        try:
            game_id = data.get('game_id')
            
            # Отправляем запрос на установку бомбы в game-service через NATS
            response = await self.game_service.place_bomb(game_id=game_id, sid_user_id=sid_user_id)
            return response
        except Exception as e:
            logger.error(f"Error placing bomb: {e}")
            return {"success": False, "message": str(e)}

    async def io_handle_get_game_state(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get current game state"""
        try:
            game_id = data.get('game_id')
            if not game_id:
                return {"success": False, "message": "Missing game_id"}

            # Получаем состояние игры из game-service через NATS
            response = await self.game_service.get_game_state(game_id=game_id)
            return response
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return {"success": False, "message": str(e)}

    async def handle_game_update(self, room_sid: str, game_id: str, game_state: Dict[str, Any]) -> None:
        """Handle game state update from game service"""
        try:
            await self.sio.emit('game_update', game_state, room=room_sid)
        except Exception as e:
            logger.error(f"Error in handle_game_update: {e}")
    
    async def handle_game_over(self, room_sid: str, game_id: str) -> None:
        """Handle game over notification from game service"""
        try:
            await self.sio.emit('game_over', {}, room=room_sid)
            self.sio.decrement_games()
        except Exception as e:
            logger.error(f"Error in handle_game_over: {e}")
    
    async def handle_player_disconnected(self, room_sid: str, game_id: str, data: Dict[str, Any]) -> None:
        """Handle player disconnection notification from game service"""
        try:
            await self.sio.emit('player_disconnected', data, room=room_sid)
        except Exception as e:
            logger.error(f"Error in handle_player_disconnected: {e}")

    # Получаем Socket.IO приложение для подключения к FastAPI
    def get_app(self) -> Any:
        """Get Socket.IO application for ASGI integration"""
        return socketio.ASGIApp(self.sio)
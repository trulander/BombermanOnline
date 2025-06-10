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

        
        # Используем наш класс с метриками вместо стандартного AsyncServer
        self.sio = MetricsSocketServer(
            async_mode='asgi',
            client_manager=AsyncRedisManager(settings.REDIS_URI),
            cors_allowed_origins=settings.CORS_ORIGINS,
            cors_credentials=settings.CORS_CREDENTIALS
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
        self.sio.on("apply_weapon", self.io_handle_apply_weapon)
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
            logger.error(f"Error creating game: {e}", exc_info=True)
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
                await self.game_service.register_socket_handler(sid=game_id, event='game_update', handler=self.handle_game_update)
                await self.game_service.register_socket_handler(sid=game_id, event='game_over', handler=self.handle_game_over)
                await self.game_service.register_socket_handler(sid=game_id, event='player_disconnected', handler=self.handle_player_disconnected)

            return response
        except Exception as e:
            logger.error(f"Error joining game: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    async def io_handle_input(self, sid_user_id: str, data: Dict[str, Any]) -> None:
        """Handle player input"""
        try:
            game_id = data.get('game_id')
            inputs = data.get('inputs')

            # Отправляем ввод игрока в game-service через NATS
            await self.game_service.send_input(game_id=game_id, sid_user_id=sid_user_id, inputs=inputs)
        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)


    async def io_handle_apply_weapon(self, sid_user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weapon application"""
        try:
            game_id = data.get('game_id')
            weapon_type = data.get('weapon_type', 'bomb')  # По умолчанию бомба для совместимости
            
            # Отправляем запрос на применение оружия в game-service через NATS
            response = await self.game_service.apply_weapon(game_id=game_id, sid_user_id=sid_user_id, weapon_type=weapon_type)
            return response
        except Exception as e:
            logger.error(f"Error applying weapon: {e}", exc_info=True)
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
            logger.error(f"Error getting game state: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    async def handle_game_update(self, game_id: str, game_state: Dict[str, Any]) -> None:
        """Handle game state update from game service"""
        try:
            await self.sio.emit(event='game_update', data=game_state, room=f"game_{game_id}")
        except Exception as e:
            logger.error(f"Error in handle_game_update: {e}", exc_info=True)
    
    async def handle_game_over(self, game_id: str) -> None:
        """Handle game over notification from game service"""
        try:
            logger.info(f"Handling game_over event for {game_id}")
            await self.sio.emit('game_over', {}, room=f"game_{game_id}")
            self.sio.decrement_games()
        except Exception as e:
            logger.error(f"Error in handle_game_over: {e}", exc_info=True)
    
    async def handle_player_disconnected(self, game_id, player_id) -> None:
        """Handle player disconnection notification from game service"""
        try:
            await self.sio.leave_room(sid=player_id, room=f"game_{game_id}")
            await self.sio.emit(event='player_disconnected', data={}, room=f"game_{game_id}")
        except Exception as e:
            logger.error(f"Error in handle_player_disconnected: {e}", exc_info=True)

    # Получаем Socket.IO приложение для подключения к FastAPI
    def get_app(self) -> Any:
        """Get Socket.IO application for ASGI integration"""
        return socketio.ASGIApp(socketio_server=self.sio)
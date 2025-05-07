import json
import uuid
from typing import Dict, Any, Callable, Awaitable

import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from ..config import settings

class NatsService:
    def __init__(self) -> None:
        self.nc: NATS | None = None
        self.socket_event_handlers: Dict[str, Dict[str, Callable]] = {}
        
    async def connect(self) -> None:
        """Подключение к NATS серверу"""
        self.nc = await nats.connect(settings.NATS_URL)
        print(f"Подключен к NATS: {settings.NATS_URL}")
        
        # Подписываемся на обновления игры
        await self.nc.subscribe("game.update.*", cb=self.handle_game_update)
        await self.nc.subscribe("game.over.*", cb=self.handle_game_over)
        await self.nc.subscribe("game.player_disconnected.*", cb=self.handle_player_disconnected)
        
    async def disconnect(self) -> None:
        """Отключение от NATS сервера"""
        if self.nc:
            await self.nc.drain()
            self.nc = None
            
    def register_socket_handler(
            self, 
            sid: str, 
            event: str, 
            handler: Callable
    ) -> None:
        """Регистрация обработчика сокет-событий"""
        if sid not in self.socket_event_handlers:
            self.socket_event_handlers[sid] = {}
        
        self.socket_event_handlers[sid][event] = handler
    
    def unregister_socket_handler(self, sid: str) -> None:
        """Удаление обработчиков сокет-событий"""
        if sid in self.socket_event_handlers:
            del self.socket_event_handlers[sid]
            
    async def handle_game_update(self, msg: Msg) -> None:
        """Обработчик обновления игры"""
        try:
            game_id = msg.subject.split('.')[-1]
            game_state = json.loads(msg.data.decode())
            
            # Отправляем обновление всем подключенным клиентам через сокеты
            for sid, handlers in self.socket_event_handlers.items():
                if 'game_update' in handlers:
                    await handlers['game_update'](sid, game_id, game_state)
        except Exception as e:
            print(f"Error handling game update: {e}")
    
    async def handle_game_over(self, msg: Msg) -> None:
        """Обработчик завершения игры"""
        try:
            game_id = msg.subject.split('.')[-1]
            
            # Отправляем уведомление всем подключенным клиентам через сокеты
            for sid, handlers in self.socket_event_handlers.items():
                if 'game_over' in handlers:
                    await handlers['game_over'](sid, game_id)
        except Exception as e:
            print(f"Error handling game over: {e}")
    
    async def handle_player_disconnected(self, msg: Msg) -> None:
        """Обработчик отключения игрока"""
        try:
            game_id = msg.subject.split('.')[-1]
            data = json.loads(msg.data.decode())
            player_id = data.get('player_id')
            
            # Отправляем уведомление всем подключенным клиентам через сокеты
            for sid, handlers in self.socket_event_handlers.items():
                if 'player_disconnected' in handlers:
                    await handlers['player_disconnected'](sid, game_id, {'player_id': player_id})
        except Exception as e:
            print(f"Error handling player disconnect: {e}")
    
    async def create_game(self) -> Dict[str, Any]:
        """Отправка запроса на создание игры"""
        if not self.nc:
            raise Exception("NATS client is not connected")
        
        game_id = str(uuid.uuid4())
        
        try:
            response = await self.nc.request(
                "game.create",
                json.dumps({"game_id": game_id}).encode(),
                timeout=5.0
            )
            return json.loads(response.data.decode())
        except Exception as e:
            print(f"Error creating game: {e}")
            return {"success": False, "message": str(e)}
    
    async def join_game(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Отправка запроса на присоединение к игре"""
        if not self.nc:
            raise Exception("NATS client is not connected")
        
        try:
            response = await self.nc.request(
                "game.join",
                json.dumps({"game_id": game_id, "player_id": player_id}).encode(),
                timeout=5.0
            )
            return json.loads(response.data.decode())
        except Exception as e:
            print(f"Error joining game: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_input(self, game_id: str, player_id: str, inputs: Dict[str, bool]) -> None:
        """Отправка ввода игрока"""
        if not self.nc:
            raise Exception("NATS client is not connected")
        
        try:
            await self.nc.publish(
                "game.input",
                json.dumps({
                    "game_id": game_id,
                    "player_id": player_id,
                    "inputs": inputs
                }).encode()
            )
        except Exception as e:
            print(f"Error sending input: {e}")
    
    async def place_bomb(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Отправка запроса на установку бомбы"""
        if not self.nc:
            raise Exception("NATS client is not connected")
        
        try:
            response = await self.nc.request(
                "game.place_bomb",
                json.dumps({"game_id": game_id, "player_id": player_id}).encode(),
                timeout=5.0
            )
            return json.loads(response.data.decode())
        except Exception as e:
            print(f"Error placing bomb: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Получение состояния игры"""
        if not self.nc:
            raise Exception("NATS client is not connected")
        
        try:
            response = await self.nc.request(
                "game.get_state",
                json.dumps({"game_id": game_id}).encode(),
                timeout=5.0
            )
            return json.loads(response.data.decode())
        except Exception as e:
            print(f"Error getting game state: {e}")
            return {"success": False, "message": str(e)}
    
    async def disconnect_player(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Отправка запроса на отключение игрока"""
        if not self.nc:
            raise Exception("NATS client is not connected")
        
        try:
            response = await self.nc.request(
                "game.disconnect",
                json.dumps({"game_id": game_id, "player_id": player_id}).encode(),
                timeout=5.0
            )
            return json.loads(response.data.decode())
        except Exception as e:
            print(f"Error disconnecting player: {e}")
            return {"success": False, "message": str(e)} 
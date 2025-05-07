import asyncio
import json
from typing import Dict, Any, Callable, Awaitable
import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from ..config import settings
from ..services.game_service import GameService

class NatsService:
    def __init__(self) -> None:
        self.nc: NATS | None = None
        self.games: Dict[str, GameService] = {}
        
    async def connect(self) -> None:
        """Подключение к NATS серверу"""
        self.nc = await nats.connect(settings.NATS_URL)
        
        # Подписка на события
        await self.nc.subscribe("game.create", cb=self.handle_create_game)
        await self.nc.subscribe("game.join", cb=self.handle_join_game)
        await self.nc.subscribe("game.input", cb=self.handle_input)
        await self.nc.subscribe("game.place_bomb", cb=self.handle_place_bomb)
        await self.nc.subscribe("game.get_state", cb=self.handle_get_game_state)
        await self.nc.subscribe("game.disconnect", cb=self.handle_disconnect)
        
        print(f"Подключен к NATS: {settings.NATS_URL}")
    
    async def disconnect(self) -> None:
        """Отключение от NATS сервера"""
        if self.nc:
            await self.nc.drain()
            self.nc = None
            
    async def start_game_loop(self) -> None:
        """Запуск игрового цикла"""
        while True:
            for game_id, game in list(self.games.items()):
                if game.is_active():
                    updated_state = game.update()
                    # Отправляем обновление через NATS всем подключенным клиентам
                    if self.nc:
                        await self.nc.publish(f"game.update.{game_id}", json.dumps(updated_state).encode())
                else:
                    # Игра окончена, отправляем уведомление всем игрокам
                    if self.nc:
                        await self.nc.publish(f"game.over.{game_id}", b"")
                    del self.games[game_id]
            
            await asyncio.sleep(settings.GAME_UPDATE_RATE)
    
    async def handle_create_game(self, msg: Msg) -> None:
        """Обработчик создания новой игры"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            
            if game_id:
                self.games[game_id] = GameService()
                response = {"success": True, "game_id": game_id}
            else:
                response = {"success": False, "message": "Missing game_id"}
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            print(f"Error creating game: {e}")
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": str(e)}).encode())
    
    async def handle_join_game(self, msg: Msg) -> None:
        """Обработчик присоединения к игре"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            
            if not game_id or not player_id:
                response = {"success": False, "message": "Missing game_id or player_id"}
            elif game_id not in self.games:
                response = {"success": False, "message": "Game not found"}
            else:
                from ..entities.player import Player
                player = Player(player_id)
                success = self.games[game_id].add_player(player)
                
                if success:
                    # Получаем начальное состояние игры с данными для текущего игрока
                    game_state = self.games[game_id].get_state()
                    
                    response = {
                        "success": True,
                        "player_id": player_id,
                        "game_state": game_state
                    }
                else:
                    response = {"success": False, "message": "Game is full"}
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            print(f"Error joining game: {e}")
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": str(e)}).encode())
    
    async def handle_input(self, msg: Msg) -> None:
        """Обработчик ввода игрока"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            inputs = data.get("inputs")
            
            if game_id in self.games:
                game = self.games[game_id]
                player = game.get_player(player_id)
                
                if player:
                    player.set_inputs(inputs)
        except Exception as e:
            print(f"Error handling input: {e}")
    
    async def handle_place_bomb(self, msg: Msg) -> None:
        """Обработчик размещения бомбы"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            
            if game_id in self.games:
                game = self.games[game_id]
                player = game.get_player(player_id)
                
                if player:
                    success = game.place_bomb(player)
                    response = {"success": success}
                else:
                    response = {"success": False, "message": "Player not found"}
            else:
                response = {"success": False, "message": "Game not found"}
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            print(f"Error placing bomb: {e}")
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": str(e)}).encode())
    
    async def handle_get_game_state(self, msg: Msg) -> None:
        """Обработчик получения состояния игры"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            
            if game_id in self.games:
                # Получаем состояние игры
                game_state = self.games[game_id].get_state()
                
                # Дополнительно получаем полную карту
                full_map = self.games[game_id].map.get_map()
                
                response = {
                    "success": True, 
                    "game_state": game_state,
                    "full_map": full_map
                }
            else:
                response = {"success": False, "message": "Game not found"}
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            print(f"Error getting game state: {e}")
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": str(e)}).encode())
    
    async def handle_disconnect(self, msg: Msg) -> None:
        """Обработчик отключения игрока"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            
            if game_id and game_id in self.games and player_id:
                game = self.games[game_id]
                game.remove_player(player_id)
                
                if len(game.players) == 0:
                    del self.games[game_id]
                else:
                    # Уведомляем других игроков об отключении
                    await self.nc.publish(
                        f"game.player_disconnected.{game_id}", 
                        json.dumps({"player_id": player_id}).encode()
                    )
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": True}).encode())
        except Exception as e:
            print(f"Error handling disconnect: {e}")
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": str(e)}).encode()) 
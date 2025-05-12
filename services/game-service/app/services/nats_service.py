import asyncio
import json
import logging
from typing import Dict, Any, Callable, Awaitable
import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from ..config import settings
from ..services.game_service import GameService

logger = logging.getLogger(__name__)

class NatsService:
    def __init__(self) -> None:
        try:
            self.nc: NATS | None = None
            self.games: Dict[str, GameService] = {}
            logger.info("NatsService initialized")
        except Exception as e:
            logger.error(f"Error initializing NatsService: {e}", exc_info=True)
            raise
        
    async def connect(self) -> None:
        """Подключение к NATS серверу"""
        try:
            logger.info(f"Connecting to NATS server at {settings.NATS_URL}")
            self.nc = await nats.connect(settings.NATS_URL)
            
            # Подписка на события
            await self.nc.subscribe("game.create", cb=self.handle_create_game)
            await self.nc.subscribe("game.join", cb=self.handle_join_game)
            await self.nc.subscribe("game.input", cb=self.handle_input)
            await self.nc.subscribe("game.place_bomb", cb=self.handle_place_bomb)
            await self.nc.subscribe("game.get_state", cb=self.handle_get_game_state)
            await self.nc.subscribe("game.disconnect", cb=self.handle_disconnect)
            
            logger.info(f"Connected to NATS: {settings.NATS_URL}")
        except Exception as e:
            logger.error(f"Error connecting to NATS at {settings.NATS_URL}: {e}", exc_info=True)
            raise
    
    async def disconnect(self) -> None:
        """Отключение от NATS сервера"""
        try:
            if self.nc:
                logger.info("Disconnecting from NATS server")
                await self.nc.drain()
                self.nc = None
                logger.info("Disconnected from NATS server")
        except Exception as e:
            logger.error(f"Error disconnecting from NATS: {e}", exc_info=True)
            
    async def start_game_loop(self) -> None:
        """Запуск игрового цикла"""
        try:
            logger.info("Starting game loop")
            while True:
                active_games = 0
                for game_id, game in list(self.games.items()):
                    if game.is_active():
                        active_games += 1
                        updated_state = game.update()
                        # Отправляем обновление через NATS всем подключенным клиентам
                        if self.nc:
                            await self.nc.publish(f"game.update.{game_id}", json.dumps(updated_state).encode())
                    else:
                        # Игра окончена, отправляем уведомление всем игрокам
                        logger.info(f"Game {game_id} is over or has no players, sending game over notification")
                        if self.nc:
                            await self.nc.publish(f"game.over.{game_id}", b"")
                        del self.games[game_id]
                
                if active_games > 0:
                    logger.debug(f"Game loop update: {active_games} active games")
                
                await asyncio.sleep(settings.GAME_UPDATE_RATE)
        except Exception as e:
            logger.error(f"Error in game loop: {e}", exc_info=True)
    
    async def handle_create_game(self, msg: Msg) -> None:
        """Обработчик создания новой игры"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            
            if game_id:
                self.games[game_id] = GameService()
                response = {"success": True, "game_id": game_id}
                logger.info(f"Game created with ID: {game_id}")
            else:
                response = {"success": False, "message": "Missing game_id"}
                logger.warning("Failed to create game: Missing game_id")
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            error_msg = f"Error creating game: {e}"
            logger.error(error_msg, exc_info=True)
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": error_msg}).encode())
    
    async def handle_join_game(self, msg: Msg) -> None:
        """Обработчик присоединения к игре"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            
            if not game_id or not player_id:
                response = {"success": False, "message": "Missing game_id or player_id"}
                logger.warning(f"Failed to join game: Missing game_id or player_id. Data: {data}")
            elif game_id not in self.games:
                response = {"success": False, "message": "Game not found"}
                logger.warning(f"Failed to join game: Game {game_id} not found")
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
                    logger.info(f"Player {player_id} joined game {game_id}")
                else:
                    response = {"success": False, "message": "Game is full"}
                    logger.warning(f"Failed to join game: Game {game_id} is full")
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            error_msg = f"Error joining game: {e}"
            logger.error(error_msg, exc_info=True)
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": error_msg}).encode())
    
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
                    logger.debug(f"Input received for player {player_id} in game {game_id}: {inputs}")
                else:
                    logger.warning(f"Player {player_id} not found in game {game_id} for input")
            else:
                logger.warning(f"Game {game_id} not found for input")
        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)
    
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
                    if success:
                        logger.info(f"Bomb placed by player {player_id} in game {game_id}")
                    else:
                        logger.debug(f"Failed to place bomb for player {player_id} in game {game_id}")
                else:
                    response = {"success": False, "message": "Player not found"}
                    logger.warning(f"Player {player_id} not found in game {game_id} for place_bomb")
            else:
                response = {"success": False, "message": "Game not found"}
                logger.warning(f"Game {game_id} not found for place_bomb")
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            error_msg = f"Error placing bomb: {e}"
            logger.error(error_msg, exc_info=True)
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": error_msg}).encode())
    
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
                logger.debug(f"State requested for game {game_id}")
            else:
                response = {"success": False, "message": "Game not found"}
                logger.warning(f"Game {game_id} not found for get_game_state")
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
        except Exception as e:
            error_msg = f"Error getting game state: {e}"
            logger.error(error_msg, exc_info=True)
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": error_msg}).encode())
    
    async def handle_disconnect(self, msg: Msg) -> None:
        """Обработчик отключения игрока"""
        try:
            data = json.loads(msg.data.decode())
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            
            if game_id and game_id in self.games and player_id:
                game = self.games[game_id]
                game.remove_player(player_id)
                logger.info(f"Player {player_id} disconnected from game {game_id}")
                
                if len(game.players) == 0:
                    logger.info(f"No players left in game {game_id}, removing game")
                    del self.games[game_id]
                else:
                    # Уведомляем других игроков об отключении
                    if self.nc:
                        await self.nc.publish(
                            f"game.player_disconnected.{game_id}", 
                            json.dumps({"player_id": player_id}).encode()
                        )
                        logger.info(f"Sent player_disconnected notification for player {player_id} in game {game_id}")
            else:
                if not game_id:
                    logger.warning("Missing game_id in disconnect request")
                elif game_id not in self.games:
                    logger.warning(f"Game {game_id} not found for disconnect")
                elif not player_id:
                    logger.warning(f"Missing player_id in disconnect request for game {game_id}")
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": True}).encode())
        except Exception as e:
            error_msg = f"Error handling disconnect: {e}"
            logger.error(error_msg, exc_info=True)
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps({"success": False, "message": error_msg}).encode()) 
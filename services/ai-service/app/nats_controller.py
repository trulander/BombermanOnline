import logging
from typing import Any, Callable, Dict, Optional

from app.entities.game_state_representation import GameStateRepresentation, PlayerInput
from app.repositories.nats_repository import NatsRepository

logger = logging.getLogger(__name__)


class NATSController:
    def __init__(self, nats_repository: NatsRepository):
        self.nats_repository = nats_repository
        logger.info("NATSController initialized.")

    async def request_game_state(self, game_id: str) -> GameStateRepresentation | None:
        subject = f"game.get_state.{game_id}"
        logger.debug(f"Requesting full game state for game {game_id} on subject {subject}")
        response = await self.nats_repository.request(subject, {"game_id": game_id})
        if response and response.get("success") and response.get("game_state"):
            try:
                game_state = GameStateRepresentation(**response["game_state"])
                logger.debug(f"Successfully received and parsed full game state for {game_id}.")
                return game_state
            except Exception as e:
                logger.error(f"Error parsing game state for {game_id}: {e}", exc_info=True)
                return None
        logger.error(f"Failed to get full game state for {game_id}. Response: {response}")
        return None

    async def publish_ai_input(self, game_id: str, player_id: str, inputs: PlayerInput) -> None:
        subject = f"game.input.{game_id}"
        data = {
            "game_id": game_id,
            "player_id": player_id,
            "inputs": inputs.model_dump()  # Use .model_dump() for Pydantic v2
        }
        logger.debug(f"Publishing AI input for player {player_id} in game {game_id} on subject {subject}")
        await self.nats_repository.publish(subject, data)

    async def subscribe_game_updates(self, game_id: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        subject = f"game.update.{game_id}"
        logger.info(f"Subscribing to game updates for game {game_id} on subject {subject}")
        await self.nats_repository.subscribe(subject, callback)

    async def publish_ai_entity_spawn(self, game_id: str, entity_id: str, entity_type: str, is_player: bool, game_mode: str) -> None:
        subject = "ai.entity_spawn"
        data = {
            "game_id": game_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "is_player": is_player,
            "game_mode": game_mode
        }
        logger.debug(f"Publishing AI entity spawn for {entity_type} {entity_id} in game {game_id} on subject {subject}")
        await self.nats_repository.publish(subject, data)

    async def publish_ai_entity_despawn(self, game_id: str, entity_id: str) -> None:
        subject = "ai.entity_despawn"
        data = {
            "game_id": game_id,
            "entity_id": entity_id
        }
        logger.debug(f"Publishing AI entity despawn for {entity_id} in game {game_id} on subject {subject}")
        await self.nats_repository.publish(subject, data) 
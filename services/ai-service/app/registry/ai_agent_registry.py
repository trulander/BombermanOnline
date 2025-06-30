import asyncio
import logging
from typing import Dict, Any, Callable

import numpy as np

from app.agents.bomberman_ai_agent import BombermanAIAgent
from app.agents.enemy_ai_agent import EnemyAIAgent
from app.entities.game_state_representation import PlayerInput

from app.nats_controller import NATSController
from app.training.model_manager import ModelManager

logger = logging.getLogger(__name__)

class AIAgentRegistry:
    """Manages active AI agents and their game states."""
    def __init__(self, nats_controller: NATSController, model_manager: ModelManager):
        self.agents: Dict[str, BombermanAIAgent | EnemyAIAgent] = {}
        self.game_states: Dict[str, Any] = {}
        self.nats_controller = nats_controller
        self.model_manager = model_manager

    async def handle_entity_spawn(self, data: Dict[str, Any]) -> None:
        game_id = data["game_id"]
        entity_id = data["entity_id"]
        entity_type = data["entity_type"]
        is_player = data["is_player"]
        game_mode = data["game_mode"]

        logger.info(f"Handling entity spawn: game_id={game_id}, entity_id={entity_id}, type={entity_type}, is_player={is_player}, mode={game_mode}")

        # Load appropriate model based on entity type and game mode
        model_name = f"{game_mode}_{entity_type}"
        # For simplicity, always load the latest model
        model = self.model_manager.load_model(model_name)

        if is_player:
            agent = BombermanAIAgent(model=model)
        else:
            agent = EnemyAIAgent(model=model)

        self.agents[entity_id] = agent
        logger.info(f"AI agent {entity_id} ({entity_type}) registered for game {game_id}.")

        # Subscribe to game updates for this game if not already subscribed
        if game_id not in self.game_states:
            self.game_states[game_id] = {"manager": None, "listener_task": None}
            # Request full state first
            initial_state = await self.nats_controller.request_game_state(game_id)
            if initial_state:
                from app.environment.bomberman_env import GameStateManager # Deferred import
                state_manager = GameStateManager()
                state_manager.initialize_state(initial_state.model_dump())
                self.game_states[game_id]["manager"] = state_manager

                # Start listening for incremental updates
                listener_task = asyncio.create_task(
                    self.nats_controller.subscribe_game_updates(game_id, await self._game_update_handler(game_id))
                )
                self.game_states[game_id]["listener_task"] = listener_task
                logger.info(f"Subscribed to game updates for game {game_id}.")
            else:
                logger.error(f"Could not get initial game state for {game_id}. AI will not operate for this game.")

    async def _game_update_handler(self, game_id: str) -> Callable[[Dict[str, Any]], Any]:
        # This closure ensures the handler has access to the game_id and current agent registry.
        async def handler(data: Dict[str, Any]) -> None:
            if game_id in self.game_states and self.game_states[game_id]["manager"]:
                self.game_states[game_id]["manager"].apply_update(data)
                logger.debug(f"Game {game_id} state updated in registry.")

                # After update, iterate through all agents assigned to this game
                # and prompt them for action based on the latest state.
                # This is a simplified active polling; a more sophisticated approach
                # might have agents react to specific state changes.
                for entity_id, agent in self.agents.items():
                    if agent: # Ensure agent exists and is not None
                        current_state = self.game_states[game_id]["manager"].get_current_state()
                        if current_state and (entity_id in current_state.players or entity_id in current_state.enemies):
                            # Extract observation for the specific agent
                            # This requires a function to create an observation for a single entity
                            # For simplicity, let's assume we can get a slice or transform the full state
                            # For now, we will pass the full state and let the agent decide what to use.
                            # In a real scenario, BombermanEnv._get_observation() logic might be adapted.
                            # This is a placeholder for observation generation.

                            # Determine if it's a player or enemy for observation generation
                            is_player = entity_id in current_state.players
                            entity_state = current_state.players.get(entity_id) if is_player else current_state.enemies.get(entity_id)
                            if not entity_state: continue # Skip if entity no longer exists in state

                            # Dummy observation for now - replace with actual observation logic
                            # This would ideally come from a simplified BombermanEnv for inference
                            # For training, it uses the full env. For inference, we need a lightweight obs.
                            # For initial implementation, a zero array. This needs significant refinement.
                            # A better approach is to have an `EnvHelper` or similar.

                            # Placeholder for actual observation: need to adapt BombermanEnv._get_observation
                            # to generate observation for a specific agent given the full game state.
                            # For now, we will create a dummy observation. This is a critical TODO.
                            # observation_for_agent = self._create_observation_for_agent(current_state, entity_id)
                            # For now, let's just make a dummy observation. This is a major simplification.
                            dummy_obs_shape = (current_state.map.height, current_state.map.width, 5) if current_state.map else (10,10,5)
                            observation_for_agent = np.zeros(dummy_obs_shape, dtype=np.uint8)

                            action, _ = agent.predict(observation_for_agent)
                            # Convert action to PlayerInput and publish
                            action_map = {
                                0: {}, # NO_ACTION
                                1: {"up": True},
                                2: {"down": True},
                                3: {"left": True},
                                4: {"right": True},
                                5: {"weapon1": True},
                                6: {"weapon2": True},
                                7: {"action1": True}
                            }
                            input_dict = action_map.get(action, {})
                            player_input = PlayerInput(**input_dict)
                            await self.nats_controller.publish_ai_input(game_id, entity_id, player_input)
                            logger.debug(f"AI agent {entity_id} in game {game_id} executed action {action}")
            else:
                logger.warning(f"Game state manager not found for game {game_id} in registry.")
        return handler

    async def handle_entity_despawn(self, data: Dict[str, Any]) -> None:
        game_id = data["game_id"]
        entity_id = data["entity_id"]

        if entity_id in self.agents:
            del self.agents[entity_id]
            logger.info(f"AI agent {entity_id} removed from registry.")

        # If no more agents for this game, consider cleaning up game state listener
        if not any(agent.game_id == game_id for agent in self.agents.values()): # This needs game_id in agent
            # This needs revision. Agents don't have game_id directly.
            # A better way is to track agents per game_id
            agents_in_game = [aid for aid, agent in self.agents.items() if aid in self.game_states[game_id]["manager"].get_current_state().players or aid in self.game_states[game_id]["manager"].get_current_state().enemies]
            if not agents_in_game and game_id in self.game_states:
                if self.game_states[game_id]["listener_task"]:
                    self.game_states[game_id]["listener_task"].cancel()
                    logger.info(f"Cancelled game update listener for game {game_id}.")
                del self.game_states[game_id]
                logger.info(f"Cleaned up game state for game {game_id}.")

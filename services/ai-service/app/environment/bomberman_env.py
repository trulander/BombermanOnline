import asyncio
from concurrent.futures import ThreadPoolExecutor

import gymnasium as gym
import logging
import numpy as np
from gymnasium import spaces
from typing import Any, Dict, List, Optional, Tuple

from app.entities.game_state_representation import (GamePlayerInfo, GameStateRepresentation, MapCellUpdate,
                                                     MapState, GameUpdateEvent, EnemyState, WeaponState, PowerUpState, PlayerInput)
from app.repositories.nats_repository import NatsRepository

logger = logging.getLogger(__name__)

class GameStateManager:
    def __init__(self):
        self._full_state: GameStateRepresentation | None = None

    def initialize_state(self, full_game_state: Dict[str, Any]) -> None:
        try:
            # Ensure MapState is initialized if it's part of full_game_state and not already a Pydantic model
            if 'map' in full_game_state and isinstance(full_game_state['map'], dict):
                full_game_state['map'] = MapState(**full_game_state['map'])

            self._full_state = GameStateRepresentation(**full_game_state)
            logger.debug(f"GameStateManager initialized with game ID: {self._full_state.game_id}")
        except Exception as e:
            logger.error(f"Error initializing game state: {e}", exc_info=True)
            self._full_state = None

    def apply_update(self, game_update_data: Dict[str, Any]) -> None:
        if not self._full_state:
            logger.warning("Cannot apply update: full game state not initialized.")
            return
        try:
            game_update = GameUpdateEvent(**game_update_data)

            # Update basic game status
            self._full_state.status = game_update.status
            self._full_state.is_active = game_update.is_active

            # Apply map updates
            if game_update.map_update and self._full_state.map:
                for cell_update in game_update.map_update:
                    try:
                        # Check if map.grid exists and is a list of lists before accessing
                        if self._full_state.map.grid and cell_update.y < len(self._full_state.map.grid) and cell_update.x < len(self._full_state.map.grid[cell_update.y]):
                            self._full_state.map.grid[cell_update.y][cell_update.x] = cell_update.type
                        else:
                            logger.warning(f"Map update out of bounds or invalid map grid for cell ({cell_update.x}, {cell_update.y})")
                    except IndexError:
                        logger.warning(f"Map update index error for cell ({cell_update.x}, {cell_update.y})")
                    except Exception as e:
                        logger.error(f"Error applying single map cell update: {e}", exc_info=True)

            # Apply players update
            if game_update.players_update:
                for player_id, player_data in game_update.players_update.items():
                    if player_id in self._full_state.players:
                        # Update existing player. Use .model_copy(update=...) for Pydantic v2
                        # Or manually update fields for Pydantic v1. Assuming v2 for now.
                        self._full_state.players[player_id] = self._full_state.players[player_id].model_copy(update=player_data.model_dump())
                    else:
                        # Add new player
                        self._full_state.players[player_id] = GamePlayerInfo(**player_data.model_dump())

            # Apply enemies update (similar logic for removal and update/add)
            if game_update.enemies_update:
                current_enemies_ids = set(self._full_state.enemies.keys())
                updated_enemies_ids = set(game_update.enemies_update.keys())

                for enemy_id in current_enemies_ids - updated_enemies_ids:
                    del self._full_state.enemies[enemy_id]

                for enemy_id, enemy_data in game_update.enemies_update.items():
                    if enemy_id in self._full_state.enemies:
                        self._full_state.enemies[enemy_id] = self._full_state.enemies[enemy_id].model_copy(update=enemy_data.model_dump())
                    else:
                        self._full_state.enemies[enemy_id] = EnemyState(**enemy_data.model_dump())

            # Apply weapons update
            if game_update.weapons_update:
                current_weapons_ids = set(self._full_state.weapons.keys())
                updated_weapons_ids = set(game_update.weapons_update.keys())

                for weapon_id in current_weapons_ids - updated_weapons_ids:
                    del self._full_state.weapons[weapon_id]

                for weapon_id, weapon_data in game_update.weapons_update.items():
                    if weapon_id in self._full_state.weapons:
                        self._full_state.weapons[weapon_id] = self._full_state.weapons[weapon_id].model_copy(update=weapon_data.model_dump())
                    else:
                        self._full_state.weapons[weapon_id] = WeaponState(**weapon_data.model_dump())

            # Apply power-ups update
            if game_update.power_ups_update:
                current_power_ups_ids = set(self._full_state.power_ups.keys())
                updated_power_ups_ids = set(game_update.power_ups_update.keys())

                for power_up_id in current_power_ups_ids - updated_power_ups_ids:
                    del self._full_state.power_ups[power_up_id]

                for power_up_id, power_up_data in game_update.power_ups_update.items():
                    if power_up_id in self._full_state.power_ups:
                        self._full_state.power_ups[power_up_id] = self._full_state.power_ups[power_up_id].model_copy(update=power_up_data.model_dump())
                    else:
                        self._full_state.power_ups[power_up_id] = PowerUpState(**power_up_data.model_dump())

            logger.debug(f"Applied update to game ID: {game_update.game_id}, status: {self._full_state.status}")
        except Exception as e:
            logger.error(f"Error applying game state update: {e}", exc_info=True)

    def get_current_state(self) -> GameStateRepresentation | None:
        return self._full_state


class BombermanEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(
            self,
            game_id: str,
            player_id: str,
            nats_repository: NatsRepository,
            async_loop: any,
            render_mode: Optional[str] = None
    ):
        super().__init__()
        self.game_id: str = game_id
        self.player_id: str = player_id
        self.nats_repository: NatsRepository = nats_repository
        self.game_state_manager: GameStateManager = GameStateManager()
        self.render_mode = render_mode
        self.current_player_lives: int = 0
        self._async_loop = async_loop

        # Define action and observation space
        # Actions: 0: NO_ACTION, 1: UP, 2: DOWN, 3: LEFT, 4: RIGHT, 5: WEAPON1 (bomb), 6: WEAPON2, 7: ACTION1
        self.action_space = spaces.Discrete(8)

        # Observation space: This will depend heavily on what information we extract from the game state
        # For simplicity, let's assume a flattened map representation + player/enemy positions + player stats
        # We need the full map dimensions to define this properly
        # Initial dummy observation space - will be updated after first state is received
        self.observation_space = spaces.Box(low=0, high=255, shape=(10, 10, 5), dtype=np.uint8) # Default to 5 channels for map, player, enemy, bomb, powerup
        logger.info(f"BombermanEnv initialized for game {game_id}, player {player_id}")

    async def _request_full_game_state(self) -> Dict[str, Any] | None:
        subject = f"game.get_state.{self.game_id}"
        logger.info(f"Requesting full game state from {subject}")
        try:
            response = await self.nats_repository.request(subject, {"game_id": self.game_id})
            if response and response.get("success") and response.get("game_state"):
                return response["game_state"]
            logger.error(f"Failed to get full game state for {self.game_id}: {response}")
            return None
        except Exception as e:
            logger.error(f"Error during NATS request for full game state: {e}", exc_info=True)
            return None

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        future = asyncio.run_coroutine_threadsafe(self._reset(seed=seed, options=options), self._async_loop)
        return future.result()

    async def _reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        # Request full game state
        full_state_data = await self._request_full_game_state()
        if not full_state_data:
            raise RuntimeError("Failed to retrieve initial game state for reset.")

        self.game_state_manager.initialize_state(full_state_data)

        # Update observation space based on actual map size and features
        current_map = self.game_state_manager.get_current_state().map
        if current_map:
            map_width = current_map.width
            map_height = current_map.height
            # Update observation space shape based on map dimensions and number of features (e.g., 5 channels)
            self.observation_space = spaces.Box(
                low=0, high=255, shape=(map_height, map_width, 5), dtype=np.uint8
            )
            logger.info(f"Observation space updated to {self.observation_space.shape} based on map size.")
        else:
            logger.warning("Map information not available after reset, using default observation space.")

        # Subscribe to game updates
        await self.nats_repository.subscribe(f"game.update.{self.game_id}", self._handle_game_update)
        logger.info(f"Subscribed to game.update.{self.game_id}")

        # Initialize current player lives for reward calculation
        player = self.game_state_manager.get_current_state().players.get(self.player_id)
        self.current_player_lives = player.lives if player else 0

        observation = self._get_observation()
        info = self._get_info()
        logger.info(f"Environment reset for game {self.game_id}")
        return observation, info

    async def _handle_game_update(self, data: Dict[str, Any]) -> None:
        # This callback is called when a NATS message arrives. It updates the internal state.
        self.game_state_manager.apply_update(data)
        logger.debug(f"Game state updated from NATS for {self.game_id}")

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        future = asyncio.run_coroutine_threadsafe(self._step(action=action), self._async_loop)
        return future.result()

    async def _step(self, action: int):
        # Map action to player input
        player_input = PlayerInput()
        if action == 1:
            player_input.up = True
        elif action == 2:
            player_input.down = True
        elif action == 3:
            player_input.left = True
        elif action == 4:
            player_input.right = True
        elif action == 5:
            player_input.weapon1 = True
        elif action == 6:
            player_input.weapon2 = True
        elif action == 7:
            player_input.action1 = True

        # Publish player input to game-service
        await self.nats_repository.publish(
            f"game.input.{self.game_id}",
            {
                "game_id": self.game_id,
                "player_id": self.player_id,
                "inputs": player_input.model_dump()
            }
        )

        # Give some time for the game service to process input and send update
        await asyncio.sleep(0.05)  # Small delay to allow for NATS round trip and state update

        current_state = self.game_state_manager.get_current_state()
        if not current_state:
            logger.error("Game state is None after step - potential issue with state updates.")
            return self._get_observation(), 0.0, True, False, self._get_info()  # Terminate episode on severe error

        # Reward calculation (simplified example)
        reward: float = 0.0
        terminated: bool = False
        truncated: bool = False

        player = current_state.players.get(self.player_id)
        if player:
            # Calculate reward based on change in lives
            if player.lives < self.current_player_lives:
                reward -= 10.0  # Penalty for losing a life
                logger.debug(f"Player {self.player_id} lost a life. Reward: {reward}")
            elif player.lives > self.current_player_lives:
                reward += 5.0  # Reward for gaining a life (e.g., from power-up)
                logger.debug(f"Player {self.player_id} gained a life. Reward: {reward}")
            self.current_player_lives = player.lives  # Update for next step

            if not player.is_alive:
                reward -= 100.0  # Large penalty for dying
                terminated = True
                logger.info(f"Player {self.player_id} died. Episode terminated. Final reward: {reward}")

        # Check game status for termination
        if current_state.status == "FINISHED":
            terminated = True
            # You might add a positive reward for winning, or a penalty for losing the game based on other criteria.
            logger.info(f"Game {self.game_id} finished. Episode terminated. Current reward: {reward}")

        observation = self._get_observation()
        info = self._get_info()

        logger.debug(f"Step executed. Action: {action}, Reward: {reward}, Terminated: {terminated}")
        return observation, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        # Convert current_state to a numpy array observation
        current_state = self.game_state_manager.get_current_state()
        if not current_state or not current_state.map:
            # Return a zero array of default shape if state is not ready
            logger.warning("Game state or map not available for observation. Returning zero array.")
            return np.zeros(self.observation_space.shape, dtype=self.observation_space.dtype)

        map_grid = current_state.map.grid
        map_height = current_state.map.height
        map_width = current_state.map.width

        # Initialize observation array (map_height x map_width x num_features)
        # Features: cell_type, player_presence, enemy_presence, bomb_presence, powerup_presence
        observation_array = np.zeros((map_height, map_width, 5), dtype=np.uint8)

        # Populate cell types
        for y in range(map_height):
            for x in range(map_width):
                if 0 <= y < map_height and 0 <= x < map_width:
                    observation_array[y, x, 0] = map_grid[y][x] # Cell type

        # Populate player presence
        for player_info in current_state.players.values():
            # Only consider the player this environment is controlling if needed, or all players.
            # For now, let's mark all players.
            if player_info.is_alive:
                # Map world coordinates (float) to grid coordinates (int)
                # Assuming cell_size is implicit or derived. For now, simple scaling.
                grid_x = int(player_info.x / (current_state.map.width / map_width))
                grid_y = int(player_info.y / (current_state.map.height / map_height))
                if 0 <= grid_y < map_height and 0 <= grid_x < map_width:
                    observation_array[grid_y, grid_x, 1] = 1 # Player presence

        # Populate enemy presence
        for enemy_info in current_state.enemies.values():
            if enemy_info.is_alive:
                grid_x = int(enemy_info.x / (current_state.map.width / map_width))
                grid_y = int(enemy_info.y / (current_state.map.height / map_height))
                if 0 <= grid_y < map_height and 0 <= grid_x < map_width:
                    observation_array[grid_y, grid_x, 2] = 1 # Enemy presence

        # Populate weapon presence (bombs for simplicity)
        for weapon_info in current_state.weapons.values():
            # Assuming weapons are placed at grid cell centers or are large enough to cover a cell
            grid_x = int(weapon_info.x / (current_state.map.width / map_width))
            grid_y = int(weapon_info.y / (current_state.map.height / map_height))
            if 0 <= grid_y < map_height and 0 <= grid_x < map_width:
                observation_array[grid_y, grid_x, 3] = 1 # Weapon (bomb) presence

        # Populate power-up presence
        for power_up_info in current_state.power_ups.values():
            grid_x = int(power_up_info.x / (current_state.map.width / map_width))
            grid_y = int(power_up_info.y / (current_state.map.height / map_height))
            if 0 <= grid_y < map_height and 0 <= grid_x < map_width:
                observation_array[grid_y, grid_x, 4] = 1 # Power-up presence

        return observation_array

    def _get_info(self) -> Dict[str, Any]:
        current_state = self.game_state_manager.get_current_state()
        if not current_state:
            return {"error": "Game state not available"}

        info = {
            "game_id": current_state.game_id,
            "status": current_state.status,
            "level": current_state.level,
            "player_lives": current_state.players.get(self.player_id).lives if self.player_id in current_state.players else 0,
            "player_x": current_state.players.get(self.player_id).x if self.player_id in current_state.players else 0,
            "player_y": current_state.players.get(self.player_id).y if self.player_id in current_state.players else 0,
            "num_enemies": len(current_state.enemies),
            "num_weapons": len(current_state.weapons),
            "num_power_ups": len(current_state.power_ups),
        }
        return info

    def render(self) -> None:
        # Rendering logic for visualization (optional for training environments)
        if self.render_mode == "human":
            pass # Implement rendering if needed

    def close(self) -> None:
        # Close NATS connection or other resources
        logger.info(f"Closing BombermanEnv for game {self.game_id}")
        # No need to explicitly close nats_repository here as it's managed by the main app 
import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from app.entities.game_mode import GameModeType
from app.entities.player import UnitType
from app.entities.weapon import WeaponAction

from app.services.ai_action_mapper import action_to_inputs

from app.services.ai_observation import build_basic_observation
from app.services.game_service import GameService
from app.services.map_service import MapService
from app.models.game_models import GameSettings


if TYPE_CHECKING:
    from app.repositories.map_repository import MapRepository
    from app.services.ai_inference_service import AIInferenceService

@dataclass
class TrainingSession:
    session_id: str
    game_service: GameService
    player_id: str
    last_player_lives: int
    last_enemy_count: int


@dataclass
class TrainingResetResult:
    session_id: str
    observation_values: list[float]
    info_json: str


@dataclass
class TrainingStepResult:
    observation_values: list[float]
    reward: float
    terminated: bool
    truncated: bool
    info_json: str


class TrainingCoordinator:
    def __init__(
        self,
        map_repository: "MapRepository",
        ai_inference_service: "AIInferenceService"
    ) -> None:
        self.ai_inference_service = ai_inference_service
        self._map_repository = map_repository
        self._sessions: dict[str, TrainingSession] = {}

    async def reset(
        self,
        *,
        map_width: int | None,
        map_height: int | None,
        enemy_count: int | None,
        enable_enemies: bool | None,
        seed: int | None,
    ) -> TrainingResetResult:
        if seed is not None:
            random.seed(a=seed)
        defaults = GameSettings()
        game_settings = GameSettings(
            game_id=str(uuid4()),
            game_mode=GameModeType.CAMPAIGN,
            max_players=1,
            default_map_width=map_width or defaults.default_map_width,
            default_map_height=map_height or defaults.default_map_height,
        )

        if enemy_count is not None:
            if enemy_count <= 0:
                game_settings.enable_enemies = False
                game_settings.enemy_count_multiplier = -3.0
            else:
                game_settings.enable_enemies = True
                game_settings.enemy_count_multiplier = float(enemy_count - 3)
        if enable_enemies is not None:
            game_settings.enable_enemies = enable_enemies

        map_service = MapService(
            map_repository=self._map_repository,
            game_settings=game_settings,
        )
        game_service = GameService(
            game_settings=game_settings,
            map_service=map_service,
            ai_inference_service=self.ai_inference_service
        )
        await game_service.initialize_game()

        player_id = str(uuid4())
        game_service.add_player(
            player_id=player_id,
            unit_type=UnitType.BOMBERMAN,
        )
        player = game_service.get_player(player_id=player_id)
        if player is not None:
            player.ai = True

        game_service.start_game()

        observation = self._build_observation(
            game_service=game_service,
            player_id=player_id,
        )
        enemy_total = len(game_service.game_mode.enemies)
        session_id = str(uuid4())
        self._sessions[session_id] = TrainingSession(
            session_id=session_id,
            game_service=game_service,
            player_id=player_id,
            last_player_lives=player.lives if player else 0,
            last_enemy_count=enemy_total,
        )
        info_json = json.dumps(
            {
                "game_id": game_settings.game_id,
                "player_id": player_id,
                "map_width": game_settings.default_map_width,
                "map_height": game_settings.default_map_height,
            }
        )
        return TrainingResetResult(
            session_id=session_id,
            observation_values=observation,
            info_json=info_json,
        )

    async def step(
        self,
        *,
        session_id: str,
        action: int,
        delta_seconds: float,
    ) -> TrainingStepResult:
        session = self._sessions.get(session_id)
        if session is None:
            return TrainingStepResult(
                observation_values=[],
                reward=0.0,
                terminated=True,
                truncated=False,
                info_json=json.dumps({"error": "session_not_found"}),
            )

        game_service = session.game_service
        player = game_service.get_player(player_id=session.player_id)
        if player is None:
            return TrainingStepResult(
                observation_values=[],
                reward=0.0,
                terminated=True,
                truncated=False,
                info_json=json.dumps({"error": "player_not_found"}),
            )

        inputs = action_to_inputs(action=action)
        player.set_inputs(inputs=inputs)
        if action == 5:
            game_service.place_weapon(
                player_id=player.id,
                weapon_action=WeaponAction.PLACEWEAPON1,
            )

        await game_service.update(delta_seconds=delta_seconds)

        observation = self._build_observation(
            game_service=game_service,
            player_id=session.player_id,
        )

        enemy_total = len(game_service.game_mode.enemies)
        reward = self._calculate_reward(
            player_lives=player.lives,
            last_player_lives=session.last_player_lives,
            enemy_count=enemy_total,
            last_enemy_count=session.last_enemy_count,
            game_over=game_service.game_mode.game_over,
            player_alive=player.is_alive(),
        )
        terminated = game_service.game_mode.game_over or not player.is_alive()
        session.last_player_lives = player.lives
        session.last_enemy_count = enemy_total

        info_json = json.dumps(
            {
                "game_id": game_service.settings.game_id,
                "player_id": player.id,
                "enemy_count": enemy_total,
            }
        )

        return TrainingStepResult(
            observation_values=observation,
            reward=reward,
            terminated=terminated,
            truncated=False,
            info_json=info_json,
        )

    def _build_observation(self, *, game_service: GameService, player_id: str) -> list[float]:
        player = game_service.get_player(player_id=player_id)
        if player is None or game_service.game_mode.map is None:
            return []
        map_width = game_service.game_mode.map.width
        map_height = game_service.game_mode.map.height
        map_grid = game_service.game_mode.map.grid
        return build_basic_observation(
            map_grid=map_grid,
            map_width=map_width,
            map_height=map_height,
            cell_size=game_service.settings.cell_size,
            entity_x=player.x,
            entity_y=player.y,
            lives=player.lives,
            max_lives=game_service.settings.player_max_lives,
            enemy_count=len(game_service.game_mode.enemies),
            window_size=15,
        )

    def _calculate_reward(
        self,
        *,
        player_lives: int,
        last_player_lives: int,
        enemy_count: int,
        last_enemy_count: int,
        game_over: bool,
        player_alive: bool,
    ) -> float:
        reward = 0.0
        if player_lives < last_player_lives:
            reward -= 1.0
        if enemy_count < last_enemy_count:
            reward += float(last_enemy_count - enemy_count)
        if game_over:
            reward += 5.0 if player_alive else -5.0
        return reward


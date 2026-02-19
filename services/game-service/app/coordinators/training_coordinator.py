import json
import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4


from app.entities.game_mode import GameModeType
from app.entities.player import UnitType
from app.entities.weapon import WeaponAction

from app.services.ai_action_mapper import action_to_inputs

from app.services.ai_observation import build_observation, ObservationData, GRID_SIZE, STATS_SIZE
from app.services.game_service import GameService
from app.services.map_service import MapService
from app.models.game_models import GameSettings


if TYPE_CHECKING:
    from app.repositories.map_repository import MapRepository
    from app.services.ai_inference_service import AIInferenceService

IDLE_LIMIT: int = 50


@dataclass
class TrainingSession:
    session_id: str
    game_service: GameService
    player_id: str
    last_player_lives: int
    last_enemy_count: int
    last_x: float = 0.0
    last_y: float = 0.0
    last_closest_enemy_dist: float = 0.0
    total_steps: int = 0
    idle_steps: int = 0
    last_player_score: int = 0


@dataclass
class TrainingResetResult:
    session_id: str
    grid_values: list[float]
    stats_values: list[float]
    info_json: str


@dataclass
class TrainingStepResult:
    grid_values: list[float]
    stats_values: list[float]
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
            game_mode=GameModeType.TRAINING_IA,
            max_players=1,
            default_map_width=map_width or defaults.default_map_width,
            default_map_height=map_height or defaults.default_map_height,
            enemy_ai_controlled=False,
            time_limit=defaults.time_limit,  # Используем таймер из настроек по умолчанию (300 сек)
            randomize_spawn_positions=True,  # Включаем рандомизацию spawn точек для тренировочного режима
            randomize_spawn_assignment=True,  # Включаем рандомное распределение игроков по spawn точкам
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

        player.can_handle_ai_action = lambda x=None: False# patching to avoid back requests to the ai-service

        game_service.start_game()

        enemy_total = len(game_service.game_mode.enemies)

        player_x: float = player.x if player else 0.0
        player_y: float = player.y if player else 0.0

        closest_dist: float = self._closest_enemy_distance(
            game_service=game_service,
            px=player_x,
            py=player_y,
        )

        session_id = str(uuid4())
        self._sessions[session_id] = TrainingSession(
            session_id=session_id,
            game_service=game_service,
            player_id=player_id,
            last_player_lives=player.lives if player else 0,
            last_enemy_count=enemy_total,
            last_x=player_x,
            last_y=player_y,
            last_closest_enemy_dist=closest_dist,
            total_steps=0,
            idle_steps=0,
            last_player_score=0
        )

        obs: ObservationData = self._build_observation(
            session=self._sessions[session_id],
            player_id=player_id,
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
            grid_values=obs.grid_values,
            stats_values=obs.stats_values,
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
                grid_values=[0.0] * GRID_SIZE,
                stats_values=[0.0] * STATS_SIZE,
                reward=0.0,
                terminated=True,
                truncated=False,
                info_json=json.dumps({"error": "session_not_found"}),
            )

        game_service = session.game_service
        player = game_service.get_player(player_id=session.player_id)
        if player is None:
            return TrainingStepResult(
                grid_values=[0.0] * GRID_SIZE,
                stats_values=[0.0] * STATS_SIZE,
                reward=0.0,
                terminated=True,
                truncated=False,
                info_json=json.dumps({"error": "player_not_found"}),
            )

        inputs = action_to_inputs(action=action)
        player.set_inputs(inputs=inputs)
        if action == 5:
            is_placed_weapon = game_service.place_weapon(
                player_id=player.id,
                weapon_action=WeaponAction.PLACEWEAPON1,
            )
            game_service.team_service.add_score_to_player_team(
                player_id=player.id,
                points=game_service.settings.placed_bomb_score if is_placed_weapon else game_service.settings.couldnt_place_bomb
            )

        await game_service.update(delta_seconds=delta_seconds)

        time_to_target = player.get_remaining_movement_time()
        if time_to_target:
            await game_service.update(delta_seconds=time_to_target+0.01)

        session.total_steps += 1

        obs: ObservationData = self._build_observation(
            session=session,
            player_id=session.player_id,
        )

        enemy_total = len(game_service.game_mode.enemies)
        px: float = player.x
        py: float = player.y

        moved: bool = abs(px - session.last_x) > 1.0 or abs(py - session.last_y) > 1.0
        if moved:
            session.idle_steps = 0
        else:
            session.idle_steps += 1

        closest_dist: float = game_service.game_mode.get_closest_enemy_distance(
            px=px,
            py=py,
        )

        session.last_player_lives = player.lives
        session.last_x = px
        session.last_y = py
        session.last_closest_enemy_dist = closest_dist

        terminated: bool = game_service.game_mode.game_over or not player.is_alive()
        # Truncate если превышен лимит шагов, лимит простоя, или истёк таймер
        truncated: bool = (
            session.idle_steps >= IDLE_LIMIT
        )

        info_json = json.dumps(
            {
                "game_id": game_service.settings.game_id,
                "player_id": player.id,
                "enemy_count": enemy_total,
                "total_steps": session.total_steps,
                "idle_steps": session.idle_steps,
            }
        )

        player_team = game_service.team_service.get_player_team(player_id=player.id)
        reward = 0
        if player_team:
            reward = player_team.score - session.last_player_score
            session.last_player_score = player_team.score

        return TrainingStepResult(
            grid_values=obs.grid_values,
            stats_values=obs.stats_values,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info_json=info_json,
        )


    def _build_observation(self, *, session: TrainingSession, player_id: str) -> ObservationData:
        game_service: GameService = session.game_service
        player = game_service.get_player(player_id=player_id)
        if player is None or game_service.game_mode.map is None:
            return ObservationData(
                grid_values=[0.0] * GRID_SIZE,
                stats_values=[0.0] * STATS_SIZE,
            )
        map_width: int = game_service.game_mode.map.width
        map_height: int = game_service.game_mode.map.height
        map_grid = game_service.game_mode.map.grid

        enemies_positions: list[tuple[float, float]] = [
            (e.x, e.y) for e in game_service.game_mode.enemies if not e.destroyed
        ]
        enemies_positions.extend(
            (p.x, p.y) for p in game_service.game_mode.players.values() if p.is_alive() and p.id != player.id
        )
        weapons_positions: list[tuple[float, float]] = [
            (w.x, w.y) for w in game_service.game_mode.weapons.values()
        ]
        power_ups_positions: list[tuple[float, float]] = [
            (p.x, p.y) for p in game_service.game_mode.power_ups.values()
        ]
        active_bombs: int = sum(
            1 for w in game_service.game_mode.weapons.values()
            if w.owner_id == player_id
        )
        return build_observation(
            map_grid=map_grid,
            map_width=map_width,
            map_height=map_height,
            cell_size=game_service.settings.cell_size,
            entity_x=player.x,
            entity_y=player.y,
            lives=player.lives,
            max_lives=game_service.settings.player_max_lives,
            enemy_count=len(game_service.game_mode.enemies),
            max_enemies=game_service.map_service.enemy_count + (len(game_service.game_mode.players) - 1),
            bombs_left=max(0, player.primary_weapon_max_count - active_bombs),
            max_bombs=player.primary_weapon_max_count,
            bomb_power=player.primary_weapon_power,
            max_bomb_power=game_service.settings.max_bomb_power,
            is_invulnerable=player.invulnerable,
            speed=player.speed,
            max_speed=game_service.settings.player_max_speed,
            time_left=game_service.game_mode.time_remaining,
            time_limit=float(game_service.settings.time_limit or 0),
            enemies_positions=enemies_positions,
            weapons_positions=weapons_positions,
            power_ups_positions=power_ups_positions,
            closest_enemy=session.last_closest_enemy_dist
        )

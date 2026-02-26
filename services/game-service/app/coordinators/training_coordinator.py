import json
import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from app.entities import Entity
from app.entities.game_mode import GameModeType
from app.entities.player import UnitType
from app.entities.weapon import WeaponAction
from app.entities.enemy import Enemy, EnemyType

from app.services.ai_action_mapper import action_to_inputs, action_to_direction

from app.services.ai_observation import build_observation, ObservationData, GRID_ENEMY_INFERENCE_SIZE, \
    GRID_PLAYER_INFERENCE_SIZE, STATS_SIZE, DEFAULT_WINDOW_SIZE, get_closest_enemy_distance
from app.services.game_service import GameService
from app.services.map_service import MapService
from app.models.game_models import GameSettings

logger = logging.getLogger(__name__)

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
    last_x: float = 0.0
    last_y: float = 0.0
    total_steps: int = 0
    idle_steps: int = 0
    last_player_score: int = 0
    training_player: bool = True
    max_enemies: int = 0
    max_lives_val: int = 0
    max_bombs: int = 0
    last_closest_enemy: float = 0.0


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

class EntityType(Enum):
    Player = 0
    Enemy = 1

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
        map_width: int = DEFAULT_WINDOW_SIZE,
        map_height: int = DEFAULT_WINDOW_SIZE,
        enemy_count: int = 3,
        bomb_power: int = 1,
        count_bombs: int = 1,
        player_lives: int = 3,
        training_player: bool = True,
        seed: int | None,
    ) -> TrainingResetResult:
        # if seed is not None:
        #     random.seed(a=seed)
        try:
            if training_player:
                self.grid_size = GRID_PLAYER_INFERENCE_SIZE
            else:
                self.grid_size = GRID_ENEMY_INFERENCE_SIZE

            defaults = GameSettings()
            game_settings = GameSettings(
                game_id=str(uuid4()),
                game_mode=GameModeType.TRAINING_IA,
                max_players=10,
                default_map_width=map_width or defaults.default_map_width,
                default_map_height=map_height or defaults.default_map_height,
                enemy_ai_controlled=False,
                enable_enemies=True,
                time_limit=defaults.time_limit,  # Используем таймер из настроек по умолчанию (300 сек)
                randomize_spawn_positions=True,  # Включаем рандомизацию spawn точек для тренировочного режима
                randomize_spawn_assignment=True,  # Включаем рандомное распределение игроков по spawn точкам
                spawn_points_count=1,
                allow_spawn_on_empty_cells=True,
                default_bomb_power=bomb_power,
                default_count_bombs=count_bombs,
                player_start_lives=player_lives,
                powerup_drop_chance=0.7,
                enemy_powerup_drop_chance=0.7
            )

            map_service = MapService(
                map_repository=self._map_repository,
                game_settings=game_settings,
            )
            game_service = GameService(
                game_settings=game_settings,
                map_service=map_service,
                ai_inference_service=self.ai_inference_service
            )

            if training_player:
                player_ai_count: int = random.randint(1, enemy_count)
                game_settings.enemy_count_multiplier = 1
                game_settings.enemy_on_start = (enemy_count - player_ai_count) - 1
            else:
                # player_ai_count: int = 1
                player_ai_count: int = enemy_count
                game_settings.enemy_count_multiplier = 1
                game_settings.enemy_on_start = - 1

            await game_service.initialize_game()


            if training_player:
                # Player
                entity_id = str(uuid4())
                game_service.add_player(
                    player_id=entity_id,
                    unit_type=UnitType.BOMBERMAN,
                )
                entity = game_service.get_player(player_id=entity_id)
                if entity is not None:
                    entity.ai = True

            else:
                # Enemy
                entity = Enemy(
                    x=0,
                    y=0,
                    size=game_service.settings.cell_size,
                    enemy_type=random.choice(list(EnemyType)),
                    speed=game_service.settings.player_default_speed,
                    map=game_service.game_mode.map,
                    settings=game_service.settings,
                    ai=True
                )
                entity_id = entity.id
                # game_service.settings.enable_enemies = False
                game_service.game_mode.add_player(
                    player=entity,
                )
                game_service.team_service.auto_distribute_players([entity])

            entity.can_handle_ai_action = lambda x=None: False  # patching to avoid back requests to the ai-service

            for i in range(player_ai_count):
                game_service.add_player(
                    player_id=str(uuid4()),
                    unit_type=UnitType.BOMBERMAN,
                    ai_player=True
                )

            game_service.start_game()

            entity_x: float = entity.x if entity else 0.0
            entity_y: float = entity.y if entity else 0.0

            if training_player:
                max_bombs: int = entity.primary_weapon_max_count
                max_lives_val: int = game_service.settings.player_max_lives
            else:
                max_bombs: int = 0
                max_lives_val: int = game_service.settings.player_max_lives

            session_id = str(uuid4())
            self._sessions[session_id] = TrainingSession(
                session_id=session_id,
                game_service=game_service,
                player_id=entity_id,
                last_player_lives=entity.lives if entity else 0,
                last_x=entity_x,
                last_y=entity_y,
                total_steps=0,
                idle_steps=0,
                last_player_score=0,
                training_player=training_player,
                max_enemies=enemy_count,
                max_lives_val=max_lives_val,
                max_bombs=max_bombs
            )

            obs: ObservationData = self._build_observation(
                session=self._sessions[session_id],
                entity=entity,
            )

            info_json = json.dumps(
                {
                    "game_id": game_settings.game_id,
                    "player_id": entity_id,
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
        except Exception as e:
            logger.critical(f"error happened: {e}")

    async def step(
        self,
        *,
        session_id: str,
        action: int,
        delta_seconds: float,
    ) -> TrainingStepResult:
        try:
            session = self._sessions.get(session_id)
            if session is None:
                return TrainingStepResult(
                    grid_values=[0.0] * self.grid_size,
                    stats_values=[0.0] * STATS_SIZE,
                    reward=0.0,
                    terminated=True,
                    truncated=False,
                    info_json=json.dumps({"error": "session_not_found"}),
                )

            game_service = session.game_service

            training_player: bool = session.training_player
            if training_player:
                entity = game_service.get_player(player_id=session.player_id)
                inputs = action_to_inputs(action=action)
                entity.set_inputs(inputs=inputs)
                if action == 5:
                    is_placed_weapon = game_service.place_weapon(
                        player_id=entity.id,
                        weapon_action=WeaponAction.PLACEWEAPON1,
                    )
                    game_service.team_service.add_score_to_player_team(
                        player_id=entity.id,
                        points=game_service.settings.placed_bomb_score if is_placed_weapon else game_service.settings.couldnt_place_bomb
                    )
            else:
                entity = game_service.game_mode.enemies.get(session.player_id, None)
                entity.direction = action_to_direction(action=action)

            if entity is None:
                logger.error("player не найден в сессии, чтото пошло не так.")
                return TrainingStepResult(
                    grid_values=[0.0] * self.grid_size,
                    stats_values=[0.0] * STATS_SIZE,
                    reward=0.0,
                    terminated=True,
                    truncated=False,
                    info_json=json.dumps({"error": "player_not_found"}),
                )


            await game_service.update(delta_seconds=delta_seconds)

            time_to_target = entity.get_remaining_movement_time()
            if time_to_target:
                await game_service.update(delta_seconds=time_to_target + 0.01)

            session.total_steps += 1

            obs: ObservationData = self._build_observation(
                session=session,
                entity=entity,
            )

            px: float = entity.x
            py: float = entity.y

            moved: bool = abs(px - session.last_x) > 1.0 or abs(py - session.last_y) > 1.0
            if moved:
                session.idle_steps = 0
            else:
                session.idle_steps += 1

            session.last_player_lives = entity.lives
            session.last_x = px
            session.last_y = py

            terminated: bool = game_service.game_mode.game_over or not entity.is_alive()
            # Truncate если превышен лимит шагов, лимит простоя, или истёк таймер
            if training_player:
                truncated: bool = (
                        session.idle_steps >= IDLE_LIMIT
                )
            else:
                truncated: bool = (
                        session.idle_steps >= IDLE_LIMIT or
                        game_service.game_mode.level > 1
                )

            info_json = json.dumps(
                {
                    "game_id": game_service.settings.game_id,
                    "player_id": entity.id,
                    "total_steps": session.total_steps,
                    "idle_steps": session.idle_steps,
                }
            )

            player_team = game_service.team_service.get_player_team(player_id=entity.id)
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
        except Exception as e:
            logger.critical(f"error happened: {e}")


    def _build_observation(self, *, session: TrainingSession, entity: Entity) -> ObservationData:
        game_service: GameService = session.game_service

        players_positions: list[tuple[float, float]] = []
        if session.training_player:
            enemies_positions: list[tuple[float, float]] = [
                (e.x, e.y) for e in game_service.game_mode.enemies.values() if e.is_alive() and e.id != entity.id
            ]
        else:
            enemies_positions = []

        if not session.training_player:
            players_positions.extend(
                (p.x, p.y) for p in game_service.game_mode.players.values() if p.is_alive() and p.id != entity.id
            )

        weapons_positions: list[tuple[float, float]] = [
            (w.x, w.y) for w in game_service.game_mode.weapons.values()
        ]
        power_ups_positions: list[tuple[float, float]] = [
            (p.x, p.y) for p in game_service.game_mode.power_ups.values()
        ]

        in_blast_zone: float = (
            1.0
            if game_service.game_mode.is_entity_in_any_blast_zone(entity_x=entity.x, entity_y=entity.y)
            else 0.0
        )
        #Отнимаем у игрока очки за нахождение в зоне взрыва бомбы
        if in_blast_zone:
            session.game_service.team_service.get_player_team(
                player_id=entity.id
            ).add_score(
                points=session.game_service.settings.in_blast_zone_score
            )

        if session.training_player:
            active_bombs: int = sum(
                1 for w in game_service.game_mode.weapons.values()
                if w.owner_id == entity.id
            )

            bomb_left: int = max(0, session.max_bombs - active_bombs)
        else:
            bomb_left: int = 0

        entities_positions = []
        entities_positions.extend(players_positions)

        if session.training_player:
            entities_positions.extend(enemies_positions)

        closest_enemy = get_closest_enemy_distance(
            px=entity.x,
            py=entity.y,
            enemies=entities_positions,
            cell_size=game_service.settings.cell_size,
            map_width=game_service.game_mode.map.width,
            map_height=game_service.game_mode.map.height
        )
        if session.last_closest_enemy - closest_enemy >= 0.06: # ~0.03 = 1 клетка приближения
            # Прибавляем игроку очки за приближение к врагу
            session.game_service.team_service.get_player_team(
                player_id=entity.id
            ).add_score(
                points=session.game_service.settings.compensation_move_toward_enemy_score
            )
            session.last_closest_enemy = closest_enemy
        elif session.last_closest_enemy - closest_enemy <= -0.06: # ~0.03 = 1 клетка приближения:
            session.last_closest_enemy = closest_enemy




        return build_observation(
            closest_enemy=closest_enemy,
            is_player=session.training_player,
            is_cooperative=False,
            map_grid=game_service.game_mode.map.grid,
            map_width=game_service.game_mode.map.width,
            map_height=game_service.game_mode.map.height,
            cell_size=game_service.settings.cell_size,
            entity_x=entity.x,
            entity_y=entity.y,
            lives=entity.lives,
            max_lives=session.max_lives_val,
            enemy_count=len(entities_positions),
            max_enemies=session.max_enemies,
            bombs_left=bomb_left,
            max_bombs=session.max_bombs,
            is_invulnerable=entity.invulnerable,
            in_blast_zone=in_blast_zone,
            time_left=game_service.game_mode.time_remaining,
            time_limit=float(game_service.settings.time_limit or 0),
            enemies_positions=enemies_positions,
            players_positions=players_positions,
            weapons_positions=weapons_positions,
            power_ups_positions=power_ups_positions,
        )

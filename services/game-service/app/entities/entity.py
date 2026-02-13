from abc import abstractmethod

import math
import random
import time
import uuid
import logging
from typing import Any, TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.entities import Map
    from app.models.game_models import GameSettings


logger = logging.getLogger(__name__)

class Entity:
    """Базовый класс для всех игровых сущностей."""
    scale_size: float = 1.0

    def __init__(
        self,
        map: "Map",
        settings: "GameSettings",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        id: str | None = None,
        name: str = "",
        ai: bool = False,
        speed: float = 0.0,
        lives: int = 1,
        invulnerable: bool = False,
        color: str = "#FFFFFF"  # Белый цвет по умолчанию
    ):
        try:
            self.map = map
            self.settings = settings

            self.x: float = x
            self.y: float = y
            self.width: float = width
            self.height: float = height
            self.id: str = id if id is not None else str(uuid.uuid4())
            self.name: str = name
            self.destroyed: bool = False
            # State
            self.destroy_animation_timer: float = 0

            self.ai: bool = ai
            self.ai_last_action_time: float = 0.0
            self.move_timer = 0

            self.speed: float = speed
            self.lives: int = lives
            self.invulnerable: bool = invulnerable
            self.color: str = color

            # таймер бессмертия после получения урона, по умолчанию таймер для enemy должен быть переопределен для других типов
            self.invulnerable_timer: float = 0

            self.direction: tuple[float, float] = (0, 1)  # Направление

            logger.debug(f"Entity created: id={self.id}, name={name}, position=({x}, {y})")
        except Exception as e:
            logger.error(f"Error creating entity: {e}", exc_info=True)
            raise

    @abstractmethod
    def get_changes(self, *args, **kwargs):
        """Возвращает последние изменения в обьекте,
        каждый класс должен реализовывать самостоятельно логику
        и базироваться на своей моделе обновлений данных"""
        return self._state

    def get_direction(self, delta_time: float) -> tuple[float, float]:
        """Get a random normalized direction vector"""
        try:
            # рассчет движерия ботов
            if not self.ai:
                # Обновление таймера движения
                self.move_timer += delta_time
                # Смена направления периодически или при столкновении со стеной
                change_direction_interval: float = 1.0 + random.random() * 2.0
                if self.move_timer >= change_direction_interval:
                    # Choose one of four cardinal directions
                    # choices = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    choices = self.map.get_available_direction(
                        x=round(self.x / self.settings.cell_size),
                        y=round(self.y / self.settings.cell_size)
                    )
                    if not choices:
                        choices = [0,0]
                    direction = random.choice(choices)
                    self.direction = direction
                    self.move_timer = 0

            logger.debug(f"Enemy new direction: {self.direction}")
            return self.direction
        except Exception as e:
            logger.error(f"Error generating random direction: {e}", exc_info=True)
            # Fallback to a default direction
            return (0, 1)

    def is_alive(self):
        if not self.destroyed:
            return True
        return False

    def set_hit(self) -> bool:
        if self.invulnerable:
            return False
        self.lives -= 1
        self.invulnerable = True
        self.invulnerable_timer = self.settings.enemy_invulnerable_time
        if self.lives <= 0:
            self.destroyed = True
        return True


    def move(self, delta_time: float) -> bool:
        # Обработка движения

        dx, dy = self.get_direction(delta_time=delta_time)
        # Попытка движения в текущем направлении
        dx: float = dx * self.speed
        dy: float = dy * self.speed

        # # Нормализация диагонального движения
        # if dx != 0 and dy != 0:
        #     normalize: float = 1 / math.sqrt(2)
        #     dx *= normalize
        #     dy *= normalize

        # Применяем delta time
        dx *= delta_time * 60
        dy *= delta_time * 60

        # Движение с проверкой коллизий (ось X)
        # Движение с проверкой коллизий (ось Y)
        if dx != 0 or dy != 0:
            new_x: float = self.x + dx
            new_y: float = self.y + dy
            #TODO доработать проверку коллизий со стенами в методе получения направления,
            # чтобы сразу отсечь невозможные направления и вернуть только то что возможно
            # Move with collision detection (X axis)
            collision_x = self.check_collision(new_x, self.y)
            if not collision_x:
                self.x = new_x

            # Move with collision detection (Y axis)
            collision_y = self.check_collision(self.x, new_y)
            if not collision_y:
                self.y = new_y

            # If collision occurred, change direction
            if collision_x or collision_y:
                self.move_timer = 10
                self.direction = self.get_direction(delta_time=delta_time)
            return True


            # if not self.check_collision(
            #         new_x=new_x,
            #         new_y=new_y,
            # ):
            #     self.x = new_x#round(new_x / self.settings.cell_size) * self.settings.cell_size
            #     self.y = new_y#round(new_y / self.settings.cell_size) * self.settings.cell_size
            #     return True
            # else:
            #     self.move_timer = 10
            #     self.get_direction(delta_time=delta_time)
        return False


    def update(self, delta_time: float = None) -> None:
        """Обновляет состояние сущности. Должен быть расширен в дочерних классах."""
        try:
            # Update invulnerability
            if self.invulnerable:
                self.invulnerable_timer -= delta_time
                if self.invulnerable_timer <= 0:
                    logger.debug(f"Entity {self.id} ({self.name}) is no longer invulnerable")
                    self.invulnerable = False
                    self.invulnerable_timer = 0

            #Update moving
            self.move(delta_time=delta_time)

        except Exception as e:
            logger.error(f"Error updating entity {self.id} ({self.name}): {e}", exc_info=True)


    def check_collision(
            self,
            new_x: float,
            new_y: float,
    ) -> bool:
        """Проверить коллизию сущности"""
        try:
            # Вычисляем клетки сетки, с которыми пересекается сущность
            grid_left: int = int(new_x / self.settings.cell_size)
            grid_right: int = int((new_x + self.width) / self.settings.cell_size)
            grid_top: int = int(new_y / self.settings.cell_size)
            grid_bottom: int = int((new_y + self.height) / self.settings.cell_size)

            # Check all corners in the map
            if (self.map.is_solid(grid_left, grid_top) or
                    self.map.is_solid(grid_right, grid_top) or
                    self.map.is_solid(grid_left, grid_bottom) or
                    self.map.is_solid(grid_right, grid_bottom)):
                return True
            return False

            # x_grid = round(new_x / self.settings.cell_size)
            # y_grid = round(new_y / self.settings.cell_size)
            # if self.map.is_solid(x_grid, y_grid):
            #     return True
            # return False

        except Exception as e:
            logger.error(f"Error updating entity {self.id} ({self.name}): {e}", exc_info=True)
            return False

    def can_handle_ai_action(self, now_time: float = None) -> bool:
        if not now_time:
            now_time = time.time()
        if now_time - self.ai_last_action_time >= settings.AI_ACTION_INTERVAL:
            return True
        return False
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
            
            # AI grid-based movement tracking
            # Target cell coordinates for AI entities (None when on a cell and ready for new action)
            self.ai_target_cell_x: float | None = None
            self.ai_target_cell_y: float | None = None

            self.speed: float = speed
            self.lives: int = lives
            self.invulnerable: bool = invulnerable
            self.color: str = color

            # таймер бессмертия после получения урона, по умолчанию таймер для enemy должен быть переопределен для других типов
            self.invulnerable_timer: float = 0

            self.direction: tuple[int, int] = (0, 0)  # Направление
            
            # For AI entities, ensure initial position is aligned to grid
            if self.ai:
                self._snap_to_grid()

            logger.debug(f"Entity created: id={self.id}, name={name}, position=({self.x}, {self.y})")
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
                        choices = [(0,0)]
                    self.direction = random.choice(choices)
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
        """
        Handle entity movement.
        For AI entities, implements grid-based discrete movement (cell to cell).
        For non-AI entities, uses continuous movement.
        """
        # AI entities use grid-based discrete movement
        if self.ai:
            return self._move_ai_grid_based(delta_time=delta_time)
        
        # Non-AI entities use continuous movement (original logic)
        return self._move_continuous(delta_time=delta_time)

    def _move_ai_grid_based(self, delta_time: float) -> bool:
        """
        Grid-based movement for AI entities.
        Moves entity from cell to cell, stopping exactly on each cell.
        
        Returns:
            True if movement occurred, False otherwise
        """
        try:
            # If moving to target cell
            if self.ai_target_cell_x is not None and self.ai_target_cell_y is not None:
                # Calculate distance to target
                dx_target = self.ai_target_cell_x - self.x
                dy_target = self.ai_target_cell_y - self.y
                distance_to_target = math.sqrt(dx_target * dx_target + dy_target * dy_target)
                
                # Calculate movement step
                direction_x = dx_target / distance_to_target if distance_to_target > 0 else 0
                direction_y = dy_target / distance_to_target if distance_to_target > 0 else 0
                
                step_distance = self.speed * delta_time * 60
                
                # Move towards target, but don't overshoot
                if step_distance >= distance_to_target:
                    # Reached target cell - snap to grid and reset target
                    self.x = self.ai_target_cell_x
                    self.y = self.ai_target_cell_y
                    self._snap_to_grid()
                    self.ai_target_cell_x = None
                    self.ai_target_cell_y = None
                    return True
                else:
                    # Move towards target
                    new_x = self.x + direction_x * step_distance
                    new_y = self.y + direction_y * step_distance
                    
                    # Check collision before moving
                    if not self.check_collision(new_x, new_y):
                        self.x = new_x
                        self.y = new_y
                        return True
                    else:
                        # Collision detected - stop and reset target
                        self._snap_to_grid()
                        self.ai_target_cell_x = None
                        self.ai_target_cell_y = None
                        return False
            
            # Ready for new action - get direction and set target cell
            direction = self.get_direction(delta_time=delta_time)
            
            # If no direction, don't move
            if direction[0] == 0 and direction[1] == 0:
                return False
            
            # Calculate current cell
            current_cell_x = int(round(self.x / self.settings.cell_size))
            current_cell_y = int(round(self.y / self.settings.cell_size))
            
            # Calculate target cell
            target_cell_x = current_cell_x + int(direction[0])
            target_cell_y = current_cell_y + int(direction[1])
            
            # Convert to world coordinates
            target_x = target_cell_x * self.settings.cell_size
            target_y = target_cell_y * self.settings.cell_size
            
            # Check collision before setting target
            if self.check_collision(target_x, target_y):
                # Target cell is blocked - don't move
                return False
            
            # Set target and start moving
            self.ai_target_cell_x = target_x
            self.ai_target_cell_y = target_y
            
            # Start moving towards target
            return self._move_ai_grid_based(delta_time=delta_time)
            
        except Exception as e:
            logger.error(f"Error in AI grid-based movement: {e}", exc_info=True)
            # Reset target on error
            self.ai_target_cell_x = None
            self.ai_target_cell_y = None
            return False

    def _move_continuous(self, delta_time: float) -> bool:
        """
        Continuous movement for non-AI entities (original logic).
        
        Returns:
            True if movement occurred, False otherwise
        """
        try:
            dx, dy = self.get_direction(delta_time=delta_time)
            # Попытка движения в текущем направлении
            dx: float = dx * self.speed
            dy: float = dy * self.speed

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

            return False
        except Exception as e:
            logger.error(f"Error in continuous movement: {e}", exc_info=True)
            return False


    def update(self, delta_time: float = None) -> bool:
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
            return self.move(delta_time=delta_time)

        except Exception as e:
            logger.error(f"Error updating entity {self.id} ({self.name}): {e}", exc_info=True)
            return False


    def check_collision(
            self,
            new_x: float,
            new_y: float,
    ) -> bool:
        """
        Проверить коллизию сущности.
        
        Проверяет только клетки, в которые сущность входит при движении,
        исключая текущую клетку, чтобы игрок мог уйти с клетки с бомбой.
        Оптимизировано: проверяет только углы в направлении движения.
        
        Args:
            new_x: Новая X координата сущности в пикселях
            new_y: Новая Y координата сущности в пикселях
            
        Returns:
            True если обнаружена коллизия, False иначе
        """
        try:
            # Вычисляем клетки сетки новой позиции
            new_grid_left: int = int(new_x / self.settings.cell_size)
            new_grid_right: int = int((new_x + self.width) / self.settings.cell_size)
            new_grid_top: int = int(new_y / self.settings.cell_size)
            new_grid_bottom: int = int((new_y + self.height) / self.settings.cell_size)

            # Вычисляем текущую клетку сущности (где находится центр)
            # Это нужно, чтобы исключить текущую клетку из проверки коллизий
            current_cell_x: int = int((self.x + self.width / 2) / self.settings.cell_size)
            current_cell_y: int = int((self.y + self.height / 2) / self.settings.cell_size)

            # Определяем, по какой оси происходит движение
            # Метод вызывается отдельно для X и Y, поэтому проверяем только измененную ось
            dir_x, dir_y = self.direction
            
            # Движение по оси X (влево или вправо)
            if dir_x != 0:
                if dir_x > 0:  # Движение вправо - проверяем только правые углы
                    if ((new_grid_right != current_cell_x or new_grid_top != current_cell_y) and 
                        self.map.is_solid(new_grid_right, new_grid_top)):
                        return True
                    if ((new_grid_right != current_cell_x or new_grid_bottom != current_cell_y) and 
                        self.map.is_solid(new_grid_right, new_grid_bottom)):
                        return True
                else:  # Движение влево - проверяем только левые углы
                    if ((new_grid_left != current_cell_x or new_grid_top != current_cell_y) and 
                        self.map.is_solid(new_grid_left, new_grid_top)):
                        return True
                    if ((new_grid_left != current_cell_x or new_grid_bottom != current_cell_y) and 
                        self.map.is_solid(new_grid_left, new_grid_bottom)):
                        return True

            # Движение по оси Y (вверх или вниз)
            if dir_y != 0:
                if dir_y > 0:  # Движение вниз - проверяем только нижние углы
                    if ((new_grid_left != current_cell_x or new_grid_bottom != current_cell_y) and 
                        self.map.is_solid(new_grid_left, new_grid_bottom)):
                        return True
                    if ((new_grid_right != current_cell_x or new_grid_bottom != current_cell_y) and 
                        self.map.is_solid(new_grid_right, new_grid_bottom)):
                        return True
                else:  # Движение вверх - проверяем только верхние углы
                    if ((new_grid_left != current_cell_x or new_grid_top != current_cell_y) and 
                        self.map.is_solid(new_grid_left, new_grid_top)):
                        return True
                    if ((new_grid_right != current_cell_x or new_grid_top != current_cell_y) and 
                        self.map.is_solid(new_grid_right, new_grid_top)):
                        return True

            return False

        except Exception as e:
            logger.error(f"Error updating entity {self.id} ({self.name}): {e}", exc_info=True)
            return False

    def _is_on_grid_cell(self, tolerance: float = 0.1) -> bool:
        """
        Check if entity is exactly on a grid cell (with tolerance for rounding errors).
        Used for AI entities to determine if they can change direction.
        
        Args:
            tolerance: Maximum distance from grid cell center to consider "on cell"
        
        Returns:
            True if entity is aligned to grid cell, False otherwise
        """
        try:
            # Calculate grid cell coordinates
            cell_x = round(self.x / self.settings.cell_size) * self.settings.cell_size
            cell_y = round(self.y / self.settings.cell_size) * self.settings.cell_size
            
            # Check if current position is close enough to grid cell center
            dx = abs(self.x - cell_x)
            dy = abs(self.y - cell_y)
            
            return dx <= tolerance and dy <= tolerance
        except Exception as e:
            logger.error(f"Error checking grid cell alignment: {e}", exc_info=True)
            return False

    def _snap_to_grid(self) -> None:
        """
        Snap entity coordinates exactly to the nearest grid cell.
        Used when AI entity reaches target cell.
        """
        try:
            # Calculate nearest grid cell coordinates
            cell_x = round(self.x / self.settings.cell_size) * self.settings.cell_size
            cell_y = round(self.y / self.settings.cell_size) * self.settings.cell_size
            
            # Snap to grid
            self.x = cell_x
            self.y = cell_y
        except Exception as e:
            logger.error(f"Error snapping to grid: {e}", exc_info=True)

    def get_remaining_movement_time(self) -> float:
        """
        Get remaining time to complete movement to target cell for AI entities.
        
        Returns:
            Remaining time in seconds to reach target cell.
            Returns 0.0 if entity is not AI, not moving, or has no target.
        """
        try:
            # Only for AI entities
            if not self.ai:
                return 0.0
            
            # Check if entity is moving to target cell
            if self.ai_target_cell_x is None or self.ai_target_cell_y is None:
                return 0.0
            
            # Calculate distance to target
            dx_target = self.ai_target_cell_x - self.x
            dy_target = self.ai_target_cell_y - self.y
            distance_to_target = math.sqrt(dx_target * dx_target + dy_target * dy_target)
            
            # If already at target (or very close), return 0
            if distance_to_target < 0.1:
                return 0.0
            
            # Calculate remaining time: distance / speed
            # Speed is in units per second (multiplied by 60 in movement calculation)
            if self.speed <= 0:
                return 0.0
            
            # Movement uses: speed * delta_time * 60
            # So effective speed per second is: speed * 60
            effective_speed = self.speed * 60.0
            
            remaining_time = distance_to_target / effective_speed
            
            return remaining_time
        except Exception as e:
            logger.error(f"Error calculating remaining movement time: {e}", exc_info=True)
            return 0.0

    def can_handle_ai_action(self, now_time: float = None) -> bool:
        """
        Check if AI entity can handle a new action.
        For AI entities, also checks if entity is exactly on a grid cell.
        
        Args:
            now_time: Current time (if None, uses time.time())
        
        Returns:
            True if entity can handle new action, False otherwise
        """
        if not now_time:
            now_time = time.time()
        
        # Check time interval
        if now_time - self.ai_last_action_time < settings.AI_ACTION_INTERVAL:
            return False
        
        # For AI entities, also check if they are on a grid cell
        if self.ai:
            # Check if entity is moving between cells
            if self.ai_target_cell_x is not None or self.ai_target_cell_y is not None:
                return False
            
            # Check if entity is exactly aligned to grid cell
            if not self._is_on_grid_cell():
                return False
        
        return True
import random
import time
import math
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Set

from ..config import settings
from ..entities.map import Map, CellType
from ..entities.player import Player
from ..entities.enemy import Enemy, EnemyType  # Import EnemyType
from ..entities.bomb import Bomb
from ..entities.power_up import PowerUp, PowerUpType

logger = logging.getLogger(__name__)

class GameService:
    def __init__(self):
        try:
            # Game settings
            self.cell_size: int = 40
            self.width: int = 23
            self.height: int = 23
            
            # Game state
            self.players: Dict[str, Player] = {}  # Dictionary of player_id -> Player
            self.enemies: List[Enemy] = []
            self.bombs: Dict[str, Bomb] = {}
            self.power_ups: Dict[str, PowerUp] = {}
            self.map: Map = Map(self.width, self.height)
            self.score: int = 0
            self.level: int = 1
            self.game_over: bool = False
            self.last_update_time: float = time.time()
            self.timer_is_alive: float = time.time()
            
            # Initialize game
            self.map.generate_map()
            self.create_enemies()
            
            logger.info(f"Game service initialized: map size {self.width}x{self.height}, cell size {self.cell_size}")
        except Exception as e:
            logger.error(f"Error initializing game service: {e}", exc_info=True)
            raise



    def add_player(self, player: Player) -> bool:
        """Add a player to the game"""
        try:
            if len(self.players) >= 4:  # Max 4 players
                logger.debug(f"Cannot add player {player.id}: maximum number of players reached")
                return False
            
            # Set player position at a valid starting point
            start_positions: List[Tuple[int, int]] = [
                (1, 1),                                # Top-left
                (self.width - 2, 1),                   # Top-right
                (1, self.height - 2),                  # Bottom-left
                (self.width - 2, self.height - 2)      # Bottom-right
            ]
            
            # Assign next available position
            player_idx: int = len(self.players)
            if player_idx < len(start_positions):
                x, y = start_positions[player_idx]
                player.x = x * self.cell_size
                player.y = y * self.cell_size
                player.color = player.COLORS[player_idx]
                
                self.players[player.id] = player
                logger.info(f"Player {player.id} added at position ({x}, {y}) with color {player.color}")
                return True
            
            logger.debug(f"Cannot add player {player.id}: no available starting position")
            return False
        except Exception as e:
            logger.error(f"Error adding player {player.id}: {e}", exc_info=True)
            return False
    
    def remove_player(self, player_id: str) -> None:
        """Remove a player from the game"""
        try:
            if player_id in self.players:
                logger.info(f"Player {player_id} removed from game")
                del self.players[player_id]
            else:
                logger.debug(f"Player {player_id} not found, cannot remove")
        except Exception as e:
            logger.error(f"Error removing player {player_id}: {e}", exc_info=True)
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID"""
        try:
            player = self.players.get(player_id)
            if player is None:
                logger.debug(f"Player {player_id} not found")
            return player
        except Exception as e:
            logger.error(f"Error getting player {player_id}: {e}", exc_info=True)
            return None
    
    def create_enemies(self) -> None:
        """Create enemies for the current level"""
        try:
            num_enemies: int = 3 + self.level
            self.enemies = []
            enemy_types = list(EnemyType)
            enemies_created = 0

            for _ in range(num_enemies):
                valid_position: bool = False
                attempts = 0
                while not valid_position and attempts < 50:  # Limit attempts to prevent infinite loop
                    attempts += 1
                    x: int = random.randint(1, self.width - 2)
                    y: int = random.randint(1, self.height - 2)

                    # Ensure enemy is not on walls or blocks and not too close to players
                    if self.map.get_cell_type(x, y) == 0:
                        # Check distance to all players
                        too_close: bool = False
                        for player in self.players.values():
                            player_grid_x: int = int(player.x / self.cell_size)
                            player_grid_y: int = int(player.y / self.cell_size)
                            dist: float = math.sqrt((x - player_grid_x)**2 + (y - player_grid_y)**2)
                            if dist < 3:  # Must be at least 3 cells away from players
                                too_close = True
                                break

                        if not too_close:
                            valid_position = True
                            speed: float = 1 + random.random() * 0.5
                            # Choose a random enemy type
                            chosen_type: EnemyType = random.choice(enemy_types)
                            self.enemies.append(
                                Enemy(
                                    x=x * self.cell_size,
                                    y=y * self.cell_size,
                                    size=self.cell_size,
                                    speed=speed,
                                    enemy_type=chosen_type  # Assign the chosen type
                                )
                            )
                            enemies_created += 1
                            logger.debug(f"Created enemy of type {chosen_type.value} at position ({x}, {y}) with speed {speed:.2f}")
            
            logger.info(f"Level {self.level}: Created {enemies_created} enemies")
        except Exception as e:
            logger.error(f"Error creating enemies for level {self.level}: {e}", exc_info=True)

    def update(self) -> Dict[str, Any]:
        """Update game state and return the new state"""
        try:
            # Calculate delta time
            current_time: float = time.time()
            delta_time: float = current_time - self.last_update_time
            self.last_update_time = current_time
            
            # Skip update if game is over
            if self.game_over:
                logger.debug("Game is over, skipping update")
                return self.get_state()
            
            # Update players
            logger.debug(f"Updating {len(self.players)} players")
            for player in list(self.players.values()):
                self.update_player(player, delta_time)
            
            # Update enemies
            logger.debug(f"Updating {len(self.enemies)} enemies")
            for enemy in list(self.enemies):
                self.update_enemy(enemy, delta_time)
            
            # Update bombs
            logger.debug(f"Updating {len(self.bombs)} bombs")
            for bomb in list(self.bombs.values()):
                self.update_bomb(bomb, delta_time)
            
            # Check if level is complete (all enemies defeated)
            if len(self.enemies) == 0:
                logger.info(f"Level {self.level} completed, advancing to next level")
                self.level_complete()
            
            return self.get_state()
        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            # Return the current state on error
            return self.get_state()
    
    def update_player(self, player: Player, delta_time: float) -> None:
        """Update a single player"""
        try:
            if player.lives <= 0:
                logger.debug(f"Player {player.id} has no lives left, skipping update")
                return

            player.update(delta_time=delta_time)
            
            # Handle player movement
            dx: float = 0
            dy: float = 0
            if player.inputs.get('up'):
                dy -= player.speed
            if player.inputs.get('down'):
                dy += player.speed
            if player.inputs.get('left'):
                dx -= player.speed
            if player.inputs.get('right'):
                dx += player.speed
            
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                normalize: float = 1 / math.sqrt(2)
                dx *= normalize
                dy *= normalize
            
            # Apply delta time
            dx *= delta_time * 60
            dy *= delta_time * 60
            
            # Move with collision detection (X axis)
            if dx != 0:
                new_x: float = player.x + dx
                if not self.check_collision(
                        x=new_x,
                        y=player.y,
                        width=player.width,
                        height=player.height,
                        entity=player,
                        ignore_entity=player
                ):
                    player.x = new_x
                    logger.debug(f"Player {player.id} moved to x={player.x:.2f}")
                else:
                    logger.debug(f"Player {player.id} blocked on X axis")
            
            # Move with collision detection (Y axis)
            if dy != 0:
                new_y: float = player.y + dy
                if not self.check_collision(
                        x=player.x,
                        y=new_y,
                        width=player.width,
                        height=player.height,
                        entity=player,
                        ignore_entity=player
                ):
                    player.y = new_y
                    logger.debug(f"Player {player.id} moved to y={player.y:.2f}")
                else:
                    logger.debug(f"Player {player.id} blocked on Y axis")
            
            # Check collision with power-ups
            for power_up in list(self.power_ups.values()):
                if self.check_entity_collision(player, power_up):
                    logger.info(f"Player {player.id} collected powerup {power_up.type.name}")
                    self.apply_power_up(player, power_up)
                    self.power_ups.pop(power_up.id)
            
            # Check collision with enemies
            if not player.invulnerable:
                for enemy in self.enemies:
                    if not enemy.destroyed and self.check_entity_collision(player, enemy):
                        logger.info(f"Player {player.id} hit by enemy {enemy.type.value}")
                        self.handle_player_hit(player)
        except Exception as e:
            logger.error(f"Error updating player {player.id}: {e}", exc_info=True)

    def update_enemy(self, enemy: Enemy, delta_time: float) -> None:
        """Update a single enemy"""
        try:
            if enemy.destroyed:
                enemy.destroy_animation_timer += delta_time
                if enemy.destroy_animation_timer >= 0.5:  # Animation duration
                    logger.debug(f"Enemy {enemy.id} ({enemy.type.value}) destroy animation finished, removing")
                    self.enemies.remove(enemy)
                return

            enemy.update(delta_time=delta_time)
            
            # Update movement timer
            enemy.move_timer += delta_time
            
            # Change direction periodically or when hitting a wall
            if enemy.move_timer >= enemy.change_direction_interval:
                enemy.direction = enemy.get_random_direction()
                enemy.move_timer = 0
                logger.debug(f"Enemy {enemy.id} changed direction to {enemy.direction}")
            
            # Calculate new position
            dx: float = enemy.direction[0] * enemy.speed * delta_time * 60
            dy: float = enemy.direction[1] * enemy.speed * delta_time * 60
            
            # Try to move in the current direction
            new_x: float = enemy.x + dx
            new_y: float = enemy.y + dy
            
            # If there's a collision, try a different direction
            if self.check_collision(
                    x=new_x,
                    y=new_y,
                    width=enemy.width,
                    height=enemy.height,
                    entity=enemy,
                    ignore_entity=None
            ):
                logger.debug(f"Enemy {enemy.id} collision detected, changing direction")
                enemy.direction = enemy.get_random_direction()
            else:
                enemy.x = new_x
                enemy.y = new_y
        except Exception as e:
            logger.error(f"Error updating enemy {enemy.id}: {e}", exc_info=True)
    
    def update_bomb(self, bomb: Bomb, delta_time: float) -> None:
        """Update a single bomb"""
        try:
            if bomb.exploded:
                bomb.explosion_timer += delta_time
                if bomb.explosion_timer >= 0.5:  # Explosion duration
                    logger.debug(f"Bomb {bomb.id} explosion finished, removing")
                    self.bombs.pop(bomb.id)
            else:
                bomb.timer += delta_time
                if bomb.timer >= 2:  # 2 seconds before explosion
                    logger.info(f"Bomb {bomb.id} exploded!")
                    self.handle_explosion(bomb)
        except Exception as e:
            logger.error(f"Error updating bomb {bomb.id}: {e}", exc_info=True)
    
    def handle_explosion(self, bomb: Bomb) -> None:
        """Handle bomb explosion logic"""
        try:
            bomb.exploded = True
            bomb.explosion_cells = []
            
            # Get grid coordinates for the bomb
            grid_x: int = int((bomb.x + bomb.width/2) / self.cell_size)
            grid_y: int = int((bomb.y + bomb.height/2) / self.cell_size)
            
            # Add center of explosion
            bomb.explosion_cells.append((grid_x, grid_y))
            
            # Check in each of the four directions
            directions: List[Tuple[int, int]] = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            
            logger.debug(f"Bomb at ({grid_x}, {grid_y}) exploded with power {bomb.power}")
            
            for dx, dy in directions:
                for i in range(1, bomb.power + 1):
                    check_x: int = grid_x + dx * i
                    check_y: int = grid_y + dy * i
                    
                    # Stop if we hit a wall
                    if self.map.is_wall(check_x, check_y):
                        logger.debug(f"Explosion stopped by wall at ({check_x}, {check_y})")
                        break
                    
                    bomb.explosion_cells.append((check_x, check_y))
                    
                    # If we hit a breakable block, destroy it and stop the explosion in this direction
                    if self.map.is_breakable_block(check_x, check_y):
                        self.map.destroy_block(check_x, check_y)
                        self.score += 10
                        logger.info(f"Block destroyed at ({check_x}, {check_y}), score +10")
                        
                        # Chance to spawn power-up when a block is destroyed
                        if random.random() < 0.2:  # 20% chance
                            logger.info(f"Power-up spawned at ({check_x}, {check_y})")
                            self.spawn_power_up(check_x * self.cell_size, check_y * self.cell_size)
                        
                        break
            
            # Check collision with players
            for player in list(self.players.values()):
                if not player.invulnerable and self.check_explosion_collision(bomb, player):
                    logger.info(f"Player {player.id} hit by bomb explosion")
                    self.handle_player_hit(player)

            # Check if explosion hits enemies
            for enemy in list(self.enemies):
                if not enemy.destroyed and not enemy.invulnerable and self.check_explosion_collision(bomb, enemy):
                    logger.info(f"Enemy {enemy.id} hit by bomb explosion")
                    self.handle_enemy_hit(enemy)

            # Check collision with other bombs, triggering chain reactions
            for other_bomb in self.bombs.values():
                if other_bomb != bomb and not other_bomb.exploded:
                    if self.check_explosion_collision(bomb, other_bomb):
                        logger.info(f"Chain reaction: bomb {other_bomb.id} triggered by bomb {bomb.id}")
                        self.handle_explosion(other_bomb)
        except Exception as e:
            logger.error(f"Error handling bomb explosion: {e}", exc_info=True)


    def handle_enemy_hit(self, enemy):
        """Handle enemy being hit by explosion"""
        try:
            if enemy.invulnerable:
                logger.debug(f"Enemy {enemy.id} is invulnerable, no damage taken")
                return

            enemy.lives -= 1  # Decrease lives
            logger.info(f"Enemy {enemy.id} ({enemy.type.value}) hit, lives left: {enemy.lives}")
            
            if enemy.lives > 0:
                # Make enemy invulnerable for a short time
                enemy.invulnerable = True
                enemy.invulnerable_timer = 2
                logger.debug(f"Enemy {enemy.id} is now invulnerable for 2 seconds")
            else:
                enemy.destroyed = True
                enemy.destroy_animation_timer = 0
                self.score += 100
                logger.info(f"Enemy {enemy.id} destroyed, score +100")

                # Chance to spawn powerup
                if random.random() < 0.3:  # 30% chance
                    logger.info(f"Power-up spawned at enemy location ({enemy.x/self.cell_size:.1f}, {enemy.y/self.cell_size:.1f})")
                    self.spawn_power_up(enemy.x, enemy.y)
        except Exception as e:
            logger.error(f"Error handling enemy hit: {e}", exc_info=True)


    def check_collision(
            self,
            x: float,
            y: float,
            width: int,
            height: int,
            entity: Player | Enemy,
            ignore_entity=None,
    ) -> bool:
        """
        Check if an entity at (x, y) with the given width and height would collide with any walls,
        blocks, or other entities.
        """
        try:
            # Calculate grid cells that the entity overlaps with
            grid_left: int = int(x / self.cell_size)
            grid_right: int = int((x + width - 1) / self.cell_size)
            grid_top: int = int(y / self.cell_size)
            grid_bottom: int = int((y + height - 1) / self.cell_size)
            
            # Check collision with map cells
            for grid_y in range(grid_top, grid_bottom + 1):
                for grid_x in range(grid_left, grid_right + 1):
                    if self.map.is_solid(grid_x, grid_y):
                        logger.debug(f"Collision detected with solid map cell at ({grid_x}, {grid_y})")
                        return True
            
            # Check collision with bombs (we don't walk through bombs)
            for bomb in self.bombs.values():
                if not bomb.exploded and bomb != ignore_entity and bomb.owner_id != entity.id:
                    bomb_grid_x: int = int((bomb.x + bomb.width/2) / self.cell_size)
                    bomb_grid_y: int = int((bomb.y + bomb.height/2) / self.cell_size)
                    
                    if (bomb_grid_x >= grid_left and bomb_grid_x <= grid_right and
                        bomb_grid_y >= grid_top and bomb_grid_y <= grid_bottom):
                        logger.debug(f"Collision detected with bomb at ({bomb_grid_x}, {bomb_grid_y})")
                        return True

            return False
        except Exception as e:
            logger.error(f"Error checking collision at ({x}, {y}): {e}", exc_info=True)
            # Return True on error to prevent movement
            return True


    def check_entity_collision(self, entity1: Any, entity2: Any) -> bool:
        """Check if two entities collide using simple rectangle collision detection"""
        try:
            collision = (entity1.x < entity2.x + entity2.width and
                    entity1.x + entity1.width > entity2.x and
                    entity1.y < entity2.y + entity2.height and
                    entity1.y + entity1.height > entity2.y)
            
            if collision:
                logger.debug(f"Entity collision between {entity1.name} and {entity2.name}")
            
            return collision
        except Exception as e:
            logger.error(f"Error checking entity collision: {e}", exc_info=True)
            return False


    def check_explosion_collision(self, bomb: Bomb, entity: Any) -> bool:
        """Check if an entity is within the explosion radius of a bomb"""
        try:
            entity_grid_x: int = int((entity.x + entity.width/2) / self.cell_size)
            entity_grid_y: int = int((entity.y + entity.height/2) / self.cell_size)
            
            for cell_x, cell_y in bomb.explosion_cells:
                if entity_grid_x == cell_x and entity_grid_y == cell_y:
                    logger.debug(f"Explosion collision detected with {entity.name} at grid ({entity_grid_x}, {entity_grid_y})")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking explosion collision: {e}", exc_info=True)
            return False
    
    def get_random_direction(self) -> Tuple[float, float]:
        """Get a random direction vector"""
        try:
            choices: List[Tuple[int, int]] = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            direction = random.choice(choices)
            logger.debug(f"Random direction selected: {direction}")
            return direction
        except Exception as e:
            logger.error(f"Error getting random direction: {e}", exc_info=True)
            return (1, 0)  # Default direction
    
    def handle_player_hit(self, player: Player) -> None:
        """Handle player being hit by explosion or enemy"""
        try:
            if player.invulnerable:
                logger.debug(f"Player {player.id} is invulnerable, no damage taken")
                return
            
            player.lives -= 1
            logger.info(f"Player {player.id} was hit, lives left: {player.lives}")
            
            if player.lives > 0:
                # Make player invulnerable for a short time
                player.invulnerable = True
                player.invulnerable_timer = 2
                logger.debug(f"Player {player.id} is now invulnerable for 2 seconds")
            else:
                logger.info(f"Player {player.id} has been eliminated")
                # Check if game is over (all players dead)
                alive_players = [p for p in self.players.values() if p.lives > 0]
                if not alive_players:
                    logger.info("Game over: all players eliminated")
                    self.game_over = True
        except Exception as e:
            logger.error(f"Error handling player hit for player {player.id}: {e}", exc_info=True)
    
    def spawn_power_up(self, x: float, y: float) -> None:
        """Spawn a random power-up at the given position"""
        try:
            power_type: PowerUpType = random.choice(list(PowerUpType))
            power_up = PowerUp(x, y, self.cell_size, power_type)
            self.power_ups[power_up.id] = power_up
            logger.info(f"Power-up {power_type.name} spawned at ({x/self.cell_size:.1f}, {y/self.cell_size:.1f})")
        except Exception as e:
            logger.error(f"Error spawning power-up at ({x}, {y}): {e}", exc_info=True)
    
    def apply_power_up(self, player: Player, power_up: PowerUp) -> None:
        """Apply a power-up to a player"""
        try:
            power_up.apply_to_player(player)
            
            # Award points for collecting power-ups
            self.score += 25
            logger.info(f"Applied power-up {power_up.type.name} to player {player.id}, score +25, total score: {self.score}")
        except Exception as e:
            logger.error(f"Error applying power-up {power_up.type.name} to player {player.id}: {e}", exc_info=True)
    
    def place_bomb(self, player: Player) -> bool:
        """
        Place a bomb at the player's position.
        Returns True if bomb was placed, False otherwise.
        """
        try:
            # Count how many bombs this player already has active
            active_bombs: int = 0
            for bomb in self.bombs.values():
                if bomb.owner_id == player.id and not bomb.exploded:
                    active_bombs += 1
            
            # Don't allow more than max_bombs
            if active_bombs >= player.max_bombs:
                logger.debug(f"Player {player.id} cannot place bomb: already has {active_bombs}/{player.max_bombs} active bombs")
                return False
            
            # Get the grid cell the player is mostly in
            grid_x: int = int((player.x + player.width/2) / self.cell_size)
            grid_y: int = int((player.y + player.height/2) / self.cell_size)
            
            # Calculate exact position for the bomb
            bomb_x: float = grid_x * self.cell_size
            bomb_y: float = grid_y * self.cell_size
            
            # Check if there's already a bomb here
            for bomb in self.bombs.values():
                bomb_grid_x: int = int((bomb.x + bomb.width/2) / self.cell_size)
                bomb_grid_y: int = int((bomb.y + bomb.height/2) / self.cell_size)
                
                if bomb_grid_x == grid_x and bomb_grid_y == grid_y:
                    logger.debug(f"Player {player.id} cannot place bomb: position ({grid_x}, {grid_y}) already has a bomb")
                    return False
            
            # Create and add the bomb
            bomb: Bomb = Bomb(
                x=bomb_x,
                y=bomb_y,
                size=self.cell_size,
                power=player.bomb_power,
                owner_id=player.id
            )
            self.bombs[bomb.id] = bomb
            logger.info(f"Player {player.id} placed bomb at ({grid_x}, {grid_y}) with power {player.bomb_power}")
            return True
        except Exception as e:
            logger.error(f"Error placing bomb for player {player.id}: {e}", exc_info=True)
            return False
    
    def level_complete(self) -> None:
        """Handle level completion logic"""
        try:
            self.level += 1
            # Bonus score for completing level
            self.score += 500
            logger.info(f"Level {self.level-1} completed! Score +500, advancing to level {self.level}")
            
            # Reset map for next level
            self.map.generate_map()
            
            # Create new enemies
            self.create_enemies()
            
            # Clear bombs and power-ups
            bombs_count = len(self.bombs)
            powerups_count = len(self.power_ups)
            self.bombs = {}
            self.power_ups = {}
            logger.debug(f"Cleared {bombs_count} bombs and {powerups_count} power-ups")
            
            # Reset player positions
            start_positions: List[Tuple[int, int]] = [
                (1, 1),                                # Top-left
                (self.width - 2, 1),                   # Top-right
                (1, self.height - 2),                  # Bottom-left
                (self.width - 2, self.height - 2)      # Bottom-right
            ]
            
            for i, player in enumerate(self.players.values()):
                if i < len(start_positions):
                    x, y = start_positions[i]
                    player.x = x * self.cell_size
                    player.y = y * self.cell_size
                    logger.debug(f"Reset player {player.id} position to ({x}, {y})")
        except Exception as e:
            logger.error(f"Error handling level completion: {e}", exc_info=True)
    
    def is_active(self) -> bool:
        """Check if the game is still active (not over)"""
        try:
            is_active = not self.game_over and len(self.players) > 0
            if not is_active:
                #check if timeout inactive game is not over
                if time.time() - self.timer_is_alive < settings.GAME_OVER_TIMEOUT:
                    is_active = True
                    logger.debug("Game inactive time is not expired yet.")
                else:
                    if self.game_over:
                        logger.info("Game is not active: game over flag is set")
                    else:
                        logger.info("Game is not active: no players remaining")
            else:
                self.timer_is_alive = time.time()
            return is_active
        except Exception as e:
            logger.error(f"Error checking if game is active: {e}", exc_info=True)
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get the full game state to send to clients"""
        try:
            # Подготавливаем данные карты - только изменения
            map_data = {
                'width': self.map.width,
                'height': self.map.height,
                'changedCells': self.map.get_changes(),
                'cellSize': self.cell_size
            }
            
            # Подготавливаем данные игроков
            players_data: Dict[str, Dict[str, Any]] = {}
            for player_id, player in self.players.items():
                players_data[player_id] = {
                    'x': player.x,
                    'y': player.y,
                    'width': player.width,
                    'height': player.height,
                    'lives': player.lives,
                    'maxBombs': player.max_bombs,
                    'bombPower': player.bomb_power,
                    'invulnerable': player.invulnerable,
                    'color': player.color
                }

            # Подготавливаем данные врагов
            enemies_data: List[Dict[str, Any]] = []
            for enemy in self.enemies:
                enemies_data.append({
                    'x': enemy.x,
                    'y': enemy.y,
                    'width': enemy.width,
                    'height': enemy.height,
                    'type': enemy.type.value,
                    'lives': enemy.lives,
                    'invulnerable': enemy.invulnerable,
                    'destroyed': enemy.destroyed
                })

            # Подготавливаем данные бомб
            bombs_data: List[Dict[str, Any]] = []
            for bomb in self.bombs.values():
                explosion_cells: List[Dict[str, float]] = []
                if bomb.exploded:
                    for x, y in bomb.explosion_cells:
                        explosion_cells.append({
                            'x': (x * self.cell_size),
                            'y': (y * self.cell_size)
                        })
                bombs_data.append({
                    'x': bomb.x,
                    'y': bomb.y,
                    'width': bomb.width,
                    'height': bomb.height,
                    'exploded': bomb.exploded,
                    'explosionCells': explosion_cells,
                    'ownerId': bomb.owner_id
                })

            # Подготавливаем данные усилений
            power_ups_data = [
                {
                    'x': power_up.x,
                    'y': power_up.y,
                    'width': power_up.width,
                    'height': power_up.height,
                    'type': power_up.type.value
                }
                for power_up in self.power_ups.values()
            ]

            state = {
                'players': players_data,
                'enemies': enemies_data,
                'bombs': bombs_data,
                'powerUps': power_ups_data,
                'map': map_data,
                'score': self.score,
                'level': self.level,
                'gameOver': self.game_over
            }
            
            logger.debug(f"Game state prepared: {len(players_data)} players, {len(enemies_data)} enemies, {len(bombs_data)} bombs, {len(power_ups_data)} power-ups")
            return state
        except Exception as e:
            logger.error(f"Error getting game state: {e}", exc_info=True)
            # Return minimal state in case of error
            return {
                'error': True,
                'players': {},
                'enemies': [],
                'bombs': [],
                'powerUps': [],
                'map': {'width': self.width, 'height': self.height, 'changedCells': [], 'cellSize': self.cell_size},
                'score': self.score,
                'level': self.level,
                'gameOver': True
            } 
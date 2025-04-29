import time
import random
import math
from typing import Dict, List, Tuple, Optional, Any, Union

from .map import Map
from .player import Player
from .enemy import Enemy
from .bomb import Bomb
from .power_up import PowerUp, PowerUpType

class Game:
    def __init__(self):
        # Game settings
        self.cell_size: int = 40
        self.width: int = 15
        self.height: int = 13
        
        # Game state
        self.players: Dict[str, Player] = {}  # Dictionary of player_id -> Player
        self.enemies: List[Enemy] = []
        self.bombs: List[Bomb] = []
        self.power_ups: List[PowerUp] = []
        self.map: Map = Map(self.width, self.height)
        self.score: int = 0
        self.level: int = 1
        self.game_over: bool = False
        self.last_update_time: float = time.time()
        
        # Initialize game
        self.map.generate_map()
        self.create_enemies()

    def add_player(self, player: Player) -> bool:
        """Add a player to the game"""
        if len(self.players) >= 4:  # Max 4 players
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
            return True
        
        return False
    
    def remove_player(self, player_id: str) -> None:
        """Remove a player from the game"""
        if player_id in self.players:
            del self.players[player_id]
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID"""
        return self.players.get(player_id)
    
    def create_enemies(self) -> None:
        """Create enemies for the current level"""
        num_enemies: int = 3 + self.level
        self.enemies = []
        
        for _ in range(num_enemies):
            valid_position: bool = False
            while not valid_position:
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
                        self.enemies.append(Enemy(x * self.cell_size, y * self.cell_size, 
                                                  self.cell_size, speed))
    
    def update(self) -> Dict[str, Any]:
        """Update game state and return the new state"""
        # Calculate delta time
        current_time: float = time.time()
        delta_time: float = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Skip update if game is over
        if self.game_over:
            return self.get_state()
        
        # Update players
        for player in list(self.players.values()):
            self.update_player(player, delta_time)
        
        # Update enemies
        for enemy in list(self.enemies):
            self.update_enemy(enemy, delta_time)
        
        # Update bombs
        for bomb in list(self.bombs):
            self.update_bomb(bomb, delta_time)
        
        # Check if level is complete (all enemies defeated)
        if len(self.enemies) == 0:
            self.level_complete()
        
        return self.get_state()
    
    def update_player(self, player: Player, delta_time: float) -> None:
        """Update a single player"""
        if player.lives <= 0:
            return
        
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
            if not self.check_collision(new_x, player.y, player.width, player.height, player):
                player.x = new_x
        
        # Move with collision detection (Y axis)
        if dy != 0:
            new_y: float = player.y + dy
            if not self.check_collision(player.x, new_y, player.width, player.height, player):
                player.y = new_y
        
        # Check collision with power-ups
        for power_up in list(self.power_ups):
            if self.check_entity_collision(player, power_up):
                self.apply_power_up(player, power_up)
                self.power_ups.remove(power_up)
        
        # Check collision with enemies
        if not player.invulnerable:
            for enemy in self.enemies:
                if not enemy.destroyed and self.check_entity_collision(player, enemy):
                    self.handle_player_hit(player)
        
        # Update invulnerability
        if player.invulnerable:
            player.invulnerable_timer += delta_time
            if player.invulnerable_timer >= 2:  # 2 seconds of invulnerability
                player.invulnerable = False
                player.invulnerable_timer = 0
    
    def update_enemy(self, enemy: Enemy, delta_time: float) -> None:
        """Update a single enemy"""
        if enemy.destroyed:
            enemy.destroy_animation_timer += delta_time
            if enemy.destroy_animation_timer >= 0.5:  # Animation duration
                self.enemies.remove(enemy)
            return
        
        # Update movement timer
        enemy.move_timer += delta_time
        
        # Change direction periodically or when hitting a wall
        if enemy.move_timer >= enemy.change_direction_interval:
            enemy.direction = self.get_random_direction()
            enemy.move_timer = 0
        
        # Calculate new position
        dx: float = enemy.direction[0] * enemy.speed * delta_time * 60
        dy: float = enemy.direction[1] * enemy.speed * delta_time * 60
        
        # Try to move in the current direction
        new_x: float = enemy.x + dx
        new_y: float = enemy.y + dy
        
        # If there's a collision, try a different direction
        if self.check_collision(new_x, new_y, enemy.width, enemy.height):
            enemy.direction = self.get_random_direction()
        else:
            enemy.x = new_x
            enemy.y = new_y
        
        # Check collision with bombs (explosions)
        for bomb in self.bombs:
            if bomb.exploded and self.check_explosion_collision(bomb, enemy):
                enemy.destroyed = True
                self.score += 100
                
                # Chance to spawn power-up when an enemy is destroyed
                if random.random() < 0.3:  # 30% chance
                    self.spawn_power_up(enemy.x, enemy.y)
                
                break
    
    def update_bomb(self, bomb: Bomb, delta_time: float) -> None:
        """Update a single bomb"""
        if bomb.exploded:
            bomb.explosion_timer += delta_time
            if bomb.explosion_timer >= 0.5:  # Explosion duration
                self.bombs.remove(bomb)
        else:
            bomb.timer += delta_time
            if bomb.timer >= 2:  # 2 seconds before explosion
                self.handle_explosion(bomb)
    
    def handle_explosion(self, bomb: Bomb) -> None:
        """Handle bomb explosion logic"""
        bomb.exploded = True
        bomb.explosion_cells = []
        
        # Get grid coordinates for the bomb
        grid_x: int = int((bomb.x + bomb.width/2) / self.cell_size)
        grid_y: int = int((bomb.y + bomb.height/2) / self.cell_size)
        
        # Add center of explosion
        bomb.explosion_cells.append((grid_x, grid_y))
        
        # Check in each of the four directions
        directions: List[Tuple[int, int]] = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        
        for dx, dy in directions:
            for i in range(1, bomb.power + 1):
                check_x: int = grid_x + dx * i
                check_y: int = grid_y + dy * i
                
                # Stop if we hit a wall
                if self.map.is_wall(check_x, check_y):
                    break
                
                bomb.explosion_cells.append((check_x, check_y))
                
                # If we hit a breakable block, destroy it and stop the explosion in this direction
                if self.map.is_breakable_block(check_x, check_y):
                    self.map.destroy_block(check_x, check_y)
                    self.score += 10
                    
                    # Chance to spawn power-up when a block is destroyed
                    if random.random() < 0.2:  # 20% chance
                        self.spawn_power_up(check_x * self.cell_size, check_y * self.cell_size)
                    
                    break
        
        # Check collision with players
        for player in list(self.players.values()):
            if not player.invulnerable and self.check_explosion_collision(bomb, player):
                self.handle_player_hit(player)
        
        # Check collision with enemies
        for enemy in list(self.enemies):
            if not enemy.destroyed and self.check_explosion_collision(bomb, enemy):
                enemy.destroyed = True
                self.score += 100
                
                # Chance to spawn power-up when an enemy is destroyed
                if random.random() < 0.3:  # 30% chance
                    self.spawn_power_up(enemy.x, enemy.y)
        
        # Check collision with other bombs, triggering chain reactions
        for other_bomb in self.bombs:
            if other_bomb != bomb and not other_bomb.exploded:
                if self.check_explosion_collision(bomb, other_bomb):
                    self.handle_explosion(other_bomb)
    
    def check_collision(self, x: float, y: float, width: int, height: int, ignore_entity=None) -> bool:
        """
        Check if an entity at (x, y) with the given width and height would collide with any walls,
        blocks, or other entities.
        """
        # Calculate grid cells that the entity overlaps with
        grid_left: int = int(x / self.cell_size)
        grid_right: int = int((x + width - 1) / self.cell_size)
        grid_top: int = int(y / self.cell_size)
        grid_bottom: int = int((y + height - 1) / self.cell_size)
        
        # Check collision with map cells
        for grid_y in range(grid_top, grid_bottom + 1):
            for grid_x in range(grid_left, grid_right + 1):
                if self.map.is_solid(grid_x, grid_y):
                    return True
        
        # Check collision with bombs (we don't walk through bombs)
        for bomb in self.bombs:
            if not bomb.exploded and bomb != ignore_entity:
                bomb_grid_x: int = int((bomb.x + bomb.width/2) / self.cell_size)
                bomb_grid_y: int = int((bomb.y + bomb.height/2) / self.cell_size)
                
                if (bomb_grid_x >= grid_left and bomb_grid_x <= grid_right and
                    bomb_grid_y >= grid_top and bomb_grid_y <= grid_bottom):
                    return True
        
        return False
    
    def check_entity_collision(self, entity1: Any, entity2: Any) -> bool:
        """Check if two entities collide using simple rectangle collision detection"""
        return (entity1.x < entity2.x + entity2.width and
                entity1.x + entity1.width > entity2.x and
                entity1.y < entity2.y + entity2.height and
                entity1.y + entity1.height > entity2.y)
    
    def check_explosion_collision(self, bomb: Bomb, entity: Any) -> bool:
        """Check if an entity is within the explosion radius of a bomb"""
        entity_grid_x: int = int((entity.x + entity.width/2) / self.cell_size)
        entity_grid_y: int = int((entity.y + entity.height/2) / self.cell_size)
        
        for cell_x, cell_y in bomb.explosion_cells:
            if entity_grid_x == cell_x and entity_grid_y == cell_y:
                return True
        
        return False
    
    def get_random_direction(self) -> Tuple[float, float]:
        """Get a random direction vector"""
        choices: List[Tuple[int, int]] = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        return random.choice(choices)
    
    def handle_player_hit(self, player: Player) -> None:
        """Handle player being hit by explosion or enemy"""
        if player.invulnerable:
            return
        
        player.lives -= 1
        
        if player.lives > 0:
            # Make player invulnerable for a short time
            player.invulnerable = True
            player.invulnerable_timer = 0
        else:
            # Check if game is over (all players dead)
            all_dead: bool = True
            for p in self.players.values():
                if p.lives > 0:
                    all_dead = False
                    break
            
            if all_dead:
                self.game_over = True
    
    def spawn_power_up(self, x: float, y: float) -> None:
        """Spawn a random power-up at the given position"""
        power_type: PowerUpType = random.choice(list(PowerUpType))
        self.power_ups.append(PowerUp(x, y, self.cell_size * 0.6, power_type))
    
    def apply_power_up(self, player: Player, power_up: PowerUp) -> None:
        """Apply a power-up to a player"""
        power_up.apply_to_player(player)
        
        # Award points for collecting power-ups
        self.score += 25
    
    def place_bomb(self, player: Player) -> bool:
        """
        Place a bomb at the player's position.
        Returns True if bomb was placed, False otherwise.
        """
        # Count how many bombs this player already has active
        active_bombs: int = 0
        for bomb in self.bombs:
            if bomb.owner_id == player.id and not bomb.exploded:
                active_bombs += 1
        
        # Don't allow more than max_bombs
        if active_bombs >= player.max_bombs:
            return False
        
        # Get the grid cell the player is mostly in
        grid_x: int = int((player.x + player.width/2) / self.cell_size)
        grid_y: int = int((player.y + player.height/2) / self.cell_size)
        
        # Calculate exact position for the bomb
        bomb_x: float = grid_x * self.cell_size
        bomb_y: float = grid_y * self.cell_size
        
        # Check if there's already a bomb here
        for bomb in self.bombs:
            bomb_grid_x: int = int((bomb.x + bomb.width/2) / self.cell_size)
            bomb_grid_y: int = int((bomb.y + bomb.height/2) / self.cell_size)
            
            if bomb_grid_x == grid_x and bomb_grid_y == grid_y:
                return False
        
        # Create and add the bomb
        bomb: Bomb = Bomb(bomb_x, bomb_y, self.cell_size * 0.8, player.bomb_power, player.id)
        self.bombs.append(bomb)
        
        return True
    
    def level_complete(self) -> None:
        """Handle level completion logic"""
        self.level += 1
        
        # Reset map for next level
        self.map.generate_map()
        
        # Create new enemies
        self.create_enemies()
        
        # Clear bombs and power-ups
        self.bombs = []
        self.power_ups = []
        
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
        
        # Bonus score for completing level
        self.score += 500
    
    def is_active(self) -> bool:
        """Check if the game is still active (not over)"""
        return not self.game_over
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current game state to send to clients"""
        player_states: dict = {}
        for player_id, player in self.players.items():
            player_states[player_id] = {
                # 'id': player.id,
                'x': player.x,
                'y': player.y,
                'width': player.width,
                'height': player.height,
                'color': player.color,
                'lives': player.lives,
                'max_bombs': player.max_bombs,
                'bomb_power': player.bomb_power,
                'invulnerable': player.invulnerable
            }
        
        enemy_states: List[Dict[str, Any]] = []
        for enemy in self.enemies:
            if not enemy.destroyed:
                enemy_states.append({
                    'x': enemy.x,
                    'y': enemy.y,
                    'width': enemy.width,
                    'height': enemy.height,
                    'destroyed': enemy.destroyed
                })
        
        bomb_states: List[Dict[str, Any]] = []
        for bomb in self.bombs:
            explosion_cells = []
            if bomb.exploded:
                for x, y in bomb.explosion_cells:
                    explosion_cells.append({
                        'x': x * self.cell_size,
                        'y': y * self.cell_size
                    })

            bomb_data: Dict[str, Any] = {
                'x': bomb.x,
                'y': bomb.y,
                'width': bomb.width,
                'height': bomb.height,
                'exploded': bomb.exploded,
                'explosionCells': explosion_cells,
                'ownerId': bomb.owner_id
            }
            

            
            bomb_states.append(bomb_data)
        
        power_up_states: List[Dict[str, Any]] = []
        for power_up in self.power_ups:
            power_up_states.append({
                'x': power_up.x,
                'y': power_up.y,
                'width': power_up.width,
                'height': power_up.height,
                'type': power_up.type.value
            })

        map_data = {
            'width': self.width,
            'height': self.height,
            'cellSize': self.cell_size,
            'grid': self.map.grid
        }

        return {
            'players': player_states,
            'enemies': enemy_states,
            'bombs': bomb_states,
            'power_ups': power_up_states,
            'map': map_data,
            'score': self.score,
            'level': self.level,
            'game_over': self.game_over
        } 
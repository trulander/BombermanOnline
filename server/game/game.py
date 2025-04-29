import time
from .map import Map
from .player import Player
from .enemy import Enemy
from .bomb import Bomb
from .power_up import PowerUp, PowerUpType
import random
import math

class Game:
    def __init__(self):
        # Game settings
        self.cell_size = 40
        self.width = 15
        self.height = 13
        
        # Game state
        self.players = {}  # Dictionary of player_id -> Player
        self.enemies = []
        self.bombs = []
        self.power_ups = []
        self.map = Map(self.width, self.height)
        self.score = 0
        self.level = 1
        self.game_over = False
        self.last_update_time = time.time()
        
        # Initialize game
        self.map.generate_map()
        self.create_enemies()

    def add_player(self, player):
        """Add a player to the game"""
        if len(self.players) >= 4:  # Max 4 players
            return False
        
        # Set player position at a valid starting point
        start_positions = [
            (1, 1),                                # Top-left
            (self.width - 2, 1),                   # Top-right
            (1, self.height - 2),                  # Bottom-left
            (self.width - 2, self.height - 2)      # Bottom-right
        ]
        
        # Assign next available position
        player_idx = len(self.players)
        if player_idx < len(start_positions):
            x, y = start_positions[player_idx]
            player.x = x * self.cell_size
            player.y = y * self.cell_size
            player.color = player.COLORS[player_idx]
            
            self.players[player.id] = player
            return True
        
        return False
    
    def remove_player(self, player_id):
        """Remove a player from the game"""
        if player_id in self.players:
            del self.players[player_id]
    
    def get_player(self, player_id):
        """Get a player by ID"""
        return self.players.get(player_id)
    
    def create_enemies(self):
        """Create enemies for the current level"""
        num_enemies = 3 + self.level
        self.enemies = []
        
        for _ in range(num_enemies):
            valid_position = False
            while not valid_position:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
                
                # Ensure enemy is not on walls or blocks and not too close to players
                if self.map.get_cell_type(x, y) == 0:
                    # Check distance to all players
                    too_close = False
                    for player in self.players.values():
                        player_grid_x = int(player.x / self.cell_size)
                        player_grid_y = int(player.y / self.cell_size)
                        dist = math.sqrt((x - player_grid_x)**2 + (y - player_grid_y)**2)
                        if dist < 3:  # Must be at least 3 cells away from players
                            too_close = True
                            break
                    
                    if not too_close:
                        valid_position = True
                        speed = 1 + random.random() * 0.5
                        self.enemies.append(Enemy(x * self.cell_size, y * self.cell_size, 
                                                  self.cell_size, speed))
    
    def update(self):
        """Update game state and return the new state"""
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_update_time
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
    
    def update_player(self, player, delta_time):
        """Update a single player"""
        if player.lives <= 0:
            return
        
        # Handle player movement
        dx, dy = 0, 0
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
            normalize = 1 / math.sqrt(2)
            dx *= normalize
            dy *= normalize
        
        # Apply delta time
        dx *= delta_time * 60
        dy *= delta_time * 60
        
        # Move with collision detection (X axis)
        if dx != 0:
            new_x = player.x + dx
            if not self.check_collision(new_x, player.y, player.width, player.height, player):
                player.x = new_x
        
        # Move with collision detection (Y axis)
        if dy != 0:
            new_y = player.y + dy
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
    
    def update_enemy(self, enemy, delta_time):
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
        dx = enemy.direction[0] * enemy.speed * delta_time * 60
        dy = enemy.direction[1] * enemy.speed * delta_time * 60
        
        new_x = enemy.x + dx
        new_y = enemy.y + dy
        
        # Move with collision detection (X axis)
        collision_x = self.check_collision(new_x, enemy.y, enemy.width, enemy.height)
        if not collision_x:
            enemy.x = new_x
        
        # Move with collision detection (Y axis)
        collision_y = self.check_collision(enemy.x, new_y, enemy.width, enemy.height)
        if not collision_y:
            enemy.y = new_y
        
        # If collision occurred, change direction
        if collision_x or collision_y:
            enemy.direction = self.get_random_direction()
            enemy.move_timer = 0
    
    def update_bomb(self, bomb, delta_time):
        """Update a single bomb"""
        bomb.timer += delta_time
        
        if not bomb.exploded and bomb.timer >= 3:  # Explode after 3 seconds
            bomb.exploded = True
            self.handle_explosion(bomb)
        
        if bomb.exploded:
            bomb.explosion_timer += delta_time
            if bomb.explosion_timer >= 0.7:  # Explosion duration
                self.bombs.remove(bomb)
    
    def handle_explosion(self, bomb):
        """Handle bomb explosion effects"""
        # Calculate explosion cells
        grid_x = int(bomb.x / self.cell_size)
        grid_y = int(bomb.y / self.cell_size)
        bomb.explosion_cells = [(grid_x, grid_y)]  # Center cell
        
        # Check each direction (right, left, down, up)
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        for dx, dy in directions:
            for i in range(1, bomb.power + 1):
                current_x = grid_x + (dx * i)
                current_y = grid_y + (dy * i)
                
                # Check if explosion hits a wall
                if self.map.is_wall(current_x, current_y):
                    break  # Stop explosion in this direction
                
                # Add explosion cell
                bomb.explosion_cells.append((current_x, current_y))
                
                # If explosion hits a breakable block
                if self.map.is_breakable_block(current_x, current_y):
                    self.map.destroy_block(current_x, current_y)
                    self.score += 10
                    
                    # Chance to spawn powerup
                    if random.random() < 0.2:
                        self.spawn_power_up(current_x * self.cell_size, current_y * self.cell_size)
                    break  # Stop explosion in this direction
        
        # Check if explosion hits players
        for player in self.players.values():
            if self.check_explosion_collision(bomb, player) and not player.invulnerable:
                self.handle_player_hit(player)
        
        # Check if explosion hits enemies
        for enemy in list(self.enemies):
            if not enemy.destroyed and self.check_explosion_collision(bomb, enemy):
                enemy.destroyed = True
                enemy.destroy_animation_timer = 0
                self.score += 100
                
                # Chance to spawn powerup
                if random.random() < 0.3:
                    self.spawn_power_up(enemy.x, enemy.y)
    
    def check_collision(self, x, y, width, height, ignore_entity=None):
        """Check if position collides with map or entities"""
        # Check map collision
        grid_left = int(x / self.cell_size)
        grid_right = int((x + width) / self.cell_size)
        grid_top = int(y / self.cell_size)
        grid_bottom = int((y + height) / self.cell_size)
        
        # Check all corners
        if (self.map.is_solid(grid_left, grid_top) or
            self.map.is_solid(grid_right, grid_top) or
            self.map.is_solid(grid_left, grid_bottom) or
            self.map.is_solid(grid_right, grid_bottom)):
            return True
        
        # Check collision with bombs
        for bomb in self.bombs:
            if bomb == ignore_entity:
                continue
                
            bomb_grid_x = int(bomb.x / self.cell_size)
            bomb_grid_y = int(bomb.y / self.cell_size)
            
            # Check if entity is trying to move into a bomb's cell
            entity_current_grid_x = int((x + width/2) / self.cell_size)
            entity_current_grid_y = int((y + height/2) / self.cell_size)
            
            # Don't allow moving into a cell with a bomb unless already in it
            if (bomb_grid_x == entity_current_grid_x and bomb_grid_y == entity_current_grid_y):
                # Already in the same cell as bomb, allow movement
                continue
            
            # Entity trying to enter bomb's cell
            entity_new_grid_x = int((x + width/2) / self.cell_size)
            entity_new_grid_y = int((y + height/2) / self.cell_size)
            
            if bomb_grid_x == entity_new_grid_x and bomb_grid_y == entity_new_grid_y:
                return True
        
        return False
    
    def check_entity_collision(self, entity1, entity2):
        """Check collision between two entities"""
        return (entity1.x < entity2.x + entity2.width and
                entity1.x + entity1.width > entity2.x and
                entity1.y < entity2.y + entity2.height and
                entity1.y + entity1.height > entity2.y)
    
    def check_explosion_collision(self, bomb, entity):
        """Check if an explosion hits an entity"""
        entity_grid_x = int((entity.x + entity.width/2) / self.cell_size)
        entity_grid_y = int((entity.y + entity.height/2) / self.cell_size)
        
        for cell_x, cell_y in bomb.explosion_cells:
            if cell_x == entity_grid_x and cell_y == entity_grid_y:
                return True
        
        return False
    
    def get_random_direction(self):
        """Get a random direction for enemy movement"""
        if random.random() < 0.5:
            return (random.choice([-1, 1]), 0)
        else:
            return (0, random.choice([-1, 1]))
    
    def handle_player_hit(self, player):
        """Handle player being hit by an enemy or explosion"""
        player.lives -= 1
        
        if player.lives <= 0:
            # Check if all players are dead
            alive_players = [p for p in self.players.values() if p.lives > 0]
            if not alive_players:
                self.game_over = True
        else:
            # Make player invulnerable temporarily
            player.invulnerable = True
            player.invulnerable_timer = 0
    
    def spawn_power_up(self, x, y):
        """Spawn a power-up at the given position"""
        power_up_type = random.choice(list(PowerUpType))
        self.power_ups.append(PowerUp(x, y, self.cell_size, power_up_type))
    
    def apply_power_up(self, player, power_up):
        """Apply power-up effect to player"""
        if power_up.type == PowerUpType.BOMB_UP:
            player.max_bombs += 1
        elif power_up.type == PowerUpType.POWER_UP:
            player.bomb_power += 1
        elif power_up.type == PowerUpType.LIFE_UP:
            player.lives += 1
        elif power_up.type == PowerUpType.SPEED_UP:
            player.speed += 0.5
            if player.speed > 6:
                player.speed = 6
    
    def place_bomb(self, player):
        """Place a bomb at the player's position"""
        if len([b for b in self.bombs if b.owner_id == player.id]) >= player.max_bombs:
            return False
        
        grid_x = int((player.x + player.width/2) / self.cell_size)
        grid_y = int((player.y + player.height/2) / self.cell_size)
        
        # Check if there's already a bomb at this position
        for bomb in self.bombs:
            bomb_grid_x = int(bomb.x / self.cell_size)
            bomb_grid_y = int(bomb.y / self.cell_size)
            if bomb_grid_x == grid_x and bomb_grid_y == grid_y:
                return False
        
        # Check if position is solid (wall or block)
        if self.map.is_solid(grid_x, grid_y):
            return False
        
        # Place bomb
        bomb = Bomb(
            grid_x * self.cell_size,
            grid_y * self.cell_size,
            self.cell_size,
            player.bomb_power,
            player.id
        )
        self.bombs.append(bomb)
        return True
    
    def level_complete(self):
        """Handle level completion"""
        self.level += 1
        self.score += 500
        
        # Reset map and create new enemies
        self.map.generate_map()
        self.create_enemies()
        self.power_ups = []
        
        # Reset player positions
        start_positions = [
            (1, 1),
            (self.width - 2, 1),
            (1, self.height - 2),
            (self.width - 2, self.height - 2)
        ]
        
        for i, player in enumerate(self.players.values()):
            if i < len(start_positions):
                x, y = start_positions[i]
                player.x = x * self.cell_size
                player.y = y * self.cell_size
    
    def is_active(self):
        """Check if the game is still active"""
        return not self.game_over and len(self.players) > 0
    
    def get_state(self):
        """Get the full game state to send to clients"""
        players_data = {}
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
        
        enemies_data = []
        for enemy in self.enemies:
            enemies_data.append({
                'x': enemy.x,
                'y': enemy.y,
                'width': enemy.width,
                'height': enemy.height,
                'destroyed': enemy.destroyed
            })
        
        bombs_data = []
        for bomb in self.bombs:
            explosion_cells = []
            if bomb.exploded:
                for x, y in bomb.explosion_cells:
                    explosion_cells.append({
                        'x': x * self.cell_size,
                        'y': y * self.cell_size
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
        
        power_ups_data = []
        for power_up in self.power_ups:
            power_ups_data.append({
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
            'players': players_data,
            'enemies': enemies_data,
            'bombs': bombs_data,
            'powerUps': power_ups_data,
            'map': map_data,
            'score': self.score,
            'level': self.level,
            'gameOver': self.game_over
        }

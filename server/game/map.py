import random

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = []
        
        # Cell types:
        # 0 = empty
        # 1 = solid wall (indestructible)
        # 2 = breakable block
        
        # Initialize grid with empty cells
        for y in range(height):
            self.grid.append([0] * width)
    
    def generate_map(self):
        """Generate a new map with walls and breakable blocks"""
        # Reset grid
        for y in range(self.height):
            for x in range(self.width):
                # Place solid walls on the border and in checkerboard pattern
                if (x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1 or 
                    (x % 2 == 0 and y % 2 == 0)):
                    self.grid[y][x] = 1  # Solid wall
                else:
                    self.grid[y][x] = 0  # Empty
        
        # Place breakable blocks randomly (40% chance for empty spaces)
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 0 and random.random() < 0.4:
                    # Keep starting areas clear for players
                    if not self.is_player_start_area(x, y):
                        self.grid[y][x] = 2  # Breakable block
    
    def is_player_start_area(self, x, y):
        """Check if position is in a player starting area (corners)"""
        # Top-left
        if x <= 2 and y <= 2:
            return True
        # Top-right
        if x >= self.width - 3 and y <= 2:
            return True
        # Bottom-left
        if x <= 2 and y >= self.height - 3:
            return True
        # Bottom-right
        if x >= self.width - 3 and y >= self.height - 3:
            return True
        return False
    
    def get_cell_type(self, x, y):
        """Get the type of cell at the specified coordinates"""
        # Check bounds
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return 1  # Treat out of bounds as solid wall
        
        return self.grid[y][x]
    
    def is_wall(self, x, y):
        """Check if the cell is a solid wall"""
        return self.get_cell_type(x, y) == 1
    
    def is_breakable_block(self, x, y):
        """Check if the cell is a breakable block"""
        return self.get_cell_type(x, y) == 2
    
    def is_solid(self, x, y):
        """Check if the cell is solid (wall or breakable block)"""
        cell_type = self.get_cell_type(x, y)
        return cell_type == 1 or cell_type == 2
    
    def destroy_block(self, x, y):
        """Destroy a breakable block"""
        # Check bounds
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        
        # Only destroy breakable blocks
        if self.grid[y][x] == 2:
            self.grid[y][x] = 0

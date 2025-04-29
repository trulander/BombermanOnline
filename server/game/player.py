class Player:
    # Colors for different players
    COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    
    def __init__(self, player_id):
        self.id = player_id
        self.x = 0
        self.y = 0
        self.width = 32  # Slightly smaller than cell size
        self.height = 32
        self.speed = 3
        self.max_bombs = 1
        self.bomb_power = 1
        self.lives = 3
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.color = self.COLORS[0]  # Default color, will be assigned based on player index
        
        # Input state
        self.inputs = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'bomb': False
        }
    
    def set_inputs(self, inputs):
        """Update player inputs"""
        for key, value in inputs.items():
            if key in self.inputs:
                self.inputs[key] = value

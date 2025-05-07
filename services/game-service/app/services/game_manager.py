import time
import random
from typing import Optional, Any

from ..entities.player import Player

class GameManager:
    """Менеджер игр, управляющий всеми активными играми"""
    
    def __init__(self):
        self.games: dict[str, Game] = {}  # Словарь с активными играми
    
    def create_game(self, game_id: str) -> Game:
        """Создает новую игру с указанным ID"""
        game = Game(game_id)
        self.games[game_id] = game
        return game
    
    def game_exists(self, game_id: str) -> bool:
        """Проверяет существование игры с указанным ID"""
        return game_id in self.games
    
    def add_player(self, game_id: str, player_id: str) -> Optional[Player]:
        """Добавляет игрока в игру"""
        if not self.game_exists(game_id):
            return None
        
        game = self.games[game_id]
        
        # Создаем игрока со случайным цветом
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF"]
        color = random.choice(colors)
        
        # Находим свободную позицию для спавна игрока
        spawn_positions = game.get_spawn_positions()
        if not spawn_positions:
            return None  # Нет свободных позиций
        
        spawn_pos = random.choice(spawn_positions)
        
        # Создаем игрока
        player = Player(
            player_id=player_id,
            x=spawn_pos[0],
            y=spawn_pos[1],
            color=color
        )
        
        # Добавляем игрока в игру
        game.add_player(player)
        
        return player
    
    def remove_player(self, game_id: str, player_id: str) -> bool:
        """Удаляет игрока из игры"""
        if not self.game_exists(game_id):
            return False
        
        return self.games[game_id].remove_player(player_id)
    
    def process_player_input(self, game_id: str, player_id: str, inputs: dict[str, bool]) -> bool:
        """Обрабатывает ввод игрока"""
        if not self.game_exists(game_id):
            return False
        
        game = self.games[game_id]
        
        # Устанавливаем ввод игрока
        return game.set_player_input(player_id, inputs)
    
    def place_bomb(self, game_id: str, player_id: str) -> bool:
        """Устанавливает бомбу для указанного игрока"""
        if not self.game_exists(game_id):
            return False
        
        game = self.games[game_id]
        
        # Устанавливаем бомбу
        return game.place_bomb(player_id)
    
    def get_game_state(self, game_id: str) -> Optional[dict[str, Any]]:
        """Возвращает текущее состояние игры"""
        if not self.game_exists(game_id):
            return None
        
        return self.games[game_id].get_state()
    
    def update_all_games(self) -> dict[str, dict[str, Any]]:
        """Обновляет все активные игры и возвращает их состояния"""
        current_time = time.time()
        game_states = {}
        
        # Список игр для удаления (те, что завершились или не имеют игроков)
        games_to_remove = []
        
        for game_id, game in self.games.items():
            # Обновляем игру
            game.update(current_time)
            
            # Получаем актуальное состояние
            game_state = game.get_state()
            game_states[game_id] = game_state
            
            # Проверяем необходимость удаления игры
            if game.is_empty() or game.is_over():
                # Если в игре нет игроков или игра завершена,
                # добавляем ее в список для удаления
                if game.is_empty():
                    print(f"Игра {game_id} не имеет игроков и будет удалена")
                elif game.is_over():
                    print(f"Игра {game_id} завершена и будет удалена")
                    
                games_to_remove.append(game_id)
                # Даем последнее состояние перед удалением
                game_states[game_id] = game_state
        
        # Удаляем игры, которые нужно убрать
        for game_id in games_to_remove:
            del self.games[game_id]
            
        return game_states 
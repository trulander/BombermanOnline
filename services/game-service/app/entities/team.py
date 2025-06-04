from uuid import uuid4
from typing import List


class Team:
    """Класс представляет команду в игре."""
    
    def __init__(self, team_id: str = None, name: str = None):
        self.id: str = team_id or str(uuid4())
        self.name: str = name or f"Team {self.id[:8]}"
        self.score: int = 0
        self.player_ids: List[str] = []
    
    def add_player(self, player_id: str) -> None:
        """Добавляет игрока в команду."""
        if player_id not in self.player_ids:
            self.player_ids.append(player_id)
    
    def remove_player(self, player_id: str) -> bool:
        """Удаляет игрока из команды. Возвращает True если игрок был удален."""
        if player_id in self.player_ids:
            self.player_ids.remove(player_id)
            return True
        return False
    
    def add_score(self, points: int) -> None:
        """Добавляет очки команде."""
        self.score += points
    
    def get_player_count(self) -> int:
        """Возвращает количество игроков в команде."""
        return len(self.player_ids)
    
    def to_dict(self) -> dict:
        """Возвращает словарь с данными команды."""
        return {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "player_ids": self.player_ids.copy(),
            "player_count": self.get_player_count()
        } 
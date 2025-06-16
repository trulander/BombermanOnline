from typing import Dict, List, Optional
import random
from app.entities.team import Team
from app.models.team_models import TeamModeSettings
from app.entities.game_mode import GameModeType
from app.entities.player import Player


class TeamService:
    """Сервис для управления командами в игровой сессии."""
    
    def __init__(self, team_mode_settings: TeamModeSettings):
        self.teams: Dict[str, Team] = {}
        self.mode_settings: TeamModeSettings = team_mode_settings
    
    def create_team(self, team_name: str, team_id: str = None) -> Team:
        """Создает новую команду."""
        if len(self.teams) >= self.mode_settings.max_team_count:
            raise ValueError(f"Превышен максимальный лимит команд: {self.mode_settings.max_team_count}")
        
        team = Team(team_id=team_id, name=team_name)
        self.teams[team.id] = team
        return team
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Получает команду по ID."""
        return self.teams.get(team_id)
    
    def get_all_teams(self) -> List[Team]:
        """Возвращает все команды."""
        return list(self.teams.values())
    
    def update_team(self, team_id: str, name: str = None) -> Optional[Team]:
        """Обновляет команду."""
        team = self.teams.get(team_id)
        if not team:
            return None
        
        if name is not None:
            team.name = name
        
        return team
    
    def delete_team(self, team_id: str) -> bool:
        """Удаляет команду."""
        if team_id in self.teams:
            del self.teams[team_id]
            return True
        return False
    
    def add_player_to_team(self, team_id: str, player_id: str) -> bool:
        """Добавляет игрока в команду."""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Проверяем лимит игроков в команде
        if team.get_player_count() >= self.mode_settings.max_players_per_team:
            raise ValueError(f"Превышен максимальный лимит игроков в команде: {self.mode_settings.max_players_per_team}")
        
        # Удаляем игрока из других команд
        self._remove_player_from_all_teams(player_id)
        
        team.add_player(player_id)
        return True
    
    def remove_player_from_team(self, player_id: str) -> bool:
        """Удаляет игрока из команды."""
        team = self.get_player_team(player_id=player_id)
        if not team:
            return False
        
        return team.remove_player(player_id)
    
    def _remove_player_from_all_teams(self, player_id: str) -> None:
        """Удаляет игрока из всех команд."""
        for team in self.teams.values():
            team.remove_player(player_id)
    
    def get_player_team(self, player_id: str) -> Optional[Team]:
        """Возвращает команду игрока."""
        for team in self.teams.values():
            if player_id in team.player_ids:
                return team
        return None
    
    def add_score_to_player_team(self, player_id: str, points: int) -> bool:
        """Добавляет очки команде игрока."""
        team = self.get_player_team(player_id)
        if team:
            team.add_score(points)
            return True
        return False
    
    def setup_default_teams(self) -> None:
        """Создает команды по умолчанию для текущего игрового режима."""
        self.teams.clear()
        
        if self.mode_settings.game_mode == GameModeType.FREE_FOR_ALL:
            # Для FFA команды создаются для каждого игрока отдельно
            return
        
        team_count = self.mode_settings.default_team_count
        team_names = self.mode_settings.default_team_names
        
        for i in range(team_count):
            if i < len(team_names):
                team_name = team_names[i]
            else:
                team_name = f"Team {i + 1}"
            
            self.create_team(team_name)
    
    def auto_distribute_players(self, players: List[Player], redistribute_existing: bool = False) -> None:
        """Автоматически распределяет игроков по командам."""
        if not self.mode_settings.auto_distribute_players:
            return
        
        # Очищаем существующее распределение если требуется
        if redistribute_existing:
            for team in self.teams.values():
                team.player_ids.clear()
        
        # Получаем игроков без команды
        unassigned_players = []
        for player in players:
            if redistribute_existing or not self.get_player_team(player.id):
                unassigned_players.append(player)
        
        if not unassigned_players:
            return
        
        if self.mode_settings.game_mode == GameModeType.FREE_FOR_ALL:
            # Каждый игрок в своей команде
            self._distribute_ffa_players(unassigned_players)
        else:
            # Равномерное распределение по существующим командам
            self._distribute_team_players(unassigned_players)
    
    def _distribute_ffa_players(self, players: List[Player]) -> None:
        """Распределяет игроков для режима FFA (каждый в своей команде)."""
        for player in players:
            team_name = f"{player.name}'s Team"
            team = self.create_team(team_name)
            team.add_player(player.id)
    
    def _distribute_team_players(self, players: List[Player]) -> None:
        """Равномерно распределяет игроков по существующим командам."""
        if not self.teams:
            self.setup_default_teams()
        
        teams_list = list(self.teams.values())
        random.shuffle(players)  # Перемешиваем для случайного распределения
        
        for i, player in enumerate(players):
            team_index = i % len(teams_list)
            team = teams_list[team_index]
            
            # Проверяем лимит игроков в команде
            if team.get_player_count() < self.mode_settings.max_players_per_team:
                team.add_player(player.id)
    
    def validate_teams(self) -> List[str]:
        """Проверяет корректность настройки команд. Возвращает список ошибок."""
        errors = []
        
        # Проверяем минимальное количество игроков в команде
        if not self.mode_settings.allow_uneven_teams:
            team_sizes = [team.get_player_count() for team in self.teams.values()]
            if team_sizes and max(team_sizes) - min(team_sizes) > 1:
                errors.append("Команды должны быть примерно равными по размеру")
        
        # Проверяем минимальное количество игроков в команде
        for team in self.teams.values():
            if team.get_player_count() < self.mode_settings.min_players_per_team:
                errors.append(f"Команда '{team.name}' имеет слишком мало игроков (минимум: {self.mode_settings.min_players_per_team})")
        
        return errors
    
    def get_teams_state(self) -> dict[str, dict]:
        """Возвращает состояние всех команд."""
        return {
            team.id: team.to_dict()
            for team in self.teams.values()
        }
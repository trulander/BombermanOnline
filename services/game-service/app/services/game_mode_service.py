from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Dict, Any, Tuple

if TYPE_CHECKING:
    from ..entities.game_settings import GameSettings


class GameModeService(ABC):
    """Абстрактный базовый класс для игровых режимов"""
    
    def __init__(self, game_settings: 'GameSettings'):
        self.settings = game_settings
    



from enum import Enum


class GameStatus(Enum):
    """Статусы игры"""
    PENDING = "PENDING"        # Ожидание игроков
    ACTIVE = "ACTIVE"          # Активная игра
    PAUSED = "PAUSED"          # Приостановлена
    FINISHED = "FINISHED"      # Завершена